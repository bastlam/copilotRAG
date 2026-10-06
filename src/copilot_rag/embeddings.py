"""Embeddings 100 % locaux via sentence-transformers (chargement paresseux)."""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=2)
def _get_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def embed_texts(
    texts: list[str], model_name: str, batch_size: int = 64
) -> list[list[float]]:
    """Vectorise une liste de textes (vecteurs normalisés -> similarité cosinus)."""
    if not texts:
        return []
    model = _get_model(model_name)
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vectors.tolist()
