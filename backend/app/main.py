from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes import auth_router, documents_router, knowledge_router, repositories_router
from app.db.database import Base, engine
from app.models import Document, KnowledgeChunk, Repository, RepositoryFile, User


def ensure_pgvector_extension() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))


def ensure_repository_columns() -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE repositories ADD COLUMN IF NOT EXISTS repository_type VARCHAR(32) NOT NULL DEFAULT 'project'"
            )
        )


def ensure_knowledge_chunk_columns() -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS repository_id INTEGER"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS repository_file_id INTEGER"
            )
        )

app = FastAPI(
    title="Personal Engineering Knowledge Assistant API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_pgvector_extension()
Base.metadata.create_all(bind=engine)
ensure_repository_columns()
ensure_knowledge_chunk_columns()
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(knowledge_router)
app.include_router(repositories_router)

@app.get("/")
def root():
    return {
        "message": "Personal Engineering Knowledge Assistant API is Running 🚀"
    }


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "not connected",
            "error": str(e)
        }