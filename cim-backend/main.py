from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict
from starlette.responses import StreamingResponse

# Import the Clerk SDK and required types
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions

import models, schemas, services
from database import get_db

# --- Initialize Clerk SDK with explicit secret key ---
clerk_secret_key = os.getenv("CLERK_SECRET_KEY")
if not clerk_secret_key:
    raise ValueError("CLERK_SECRET_KEY environment variable not found. Please check your .env file.")

clerk = Clerk(bearer_auth=clerk_secret_key)

# --- Configure Authorized Parties / CORS Origins ---
# This list is now used for BOTH Clerk authentication and CORS.
AUTHORIZED_PARTIES = os.getenv("CLERK_AUTHORIZED_PARTIES", "http://localhost:3000,http://localhost:3001").split(',')


app = FastAPI(title="IIP API")

# --- CORRECTED CORS MIDDLEWARE ---
# We now pass the specific list of authorized origins instead of a wildcard.
# This is required when allow_credentials=True.
app.add_middleware(
    CORSMiddleware, 
    allow_origins=AUTHORIZED_PARTIES, # Use the specific list of origins
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# --- Custom Dependency for Clerk Authentication with Debugging ---
def get_current_user(req: Request) -> Dict:
    """
    Authenticates a request using Clerk. Includes debugging output.
    If the request is authenticated, returns the session claims as a dictionary.
    If not, raises an HTTPException.
    """
    print("\n--- Clerk Auth Debug ---")
    origin = req.headers.get('origin')
    print(f"Request Origin: {origin}")
    print(f"Allowed Parties: {AUTHORIZED_PARTIES}")
    
    # This check is now implicitly handled by the CORSMiddleware, but we keep the log for clarity.
    if origin not in AUTHORIZED_PARTIES:
        print("Warning: Request Origin may not be in the configured AUTHORIZED_PARTIES list.")

    try:
        options = AuthenticateRequestOptions(authorized_parties=AUTHORIZED_PARTIES)
        request_state = clerk.authenticate_request(req, options)
        
        if not request_state.is_signed_in:
            print(f"Clerk: Token validation failed. Reason: {getattr(request_state, 'reason', 'Unknown')}")
            print("--- End Clerk Auth Debug ---\n")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        
        print("Clerk: Authentication successful.")
        print("--- End Clerk Auth Debug ---\n")
        return request_state.payload

    except Exception as e:
        print(f"Clerk: An exception occurred during authentication: {e}")
        print("--- End Clerk Auth Debug ---\n")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication error: {e}")

# --- PROTECTED ENDPOINTS ---

@app.get("/api/deals", response_model=List[schemas.Deal])
def get_all_deals(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    deals = db.query(models.Deal).order_by(models.Deal.id.desc()).all()
    return deals

@app.post("/analyze/", response_model=schemas.Deal)
def analyze_document(current_user: dict = Depends(get_current_user), file: UploadFile = File(...), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID (sub) not found in token")

    text = services.extract_text_from_pdf(file.file)
    if not text: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to extract text from PDF.")
    
    file.file.seek(0)
    
    try:
        s3_url = services.upload_to_s3(file.file, file.filename)
    except Exception as e: 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"S3 upload failed: {e}")
        
    analysis_data = services.analyze_document_text(text)
    if "error" in analysis_data: 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=analysis_data["error"])
    
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
def create_feedback_for_deal(deal_id: int, feedback: schemas.FeedbackCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID (sub) not found in token")

    db_deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if db_deal is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    
    db_feedback = models.Feedback(**feedback.dict(), deal_id=deal_id, user_id=user_id)
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
    if deal is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
        
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
