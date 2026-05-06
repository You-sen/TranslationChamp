# tdesignAI — Translation API

Localized translation for text, voice messages, video subtitles, and imported media.

---

## Required environment variables

Copy `.env.example` to `.env` and fill in all three keys before running.

| Variable | Where to get it |
|---|---|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `DEEPL_API_KEY` | https://www.deepl.com/pro-api |
| `ELEVENLABS_API_KEY` | https://elevenlabs.io/app/settings/api-keys |

Translation backend modes:

- `TRANSLATOR_BACKEND=openai` -> GPT handles translation + localization in one call
- `TRANSLATOR_BACKEND=deepl` -> DeepL-only translation
- `TRANSLATOR_BACKEND=hybrid` -> DeepL translation + GPT localization polish
- `TRANSLATOR_BACKEND=auto` -> uses `OPENAI_TRANSLATION_ENABLED` and `DEEPL_TRANSLATION_ENABLED`

```env
OPENAI_API_KEY=sk-...
DEEPL_API_KEY=...
ELEVENLABS_API_KEY=...
TRANSLATOR_BACKEND=hybrid
OPENAI_TRANSLATION_ENABLED=true
DEEPL_TRANSLATION_ENABLED=true
```

> **ElevenLabs plan note:** voice cloning via `/voices/add` requires a paid plan
> that supports Instant Voice Cloning. Verify your quota at
> https://elevenlabs.io/app/subscription before using the `/translate/voice` endpoint.

---

## Run with Docker (recommended)

```bash
cp .env.example .env   # fill in your keys
docker-compose up --build
```

API available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

---

## Run locally (requires Python 3.12+ and ffmpeg in PATH)

**Windows:** download ffmpeg from https://ffmpeg.org/download.html and add to PATH.  
**macOS:** `brew install ffmpeg`  
**Linux:** `sudo apt install ffmpeg`

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn main:app --reload
```

---

## curl examples

### 1. Text translation
```bash
curl -X POST http://localhost:8000/api/v1/translate/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hey, what are you up to tonight?",
    "localization": {
      "target_language": "Spanish",
      "target_locale": "Colombia",
      "style": "conversational"
    }
  }'
```

### 2. Voice translation (returns ephemeral audio URL)
```bash
curl -X POST http://localhost:8000/api/v1/translate/voice \
  -F "audio=@/path/to/voice.mp3" \
  -F 'localization={"target_language":"Spanish","target_locale":"Colombia","style":"conversational"}'
```

Then request the returned `audio_url` (valid for 5 minutes):

```bash
curl "http://localhost:8000/api/v1/translate/voice/play/<token>" --output translated_voice.mp3
```

### 3. Video translation (returns translated text)
```bash
curl -X POST http://localhost:8000/api/v1/translate/video \
  -F "video=@/path/to/clip.mp4" \
  -F 'localization={"target_language":"French","target_locale":"France","style":"conversational"}'
```

### 4. Import media (audio or video → translated text)
```bash
curl -X POST http://localhost:8000/api/v1/translate/import \
  -F "media=@/path/to/audio.mp3" \
  -F 'localization={"target_language":"German","target_locale":"Germany","style":"conversational"}'
```

### Health check
```bash
curl http://localhost:8000/health
```

---

## Duration limits

| Endpoint | Max duration |
|---|---|
| `/translate/voice` | 45 seconds |
| `/translate/video` | 90 seconds |
| `/translate/import` | 90 seconds |

Ephemeral voice playback URL TTL: 5 minutes.