"""FastAPI wrapper for Deafine transcription service."""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import asyncio
import uuid
import os
import json
import numpy as np
from pathlib import Path

from .config import Config
from .elevenlabs import ElevenLabsTranscriber
from .summarization import SessionSummarizer
from .events import AudioFrame, TranscriptSegment

# Initialize FastAPI
app = FastAPI(
    title="Audio Access API",
    description="Real-time multi-speaker transcription API for deaf and hard-of-hearing users",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage for active sessions
active_sessions: Dict[str, dict] = {}
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ==================== Models ====================

class TranscriptResponse(BaseModel):
    session_id: str
    segments: List[Dict]
    summary: Optional[Dict] = None
    duration: float
    speakers_detected: int


class SessionInfo(BaseModel):
    session_id: str
    status: str
    created_at: str
    segments_count: int
    speakers: List[str]


class HealthResponse(BaseModel):
    status: str
    elevenlabs: bool
    openrouter: bool
    version: str


# ==================== Helper Functions ====================

def create_session_id() -> str:
    """Generate unique session ID."""
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


async def process_audio_file(
    file_path: Path,
    config: Config,
    chunk_duration: int = 5
) -> List[TranscriptSegment]:
    """Process uploaded audio file."""
    
    import soundfile as sf
    import numpy as np
    
    # Read audio file
    audio_data, sample_rate = sf.read(file_path)
    
    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)
    
    # Resample to 16kHz if needed
    if sample_rate != 16000:
        try:
            from scipy import signal as scipy_signal
            audio_data = scipy_signal.resample(
                audio_data, 
                int(len(audio_data) * 16000 / sample_rate)
            )
        except ImportError:
            # If scipy not available, simple decimation
            step = sample_rate // 16000
            audio_data = audio_data[::step]
        sample_rate = 16000
    
    # Convert to int16
    audio_int16 = (audio_data * 32767).astype(np.int16)
    
    # Initialize transcriber
    transcriber = ElevenLabsTranscriber(config)
    all_segments = []
    
    # Process in chunks
    chunk_samples = chunk_duration * sample_rate
    
    for i in range(0, len(audio_int16), chunk_samples):
        chunk = audio_int16[i:i + chunk_samples]
        
        if len(chunk) < sample_rate * 0.5:  # Skip chunks < 0.5s
            continue
        
        # Create audio frame
        frame = AudioFrame(
            timestamp=i / sample_rate,
            pcm_bytes=chunk.tobytes(),
            sample_rate=sample_rate
        )
        
        await transcriber.add_audio(frame)
        
        # Process buffer
        if await transcriber.should_process(frame.timestamp):
            segments = await transcriber.process_buffer()
            all_segments.extend(segments)
    
    # Process remaining buffer
    if transcriber.audio_buffer:
        segments = await transcriber.process_buffer()
        all_segments.extend(segments)
    
    await transcriber.close()
    
    return all_segments


# ==================== API Endpoints ====================

@app.get("/", response_model=Dict)
async def root():
    """Root endpoint."""
    return {
        "message": "Deafine Transcription API",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "transcribe": "POST /transcribe",
            "transcribe_async": "POST /transcribe/stream",
            "get_session": "GET /session/{session_id}",
            "get_transcript": "GET /session/{session_id}/transcript",
            "list_sessions": "GET /sessions"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    
    try:
        config = Config()
        elevenlabs_ok = bool(config.eleven_api_key)
    except:
        elevenlabs_ok = False
    
    # Check OpenRouter
    openrouter_ok = bool(os.getenv("OPENROUTER_API_KEY"))
    
    return HealthResponse(
        status="healthy" if elevenlabs_ok else "degraded",
        elevenlabs=elevenlabs_ok,
        openrouter=openrouter_ok,
        version="0.2.0"
    )


@app.post("/transcribe", response_model=TranscriptResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    eleven_api_key: Optional[str] = Form(None),
    chunk_duration: int = Form(5),
    num_speakers: int = Form(5),
    generate_summary: bool = Form(True)
):
    """
    Transcribe an audio file with speaker diarization.
    
    Args:
        file: Audio file (WAV, MP3, M4A, etc.)
        eleven_api_key: ElevenLabs API key (optional if set in env)
        chunk_duration: Seconds per chunk (default: 5)
        num_speakers: Max speakers to detect (default: 5)
        generate_summary: Generate AI summary (default: True)
    
    Returns:
        Transcription with speaker labels and optional summary
    """
    
    session_id = create_session_id()
    file_path = None
    
    try:
        # Create config
        config = Config()
        if eleven_api_key:
            config.eleven_api_key = eleven_api_key
        
        if not config.eleven_api_key:
            raise HTTPException(
                status_code=400,
                detail="ELEVEN_API_KEY required (set in .env or pass as parameter)"
            )
        
        # Save uploaded file
        file_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process audio
        segments = await process_audio_file(
            file_path,
            config,
            chunk_duration
        )
        
        # Generate summary if requested
        summary_data = None
        if generate_summary and segments:
            summarizer = SessionSummarizer(config)
            for seg in segments:
                summarizer.add_transcript(seg)
            
            summary_data = summarizer.generate_session_summary()
            stats = summarizer.get_stats()
            summary_data["stats"] = stats
        
        # Convert segments to dict
        segments_dict = [
            {
                "speaker_id": seg.speaker_id,
                "text": seg.text,
                "start_time": seg.start_time,
                "end_time": seg.end_time
            }
            for seg in segments
        ]
        
        # Calculate duration
        duration = max(seg.end_time for seg in segments) if segments else 0
        
        # Get unique speakers
        speakers = list(set(seg.speaker_id for seg in segments))
        
        # Clean up file
        if file_path and file_path.exists():
            os.remove(file_path)
        
        return TranscriptResponse(
            session_id=session_id,
            segments=segments_dict,
            summary=summary_data,
            duration=duration,
            speakers_detected=len(speakers)
        )
        
    except Exception as e:
        # Clean up on error
        if file_path and file_path.exists():
            os.remove(file_path)
        
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcribe/stream")
async def transcribe_stream(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    eleven_api_key: Optional[str] = Form(None)
):
    """
    Start streaming transcription (async processing).
    Returns immediately with session_id.
    Use /session/{session_id} to check status.
    """
    
    session_id = create_session_id()
    
    # Save file
    file_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create session
    active_sessions[session_id] = {
        "status": "processing",
        "created_at": datetime.now().isoformat(),
        "file_path": str(file_path),
        "segments": [],
        "speakers": [],
        "error": None
    }
    
    # Process in background
    background_tasks.add_task(
        process_session_async,
        session_id,
        file_path,
        eleven_api_key
    )
    
    return {
        "session_id": session_id,
        "status": "processing",
        "check_status": f"/session/{session_id}",
        "get_transcript": f"/session/{session_id}/transcript"
    }


async def process_session_async(
    session_id: str,
    file_path: Path,
    api_key: Optional[str] = None
):
    """Background task to process audio."""
    
    try:
        config = Config()
        if api_key:
            config.eleven_api_key = api_key
        
        segments = await process_audio_file(file_path, config)
        
        segments_dict = [
            {
                "speaker_id": seg.speaker_id,
                "text": seg.text,
                "start_time": seg.start_time,
                "end_time": seg.end_time
            }
            for seg in segments
        ]
        
        speakers = list(set(seg.speaker_id for seg in segments))
        
        active_sessions[session_id]["status"] = "completed"
        active_sessions[session_id]["segments"] = segments_dict
        active_sessions[session_id]["speakers"] = speakers
        
        # Clean up
        if file_path.exists():
            os.remove(file_path)
        
    except Exception as e:
        active_sessions[session_id]["status"] = "failed"
        active_sessions[session_id]["error"] = str(e)
        
        if file_path.exists():
            os.remove(file_path)


@app.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get session status and results."""
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    return SessionInfo(
        session_id=session_id,
        status=session["status"],
        created_at=session["created_at"],
        segments_count=len(session.get("segments", [])),
        speakers=session.get("speakers", [])
    )


@app.get("/session/{session_id}/transcript")
async def get_session_transcript(session_id: str):
    """Get full transcript for a session."""
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    if session["status"] == "processing":
        raise HTTPException(
            status_code=425,
            detail="Session still processing. Check back later."
        )
    
    return {
        "session_id": session_id,
        "status": session["status"],
        "segments": session.get("segments", []),
        "speakers": session.get("speakers", []),
        "error": session.get("error")
    }


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del active_sessions[session_id]
    
    return {"message": "Session deleted", "session_id": session_id}


@app.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    
    return {
        "total": len(active_sessions),
        "sessions": [
            {
                "session_id": sid,
                "status": data["status"],
                "created_at": data["created_at"],
                "segments_count": len(data.get("segments", []))
            }
            for sid, data in active_sessions.items()
        ]
    }


# ==================== WebSocket Endpoints ====================

# Store active WebSocket connections
websocket_sessions: Dict[str, Dict] = {}


@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio transcription with haptic feedback.
    
    Protocol:
    1. Client connects
    2. Server sends: {"type": "connected", "session_id": "..."}
    3. Client sends: {"type": "config", "user_name": "John"} (optional, for haptics)
    4. Client sends: binary audio chunks (PCM 16-bit, 16kHz, mono)
    5. Server sends: {"type": "transcript", "segment": {...}}
    6. Server sends: {"type": "haptic", "reason": "name_mentioned"} (if name detected)
    7. Server sends: {"type": "status", "message": "..."}
    8. On disconnect: {"type": "summary", "data": {...}}
    """
    
    await websocket.accept()
    session_id = create_session_id()
    user_name = None  # User's name for haptic feedback
    
    # Initialize session
    try:
        config = Config()
        if not config.eleven_api_key:
            await websocket.send_json({
                "type": "error",
                "message": "ELEVEN_API_KEY not configured on server"
            })
            await websocket.close()
            return
        
        transcriber = ElevenLabsTranscriber(config)
        summarizer = SessionSummarizer(config)
        
        # Store session
        websocket_sessions[session_id] = {
            "transcriber": transcriber,
            "summarizer": summarizer,
            "timestamp": 0.0,
            "connected_at": datetime.now().isoformat(),
            "user_name": None  # For haptic feedback
        }
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "WebSocket connected. Send PCM audio data (16-bit, 16kHz, mono)"
        })
        
        print(f"🔌 WebSocket connected: {session_id}")
        
        # Main message loop
        try:
            while True:
                # Receive audio data (binary)
                data = await websocket.receive()
                
                if "bytes" in data:
                    # Binary audio data received
                    audio_bytes = data["bytes"]
                    
                    # Convert to numpy array (assuming 16-bit PCM)
                    audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
                    
                    # Create audio frame
                    frame = AudioFrame(
                        timestamp=websocket_sessions[session_id]["timestamp"],
                        pcm_bytes=audio_bytes,
                        sample_rate=16000
                    )
                    
                    # Update timestamp (samples / sample_rate)
                    websocket_sessions[session_id]["timestamp"] += len(audio_array) / 16000.0
                    
                    # Add to transcriber buffer
                    await transcriber.add_audio(frame)
                    
                    # Check if we should process
                    if await transcriber.should_process(frame.timestamp):
                        # Send processing status
                        await websocket.send_json({
                            "type": "status",
                            "message": "Processing audio...",
                            "timestamp": frame.timestamp
                        })
                        
                        # Process buffer
                        segments = await transcriber.process_buffer()
                        
                        # Send each segment back to client
                        for segment in segments:
                            # Add to summarizer
                            summarizer.add_transcript(segment)
                            
                            # Check for name mention (haptic trigger)
                            name_mentioned = False
                            user_name = websocket_sessions[session_id].get("user_name")
                            if user_name and user_name.lower() in segment.text.lower():
                                name_mentioned = True
                            
                            # Send transcript segment
                            await websocket.send_json({
                                "type": "transcript",
                                "segment": {
                                    "speaker_id": segment.speaker_id,
                                    "text": segment.text,
                                    "start_time": segment.start_time,
                                    "end_time": segment.end_time,
                                    "haptic": name_mentioned  # Trigger haptic if name mentioned
                                }
                            })
                            
                            # Send separate haptic event for stronger feedback
                            if name_mentioned:
                                await websocket.send_json({
                                    "type": "haptic",
                                    "reason": "name_mentioned",
                                    "text": segment.text,
                                    "speaker_id": segment.speaker_id,
                                    "user_name": user_name
                                })
                                print(f"📳 [{session_id}] HAPTIC: {user_name} mentioned by {segment.speaker_id}")
                            
                            print(f"📝 [{session_id}] {segment.speaker_id}: {segment.text}")
                
                elif "text" in data:
                    # Text message (commands)
                    message = json.loads(data["text"])
                    
                    if message.get("command") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": websocket_sessions[session_id]["timestamp"]
                        })
                    
                    elif message.get("command") == "set_name":
                        # Set user name for haptic feedback
                        user_name = message.get("user_name", "").strip()
                        websocket_sessions[session_id]["user_name"] = user_name
                        await websocket.send_json({
                            "type": "config_confirmed",
                            "user_name": user_name,
                            "message": f"Haptic feedback enabled for name: {user_name}"
                        })
                        print(f"👤 [{session_id}] User name set: {user_name}")
                    
                    elif message.get("command") == "get_summary":
                        # Generate and send summary
                        summary = summarizer.generate_session_summary()
                        stats = summarizer.get_stats()
                        
                        await websocket.send_json({
                            "type": "summary",
                            "data": {
                                "summary": summary,
                                "stats": stats
                            }
                        })
        
        except WebSocketDisconnect:
            print(f"🔌 WebSocket disconnected: {session_id}")
            
            # Generate final summary
            if summarizer.transcripts:
                summary = summarizer.generate_session_summary()
                stats = summarizer.get_stats()
                
                try:
                    await websocket.send_json({
                        "type": "summary",
                        "data": {
                            "summary": summary,
                            "stats": stats
                        }
                    })
                except:
                    pass  # Connection already closed
            
            # Cleanup
            await transcriber.close()
            if session_id in websocket_sessions:
                del websocket_sessions[session_id]
    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
        
        # Cleanup
        if session_id in websocket_sessions:
            try:
                await websocket_sessions[session_id]["transcriber"].close()
            except:
                pass
            del websocket_sessions[session_id]


@app.get("/ws/sessions")
async def list_websocket_sessions():
    """List active WebSocket sessions."""
    return {
        "total": len(websocket_sessions),
        "sessions": [
            {
                "session_id": sid,
                "connected_at": data["connected_at"],
                "duration": data["timestamp"]
            }
            for sid, data in websocket_sessions.items()
        ]
    }


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

