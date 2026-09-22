"""Streamlit interface for batch resume analysis."""

import json

import streamlit as st

from document_extractor import ExtractionError, extract_text
from resume_parser import parse_resume


st.set_page_config(page_title="scanResume", page_icon="📄", layout="wide")
st.title("scanResume")
st.caption("Upload text-based resumes to extract structured candidate information locally.")

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
