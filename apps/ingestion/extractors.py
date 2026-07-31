"""Text extraction for the supported enterprise document formats."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ExtractedPage:
    page_number: int | None
    text: str


def extract_pages(path: Path) -> list[ExtractedPage]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return [
            ExtractedPage(page_number=index + 1, text=(page.extract_text() or ""))
            for index, page in enumerate(reader.pages)
        ]
    if suffix == ".docx":
        from docx import Document

        document = Document(str(path))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        return [ExtractedPage(page_number=None, text=text)]
    if suffix in {".md", ".markdown", ".txt"}:
        return [ExtractedPage(page_number=None, text=path.read_text(encoding="utf-8"))]
    raise ValueError(f"Unsupported document extension: {path.suffix}")
