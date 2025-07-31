# cim-backend/routers/email_ingest.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from starlette.responses import JSONResponse
import io
import base64
from pydantic import BaseModel

import models, schemas, services
from database import get_db, SessionLocal

router = APIRouter()

# It's better to access environment variables through the services module for consistency
EMAIL_WEBHOOK_SECRET = services.os.getenv("EMAIL_WEBHOOK_SECRET")
if not EMAIL_WEBHOOK_SECRET:
    raise ValueError("EMAIL_WEBHOOK_SECRET environment variable not found.")

# --- Pydantic Models for Resend Webhook Payload ---
class ResendAttachment(BaseModel):
    filename: str
    content: str

class ResendInboundEmail(BaseModel):
    subject: Optional[str] = "No Subject"
    attachments: Optional[List[ResendAttachment]] = []

def perform_analysis_and_update(deal_id: int, file_contents: bytes, file_name: str):
    """
    Background task to process the PDF, run analysis, and update the deal in the database.
    This is the same function from the original main.py.
    """
    db = SessionLocal()
    try:
        deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
        if not deal:
            print(f"Background task failed: Deal with ID {deal_id} not found.")
            return

        # 1. Upload the original file to S3
        s3_stream = io.BytesIO(file_contents)
        s3_url = services.upload_to_s3(s3_stream, file_name)
        
        # 2. Extract text from the PDF
        pdf_stream = io.BytesIO(file_contents)
        text = services.extract_text_from_pdf(pdf_stream)
        if not text:
            raise Exception("Failed to extract text from PDF.")

        # 3. Analyze the text with OpenAI
        analysis_data = services.analyze_document_text(text)
        if "error" in analysis_data:
            raise Exception(analysis_data["error"])

        # 4. Update the deal record with the results
        deal.s3_url = s3_url
        deal.analysis_data = analysis_data
        deal.status = "Complete"
        db.commit()
        print(f"Successfully processed and analyzed deal {deal_id}.")
    except Exception as e:
        print(f"Error in background task for deal {deal_id}: {e}")
        deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
        if deal:
            deal.status = "Failed"
            db.commit()
    finally:
        db.close()

# --- Email Ingest Webhook for Resend ---
@router.post("/api/webhooks/email-ingest", tags=["Webhooks"])
async def email_ingest_webhook(
    request: Request,
    payload: ResendInboundEmail,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    This endpoint receives inbound emails from a service like Resend,
    extracts the first PDF attachment, creates a new deal, and starts
    the analysis process in the background.
    """
    # 1. Authenticate the webhook request
    auth_token = request.headers.get("Authorization")
    if auth_token != f"Bearer {EMAIL_WEBHOOK_SECRET}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")

    # 2. Find the first PDF attachment in the email
    pdf_attachment = None
    if payload.attachments:
        for attachment in payload.attachments:
            if attachment.filename.lower().endswith('.pdf'):
                pdf_attachment = attachment
                break
    
    if not pdf_attachment:
        # It's okay if there's no PDF, just acknowledge the request.
        return JSONResponse(content={"message": "No PDF attachment found."}, status_code=200)

    # 3. Decode the attachment content from Base64
    try:
        file_contents = base64.b64decode(pdf_attachment.content)
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to decode attachment content.")

    file_name = pdf_attachment.filename
    deal_title = payload.subject or file_name

    # 4. Create a new Deal record with "Analyzing" status
    new_deal = models.Deal(
        user_id="system-auto-import", 
        user_name="Auto-Import",
        file_name=deal_title,
        status="Analyzing"
    )
    db.add(new_deal)
    db.commit()
    db.refresh(new_deal)

    # 5. Add the analysis function to the background tasks
    background_tasks.add_task(perform_analysis_and_update, new_deal.id, file_contents, file_name)

    return JSONResponse(content={"message": "Email received and processing started."}, status_code=200)
