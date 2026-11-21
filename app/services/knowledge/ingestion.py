
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.services.ai.embeddings import embedding_service
from app.services.knowledge.document_processor import document_processor
from app.services.knowledge.chunker import document_chunker


class DocumentIngestionService:
    """Process documents and store their embeddings in PostgreSQL."""

    EMBEDDING_BATCH_SIZE = 50

    async def ingest_document(
        self,
        db: AsyncSession,
        filename: str,
        file_content: bytes,
        uploaded_by: UUID | None = None,
        guest_session_id: UUID | None = None,
    ) -> dict:

        if uploaded_by is not None and guest_session_id is not None:
            raise ValueError(
                "A document cannot belong to both a user and a guest session."
            )

        try:
            extracted_text = document_processor.extract_text(
                file_content=file_content,
                filename=filename,
            )

            chunks = document_chunker.split_text(extracted_text)

            if not chunks:
                raise ValueError(
                    "Document did not produce any text chunks."
                )

            extension = Path(filename).suffix.lower()

            document = KnowledgeDocument(
                title=Path(filename).stem,
                source_type="pdf" if extension == ".pdf" else "text",
                original_filename=filename,
                raw_text=extracted_text,
                status="processing",
                uploaded_by=uploaded_by,
                guest_session_id=guest_session_id,
                is_public=False,
            )

            db.add(document)
            await db.flush()

            document_chunks = []

            for start in range(
                0,
                len(chunks),
                self.EMBEDDING_BATCH_SIZE,
            ):
                chunk_batch = chunks[
                    start:start + self.EMBEDDING_BATCH_SIZE
                ]

                embeddings = (
                    await embedding_service.generate_batch_embeddings(
                        chunk_batch
                    )
                )

                for offset, (content, embedding) in enumerate(
                    zip(chunk_batch, embeddings, strict=True)
                ):
                    chunk_index = start + offset

                    document_chunks.append(
                        DocumentChunk(
                            document_id=document.id,
                            chunk_index=chunk_index,
                            content=content,
                            embedding=embedding,
                            token_count=len(content.split()),
                            chunk_metadata={
                                "filename": filename,
                                "chunk_index": chunk_index,
                            },
                        )
                    )

            db.add_all(document_chunks)

            document.status = "completed"

            await db.commit()
            await db.refresh(document)

            return {
                "success": True,
                "document_id": str(document.id),
                "title": document.title,
                "filename": document.original_filename,
                "status": document.status,
                "total_chunks": len(document_chunks),
                "message": "Document ingested successfully.",
            }

        except Exception:
            await db.rollback()
            raise


document_ingestion_service = DocumentIngestionService()
