from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes import auth_router, documents_router
from app.db.database import Base, engine
from app.models import Document, User

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

Base.metadata.create_all(bind=engine)
app.include_router(auth_router)
app.include_router(documents_router)

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