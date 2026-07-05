"""
Document chunker — reads markdown files and splits them into
small, self-contained chunks with metadata for citation.
"""

import os
import re
from dataclasses import dataclass, field


@dataclass
class Chunk:
    """A single text chunk with its source metadata."""
    text: str
    source_file: str
    chunk_index: int
    heading: str = ""

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "source_file": self.source_file,
            "chunk_index": self.chunk_index,
            "heading": self.heading,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Chunk":
        return cls(**d)


def _extract_heading(text: str) -> str:
    """Extract the first markdown heading from text, if any."""
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.startswith("#"):
            return re.sub(r"^#+\s*", "", line).strip()
    return ""


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Recursively split text into chunks of approximately `chunk_size` characters
    with `chunk_overlap` overlap. Tries to split on paragraph breaks first,
    then sentence breaks, then word breaks.
    """
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    # Try splitting on double newlines (paragraphs) first
    separators = ["\n\n", "\n", ". ", " "]

    for sep in separators:
        parts = text.split(sep)
        if len(parts) <= 1:
            continue

        chunks = []
        current = ""

        for part in parts:
            # If adding this part would exceed chunk_size, save current and start new
            candidate = current + sep + part if current else part
            if len(candidate) > chunk_size and current:
                chunks.append(current.strip())
                # Start new chunk with overlap from end of previous
                overlap_start = max(0, len(current) - chunk_overlap)
                current = current[overlap_start:] + sep + part
            else:
                current = candidate

        if current.strip():
            chunks.append(current.strip())

        if len(chunks) > 1:
            return chunks

    # Fallback: hard split by character
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - chunk_overlap
    return chunks


def load_and_chunk_documents(
    documents_dir: str,
    chunk_size: int = 800,
    chunk_overlap: int = 200,
) -> list[Chunk]:
    """
    Read all .md files from `documents_dir`, split into chunks,
    and return a list of Chunk objects with metadata.
    """
    chunks: list[Chunk] = []

    if not os.path.isdir(documents_dir):
        raise FileNotFoundError(f"Documents directory not found: {documents_dir}")

    md_files = sorted(
        f for f in os.listdir(documents_dir) if f.endswith(".md")
    )

    if not md_files:
        raise ValueError(f"No .md files found in {documents_dir}")

    for filename in md_files:
        filepath = os.path.join(documents_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        text_chunks = _split_text(content, chunk_size, chunk_overlap)

        for i, text in enumerate(text_chunks):
            heading = _extract_heading(text)
            chunks.append(Chunk(
                text=text,
                source_file=filename,
                chunk_index=i,
                heading=heading,
            ))

    return chunks
