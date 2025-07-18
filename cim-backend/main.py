from fastapi import FastAPI, Depends, UploadFile, File
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy.sql import insert
import models
import services

# Load environment variables from the .env file
load_dotenv()

# Create the database tables on startup
models.metadata.create_all(models.engine)

# Dependency to get a database connection
def get_db_conn():
    return models.engine.connect()

app = FastAPI(title="CIM Analyzer API")

@app.get("/")
def read_root():
    return {"message": "Welcome! The CIM Analyzer API is running."}

@app.post("/analyze/")
def analyze_document(
    conn: Session = Depends(get_db_conn), 
    file: UploadFile = File(...)
):
    """
    This endpoint accepts a PDF file, extracts text, analyzes it with AI,
    saves the result to the database, and returns the analysis.
    """
    # 1. Extract text from the PDF
    text = services.extract_text_from_pdf(file.file)
    if not text:
        return {"error": "Failed to extract text from PDF."}

    # 2. Analyze text with OpenAI
    analysis_data = services.analyze_document_text(text)
    if "error" in analysis_data:
        return analysis_data

    # 3. Save the result to the database
    stmt = insert(models.deals).values(
        file_name=file.filename,
        analysis_data=analysis_data
    )
    result_proxy = conn.execute(stmt)
    conn.commit()
    conn.close()
    
    # 4. Return the analysis
    return {
        "deal_id": result_proxy.inserted_primary_key[0],
        "file_name": file.filename,
        "analysis": analysis_data
    }

# This block runs the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)