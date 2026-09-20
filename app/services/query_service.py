from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Optional, Union

from openai import RateLimitError

from app.citation.citation_manager import validate_response
from app.config import Settings
from app.document.chunker import TextChunk, chunk_pages
from app.document.extractor import extract_pdf
from app.llm.openai_client import OpenAIClient
from app.models.response_model import QueryResponse


class QueryService:
    def __init__(self, settings: Settings, llm_client: Optional[OpenAIClient] = None):
        self.settings = settings
        self.llm_client = llm_client
        self.chunks: list[TextChunk] = []
        self._index = None
        self._vectors: list[list[float]] = []

    def ingest(self, path: Union[str, Path]) -> int:
        pages = extract_pdf(path)
        self.chunks = chunk_pages(pages, self.settings.chunk_size, self.settings.chunk_overlap)
        if self.llm_client:
            try:
                self._vectors = self.llm_client.embed([chunk.text for chunk in self.chunks])
            except RateLimitError:
                self._vectors = []
                self._index = None
                return len(self.chunks)
            try:
                import faiss
                import numpy as np
                matrix = np.asarray(self._vectors, dtype="float32")
                faiss.normalize_L2(matrix)
                self._index = faiss.IndexFlatIP(matrix.shape[1])
                self._index.add(matrix)
            except ImportError:
                self._index = None
        return len(self.chunks)

    def _lexical_search(self, query: str, limit: int) -> list[TextChunk]:
        terms = set(re.findall(r"\w+", query.lower()))
        ranked = sorted(self.chunks, key=lambda chunk: len(terms & set(re.findall(r"\w+", chunk.text.lower()))), reverse=True)
        return ranked[:limit]

    def retrieve(self, query: str, limit: int = 5) -> list[TextChunk]:
        if not self.chunks:
            return []
        if self._index is not None and self.llm_client:
            import numpy as np
            vector = np.asarray(self.llm_client.embed([query]), dtype="float32")
            import faiss
            faiss.normalize_L2(vector)
            _, indices = self._index.search(vector, min(limit, len(self.chunks)))
            return [self.chunks[index] for index in indices[0] if index >= 0]
        return self._lexical_search(query, limit)

    def query(self, query: str, limit: int = 5) -> QueryResponse:
        matches = self.retrieve(query, limit)
        if not matches:
            return QueryResponse(query=query, answer="Not available in the document.", summary="Not available in the document.", confidence="Low")
        if not self.llm_client:
            return QueryResponse(query=query, answer="LLM configuration is unavailable.", summary="An OpenAI API key is required to generate an answer.", confidence="Low")
        excerpts = [(chunk.citation, chunk.text) for chunk in matches]
        try:
            result = QueryResponse.model_validate(self.llm_client.answer(query, excerpts))
        except RateLimitError:
            first_chunk = matches[0]
            fallback = f"Relevant document text: {first_chunk.text} [{first_chunk.citation}]"
            return QueryResponse(
                query=query,
                answer=fallback,
                summary=f"The answer is based on the most relevant available document excerpt [{first_chunk.citation}].",
                key_information=[{"field": "Relevant excerpt", "value": first_chunk.text, "citation": first_chunk.citation}],
                citations=[{"claim": "Relevant document excerpt", "location": first_chunk.citation}],
                confidence="Low",
            )
        return validate_response(result, matches)
