import os
import json
import fitz
from openai import OpenAI
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

# ... (client initializations remain the same) ...
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60.0)
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
s3_client = boto3.client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'), region_name=os.getenv('AWS_REGION'))

SYSTEM_PROMPT = """
[Your detailed system prompt remains the same]
"""

def upload_to_s3(file_stream, file_name: str) -> str:
    # ... (this function remains the same) ...
    if not S3_BUCKET:
        raise ValueError("S3_BUCKET_NAME environment variable is not set.")
    try:
        s3_client.upload_fileobj(file_stream, S3_BUCKET, file_name)
        return f"https://{S3_BUCKET}.s3.amazonaws.com/{file_name}"
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        raise

# *** NEW FUNCTION ***
def delete_from_s3(file_name: str):
    """Deletes a file from the S3 bucket."""
    if not S3_BUCKET:
        raise ValueError("S3_BUCKET_NAME environment variable is not set.")
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=file_name)
        print(f"Successfully deleted {file_name} from S3 bucket {S3_BUCKET}.")
    except ClientError as e:
        print(f"Error deleting {file_name} from S3: {e}")
        # Don't re-raise, as we still want to delete the DB record
    except Exception as e:
        print(f"An unexpected error occurred during S3 deletion: {e}")

def extract_text_from_pdf(file_stream) -> str:
    # ... (this function remains the same) ...
    file_content = file_stream.read()
    file_stream.seek(0)
    doc = fitz.open(stream=file_content, filetype="pdf")
    text = "".join(page.get_text() for page in doc)
    doc.close()
    return text

def analyze_document_text(text: str) -> dict:
    # ... (this function remains the same) ...
    truncated_text = text[:120000]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": truncated_text}
        ]
    )
    return json.loads(response.choices[0].message.content)
