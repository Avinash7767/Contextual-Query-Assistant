from __future__ import annotations

import re

from app.document.chunker import TextChunk
from app.models.response_model import QueryResponse


_CITATION_RE = re.compile(r"\[([^\]]+)\]")


def validate_response(response: QueryResponse, chunks: list[TextChunk]) -> QueryResponse:
    valid_locations = {chunk.citation for chunk in chunks}
    citations = [item for item in response.citations if item.location in valid_locations]
    for item in response.key_information:
        if item.citation not in valid_locations:
            item.citation = "Citation unavailable"
    response.citations = citations
    return response


def citations_in(text: str) -> list[str]:
    return _CITATION_RE.findall(text)
