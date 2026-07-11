# from pathlib import Path
# from fastapi import UploadFile, HTTPException

# from app.core.config import settings
# from app.schemas.translate_schema import LocalizationParams
# from app.schemas.import_schema import ImportMediaResponse
# from app.services.translation.clients.whisper_client import WhisperClient
# from app.services.translation.clients.translator_factory import get_translator_client
# from app.services.translation.utils.file_utils import save_upload, cleanup, temp_path
# from app.services.translation.utils.ffmpeg_utils import extract_audio, get_duration
# from app.services.translation.utils.cost_tracker import build_cost_breakdown

# whisper = WhisperClient()
# translator = get_translator_client()

# VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm", "video/x-msvideo", "video/mpeg"}
# AUDIO_TYPES = {"audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav", "audio/webm", "audio/x-m4a"}


# async def handle_import_media(
#     media_file: UploadFile,
#     localization: LocalizationParams,
# ) -> ImportMediaResponse:
#     """
#     1. Detect if video or audio → 2. If video, extract audio
#     → 3. Validate duration → 4. Transcribe → 5. Translate → return text
#     """
#     media_path = audio_path = None
#     try:
#         content_type = media_file.content_type or ""
#         is_video = content_type in VIDEO_TYPES

#         suffix = ".mp4" if is_video else ".mp3"
#         media_path = await save_upload(media_file, suffix)

#         # Extract audio if video
#         if is_video:
#             audio_path = temp_path(".mp3")
#             await extract_audio(media_path, audio_path)
#             transcribe_target = audio_path
#         else:
#             transcribe_target = media_path

#         # Validate duration
#         duration = await get_duration(transcribe_target)
#         if duration > settings.MAX_IMPORT_DURATION_SECONDS:
#             raise HTTPException(
#                 status_code=422,
#                 detail=f"Media exceeds maximum duration of {settings.MAX_IMPORT_DURATION_SECONDS}s.",
#             )

#         # Transcribe
#         transcript = await whisper.transcribe(transcribe_target)
#         text = transcript["text"]
#         whisper_seconds = transcript.get("duration_seconds", duration)
#         if not text:
#             raise HTTPException(status_code=422, detail="No speech detected in media.")

#         # Translate
#         result = await translator.translate(text, localization)

#         cost = build_cost_breakdown(
#             whisper_seconds=whisper_seconds,
#             gpt_input_tokens=result.get("gpt_input_tokens", 0),
#             gpt_output_tokens=result.get("gpt_output_tokens", 0),
#             deepl_characters=result.get("characters_used", 0),
#         )

#         return ImportMediaResponse(
#             translated_text=result["translated_text"],
#             source_language_detected=result.get("detected_source_language"),
#             duration_seconds=round(duration, 2),
#             cost_breakdown=cost,
#         )

#     finally:
#         cleanup(*filter(None, [media_path, audio_path]))

from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.schemas.translate_schema import LocalizationParams
from app.schemas.import_schema import ImportMediaResponse
from app.services.translation.clients.whisper_client import WhisperClient
from app.services.translation.clients.translator_factory import get_translator_client
from app.services.translation.utils.file_utils import save_upload, cleanup, temp_path
from app.services.translation.utils.ffmpeg_utils import extract_audio, get_duration
from app.services.translation.utils.cost_tracker import build_cost_breakdown

whisper = WhisperClient()
translator = get_translator_client()

VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm", "video/x-msvideo", "video/mpeg"}
AUDIO_TYPES = {"audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav", "audio/webm", "audio/x-m4a", "audio/m4a"}

AUDIO_SUFFIX_MAP = {
    "audio/mpeg":  ".mp3",
    "audio/mp4":   ".m4a",
    "audio/m4a":   ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/ogg":   ".ogg",
    "audio/wav":   ".wav",
    "audio/webm":  ".webm",
}


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

        suffix = ".mp4" if is_video else AUDIO_SUFFIX_MAP.get(content_type, ".mp3")
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
        whisper_seconds = transcript.get("duration_seconds", duration)
        if not text:
            raise HTTPException(status_code=422, detail="No speech detected in media.")

        # Translate
        result = await translator.translate(text, localization)

        cost = build_cost_breakdown(
            whisper_seconds=whisper_seconds,
            gpt_input_tokens=result.get("gpt_input_tokens", 0),
            gpt_output_tokens=result.get("gpt_output_tokens", 0),
            deepl_characters=result.get("characters_used", 0),
        )

        return ImportMediaResponse(
            translated_text=result["translated_text"],
            source_language_detected=result.get("detected_source_language"),
            duration_seconds=round(duration, 2),
            cost_breakdown=cost,
        )

    finally:
        cleanup(*filter(None, [media_path, audio_path]))