from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Annotated
from starlette.responses import StreamingResponse

# Import the Clerk library
from clerk_sdk.clerk import Clerk
from clerk_sdk.models.sessions import Session as ClerkSession

import models, schemas, services
from database import get_db

# Initialize the Clerk client with your secret key
clerk_client = Clerk(secret_key=os.getenv("CLERK_SECRET_KEY"))

app = FastAPI(title="IIP API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- NEW AUTHENTICATION DEPENDENCY ---
async def get_current_user(authorization: Annotated[str, Header()]) -> str:
    """
    Dependency to get the current user from the Authorization header.
    The frontend will send a token from Clerk, and this function verifies it.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        # The token is sent as "Bearer <token>", so we split it
        token = authorization.split(" ")[1]
        session = await clerk_client.sessions.verify_token(token=token)
        if not session or not session.user_id:
            raise HTTPException(status_code=401, detail="Invalid token or session")
        return session.user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

# --- PROTECTED ENDPOINTS ---

@app.get("/api/deals", response_model=List[schemas.Deal])
def get_all_deals(user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    # This endpoint now requires a valid login, but we don't filter deals by user yet.
    # In the future, you could add: .filter(models.Deal.user_id == user_id)
    deals = db.query(models.Deal).order_by(models.Deal.id.desc()).all()
    return deals

@app.post("/analyze/", response_model=schemas.Deal)
def analyze_document(
    user_id: str = Depends(get_current_user), 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # ... (analysis logic is the same) ...
    text = services.extract_text_from_pdf(file.file)
    if not text: raise HTTPException(status_code=400, detail="Failed to extract text from PDF.")
    file.file.seek(0)
    try:
        s3_url = services.upload_to_s3(file.file, file.filename)
    except Exception as e: raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")
    analysis_data = services.analyze_document_text(text)
    if "error" in analysis_data: raise HTTPException(status_code=500, detail=analysis_data["error"])
    
    # *** THIS IS THE CHANGE ***
    # We now save the user's ID with the new deal.
    new_deal = models.Deal(
        user_id=user_id, 
        file_name=file.filename, 
        s3_url=s3_url, 
        analysis_data=analysis_data
    )
    db.add(new_deal)
    db.commit()
    db.refresh(new_deal)
    return new_deal

@app.post("/api/deals/{deal_id}/feedback", response_model=schemas.Feedback)
def create_feedback_for_deal(
    deal_id: int, 
    feedback: schemas.FeedbackCreate, 
    user_id: str = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    db_deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if db_deal is None: raise HTTPException(status_code=404, detail="Deal not found")
    
    # *** THIS IS THE CHANGE ***
    # We now save the user's ID with the new feedback.
    db_feedback = models.Feedback(**feedback.dict(), deal_id=deal_id, user_id=user_id)
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

@app.delete("/api/deals/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deal(deal_id: int, user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if deal is None: raise HTTPException(status_code=404, detail="Deal not found")
    
    # In the future, you might want to restrict deletion to only the user who created it:
    # if deal.user_id != user_id:
    #     raise HTTPException(status_code=403, detail="Not authorized to delete this deal")
    
    services.delete_from_s3(deal.file_name)
    db.delete(deal)
    db.commit()
    return

# ... (other endpoints like view-pdf and delete-feedback would also be protected) ...
@app.get("/api/deals/{deal_id}/view-pdf")
def view_pdf(deal_id: int, user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if deal is None: raise HTTPException(status_code=404, detail="Deal not found")
    pdf_stream = services.get_s3_object_stream(deal.file_name)
    if pdf_stream is None: raise HTTPException(status_code=500, detail="Could not retrieve PDF.")
    return StreamingResponse(pdf_stream, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename=\"{deal.file_name}\""})

@app.delete("/api/feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(feedback_id: int, user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    feedback = db.query(models.Feedback).filter(models.Feedback.id == feedback_id).first()
    if feedback is None: raise HTTPException(status_code=404, detail="Feedback not found")
    db.delete(feedback)
    db.commit()
    return
