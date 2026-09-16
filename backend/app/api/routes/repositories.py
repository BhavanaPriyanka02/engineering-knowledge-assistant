import shutil

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.dependencies import get_db
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile
from app.models.user import User
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryFileDetailRead,
    RepositoryFileRead,
    RepositoryRead,
)
from app.services.github_service import clone_repository, validate_github_url

router = APIRouter(
    prefix="/repositories",
    tags=["repositories"],
)


@router.post("", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED)
def create_repository(
    repository_create: RepositoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        repo_url = validate_github_url(repository_create.repo_url)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    repository_type = repository_create.repository_type.lower()
    if repository_type not in {"project", "coding"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository type must be 'project' or 'coding'.",
        )

    existing_repository = (
        db.query(Repository)
        .filter(Repository.user_id == current_user.id, Repository.repo_url == repo_url)
        .first()
    )
    if existing_repository is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository already added.",
        )

    try:
        repo_name, clone_dir, file_records = clone_repository(repo_url)
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    repository = Repository(
        user_id=current_user.id,
        repo_url=repo_url,
        repo_name=repo_name,
        local_path=str(clone_dir),
        repository_type=repository_type,
    )

    try:
        db.add(repository)
        db.commit()
        db.refresh(repository)
    except Exception as error:
        db.rollback()
        shutil.rmtree(clone_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The repository could not be saved.",
        ) from error

    repository_files = [
        RepositoryFile(
            repository_id=repository.id,
            file_path=item["file_path"],
            file_name=item["file_name"],
            file_extension=item["file_extension"],
            content=item["content"],
        )
        for item in file_records
    ]

    try:
        db.add_all(repository_files)
        db.commit()
    except Exception as error:
        db.rollback()
        db.delete(repository)
        db.commit()
        shutil.rmtree(clone_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The repository files could not be saved.",
        ) from error

    return repository


@router.get("", response_model=list[RepositoryRead])
def list_repositories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Repository)
        .filter(Repository.user_id == current_user.id)
        .order_by(Repository.created_at.desc())
        .all()
    )


@router.get("/{repository_id}", response_model=RepositoryRead)
def get_repository(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id, Repository.user_id == current_user.id)
        .first()
    )
    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found.",
        )
    return repository


@router.get("/{repository_id}/files", response_model=list[RepositoryFileRead])
def list_repository_files(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id, Repository.user_id == current_user.id)
        .first()
    )
    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found.",
        )

    return (
        db.query(RepositoryFile)
        .filter(RepositoryFile.repository_id == repository_id)
        .order_by(RepositoryFile.file_path.asc())
        .all()
    )


@router.get("/{repository_id}/files/{file_id}", response_model=RepositoryFileDetailRead)
def get_repository_file(
    repository_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id, Repository.user_id == current_user.id)
        .first()
    )
    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found.",
        )

    repository_file = (
        db.query(RepositoryFile)
        .filter(
            RepositoryFile.id == file_id,
            RepositoryFile.repository_id == repository_id,
        )
        .first()
    )
    if repository_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository file not found.",
        )

    return repository_file


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repository(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id, Repository.user_id == current_user.id)
        .first()
    )
    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found.",
        )

    db.query(RepositoryFile).filter(RepositoryFile.repository_id == repository.id).delete()
    db.delete(repository)
    db.commit()

    if repository.local_path:
        shutil.rmtree(repository.local_path, ignore_errors=True)
