
"""add guest session ownership to knowledge documents

Revision ID: 3d4448e788ae
Revises: f2ae49211999
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3d4448e788ae"
down_revision: Union[str, Sequence[str], None] = "f2ae49211999"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FK_NAME = "knowledge_documents_guest_session_id_fkey"


def upgrade() -> None:
    op.add_column(
        "knowledge_documents",
        sa.Column("guest_session_id", sa.UUID(), nullable=True),
    )

    op.create_index(
        op.f("ix_knowledge_documents_guest_session_id"),
        "knowledge_documents",
        ["guest_session_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_knowledge_documents_uploaded_by"),
        "knowledge_documents",
        ["uploaded_by"],
        unique=False,
    )

    op.create_foreign_key(
        FK_NAME,
        "knowledge_documents",
        "guest_sessions",
        ["guest_session_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        FK_NAME,
        "knowledge_documents",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_knowledge_documents_uploaded_by"),
        table_name="knowledge_documents",
    )

    op.drop_index(
        op.f("ix_knowledge_documents_guest_session_id"),
        table_name="knowledge_documents",
    )

    op.drop_column(
        "knowledge_documents",
        "guest_session_id",
    )
