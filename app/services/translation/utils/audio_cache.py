import asyncio
import time
from typing import Optional

_CACHE: dict = {}
_LOCK = asyncio.Lock()


async def store_audio(token: str, data: bytes, media_type: str = "audio/mpeg", ttl: int = 300) -> None:
    """Store audio bytes in-memory with a TTL (seconds). Default: 300s (5 minutes)."""
    expires_at = time.time() + ttl
    async with _LOCK:
        _CACHE[token] = {"bytes": data, "expires_at": expires_at, "media_type": media_type}


async def get_audio(token: str) -> Optional[dict]:
    """Retrieve the cached audio dict or None if missing/expired."""
    async with _LOCK:
        item = _CACHE.get(token)
        if not item:
            return None
        if item["expires_at"] < time.time():
            # expired — remove and return None
            del _CACHE[token]
            return None
        return item


async def _cleanup_loop(interval: int = 10) -> None:
    """Background task that periodically removes expired entries."""
    while True:
        now = time.time()
        async with _LOCK:
            to_delete = [k for k, v in _CACHE.items() if v["expires_at"] < now]
            for k in to_delete:
                del _CACHE[k]
        await asyncio.sleep(interval)


def start_cleanup_task() -> None:
    """Start the cleanup loop if an event loop is running (best-effort).

    Call this from FastAPI startup (it will schedule an asyncio task).
    """
    try:
        asyncio.create_task(_cleanup_loop())
    except RuntimeError:
        # No running event loop — caller should schedule when ready
        pass
