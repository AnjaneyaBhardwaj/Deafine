"""Recording functionality for audio and transcripts."""

import soundfile as sf
import json
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

from .config import Config
from .events import *


class Recorder:
    """Records audio and transcripts to disk."""
    
    def __init__(self, config: Config, output_dir: str = "."):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Generate session filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_id = f"session_{timestamp}"
        
        # Audio file
        self.audio_file = self.output_dir / f"{self.session_id}.wav"
        self.audio_writer = sf.SoundFile(
            self.audio_file,
            mode='w',
            samplerate=config.sample_rate,
            channels=config.channels,
            format='WAV',
            subtype='PCM_16'
        )
        
        # Transcript file
        self.transcript_file = self.output_dir / f"{self.session_id}_transcript.jsonl"
        self.transcript_handle = open(self.transcript_file, 'w', encoding='utf-8')
        
        print(f"Recording to: {self.audio_file}")
        print(f"Transcript log: {self.transcript_file}")
    
    def write_audio(self, frame: AudioFrame):
        """Write audio frame to WAV file."""
        import numpy as np
        audio_int16 = np.frombuffer(frame.pcm_bytes, dtype=np.int16)
        self.audio_writer.write(audio_int16)
    
    def write_event(self, event_type: str, data: Dict[str, Any], timestamp: float):
        """Write event to JSONL file."""
        event = {
            "timestamp": timestamp,
            "type": event_type,
            "data": data
        }
        self.transcript_handle.write(json.dumps(event) + '\n')
        self.transcript_handle.flush()
    
    def log_transcript(self, segment: TranscriptSegment):
        """Log transcript segment."""
        self.write_event("transcript", {
            "speaker_id": segment.speaker_id,
            "text": segment.text,
            "start_time": segment.start_time,
            "end_time": segment.end_time
        }, segment.start_time)
    
    def close(self):
        """Close all file handles."""
        if hasattr(self, 'audio_writer'):
            self.audio_writer.close()
        if hasattr(self, 'transcript_handle'):
            self.transcript_handle.close()
        
        print(f"\nRecording saved:")
        print(f"  Audio: {self.audio_file}")
        print(f"  Transcript: {self.transcript_file}")
