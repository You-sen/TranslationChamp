

# import httpx
# from pathlib import Path
# from app.core.config import settings


# class WhisperClient:
#     """Transcribes audio using OpenAI Whisper API (verbose_json)."""

#     BASE_URL = "https://api.openai.com/v1/audio/transcriptions"

#     async def transcribe(self, audio_path: Path, hint_language: str | None = None) -> dict:
#         """
#         Returns dict with:
#           - text:     full transcript string
#           - language: detected language code (e.g. 'en')
#           - segments: list of timed segments [{ id, start, end, text }, ...]
#                       useful if caller needs subtitle timing
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

#         # duration is in the verbose_json response — used for Whisper cost calculation
#         duration_seconds = result.get("duration", 0.0)

#         return {
#             "text": result.get("text", "").strip(),
#             "language": result.get("language"),
#             "segments": result.get("segments", []),
#             "duration_seconds": float(duration_seconds),
#         }
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

import httpx
from pathlib import Path
from app.core.config import settings



def _mime_type_for_path(audio_path: Path) -> str:
    """Return the correct MIME type based on file extension."""
    mapping = {
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".mp4": "audio/mp4",
        ".ogg": "audio/ogg",
        ".wav": "audio/wav",
        ".webm": "audio/webm",
    }
    return mapping.get(audio_path.suffix.lower(), "audio/mpeg")


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
                files = {"file": (audio_path.name, f, _mime_type_for_path(audio_path))}
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

        # duration is in the verbose_json response — used for Whisper cost calculation
        duration_seconds = result.get("duration", 0.0)

        return {
            "text": result.get("text", "").strip(),
            "language": result.get("language"),
            "segments": result.get("segments", []),
            "duration_seconds": float(duration_seconds),
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
#                 files = {"file": (audio_path.name, f, _mime_type_for_path(audio_path))}
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