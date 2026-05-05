from typing import Optional
from pydantic import BaseModel


class VoiceTranslateResponse(BaseModel):
    """Response for the voice translation endpoint.

    Historically we returned an inlined `audio_data_url` (data URI). Newer
    behavior returns an ephemeral `audio_url` that points to a short,
    server-hosted play endpoint. Both fields are optional to preserve
    compatibility during transition.
    """

    audio_data_url: Optional[str] = None
    audio_url: Optional[str] = None