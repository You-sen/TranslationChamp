# from pathlib import Path
# from fastapi import UploadFile, HTTPException

# from app.core.config import settings
# from app.schemas.translate_schema import LocalizationParams
# from app.services.translation.clients.whisper_client import WhisperClient
# from app.services.translation.clients.elevenlabs_client import ElevenLabsClient
# from app.services.translation.clients.translator_factory import get_translator_client
# from app.services.translation.utils.file_utils import save_upload, cleanup, temp_path
# from app.services.translation.utils.ffmpeg_utils import get_duration, change_tempo
# from app.services.translation.utils.cost_tracker import build_cost_breakdown
# import aiofiles

# whisper = WhisperClient()
# translator = get_translator_client()
# elevenlabs = ElevenLabsClient()


# async def handle_voice_translation(
#     audio_file: UploadFile,
#     localization: LocalizationParams,
#     existing_voice_id: str | None = None,
# ) -> tuple[bytes, float, dict, str]:
#     """
#     1. Save upload
#     2. Validate duration (max 60s)
#     3. Transcribe with Whisper
#     4. Translate
#     5. Clone voice if no existing_voice_id, otherwise reuse it
#     6. Synthesize translated text with voice
#     7. Delete cloned voice ONLY if we created it this request
#     8. Return (MP3 bytes, duration, cost_breakdown, voice_id)
#     """
#     audio_path: Path | None = None
#     newly_cloned_voice_id: str | None = None

#     try:
#         suffix = _audio_suffix(audio_file.content_type)
#         audio_path = await save_upload(audio_file, suffix)

#         # Validate duration
#         duration = await get_duration(audio_path)
#         if duration > settings.MAX_VOICE_DURATION_SECONDS:
#             raise HTTPException(
#                 status_code=422,
#                 detail=f"Audio exceeds maximum of {settings.MAX_VOICE_DURATION_SECONDS}s (got {duration:.1f}s).",
#             )

#         # Step 1: Transcribe
#         transcript = await whisper.transcribe(audio_path)
#         text = transcript["text"]
#         whisper_seconds = transcript.get("duration_seconds", duration)
#         if not text:
#             raise HTTPException(status_code=422, detail="No speech detected in audio.")

#         # Step 2: Translate
#         result = await translator.translate(text, localization)
#         translated_text = result["translated_text"]

#         # Step 3: Use existing voice or clone a new one
#         if existing_voice_id:
#             # Reuse saved voice — no clone operation used, limit preserved
#             voice_id = existing_voice_id
#         else:
#             # First request — clone voice and return the ID to frontend to store
#             newly_cloned_voice_id = await elevenlabs.clone_voice(
#                 audio_path,
#                 content_type=audio_file.content_type,
#             )
#             voice_id = newly_cloned_voice_id

#         # Step 4: Synthesize with voice
#         audio_bytes, elevenlabs_chars = await elevenlabs.synthesize(translated_text, voice_id)

#         # Build cost breakdown
#         cost = build_cost_breakdown(
#             whisper_seconds=whisper_seconds,
#             gpt_input_tokens=result.get("gpt_input_tokens", 0),
#             gpt_output_tokens=result.get("gpt_output_tokens", 0),
#             deepl_characters=result.get("characters_used", 0),
#             elevenlabs_tts_characters=elevenlabs_chars,
#         )
#         cost["detected_source_language"] = result.get("detected_source_language") or transcript.get("language")

#         # Optionally adjust playback speed if configured
#         rate = settings.DEFAULT_SPEECH_RATE
#         if rate != 1.0:
#             tmp_in = temp_path(".mp3")
#             tmp_out = temp_path(".mp3")
#             try:
#                 async with aiofiles.open(tmp_in, "wb") as f:
#                     await f.write(audio_bytes)
#                 await change_tempo(tmp_in, tmp_out, rate)
#                 async with aiofiles.open(tmp_out, "rb") as f:
#                     adjusted = await f.read()
#                 audio_bytes = adjusted
#                 return audio_bytes, round(duration, 2), cost, voice_id
#             finally:
#                 cleanup(tmp_in, tmp_out)

#         return audio_bytes, round(duration, 2), cost, voice_id

#     finally:
#         # Only delete if we cloned a NEW voice this request
#         # Do NOT delete if we reused an existing_voice_id from frontend
#         # if newly_cloned_voice_id:
#         #     try:
#         #         await elevenlabs.delete_voice(newly_cloned_voice_id)
#         #     except Exception:
#         #         pass
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

from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.schemas.translate_schema import LocalizationParams
from app.services.translation.clients.whisper_client import WhisperClient
from app.services.translation.clients.elevenlabs_client import ElevenLabsClient
from app.services.translation.clients.translator_factory import get_translator_client
from app.services.translation.utils.file_utils import save_upload, cleanup, temp_path
from app.services.translation.utils.ffmpeg_utils import get_duration, change_tempo
from app.services.translation.utils.cost_tracker import build_cost_breakdown
import aiofiles

whisper = WhisperClient()
translator = get_translator_client()
elevenlabs = ElevenLabsClient()


async def handle_voice_translation(
    audio_file: UploadFile,
    localization: LocalizationParams,
    existing_voice_id: str | None = None,
) -> tuple[bytes, float, dict, str]:
    """
    1. Save upload
    2. Validate duration (max 60s)
    3. Transcribe with Whisper
    4. Translate
    5. Clone voice if no existing_voice_id, otherwise reuse it
    6. Synthesize translated text with voice
    7. Delete cloned voice ONLY if we created it this request
    8. Return (MP3 bytes, duration, cost_breakdown, voice_id)
    """
    audio_path: Path | None = None
    newly_cloned_voice_id: str | None = None

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
        whisper_seconds = transcript.get("duration_seconds", duration)
        if not text:
            raise HTTPException(status_code=422, detail="No speech detected in audio.")

        # Step 2: Translate
        result = await translator.translate(text, localization)
        translated_text = result["translated_text"]

        # Step 3: Use existing voice or clone a new one
        if existing_voice_id:
            # Reuse saved voice — no clone operation used, limit preserved
            voice_id = existing_voice_id
        else:
            # First request — clone voice and return the ID to frontend to store
            newly_cloned_voice_id = await elevenlabs.clone_voice(
                audio_path,
                content_type=audio_file.content_type,
            )
            voice_id = newly_cloned_voice_id

        # Step 4: Synthesize with voice
        audio_bytes, elevenlabs_chars = await elevenlabs.synthesize(translated_text, voice_id)

        # Build cost breakdown
        cost = build_cost_breakdown(
            whisper_seconds=whisper_seconds,
            gpt_input_tokens=result.get("gpt_input_tokens", 0),
            gpt_output_tokens=result.get("gpt_output_tokens", 0),
            deepl_characters=result.get("characters_used", 0),
            elevenlabs_tts_characters=elevenlabs_chars,
        )
        cost["detected_source_language"] = result.get("detected_source_language") or transcript.get("language")

        # Optionally adjust playback speed if configured
        rate = settings.DEFAULT_SPEECH_RATE
        if rate != 1.0:
            tmp_in = temp_path(".mp3")
            tmp_out = temp_path(".mp3")
            try:
                async with aiofiles.open(tmp_in, "wb") as f:
                    await f.write(audio_bytes)
                await change_tempo(tmp_in, tmp_out, rate)
                async with aiofiles.open(tmp_out, "rb") as f:
                    adjusted = await f.read()
                audio_bytes = adjusted
                return audio_bytes, round(duration, 2), cost, voice_id
            finally:
                cleanup(tmp_in, tmp_out)

        return audio_bytes, round(duration, 2), cost, voice_id

    finally:
        # Only delete if we cloned a NEW voice this request
        # Do NOT delete if we reused an existing_voice_id from frontend
        # if newly_cloned_voice_id:
        #     try:
        #         await elevenlabs.delete_voice(newly_cloned_voice_id)
        #     except Exception:
        #         pass
        if audio_path:
            cleanup(audio_path)


def _audio_suffix(content_type: str | None) -> str:
    mapping = {
        "audio/mpeg":  ".mp3",
        "audio/mp4":   ".m4a",
        "audio/m4a":   ".m4a",
        "audio/x-m4a": ".m4a",
        "audio/ogg":   ".ogg",
        "audio/wav":   ".wav",
        "audio/webm":  ".webm",
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