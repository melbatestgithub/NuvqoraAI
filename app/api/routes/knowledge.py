
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.core.dependencies import  get_admin_user

from app.schemas.knowledge import (
    KnowledgeUploadResponse,
    KnowledgeDocumentDetailResponse,
    KnowledgeDocumentListResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)

from app.services.knowledge.ingestion import (
    document_ingestion_service,
)

from app.services.knowledge.retrieval import (
    knowledge_retrieval_service,
)


router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Base"],
)

MAX_UPLOAD_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@router.post(
    "/upload",
    response_model=KnowledgeUploadResponse,
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required.",
        )

    filename = Path(file.filename).name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported.",
        )

    try:
        content = await file.read(MAX_UPLOAD_SIZE + 1)

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Maximum upload size is 10 MB.",
            )

        result = await document_ingestion_service.ingest_document(
            db=db,
            filename=filename,
            file_content=content,
            uploaded_by=current_user.id,
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except RuntimeError:
        raise HTTPException(
            status_code=502,
            detail="Document processing failed. Please try again.",
        )

    finally:
        await file.close()


@router.get(
    "",
    response_model=KnowledgeDocumentListResponse,
)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if skip < 0 or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Invalid pagination parameters.",
        )

    count_result = await db.execute(
        select(func.count(KnowledgeDocument.id)).where(
            KnowledgeDocument.uploaded_by == current_user.id
        )
    )

    total = count_result.scalar_one()

    result = await db.execute(
        select(KnowledgeDocument)
        .where(
            KnowledgeDocument.uploaded_by == current_user.id
        )
        .order_by(KnowledgeDocument.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    documents = result.scalars().all()

    return {
        "total": total,
        "documents": documents,
    }


@router.get(
    "/{document_id}",
    response_model=KnowledgeDocumentDetailResponse,
)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.uploaded_by == current_user.id,
        )
    )

    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Knowledge document not found.",
        )

    count_result = await db.execute(
        select(func.count(DocumentChunk.id)).where(
            DocumentChunk.document_id == document.id
        )
    )

    total_chunks = count_result.scalar_one()

    return {
        "id": document.id,
        "title": document.title,
        "source_type": document.source_type,
        "original_filename": document.original_filename,
        "status": document.status,
        "created_at": document.created_at,
        "total_chunks": total_chunks,
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.uploaded_by == current_user.id,
        )
    )

    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Knowledge document not found.",
        )

    await db.delete(document)
    await db.commit()

    return {
        "success": True,
        "document_id": str(document_id),
        "message": "Document and associated chunks deleted successfully.",
    }


@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
)
async def search_knowledge(
    payload: KnowledgeSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        results = await knowledge_retrieval_service.search_knowledge(
            db=db,
            user_id=current_user.id,
            query=payload.query,
            top_k=payload.top_k,
        )

        return {
            "query": payload.query,
            "total_results": len(results),
            "results": results,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except RuntimeError:
        raise HTTPException(
            status_code=502,
            detail="Knowledge search failed. Please try again.",
        )


@router.patch("/{document_id}/publish")
async def publish_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    result = await db.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id
        )
    )

    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Knowledge document not found.",
        )

    if document.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Only successfully processed documents can be published.",
        )

    document.is_public = True
    await db.commit()

    return {
        "success": True,
        "document_id": str(document.id),
        "is_public": True,
        "message": "Document published successfully.",
    }


@router.patch("/{document_id}/unpublish")
async def unpublish_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    result = await db.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id
        )
    )

    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Knowledge document not found.",
        )

    document.is_public = False
    await db.commit()

    return {
        "success": True,
        "document_id": str(document.id),
        "is_public": False,
        "message": "Document unpublished successfully.",
    }
