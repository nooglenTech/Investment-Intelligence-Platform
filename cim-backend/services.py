import os
import json
import fitz  # PyMuPDF
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60.0)  # Added a 60-second timeout

# The System prompt now only contains the instructions
SYSTEM_PROMPT = """
You are a top-tier private equity analyst. Your task is to analyze the provided Confidential Information Memorandum (CIM) or teaser text and return a structured JSON object.

Your goal is to extract only **explicitly stated** information. You may not infer, estimate, or assume values that are not clearly supported by the document. If something is not clearly present, return \"N/A\".

The JSON object must follow this exact structure:

{
  "company": {
    "name": "[Name of the company]",
    "description": "[One-sentence description of what the company does]"
  },
  "industry": "[Primary industry and sub-industry]",
  "financials": {
    "revenue": "[Explicit value (e.g., '$120M', 'N/A')]",
    "ebitda": "[Explicit value or 'N/A']",
    "margin": "[Explicit EBITDA or operating margin (e.g., '21%') or 'N/A']",
    "gross_margin": "[Explicit gross margin value or 'N/A']",
    "capex": "[Only include reported, realized capital expenditures. Do NOT include forward-looking 'capex plans'. If no actuals are stated, return 'N/A']",
    "capex_pct_revenue": "[Only calculate if both capex and revenue are present and clearly stated. Otherwise return 'N/A']",
    "fcf": "[Free cash flow, if stated. Otherwise return 'N/A']"
  },
  "thesis": "- [1 sentence]\\n- [2 sentence]\\n- [3 sentence]",
  "red_flags": "- [1 sentence]\\n- [2 sentence]\\n- [3 sentence]",
  "summary": "[Concise paragraph under 200 words summarizing the investment opportunity using only verifiable information]",
  "confidence_score": [Integer from 0–100, representing % of fields extracted from clearly labeled data tables or numbers. Return 100 only if all numeric values were explicitly available.],
  "flagged_fields": ["List any fields that are based on soft language such as 'expected', 'targeted', 'estimated', or derived from context instead of explicit numbers. Otherwise return an empty array."],
  "confidence_breakdown": {
    "company": 0,
    "industry": 0,
    "financials": {
      "revenue": 0,
      "ebitda": 0,
      "margin": 0,
      "gross_margin": 0,
      "capex": 0,
      "capex_pct_revenue": 0,
      "fcf": 0
    },
    "thesis": 0,
    "red_flags": 0,
    "summary": 0
  },
  "low_confidence_flags": [
    "capex: Value appears to be from a capex *plan*, not actuals.",
    "revenue: Projected figure for 2025, not current revenue."
  ]
}

Rules:
- Do not use projected or aspirational values in place of actuals.
- Do not compute ratios unless both underlying figures are clearly provided.
- Do not use generic descriptive statements in place of financials.
- Use \"N/A\" aggressively when values are unclear, forward-looking, or absent.
- All outputs must be in clean, human-readable units (e.g., \"$135M\", \"23%\").
- If any value is estimated, forward-looking, or loosely inferred, include an explanation in `low_confidence_flags` and reduce the corresponding score in `confidence_breakdown`. Do not hallucinate figures. Always prefer \u201cN/A\u201d over guessing.

Your output will be parsed and displayed to investment professionals — avoid any hallucination or overconfidence. If in doubt, label the field as \"N/A\" and flag it in `flagged_fields`.
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

        response = client.chat.completions.create(
            model="gpt-4.1-nano",  # Using a cost-effective and capable model
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": truncated_text}
            ]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return {"error": "Failed to analyze document."}