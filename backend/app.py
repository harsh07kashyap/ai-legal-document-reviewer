from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import os
from pypdf import PdfReader

from langchain_logic import (
    extract_text_from_pdf,
    store_contract_clauses,
    store_legal_standards,
    retrieve_and_compare
)


app = FastAPI(title="AI Legal Reviewer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


LEGAL_CORPUS_PATH = "legal_corpus.pdf"

@app.on_event("startup")
def load_legal_corpus():
    """Load and store the legal standards corpus from a PDF once on startup."""
    if not os.path.exists(LEGAL_CORPUS_PATH):
        print("⚠️ Legal corpus file not found — please create 'legal_corpus.pdf'")
        return

    try:
        reader = PdfReader(LEGAL_CORPUS_PATH)
        legal_text = ""

        for page in reader.pages:
            text = page.extract_text()
            if text:
                legal_text += text + "\n"

        if not legal_text.strip():
            print("⚠️ PDF found but no readable text extracted.")
            return

        store_legal_standards(legal_text)
        print("✅ Legal corpus (PDF) initialized successfully!")

    except Exception as e:
        print(f"❌ Error reading legal corpus PDF: {e}")




@app.post("/upload")
async def upload_contract(file: UploadFile):
    """Upload PDF and store its embeddings."""
    try:
        document_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        # Save file temporarily
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Extract and store
        text = extract_text_from_pdf(file_path)
        store_contract_clauses(document_id, text)

        return {"message": "Document uploaded and stored successfully", "document_id": document_id}
    except Exception as e:
        print(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/compare")
async def compare_documents(
    document_id: str = Form(...),
    query: str = Form(...)
):
    """Compare uploaded document with legal corpus based on query."""
    try:
        result = retrieve_and_compare(document_id, query)
        return {"comparison_result": result}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)



@app.get("/")
def home():
    return {"message": "AI Legal Document Reviewer Backend is running 🚀"}
