# Deafine Installation Guide

## Prerequisites

- Python 3.9 or higher
- Microphone access
- ElevenLabs API key
- Internet connection

## Step-by-Step Installation

### 1. Navigate to Project

```bash
cd deafine
```

### 2. Create Virtual Environment

**Linux/Mac:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 3. Upgrade pip

```bash
pip install --upgrade pip
```

### 4. Install Dependencies

```bash
pip install -e .
```

This will install:

- sounddevice (audio capture)
- numpy (array operations)
- soundfile (audio file I/O)
- rich (console UI)
- typer (CLI)
- httpx (HTTP client for ElevenLabs API)
- python-dotenv (environment variables)

**Note:** Installation takes ~1-2 minutes. No C++ compilers needed! No large ML models!

### 5. (Optional) Install VAD for Cost Savings

**What is VAD?** Voice Activity Detection filters out silence, saving ~60% in bandwidth and API costs.

**Linux/Mac:**

```bash
pip install webrtcvad
```

**Windows:**

```bash
# Requires Microsoft C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Then:
pip install webrtcvad
```

**Skip this if you don't want to install build tools - the app works fine without it!**

### 6. Get ElevenLabs API Key

1. Visit https://elevenlabs.io
2. Sign up or log in
3. Go to your profile settings
4. Copy your API key

### 7. Configure Environment

Copy the environment template:

**Linux/Mac:**

```bash
cp env.template .env
```

**Windows:**

```cmd
copy env.template .env
```

Edit `.env` and add your ElevenLabs API key:

```bash
ELEVEN_API_KEY=your_elevenlabs_api_key_here
```

If you didn't install webrtcvad, also set:

```bash
DEAFINE_USE_VAD=false
```

### 8. Test Installation

```bash
python test_installation.py
```

This will verify:

- ✅ Python version
- ✅ All dependencies installed
- ✅ CLI command works
- ✅ Audio devices detected
- ✅ API key configured
- ℹ️ VAD status (installed or not)

## First Run

Start Deafine:

```bash
deafine run
```

**What to expect:**

1. You'll see if VAD is enabled or disabled
2. The app will start and show "Listening for speakers..."
3. Speak near your microphone
4. Every 5 seconds, audio is sent to ElevenLabs for transcription
5. Speakers will be labeled S1, S2, etc.
6. Live captions will appear

**To stop:** Press `Ctrl+C`

## Troubleshooting

### "ELEVEN_API_KEY is required"

Make sure:

1. You created the `.env` file
2. You added your API key to it
3. The key is valid

### webrtcvad installation fails (Windows)

**Don't worry!** The app works fine without it. Just:

1. Set `DEAFINE_USE_VAD=false` in `.env`
2. Or ignore the error - the app will auto-detect and skip VAD

If you really want VAD:

- Install Microsoft C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Then: `pip install webrtcvad`

### Audio Device Issues

**Linux:** Install PortAudio:

```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

**Mac:** Install via Homebrew:

```bash
brew install portaudio
```

**Windows:** Should work out of the box. If not:

```bash
pip install sounddevice --force-reinstall
```

### "No module named 'deafine'"

Make sure you:

1. Installed with `pip install -e .`
2. Are in the virtual environment (you should see `(.venv)` in prompt)

### Installation Fails

If you get build errors:

1. Make sure you have Python 3.9+
2. Try: `pip install --upgrade setuptools wheel`
3. Then: `pip install -e .`

## VAD Comparison

| Feature          | With VAD                    | Without VAD   |
| ---------------- | --------------------------- | ------------- |
| **Installation** | ⚠️ Needs compiler (Windows) | ✅ Easy       |
| **Bandwidth**    | ~40% of total               | 100%          |
| **API Costs**    | Lower (~60% savings)        | Higher        |
| **Accuracy**     | May cut soft speech         | No audio loss |
| **Works on**     | Linux, Mac, Docker          | All platforms |

## Verification Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -e .`)
- [ ] ElevenLabs API key obtained
- [ ] `.env` file created with API key
- [ ] Microphone connected and working
- [ ] `deafine --help` works
- [ ] `python test_installation.py` passes
- [ ] Internet connection available
- [ ] (Optional) webrtcvad installed

## Usage

```bash
# Basic usage
deafine run

# With recording
deafine run --record
```

## Uninstallation

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf .venv  # Linux/Mac
rmdir /s .venv  # Windows
```

## Support

If you have issues:

1. Check that your microphone works in other apps
2. Verify your ElevenLabs API key is correct
3. Check internet connection
4. Run `python test_installation.py`
5. If webrtcvad fails, set `DEAFINE_USE_VAD=false` in `.env`
6. Check error messages (they're descriptive)

## Cost

ElevenLabs charges based on API usage. Check their pricing at https://elevenlabs.io/pricing

**Without VAD:** Sends all audio (including silence)  
**With VAD:** Sends only speech (~60% less)

Adjust send frequency in `.env`:

```bash
DEAFINE_ELEVENLABS_CHUNK_SECS=10  # Send every 10 seconds instead of 5
```
