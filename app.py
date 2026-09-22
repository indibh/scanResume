"""Streamlit interface for batch resume analysis."""

import json

import streamlit as st

from document_extractor import ExtractionError, extract_text
from resume_parser import parse_resume


st.set_page_config(page_title="Resume Scanner", page_icon="📄", layout="wide")
st.markdown(
    """
    <style>
    :root {
        --resume-green: #2f855a;
        --resume-light-green: #eaf7ef;
        --resume-border: #b7dfc3;
    }

    .stApp {
        background: linear-gradient(135deg, #f8fdf9 0%, var(--resume-light-green) 100%);
    }

    .app-header {
        padding: 1.5rem 2rem;
        margin: 0 0 1.5rem;
        border: 1px solid var(--resume-border);
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.88);
        box-shadow: 0 8px 24px rgba(47, 133, 90, 0.10);
    }

    .app-header h1 {
        margin: 0;
        color: var(--resume-green);
        font-size: 2.5rem;
        letter-spacing: -0.03em;
    }

    .app-header p {
        margin: 0.45rem 0 0;
        color: #42634d;
        font-size: 1.05rem;
    }

    [data-testid="stFileUploader"] section {
        border: 2px dashed var(--resume-border);
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.72);
    }

    .stDownloadButton button {
        border: 0;
        color: white;
        background: var(--resume-green);
    }

    .stDownloadButton button:hover {
        color: white;
        background: #276749;
    }
    </style>
    <div class="app-header">
        <h1>Resume Scanner</h1>
        <p>Upload resumes and get structured candidate insights in seconds.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_files = st.file_uploader(
    "Upload resumes",
    type=["pdf", "doc", "docx"],
    accept_multiple_files=True,
    help="Supported formats: text-based PDF, legacy .doc, and .docx.",
)

if uploaded_files:
    results = []
    errors = []

    with st.spinner("Analyzing resumes..."):
        for uploaded_file in uploaded_files:
            try:
                text = extract_text(uploaded_file.name, uploaded_file.getvalue())
                result = parse_resume(uploaded_file.name, text)
                results.append(result)
            except ExtractionError as error:
                errors.append({"filename": uploaded_file.name, "error": str(error)})

    if errors:
        st.warning(f"{len(errors)} file(s) could not be processed.")
        for error in errors:
            st.error(f"{error['filename']}: {error['error']}")

    if results:
        st.subheader(f"Results ({len(results)})")
        for result in results:
            with st.expander(result["filename"], expanded=True):
                st.json(result)

        st.download_button(
            "Download combined JSON",
            data=json.dumps(results, indent=2),
            file_name="scanresume_results.json",
            mime="application/json",
        )
else:
    st.info("Choose one or more resumes to begin.")
