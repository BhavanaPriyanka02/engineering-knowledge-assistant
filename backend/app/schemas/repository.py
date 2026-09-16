from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RepositoryCreate(BaseModel):
    repo_url: str


class RepositoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repo_url: str
    repo_name: str
    created_at: datetime


class RepositoryFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: str
    file_name: str
    file_extension: str
    created_at: datetime


class RepositoryFileDetailRead(RepositoryFileRead):
    content: str
