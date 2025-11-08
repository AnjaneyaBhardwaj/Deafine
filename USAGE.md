# Deafine Usage Guide

## Quick Reference

### Basic Commands

```bash
# Start transcription
deafine run

# With recording
deafine run --record

# Show version
deafine version
```

## Configuration

Edit `.env` to configure:

```bash
# REQUIRED: Your ElevenLabs API key
ELEVEN_API_KEY=your_key_here

# How often to send audio to ElevenLabs (seconds)
DEAFINE_ELEVENLABS_CHUNK_SECS=5

# Voice activity detection aggressiveness (0-3, higher = more aggressive)
DEAFINE_VAD_AGGRESSIVENESS=2

# Audio processing settings
DEAFINE_CHUNK_MS=320
DEAFINE_HOP_MS=160
```

## Understanding the Display

```
┌─ 🎤 Deafine - Live Transcription (ElevenLabs) [00:45] ─────┐
│ Speaker  | Live Transcript                                  │
│ ──────────────────────────────────────────────────────────  │
│ S1       | Hello, how are you today?                        │
│ S2       | I'm doing great, thanks!                         │
│          | [OVERLAP] S1, S2                                 │
└─────────────────────────────────────────────────────────────┘
```

**Speaker Labels:**

- `S1`, `S2`, `S3`, etc. - Automatically detected speakers
- Each speaker gets a unique color

**Live Transcript:**

- Shows the most recent speech from that speaker
- Updates every 5 seconds (or your configured interval)

**[OVERLAP]:**

- Appears when multiple people speak close together

## How It Works

1. **Audio Capture**: Your microphone is continuously recorded
2. **VAD Filtering**: Silence is removed to save bandwidth
3. **API Upload**: Every 5 seconds, audio is sent to ElevenLabs
4. **Transcription**: ElevenLabs returns text with speaker labels
5. **Display**: Results shown in real-time

## Recording

When using `--record`, two files are created:

### 1. Audio File (`session_YYYYMMDD_HHMMSS.wav`)

- Full audio recording
- 16 kHz, mono, WAV format

### 2. Transcript File (`session_YYYYMMDD_HHMMSS_transcript.jsonl`)

JSON Lines format with timestamps:

```json
{"timestamp": 1.23, "type": "transcript", "data": {"speaker_id": "S1", "text": "Hello", "start_time": 1.0, "end_time": 2.5}}
{"timestamp": 3.45, "type": "transcript", "data": {"speaker_id": "S2", "text": "Hi there", "start_time": 2.6, "end_time": 4.0}}
```

## Performance Tuning

### For Real-Time Feel (More API Calls)

```bash
# In .env
DEAFINE_ELEVENLABS_CHUNK_SECS=3
```

- Faster updates (every 3 seconds)
- More responsive
- Uses more API credits

### For Cost Savings (Fewer API Calls)

```bash
# In .env
DEAFINE_ELEVENLABS_CHUNK_SECS=10
```

- Slower updates (every 10 seconds)
- Less responsive
- Uses fewer API credits

### For Noisy Environments

```bash
# In .env
DEAFINE_VAD_AGGRESSIVENESS=3
```

- More aggressive silence filtering
- Reduces bandwidth and costs
- May cut off soft speech

## Tips & Best Practices

### Audio Setup

1. **Use a good microphone** - Better audio = better transcription
2. **Position matters** - Place mic equidistant from all speakers
3. **Reduce background noise** - Close windows, turn off fans
4. **Internet stability** - Stable connection required

### For Meetings

1. Place microphone in center of room
2. Use `--record` to save the session
3. Test with `deafine run` before the meeting starts
4. Monitor your ElevenLabs API usage

### For Interviews

1. Use `--record` for documentation
2. Use headphones to avoid feedback
3. Consider a directional microphone
4. Keep laptop/device powered (don't let it sleep)

## Troubleshooting

### No transcription appearing

- Check internet connection
- Verify `ELEVEN_API_KEY` in `.env`
- Speak louder or closer to microphone
- Wait 5 seconds (or your configured interval)

### Speakers not being separated

- ElevenLabs handles speaker separation
- Some voices may be similar
- Try speaking more distinctly
- Check ElevenLabs API documentation for limits

### High API costs

- Increase `DEAFINE_ELEVENLABS_CHUNK_SECS` to send less frequently
- Increase `DEAFINE_VAD_AGGRESSIVENESS` to filter more silence
- Use only when needed (not continuously)

### Lag/delay in captions

- Normal: 5-10 second delay (depends on your settings)
- Check internet speed
- Try shorter chunk intervals (but costs more)

## API Usage

ElevenLabs charges based on characters transcribed.

**Rough estimates:**

- Speaking rate: ~150 words/minute = ~750 characters/minute
- Sending every 5 seconds: ~60 characters per request
- One hour: ~12 _ 60 _ 60 = 45,000 characters

Check ElevenLabs pricing for current rates.

## Keyboard Shortcuts

- `Ctrl+C` - Stop Deafine gracefully

## Advanced Usage

### Multiple Sessions

Run different sessions in different directories to avoid filename conflicts.

### Post-Processing Transcripts

Read the JSONL file:

```python
import json

with open('session_20241108_120000_transcript.jsonl') as f:
    events = [json.loads(line) for line in f]

# Get all text by speaker
transcripts = {}
for event in events:
    if event['type'] == 'transcript':
        speaker = event['data']['speaker_id']
        text = event['data']['text']
        transcripts.setdefault(speaker, []).append(text)

# Print by speaker
for speaker, texts in transcripts.items():
    print(f"\n{speaker}:")
    print(' '.join(texts))
```

## Examples

### Example 1: Quick Conversation

```bash
deafine run
```

### Example 2: Important Meeting (with recording)

```bash
deafine run --record
```

### Example 3: Long Session (cost-optimized)

```bash
# Edit .env first:
# DEAFINE_ELEVENLABS_CHUNK_SECS=10
# DEAFINE_VAD_AGGRESSIVENESS=3

deafine run --record
```

## Limitations

- Requires internet connection
- Requires ElevenLabs API key (not free)
- 5-10 second latency (depends on settings)
- English works best (check ElevenLabs for language support)
- Accuracy depends on audio quality and ElevenLabs API

## Support

For issues:

1. Check INSTALL.md for setup problems
2. Verify `.env` configuration
3. Test microphone in other applications
4. Check ElevenLabs API status
5. Review error messages

Happy transcribing! 🎤
