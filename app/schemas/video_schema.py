from pydantic import BaseModel
from typing import Optional, List


class SubtitleSegment(BaseModel):
    start: float
    end: float
    text: str


class VideoTranslateResponse(BaseModel):
    """
    Returns translated text and translated segments with timestamps.
    Frontend can use `segments` to build SRT/VTT or render overlays.
    """
    translated_text: str
    source_language_detected: Optional[str] = None
    segments: Optional[List[SubtitleSegment]] = None