
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.services.ai.embeddings import embedding_service


class KnowledgeRetrievalService:
    """Retrieve public, user-owned, or guest-session knowledge."""

    async def _search(
        self,
        db: AsyncSession,
        query: str,
        user_id: UUID | None = None,
        guest_session_id: UUID | None = None,
        top_k: int | None = None,
    ) -> list[dict]:

        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        if user_id is not None and guest_session_id is not None:
            raise ValueError(
                "Cannot search as both a user and a guest session."
            )

        limit = settings.RETRIEVAL_TOP_K if top_k is None else top_k

        if limit < 1:
            raise ValueError("top_k must be greater than zero.")

        query_embedding = await embedding_service.generate_query_embedding(
            query.strip()
        )

        distance = DocumentChunk.embedding.cosine_distance(
            query_embedding
        ).label("distance")

        conditions = [
            KnowledgeDocument.status == "completed",
            DocumentChunk.embedding.is_not(None),
        ]

        if guest_session_id is not None:
            # Guest: own uploaded documents and published public documents.
            conditions.append(
                or_(
                    KnowledgeDocument.guest_session_id == guest_session_id,
                    KnowledgeDocument.is_public.is_(True),
                )
            )

        elif user_id is None:
            # Anonymous public search: published documents only.
            conditions.append(
                KnowledgeDocument.is_public.is_(True)
            )

        else:
            # Authenticated: own documents and published public documents.
            conditions.append(
                or_(
                    KnowledgeDocument.uploaded_by == user_id,
                    KnowledgeDocument.is_public.is_(True),
                )
            )

        statement = (
            select(DocumentChunk, KnowledgeDocument, distance)
            .join(
                KnowledgeDocument,
                DocumentChunk.document_id == KnowledgeDocument.id,
            )
            .where(*conditions)
            .order_by(distance.asc())
            .limit(limit)
        )

        result = await db.execute(statement)

        matches = []

        for chunk, document, cosine_distance in result.all():
            similarity = 1.0 - float(cosine_distance)

            matches.append({
                "chunk_id": str(chunk.id),
                "document_id": str(document.id),
                "document_title": document.title,
                "filename": document.original_filename,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "similarity": round(similarity, 4),
                "metadata": chunk.chunk_metadata,
            })

        return matches

    async def search_public_knowledge(
        self,
        db: AsyncSession,
        query: str,
        top_k: int | None = None,
    ) -> list[dict]:
        """Search only published public documents."""
        return await self._search(
            db=db,
            query=query,
            top_k=top_k,
        )

    async def search_guest_knowledge(
        self,
        db: AsyncSession,
        guest_session_id: UUID,
        query: str,
        top_k: int | None = None,
    ) -> list[dict]:
        """Search this guest's documents and published public documents."""
        return await self._search(
            db=db,
            query=query,
            guest_session_id=guest_session_id,
            top_k=top_k,
        )

    async def search_knowledge(
        self,
        db: AsyncSession,
        user_id: UUID,
        query: str,
        top_k: int | None = None,
    ) -> list[dict]:
        """Search the user's documents and published public documents."""
        return await self._search(
            db=db,
            user_id=user_id,
            query=query,
            top_k=top_k,
        )


knowledge_retrieval_service = KnowledgeRetrievalService()
