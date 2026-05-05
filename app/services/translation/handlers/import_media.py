from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.schemas.translate_schema import LocalizationParams
from app.schemas.import_schema import ImportMediaResponse
from app.services.translation.clients.whisper_client import WhisperClient
from app.services.translation.clients.translator_factory import get_translator_client
from app.services.translation.utils.file_utils import save_upload, cleanup, temp_path
from app.services.translation.utils.ffmpeg_utils import extract_audio, get_duration

whisper = WhisperClient()
translator = get_translator_client()

VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm", "video/x-msvideo", "video/mpeg"}
AUDIO_TYPES = {"audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav", "audio/webm", "audio/x-m4a"}


async def handle_import_media(
    media_file: UploadFile,
    localization: LocalizationParams,
) -> ImportMediaResponse:
    """
    1. Detect if video or audio → 2. If video, extract audio
    → 3. Validate duration → 4. Transcribe → 5. Translate → return text
    """
    media_path = audio_path = None
    try:
        content_type = media_file.content_type or ""
        is_video = content_type in VIDEO_TYPES

        suffix = ".mp4" if is_video else ".mp3"
        media_path = await save_upload(media_file, suffix)

        # Extract audio if video
        if is_video:
            audio_path = temp_path(".mp3")
            await extract_audio(media_path, audio_path)
            transcribe_target = audio_path
        else:
            transcribe_target = media_path

        # Validate duration
        duration = await get_duration(transcribe_target)
        if duration > settings.MAX_IMPORT_DURATION_SECONDS:
            raise HTTPException(
                status_code=422,
                detail=f"Media exceeds maximum duration of {settings.MAX_IMPORT_DURATION_SECONDS}s.",
            )

        # Transcribe
        transcript = await whisper.transcribe(transcribe_target)
        text = transcript["text"]
        if not text:
            raise HTTPException(status_code=422, detail="No speech detected in media.")

        # Translate
        result = await translator.translate(text, localization)

        return ImportMediaResponse(
            translated_text=result["translated_text"],
            source_language_detected=result.get("detected_source_language"),
        )

    finally:
        cleanup(*filter(None, [media_path, audio_path]))