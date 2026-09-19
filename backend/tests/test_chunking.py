from uuid import uuid4

from app.db.database import SessionLocal
from app.models.document import Document
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile
from app.models.user import User
from app.services import knowledge_processing as knowledge_processing_service
from app.services.chunking import chunk_text


def _create_user(db):
    unique_id = uuid4().hex[:12]
    user = User(
        name=f"Test User {unique_id}",
        email=f"{unique_id}@example.com",
        hashed_password="hashed-password",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _mock_repo_processing(monkeypatch):
    monkeypatch.setattr(
        knowledge_processing_service,
        "chunk_text",
        lambda text: [
            {"content": f"chunk-{index}-{text[:8]}", "chunk_index": index}
            for index in range(2)
        ],
    )
    monkeypatch.setattr(
        knowledge_processing_service,
        "generate_embeddings",
        lambda chunks: [[0.1] * 384 for _ in chunks],
    )


def test_chunk_text_returns_ordered_non_empty_chunks():
    text = "word " * 1200
    chunks = chunk_text(text, chunk_size=500)

    assert chunks
    assert all(chunk["content"].strip() for chunk in chunks)
    assert [chunk["chunk_index"] for chunk in chunks] == list(range(len(chunks)))
    assert "" not in [chunk["content"] for chunk in chunks]


def test_process_document_chunks_replaces_previous_chunks(monkeypatch):
    _mock_repo_processing(monkeypatch)
    db = SessionLocal()
    try:
        user = _create_user(db)
        document = Document(
            user_id=user.id,
            filename="sample.txt",
            file_path="/tmp/sample.txt",
            file_type="txt",
            extracted_text="alpha beta gamma delta",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        first_result = knowledge_processing_service.process_document_chunks(db, document)
        second_result = knowledge_processing_service.process_document_chunks(db, document)

        rows = (
            db.query(KnowledgeChunk)
            .filter(
                KnowledgeChunk.user_id == user.id,
                KnowledgeChunk.source_type == "document",
                KnowledgeChunk.source_id == document.id,
            )
            .all()
        )

        assert first_result["chunks_created"] == 2
        assert second_result["chunks_created"] == 2
        assert len(rows) == 2
    finally:
        db.close()


def test_process_repository_chunks_replaces_previous_chunks_for_repository(monkeypatch):
    _mock_repo_processing(monkeypatch)
    db = SessionLocal()
    try:
        user = _create_user(db)
        repository = Repository(
            user_id=user.id,
            repo_url="https://example.com/repo",
            repo_name="repo-duplicate-test",
            local_path="/tmp/repo-duplicate-test",
            repository_type="project",
        )
        db.add(repository)
        db.commit()
        db.refresh(repository)

        old_files = [
            RepositoryFile(
                repository_id=repository.id,
                file_path="src/a.py",
                file_name="a.py",
                file_extension=".py",
                content="print('first')",
            ),
            RepositoryFile(
                repository_id=repository.id,
                file_path="src/b.py",
                file_name="b.py",
                file_extension=".py",
                content="print('second')",
            ),
        ]
        db.add_all(old_files)
        db.commit()
        for file in old_files:
            db.refresh(file)

        first_result = knowledge_processing_service.process_repository_chunks(db, repository)
        assert first_result["chunks_created"] == 4

        for file in old_files:
            db.delete(file)
        db.commit()

        new_files = [
            RepositoryFile(
                repository_id=repository.id,
                file_path="src/c.py",
                file_name="c.py",
                file_extension=".py",
                content="print('third')",
            ),
            RepositoryFile(
                repository_id=repository.id,
                file_path="src/d.py",
                file_name="d.py",
                file_extension=".py",
                content="print('fourth')",
            ),
        ]
        db.add_all(new_files)
        db.commit()
        for file in new_files:
            db.refresh(file)

        second_result = knowledge_processing_service.process_repository_chunks(db, repository)
        total_rows = (
            db.query(KnowledgeChunk)
            .filter(
                KnowledgeChunk.user_id == user.id,
                KnowledgeChunk.source_type == "repository_file",
                KnowledgeChunk.source_id.in_([file.id for file in new_files]),
            )
            .count()
        )

        assert second_result["chunks_created"] == 4
        assert total_rows == 4
        assert (
            db.query(KnowledgeChunk)
            .filter(
                KnowledgeChunk.user_id == user.id,
                KnowledgeChunk.source_type == "repository_file",
            )
            .count()
            == 4
        )
    finally:
        db.close()


def test_process_all_user_knowledge_is_idempotent(monkeypatch):
    _mock_repo_processing(monkeypatch)
    db = SessionLocal()
    try:
        user = _create_user(db)
        repository = Repository(
            user_id=user.id,
            repo_url="https://example.com/full-repo",
            repo_name="full-repo",
            local_path="/tmp/full-repo",
            repository_type="project",
        )
        db.add(repository)
        db.commit()
        db.refresh(repository)

        files = [
            RepositoryFile(
                repository_id=repository.id,
                file_path="src/one.py",
                file_name="one.py",
                file_extension=".py",
                content="print('one')",
            ),
            RepositoryFile(
                repository_id=repository.id,
                file_path="src/two.py",
                file_name="two.py",
                file_extension=".py",
                content="print('two')",
            ),
        ]
        db.add_all(files)
        db.commit()
        for file in files:
            db.refresh(file)

        first_result = knowledge_processing_service.process_all_user_knowledge(db, user.id)
        assert first_result["total_chunks_created"] == 4

        for file in files:
            db.delete(file)
        db.commit()

        replacement_files = [
            RepositoryFile(
                repository_id=repository.id,
                file_path="src/three.py",
                file_name="three.py",
                file_extension=".py",
                content="print('three')",
            ),
            RepositoryFile(
                repository_id=repository.id,
                file_path="src/four.py",
                file_name="four.py",
                file_extension=".py",
                content="print('four')",
            ),
        ]
        db.add_all(replacement_files)
        db.commit()
        for file in replacement_files:
            db.refresh(file)

        second_result = knowledge_processing_service.process_all_user_knowledge(db, user.id)
        total_rows = db.query(KnowledgeChunk).filter(KnowledgeChunk.user_id == user.id).count()

        assert second_result["total_chunks_created"] == 4
        assert total_rows == 4
    finally:
        db.close()
