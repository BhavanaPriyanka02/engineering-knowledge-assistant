from typing import Any

from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_DIMENSION = 384

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def generate_embeddings(chunks: list[str]) -> list[list[float]]:
    if not chunks:
        return []

    valid_chunks = [chunk for chunk in chunks if chunk and chunk.strip()]
    if not valid_chunks:
        return []

    model = get_embedding_model()
    embeddings = model.encode(valid_chunks, batch_size=32, convert_to_numpy=True, normalize_embeddings=True)
    vectors = embeddings.tolist()
    return [list(map(float, vector)) for vector in vectors]
