from pydantic import BaseModel, ConfigDict, Field, field_validator


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Query must not be empty.")
        return cleaned


class KnowledgeSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: int
    source_type: str
    source_id: int
    source_name: str | None = None
    source_path: str | None = None
    chunk_index: int
    content: str
    similarity_score: float


class KnowledgeSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    results: list[KnowledgeSearchResult]
