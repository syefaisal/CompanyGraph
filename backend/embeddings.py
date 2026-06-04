"""Local semantic embeddings for the hybrid search semantic arm.

Uses sentence-transformers (all-MiniLM-L6-v2) so search works fully offline
with no API key. The model loads lazily on first use and per-text vectors are
cached so repeated searches over the same corpus don't re-encode.

If sentence-transformers is not installed the module degrades gracefully:
`is_available()` returns False and the caller falls back to pure BM25.
"""

import math
import os

_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

_model = None
_model_failed = False
_cache: dict[str, list[float]] = {}


def is_available() -> bool:
    """Whether the embedding model can be loaded (lazily attempts the import/load)."""
    return _get_model() is not None


def _get_model():
    global _model, _model_failed
    if _model is not None or _model_failed:
        return _model
    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(_MODEL_NAME)
    except Exception:
        # Missing dependency or model download failure -> caller falls back to BM25.
        _model_failed = True
        _model = None
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts, using a per-text cache. Returns [] if unavailable."""
    model = _get_model()
    if model is None:
        return []

    missing = [t for t in texts if t not in _cache]
    if missing:
        vectors = model.encode(missing, normalize_embeddings=True)
        for text, vec in zip(missing, vectors):
            _cache[text] = [float(x) for x in vec]
    return [_cache[t] for t in texts]


def embed_query(text: str) -> list[float]:
    """Embed a single query string. Returns [] if unavailable."""
    result = embed_texts([text])
    return result[0] if result else []


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity. Vectors from `embed_*` are already L2-normalized."""
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
