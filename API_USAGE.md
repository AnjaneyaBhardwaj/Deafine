# Deafine API Usage Guide

## Starting the API

### Option 1: Local Development

```bash
# Install FastAPI dependencies (if not already installed)
pip install -r requirements.txt

# Run server
uvicorn deafine.api:app --reload --host 0.0.0.0 --port 8000

# Or run directly with Python
python -m deafine.api
```

API will be available at: **http://localhost:8000**

### Option 2: Docker

```bash
# Build and run with docker-compose
docker-compose up --build

# Or build and run manually
docker build -t deafine-api .
docker run -p 8000:8000 \
  -e ELEVEN_API_KEY=your_key \
  -e OPENROUTER_API_KEY=your_key \
  deafine-api
```

### Option 3: Production Deployment

```bash
# With gunicorn for production
pip install gunicorn
gunicorn deafine.api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

---

## API Documentation

Interactive documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check API health and configuration.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "elevenlabs": true,
  "openrouter": true,
  "version": "0.2.0"
}
```

---

### 2. Transcribe Audio (Synchronous)

**POST** `/transcribe`

Upload and transcribe audio file immediately.

**Parameters:**
- `file` (required): Audio file (WAV, MP3, M4A, etc.)
- `eleven_api_key` (optional): ElevenLabs API key
- `chunk_duration` (optional): Seconds per chunk (default: 5)
- `num_speakers` (optional): Max speakers (default: 5)
- `generate_summary` (optional): Generate summary (default: true)

**Example:**

```bash
curl -X POST http://localhost:8000/transcribe \
  -F "file=@meeting.wav" \
  -F "chunk_duration=5" \
  -F "num_speakers=5" \
  -F "generate_summary=true"
```

**Response:**
```json
{
  "session_id": "20241108_143022_a1b2c3d4",
  "segments": [
    {
      "speaker_id": "S1",
      "text": "Hello everyone, welcome to the meeting.",
      "start_time": 0.0,
      "end_time": 3.5
    },
    {
      "speaker_id": "S2",
      "text": "Hi there, glad to be here.",
      "start_time": 3.6,
      "end_time": 5.8
    }
  ],
  "summary": {
    "overall": "Meeting discussion about project status and updates.",
    "S1": "Opened the meeting and discussed project progress.",
    "S2": "Provided development updates and raised concerns.",
    "stats": {
      "total_speakers": 2,
      "total_segments": 15
    }
  },
  "duration": 125.3,
  "speakers_detected": 2
}
```

---

### 3. Transcribe Audio (Asynchronous)

**POST** `/transcribe/stream`

Upload audio and process in background (for large files).

```bash
curl -X POST http://localhost:8000/transcribe/stream \
  -F "file=@long_meeting.wav"
```

**Response:**
```json
{
  "session_id": "20241108_143022_a1b2c3d4",
  "status": "processing",
  "check_status": "/session/20241108_143022_a1b2c3d4",
  "get_transcript": "/session/20241108_143022_a1b2c3d4/transcript"
}
```

---

### 4. Get Session Status

**GET** `/session/{session_id}`

Check status of async transcription.

```bash
curl http://localhost:8000/session/20241108_143022_a1b2c3d4
```

**Response:**
```json
{
  "session_id": "20241108_143022_a1b2c3d4",
  "status": "completed",
  "created_at": "2024-11-08T14:30:22",
  "segments_count": 25,
  "speakers": ["S1", "S2", "S3"]
}
```

**Status values:**
- `processing` - Still transcribing
- `completed` - Finished successfully
- `failed` - Error occurred

---

### 5. Get Transcript

**GET** `/session/{session_id}/transcript`

Get full transcript for completed session.

```bash
curl http://localhost:8000/session/20241108_143022_a1b2c3d4/transcript
```

**Response:**
```json
{
  "session_id": "20241108_143022_a1b2c3d4",
  "status": "completed",
  "segments": [...],
  "speakers": ["S1", "S2"],
  "error": null
}
```

---

### 6. List All Sessions

**GET** `/sessions`

List all active sessions.

```bash
curl http://localhost:8000/sessions
```

**Response:**
```json
{
  "total": 3,
  "sessions": [
    {
      "session_id": "20241108_143022_a1b2c3d4",
      "status": "completed",
      "created_at": "2024-11-08T14:30:22",
      "segments_count": 25
    }
  ]
}
```

---

### 7. Delete Session

**DELETE** `/session/{session_id}`

Delete a session and its data.

```bash
curl -X DELETE http://localhost:8000/session/20241108_143022_a1b2c3d4
```

**Response:**
```json
{
  "message": "Session deleted",
  "session_id": "20241108_143022_a1b2c3d4"
}
```

---

## Client Examples

### Python

```python
import requests

# Transcribe file
with open("meeting.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/transcribe",
        files={"file": f},
        data={
            "chunk_duration": 5,
            "num_speakers": 5,
            "generate_summary": True
        }
    )

result = response.json()
print(f"Session ID: {result['session_id']}")
print(f"Detected {result['speakers_detected']} speakers")

# Print transcript
for segment in result['segments']:
    print(f"{segment['speaker_id']}: {segment['text']}")

# Print summary
if result['summary']:
    print(f"\nOverall: {result['summary']['overall']}")
```

### JavaScript

```javascript
const formData = new FormData();
formData.append('file', audioFile);
formData.append('chunk_duration', '5');
formData.append('generate_summary', 'true');

const response = await fetch('http://localhost:8000/transcribe', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Transcription:', result);

// Display transcript
result.segments.forEach(seg => {
  console.log(`${seg.speaker_id}: ${seg.text}`);
});
```

### cURL with API Key

```bash
# Pass API key as form parameter
curl -X POST http://localhost:8000/transcribe \
  -F "file=@audio.wav" \
  -F "eleven_api_key=your_key_here"
```

---

## Error Handling

### Common Errors

**400 Bad Request**
```json
{
  "detail": "ELEVEN_API_KEY required (set in .env or pass as parameter)"
}
```

**404 Not Found**
```json
{
  "detail": "Session not found"
}
```

**425 Too Early**
```json
{
  "detail": "Session still processing. Check back later."
}
```

**500 Internal Server Error**
```json
{
  "detail": "Error processing audio: ..."
}
```

---

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Required
ELEVEN_API_KEY=your_elevenlabs_key

# Optional
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=mistralai/mistral-small-3.2-24b-instruct:free
```

---

## Performance Tips

### For Large Files

Use async endpoint:
```bash
# Start processing
curl -X POST http://localhost:8000/transcribe/stream -F "file=@large.wav"

# Check status periodically
curl http://localhost:8000/session/{session_id}

# Get results when done
curl http://localhost:8000/session/{session_id}/transcript
```

### For Multiple Files

Process in parallel:
```python
import asyncio
import aiohttp

async def transcribe_file(session, filepath):
    async with session.post(
        'http://localhost:8000/transcribe/stream',
        data={'file': open(filepath, 'rb')}
    ) as resp:
        return await resp.json()

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [
            transcribe_file(session, f)
            for f in ['file1.wav', 'file2.wav', 'file3.wav']
        ]
        results = await asyncio.gather(*tasks)
        return results
```

---

## Deployment

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Increase timeout for large files
        proxy_read_timeout 300s;
        client_max_body_size 100M;
    }
}
```

### systemd Service

```ini
[Unit]
Description=Deafine API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/app/deafine
Environment="PATH=/app/deafine/.venv/bin"
ExecStart=/app/deafine/.venv/bin/uvicorn deafine.api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Monitoring

### Health Checks

```bash
# Continuous health monitoring
watch -n 5 'curl -s http://localhost:8000/health | jq'
```

### Logging

```bash
# View logs (Docker)
docker-compose logs -f deafine-api

# View logs (systemd)
journalctl -u deafine-api -f
```

---

## Security

### Add API Key Authentication

Update `deafine/api.py`:

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY = os.getenv("API_KEY", "your-secret-key")
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Add to endpoints
@app.post("/transcribe")
async def transcribe_audio(
    api_key: str = Security(verify_api_key),
    ...
):
    ...
```

Usage:
```bash
curl -X POST http://localhost:8000/transcribe \
  -H "X-API-Key: your-secret-key" \
  -F "file=@audio.wav"
```

---

## Support

- **Swagger UI**: http://localhost:8000/docs (interactive testing)
- **ReDoc**: http://localhost:8000/redoc (documentation)
- **Health**: http://localhost:8000/health (status check)

---

Happy transcribing! 🎉

