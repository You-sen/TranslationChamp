from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.translate import router as translate_router
from app.services.translation.utils import audio_cache

app = FastAPI(
    title="tdesignAI Translation API",
    description="Localized translation for text, voice, video, and imported media.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(translate_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def _startup_tasks():
    # Start background cleanup for ephemeral audio cache
    audio_cache.start_cleanup_task()