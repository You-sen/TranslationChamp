"""
cost_tracker.py
Pure cost calculation — no API calls, no side effects.
All prices in USD as of 2025.
"""

# ── Pricing Constants ─────────────────────────────────────────────────────────

# Whisper: $0.006 per minute = $0.0001 per second
WHISPER_COST_PER_SECOND: float = 0.0001

# GPT-4o
# Input:  $2.50 per 1M tokens = $0.0000025 per token
# Output: $10.00 per 1M tokens = $0.00001 per token
GPT4O_COST_PER_INPUT_TOKEN: float = 0.0000025
GPT4O_COST_PER_OUTPUT_TOKEN: float = 0.00001

# DeepL: $25 per 1M characters = $0.000025 per character
DEEPL_COST_PER_CHARACTER: float = 0.000025

# ElevenLabs Multilingual v2: ~$0.00022 per character (Creator plan)
# Voice cloning (instant): included in plan, no per-request cost
# Dubbing API: ~$0.003 per second of input audio
ELEVENLABS_TTS_COST_PER_CHARACTER: float = 0.00022
ELEVENLABS_DUBBING_COST_PER_SECOND: float = 0.003


# ── Cost Breakdown Model ──────────────────────────────────────────────────────

def build_cost_breakdown(
    # Whisper
    whisper_seconds: float = 0.0,
    # GPT-4o
    gpt_input_tokens: int = 0,
    gpt_output_tokens: int = 0,
    # DeepL
    deepl_characters: int = 0,
    # ElevenLabs TTS (v1 - clone + synthesize)
    elevenlabs_tts_characters: int = 0,
    # ElevenLabs Dubbing (v2)
    elevenlabs_dubbing_seconds: float = 0.0,
) -> dict:
    """
    Calculate cost breakdown from raw usage numbers.
    Returns a dict with per-service usage, per-service cost, and total.
    Unused services return 0.
    """
    whisper_cost       = round(whisper_seconds * WHISPER_COST_PER_SECOND, 6)
    gpt_cost           = round(
        (gpt_input_tokens * GPT4O_COST_PER_INPUT_TOKEN) +
        (gpt_output_tokens * GPT4O_COST_PER_OUTPUT_TOKEN), 6
    )
    deepl_cost         = round(deepl_characters * DEEPL_COST_PER_CHARACTER, 6)
    elevenlabs_tts_cost     = round(elevenlabs_tts_characters * ELEVENLABS_TTS_COST_PER_CHARACTER, 6)
    elevenlabs_dub_cost     = round(elevenlabs_dubbing_seconds * ELEVENLABS_DUBBING_COST_PER_SECOND, 6)
    elevenlabs_cost    = elevenlabs_tts_cost + elevenlabs_dub_cost

    total = round(whisper_cost + gpt_cost + deepl_cost + elevenlabs_cost, 6)

    return {
        # Whisper
        "whisper_seconds":            round(whisper_seconds, 2),
        "whisper_cost_usd":           whisper_cost,
        # GPT-4o
        "gpt_input_tokens":           gpt_input_tokens,
        "gpt_output_tokens":          gpt_output_tokens,
        "gpt_cost_usd":               gpt_cost,
        # DeepL
        "deepl_characters":           deepl_characters,
        "deepl_cost_usd":             deepl_cost,
        # ElevenLabs
        "elevenlabs_tts_characters":  elevenlabs_tts_characters,
        "elevenlabs_dubbing_seconds": round(elevenlabs_dubbing_seconds, 2),
        "elevenlabs_cost_usd":        elevenlabs_cost,
        # Total
        "total_cost_usd":             total,
    }