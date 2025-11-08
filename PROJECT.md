# Deafine - Simplified ElevenLabs Version

## What Changed

This project has been **dramatically simplified** to use only ElevenLabs API for transcription and speaker diarization.

### Before (v0.1.0)
- ❌ Complex local ML pipeline
- ❌ PyTorch, pyannote.audio, faster-whisper
- ❌ 15 dependencies, ~5GB install
- ❌ CPU/GPU options
- ❌ Multiple model sizes
- ❌ OpenAI summaries
- ❌ RAKE extractive summaries
- ❌ Complex speaker registry

### After (v0.2.0)
- ✅ Simple ElevenLabs API integration
- ✅ 8 dependencies, ~50MB install
- ✅ Fast setup (1-2 minutes)
- ✅ No local ML models
- ✅ Clean, maintainable code
- ✅ Just works™

## Architecture

```
Microphone → VAD → ElevenLabs API → Speaker-labeled Transcription
                                  → Console Display
```

**That's it.** No complex pipeline, no local models, no ML frameworks.

## Project Structure

```
deafine/
├── deafine/                 # Main package (9 files)
│   ├── __init__.py         # Version
│   ├── config.py           # Configuration
│   ├── events.py           # Data classes
│   ├── audio_capture.py    # Microphone + VAD
│   ├── elevenlabs.py       # ElevenLabs API client
│   ├── console_ui.py       # Rich terminal UI
│   ├── recorder.py         # Optional recording
│   ├── main.py             # Application loop
│   └── cli.py              # CLI interface
│
├── README.md               # Quick start guide
├── INSTALL.md              # Installation instructions
├── USAGE.md                # Usage guide
├── CHANGELOG.md            # Version history
├── requirements.txt        # 8 dependencies
├── pyproject.toml          # Package config
├── env.template            # Environment template
├── test_installation.py    # Installation test
├── quickstart.sh           # Unix quick start
├── quickstart.bat          # Windows quick start
└── LICENSE                 # MIT License

Total: 16 files (~1,500 lines of code)
```

## Dependencies

```
sounddevice     # Microphone capture
webrtcvad       # Voice activity detection
numpy           # Array operations
soundfile       # Audio file I/O
rich            # Console UI
typer           # CLI framework
python-dotenv   # Environment variables
httpx           # HTTP client for API
```

## Quick Start

```bash
# 1. Install
pip install -e .

# 2. Configure
cp env.template .env
# Edit .env and add: ELEVEN_API_KEY=your_key

# 3. Run
deafine run
```

## Usage

```bash
# Basic
deafine run

# With recording
deafine run --record
```

## Configuration

Only one required setting:

```bash
# .env
ELEVEN_API_KEY=your_elevenlabs_api_key_here
```

Optional settings:
- `DEAFINE_ELEVENLABS_CHUNK_SECS` - How often to send audio (default: 5)
- `DEAFINE_VAD_AGGRESSIVENESS` - Silence filtering (0-3, default: 2)

## Features

✅ Real-time transcription  
✅ Automatic speaker detection (S1, S2, S3...)  
✅ Live console display  
✅ Overlap detection  
✅ Optional recording  
✅ Simple setup  
✅ Small footprint  

❌ No offline mode (requires internet)  
❌ No local processing (requires API key)  
❌ No summaries (just transcription)  

## Cost

ElevenLabs charges per API usage. With default settings (5-second chunks):
- ~12 requests per minute
- Check ElevenLabs pricing for current rates
- Adjust `DEAFINE_ELEVENLABS_CHUNK_SECS` to control costs

## Why This Is Better

1. **Fast Setup** - 1-2 minutes vs 10+ minutes
2. **Small Install** - 50MB vs 5GB
3. **No GPU Needed** - API handles compute
4. **Simple Code** - Easy to understand and modify
5. **Reliable** - No local model issues
6. **Always Updated** - ElevenLabs improves their models

## When to Use This

✅ Need quick setup  
✅ Don't want to manage ML models  
✅ Have internet connection  
✅ Have ElevenLabs API key  
✅ Want simple, reliable transcription  

## When NOT to Use This

❌ Need offline operation  
❌ Want to avoid API costs  
❌ Need custom ML models  
❌ Require on-premise processing  

## Development

The code is simple and easy to modify:

- **Add features** - Edit relevant module
- **Change UI** - Edit `console_ui.py`
- **Adjust API** - Edit `elevenlabs.py`
- **Add flags** - Edit `cli.py`

## Support

- **Installation issues** → See INSTALL.md
- **Usage questions** → See USAGE.md
- **API issues** → Check ElevenLabs documentation
- **Bugs** → Check error messages (they're descriptive)

## License

MIT License - Do whatever you want with it.

---

**Version:** 0.2.0  
**Status:** Production ready  
**Complexity:** Low  
**Dependencies:** 8  
**Install time:** ~2 minutes  
**First run:** Instant  

**Built for accessibility. Simplified for everyone.**

