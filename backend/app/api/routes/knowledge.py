import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.dependencies import get_db
from app.models.document import Document
from app.models.repository import Repository
from app.models.user import User
from app.schemas.knowledge import KnowledgeSearchRequest, KnowledgeSearchResponse
from app.services.knowledge_processing import process_all_user_knowledge, process_document_chunks, process_repository_chunks
from app.services.retrieval import search_user_knowledge

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
logger = logging.getLogger(__name__)


@router.post("/process/documents/{document_id}")
def process_document_for_ai(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    try:
        result = process_document_chunks(db, document)
        return result
    except Exception as error:
        db.rollback()
        logger.exception("Document knowledge processing failed for document_id=%s user_id=%s", document_id, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The document could not be processed for AI.",
        ) from error


@router.post("/process/repositories/{repository_id}")
def process_repository_for_ai(
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")

    try:
        result = process_repository_chunks(db, repository)
        return result
    except Exception as error:
        db.rollback()
        logger.exception("Repository knowledge processing failed for repository_id=%s user_id=%s", repository_id, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The repository could not be processed for AI.",
        ) from error


@router.post("/process/all")
def process_all_user_knowledge_for_ai(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return process_all_user_knowledge(db, current_user.id)
    except Exception as error:
        db.rollback()
        logger.exception("Bulk knowledge processing failed for user_id=%s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Knowledge processing failed for your account.",
        ) from error


@router.post("/search", response_model=KnowledgeSearchResponse)
def search_knowledge(
    payload: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        results = search_user_knowledge(db, current_user.id, payload.query, payload.top_k)
        return {"results": results}
    except Exception as error:
        logger.exception("Knowledge search failed for user_id=%s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Knowledge search failed.",
        ) from error
