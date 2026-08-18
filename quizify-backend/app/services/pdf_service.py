"""PDF ingestion: extract and clean text so it can be handed to the AI service."""
import re
from pathlib import Path
from typing import Tuple

import pdfplumber


def extract_text(filepath: Path) -> Tuple[str, int]:
    """Extract raw text from a PDF file.

    Returns (cleaned_text, page_count).
    """
    text_parts = []
    page_count = 0
    with pdfplumber.open(str(filepath)) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    raw_text = "\n".join(text_parts)
    return clean_text(raw_text), page_count


def clean_text(raw: str) -> str:
    """Collapse whitespace, drop page-number-only lines, normalize bullets."""
    lines = raw.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r"[\d\-\s]{1,6}", line):  # stray page numbers
            continue
        line = re.sub(r"\s+", " ", line)
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_sentences(text: str) -> list:
    """Very lightweight sentence splitter (avoids extra NLP dependency)."""
    text = text.replace("\n", " ")
    raw_sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 25]
    return sentences


def identify_key_terms(text: str, max_terms: int = 40) -> list:
    """Heuristic keyword/concept extraction: capitalized terms + noun-like
    repeated tokens. Used by the offline fallback AI generator, and as
    metadata even when a real LLM is used."""
    words = re.findall(r"\b[A-Za-z][A-Za-z\-]{3,}\b", text)
    freq = {}
    stop = {
        "this", "that", "with", "from", "have", "will", "which", "their",
        "such", "these", "those", "into", "your", "also", "about", "when",
        "where", "there", "then", "than", "each", "some", "more", "most",
        "other", "used", "uses", "using", "example", "chapter",
    }
    for w in words:
        lw = w.lower()
        if lw in stop:
            continue
        freq[lw] = freq.get(lw, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: -x[1])
    return [w for w, _ in ranked[:max_terms]]
