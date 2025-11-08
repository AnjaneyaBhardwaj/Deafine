"""Event types for Deafine pipeline."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AudioFrame:
    """Audio frame from capture."""
    timestamp: float
    pcm_bytes: bytes
    sample_rate: int


@dataclass
class TranscriptSegment:
    """Transcription segment from ElevenLabs."""
    speaker_id: str  # e.g., "speaker_0", "speaker_1"
    text: str
    start_time: float
    end_time: float
    words: List[dict] = None


@dataclass
class OverlapEvent:
    """Overlap detection event."""
    active_speakers: List[str]
    start_time: float
    end_time: float
