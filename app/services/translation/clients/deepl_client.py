import httpx
import logging
from app.core.config import settings
from app.schemas.translate_schema import LocalizationParams

logger = logging.getLogger(__name__)


# LOCALIZATION_SYSTEM_PROMPT = (
#     "You are a professional localization expert. "
#     "Translate the following text into {language} as spoken in {locale}. "
#     "Use conversational, natural phrasing that reflects how a real local speaker would say it. "
#     "Preserve the emotional tone of the original message. "
#     "Avoid literal, word-for-word translation. "
#     "Do not add explanations — return only the translated text."
# )
LOCALIZATION_SYSTEM_PROMPT = (
    "You are a native-level localization expert and cultural linguist. "
    "Translate the following message into {language} as naturally spoken in {locale}. "
    "Sound exactly like someone from {locale} said this in a real casual conversation. "
    "Preserve the exact emotional weight of the original — not more, not less. "
    "Use the vocabulary, rhythm, fillers, and expressions that locals in {locale} actually use. "
    "Never add words, emotions, or meaning that were not in the original. "
    "Never remove words, emotions, or meaning that were in the original. "
    "Avoid textbook phrasing, robotic wording, and literal word-for-word translation. "
    "Do not add explanations, alternatives, or notes. "
    "Return only the final translated text."
)

class DeepLClient:
    """Translates text using DeepL API with localization context."""

    async def translate(self, text: str, localization: LocalizationParams) -> dict:
        """
        Returns dict:
          - translated_text: str
          - detected_source_language: str | None
        """
        # DeepL endpoint
        url = f"{settings.DEEPL_API_URL}/translate"
        headers = {
            "Authorization": f"DeepL-Auth-Key {settings.DEEPL_API_KEY}",
            "Content-Type": "application/json",
        }

        # Resolve a DeepL target language code (e.g. EN-US, PT-BR, ES)
        lang_code = self._resolve_language_code(localization.target_language, localization.target_locale)

        # Inject lightweight localization hints via the `context` field.
        context = (
            f"Translate for a speaker from {localization.target_locale}. "
            f"Style: {localization.style or 'conversational'}, preserve emotional tone, avoid literal translation."
        )

        payload = {
            "text": [text],
            "target_lang": lang_code,
            "context": context,
            "formality": "default",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        translation = data["translations"][0]
        return {
            "translated_text": translation["text"],
            "detected_source_language": translation.get("detected_source_language"),
        }

    def _resolve_language_code(self, language: str, locale: str) -> str:
        """Return a DeepL target language code for given human language and locale.

        Behavior:
        - If `language` already looks like a DeepL code (e.g. `en`, `EN-US`, `pt-BR`), normalize and return it.
        - Check explicit (language, locale) overrides (e.g. portuguese + brazil -> PT-BR).
        - Check region-specific overrides for languages that have multiple variants (en, pt).
        - Fall back to a generic language code (ES, FR, DE, ...).
        - As last resort, return the uppercased 2-letter language.
        """
        lang = (language or "").strip()
        loc = (locale or "").strip()
        if not lang:
            raise ValueError("Empty language passed to _resolve_language_code")

        lang_norm = lang.lower()
        loc_norm = loc.lower()

        # If caller already passed a code like 'en' or 'en-us' or 'EN-US', normalize it.
        def normalize_code(code: str) -> str:
            parts = [p for p in code.replace('_', '-').split('-') if p]
            if len(parts) == 1:
                return parts[0][:2].upper()
            return f"{parts[0][:2].upper()}-{parts[1].upper()}"

        # Accept explicit codes
        if len(lang) <= 5 and all(c.isalpha() or c in "-_" for c in lang):
            try:
                return normalize_code(lang)
            except Exception:
                pass

        # Explicit (language, locale) overrides -> DeepL codes
        locale_map = {
            ("portuguese", "brazil"): "PT-BR",
            ("portuguese", "brasil"): "PT-BR",
            ("portuguese", "portugal"): "PT-PT",
            ("english", "united states"): "EN-US",
            ("english", "us"): "EN-US",
            ("english", "united kingdom"): "EN-GB",
            ("english", "uk"): "EN-GB",
            ("chinese", "china"): "ZH",
            ("chinese", "simplified"): "ZH",
        }

        key = (lang_norm, loc_norm)
        if key in locale_map:
            return locale_map[key]

        # Region overrides for languages with multiple variants
        region_overrides = {
            "english": {"us": "EN-US", "united states": "EN-US", "uk": "EN-GB", "united kingdom": "EN-GB", "gb": "EN-GB"},
            "portuguese": {"brazil": "PT-BR", "brasil": "PT-BR", "portugal": "PT-PT"},
        }
        if lang_norm in region_overrides and loc_norm in region_overrides[lang_norm]:
            return region_overrides[lang_norm][loc_norm]

        # Broad language name -> DeepL code map
        generic_map = {
            "spanish": "ES",
            "espanol": "ES",
            "french": "FR",
            "german": "DE",
            "italian": "IT",
            "japanese": "JA",
            "korean": "KO",
            "arabic": "AR",
            "russian": "RU",
            "dutch": "NL",
            "polish": "PL",
            "turkish": "TR",
            "portuguese": "PT-PT",
            "english": "EN-US",
            "chinese": "ZH",
            "hindi": "HI",
            "swedish": "SV",
            "danish": "DA",
            "norwegian": "NB",
            "finnish": "FI",
            "czech": "CS",
            "romanian": "RO",
            "hungarian": "HU",
            "slovak": "SK",
            "bulgarian": "BG",
            "greek": "EL",
            "ukrainian": "UK",
            "indonesian": "ID",
            "latvian": "LV",
            "lithuanian": "LT",
            "slovenian": "SL",
            "estonian": "ET",
            "bengali": "BN",
            "bangla": "BN",
            "urdu": "UR",
            "persian": "FA",
            "farsi": "FA",
            "tagalog": "TL",
            "malay": "MS",
        }

        if lang_norm in generic_map:
            return generic_map[lang_norm]

        # If locale itself looks like a DeepL code (e.g. 'us' with language 'en'), try to combine
        if loc_norm and len(loc_norm) <= 3 and loc_norm.isalpha():
            candidate = f"{lang_norm[:2].upper()}-{loc_norm[:2].upper()}"
            logger.debug("Falling back to candidate code %s for %s/%s", candidate, language, locale)
            return candidate

        # Last resort: uppercase first two chars of language
        fallback = lang_norm[:2].upper()
        logger.debug("Falling back to generic code %s for language=%s locale=%s", fallback, language, locale)
        return fallback


class OpenAITranslator:
    """Translates text using OpenAI Chat Completions."""

    def __init__(self) -> None:
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def translate(self, text: str, localization: LocalizationParams) -> dict:
        # system_prompt = (
        #     "You are a professional localization expert. "
        #     "Translate the following text into the requested language and locale. "
        #     "Use conversational, natural phrasing that reflects how a real local speaker would say it. "
        #     "Preserve the emotional tone of the original message. "
        #     "Avoid literal, word-for-word translation. "
        #     "Return only the translated text."
        # )
        system_prompt = """
        You are a native-level localization expert and cultural linguist.
        Your job is to translate spoken conversational messages — the kind people send 
        each other in voice notes, chats, and casual calls.

        Rules you must always follow:
        - Translate meaning and emotion, not words
        - Match the energy of the original exactly — if it's chill, keep it chill. If it's frustrated, keep that frustration. If it's warm, keep it warm.
        - Never add words, emotions, or meaning that weren't in the original
        - Never remove words, emotions, or meaning that were in the original
        - Use contractions, slang, and fillers the way real people in that region actually speak
        - Avoid textbook phrasing — no one talks like a dictionary
        - If the original has hesitation or informality, reflect that
        - Return only the final translated text. No explanations, no alternatives, no notes.
        """
        user_prompt = (
            f"Translate into {localization.target_language} as spoken in {localization.target_locale}. "
            f"Style: {localization.style}.\n\n"
            f"Text:\n{text}"
        )

        response = await self.client.chat.completions.create(
            model=settings.OPENAI_TRANSLATION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=settings.OPENAI_TRANSLATION_MAX_OUTPUT_TOKENS,
        )

        translated_text = (response.choices[0].message.content or "").strip()
        return {
            "translated_text": translated_text,
            "detected_source_language": None,
        }