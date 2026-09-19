from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=True, index=True)
    repository_file_id = Column(Integer, ForeignKey("repository_files.id"), nullable=True, index=True)
    source_type = Column(String(64), nullable=False, index=True)
    source_id = Column(Integer, nullable=False, index=True)
    source_name = Column(String(512), nullable=True)
    source_path = Column(String(1024), nullable=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(384), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="knowledge_chunks")
    repository = relationship("Repository", back_populates="knowledge_chunks")
    repository_file = relationship("RepositoryFile", back_populates="knowledge_chunks")
