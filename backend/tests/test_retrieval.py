from uuid import uuid4

from fastapi.testclient import TestClient
from sentence_transformers import SentenceTransformer

from app.db.database import SessionLocal
from app.main import app
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.user import User
from app.services import auth as auth_service


client = TestClient(app)
_EMBEDDING_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def _make_user(db, email_suffix="test"):
    unique = uuid4().hex[:8]
    email = f"{email_suffix}+{unique}@example.com"
    password = "password123"
    user = User(
        name=f"User {unique}",
        email=email,
        hashed_password=auth_service.get_password_hash(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, password


def _build_embedding(prefix: str, index: int = 0):
    text = f"{prefix} relevant context {index}"
    vector = _EMBEDDING_MODEL.encode([text], normalize_embeddings=True)[0].tolist()
    return [float(value) for value in vector]


def _login(client_instance, user_email, password):
    response = client_instance.post(
        "/auth/login",
        json={"email": user_email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _insert_chunk(db, user_id, source_type, source_id, content, embedding, source_name="chunk.txt", source_path="/tmp/chunk.txt", chunk_index=0):
    chunk = KnowledgeChunk(
        user_id=user_id,
        source_type=source_type,
        source_id=source_id,
        source_name=source_name,
        source_path=source_path,
        content=content,
        chunk_index=chunk_index,
        embedding=embedding,
    )
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk


def test_authenticated_search_returns_relevant_chunks():
    db = SessionLocal()
    try:
        user, password = _make_user(db, "retrieval-user")
        target_embedding = _build_embedding("auth")
        other_embedding = [0.0] * 384
        other_embedding[0] = -1.0
        _insert_chunk(db, user.id, "document", 101, "OrderFlow uses JWT for authentication.", target_embedding, "doc.txt", "/tmp/doc.txt", 0)
        _insert_chunk(db, user.id, "repository_file", 201, "Some unrelated repo content.", other_embedding, "repo.py", "/tmp/repo.py", 0)

        token = _login(client, user.email, password)
        response = client.post(
            "/knowledge/search",
            json={"query": "What authentication did I use in OrderFlow?", "top_k": 5},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert "results" in payload
        assert len(payload["results"]) >= 1
        assert payload["results"][0]["source_id"] == 101
        assert payload["results"][0]["source_type"] == "document"
        assert "similarity_score" in payload["results"][0]
    finally:
        db.query(KnowledgeChunk).filter(KnowledgeChunk.user_id == user.id).delete(synchronize_session=False)
        db.delete(user)
        db.commit()
        db.close()


def test_user_can_only_retrieve_their_own_chunks():
    db = SessionLocal()
    try:
        owner, owner_password = _make_user(db, "owner")
        other, other_password = _make_user(db, "other")

        query_embedding = _build_embedding("shared")
        _insert_chunk(db, owner.id, "document", 301, "Owner only content.", query_embedding, "owner.txt", "/tmp/owner.txt", 0)
        _insert_chunk(db, other.id, "document", 302, "Other user content.", query_embedding, "other.txt", "/tmp/other.txt", 0)

        token = _login(client, owner.email, owner_password)
        response = client.post(
            "/knowledge/search",
            json={"query": "Owner only content.", "top_k": 5},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert all(result["source_id"] != 302 for result in payload["results"])
        assert any(result["source_id"] == 301 for result in payload["results"])
    finally:
        db.query(KnowledgeChunk).filter(KnowledgeChunk.user_id.in_([owner.id, other.id])).delete(synchronize_session=False)
        db.delete(owner)
        db.delete(other)
        db.commit()
        db.close()


def test_top_k_works():
    db = SessionLocal()
    try:
        user, password = _make_user(db, "topk")
        vector = _build_embedding("topk")
        for index in range(3):
            _insert_chunk(db, user.id, "repository_file", 401 + index, f"chunk {index}", vector, f"file{index}.py", f"/tmp/file{index}.py", index)

        token = _login(client, user.email, password)
        response = client.post(
            "/knowledge/search",
            json={"query": "Find relevant chunk.", "top_k": 2},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert len(payload["results"]) == 2
    finally:
        db.query(KnowledgeChunk).filter(KnowledgeChunk.user_id == user.id).delete(synchronize_session=False)
        db.delete(user)
        db.commit()
        db.close()


def test_empty_query_is_rejected():
    db = SessionLocal()
    try:
        user, password = _make_user(db, "empty-query")
        token = _login(client, user.email, password)
        response = client.post(
            "/knowledge/search",
            json={"query": "   ", "top_k": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
    finally:
        db.delete(user)
        db.commit()
        db.close()


def test_search_works_when_knowledge_chunks_exist():
    db = SessionLocal()
    try:
        user, password = _make_user(db, "search-exists")
        vector = _build_embedding("exists")
        _insert_chunk(db, user.id, "document", 501, "This is stored knowledge.", vector, "exists.txt", "/tmp/exists.txt", 0)

        token = _login(client, user.email, password)
        response = client.post(
            "/knowledge/search",
            json={"query": "stored knowledge", "top_k": 5},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["results"]
        assert payload["results"][0]["content"] == "This is stored knowledge."
    finally:
        db.query(KnowledgeChunk).filter(KnowledgeChunk.user_id == user.id).delete(synchronize_session=False)
        db.delete(user)
        db.commit()
        db.close()
