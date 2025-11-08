# Changelog

## [0.2.0] - 2024-11-08

### Changed - Major Simplification

- **Removed all local ML models** - No more PyTorch, pyannote, or faster-whisper
- **ElevenLabs only** - Uses ElevenLabs API for both transcription and diarization
- **Simplified dependencies** - From 15 to 8 core packages
- **Faster installation** - No large model downloads (5GB → 50MB)
- **Cleaner codebase** - Removed complex speaker registry and ASR streams
- **No summaries** - Focus on live transcription only

### Added

- Simpler speaker ID mapping (ElevenLabs speakers → S1, S2, etc.)
- Streamlined configuration (only ElevenLabs key required)

### Removed

- Local ASR (faster-whisper)
- Local diarization (pyannote.audio)
- OpenAI summaries
- RAKE extractive summaries
- Complex speaker registry
- Model selection (--model flag)
- Device selection (--device flag)
- Unnecessary documentation files

### Requirements

- **ELEVEN_API_KEY required** - Must have ElevenLabs API key
- **Internet required** - No offline mode
- Much smaller install size
- No GPU needed

## [0.1.0] - 2024-11-08

### Initial Release (Deprecated)

- Complex local ML pipeline with multiple models
- Optional ElevenLabs integration
- Large dependency footprint
- Local processing capability

---

**Current Version:** 0.2.0  
**Focus:** Simple, cloud-based transcription using ElevenLabs
