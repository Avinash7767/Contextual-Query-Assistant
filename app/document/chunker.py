from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.document.extractor import DocumentPage


@dataclass(frozen=True)
class TextChunk:
    text: str
    page_number: int
    section: Optional[str]
    paragraph_number: int
    start_line: int
    end_line: int

    @property
    def citation(self) -> str:
        if self.section:
            return f"Page {self.page_number}, Section: {self.section}"
        if self.start_line != self.end_line:
            return f"Page {self.page_number}, Lines {self.start_line}-{self.end_line}"
        return f"Page {self.page_number}, Line {self.start_line}"


def _section_for(paragraph: str, current: Optional[str]) -> Optional[str]:
    cleaned = paragraph.strip()
    if len(cleaned) <= 100 and not cleaned.endswith((".", ":", ";")):
        return cleaned
    return current


def chunk_pages(pages: list[DocumentPage], chunk_size: int = 1200, chunk_overlap: int = 200) -> list[TextChunk]:
    if chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and chunk_overlap must be smaller")

    chunks: list[TextChunk] = []
    for page in pages:
        paragraphs = [part.strip() for part in page.text.split("\n\n") if part.strip()]
        section: Optional[str] = None
        for paragraph_number, paragraph in enumerate(paragraphs, start=1):
            section = _section_for(paragraph, section)
            lines = paragraph.splitlines() or [paragraph]
            for start in range(0, len(paragraph), chunk_size - chunk_overlap):
                text = paragraph[start : start + chunk_size].strip()
                if not text:
                    continue
                start_line = min(len(lines), max(1, paragraph[:start].count("\n") + 1))
                end_line = min(len(lines), start_line + text.count("\n"))
                chunks.append(TextChunk(text, page.page_number, section, paragraph_number, start_line, end_line))
                if start + chunk_size >= len(paragraph):
                    break
    return chunks
