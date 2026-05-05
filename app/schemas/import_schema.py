from pydantic import BaseModel
from typing import Optional


class ImportRequest(BaseModel):
    """
    Used for audio/video import translation feature.
    Input: uploaded file (audio or video)
    Output: translated text only
    """

    target_language: str

    # Optional metadata (useful later if you expand features)
    source_language: Optional[str] = None

    # You can extend later if needed:
    # model_type: Optional[str] = "whisper"


class ImportMediaResponse(BaseModel):
    """
    Returns translated text from imported audio/video.
    No video/audio output — text only.
    """
    translated_text: str
    source_language_detected: Optional[str] = None