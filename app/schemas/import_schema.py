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
    duration_seconds and cost_breakdown are internal — used by translate.py
    for usage reporting only. They are not populated in the return statement
    so the frontend never receives them.
    """
    translated_text: str
    source_language_detected: Optional[str] = None
    # Internal fields — populated by handler, stripped before returning to frontend
    duration_seconds: Optional[float] = None
    cost_breakdown: Optional[dict] = None