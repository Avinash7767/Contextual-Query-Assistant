# Contextual Query Assistant

A FastAPI and Streamlit application for asking grounded questions about PDF documents. It extracts page text with PyMuPDF, preserves citation metadata while chunking, retrieves relevant chunks with OpenAI embeddings and FAISS, and asks OpenAI for strict structured JSON answers.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `.env`, then run the API and UI in separate terminals. The FastAPI backend reads the key for embeddings and answers; the Flask frontend reads `API_URL` to connect to that backend:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
API_URL=http://localhost:8000/api
```

```powershell
python run.py
streamlit run frontend/streamlit_app.py
```

Open the Streamlit URL shown by the command. The API exposes `GET /health`, `POST /api/documents` for PDF uploads, and `POST /api/query` for JSON queries.

To use the Flask frontend instead, keep the API running and start a second terminal:

```powershell
python frontend/flask_app.py
```

Open http://localhost:5000. The Flask frontend connects to the FastAPI backend through `API_URL` (default: `http://localhost:8000/api`).

## Response behavior

Answers use only retrieved excerpts. Important claims include citations immediately after the claim, and structured fields and citation records are validated against locations present in the retrieved chunks. Missing information is returned as `Not available in the document.`

Run tests with:

```powershell
pytest
```
