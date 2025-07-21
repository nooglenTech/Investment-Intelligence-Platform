from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

import models, schemas, services
from database import get_db

app = FastAPI(title="IIP API")
# ... (CORS middleware remains the same) ...
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/deals", response_model=List[schemas.Deal])
def get_all_deals(db: Session = Depends(get_db)):
    deals = db.query(models.Deal).order_by(models.Deal.id.desc()).all()
    return deals

@app.get("/api/deals/{deal_id}", response_model=schemas.Deal)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal

@app.post("/api/deals/{deal_id}/feedback", response_model=schemas.Feedback)
def create_feedback_for_deal(deal_id: int, feedback: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    db_deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if db_deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    db_feedback = models.Feedback(**feedback.dict(), deal_id=deal_id)
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

@app.post("/analyze/", response_model=schemas.Deal)
def analyze_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # ... (this function remains the same) ...
    text = services.extract_text_from_pdf(file.file)
    if not text:
        raise HTTPException(status_code=400, detail="Failed to extract text from PDF.")
    file.file.seek(0)
    try:
        s3_url = services.upload_to_s3(file.file, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")
    analysis_data = services.analyze_document_text(text)
    if "error" in analysis_data:
        raise HTTPException(status_code=500, detail=analysis_data["error"])
    new_deal = models.Deal(file_name=file.filename, s3_url=s3_url, analysis_data=analysis_data)
    db.add(new_deal)
    db.commit()
    db.refresh(new_deal)
    return new_deal

# *** NEW ENDPOINT ***
@app.delete("/api/deals/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deal(deal_id: int, db: Session = Depends(get_db)):
    """Deletes a deal, its feedback, and its file from S3."""
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Delete the file from S3 first
    services.delete_from_s3(deal.file_name)
    
    # Delete the deal from the database (feedback will be deleted by cascade)
    db.delete(deal)
    db.commit()
    return

# *** NEW ENDPOINT ***
@app.delete("/api/feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(feedback_id: int, db: Session = Depends(get_db)):
    """Deletes a single piece of feedback."""
    feedback = db.query(models.Feedback).filter(models.Feedback.id == feedback_id).first()
    if feedback is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    db.delete(feedback)
    db.commit()
    return
