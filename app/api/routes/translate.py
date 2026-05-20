import json
import uuid

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, BackgroundTasks
from fastapi.responses import Response

from app.schemas.translate_schema import TextTranslateRequest, TextTranslateResponse, LocalizationParams
from app.schemas.voice_schema import VoiceTranslateResponse
from app.schemas.video_schema import VideoTranslateResponse
from app.schemas.import_schema import ImportMediaResponse
from app.services.translation import service
from app.services.translation.utils.audio_cache import store_audio, get_audio
from app.services.translation.utils.usage_reporter import report_usage
from app.services.translation.clients.deepl_client import DeepLClient

router = APIRouter(prefix="/translate", tags=["Translation"])

# Used to resolve target language name → ISO code for the reporter
_deepl = DeepLClient()


def _to_language_code(localization: LocalizationParams) -> str:
    """Resolve target language name to uppercase ISO code for usage reporting."""
    try:
        return _deepl._resolve_language_code(
            localization.target_language,
            localization.target_locale,
        ).split("-")[0].upper()  # ES-LA → ES, PT-BR → PT, EN-US → EN
    except Exception:
        return localization.target_language[:2].upper()


# ── 1. Text ───────────────────────────────────────────────────────────────────

@router.post("/text", response_model=TextTranslateResponse, summary="Translate typed text")
async def translate_text(
    request: TextTranslateRequest,
    background_tasks: BackgroundTasks,
):
    result = await service.translate_text(request.text, request.localization)

    from_lang = (result.source_language_detected or "").upper()
    to_lang = _to_language_code(request.localization)

    background_tasks.add_task(
        report_usage,
        user_token=request.user_token,
        endpoint="text",
        duration_seconds=0.0,
        cost_breakdown=result.cost_breakdown or {},
        from_language_code=from_lang,
        to_language_code=to_lang,
        content_type=None,
    )

    return TextTranslateResponse(
        translated_text=result.translated_text,
        source_language_detected=result.source_language_detected,
    )


# ── 2. Voice ──────────────────────────────────────────────────────────────────

@router.post(
    "/voice",
    summary="Translate voice message — user's voice preserved (max 45s)",
    response_model=VoiceTranslateResponse,
)
async def translate_voice_with_request(
    request: Request,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(..., description="Voice recording (MP3, WAV, OGG, WebM, M4A)"),
    user_token: str = Form(..., description="User token"),
    localization: str = Form(
        ...,
        description='JSON: {"target_language":"Spanish","target_locale":"Colombia","style":"conversational"}',
    ),
):
    loc = _parse_localization(localization)
    audio_bytes, duration, cost = await service.translate_voice(audio, loc)

    token = uuid.uuid4().hex[:10]
    await store_audio(token, audio_bytes, media_type="audio/mpeg")

    base = str(request.base_url).rstrip("/")
    audio_url = f"{base}/api/v1/translate/voice/play/{token}"

    from_lang = (cost.get("detected_source_language") or "").upper()
    to_lang = _to_language_code(loc)

    background_tasks.add_task(
        report_usage,
        user_token=user_token,
        endpoint="voice",
        duration_seconds=duration,
        cost_breakdown=cost,
        from_language_code=from_lang,
        to_language_code=to_lang,
        content_type=audio.content_type,
    )

    return VoiceTranslateResponse(audio_url=audio_url)


@router.get(
    "/voice/play/{token}",
    summary="Play ephemeral synthesized audio",
    responses={200: {"content": {"audio/mpeg": {}}, "description": "Ephemeral MP3 audio"}},
)
async def play_ephemeral_audio(token: str):
    item = await get_audio(token)
    if not item:
        raise HTTPException(status_code=404, detail="Audio not found or expired")
    return Response(content=item["bytes"], media_type=item.get("media_type", "audio/mpeg"))


# ── 3. Video ──────────────────────────────────────────────────────────────────

@router.post(
    "/video",
    response_model=VideoTranslateResponse,
    summary="Translate video — returns translated text for frontend overlay (max 90s)",
)
async def translate_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(..., description="Video file (MP4, MOV, WebM)"),
    user_token: str = Form(..., description="User token"),
    localization: str = Form(
        ...,
        description='JSON: {"target_language":"French","target_locale":"France","style":"conversational"}',
    ),
):
    loc = _parse_localization(localization)
    result = await service.translate_video(video, loc)

    from_lang = (result.source_language_detected or "").upper()
    to_lang = _to_language_code(loc)

    background_tasks.add_task(
        report_usage,
        user_token=user_token,
        endpoint="video",
        duration_seconds=result.duration_seconds or 0.0,
        cost_breakdown=result.cost_breakdown or {},
        from_language_code=from_lang,
        to_language_code=to_lang,
        content_type=video.content_type,
    )

    return VideoTranslateResponse(
        translated_text=result.translated_text,
        source_language_detected=result.source_language_detected,
        segments=result.segments,
    )


# ── 4. Import ─────────────────────────────────────────────────────────────────

@router.post(
    "/import",
    response_model=ImportMediaResponse,
    summary="Import audio/video — returns translated text (max 90s)",
)
async def import_media(
    background_tasks: BackgroundTasks,
    media: UploadFile = File(..., description="Audio or video file"),
    user_token: str = Form(..., description="User token"),
    localization: str = Form(
        ...,
        description='JSON: {"target_language":"German","target_locale":"Germany","style":"conversational"}',
    ),
):
    loc = _parse_localization(localization)
    result = await service.import_media(media, loc)

    from_lang = (result.source_language_detected or "").upper()
    to_lang = _to_language_code(loc)

    background_tasks.add_task(
        report_usage,
        user_token=user_token,
        endpoint="import",
        duration_seconds=result.duration_seconds or 0.0,
        cost_breakdown=result.cost_breakdown or {},
        from_language_code=from_lang,
        to_language_code=to_lang,
        content_type=media.content_type,
    )

    return ImportMediaResponse(
        translated_text=result.translated_text,
        source_language_detected=result.source_language_detected,
    )


# ── Helper ────────────────────────────────────────────────────────────────────

def _parse_localization(raw: str) -> LocalizationParams:
    try:
        return LocalizationParams(**json.loads(raw))
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid localization JSON: {e}")  
# This part is old one. upper is working part

# import json
# from fastapi import APIRouter, UploadFile, File, Form, HTTPException
# from fastapi.responses import Response

# from app.schemas.translate_schema import TextTranslateRequest, TextTranslateResponse, LocalizationParams
# from app.schemas.import_schema import ImportMediaResponse
# from app.services.translation import service

# router = APIRouter(prefix="/translate", tags=["Translation"])


# # ─── 1. Text Translation ──────────────────────────────────────────────────────

# @router.post("/text", response_model=TextTranslateResponse, summary="Translate typed text")
# async def translate_text(request: TextTranslateRequest):
#     """
#     Translates typed text into the target language with locale-aware,
#     conversational phrasing via DeepL.
#     """
#     return await service.translate_text(request.text, request.localization)


# # ─── 2. Voice Translation ─────────────────────────────────────────────────────

# @router.post(
#     "/voice",
#     summary="Translate a voice message (max 45s)",
#     response_class=Response,
#     responses={200: {"content": {"audio/mpeg": {}}, "description": "Translated audio (MP3)"}},
# )
# async def translate_voice(
#     audio: UploadFile = File(..., description="Voice recording (MP3, WAV, OGG, WebM, M4A)"),
#     localization: str = Form(
#         ...,
#         description='JSON string: {"target_language":"Spanish","target_locale":"Colombia","style":"conversational"}',
#     ),
# ):
#     """
#     Transcribes audio → translates → synthesizes with ElevenLabs.
#     Returns translated MP3 audio. No transcript is exposed.
#     """
#     loc = _parse_localization(localization)
#     audio_bytes = await service.translate_voice(audio, loc)
#     return Response(content=audio_bytes, media_type="audio/mpeg")


# # ─── 3. Video Subtitle Translation ───────────────────────────────────────────

# @router.post(
#     "/video",
#     summary="Translate video subtitles (max 90s)",
#     response_class=Response,
#     responses={200: {"content": {"video/mp4": {}}, "description": "Video with burned-in translated subtitles"}},
# )
# async def translate_video(
#     video: UploadFile = File(..., description="Video file (MP4, MOV, WebM)"),
#     localization: str = Form(
#         ...,
#         description='JSON string: {"target_language":"French","target_locale":"France","style":"conversational"}',
#     ),
# ):
#     """
#     Extracts audio → transcribes → translates segments → burns subtitles.
#     Returns MP4 with hard-coded translated subtitles. No voice dubbing.
#     """
#     loc = _parse_localization(localization)
#     video_bytes = await service.translate_video(video, loc)
#     return Response(content=video_bytes, media_type="video/mp4")


# # ─── 4. Import Media ──────────────────────────────────────────────────────────

# @router.post(
#     "/import",
#     response_model=ImportMediaResponse,
#     summary="Import audio/video and get translated transcript (max 90s)",
# )
# async def import_media(
#     media: UploadFile = File(..., description="Audio or video file"),
#     localization: str = Form(
#         ...,
#         description='JSON string: {"target_language":"German","target_locale":"Germany","style":"conversational"}',
#     ),
# ):
#     """
#     Understands an uploaded audio or video file and returns
#     the translated text. No audio/video output.
#     """
#     loc = _parse_localization(localization)
#     return await service.import_media(media, loc)


# # ─── Helpers ──────────────────────────────────────────────────────────────────

# def _parse_localization(raw: str) -> LocalizationParams:
#     try:
#         data = json.loads(raw)
#         return LocalizationParams(**data)
#     except (json.JSONDecodeError, ValueError) as e:
#         raise HTTPException(status_code=422, detail=f"Invalid localization JSON: {e}")