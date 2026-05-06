# tdesignAI — API Endpoints Documentation

**Base URL:** `http://localhost:8000/api/v1`

---

## 1. Text Translation

**Endpoint:** `POST /translate/text`

**Summary:** Translate typed text with locale awareness.

### Request

```json
{
  "text": "Hey, what are you up to tonight?",
  "localization": {
    "target_language": "Spanish",
    "target_locale": "Colombia",
    "style": "conversational"
  }
}
```

**Request fields:**
- `text` (string, required): Text to translate (min: 1 char, max: 5000 chars)
- `localization` (object, required):
  - `target_language` (string, required): Language name (e.g., "Spanish", "French", "German", "Portuguese")
  - `target_locale` (string, required): Locale/region (e.g., "Colombia", "France", "Brazil", "Portugal")
  - `style` (string, optional): Tone — `"conversational"` (default), `"formal"`, `"casual"`

### Response

```json
{
  "translated_text": "¿Oye, qué estás haciendo esta noche?",
  "source_language_detected": "en"
}
```

**Response fields:**
- `translated_text` (string): Translated text
- `source_language_detected` (string or null): Detected source language code (e.g., "en")

### Example cURL

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

---

## 2. Voice Translation

**Endpoints:**
- `POST /translate/voice` — Submit voice for translation
- `GET /translate/voice/play/{token}` — Play the synthesized audio

**Summary:** Translate voice message with speaker's voice preserved. Max 45 seconds.

### Request (POST /translate/voice)

**Multipart form data:**
- `audio` (file, required): Voice recording (MP3, WAV, OGG, WebM, M4A)
- `localization` (string, required): JSON-encoded localization params

```bash
curl -X POST http://localhost:8000/api/v1/translate/voice \
  -F 'audio=@voice_recording.mp3;type=audio/mpeg' \
  -F 'localization={"target_language":"Spanish","target_locale":"Colombia","style":"conversational"}'
```

**localization JSON format:**
```json
{
  "target_language": "Spanish",
  "target_locale": "Colombia",
  "style": "conversational"
}
```

### Response (POST /translate/voice)

```json
{
  "audio_url": "http://localhost:8000/api/v1/translate/voice/play/a1b2c3d4e5"
}
```

**Response fields:**
- `audio_url` (string): Ephemeral URL (valid for 5 minutes) to download/play the synthesized MP3

### Response (GET /translate/voice/play/{token})

Returns the raw MP3 audio file.

**Content-Type:** `audio/mpeg`

### Example Flow (Frontend)

1. User records voice (frontend creates audio blob)
2. POST to `/translate/voice` with audio file + localization
3. Backend returns `audio_url`
4. Frontend can play with `<audio src={audio_url} controls />`

---

## 3. Video Translation

**Endpoint:** `POST /translate/video`

**Summary:** Translate video and return translated text with subtitle segments. Max 90 seconds.

### Request

**Multipart form data:**
- `video` (file, required): Video file (MP4, MOV, WebM)
- `localization` (string, required): JSON-encoded localization params

```bash
curl -X POST http://localhost:8000/api/v1/translate/video \
  -F 'video=@clip.mp4' \
  -F 'localization={"target_language":"French","target_locale":"France","style":"conversational"}'
```

### Response

```json
{
  "translated_text": "Bonjour, comment ça va? C'est une belle journée.",
  "source_language_detected": "en",
  "segments": [
    {
      "start": 0.5,
      "end": 3.2,
      "text": "Bonjour, comment ça va?"
    },
    {
      "start": 3.5,
      "end": 5.8,
      "text": "C'est une belle journée."
    }
  ]
}
```

**Response fields:**
- `translated_text` (string): Full translated text
- `source_language_detected` (string or null): Detected source language code
- `segments` (array): List of subtitle segments with timings
  - `start` (float): Start time in seconds
  - `end` (float): End time in seconds
  - `text` (string): Translated text for this segment

### Use Cases

**For frontend overlay:**
- Use `segments` array to display translated text at the right moment
- Show each `text` from `start` to `end` time

**For SRT/VTT subtitle file:**
- Convert `segments` to SRT format and let user download

---

## 4. Import Media

**Endpoint:** `POST /translate/import`

**Summary:** Import audio or video and return translated text only. Max 90 seconds.

### Request

**Multipart form data:**
- `media` (file, required): Audio or video file
- `localization` (string, required): JSON-encoded localization params

```bash
curl -X POST http://localhost:8000/api/v1/translate/import \
  -F 'media=@audio.mp3' \
  -F 'localization={"target_language":"German","target_locale":"Germany","style":"formal"}'
```

### Response

```json
{
  "translated_text": "Guten Morgen, wie geht es Ihnen?",
  "source_language_detected": "en"
}
```

**Response fields:**
- `translated_text` (string): Translated text
- `source_language_detected` (string or null): Detected source language code

### Use Case

- Extract and translate text from any audio/video without any audio synthesis or segment timing
- Simple text-only import workflow

---

## 5. LocalizationParams (Common Format)

Used across all endpoints as the localization specification.

```json
{
  "target_language": "Spanish",
  "target_locale": "Colombia",
  "style": "conversational"
}
```

**Fields:**
- `target_language` (string): Human-readable language name
  - Supported: Spanish, French, German, Italian, Japanese, Korean, Arabic, Russian, Dutch, Polish, Turkish, Portuguese, English, Chinese, Hindi, Swedish, Danish, Norwegian, Finnish, Czech, Romanian, Hungarian, Slovak, Bulgarian, Greek, Ukrainian, Indonesian, Latvian, Lithuanian, Slovenian, Estonian, Bengali, Urdu, Persian, Tagalog, Malay, and many more.
  
- `target_locale` (string): Locale/region (e.g., "Colombia", "Brazil", "United Kingdom", "United States")
  - Special variants:
    - English: "United States" → EN-US, "United Kingdom" → EN-GB
    - Portuguese: "Brazil" → PT-BR, "Portugal" → PT-PT

- `style` (string): Tone preference
  - `"conversational"` (default) — Natural, spoken tone
  - `"formal"` — Professional, polite tone
  - `"casual"` — Relaxed, informal tone

---

## 6. Configuration & Features

### Speech Rate (Voice Translation)

Adjust playback speed of synthesized audio via environment variable:

```env
DEFAULT_SPEECH_RATE=0.95  # 95% of normal speed (slower)
DEFAULT_SPEECH_RATE=1.0   # Normal speed (default)
DEFAULT_SPEECH_RATE=1.1   # 110% of normal speed (faster)
```

Valid range: 0.5–2.0

### Translation Backend Configuration

Choose translation mode using `TRANSLATOR_BACKEND`:

```env
TRANSLATOR_BACKEND=openai  # GPT only (translate + localize)
TRANSLATOR_BACKEND=deepl   # DeepL only
TRANSLATOR_BACKEND=hybrid  # DeepL translate -> GPT localization polish
TRANSLATOR_BACKEND=auto    # Use feature flags below
```

If using `TRANSLATOR_BACKEND=auto`, control behavior with feature flags:

```env
# OpenAI only
OPENAI_TRANSLATION_ENABLED=true
DEEPL_TRANSLATION_ENABLED=false

# DeepL only
OPENAI_TRANSLATION_ENABLED=false
DEEPL_TRANSLATION_ENABLED=true

# Hybrid (both enabled)
OPENAI_TRANSLATION_ENABLED=true
DEEPL_TRANSLATION_ENABLED=true
```

---

## 7. Error Responses

All endpoints may return HTTP error codes:

### 422 Unprocessable Entity

```json
{
  "detail": "Audio exceeds maximum of 45s (got 60.5s)."
}
```

**Causes:**
- Audio/video exceeds duration limit
- No speech detected
- Invalid localization JSON
- Unsupported media format

### 500 Internal Server Error

```json
{
  "detail": "ElevenLabs voice cloning failed (401): Unauthorized"
}
```

**Causes:**
- API service failure (OpenAI, ElevenLabs, DeepL)
- Authentication issues with external services
- ffmpeg not available

---

## 8. Interactive API Documentation

Once the server is running, visit:

**Swagger UI:** `http://localhost:8000/docs`

**ReDoc:** `http://localhost:8000/redoc`

Both allow you to try endpoints interactively with live requests.

---

## 9. Rate Limits & Quotas

- Text translation: No hard limit (depends on DeepL/OpenAI quota)
- Voice translation: 45 seconds max per request
- Video translation: 90 seconds max per request
- Ephemeral audio URLs: Expire after 5 minutes
- ElevenLabs voice cloning: Requires paid plan with Instant Voice Cloning quota

---

## 10. Supported Audio/Video Formats

**Audio:** MP3, WAV, OGG, WebM, M4A, FLAC  
**Video:** MP4, MOV, WebM

---

## Examples by Use Case

### Use Case 1: Translate a Chat Message

```bash
curl -X POST http://localhost:8000/api/v1/translate/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "See you tomorrow!",
    "localization": {
      "target_language": "French",
      "target_locale": "France",
      "style": "casual"
    }
  }'
```

### Use Case 2: Translate a Voice Note with Speaker's Voice

```bash
curl -X POST http://localhost:8000/api/v1/translate/voice \
  -F 'audio=@voice_note.mp3;type=audio/mpeg' \
  -F 'localization={"target_language":"Spanish","target_locale":"Mexico","style":"conversational"}'
```

Then play the returned `audio_url` in frontend audio player.

### Use Case 3: Translate Video with Subtitles for Overlay

```bash
curl -X POST http://localhost:8000/api/v1/translate/video \
  -F 'video=@tutorial.mp4' \
  -F 'localization={"target_language":"Japanese","target_locale":"Japan","style":"formal"}'
```

Use the returned `segments` array to render subtitles timed with the video.

### Use Case 4: Extract & Translate Text from Audio

```bash
curl -X POST http://localhost:8000/api/v1/translate/import \
  -F 'media=@recording.wav' \
  -F 'localization={"target_language":"Portuguese","target_locale":"Portugal","style":"conversational"}'
```

Get just the translated text, no audio synthesis.

---

**Last Updated:** May 6, 2026  
**API Version:** v1
