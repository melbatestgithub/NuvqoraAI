
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

from app.api.routes.health import router as health_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.auth import router as auth_router
from app.api.routes.guest import router as guest_router


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered conversational customer support platform",
    version="1.0.0",
    debug=settings.DEBUG,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(guest_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Welcome to Nuvqora AI",
        "version": "1.0.0",
        "documentation": "/docs",
    }
    