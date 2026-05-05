import asyncio
import shutil
from pathlib import Path
from fastapi import HTTPException


def _check_ffmpeg() -> None:
    """Raise a clear error if ffmpeg/ffprobe are not available in PATH."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg not found in PATH. "
            "Install it (https://ffmpeg.org/download.html) or run inside Docker."
        )
    if not shutil.which("ffprobe"):
        raise RuntimeError(
            "ffprobe not found in PATH. "
            "It ships with ffmpeg — ensure the full ffmpeg package is installed."
        )


async def extract_audio(video_path: Path, output_path: Path) -> Path:
    """Extract audio track from a video file as MP3."""
    _check_ffmpeg()
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "2",
        str(output_path),
    ]
    await _run(cmd, context="audio extraction")
    return output_path


async def get_duration(media_path: Path) -> float:
    """Return media duration in seconds using ffprobe."""
    _check_ffmpeg()
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(media_path),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise HTTPException(
            status_code=422,
            detail=f"Could not read media duration: {stderr.decode().strip()}",
        )

    raw = stdout.decode().strip()
    if not raw:
        raise HTTPException(status_code=422, detail="Media file appears to have no duration.")

    try:
        return float(raw)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Unexpected ffprobe output: {raw!r}")


async def _run(cmd: list[str], context: str = "ffmpeg") -> None:
    """Run an ffmpeg command and raise a clear HTTPException on failure."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"ffmpeg failed during {context}: {stderr.decode().strip()}",
        )


async def change_tempo(input_path: Path, output_path: Path, rate: float) -> Path:
    """Change playback speed (tempo) without altering pitch using ffmpeg's atempo.

    `rate` is the speed multiplier: <1.0 slows, >1.0 speeds up. atempo supports 0.5-2.0,
    so for rates outside that range we clamp into allowable ranges by chaining filters.
    """
    _check_ffmpeg()
    if rate <= 0:
        raise ValueError("rate must be positive")

    # Build atempo filter chain that stays within 0.5-2.0 per element
    remaining = rate
    factors: list[str] = []
    while remaining < 0.5:
        factors.append("0.5")
        remaining = remaining / 0.5
    while remaining > 2.0:
        factors.append("2.0")
        remaining = remaining / 2.0
    factors.append(f"{remaining:.6f}")

    atempo_filter = ",".join(f"atempo={f}" for f in factors)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-af",
        atempo_filter,
        "-acodec",
        "libmp3lame",
        "-q:a",
        "2",
        str(output_path),
    ]

    await _run(cmd, context=f"change tempo to {rate}")
    return output_path

# import asyncio
# from pathlib import Path


# async def extract_audio(video_path: Path, output_path: Path) -> Path:
#     """Extract audio track from a video file as MP3."""
#     cmd = [
#         "ffmpeg", "-y",
#         "-i", str(video_path),
#         "-vn",
#         "-acodec", "libmp3lame",
#         "-q:a", "2",
#         str(output_path),
#     ]
#     await _run(cmd)
#     return output_path


# async def get_duration(media_path: Path) -> float:
#     """Return duration in seconds using ffprobe."""
#     cmd = [
#         "ffprobe",
#         "-v", "error",
#         "-show_entries", "format=duration",
#         "-of", "default=noprint_wrappers=1:nokey=1",
#         str(media_path),
#     ]
#     proc = await asyncio.create_subprocess_exec(
#         *cmd,
#         stdout=asyncio.subprocess.PIPE,
#         stderr=asyncio.subprocess.PIPE,
#     )
#     stdout, _ = await proc.communicate()
#     return float(stdout.decode().strip())


# async def _run(cmd: list[str]) -> None:
#     proc = await asyncio.create_subprocess_exec(
#         *cmd,
#         stdout=asyncio.subprocess.PIPE,
#         stderr=asyncio.subprocess.PIPE,
#     )
#     _, stderr = await proc.communicate()
#     if proc.returncode != 0:
#         raise RuntimeError(f"ffmpeg error: {stderr.decode()}")

# import asyncio
# import subprocess
# from pathlib import Path


# async def extract_audio(video_path: Path, output_path: Path) -> Path:
#     """Extract audio track from a video file as MP3."""
#     cmd = [
#         "ffmpeg", "-y",
#         "-i", str(video_path),
#         "-vn",                    # no video
#         "-acodec", "libmp3lame",
#         "-q:a", "2",
#         str(output_path),
#     ]
#     await _run(cmd)
#     return output_path


# async def get_duration(media_path: Path) -> float:
#     """Return duration in seconds using ffprobe."""
#     cmd = [
#         "ffprobe",
#         "-v", "error",
#         "-show_entries", "format=duration",
#         "-of", "default=noprint_wrappers=1:nokey=1",
#         str(media_path),
#     ]
#     proc = await asyncio.create_subprocess_exec(
#         *cmd,
#         stdout=asyncio.subprocess.PIPE,
#         stderr=asyncio.subprocess.PIPE,
#     )
#     stdout, _ = await proc.communicate()
#     return float(stdout.decode().strip())


# async def burn_subtitles(
#     video_path: Path,
#     srt_path: Path,
#     output_path: Path,
# ) -> Path:
#     """Burn SRT subtitles into video (hard-coded subtitles)."""
#     cmd = [
#         "ffmpeg", "-y",
#         "-i", str(video_path),
#         "-vf", f"subtitles={srt_path}:force_style='FontSize=20,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2'",
#         "-c:a", "copy",
#         str(output_path),
#     ]
#     await _run(cmd)
#     return output_path


# async def _run(cmd: list[str]) -> None:
#     proc = await asyncio.create_subprocess_exec(
#         *cmd,
#         stdout=asyncio.subprocess.PIPE,
#         stderr=asyncio.subprocess.PIPE,
#     )
#     _, stderr = await proc.communicate()
#     if proc.returncode != 0:
#         raise RuntimeError(f"ffmpeg error: {stderr.decode()}")