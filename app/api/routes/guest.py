
from pathlib import Path
import json
import logging
from fastapi.responses import StreamingResponse
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.conversations.guest import guest_chat_service
from app.services.knowledge.ingestion import document_ingestion_service


router = APIRouter(prefix="/guest", tags=["Guest Chat"])

bearer_scheme = HTTPBearer(auto_error=False)

MAX_FILE_SIZE = 15 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".txt"}


async def get_guest_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Guest session token required.",
        )

    return credentials.credentials


class GuestMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=10000)


@router.post("/sessions")
async def create_guest_session(
    db: AsyncSession = Depends(get_db),
):
    try:
        return await guest_chat_service.create_session(db)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Could not create guest session.",
        ) from error


@router.post("/upload")
async def upload_guest_document(
    file: UploadFile = File(...),
    token: str = Depends(get_guest_token),
    db: AsyncSession = Depends(get_db),
):
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported.",
        )

    try:
        session = await guest_chat_service.get_valid_session(
            db=db,
            token=token,
        )

        file_content = await file.read(MAX_FILE_SIZE + 1)

        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds the 15 MB upload limit.",
            )

        result = await document_ingestion_service.ingest_document(
            db=db,
            filename=filename,
            file_content=file_content,
            guest_session_id=session.id,
        )

        return {
            "success": True,
            "conversation_id": str(session.conversation_id),
            **result,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=401 if "session" in str(error).lower()
            else 400,
            detail=str(error),
        ) from error

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Could not process uploaded document.",
        ) from error

    finally:
        await file.close()


@router.post("/message")
async def send_guest_message(
    payload: GuestMessageCreate,
    token: str = Depends(get_guest_token),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await guest_chat_service.send_message(
            db=db,
            token=token,
            message=payload.message,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=401 if "session" in str(error).lower()
            else 404 if "not found" in str(error).lower()
            else 400,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Could not generate a response.",
        ) from error



@router.post("/message/stream")
async def stream_guest_message(
    payload: GuestMessageCreate,
    token: str = Depends(get_guest_token),
    db: AsyncSession = Depends(get_db),
):
    async def event_generator():
        try:
            async for event in guest_chat_service.stream_message(
                db=db,
                token=token,
                message=payload.message,
            ):
                yield (
                    f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                )

        except Exception:
            logging.exception("Guest streaming endpoint failed.")

            yield (
                "data: "
                + json.dumps({
                    "type": "error",
                    "message": "An unexpected error occurred.",
                })
                + "\n\n"
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history")
async def get_guest_history(
    token: str = Depends(get_guest_token),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await guest_chat_service.get_history(
            db=db,
            token=token,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=401,
            detail=str(error),
        ) from error
