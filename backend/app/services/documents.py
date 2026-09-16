from pathlib import Path
from uuid import uuid4

import pymupdf
from fastapi import UploadFile

UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"


async def save_pdf_and_extract_text(file: UploadFile) -> tuple[Path, str]:
    file_contents = await file.read()

    if not file_contents:
        raise ValueError("The uploaded file is empty.")

    if not file_contents.startswith(b"%PDF"):
        raise ValueError("The uploaded file is not a valid PDF.")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    saved_path = UPLOADS_DIR / f"{uuid4().hex}.pdf"
    saved_path.write_bytes(file_contents)

    try:
        with pymupdf.open(saved_path) as pdf:
            extracted_text = "".join(page.get_text() for page in pdf)

        # PostgreSQL TEXT columns cannot contain NUL characters.
        extracted_text = extracted_text.replace("\x00", "")

    except Exception as error:
        saved_path.unlink(missing_ok=True)
        raise ValueError("The uploaded PDF could not be read.") from error

    return saved_path, extracted_text