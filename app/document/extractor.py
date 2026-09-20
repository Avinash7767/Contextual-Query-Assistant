from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

import fitz


@dataclass(frozen=True)
class DocumentPage:
    page_number: int
    text: str


def extract_pdf(path: Union[str, Path]) -> list[DocumentPage]:
    """Extract one normalized text record per PDF page."""
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF documents are supported")

    pages: list[DocumentPage] = []
    with fitz.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").replace("\r\n", "\n").replace("\r", "\n").strip()
            pages.append(DocumentPage(page_number=page_number, text=text))
    return pages
