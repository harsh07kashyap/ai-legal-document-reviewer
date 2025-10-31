from pinecone import Pinecone
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import time
load_dotenv(override=True)
import os
import re
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter


pc=Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name="ai-legal-document-reviewer"
index = pc.Index(index_name)

llm=ChatGoogleGenerativeAI(model='gemini-2.5-flash', google_api_key=os.getenv("GOOGLE_API_KEY"))

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text.strip()

def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", "!", "?"]
    )
    chunks = text_splitter.split_text(text)
    return chunks

def store_legal_standards(legal_text: str):
    """Store the static legal corpus only once."""
    chunks = chunk_text(legal_text)
    records = []

    for i, chunk in enumerate(chunks):
        records.append({
            "id": f"legal-{i}",
            "text": chunk
        })

    index.upsert_records(namespace="legal-standards", records=records)
    print("Legal standards corpus stored successfully.")



def store_contract_clauses(document_id: str, logs: str):
    chunks = chunk_text(logs)
    records = []

    for i, chunk in enumerate(chunks):
        records.append({
            "id": f"{document_id}-{i}",
            "text": chunk
        })

    namespace = f"document-{document_id}"
    index.upsert_records(namespace=namespace, records=records)
    print(f"Stored document {document_id} in namespace {namespace}")



def retrieve_and_compare(document_id: str, query: str, top_k: int = 3):
    """Search both legal corpus and uploaded document, then compare results."""

    # Namespaces
    doc_namespace = f"document-{document_id}"
    legal_namespace = "legal-standards"

    # Search both spaces
    doc_results = index.search(
        namespace=doc_namespace,
        query={"inputs": {"text": query}, "top_k": top_k}
    )
    legal_results = index.search(
        namespace=legal_namespace,
        query={"inputs": {"text": query}, "top_k": top_k}
    )

    doc_hits = [hit["fields"]["text"] for hit in doc_results.get("result", {}).get("hits", [])]
    legal_hits = [hit["fields"]["text"] for hit in legal_results.get("result", {}).get("hits", [])]

    time.sleep(10)

    if not doc_hits and not legal_hits:
        return "No relevant matches found in either document or legal corpus."

    # Combine for comparison
    comparison_prompt = f"""
    You are a legal compliance AI.
    Compare the following:

    Contract sections:
    {doc_hits}

    Legal standards:
    {legal_hits}

    Query: "{query}"

    Output a summary showing:
    - Whether the contract aligns with legal standards
    - Missing or risky clauses
    - Recommendations for improvement
    
    Please provide a well-formatted response with no ** marks.
    """

    response = llm.invoke(comparison_prompt)
    print(response)
    return response
