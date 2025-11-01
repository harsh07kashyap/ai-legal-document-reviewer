
import streamlit as st
import requests
import os
import re

# 🌐 Backend URL (update if hosted elsewhere)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Legal Document Reviewer", layout="wide")

# --------------------------------------
# HEADER
# --------------------------------------
st.title("⚖️ AI Legal Document Reviewer")
st.info(
    "📘 Are you overwhelmed by long job contracts or complex legal documents? 🤯 "
    "Don't worry — this app helps you **understand your contract**, **spot missing or risky clauses**, "
    "and **check its alignment with the Indian Contract Act**.\n\n"
    "Just upload your **contract, NDA, or policy**, and get clear, reliable insights instantly!"
)

# --------------------------------------
# FILE UPLOAD
# --------------------------------------
st.header(" Step 1: Upload Contract")

uploaded_file = st.file_uploader("Upload your legal document (PDF)", type=["pdf"])

# ✅ Ensure correct path for sample PDF (works locally & in deployment)
sample_path = os.path.join(os.path.dirname(__file__), "sample_contract.pdf")

def upload_pdf(file_path, file_name="sample_contract.pdf"):
    with open(file_path, "rb") as f:
        files = {"file": (file_name, f, "application/pdf")}
        response = requests.post(f"{BACKEND_URL}/upload", files=files)
    return response


if uploaded_file:
    st.info("Uploading document... please wait ⏳")

    # Save temporarily
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Send to backend
    response = upload_pdf(uploaded_file.name, uploaded_file.name)

    if response.status_code == 200:
        data = response.json()
        document_id = data["document_id"]
        st.success(f"✅ Document '{uploaded_file.name}' uploaded and indexed successfully!")
        st.session_state["document_id"] = document_id
    else:
        st.error("❌ Failed to upload document.")

else:
    st.warning("Please upload a PDF to begin.")
    
    st.markdown("Or try it out instantly with our demo contract:")

    col1, col2 = st.columns([1, 1.2])

    with col1:
        try_sample = st.button("📄 Try with Sample Contract")

    with col2:
        if os.path.exists(sample_path):
            with open(sample_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Sample Contract",
                    data=f,
                    file_name="sample_contract.pdf",
                    mime="application/pdf",
                    help="Download a copy of the sample contract for review"
                )
        else:
            st.error("⚠️ Sample contract not found in app folder!")

    if try_sample:
        if os.path.exists(sample_path):
            st.info("Uploading sample contract... please wait ⏳")
            response = upload_pdf(sample_path)
            if response.status_code == 200:
                data = response.json()
                document_id = data["document_id"]
                st.success("✅ Sample contract uploaded and indexed successfully!")
                st.session_state["document_id"] = document_id
            else:
                st.error("❌ Failed to upload sample contract.")
        else:
            st.error("⚠️ Sample contract file missing — please add it to the frontend folder.")

# --------------------------------------
# QUERY SECTION
# --------------------------------------
if "document_id" in st.session_state:
    st.header("Step 2: Ask Legal Questions")

    query = st.text_input("Enter your question", placeholder="e.g., Does this contract have a termination clause?")

    compare_btn = st.button("Compare with Legal Standards")

    if compare_btn and query.strip():
        with st.spinner("Comparing document with legal corpus..."):
            res = requests.post(f"{BACKEND_URL}/compare", data={
                "document_id": st.session_state["document_id"],
                "query": query
            })

            if res.status_code == 200:
                data = res.json()
                response_text = data.get("comparison_result", "")

                if isinstance(response_text, dict) and "content" in response_text:
                    response_text = response_text["content"]

                response_text = response_text.strip()
                response_text = re.sub(r"•\s*\*\*", "• **", response_text)
                response_text = re.sub(r":•", ":", response_text)
                response_text = re.sub(r"\*\*\s*", "** ", response_text)
                response_text = re.sub(r"\n\s+", "\n", response_text)
                response_text = response_text.replace("•", "\n-")
                response_text = re.sub(
                    r"(Alignment with Legal Standards|Missing or Risky Clauses|Summary)",
                    r"### \1",
                    response_text
                )
                response_text = response_text.replace(". ", ".\n")
                response_text = response_text.replace(": ", ":\n")

                st.markdown("### ⚖️ AI Legal Review Result")
                st.markdown(response_text, unsafe_allow_html=True)
            else:
                st.error("Error comparing with legal norms.")
