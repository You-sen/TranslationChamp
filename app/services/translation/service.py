"""
Central service router — delegates to the appropriate handler
based on translation type. This keeps the route layer thin.
"""
from fastapi import UploadFile
from app.schemas.translate_schema import LocalizationParams, TextTranslateResponse
from app.schemas.import_schema import ImportMediaResponse


async def translate_text(text: str, localization: LocalizationParams) -> TextTranslateResponse:
    from app.services.translation.handlers.text import handle_text_translation
    return await handle_text_translation(text, localization)


async def translate_voice(audio_file: UploadFile, localization: LocalizationParams) -> bytes:
    from app.services.translation.handlers.voice import handle_voice_translation
    return await handle_voice_translation(audio_file, localization)


async def translate_video(video_file: UploadFile, localization: LocalizationParams) -> bytes:
    from app.services.translation.handlers.video import handle_video_translation
    return await handle_video_translation(video_file, localization)


async def import_media(media_file: UploadFile, localization: LocalizationParams) -> ImportMediaResponse:
    from app.services.translation.handlers.import_media import handle_import_media
    return await handle_import_media(media_file, localization)