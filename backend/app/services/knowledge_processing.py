import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile
from app.services.chunking import chunk_text
from app.services.embedding_service import generate_embeddings

logger = logging.getLogger(__name__)


def truncate_metadata(value: str | None, length: int = 512) -> str | None:
    if value is None:
        return None
    return value[:length]


def _delete_document_chunks(db: Session, document: Document) -> None:
    db.query(KnowledgeChunk).filter(
        KnowledgeChunk.user_id == document.user_id,
        KnowledgeChunk.source_type == "document",
        KnowledgeChunk.source_id == document.id,
    ).delete(synchronize_session=False)


def _delete_repository_chunks(db: Session, repository: Repository) -> None:
    current_repository_file_ids = (
        db.query(RepositoryFile.id)
        .filter(RepositoryFile.repository_id == repository.id)
        .subquery()
    )

    db.query(KnowledgeChunk).filter(
        KnowledgeChunk.user_id == repository.user_id,
        KnowledgeChunk.source_type == "repository_file",
        (
            (KnowledgeChunk.repository_id == repository.id)
            | (KnowledgeChunk.source_id.in_(current_repository_file_ids))
        ),
    ).delete(synchronize_session=False)


def process_document_chunks(db: Session, document: Document) -> dict[str, Any]:
    if not document.extracted_text or not document.extracted_text.strip():
        return {"source_type": "document", "source_id": document.id, "chunks_created": 0}

    _delete_document_chunks(db, document)

    chunks = chunk_text(document.extracted_text)
    if not chunks:
        return {"source_type": "document", "source_id": document.id, "chunks_created": 0}

    chunk_contents = [chunk["content"] for chunk in chunks]
    embeddings = generate_embeddings(chunk_contents)
    if len(embeddings) != len(chunks):
        raise ValueError("Embedding count did not match the number of chunks.")

    records = [
        KnowledgeChunk(
            user_id=document.user_id,
            source_type="document",
            source_id=document.id,
            source_name=document.filename,
            source_path=document.file_path,
            content=chunk["content"],
            chunk_index=chunk["chunk_index"],
            embedding=embedding,
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]

    db.add_all(records)
    db.commit()
    return {"source_type": "document", "source_id": document.id, "chunks_created": len(records)}


def process_repository_chunks(db: Session, repository: Repository) -> dict[str, Any]:
    repository_files = (
        db.query(RepositoryFile)
        .filter(RepositoryFile.repository_id == repository.id)
        .order_by(RepositoryFile.file_path.asc())
        .all()
    )

    _delete_repository_chunks(db, repository)

    files_processed = 0
    chunks_created = 0

    for repository_file in repository_files:
        if not repository_file.content or not repository_file.content.strip():
            continue

        chunks = chunk_text(repository_file.content)
        if not chunks:
            continue

        files_processed += 1
        chunk_contents = [chunk["content"] for chunk in chunks]
        embeddings = generate_embeddings(chunk_contents)
        if len(embeddings) != len(chunks):
            raise ValueError(f"Embedding count did not match the number of chunks for file {repository_file.id}.")

        records = [
            KnowledgeChunk(
                user_id=repository.user_id,
                repository_id=repository.id,
                repository_file_id=repository_file.id,
                source_type="repository_file",
                source_id=repository_file.id,
                source_name=repository_file.file_name,
                source_path=repository_file.file_path,
                content=chunk["content"],
                chunk_index=chunk["chunk_index"],
                embedding=embedding,
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        db.add_all(records)
        chunks_created += len(records)

    db.commit()
    return {
        "source_type": "repository",
        "source_id": repository.id,
        "files_processed": files_processed,
        "chunks_created": chunks_created,
    }


def process_all_user_knowledge(db: Session, user_id: int) -> dict[str, Any]:
    docs = db.query(Document).filter(Document.user_id == user_id).all()
    repos = db.query(Repository).filter(Repository.user_id == user_id).all()

    document_chunks = 0
    repo_files_processed = 0
    repo_chunks = 0

    for document in docs:
        result = process_document_chunks(db, document)
        document_chunks += result["chunks_created"]

    for repository in repos:
        result = process_repository_chunks(db, repository)
        repo_files_processed += result["files_processed"]
        repo_chunks += result["chunks_created"]

    return {
        "documents_processed": len(docs),
        "repository_files_processed": repo_files_processed,
        "documents_chunks_created": document_chunks,
        "repository_chunks_created": repo_chunks,
        "total_chunks_created": document_chunks + repo_chunks,
    }
