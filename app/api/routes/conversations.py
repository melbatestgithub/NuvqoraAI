
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import json
from fastapi.responses import StreamingResponse
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationHistoryResponse,
    ConversationRename,
    ConversationListItem,
)

from app.services.conversations.service import conversation_service


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.post("/message", response_model=ConversationResponse)
async def send_message(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await conversation_service.send_message(
            db=db,
            user_id=current_user.id,
            message=payload.message,
            conversation_id=payload.conversation_id,
        )

    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error))


@router.post("/message/stream")
async def send_message_stream(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    async def event_generator():
        try:
            async for event in conversation_service.stream_message(
                db=db,
                user_id=current_user.id,
                message=payload.message,
                conversation_id=payload.conversation_id,
            ):
                yield (
                    f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                )

        except Exception:
            import logging
            logging.exception("Conversation streaming endpoint failed.")

            error_event = {
                "type": "error",
                "message": "An unexpected error occurred.",
            }

            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("", response_model=list[ConversationListItem])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await conversation_service.get_conversations(
        db=db,
        user_id=current_user.id,
    )


@router.patch("/{conversation_id}")
async def rename_conversation(
    conversation_id: UUID,
    payload: ConversationRename,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        conversation = await conversation_service.rename_conversation(
            db=db,
            user_id=current_user.id,
            conversation_id=conversation_id,
            title=payload.title,
        )

        return {
            "success": True,
            "conversation": conversation,
        }

    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await conversation_service.delete_conversation(
            db=db,
            user_id=current_user.id,
            conversation_id=conversation_id,
        )

        return {
            "success": True,
            "message": "Conversation deleted successfully.",
        }

    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.get(
    "/{conversation_id}/history",
    response_model=ConversationHistoryResponse,
)
async def get_conversation_history(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await conversation_service.get_history(
            db=db,
            user_id=current_user.id,
            conversation_id=conversation_id,
        )

    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
