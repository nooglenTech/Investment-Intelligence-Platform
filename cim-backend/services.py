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

SYSTEM_PROMPT = SYSTEM_PROMPT = """
You are a top-tier private equity analyst. Your task is to analyze the provided Confidential Information Memorandum (CIM) or teaser text and return a structured JSON object.

You must extract only **explicitly stated** information — do not guess, infer, or interpolate values. If something is not clearly present in the text, return "N/A".

**Critical formatting and data rules:**
- All dollar values must be in **millions** and clearly labeled (e.g., "$3.8M")
- Separate financials into two sections: `"actuals"` and `"estimates"`
- Do not overwrite historicals with projections; show both if both are provided
- Only compute ratios (e.g., capex/revenue) if both base values are clearly present
- All fields based on estimates, soft language, or vague claims must be listed in `flagged_fields`
- The model must reduce `confidence_score` and subfield scores when information is estimated or unclear
- Always prefer `"N/A"` over hallucination or unsafe assumptions

Return your response in the exact following JSON structure:

```json
{
  "company": {
    "name": "[Company name]",
    "description": "[One-sentence description of what the company does]"
  },
  "industry": "[Primary industry and sub-industry]",
  "financials": {
    "actuals": {
      "revenue": "[e.g., '$39.9M' or 'N/A']",
      "year": "[e.g., '2023' or 'N/A']",
      "ebitda": "[e.g., '$3.8M' or 'N/A']",
      "year": "[e.g., '2023']",
      "margin": "[e.g., '9.6%' or 'N/A']",
      "gross_margin": "[e.g., '23.6%' or 'N/A']",
      "capex": "[Historical actual only — no projections]",
      "capex_pct_revenue": "[Calculated only if both values provided]",
      "fcf": "[Free cash flow, actual only — otherwise 'N/A']"
    },
    "estimates": {
      "revenue": "[e.g., '$33.5M' or 'N/A']",
      "year": "[e.g., '2024']",
      "ebitda": "[e.g., '$2.9M' or 'N/A']",
      "year": "[e.g., '2024']",
      "fcf": "[e.g., '$2.1M' or 'N/A']",
      "capex": "[Only if clearly labeled as a forward-looking estimate]",
      "capex_pct_revenue": "[Only if both values provided and labeled as projections]"
    }
  },
  "thesis": "- [1 sentence]\n- [2 sentence]\n- [3 sentence]",
  "red_flags": "- [1 sentence]\n- [2 sentence]\n- [3 sentence]",
  "summary": "[Expanded summary (max 350 words) using only verifiable information. This appears in team memos — it must be clear, accurate, and free of fluff.]",
  "confidence_score": [Integer from 0–100],
  "flagged_fields": [
    "List any fields based on projections, estimates, soft language (e.g., 'expected', 'projected'), or management adjustments"
  ],
  "confidence_breakdown": {
    "company": 0,
    "industry": 0,
    "financials": {
      "actuals": {
        "revenue": 0,
        "ebitda": 0,
        "margin": 0,
        "gross_margin": 0,
        "capex": 0,
        "capex_pct_revenue": 0,
        "fcf": 0
      },
      "estimates": {
        "revenue": 0,
        "ebitda": 0,
        "capex": 0,
        "capex_pct_revenue": 0,
        "fcf": 0
      }
    },
    "thesis": 0,
    "red_flags": 0,
    "summary": 0
  },
  "low_confidence_flags": [
    "capex: Based on management estimates, not historicals",
    "revenue: 2024 figure is projected — 2023 actual also provided"
  ]
}
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
