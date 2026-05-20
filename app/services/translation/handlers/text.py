from app.services.translation.clients.translator_factory import get_translator_client
from app.schemas.translate_schema import LocalizationParams, TextTranslateResponse
from app.services.translation.utils.cost_tracker import build_cost_breakdown

translator = get_translator_client()


class TextTranslateInternalResponse(TextTranslateResponse):
    """
    Internal-only response — extends the public schema with cost data.
    cost_breakdown is used by translate.py to report to the other backend.
    Never serialized back to the frontend directly.
    """
    cost_breakdown: dict = {}


async def handle_text_translation(
    text: str,
    localization: LocalizationParams,
) -> TextTranslateInternalResponse:
    result = await translator.translate(text, localization)

    cost = build_cost_breakdown(
        gpt_input_tokens=result.get("gpt_input_tokens", 0),
        gpt_output_tokens=result.get("gpt_output_tokens", 0),
        deepl_characters=result.get("characters_used", 0),
    )

    return TextTranslateInternalResponse(
        translated_text=result["translated_text"],
        source_language_detected=result.get("detected_source_language"),
        cost_breakdown=cost,
    )