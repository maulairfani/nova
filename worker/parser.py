"""Parses a downloaded document into (title, chunks, format) — Markdown
(section-header split, same logic as mcp_servers/<unit>/seed/seed_qdrant.py)
or PDF (text extraction + fixed-size paragraph grouping, since PDFs have no
reliable heading structure to split on)."""
import io
import re

import pypdf

_MAX_PDF_CHUNK_CHARS = 1500


def _parse_markdown(text: str, filename: str) -> tuple[str, list[dict]]:
    title_match = re.match(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else filename

    sections = re.split(r"\n(?=##\s)", text)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section or section.startswith("# "):
            continue
        heading_match = re.match(r"^##\s+(.+)$", section)
        heading = heading_match.group(1).strip() if heading_match else title
        chunks.append({"text": section, "section_heading": heading, "chunk_index": len(chunks)})
    return title, chunks


def _parse_pdf(content: bytes, filename: str) -> tuple[str, list[dict]]:
    reader = pypdf.PdfReader(io.BytesIO(content))
    full_text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]

    chunks = []
    buffer = ""
    for paragraph in paragraphs:
        if buffer and len(buffer) + len(paragraph) > _MAX_PDF_CHUNK_CHARS:
            chunks.append({"text": buffer, "section_heading": None, "chunk_index": len(chunks)})
            buffer = paragraph
        else:
            buffer = f"{buffer}\n\n{paragraph}" if buffer else paragraph
    if buffer:
        chunks.append({"text": buffer, "section_heading": None, "chunk_index": len(chunks)})

    return filename, chunks


def parse_document(content: bytes, filename: str) -> tuple[str, list[dict], str]:
    if filename.lower().endswith(".pdf"):
        title, chunks = _parse_pdf(content, filename)
        return title, chunks, "pdf"
    title, chunks = _parse_markdown(content.decode("utf-8"), filename)
    return title, chunks, "markdown"
