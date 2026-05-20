from typing import List
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.schemas.translate_schema import LocalizationParams
from app.schemas.video_schema import VideoTranslateResponse
from app.services.translation.clients.whisper_client import WhisperClient
from app.services.translation.clients.translator_factory import get_translator_client
from app.services.translation.utils.file_utils import save_upload, cleanup, temp_path
from app.services.translation.utils.ffmpeg_utils import extract_audio, get_duration
from app.services.translation.utils.cost_tracker import build_cost_breakdown

whisper = WhisperClient()
translator = get_translator_client()


async def handle_video_translation(
    video_file: UploadFile,
    localization: LocalizationParams,
) -> VideoTranslateResponse:
    """
    1. Save video
    2. Validate duration (max 90s)
    3. Extract audio
    4. Transcribe with Whisper
    5. Translate with DeepL (localized)
    6. Return translated text — frontend handles overlay
    """
    video_path = audio_path = None

    try:
        video_path = await save_upload(video_file, ".mp4")

        # Validate duration
        duration = await get_duration(video_path)
        if duration > settings.MAX_VIDEO_DURATION_SECONDS:
            raise HTTPException(
                status_code=422,
                detail=f"Video exceeds maximum of {settings.MAX_VIDEO_DURATION_SECONDS}s (got {duration:.1f}s).",
            )

        # Extract audio
        audio_path = temp_path(".mp3")
        await extract_audio(video_path, audio_path)

        # Transcribe (we need segments for subtitle timing)
        transcript = await whisper.transcribe(audio_path)
        text = transcript.get("text", "")
        segments = transcript.get("segments", [])
        whisper_seconds = transcript.get("duration_seconds", duration)
        if not segments:
            raise HTTPException(status_code=422, detail="No speech detected in video.")

        # Translate the whole text for backward-compatible `translated_text`
        overall_result = await translator.translate(text, localization)

        # Translate each segment individually so we can return per-segment timing
        translated_segments: List[dict] = []
        total_gpt_input = overall_result.get("gpt_input_tokens", 0)
        total_gpt_output = overall_result.get("gpt_output_tokens", 0)
        total_deepl_chars = overall_result.get("characters_used", 0)

        for seg in segments:
            seg_text = seg.get("text", "").strip()
            if not seg_text:
                continue
            result = await translator.translate(seg_text, localization)
            total_gpt_input += result.get("gpt_input_tokens", 0)
            total_gpt_output += result.get("gpt_output_tokens", 0)
            total_deepl_chars += result.get("characters_used", 0)
            translated_segments.append(
                {
                    "start": seg.get("start", 0.0),
                    "end": seg.get("end", 0.0),
                    "text": result["translated_text"],
                }
            )

        cost = build_cost_breakdown(
            whisper_seconds=whisper_seconds,
            gpt_input_tokens=total_gpt_input,
            gpt_output_tokens=total_gpt_output,
            deepl_characters=total_deepl_chars,
        )

        return VideoTranslateResponse(
            translated_text=overall_result["translated_text"],
            source_language_detected=overall_result.get("detected_source_language") or transcript.get("language"),
            segments=translated_segments,
            duration_seconds=round(duration, 2),
            cost_breakdown=cost,
        )

    finally:
        cleanup(*filter(None, [video_path, audio_path]))

# import json
# from pathlib import Path
# from fastapi import UploadFile, HTTPException

# from app.core.config import settings
# from app.schemas.translate_schema import LocalizationParams
# from app.services.translation.clients.whisper_client import WhisperClient
# from app.services.translation.clients.deepl_client import DeepLClient
# from app.services.translation.utils.file_utils import save_upload, cleanup, temp_path, build_srt
# from app.services.translation.utils.ffmpeg_utils import extract_audio, get_duration, burn_subtitles

# whisper = WhisperClient()
# deepl = DeepLClient()


# async def handle_video_translation(
#     video_file: UploadFile,
#     localization: LocalizationParams,
# ) -> bytes:
#     """
#     1. Save video → 2. Validate duration → 3. Extract audio
#     → 4. Transcribe (Whisper, get segments) → 5. Translate each segment (DeepL)
#     → 6. Build SRT → 7. Burn subtitles → return MP4 bytes
#     """
#     video_path = audio_path = srt_path = output_path = None
#     try:
#         video_path = await save_upload(video_file, ".mp4")

#         # Validate duration
#         duration = await get_duration(video_path)
#         if duration > settings.MAX_VIDEO_DURATION_SECONDS:
#             raise HTTPException(
#                 status_code=422,
#                 detail=f"Video exceeds maximum duration of {settings.MAX_VIDEO_DURATION_SECONDS}s.",
#             )

#         # Extract audio
#         audio_path = temp_path(".mp3")
#         await extract_audio(video_path, audio_path)

#         # Transcribe — we need segments for subtitle timing
#         transcript_data = await _transcribe_with_segments(audio_path)
#         segments = transcript_data.get("segments", [])
#         if not segments:
#             raise HTTPException(status_code=422, detail="No speech detected in video.")

#         # Translate each segment text
#         translated_segments = []
#         for seg in segments:
#             result = await deepl.translate(seg["text"], localization)
#             translated_segments.append({
#                 "start": seg["start"],
#                 "end": seg["end"],
#                 "text": result["translated_text"],
#             })

#         # Build SRT file
#         srt_content = build_srt(translated_segments)
#         srt_path = temp_path(".srt")
#         srt_path.write_text(srt_content, encoding="utf-8")

#         # Burn subtitles into video
#         output_path = temp_path(".mp4")
#         await burn_subtitles(video_path, srt_path, output_path)

#         # Read output
#         return output_path.read_bytes()

#     finally:
#         cleanup(*filter(None, [video_path, audio_path, srt_path, output_path]))


# async def _transcribe_with_segments(audio_path: Path) -> dict:
#     """
#     Call Whisper and return full verbose JSON including segments.
#     We call the OpenAI API directly here to get segment timing.
#     """
#     import httpx
#     from app.core.config import settings

#     headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
#     async with httpx.AsyncClient(timeout=60.0) as client:
#         with open(audio_path, "rb") as f:
#             files = {"file": (audio_path.name, f, "audio/mpeg")}
#             data = {"model": "whisper-1", "response_format": "verbose_json"}
#             response = await client.post(
#                 "https://api.openai.com/v1/audio/transcriptions",
#                 headers=headers,
#                 files=files,
#                 data=data,
#             )
#             response.raise_for_status()
#     return response.json()