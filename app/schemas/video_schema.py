from pydantic import BaseModel
from typing import Optional, List
 
 
class SubtitleSegment(BaseModel):
    start: float
    end: float
    text: str
 
 
class VideoTranslateResponse(BaseModel):
    """
    Returns translated text and segments for frontend overlay.
    duration_seconds and cost_breakdown are internal — used by translate.py
    for usage reporting only. They are not populated in the return statement
    so the frontend never receives them.
    """
    translated_text: str
    source_language_detected: Optional[str] = None
    segments: Optional[List[SubtitleSegment]] = None
    # Internal fields — populated by handler, stripped before returning to frontend
    duration_seconds: Optional[float] = None
    cost_breakdown: Optional[dict] = None