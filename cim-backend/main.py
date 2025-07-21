from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

import models, schemas, services
from database import get_db

app = FastAPI(title="IIP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/deals", response_model=List[schemas.Deal])
def get_all_deals(db: Session = Depends(get_db)):
    """Endpoint to get all deals from the database."""
    deals = db.query(models.Deal).order_by(models.Deal.id.desc()).all()
    return deals

@app.get("/api/deals/{deal_id}", response_model=schemas.Deal)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    """Endpoint to get a single deal by its ID."""
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal

@app.post("/api/deals/{deal_id}/feedback", response_model=schemas.Feedback)
def create_feedback_for_deal(deal_id: int, feedback: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    """Endpoint to save feedback for a specific deal."""
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
    """
    Endpoint to upload a PDF, upload it to S3, analyze it with OpenAI,
    and save the results to the database.
    """
    text = services.extract_text_from_pdf(file.file)
    if not text:
        raise HTTPException(status_code=400, detail="Failed to extract text from PDF.")

    # Reset file stream pointer before uploading to S3
    file.file.seek(0)
    try:
        s3_url = services.upload_to_s3(file.file, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")

    analysis_data = services.analyze_document_text(text)
    if "error" in analysis_data:
        raise HTTPException(status_code=500, detail=analysis_data["error"])

    new_deal = models.Deal(
        file_name=file.filename,
        s3_url=s3_url,
        analysis_data=analysis_data
    )
    db.add(new_deal)
    db.commit()
    db.refresh(new_deal)
    
    return new_deal