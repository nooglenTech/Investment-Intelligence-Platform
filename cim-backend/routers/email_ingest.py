from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, Form
from sqlalchemy.orm import Session
import logging
import os
import hmac
import hashlib
from typing import Optional

# Import your existing services, schemas, and database configuration
# This has been changed from a relative import to an absolute import to fix the ImportError.
import services
import schemas
import database

router = APIRouter()

# For security, your Mailgun API key should be stored as an environment variable,
# not hardcoded in the source code.
MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY")

def verify_mailgun_webhook(token: str, timestamp: str, signature: str) -> bool:
    """
    Verifies the signature of the Mailgun webhook to ensure it's authentic.
    This is a critical security measure.
    """
    # If the API key isn't configured, we cannot verify the webhook.
    if not MAILGUN_API_KEY:
        logging.error("MAILGUN_API_KEY environment variable is not set. Cannot verify webhook.")
        # In a production environment, you should return False to reject the request.
        return False 
    
    # The signature is an HMAC-SHA256 hash of the timestamp and token, signed with your API key.
    hmac_digest = hmac.new(
        key=MAILGUN_API_KEY.encode(),
        msg=f"{timestamp}{token}".encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Use hmac.compare_digest for a secure, constant-time comparison.
    return hmac.compare_digest(hmac_digest, signature)

@router.post("/webhook", tags=["Email Ingestion"])
async def receive_email(
    request: Request,
    db: Session = Depends(database.get_db),
    # Mailgun sends these form fields for webhook verification.
    timestamp: Optional[str] = Form(None),
    token: Optional[str] = Form(None),
    signature: Optional[str] = Form(None),
    # Standard email fields from Mailgun.
    sender: Optional[str] = Form(None),
    recipient: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    body_plain: Optional[str] = Form(None, alias='body-plain'),
    # Mailgun provides the number of attachments.
    attachment_count: Optional[int] = Form(0, alias='attachment-count'),
):
    """
    This endpoint receives incoming emails from a Mailgun route.
    It verifies the request, processes attachments, and creates deals for valid CIMs.
    """
    # --- 1. Verify the Webhook Signature ---
    # It's highly recommended to enforce verification in a production environment.
    if all([timestamp, token, signature]):
        if not verify_mailgun_webhook(token, timestamp, signature):
            logging.warning("Mailgun webhook verification failed. Rejecting request.")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    else:
        # If signature fields are missing, log a warning. You might want to reject
        # these requests in production for maximum security.
        logging.warning("Mailgun signature fields not provided. Skipping verification.")

    logging.info(f"Received verified email from: {sender} to: {recipient} with subject: {subject}")

    # --- 2. Check for Attachments ---
    if not attachment_count or attachment_count == 0:
        logging.info("Email received, but it has no attachments to process.")
        return {"message": "Email received, no attachments found."}

    # --- 3. Process Each Attachment ---
    form_data = await request.form()
    deals_created = []

    for i in range(1, attachment_count + 1):
        attachment_field_name = f'attachment-{i}'
        if attachment_field_name in form_data:
            attachment_file: UploadFile = form_data[attachment_field_name]
            filename = attachment_file.filename
            file_content = await attachment_file.read()
            
            logging.info(f"Processing attachment: {filename}")

            try:
                # --- 4. Call the CIM Processing Service ---
                # This is the "chat call" that analyzes the document.
                extracted_data = services.process_cim(file_content=file_content, filename=filename)

                # --- 5. Check if it's a CIM and Create a Deal ---
                if extracted_data.get("is_cim"):
                    logging.info(f"Attachment '{filename}' identified as a CIM. Creating deal.")
                    
                    # Map the data extracted by the AI to your database schema.
                    deal_schema = schemas.DealCreate(
                        company_name=extracted_data.get("company_name", "N/A"),
                        industry=extracted_data.get("industry", "N/A"),
                        summary=extracted_data.get("summary", ""),
                        key_highlights=extracted_data.get("key_highlights", []),
                        financials=extracted_data.get("financials", {}),
                        score=extracted_data.get("score", 0),
                        # Note: user_id is not included here. Your database/model
                        # should handle cases where a deal is created by the system.
                        # This might involve making the user_id nullable or assigning
                        # it to a default system user.
                    )
                    
                    # Save the new deal to the database.
                    deal = services.create_deal(db=db, deal=deal_schema)
                    deals_created.append(deal.id)
                    logging.info(f"Successfully created deal with ID: {deal.id}")
                else:
                    logging.info(f"Attachment '{filename}' was processed but is not a CIM. Skipping deal creation.")

            except Exception as e:
                # Log errors but continue processing other attachments.
                logging.error(f"An error occurred while processing attachment {filename}: {e}", exc_info=True)
                continue

    if deals_created:
        return {"message": f"Successfully processed {attachment_count} attachment(s) and created {len(deals_created)} deal(s).", "deal_ids": deals_created}
    else:
        return {"message": "Attachments were processed, but no new CIMs were found to create deals."}
