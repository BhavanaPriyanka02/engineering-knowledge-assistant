from typing import Any

from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.services.embedding_service import get_embedding_model


def search_user_knowledge(db: Session, user_id: int, query: str, top_k: int = 5) -> list[dict[str, Any]]:
    model = get_embedding_model()
    query_embedding = model.encode([query], normalize_embeddings=True)[0].tolist()
    query_vector = [float(value) for value in query_embedding]

    distance_expr = KnowledgeChunk.embedding.cosine_distance(query_vector)

    results = (
        db.query(
            KnowledgeChunk.id.label("chunk_id"),
            KnowledgeChunk.source_type,
            KnowledgeChunk.source_id,
            KnowledgeChunk.source_name,
            KnowledgeChunk.source_path,
            KnowledgeChunk.chunk_index,
            KnowledgeChunk.content,
            (1 - distance_expr).label("similarity_score"),
        )
        .filter(KnowledgeChunk.user_id == user_id)
        .order_by(distance_expr.asc())
        .limit(top_k)
        .all()
    )

    return [
        {
            "chunk_id": row.chunk_id,
            "source_type": row.source_type,
            "source_id": row.source_id,
            "source_name": row.source_name,
            "source_path": row.source_path,
            "chunk_index": row.chunk_index,
            "content": row.content,
            "similarity_score": float(row.similarity_score),
        }
        for row in results
    ]
