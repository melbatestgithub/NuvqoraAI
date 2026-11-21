import uuid

from sqlalchemy import (
    String, Text, DateTime, ForeignKey, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class HandoffRequest(Base):
    __tablename__ = "handoff_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        default="normal",
        nullable=False
    )

    contact_email: Mapped[str | None] = mapped_column(
        String(255)
    )

    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    resolved_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True)
    )

    conversation = relationship(
        "Conversation",
        back_populates="handoff_requests"
    )