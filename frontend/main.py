import streamlit as st
import requests
import os


# 🌐 Backend URL (update if hosted elsewhere)
BACKEND_URL = (f"{os.getenv('BACKEND_URL')}" if os.getenv('BACKEND_URL') else "http://localhost:8000")

st.set_page_config(page_title="AI Legal Document Reviewer", layout="wide")

# --------------------------------------
# HEADER
# --------------------------------------
st.title("AI Legal Document Reviewer")
st.markdown("Upload a **contract, NDA, or policy document** to identify key clauses, risks, and legal compliance issues.")


# --------------------------------------
# FILE UPLOAD
# --------------------------------------
st.header(" Step 1: Upload Contract")

uploaded_file = st.file_uploader("Upload your legal document (PDF)", type=["pdf"])

if uploaded_file:
    st.info("Uploading document... please wait ⏳")

    # Save temporarily
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Send to backend
    with open(uploaded_file.name, "rb") as f:
        response = requests.post(f"{BACKEND_URL}/upload", files={"file": f})
    
    if response.status_code == 200:
        data = response.json()
        document_id = data["document_id"]
        st.success(f"✅ Document '{uploaded_file.name}' uploaded and indexed successfully!")
        st.session_state["document_id"] = document_id
    else:
        st.error("❌ Failed to upload document.")
else:
    st.warning("Please upload a PDF to begin.")


# --------------------------------------
# QUERY SECTION
# --------------------------------------
if "document_id" in st.session_state:
    st.header("Step 2: Ask Legal Questions")

    query = st.text_input("Enter your question", placeholder="e.g., Does this contract have a termination clause?")

    col1, = st.columns(1)  # notice the comma!
    with col1:
        compare_btn = st.button("Compare with Legal Standards")

    # --- Document Query ---
    # if query_btn and query.strip():
    #     with st.spinner("Retrieving relevant clauses..."):
    #         res = requests.post(f"{BACKEND_URL}/query", data={
    #             "document_id": st.session_state["document_id"],
    #             "query": query
    #         })
    #         if res.status_code == 200:
    #             results = res.json().get("results", [])
    #             st.subheader("📑 Relevant Clauses Found")
    #             for i, clause in enumerate(results):
    #                 st.markdown(f"**Clause {i+1}:** {clause}")
    #         else:
    #             st.error("Error fetching document results.")

    # --- Comparison Query ---
    if compare_btn and query.strip():
        with st.spinner("Comparing document with legal corpus..."):
            res = requests.post(f"{BACKEND_URL}/compare", data={
                "document_id": st.session_state["document_id"],
                "query": query
            })

            if res.status_code == 200:
                data = res.json()
                response_text = data.get("comparison_result", "")

                # Handle nested dicts (like {"content": "..."})
                if isinstance(response_text, dict) and "content" in response_text:
                    response_text = response_text["content"]

                # 🧹 Cleaning and Formatting
                import re
                response_text = response_text.strip()

                # Replace weird bullet patterns and spacing issues
                response_text = re.sub(r"•\s*\*\*", "• **", response_text)   # clean bullets
                response_text = re.sub(r":•", ":", response_text)            # remove bullet after colon
                response_text = re.sub(r"\*\*\s*", "** ", response_text)     # fix bold spacing
                response_text = re.sub(r"\n\s+", "\n", response_text)        # remove extra spaces
                response_text = response_text.replace("•", "\n-")            # use markdown dashes for bullets

                # Ensure key headings are formatted
                response_text = re.sub(
                    r"(Alignment with Legal Standards|Missing or Risky Clauses|Summary)",
                    r"### \1",
                    response_text
                )

                # Add line breaks for better readability
                response_text = response_text.replace(". ", ".\n")
                response_text = response_text.replace(": ", ":\n")

                # Final Display
                st.markdown("### ⚖️ AI Legal Review Result")
                st.markdown(response_text, unsafe_allow_html=True)

            else:
                st.error("Error comparing with legal norms.")

