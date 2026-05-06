from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    # DeepL
    DEEPL_API_KEY: str = ""
    DEEPL_API_URL: str = "https://api-free.deepl.com/v2"

    # ElevenLabs
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_API_URL: str = "https://api.elevenlabs.io/v1"
    ELEVENLABS_DEFAULT_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"

    # OpenAI (Whisper + Translation)
    OPENAI_API_KEY: str = ""

    # Translation backend
    # Options:
    #   "openai"  → GPT-4o only (translate + localize in one call)
    #   "deepl"   → DeepL only (no localization layer)
    #   "hybrid"  → DeepL raw translation → GPT-4o localization polish
    #   "auto"    → reads the two flags below
    TRANSLATOR_BACKEND: str = "openai"

    # Feature flags (used when TRANSLATOR_BACKEND = "auto")
    OPENAI_TRANSLATION_ENABLED: bool = True
    DEEPL_TRANSLATION_ENABLED: bool = False

    # OpenAI model settings
    OPENAI_TRANSLATION_MODEL: str = "gpt-4o"
    OPENAI_TRANSLATION_MAX_OUTPUT_TOKENS: int = 2048

    # Duration limits
    MAX_VOICE_DURATION_SECONDS: int = 45
    MAX_VIDEO_DURATION_SECONDS: int = 90
    MAX_IMPORT_DURATION_SECONDS: int = 90

    # Speech rate for synthesized audio (1.0 = original speed)
    DEFAULT_SPEECH_RATE: float = 1.0

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# prev working ver starts here
# from pydantic_settings import BaseSettings
# from functools import lru_cache


# class Settings(BaseSettings):
#     # DeepL
#     DEEPL_API_KEY: str = ""
#     DEEPL_API_URL: str = "https://api-free.deepl.com/v2"

#     # ElevenLabs
#     ELEVENLABS_API_KEY: str = ""
#     ELEVENLABS_API_URL: str = "https://api.elevenlabs.io/v1"
#     ELEVENLABS_DEFAULT_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"

#     # OpenAI (Whisper)
#     OPENAI_API_KEY: str = ""

#     # Translation backend toggle
#     # OpenAI is the default translation backend; DeepL can be enabled later.
#     OPENAI_TRANSLATION_ENABLED: bool = True
#     DEEPL_TRANSLATION_ENABLED: bool = False
#     TRANSLATOR_BACKEND: str = "auto"
#     OPENAI_TRANSLATION_MODEL: str = "gpt-4o"
#     OPENAI_TRANSLATION_MAX_OUTPUT_TOKENS: int = 2048

#     # Limits
#     MAX_VOICE_DURATION_SECONDS: int = 45
#     MAX_VIDEO_DURATION_SECONDS: int = 90
#     MAX_IMPORT_DURATION_SECONDS: int = 90
#     # Default speech rate for synthesized audio. 1.0 = original, <1.0 slower, >1.0 faster
#     DEFAULT_SPEECH_RATE: float = 1.0

#     class Config:
#         env_file = ".env"
#         extra = "ignore"


# @lru_cache()
# def get_settings() -> Settings:
#     return Settings()


# settings = get_settings()
# prev working ver ends here