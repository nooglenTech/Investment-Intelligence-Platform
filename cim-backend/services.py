import os
import json
import fitz  # PyMuPDF
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a top-tier private equity analyst. Your task is to analyze the following Confidential Information Memorandum (CIM) or teaser text and extract key details for investment review.

Return a JSON object with the following structure:

{
  "company": {
    "name": "[Name of the company]",
    "description": "[One-sentence description of what the company does]"
  },
  "industry": "[Primary industry and sub-industry]",
  "financials": {
    "revenue": "[e.g., $120M, CAGR: 12%]",
    "ebitda": "[e.g., $25M]",
    "margin": "[e.g., EBITDA Margin: 21%]",
    "gross_margin": "[e.g., 45% or N/A]",
    "capex": "[e.g., $3M or N/A]",
    "capex_pct_revenue": "[e.g., 2.5% or N/A]",
    "fcf": "[e.g., $15M or N/A]"
  },
  "thesis": "- [1 sentence]\\n- [2 sentence]\\n- [3 sentence]",
  "red_flags": "- [1 sentence]\\n- [2 sentence]\\n- [3 sentence]",
  "summary": "[Concise paragraph under 200 words summarizing the investment opportunity]",
  "mobile_friendly": "1. 📌 Company: [Company Name]\\n   🔍 Description: [One-liner]\\n\\n2. 📊 Financials:\\n   - Revenue: $XXXM (CAGR: X%)\\n   - EBITDA: $XXXM (Margin: X%)\\n   - Gross Margin: X%\\n   - Capex: $XXM (% of Revenue: X%)\\n   - FCF: $XXM",
  "confidence_score": [0–100]
}

Rules:
- Only include fields that are explicitly stated or confidently inferred from the text.
- Use "N/A" for any field that is not clearly present.
- Ensure all financial values are in consistent, human-readable units (e.g., "$125M", "20%", etc.).
- Keep all bullet points tight, decision-useful, and written in clear business English.

[BEGIN INPUT TEXT]
{{deck_text}}
[END INPUT TEXT]
"""

def extract_text_from_pdf(file_stream) -> str:
    """Extracts text from a PDF file stream."""
    try:
        doc = fitz.open(stream=file_stream.read(), filetype="pdf")
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return ""

def analyze_document_text(text: str) -> dict:
    """Sends document text to OpenAI for analysis."""
    try:
        # Truncate text to be safe with API token limits
        truncated_text = text[:120000]

        # Inject the text into the system prompt template
        formatted_prompt = SYSTEM_PROMPT.replace("{{deck_text}}", truncated_text)

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            response_format={"type": "json_object"},
            messages=[
                {"role": "user", "content": formatted_prompt}
            ]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return {"error": "Failed to analyze document."}