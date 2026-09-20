from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests
from flask import Flask, flash, redirect, render_template_string, request, url_for
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-development-secret")
API_URL = os.getenv("API_URL", "http://localhost:8000/api")

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Contextual Query Assistant</title>
  <style>
    :root { --ink:#172126; --muted:#66747b; --paper:#f5f1e9; --card:#fffdf8; --accent:#c85b3d; --line:#ded8ca; }
    * { box-sizing:border-box; }
    body { margin:0; color:var(--ink); background:linear-gradient(135deg,#f5f1e9 0%,#e8eee8 100%); font-family:Georgia,serif; }
    main { max-width:920px; margin:0 auto; padding:56px 22px 80px; }
    header { display:flex; justify-content:space-between; gap:24px; align-items:end; margin-bottom:36px; }
    h1 { margin:0; max-width:600px; font-size:clamp(2.5rem,6vw,5.5rem); line-height:.92; letter-spacing:-.04em; font-weight:500; }
    .kicker { color:var(--accent); font:700 .75rem/1.2 Arial,sans-serif; letter-spacing:.14em; text-transform:uppercase; }
    .panel { background:var(--card); border:1px solid var(--line); padding:26px; margin-top:18px; box-shadow:0 12px 30px #31443a0d; }
    label { display:block; margin-bottom:9px; font:700 .78rem Arial,sans-serif; letter-spacing:.08em; text-transform:uppercase; }
    input[type=file], textarea { width:100%; border:1px solid var(--line); background:#fff; padding:13px; font:1rem Georgia,serif; }
    textarea { min-height:120px; resize:vertical; }
    button { border:0; background:var(--accent); color:white; padding:13px 19px; cursor:pointer; font:700 .78rem Arial,sans-serif; letter-spacing:.08em; text-transform:uppercase; }
    button:hover { background:#a94731; }
    .row { display:grid; grid-template-columns:1fr auto; gap:14px; align-items:end; }
    .status { color:var(--muted); margin:12px 0 0; font: .95rem Arial,sans-serif; }
    .answer { white-space:pre-wrap; font-size:1.2rem; line-height:1.55; }
    .summary { color:#46545a; line-height:1.5; }
    .items { display:grid; gap:10px; }
    .item { border-left:3px solid var(--accent); padding:9px 13px; background:#f7f3eb; }
    .item strong { display:block; font:700 .78rem Arial,sans-serif; text-transform:uppercase; letter-spacing:.06em; }
    .citation { color:#8f432f; font: .88rem Arial,sans-serif; }
    .error { color:#a94731; font-family:Arial,sans-serif; }
    @media (max-width:650px) { header,.row { display:block; } header .kicker { margin-bottom:18px; display:block; } button { margin-top:12px; } }
  </style>
</head>
<body>
<main>
  <header><div><div class="kicker">Document intelligence</div><h1>Ask the document.</h1></div><div class="kicker">Grounded answers / precise citations</div></header>
  {% with messages = get_flashed_messages() %}{% if messages %}<div class="panel status">{{ messages[-1] }}</div>{% endif %}{% endwith %}
  <section class="panel">
    <form method="post" action="{{ url_for('upload') }}" enctype="multipart/form-data">
      <label for="document">Upload a PDF</label>
      <div class="row"><input id="document" name="document" type="file" accept="application/pdf" required><button type="submit">Index document</button></div>
    </form>
    {% if chunks %}<p class="status">{{ chunks }} chunks indexed and ready for questions.</p>{% endif %}
  </section>
  <section class="panel">
    <form method="post" action="{{ url_for('ask') }}">
      <label for="query">Your question</label>
      <textarea id="query" name="query" placeholder="What are the payment terms?" required>{{ query }}</textarea>
      <button type="submit">Ask question</button>
    </form>
  </section>
  {% if result %}
  <section class="panel"><div class="kicker">Answer / {{ result.confidence }} confidence</div><p class="answer">{{ result.answer }}</p></section>
  <section class="panel"><div class="kicker">Summary</div><p class="summary">{{ result.summary }}</p></section>
  {% if result.key_information %}<section class="panel"><div class="kicker">Structured information</div><div class="items">{% for item in result.key_information %}<div class="item"><strong>{{ item.field }}</strong>{{ item.value }}<div class="citation">{{ item.citation }}</div></div>{% endfor %}</div></section>{% endif %}
  {% if result.citations %}<section class="panel"><div class="kicker">Citations</div><div class="items">{% for citation in result.citations %}<div class="item">{{ citation.claim }}<div class="citation">{{ citation.location }}</div></div>{% endfor %}</div></section>{% endif %}
  {% endif %}
</main>
</body>
</html>
"""


def backend_error(response: requests.Response) -> str:
    try:
        return response.json().get("detail", response.text)
    except ValueError:
        return response.text or "The backend request failed."


def call_backend(method: str, url: str, **kwargs: Any) -> Optional[requests.Response]:
    try:
        return requests.request(method, url, **kwargs)
    except requests.RequestException:
        return None


@app.get("/")
def index() -> str:
    return render_template_string(PAGE, chunks=None, query="", result=None)


@app.post("/upload")
def upload() -> Any:
    document = request.files.get("document")
    if not document or not document.filename:
        flash("Choose a PDF document first.")
        return redirect(url_for("index"))
    response = call_backend("POST", f"{API_URL}/documents", files={"file": (document.filename, document.stream, document.mimetype)}, timeout=120)
    if response is None:
      flash("The FastAPI backend is not reachable. Start it on port 8000 first.")
    elif not response.ok:
        flash(f"Upload failed: {backend_error(response)}")
    else:
        flash(f"Indexed {response.json()['chunks']} chunks from {document.filename}.")
    return redirect(url_for("index"))


@app.post("/ask")
def ask() -> str:
    query = request.form.get("query", "").strip()
    response = call_backend("POST", f"{API_URL}/query", json={"query": query}, timeout=120)
    result: Optional[Dict[str, Any]] = response.json() if response is not None and response.ok else None
    if response is None:
      flash("The FastAPI backend is not reachable. Start it on port 8000 first.")
    elif not response.ok:
        flash(f"Query failed: {backend_error(response)}")
    return render_template_string(PAGE, chunks=None, query=query, result=result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("FLASK_PORT", "5000")), debug=True)
