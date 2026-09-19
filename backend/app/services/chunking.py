import re
from typing import Any


def normalize_text(text: str) -> str:
    if text is None:
        return ""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n +", "\n", normalized)
    normalized = re.sub(r" +\n", "\n", normalized)
    return normalized.strip()


def chunk_text(text: str, chunk_size: int = 800) -> list[dict[str, Any]]:
    cleaned = normalize_text(text)
    if not cleaned:
        return []

    words = cleaned.split()
    if not words:
        return []

    chunks: list[dict[str, Any]] = []
    current: list[str] = []
    current_length = 0

    for word in words:
        candidate_length = current_length + len(word) + (1 if current else 0)
        if current and candidate_length > chunk_size:
            content = " ".join(current)
            chunks.append({"chunk_index": len(chunks), "content": content})
            current = [word]
            current_length = len(word)
            continue

        current.append(word)
        current_length = len(" ".join(current))

    if current:
        chunks.append({"chunk_index": len(chunks), "content": " ".join(current)})

    return [chunk for chunk in chunks if chunk["content"].strip()]
