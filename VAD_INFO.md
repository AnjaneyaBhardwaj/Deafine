# Voice Activity Detection (VAD) - Optional Feature

## What is VAD?

**Voice Activity Detection** filters out silence and background noise from audio before sending it to the API. This can save you significant bandwidth and API costs.

## Status: Optional

The app works **perfectly fine without VAD**. It's just a cost-saving optimization.

---

## How It Works

### Without VAD (Default for Windows without build tools)

```
Microphone → All Audio → ElevenLabs API
```

- ✅ Simple, no extra setup
- ✅ Works on all platforms
- ❌ Sends silence/noise to API
- ❌ Higher bandwidth usage
- ❌ Higher API costs

### With VAD (If webrtcvad installed)

```
Microphone → VAD Filter → Only Speech → ElevenLabs API
          ↓
      Silence Dropped
```

- ✅ ~60% bandwidth savings
- ✅ ~60% cost savings
- ✅ Faster processing (less data)
- ⚠️ Requires installation
- ⚠️ May cut off very soft speech

---

## Installation

### Easy Platforms (Linux, Mac, Docker)

```bash
pip install webrtcvad
```

Done! VAD will automatically activate.

### Windows (Requires C++ Build Tools)

**Option 1: Skip it** - The app works fine without it!

**Option 2: Install build tools**

1. Download Microsoft C++ Build Tools:  
   https://visualstudio.microsoft.com/visual-cpp-build-tools/

2. Install the "Desktop development with C++" workload

3. Then install webrtcvad:
   ```bash
   pip install webrtcvad
   ```

---

## Configuration

Edit `.env` to control VAD:

```bash
# Enable/disable VAD (only matters if webrtcvad is installed)
DEAFINE_USE_VAD=true

# VAD aggressiveness (0-3)
# 0 = Keep more audio (safer, costs more)
# 3 = Drop more silence (aggressive, saves more)
DEAFINE_VAD_AGGRESSIVENESS=2
```

---

## Cost Comparison

### Example: 1 hour meeting

**Without VAD:**
- Total audio: 60 minutes
- API processing: ~57.6 MB
- Estimated cost: $X (check ElevenLabs pricing)

**With VAD (aggressiveness=2):**
- Actual speech: ~25 minutes
- API processing: ~24 MB
- Estimated cost: ~40% of above
- **Savings: ~60%**

---

## When to Use VAD

### ✅ Use VAD if:

- Running long sessions (1+ hours)
- Processing many recordings
- API costs are a concern
- You're on Linux/Mac/Docker
- You have C++ Build Tools (Windows)
- Lots of silence/pauses in audio

### ❌ Skip VAD if:

- Short sessions (< 30 minutes)
- API costs not a concern
- Windows without build tools
- Want simplest setup
- Speakers have very soft voices
- Need to capture every sound

---

## How the App Detects VAD

The app automatically checks if webrtcvad is installed:

1. **If installed and `DEAFINE_USE_VAD=true`:**
   ```
   ✅ VAD filtering enabled (bandwidth saver mode)
   ```

2. **If installed but `DEAFINE_USE_VAD=false`:**
   ```
   ℹ️  VAD filtering disabled (sending all audio)
   ```

3. **If not installed:**
   ```
   ⚠️  webrtcvad not installed - VAD disabled
      To enable VAD: pip install webrtcvad
   ```

You'll see the status message when starting the app!

---

## Troubleshooting

### "webrtcvad not installed - VAD disabled"

**This is fine!** The app works perfectly without it. If you want VAD:

**Linux/Mac:**
```bash
pip install webrtcvad
```

**Windows:**
Install C++ Build Tools first, then:
```bash
pip install webrtcvad
```

### "VAD is cutting off speech"

VAD might be too aggressive. In `.env`:
```bash
DEAFINE_VAD_AGGRESSIVENESS=0  # Least aggressive
```

Or disable VAD entirely:
```bash
DEAFINE_USE_VAD=false
```

### "I want VAD but installation fails"

On Windows, you need Microsoft C++ Build Tools. If you don't want to install them:

1. Use without VAD (works great!)
2. Or use Docker/WSL2 (Linux-based, VAD installs easily)

---

## Testing VAD

After installing webrtcvad, run:

```bash
python test_installation.py
```

You'll see:
```
Testing Optional Modules:
✅ webrtcvad (optional - installed)
```

Then run the app:
```bash
deafine run
```

Look for:
```
✅ VAD filtering enabled (bandwidth saver mode)
```

---

## Summary

| Aspect | Without VAD | With VAD |
|--------|-------------|----------|
| **Works?** | ✅ Yes | ✅ Yes |
| **Installation** | ✅ Easy | ⚠️ Needs tools (Windows) |
| **Bandwidth** | 100% | ~40% |
| **Costs** | Higher | Lower (~60% savings) |
| **Accuracy** | All audio captured | May miss soft speech |
| **Best for** | Simple setup | Cost optimization |

**Bottom line:** Skip VAD for simplicity. Add it later if costs become a concern.

---

## Quick Commands

```bash
# Check if VAD is installed
python -c "import webrtcvad; print('✅ Installed')" 2>/dev/null || echo "❌ Not installed"

# Install VAD (if possible)
pip install webrtcvad

# Disable VAD (even if installed)
echo "DEAFINE_USE_VAD=false" >> .env

# Enable VAD (if installed)
echo "DEAFINE_USE_VAD=true" >> .env
```

---

For more info, see INSTALL.md

