
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class KnowledgeUploadResponse(BaseModel):
    success: bool
    document_id: UUID
    title: str
    filename: str
    status: str
    total_chunks: int
    message: str


class KnowledgeDocumentResponse(BaseModel):
    id: UUID
    title: str
    source_type: str
    original_filename: str | None
    status: str
    is_public: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentDetailResponse(KnowledgeDocumentResponse):
    total_chunks: int


class KnowledgeDocumentListResponse(BaseModel):
    total: int
    documents: list[KnowledgeDocumentResponse]


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=10000)
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeSearchResponse(BaseModel):
    query: str
    total_results: int
    results: list[dict]
