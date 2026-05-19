"""
usage_reporter.py
Fire-and-forget usage reporting to the external WanderX backend.
Never raises — logs failure and moves on so the main request is never blocked.
"""
import json
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Source type mapping ───────────────────────────────────────────────────────
# Maps internal endpoint names to the backend's source enum values.
# Import uses content_type to determine AUDIO_FILE or VIDEO_FILE dynamically.

SOURCE_MAP = {
    "text":  "TEXT",
    "voice": "AUDIO_FILE",
    "video": "VIDEO_FILE",
}

VIDEO_CONTENT_TYPES = {
    "video/mp4", "video/quicktime", "video/webm",
    "video/x-msvideo", "video/mpeg",
}


def _resolve_source(endpoint: str, content_type: Optional[str] = None) -> str:
    """Resolve the source enum value for the external backend."""
    if endpoint == "import":
        if content_type and content_type in VIDEO_CONTENT_TYPES:
            return "VIDEO_FILE"
        return "AUDIO_FILE"
    return SOURCE_MAP.get(endpoint, "TEXT")


def _build_model_cost(endpoint: str, cost_breakdown: dict) -> list:
    """
    Build the modelCost array based on which services were used.
    Only includes models that were actually used (cost > 0).
    Each model has its own relevant fields alongside model + cost.
    """
    model_cost = []

    # Whisper — used for voice, video, import
    whisper_cost = cost_breakdown.get("whisper_cost_usd", 0)
    if whisper_cost > 0:
        model_cost.append({
            "model": "whisper",
            "cost": round(whisper_cost, 6),
            "seconds": cost_breakdown.get("whisper_seconds", 0),
        })

    # DeepL — used in hybrid mode
    deepl_cost = cost_breakdown.get("deepl_cost_usd", 0)
    if deepl_cost > 0:
        model_cost.append({
            "model": "deepl",
            "cost": round(deepl_cost, 6),
            "characters": cost_breakdown.get("deepl_characters", 0),
        })

    # GPT-4o — used for translation and/or localization
    gpt_cost = cost_breakdown.get("gpt_cost_usd", 0)
    if gpt_cost > 0:
        model_cost.append({
            "model": "gpt-4o",
            "cost": round(gpt_cost, 6),
            "inputTokens": cost_breakdown.get("gpt_input_tokens", 0),
            "outputTokens": cost_breakdown.get("gpt_output_tokens", 0),
        })

    # ElevenLabs — used for voice synthesis
    elevenlabs_cost = cost_breakdown.get("elevenlabs_cost_usd", 0)
    if elevenlabs_cost > 0:
        model_cost.append({
            "model": "elevenlabs",
            "cost": round(elevenlabs_cost, 6),
            "characters": cost_breakdown.get("elevenlabs_tts_characters", 0),
        })

    return model_cost


async def report_usage(
    user_token: str,
    endpoint: str,
    duration_seconds: float,
    cost_breakdown: dict,
    from_language_code: Optional[str] = None,
    to_language_code: Optional[str] = None,
    content_type: Optional[str] = None,
) -> None:
    """
    POST usage data to the WanderX backend.
    Called after every successful translation request.
    Fire-and-forget — failure never affects the API response.
    """
    source = _resolve_source(endpoint, content_type)
    model_cost = _build_model_cost(endpoint, cost_breakdown)

    payload = {
        "source": source,
        "fromLanguageCode": (from_language_code or "").upper() or None,
        "toLanguageCode": (to_language_code or "").upper() or None,
        "duration": str(int(duration_seconds)),
        "modelCost": model_cost,
    }

    # ── Dev mode: print to terminal instead of posting ────────────────────────
    if not settings.USAGE_REPORTING_ENABLED:
        logger.warning(
            "\n========== USAGE REPORT ==========\n"
            "Endpoint : %s\n"
            "Source   : %s\n"
            "From     : %s → To: %s\n"
            "Duration : %ss\n"
            "Total    : $%.6f\n"
            "Payload  : %s\n"
            "===================================",
            endpoint,
            source,
            (from_language_code or "?").upper(),
            (to_language_code or "?").upper(),
            int(duration_seconds),
            cost_breakdown.get("total_cost_usd", 0),
            json.dumps(payload, indent=2),
        )
        return

    if not settings.USAGE_REPORTING_URL:
        logger.warning("USAGE_REPORTING_URL is not set — skipping usage report.")
        return

    # ── Live mode: POST to WanderX backend ───────────────────────────────────
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                settings.USAGE_REPORTING_URL,
                json=payload,
                headers=headers,
            )
            if response.status_code not in (200, 201, 204):
                logger.warning(
                    "Usage report returned unexpected status %s for endpoint '%s'",
                    response.status_code,
                    endpoint,
                )
    except Exception as e:
        logger.warning(
            "Failed to report usage for endpoint '%s': %s",
            endpoint,
            str(e),
        )