from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_path: str
    file_type: str
    extracted_text: str
    created_at: datetime