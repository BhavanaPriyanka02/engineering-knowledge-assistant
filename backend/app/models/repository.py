from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    repo_url = Column(String(512), nullable=False)
    repo_name = Column(String(256), nullable=False)
    local_path = Column(String(512), nullable=False)
    repository_type = Column(String(32), nullable=False, default="project", server_default="project")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="repositories")
    repository_files = relationship(
        "RepositoryFile",
        back_populates="repository",
        cascade="all, delete-orphan",
    )
