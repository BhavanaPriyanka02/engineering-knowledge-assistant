from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.dependencies import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentRead
from app.services.documents import save_pdf_and_extract_text

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filename = file.filename or ""
    if file.content_type != "application/pdf" or not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed.",
        )

    try:
        saved_path, extracted_text = await save_pdf_and_extract_text(file)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    document = Document(
        user_id=current_user.id,
        filename=Path(filename).name,
        file_path=str(saved_path),
        file_type="application/pdf",
        extracted_text=extracted_text,
    )
    try:
        db.add(document)
        db.commit()
        db.refresh(document)
    except Exception as error:
        db.rollback()
        saved_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The document could not be saved.",
        ) from error

    return document


@router.get("", response_model=list[DocumentRead])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
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

    Path(document.file_path).unlink(missing_ok=True)
    db.delete(document)
    db.commit()