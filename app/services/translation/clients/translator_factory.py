import logging
from app.core.config import settings
from app.services.translation.clients.deepl_client import DeepLClient, OpenAITranslator
from app.services.translation.prompts.localization_prompts import DEEPL_UNSUPPORTED

logger = logging.getLogger(__name__)


# ── Hybrid Translator ─────────────────────────────────────────────────────────

class HybridTranslator:
    """
    DeepL → GPT-4o pipeline.

    Flow:
    1. If language is in DEEPL_UNSUPPORTED → skip DeepL, use GPT full translation
    2. Otherwise → DeepL for raw translation → GPT for localization polish

    This gives DeepL's linguistic accuracy for supported languages,
    with GPT's regional/cultural awareness on top.
    """

    def __init__(self) -> None:
        self.deepl = DeepLClient()
        self.openai = OpenAITranslator()

    async def translate(self, text: str, localization) -> dict:
        language = localization.target_language.strip().lower()

        # Languages DeepL can't handle — go straight to GPT full translation
        if language in DEEPL_UNSUPPORTED:
            logger.info(
                "Language '%s' not supported by DeepL — using GPT-only translation.",
                localization.target_language,
            )
            return await self.openai.translate(text, localization)

        # Step 1 — DeepL raw translation
        try:
            deepl_result = await self.deepl.translate(text, localization)
            raw_translation = deepl_result["translated_text"]
            detected_language = deepl_result.get("detected_source_language")
            logger.debug("DeepL raw translation: %s", raw_translation)
        except Exception as e:
            # DeepL failed — fall back to GPT full translation silently
            logger.warning(
                "DeepL failed for language '%s', falling back to GPT: %s",
                localization.target_language,
                str(e),
            )
            return await self.openai.translate(text, localization)

        # Step 2 — GPT localization polish
        try:
            gpt_result = await self.openai.localize_only(raw_translation, localization)
            return {
                "translated_text": gpt_result["translated_text"],
                "detected_source_language": detected_language,
            }
        except Exception as e:
            # GPT localization failed — return DeepL output as-is
            logger.warning(
                "GPT localization failed for '%s/%s', returning DeepL output: %s",
                localization.target_language,
                localization.target_locale,
                str(e),
            )
            return {
                "translated_text": raw_translation,
                "detected_source_language": detected_language,
            }


# ── Fallback Translator ───────────────────────────────────────────────────────

class FallbackTranslator:
    """Tries primary, silently falls back to secondary on any error."""

    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback

    async def translate(self, text, localization):
        try:
            return await self.primary.translate(text, localization)
        except Exception as e:
            logger.warning("Primary translator failed, using fallback: %s", str(e))
            return await self.fallback.translate(text, localization)


# ── Factory ───────────────────────────────────────────────────────────────────

def get_translator_client():
    """
    Returns the appropriate translator based on config.

    Modes (TRANSLATOR_BACKEND in .env):
      "openai"  → GPT-4o only (translate + localize in one call)
      "deepl"   → DeepL only (no localization layer)
      "hybrid"  → DeepL raw translation → GPT-4o localization polish
      "auto"    → reads OPENAI_TRANSLATION_ENABLED / DEEPL_TRANSLATION_ENABLED flags

    Default: "openai"
    """
    backend = settings.TRANSLATOR_BACKEND.strip().lower()

    if backend == "openai":
        logger.info("Translator: OpenAI GPT-4o only")
        return OpenAITranslator()

    if backend == "deepl":
        logger.info("Translator: DeepL only")
        return DeepLClient()

    if backend == "hybrid":
        logger.info("Translator: Hybrid (DeepL → GPT-4o)")
        return HybridTranslator()

    # auto mode — reads feature flags
    openai_enabled = bool(settings.OPENAI_TRANSLATION_ENABLED)
    deepl_enabled = bool(settings.DEEPL_TRANSLATION_ENABLED)

    if openai_enabled and deepl_enabled:
        logger.info("Translator: Hybrid (auto — both enabled)")
        return HybridTranslator()

    if openai_enabled:
        logger.info("Translator: OpenAI GPT-4o only (auto)")
        return OpenAITranslator()

    if deepl_enabled:
        logger.info("Translator: DeepL only (auto)")
        return DeepLClient()

    raise RuntimeError(
        "No translation backend enabled. "
        "Set TRANSLATOR_BACKEND to 'openai', 'deepl', or 'hybrid' in .env, "
        "or enable OPENAI_TRANSLATION_ENABLED / DEEPL_TRANSLATION_ENABLED."
    )
#  prev working ver starts here
# from app.core.config import settings
# from app.services.translation.clients.deepl_client import DeepLClient, OpenAITranslator


# class FallbackTranslator:
#     def __init__(self, primary, fallback):
#         self.primary = primary
#         self.fallback = fallback

#     async def translate(self, text, localization):
#         try:
#             return await self.primary.translate(text, localization)
#         except Exception:
#             return await self.fallback.translate(text, localization)


# def get_translator_client():
#     backend = settings.TRANSLATOR_BACKEND.strip().lower()

#     if backend == "openai":
#         return OpenAITranslator()

#     if backend == "deepl":
#         return DeepLClient()

#     openai_enabled = bool(settings.OPENAI_TRANSLATION_ENABLED)
#     deepl_enabled = bool(settings.DEEPL_TRANSLATION_ENABLED)

#     if openai_enabled and deepl_enabled:
#         return OpenAITranslator()

#     if openai_enabled:
#         return OpenAITranslator()

#     if deepl_enabled:
#         return DeepLClient()

#     raise RuntimeError(
#         "No translation backend is enabled. Set OPENAI_TRANSLATION_ENABLED or DEEPL_TRANSLATION_ENABLED to true."
#     )
# prev working ver ends here