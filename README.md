# Deafine - Real-Time Multi-Speaker Transcription

**Deafine** is a simple Python accessibility tool that provides real-time speaker diarization and live transcription using ElevenLabs API for deaf and hard-of-hearing users.

## Features

- 🎤 **Real-time microphone capture** 
- 👥 **Automatic multi-speaker detection** (S1, S2, S3...) via ElevenLabs
- 📝 **Live transcription** with speaker labels (full text, not summarized)
- 🔀 **Overlap detection** when multiple speakers talk simultaneously
- 💾 **Optional recording** to save audio and transcripts
- 📊 **Session summaries** - Generated when closing (overall + per-speaker)
- ⚡ **Simple and fast** - no local ML models, no build tools required
- 💰 **Optional VAD** - Save bandwidth and API costs (if webrtcvad installed)

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -e .

# Copy environment template
cp env.template .env
# (or on Windows: copy env.template .env)
```

### Configuration

**IMPORTANT:** You need an ElevenLabs API key.

1. Get your API key from https://elevenlabs.io
2. Edit `.env` and add your key:
```bash
ELEVEN_API_KEY=your_key_here
```

### Running

Basic usage:
```bash
deafine run
```

With recording enabled:
```bash
deafine run --record
```

## How It Works

```
Microphone → [Optional VAD] → ElevenLabs API → Live Transcription with Speakers
```

1. **Audio Capture**: Records from microphone at 16kHz mono
2. **VAD (Optional)**: Filters silence to save bandwidth (if installed)
3. **ElevenLabs**: Transcribes and identifies speakers (sent every 5 seconds)
4. **Display**: Shows live output in console

## Requirements

- Python 3.9+
- ElevenLabs API key (required)
- Microphone access
- Internet connection

### Optional: Voice Activity Detection

To save ~60% bandwidth and API costs, install webrtcvad:

**Linux/Mac:**
```bash
pip install webrtcvad
```

**Windows:** Requires Microsoft C++ Build Tools
```bash
# Install from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Then:
pip install webrtcvad
```

**Docker/Cloud:** Works automatically (Linux-based)

The app works fine without VAD - it just sends all audio instead of filtering silence.

## CLI Options

```bash
deafine run [OPTIONS]

Options:
  --record    Save audio and transcript to disk
  --help      Show help message
```

## Display

```
┌─ 🎤 Deafine - Live Transcription (ElevenLabs) [00:45] ─────┐
│ Speaker  | Live Transcript                                  │
│ ──────────────────────────────────────────────────────────  │
│ S1       | Hello, how are you today?                        │
│ S2       | I'm doing great, thanks!                         │
└─────────────────────────────────────────────────────────────┘
```

## Configuration Options

Edit `.env` to configure:

```bash
# Required
ELEVEN_API_KEY=your_key_here

# Optional: Enable/disable VAD (if webrtcvad installed)
DEAFINE_USE_VAD=true
DEAFINE_VAD_AGGRESSIVENESS=2  # 0-3 (higher = more aggressive)

# How often to send audio to ElevenLabs (seconds)
DEAFINE_ELEVENLABS_CHUNK_SECS=5

# Audio processing
DEAFINE_CHUNK_MS=320
DEAFINE_HOP_MS=160
```

## Session Summaries

When you stop the app (Ctrl+C), you'll see:

```
📊 SESSION SUMMARY
======================================================================

📝 Overall Conversation:
   Discussion about testing the Deafine app and confirming it works.

👥 Speaker Summaries:

   S1:
      Initiated testing of the application and asked for confirmation.
      (45 words, 12.3s speaking time)

   S2:
      Confirmed the application is working correctly.
      (23 words, 6.1s speaking time)

📈 Statistics:
   Total Speakers: 2
   Total Segments: 8
```

### With OpenAI (Optional)

Install: `pip install openai`

Add to `.env`: `OPENAI_API_KEY=your_key`

Gets **AI-powered summaries** instead of extractive summaries.

## Recording Output

When using `--record`, three files are created:
- `session_YYYYMMDD_HHMMSS.wav` - Audio recording
- `session_YYYYMMDD_HHMMSS_transcript.jsonl` - Transcript with timestamps
- `session_YYYYMMDD_HHMMSS_summary.md` - Session summary (generated on close)

## Troubleshooting

**"ELEVEN_API_KEY is required"**
- Make sure you've created `.env` file with your ElevenLabs API key

**No audio detected**
- Check microphone is connected and not muted
- Try different microphone if available

**Slow transcription**
- Normal behavior - transcription happens every 5 seconds
- Adjust `DEAFINE_ELEVENLABS_CHUNK_SECS` in `.env` for faster updates (uses more API calls)

**Want to reduce API costs?**
- Install webrtcvad: `pip install webrtcvad`
- Saves ~60% by filtering silence

## Cost Optimization

| Mode | Bandwidth | API Costs | Installation |
|------|-----------|-----------|--------------|
| **Without VAD** | 100% | Higher | ✅ Easy (no build tools) |
| **With VAD** | ~40% | Lower | ⚠️ Needs compiler (Windows) |

## License

MIT License - Built for accessibility
