from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from starlette.responses import StreamingResponse, JSONResponse
import io
import base64
from pydantic import BaseModel

from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions

import models, schemas, services
from database import get_db, SessionLocal

# --- Clerk and Security Setup ---
clerk_secret_key = os.getenv("CLERK_SECRET_KEY")
if not clerk_secret_key:
    raise ValueError("CLERK_SECRET_KEY environment variable not found.")
clerk = Clerk(bearer_auth=clerk_secret_key)

EMAIL_WEBHOOK_SECRET = os.getenv("EMAIL_WEBHOOK_SECRET")
if not EMAIL_WEBHOOK_SECRET:
    raise ValueError("EMAIL_WEBHOOK_SECRET environment variable not found.")

# --- FIX: Use a regular expression for more flexible CORS handling ---
# This allows requests from localhost and any subdomain of vercel.app,
# which is more robust for preview and production deployments.
ALLOWED_ORIGIN_REGEX = os.getenv("ALLOWED_ORIGIN_REGEX", r"http://localhost:3000")

app = FastAPI(title="IIP API")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX, # Use the regex here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Root Endpoint for Health Checks ---
@app.get("/")
def read_root():
    return {"status": "IIP API is running"}


# --- Pydantic Models for Resend Webhook Payload ---
class ResendAttachment(BaseModel):
    filename: str
    content: str

class ResendInboundEmail(BaseModel):
    subject: Optional[str] = "No Subject"
    attachments: Optional[List[ResendAttachment]] = []

# --- Existing Authentication and Helper Functions ---
def get_current_user(req: Request) -> Dict:
    try:
        request_state = clerk.authenticate_request(req)
        if not request_state.is_signed_in:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        return request_state.payload
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication error: {e}")

def perform_analysis_and_update(deal_id: int, file_contents: bytes, file_name: str):
    db = SessionLocal()
    try:
        deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
        if not deal: return

        s3_stream = io.BytesIO(file_contents)
        s3_url = services.upload_to_s3(s3_stream, file_name)
        
        pdf_stream = io.BytesIO(file_contents)
        text = services.extract_text_from_pdf(pdf_stream)
        if not text: raise Exception("Failed to extract text from PDF.")

        analysis_data = services.analyze_document_text(text)
        if "error" in analysis_data: raise Exception(analysis_data["error"])

        deal.s3_url = s3_url
        deal.analysis_data = analysis_data
        deal.status = "Complete"
        db.commit()
    except Exception as e:
        print(f"Error in background task for deal {deal_id}: {e}")
        deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
        if deal:
            deal.status = "Failed"
            db.commit()
    finally:
        db.close()

# --- Email Ingest Webhook for Resend ---
@app.post("/api/webhooks/email-ingest")
async def email_ingest_webhook(
    request: Request,
    payload: ResendInboundEmail,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    auth_token = request.headers.get("Authorization")
    if auth_token != f"Bearer {EMAIL_WEBHOOK_SECRET}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")

    pdf_attachment = None
    if payload.attachments:
        for attachment in payload.attachments:
            if attachment.filename.lower().endswith('.pdf'):
                pdf_attachment = attachment
                break
    
    if not pdf_attachment:
        return JSONResponse(content={"message": "No PDF attachment found."}, status_code=200)

    try:
        file_contents = base64.b64decode(pdf_attachment.content)
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to decode attachment content.")

    file_name = pdf_attachment.filename
    deal_title = payload.subject or file_name

    new_deal = models.Deal(
        user_id="system-auto-import", 
        user_name="Auto-Import",
        file_name=deal_title,
        status="Analyzing"
    )
    db.add(new_deal)
    db.commit()
    db.refresh(new_deal)

    background_tasks.add_task(perform_analysis_and_update, new_deal.id, file_contents, file_name)

    return JSONResponse(content={"message": "Email received and processing started."}, status_code=200)


# --- Existing User-Facing Endpoints ---
@app.get("/api/deals", response_model=List[schemas.Deal])
def get_all_deals(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    deals = db.query(models.Deal).order_by(models.Deal.id.desc()).all()
    return deals

@app.post("/analyze/", response_model=schemas.Deal)
async def analyze_document(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user), 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID not found in token")
    first_name = current_user.get("first_name", "")
    last_name = current_user.get("last_name", "")
    user_name = f"{first_name} {last_name}".strip() or "Anonymous"
    file_contents = await file.read()
    new_deal = models.Deal(
        user_id=user_id, 
        user_name=user_name,
        file_name=file.filename,
        status="Analyzing"
    )
    db.add(new_deal)
    db.commit()
    db.refresh(new_deal)
    background_tasks.add_task(perform_analysis_and_update, new_deal.id, file_contents, file.filename)
    return new_deal

@app.post("/api/deals/{deal_id}/feedback", response_model=schemas.Feedback)
def create_feedback_for_deal(deal_id: int, feedback: schemas.FeedbackCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID not found in token")
    
    db_deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if db_deal is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    first_name = current_user.get("first_name", "")
    last_name = current_user.get("last_name", "")
    user_name = f"{first_name} {last_name}".strip() or "Anonymous"
    db_feedback = models.Feedback(
        **feedback.dict(), 
        deal_id=deal_id, 
        user_id=user_id, 
        user_name=user_name
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


@app.delete("/api/deals/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deal(deal_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if deal is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    services.delete_from_s3(deal.file_name)
    db.delete(deal)
    db.commit()
    return

@app.get("/api/deals/{deal_id}/view-pdf")
def view_pdf(deal_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if deal is None or not deal.s3_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF not available yet or deal not found.")
    pdf_stream = services.get_s3_object_stream(deal.file_name)
    if pdf_stream is None: 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve PDF.")
    return StreamingResponse(pdf_stream, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename=\"{deal.file_name}\""})

@app.delete("/api/feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(feedback_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    feedback = db.query(models.Feedback).filter(models.Feedback.id == feedback_id).first()
    if feedback is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    db.delete(feedback)
    db.commit()
    return
