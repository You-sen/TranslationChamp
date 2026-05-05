from app.core.config import settings
from app.services.translation.clients.deepl_client import DeepLClient, OpenAITranslator


class FallbackTranslator:
    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback

    async def translate(self, text, localization):
        try:
            return await self.primary.translate(text, localization)
        except Exception:
            return await self.fallback.translate(text, localization)


def get_translator_client():
    backend = settings.TRANSLATOR_BACKEND.strip().lower()

    if backend == "openai":
        return OpenAITranslator()

    if backend == "deepl":
        return DeepLClient()

    openai_enabled = bool(settings.OPENAI_TRANSLATION_ENABLED)
    deepl_enabled = bool(settings.DEEPL_TRANSLATION_ENABLED)

    if openai_enabled and deepl_enabled:
        return OpenAITranslator()

    if openai_enabled:
        return OpenAITranslator()

    if deepl_enabled:
        return DeepLClient()

    raise RuntimeError(
        "No translation backend is enabled. Set OPENAI_TRANSLATION_ENABLED or DEEPL_TRANSLATION_ENABLED to true."
    )