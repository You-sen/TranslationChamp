import httpx
from pathlib import Path
from fastapi import HTTPException
from app.core.config import settings


class ElevenLabsClient:
    """ElevenLabs client — voice cloning + speech synthesis."""

    BASE_URL = settings.ELEVENLABS_API_URL

    # ── Voice Cloning ─────────────────────────────────────────────────────────

    async def clone_voice(
        self,
        audio_path: Path,
        name: str = "temp_clone",
        content_type: str | None = None,
    ) -> str:
        """
        Upload original audio to create a temporary cloned voice.
        Returns the cloned voice_id.
        """
        url = f"{self.BASE_URL}/voices/add"
        headers = {"xi-api-key": settings.ELEVENLABS_API_KEY}
        mime_type = content_type or _mime_type_for_path(audio_path)

        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(audio_path, "rb") as f:
                files = {"files": (audio_path.name, f, mime_type)}
                data = {
                    "name": name,
                    "description": "Temporary clone for translation",
                }
                response = await client.post(url, headers=headers, files=files, data=data)

                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"ElevenLabs voice cloning failed ({response.status_code}): {response.text}",
                    ) from exc

        return response.json()["voice_id"]

    async def delete_voice(self, voice_id: str) -> None:
        """Delete a cloned voice after use to keep the account clean."""
        url = f"{self.BASE_URL}/voices/{voice_id}"
        headers = {"xi-api-key": settings.ELEVENLABS_API_KEY}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(url, headers=headers)
            response.raise_for_status()

    # ── Synthesis ─────────────────────────────────────────────────────────────

    async def synthesize(self, text: str, voice_id: str) -> bytes:
        """
        Synthesize speech from translated text using the given voice_id.
        Uses eleven_multilingual_v2 to support all target languages.
        Returns raw MP3 bytes.
        """
        url = f"{self.BASE_URL}/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": settings.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"ElevenLabs speech synthesis failed ({response.status_code}): {response.text}",
                ) from exc

        return response.content


def _mime_type_for_path(audio_path: Path) -> str:
    mapping = {
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".mp4": "audio/mp4",
        ".ogg": "audio/ogg",
        ".wav": "audio/wav",
        ".webm": "audio/webm",
    }
    return mapping.get(audio_path.suffix.lower(), "audio/mpeg")


# import httpx
# from pathlib import Path
# from app.core.config import settings

# # Default voice — Rachel (multilingual). Override via env if needed.
# DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"


# class ElevenLabsClient:
#     """Synthesizes speech from translated text using ElevenLabs."""

#     async def synthesize(
#         self,
#         text: str,
#         voice_id: str = DEFAULT_VOICE_ID,
#         language_code: str | None = None,
#     ) -> bytes:
#         """
#         Returns raw MP3 audio bytes.
#         Uses the multilingual v2 model which supports 29 languages.
#         """
#         url = f"{settings.ELEVENLABS_API_URL}/text-to-speech/{voice_id}"
#         headers = {
#             "xi-api-key": settings.ELEVENLABS_API_KEY,
#             "Content-Type": "application/json",
#             "Accept": "audio/mpeg",
#         }

#         payload = {
#             "text": text,
#             "model_id": "eleven_multilingual_v2",
#             "voice_settings": {
#                 "stability": 0.5,
#                 "similarity_boost": 0.75,
#                 "style": 0.0,
#                 "use_speaker_boost": True,
#             },
#         }

#         async with httpx.AsyncClient(timeout=60.0) as client:
#             response = await client.post(url, headers=headers, json=payload)
#             response.raise_for_status()
#             return response.content