from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.schemas.translate_schema import LocalizationParams
from app.services.translation.clients.whisper_client import WhisperClient
from app.services.translation.clients.elevenlabs_client import ElevenLabsClient
from app.services.translation.clients.translator_factory import get_translator_client
from app.services.translation.utils.file_utils import save_upload, cleanup, temp_path
from app.services.translation.utils.ffmpeg_utils import get_duration, change_tempo
import aiofiles

whisper = WhisperClient()
translator = get_translator_client()
elevenlabs = ElevenLabsClient()


async def handle_voice_translation(
    audio_file: UploadFile,
    localization: LocalizationParams,
) -> bytes:
    """
    1. Save upload
    2. Validate duration (max 45s)
    3. Transcribe with Whisper
    4. Translate with DeepL (localized)
    5. Clone user's voice via ElevenLabs
    6. Synthesize translated text with cloned voice
    7. Delete cloned voice
    8. Return MP3 bytes
    """
    audio_path: Path | None = None
    cloned_voice_id: str | None = None

    try:
        suffix = _audio_suffix(audio_file.content_type)
        audio_path = await save_upload(audio_file, suffix)

        # Validate duration
        duration = await get_duration(audio_path)
        if duration > settings.MAX_VOICE_DURATION_SECONDS:
            raise HTTPException(
                status_code=422,
                detail=f"Audio exceeds maximum of {settings.MAX_VOICE_DURATION_SECONDS}s (got {duration:.1f}s).",
            )

        # Step 1: Transcribe
        transcript = await whisper.transcribe(audio_path)
        text = transcript["text"]
        if not text:
            raise HTTPException(status_code=422, detail="No speech detected in audio.")

        # Step 2: Translate
        result = await translator.translate(text, localization)
        translated_text = result["translated_text"]

        # Step 3: Clone user's voice and use it for synthesis.
        cloned_voice_id = await elevenlabs.clone_voice(
            audio_path,
            content_type=audio_file.content_type,
        )

        # Step 4: Synthesize with cloned voice
        audio_bytes = await elevenlabs.synthesize(translated_text, cloned_voice_id)

        # Optionally adjust playback speed if configured
        rate = settings.DEFAULT_SPEECH_RATE
        if rate != 1.0:
            tmp_in = temp_path(".mp3")
            tmp_out = temp_path(".mp3")
            try:
                # write bytes to temp file
                async with aiofiles.open(tmp_in, "wb") as f:
                    await f.write(audio_bytes)

                # change tempo
                await change_tempo(tmp_in, tmp_out, rate)

                # read adjusted audio
                async with aiofiles.open(tmp_out, "rb") as f:
                    adjusted = await f.read()
                audio_bytes = adjusted
            finally:
                cleanup(tmp_in, tmp_out)

        return audio_bytes

    finally:
        # Always clean up cloned voice and temp file
        if cloned_voice_id:
            try:
                await elevenlabs.delete_voice(cloned_voice_id)
            except Exception:
                pass  # best-effort cleanup
        if audio_path:
            cleanup(audio_path)


def _audio_suffix(content_type: str | None) -> str:
    mapping = {
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
        "audio/ogg": ".ogg",
        "audio/wav": ".wav",
        "audio/webm": ".webm",
        "audio/x-m4a": ".m4a",
    }
    return mapping.get(content_type or "", ".mp3")

# from pathlib import Path
# from fastapi import UploadFile, HTTPException

# from app.core.config import settings
# from app.schemas.translate_schema import LocalizationParams
# from app.services.translation.clients.whisper_client import WhisperClient
# from app.services.translation.clients.deepl_client import DeepLClient
# from app.services.translation.clients.elevenlabs_client import ElevenLabsClient
# from app.services.translation.utils.file_utils import save_upload, cleanup
# from app.services.translation.utils.ffmpeg_utils import get_duration

# whisper = WhisperClient()
# deepl = DeepLClient()
# elevenlabs = ElevenLabsClient()


# async def handle_voice_translation(
#     audio_file: UploadFile,
#     localization: LocalizationParams,
# ) -> bytes:
#     """
#     1. Save upload → 2. Validate duration → 3. Transcribe (Whisper)
#     → 4. Translate (DeepL) → 5. Synthesize (ElevenLabs) → return MP3 bytes
#     """
#     audio_path: Path | None = None
#     try:
#         # Determine suffix from content type
#         suffix = _audio_suffix(audio_file.content_type)
#         audio_path = await save_upload(audio_file, suffix)

#         # Validate duration
#         duration = await get_duration(audio_path)
#         if duration > settings.MAX_VOICE_DURATION_SECONDS:
#             raise HTTPException(
#                 status_code=422,
#                 detail=f"Audio exceeds maximum duration of {settings.MAX_VOICE_DURATION_SECONDS}s (got {duration:.1f}s).",
#             )

#         # Step 1: Speech-to-text
#         transcript = await whisper.transcribe(audio_path)
#         text = transcript["text"]
#         if not text:
#             raise HTTPException(status_code=422, detail="Could not transcribe audio — no speech detected.")

#         # Step 2: Translate
#         translation = await deepl.translate(text, localization)
#         translated_text = translation["translated_text"]

#         # Step 3: Synthesize
#         audio_bytes = await elevenlabs.synthesize(translated_text)
#         return audio_bytes

#     finally:
#         if audio_path:
#             cleanup(audio_path)


# def _audio_suffix(content_type: str | None) -> str:
#     mapping = {
#         "audio/mpeg": ".mp3",
#         "audio/mp4": ".m4a",
#         "audio/ogg": ".ogg",
#         "audio/wav": ".wav",
#         "audio/webm": ".webm",
#         "audio/x-m4a": ".m4a",
#     }
#     return mapping.get(content_type or "", ".mp3")