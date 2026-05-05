from pydantic import BaseModel, Field
from typing import Literal, Optional


class LocalizationParams(BaseModel):
    target_language: str = Field(..., example="Spanish")
    target_locale: str = Field(..., example="Colombia")
    style: Literal["conversational", "formal", "casual"] = "conversational"


class TextTranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    localization: LocalizationParams


class TextTranslateResponse(BaseModel):
    translated_text: str
    source_language_detected: Optional[str] = None