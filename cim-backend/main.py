from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="CIM Analyzer API")

@app.get("/")
def read_root():
    return {"message": "Welcome! The CIM Analyzer API is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)