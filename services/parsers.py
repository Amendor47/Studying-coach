"""Utility functions to extract text from various document types."""

from __future__ import annotations

from pathlib import Path
from typing import Callable


def extract_text_from_pdf(path: str) -> str:
    """Return text extracted from a PDF file."""
    from pdfminer.high_level import extract_text

    return extract_text(path)


def extract_text_from_docx(path: str) -> str:
    """Return text extracted from a DOCX file."""
    from docx import Document

    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text_from_txt_md(path: str) -> str:
    """Return text extracted from a plain text or markdown file."""
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()


EXTRACTORS: dict[str, Callable[[str], str]] = {
    ".pdf": extract_text_from_pdf,
    ".docx": extract_text_from_docx,
    ".txt": extract_text_from_txt_md,
    ".md": extract_text_from_txt_md,
}


def extract_text(path: str, filename: str) -> str:
    """Route to the proper extractor based on file extension."""
    ext = Path(filename).suffix.lower()
    func = EXTRACTORS.get(ext)
    if not func:
        raise ValueError(f"unsupported file type: {ext}")
    return func(path)
