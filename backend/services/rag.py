"""
Lightweight RAG using FAISS (flat index) + sentence-transformers.
The index is built once at startup from the local knowledge base.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

import numpy as np

_KB_DIR = Path(__file__).parent.parent / "data" / "knowledge_base"
_CHUNK_WORDS = 250        # approximate words per chunk
_OVERLAP_WORDS = 50       # word overlap between consecutive chunks


class Chunk(NamedTuple):
    text: str
    source: str


# ── Module-level singletons (initialised lazily on first import) ──────────────
_chunks: list[Chunk] = []
_index = None          # faiss.IndexFlatIP
_embedder = None       # SentenceTransformer


def _word_chunks(text: str, source: str) -> list[Chunk]:
    """Split text into overlapping word-window chunks."""
    words = text.split()
    results: list[Chunk] = []
    step = _CHUNK_WORDS - _OVERLAP_WORDS
    for i in range(0, len(words), step):
        chunk_words = words[i : i + _CHUNK_WORDS]
        results.append(Chunk(text=" ".join(chunk_words), source=source))
        if i + _CHUNK_WORDS >= len(words):
            break
    return results


def _load_chunks() -> list[Chunk]:
    chunks: list[Chunk] = []
    for txt_file in sorted(_KB_DIR.glob("*.txt")):
        content = txt_file.read_text(encoding="utf-8")
        chunks.extend(_word_chunks(content, txt_file.stem))
    return chunks


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def build_index() -> None:
    """Build the FAISS index. Called once at server startup."""
    import faiss

    global _chunks, _index

    _chunks = _load_chunks()
    if not _chunks:
        return

    embedder = _get_embedder()
    texts = [c.text for c in _chunks]
    vectors = embedder.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    vectors = vectors.astype(np.float32)

    dim = vectors.shape[1]
    _index = faiss.IndexFlatIP(dim)   # Inner product = cosine on unit vectors
    _index.add(vectors)               # type: ignore[arg-type]


def retrieve(query: str, top_k: int = 3) -> list[str]:
    """Return top-k chunk texts most relevant to *query*."""
    if _index is None or not _chunks:
        return []

    embedder = _get_embedder()
    q_vec = embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    q_vec = q_vec.astype(np.float32)

    _, indices = _index.search(q_vec, top_k)  # type: ignore[attr-defined]
    return [_chunks[i].text for i in indices[0] if i < len(_chunks)]
