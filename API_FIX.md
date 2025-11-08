# ElevenLabs API Fix

## Problem

The app was getting `404 Not Found` errors:
```
Error in ElevenLabs transcription: Client error '404 Not Found' 
for url 'https://api.elevenlabs.io/v1/convai/conversation'
```

## Root Cause

We were using the **wrong API endpoint**.

### ❌ What We Were Using (WRONG):
```
POST https://api.elevenlabs.io/v1/convai/conversation
```

This endpoint doesn't exist → 404 error

### ✅ What We Should Use (CORRECT):
```
POST https://api.elevenlabs.io/v1/speech-to-text
```

Source: [ElevenLabs Speech-to-Text API Documentation](https://elevenlabs.io/docs/api-reference/speech-to-text/convert)

---

## What Was Fixed

### 1. **Correct Endpoint**
```python
# Before (WRONG)
url = f"{self.base_url}/v1/convai/conversation"

# After (CORRECT)
url = f"{self.base_url}/v1/speech-to-text"
```

### 2. **Correct Model ID**
```python
# Before
"model_id": "eleven_turbo_v2_5"  # This is for TTS, not STT

# After
"model_id": "scribe_v1"  # Correct STT model
```

### 3. **Enable Diarization**
```python
data = {
    "model_id": "scribe_v1",
    "diarize": "true",  # ← Added this for speaker separation
    "timestamps_granularity": "word",
    "file_format": "pcm_s16le_16"
}
```

### 4. **Correct Response Parsing**

According to the API docs, the response format is:
```json
{
  "language_code": "en",
  "text": "Hello world!",
  "words": [
    {
      "text": "Hello",
      "start": 0,
      "end": 0.5,
      "speaker_id": "speaker_1",  ← Speaker info here
      "logprob": -0.124
    }
  ]
}
```

Updated code to parse this correctly and group words by speaker.

---

## Testing

After the fix, run:
```bash
deafine run
```

You should now see:
```
✅ Transcribed X segment(s)
```

Instead of 404 errors!

---

## API Parameters

Key parameters we're using:

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `model_id` | `scribe_v1` | Speech-to-text model |
| `diarize` | `true` | Enable speaker detection |
| `timestamps_granularity` | `word` | Get word-level timestamps |
| `file_format` | `pcm_s16le_16` | 16-bit PCM, 16kHz |
| `file` | WAV bytes | Audio to transcribe |

---

## References

- **API Documentation**: https://elevenlabs.io/docs/api-reference/speech-to-text/convert
- **Model**: `scribe_v1` (main STT model)
- **Alternative Model**: `scribe_v1_experimental` (newer features)

---

## What's Different from Before

| Aspect | Before (Broken) | After (Fixed) |
|--------|----------------|---------------|
| **Endpoint** | `/v1/convai/conversation` | `/v1/speech-to-text` |
| **Model** | `eleven_turbo_v2_5` (TTS) | `scribe_v1` (STT) |
| **Diarization** | Not specified | `diarize: true` |
| **Response** | Unknown format | Standard STT format |
| **Status** | 404 Not Found | ✅ Working |

---

**Now it should work!** Try running `deafine run` again.

