import os
import json
import fitz
from openai import OpenAI
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=90.0)
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
s3_client = boto3.client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'), region_name=os.getenv('AWS_REGION'))

# *** THIS IS THE NEW, UPGRADED PROMPT ***
SYSTEM_PROMPT = """
You are a top-tier private equity analyst. Your task is to analyze a Confidential Information Memorandum (CIM) or teaser text and return a structured, highly detailed JSON object for investment committee review.

You must extract only **explicitly stated** information — do not guess, infer, or interpolate values. If something is not clearly present in the text, return "N/A".

This output will be read carefully by professional investors — your goal is to generate a usable investment summary, complete with red flags, growth signals, and risk-adjusted valuation inputs.

---

📌 GENERAL RULES:
- Use only **verifiable data** stated in the document.
- Do not interpret, speculate, or hallucinate.
- Always return "N/A" if data is incomplete or implied.
- All dollar values must be in **millions** and clearly labeled (e.g., "$5.3M").

---

📊 FINANCIAL FORMATTING RULES:
- Separate financials into `"actuals"` and `"estimates"`.
- Do NOT overwrite actuals with projections — show both if present.
- If both revenue and capex are available, compute `capex_pct_revenue`.
- Include **free cash flow (FCF)** only if stated — do not compute from EBITDA.
- Include both historical and projected **CAGR values** (if data allows).
- If growth rates are stated or computable, include them in the `growth` section.
- If valuation multiples (EBITDA, FCF, revenue) are provided, extract and flag them.

---

📈 GROWTH SECTION (UPDATED):

If at least two years of revenue or FCF data are available in either historical or projected sections, you MUST compute the CAGR using the standard compound growth formula.

Return a `growth` object with:

- `"historical_revenue_cagr"`: Use the earliest and latest historical revenue years (e.g., 2021–2023). Format: "X% (start year – end year)"
- `"projected_revenue_cagr"`: Use the earliest and latest projected years (e.g., 2024–2029). Same format.
- `"historical_fcf_cagr"` and `"projected_fcf_cagr"`: Same rule, if FCF is provided.
- `"growth_commentary"`: Write 1–3 sentences explaining growth patterns, inflection points, or revenue declines.

Only return "N/A" if there are fewer than 2 usable years for a given metric.
- If no historical or projected data is available, return "N/A" for both CAGRs.

---

⚠️ RISK, RED FLAGS, AND CONFIDENCE:
- Use `red_flags` to highlight anything that may affect risk or valuation.
- Flag **soft language**, **management adjustments**, **"expected"/"projected"** terms, etc.
- Adjust the `confidence_score` downward for vague or soft claims.
- Add any uncertain metrics to `flagged_fields` and explain in `low_confidence_flags`.

---

You MUST compute and return a top-level `"growth"` field in the output.

This field must include:
- `"historical_revenue_cagr"`: Calculate CAGR between earliest and latest **actual** revenue years.
- `"projected_revenue_cagr"`: Calculate CAGR between earliest and latest **estimate** revenue years.
- `"historical_fcf_cagr"` and `"projected_fcf_cagr"` if FCF is available.
- `"growth_commentary"`: Write 1–3 bullet points summarizing any trends, declines, inflection points, or reasons for stagnation.

⚠️ If a CAGR is negative, still include it. Do not skip.
⚠️ If only one data point exists, set the value to `"N/A"` but still include the field.

The final JSON must include this section. Do not omit it under any condition.


📝 STRUCTURED OUTPUT FORMAT:

```json
{
  "company": {
    "name": "[Company name]",
    "description": "[One-sentence high-level description]",
    "business_model": "[How the company makes money, e.g., SaaS subscriptions, project-based revenue, etc.]",
    "products_services": "[List of key products or services offered]",
    "customer_base": "[Description of the typical customer, e.g., SMBs, enterprise, specific demographics]"
  },
  "industry": "[Primary industry and sub-industry]",
  "financials": {
    "actuals": {
      "revenue": "[e.g., '$39.9M']", 
      "year": "[e.g., '2023']",
      "ebitda": "[e.g., '$3.8M']",
      "margin": "[e.g., '9.6%']",
      "gross_margin": "[e.g., '23.6%']",
      "capex": "[e.g., '$1.2M']",
      "capex_pct_revenue": "[e.g., '3.1%']",
      "fcf": "[e.g., '$2.5M']"
    },
    "estimates": {
      "revenue": "[e.g., '$45.2M']",
      "year": "[e.g., '2024']",
      "ebitda": "[e.g., '$5.1M']",
      "fcf": "[e.g., '$3.0M']",
      "capex": "[e.g., '$1.5M']",
      "capex_pct_revenue": "[e.g., '3.3%']"
    }
  },
    "growth": {
      "historical_revenue_cagr": "1.2% (2021–2023)",
      "projected_revenue_cagr": "-3.4% (2023–2024)",
      "historical_fcf_cagr": "N/A",
      "projected_fcf_cagr": "N/A",
      "growth_commentary": "- Revenue declined in 2023 and is projected to fall further in 2024.\\n- Projected CAGR is negative, indicating a period of potential contraction.\\n- Strong backlog may provide recovery buffer in out years."
},
  "thesis": "- [Bullet point 1]\\n- [Bullet point 2]\\n- [Bullet point 3]",
  "red_flags": "- [Bullet point 1]\\n- [Bullet point 2]\\n- [Bullet point 3]",
  "summary": "[Detailed summary (300–450 words), clear, data-rich, and free of fluff. Summarize financial performance, product model, customers, headwinds, and competitive position.]",
  "confidence_score": 0,
  "flagged_fields": ["List all vague, projected, or estimated fields"],
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
    "growth": 0,
    "thesis": 0,
    "red_flags": 0,
    "summary": 0
  },
  "low_confidence_flags": [
    "revenue: 2024 figure is projected based on management estimates",
    "capex: future year value provided with no historical baseline"
  ]
}
```
"""

# ... (rest of services.py remains the same)
def upload_to_s3(file_stream, file_name: str) -> str:
    if not S3_BUCKET: raise ValueError("S3_BUCKET_NAME not set.")
    try:
        s3_client.upload_fileobj(file_stream, S3_BUCKET, file_name)
        return f"https://{S3_BUCKET}.s3.amazonaws.com/{file_name}"
    except Exception as e: raise e

def delete_from_s3(file_name: str):
    if not S3_BUCKET: raise ValueError("S3_BUCKET_NAME not set.")
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=file_name)
    except Exception as e: print(f"Error deleting {file_name} from S3: {e}")

def create_presigned_url(file_name: str, expiration=3600) -> str:
    if not S3_BUCKET: raise ValueError("S3_BUCKET_NAME environment variable is not set.")
    try:
        response = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': file_name, 'ResponseContentDisposition': 'inline'}, ExpiresIn=expiration)
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None
    return response

def extract_text_from_pdf(file_stream) -> str:
    file_content = file_stream.read()
    file_stream.seek(0)
    doc = fitz.open(stream=file_content, filetype="pdf")
    text = "".join(page.get_text() for page in doc)
    doc.close()
    return text

def analyze_document_text(text: str) -> dict:
    try:
        truncated_text = text[:120000]
        response = client.chat.completions.create( model="gpt-4o-mini", response_format={"type": "json_object"}, messages=[ {"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": truncated_text} ] )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return {"error": "Failed to analyze document."}
