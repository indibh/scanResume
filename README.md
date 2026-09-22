# scanResume

`scanResume` is a local Streamlit application for batch resume analysis. It accepts text-based PDF files and Microsoft Word `.doc`/`.docx` files, extracts their text, and produces deterministic JSON for each candidate.

## Run locally

```bash
cd scanResume
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Upload one or more resumes in the browser. The app displays each result and provides a combined `scanresume_results.json` download.

## Output schema

Each result contains:

- `filename`
- `total_experience_years`
- `companies`: company, title, start/end dates, and duration
- `skills`: grouped programming languages, frameworks/libraries, databases, cloud/DevOps, and analytics/tools
- `education`: degree, institution, field, and start/end dates

The parser is intentionally local and rule-based. It does not send documents to an external service. Image-only PDFs are not supported in this first version because OCR is not included.
