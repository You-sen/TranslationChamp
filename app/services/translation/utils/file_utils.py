import uuid
import tempfile
import aiofiles
from pathlib import Path
from fastapi import UploadFile

# Cross-platform temp directory (works on Windows, Linux, macOS, Docker)
TEMP_DIR = Path(tempfile.gettempdir()) / "tdesignai"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def temp_path(suffix: str) -> Path:
    """Generate a unique temporary file path."""
    return TEMP_DIR / f"{uuid.uuid4().hex}{suffix}"


async def save_upload(upload: UploadFile, suffix: str) -> Path:
    """Save an uploaded file to a temp path and return it."""
    path = temp_path(suffix)
    async with aiofiles.open(path, "wb") as f:
        content = await upload.read()
        await f.write(content)
    return path


def cleanup(*paths: Path) -> None:
    """Delete temp files, ignoring errors."""
    for p in paths:
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass


def build_srt(segments: list[dict]) -> str:
    """
    Build an SRT subtitle string from Whisper verbose_json segments.
    Each segment must have: start (float), end (float), text (str).
    """
    lines = []
    for i, seg in enumerate(segments, start=1):
        start = _seconds_to_srt_time(seg["start"])
        end = _seconds_to_srt_time(seg["end"])
        lines.append(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n")
    return "\n".join(lines)


def _seconds_to_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# import uuid
# import aiofiles
# from pathlib import Path
# from fastapi import UploadFile

# TEMP_DIR = Path("/tmp/tdesignai")
# TEMP_DIR.mkdir(parents=True, exist_ok=True)


# def temp_path(suffix: str) -> Path:
#     """Generate a unique temporary file path."""
#     return TEMP_DIR / f"{uuid.uuid4().hex}{suffix}"


# async def save_upload(upload: UploadFile, suffix: str) -> Path:
#     """Save an uploaded file to a temp path and return it."""
#     path = temp_path(suffix)
#     async with aiofiles.open(path, "wb") as f:
#         content = await upload.read()
#         await f.write(content)
#     return path


# def cleanup(*paths: Path) -> None:
#     """Delete temp files, ignoring errors."""
#     for p in paths:
#         try:
#             p.unlink(missing_ok=True)
#         except Exception:
#             pass


# def build_srt(segments: list[dict]) -> str:
#     """
#     Build an SRT subtitle string from Whisper verbose_json segments.
#     Each segment has: id, start, end, text.
#     """
#     lines = []
#     for i, seg in enumerate(segments, start=1):
#         start = _seconds_to_srt_time(seg["start"])
#         end = _seconds_to_srt_time(seg["end"])
#         lines.append(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n")
#     return "\n".join(lines)


# def _seconds_to_srt_time(seconds: float) -> str:
#     h = int(seconds // 3600)
#     m = int((seconds % 3600) // 60)
#     s = int(seconds % 60)
#     ms = int((seconds - int(seconds)) * 1000)
#     return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"