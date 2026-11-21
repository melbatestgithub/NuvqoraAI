
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ConversationCreate(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    conversation_id: UUID | None = None


class ConversationRename(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class ConversationListItem(BaseModel):
    id: UUID
    title: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SourceReference(BaseModel):
    document_id: str
    chunk_id: str
    document_title: str
    filename: str | None = None
    similarity: float


class ConversationResponse(BaseModel):
    success: bool
    conversation_id: UUID
    user_message: str
    assistant_message: str
    sources: list[SourceReference] = Field(default_factory=list)


class ConversationHistoryMessage(BaseModel):
    id: UUID
    role: str
    content: str

    model_config = ConfigDict(from_attributes=True)


class ConversationHistoryResponse(BaseModel):
    conversation_id: UUID
    messages: list[ConversationHistoryMessage]
