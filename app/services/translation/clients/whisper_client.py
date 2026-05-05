import httpx
from pathlib import Path
from app.core.config import settings


class WhisperClient:
    """Transcribes audio using OpenAI Whisper API (verbose_json)."""

    BASE_URL = "https://api.openai.com/v1/audio/transcriptions"

    async def transcribe(self, audio_path: Path, hint_language: str | None = None) -> dict:
        """
        Returns dict with:
          - text:     full transcript string
          - language: detected language code (e.g. 'en')
          - segments: list of timed segments [{ id, start, end, text }, ...]
                      useful if caller needs subtitle timing
        """
        headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(audio_path, "rb") as f:
                files = {"file": (audio_path.name, f, "audio/mpeg")}
                data = {"model": "whisper-1", "response_format": "verbose_json"}
                if hint_language:
                    data["language"] = hint_language

                response = await client.post(
                    self.BASE_URL,
                    headers=headers,
                    files=files,
                    data=data,
                )
                response.raise_for_status()
                result = response.json()

        return {
            "text": result.get("text", "").strip(),
            "language": result.get("language"),
            "segments": result.get("segments", []),
        }
# import httpx
# from pathlib import Path
# from app.core.config import settings


# class WhisperClient:
#     """Transcribes audio using OpenAI Whisper API."""

#     BASE_URL = "https://api.openai.com/v1/audio/transcriptions"

#     async def transcribe(self, audio_path: Path, hint_language: str | None = None) -> dict:
#         """
#         Returns dict with keys:
#           - text: full transcript
#           - language: detected language code (e.g. 'en')
#         """
#         headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}

#         async with httpx.AsyncClient(timeout=60.0) as client:
#             with open(audio_path, "rb") as f:
#                 files = {"file": (audio_path.name, f, "audio/mpeg")}
#                 data = {"model": "whisper-1", "response_format": "verbose_json"}
#                 if hint_language:
#                     data["language"] = hint_language

#                 response = await client.post(
#                     self.BASE_URL,
#                     headers=headers,
#                     files=files,
#                     data=data,
#                 )
#                 response.raise_for_status()
#                 result = response.json()

#         return {
#             "text": result["text"].strip(),
#             "language": result.get("language", None),
#         }