# app/main.py

import os
import requests
from fastapi import FastAPI, UploadFile, File , APIRouter
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.scripts.extraction import extract_file
from app.scripts.document_summarizer import summarize_text_in_batches, save_summary


from app.scripts.ingestion import ingest_files

# ---------------------------
# FastAPI app initialization
# ---------------------------
app = FastAPI(title="KMRL Document Summarizer")
router = APIRouter(prefix="/api")
# ---------------------------
# Folders for storage
# ---------------------------
RAW_FOLDER = os.path.join("app", "data", "raw")
PROCESSED_FOLDER = os.path.join("app", "data", "processed")
SUMMARY_FOLDER = os.path.join("app", "data", "summaries")

# Ensure folders exist
os.makedirs(RAW_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_FOLDER, exist_ok=True)

# ---------------------------
# Root endpoint
# ---------------------------
@app.get("/")
def root():
    return {"message": "KMRL Document Summarizer API is running"}

# ---------------------------
# Upload local file
# ---------------------------
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a single document (pdf, docx, txt) to RAW_FOLDER and process it.
    """
    raw_path = os.path.join(RAW_FOLDER, file.filename)
    with open(raw_path, "wb") as f:
        f.write(await file.read())

    # Extract text
    text = extract_file(raw_path)
    processed_path = os.path.join(PROCESSED_FOLDER, os.path.splitext(file.filename)[0] + ".txt")
    with open(processed_path, "w", encoding="utf-8") as f:
        f.write(text)

    # Summarize using Gemini Flash 2.5 (batching)
    summary_text = summarize_text_in_batches(text)
    summary_path = save_summary(summary_text, os.path.splitext(file.filename)[0], SUMMARY_FOLDER)

    return {"processed_text": processed_path, "summary_file": summary_path}

# ---------------------------
# Upload document via URL
# ---------------------------
class DocumentURL(BaseModel):
    documents: str  # Accept single URL

@app.post("/upload_url/")
def upload_url(doc: DocumentURL):
    """
    Upload a PDF/DOCX/TXT from a public URL, process, and summarize it.
    """
    url = doc.documents
    filename = url.split("/")[-1].split("?")[0]  # Extract filename
    raw_path = os.path.join(RAW_FOLDER, filename)

    # Download file
    r = requests.get(url)
    if r.status_code != 200:
        return JSONResponse(status_code=400, content={"error": "Unable to fetch file from URL"})
    with open(raw_path, "wb") as f:
        f.write(r.content)

    # Extract text
    text = extract_file(raw_path)
    processed_path = os.path.join(PROCESSED_FOLDER, os.path.splitext(filename)[0] + ".txt")
    with open(processed_path, "w", encoding="utf-8") as f:
        f.write(text)

    # Summarize in batches
    summary_text = summarize_text_in_batches(text)
    summary_path = save_summary(summary_text, os.path.splitext(filename)[0], SUMMARY_FOLDER)

    return {"processed_text": processed_path, "summary_file": summary_path}

# ---------------------------
# Download summary
# ---------------------------
@app.get("/download_summary/{filename}")
def download_summary(filename: str):
    """
    Download a summary file from SUMMARY_FOLDER.
    """
    summary_path = os.path.join(SUMMARY_FOLDER, filename)
    if not os.path.exists(summary_path):
        return JSONResponse(status_code=404, content={"error": "File not found"})
    return FileResponse(summary_path, filename=os.path.basename(summary_path))

# ---------------------------
# Bulk ingestion endpoint
# ---------------------------
@app.post("/ingest_all/")
def ingest_all():
    """
    Ingest all files in RAW_FOLDER (bulk processing).
    """
    results = ingest_files(RAW_FOLDER, PROCESSED_FOLDER, SUMMARY_FOLDER)
    return {"status": "completed", "files": results}
