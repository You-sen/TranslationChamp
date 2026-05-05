from app.services.translation.clients.translator_factory import get_translator_client
from app.schemas.translate_schema import LocalizationParams, TextTranslateResponse

translator = get_translator_client()


async def handle_text_translation(
    text: str,
    localization: LocalizationParams,
) -> TextTranslateResponse:
    result = await translator.translate(text, localization)
    return TextTranslateResponse(
        translated_text=result["translated_text"],
        source_language_detected=result.get("detected_source_language"),
    )