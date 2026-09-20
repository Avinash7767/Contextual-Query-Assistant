from __future__ import annotations

import json
import os

import requests
import streamlit as st

st.set_page_config(page_title="Contextual Query Assistant", page_icon="📄", layout="centered")
st.title("Contextual Query Assistant")
st.caption("Upload a document, ask a question, and inspect the supporting citations.")
api_url = st.sidebar.text_input("API URL", os.getenv("API_URL", "http://localhost:8000/api"))

uploaded = st.file_uploader("PDF document", type=["pdf"])
if uploaded and st.button("Index document", type="primary"):
    response = requests.post(f"{api_url}/documents", files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")}, timeout=120)
    if response.ok:
        st.success(f"Indexed {response.json()['chunks']} chunks")
    else:
        st.error(response.text)

query = st.text_area("Question", placeholder="What are the payment terms?")
if st.button("Ask", disabled=not query.strip()):
    response = requests.post(f"{api_url}/query", json={"query": query}, timeout=120)
    if response.ok:
        data = response.json()
        st.subheader("Answer")
        st.write(data["answer"])
        st.subheader("Summary")
        st.write(data["summary"])
        st.subheader("Structured information")
        st.json(data["key_information"])
        st.subheader("Citations")
        st.json(data["citations"])
        st.caption(f"Confidence: {data['confidence']}")
    else:
        st.error(response.text)
