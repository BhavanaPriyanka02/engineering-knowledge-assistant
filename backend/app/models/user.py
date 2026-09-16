from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    documents = relationship("Document", back_populates="user")
