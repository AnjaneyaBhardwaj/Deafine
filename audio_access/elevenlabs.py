"""ElevenLabs STT for transcription and diarization."""

import httpx
import numpy as np
import soundfile as sf
from typing import Dict, List
from io import BytesIO
from elevenlabs.client import ElevenLabs
from .config import Config
from .events import AudioFrame, TranscriptSegment


class ElevenLabsTranscriber:
    """ElevenLabs Speech-to-Text with diarization."""

    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.eleven_api_key
        self.base_url = "https://api.elevenlabs.io"

        if not self.api_key:
            raise ValueError("ELEVEN_API_KEY not set")

        self.client = httpx.AsyncClient(timeout=60.0)
        self.elevenlabs_client = ElevenLabs(api_key=self.api_key)

        # Buffer for chunked audio
        self.audio_buffer: List[AudioFrame] = []
        self.chunk_duration = config.elevenlabs_chunk_duration
        self.last_sent_time = 0.0  # Track relative time (from frame.timestamp)

        # Speaker mapping (ElevenLabs IDs -> Simple IDs)
        self.speaker_mapping: Dict[str, str] = {}
        self.next_speaker_num = 1

    def _get_simple_speaker_id(self, elevenlabs_id: str) -> str:
        """Map ElevenLabs speaker ID to simple S1, S2, etc."""
        if elevenlabs_id not in self.speaker_mapping:
            self.speaker_mapping[elevenlabs_id] = f"S{self.next_speaker_num}"
            self.next_speaker_num += 1
        return self.speaker_mapping[elevenlabs_id]

    async def add_audio(self, frame: AudioFrame):
        """Add audio frame to buffer."""
        self.audio_buffer.append(frame)

    async def should_process(self, current_time: float) -> bool:
        """Check if it's time to process buffered audio."""
        # Use frame timestamp (relative time) for comparison
        time_since_last = current_time - self.last_sent_time
        return time_since_last >= self.chunk_duration and len(self.audio_buffer) > 0

    async def isolate_voice(self, audio_bytes: bytes) -> bytes:
        """Isolate voice from audio using ElevenLabs Voice Isolator API."""
        try:
            # Convert raw PCM bytes to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Convert to float32 in range [-1.0, 1.0] for soundfile
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # Create a WAV file in memory with proper headers
            wav_buffer = BytesIO()
            sf.write(wav_buffer, audio_float, self.config.sample_rate, format='WAV', subtype='PCM_16')
            wav_buffer.seek(0)
            
            # Use the official ElevenLabs SDK for voice isolation
            # Note: The SDK method is synchronous, but it's fast enough for our use case
            isolated_audio_stream = self.elevenlabs_client.audio_isolation.convert(
                audio=wav_buffer
            )
            
            # Read the isolated audio stream (it returns an iterator of bytes)
            isolated_bytes = b"".join(isolated_audio_stream)
            
            print("✅ Voice isolation completed")
            return isolated_bytes
            
        except Exception as e:
            print(f"⚠️  Voice isolation error: {e}, using original audio")
            return audio_bytes

    async def process_buffer(self) -> List[TranscriptSegment]:
        """Send buffered audio to ElevenLabs and get results."""

        if not self.audio_buffer:
            return []

        try:
            # Combine audio frames
            audio_data = []
            for frame in self.audio_buffer:
                audio_int16 = np.frombuffer(frame.pcm_bytes, dtype=np.int16)
                audio_data.append(audio_int16)

            combined = np.concatenate(audio_data)

            # Convert to bytes (16-bit PCM)
            audio_bytes = combined.tobytes()
            
            # Apply voice isolation if enabled (returns WAV format)
            if self.config.use_voice_isolation:
                audio_bytes = await self.isolate_voice(audio_bytes)
            else:
                # Convert raw PCM to WAV format for consistency
                audio_float = combined.astype(np.float32) / 32768.0
                wav_buffer = BytesIO()
                sf.write(wav_buffer, audio_float, self.config.sample_rate, format='WAV', subtype='PCM_16')
                audio_bytes = wav_buffer.getvalue()

            # Get timing info
            start_timestamp = self.audio_buffer[0].timestamp
            end_timestamp = self.audio_buffer[-1].timestamp

            print(
                f"Sending {len(audio_bytes)} bytes ({end_timestamp - start_timestamp:.1f}s of audio) to ElevenLabs..."
            )

            # Prepare request to Speech-to-Text endpoint
            url = f"{self.base_url}/v1/speech-to-text"
            headers = {"xi-api-key": self.api_key}

            # Create multipart form data
            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}

            data = {
                "model_id": "scribe_v1",
                "diarize": "true",  # Enable speaker diarization
                "num_speakers": self.config.num_speakers,
                "timestamps_granularity": "word",
                # No file_format parameter - let API auto-detect WAV format
            }

            # Send request
            response = await self.client.post(
                url, headers=headers, files=files, data=data
            )
            response.raise_for_status()

            result = response.json()

            # Debug: print response structure
            print(f"📥 Response keys: {list(result.keys())}")
            if "words" in result and result["words"]:
                print(f"   Found {len(result['words'])} words")
                # Check unique speakers
                speakers = set(w.get("speaker_id", "unknown") for w in result["words"])
                print(f"   Speakers in response: {speakers}")

            # Parse results according to ElevenLabs API response format
            segments = []

            # Group words by speaker
            if "words" in result and result["words"]:
                current_speaker = None
                current_words = []
                current_start = None
                current_end = None

                for word_data in result["words"]:
                    speaker_id_raw = word_data.get("speaker_id", "speaker_0")
                    word_text = word_data.get("text", "").strip()
                    word_start = word_data.get("start", 0)
                    word_end = word_data.get("end", 0)

                    # Skip empty words
                    if not word_text:
                        continue

                    # Check if speaker changed
                    if current_speaker != speaker_id_raw:
                        # Save previous speaker's segment if exists
                        if current_speaker is not None and current_words:
                            speaker_id = self._get_simple_speaker_id(current_speaker)
                            text = " ".join(current_words)

                            segments.append(
                                TranscriptSegment(
                                    speaker_id=speaker_id,
                                    text=text,
                                    start_time=start_timestamp + current_start,
                                    end_time=start_timestamp + current_end,
                                    words=[],
                                )
                            )

                        # Start new speaker segment
                        current_speaker = speaker_id_raw
                        current_words = [word_text]
                        current_start = word_start
                        current_end = word_end
                    else:
                        # Same speaker, add word
                        current_words.append(word_text)
                        current_end = word_end

                # Don't forget the last segment
                if current_speaker is not None and current_words:
                    speaker_id = self._get_simple_speaker_id(current_speaker)
                    text = " ".join(current_words)

                    segments.append(
                        TranscriptSegment(
                            speaker_id=speaker_id,
                            text=text,
                            start_time=start_timestamp + current_start,
                            end_time=start_timestamp + current_end,
                            words=[],
                        )
                    )

            elif "text" in result and result["text"]:
                # Fallback: no word-level data, just full text
                segments.append(
                    TranscriptSegment(
                        speaker_id="S1",
                        text=result["text"],
                        start_time=start_timestamp,
                        end_time=end_timestamp,
                        words=[],
                    )
                )

            # Update last sent time using frame timestamp (relative time)
            self.last_sent_time = end_timestamp

            # Clear buffer
            self.audio_buffer = []

            if segments:
                print(f"✅ Transcribed {len(segments)} segment(s)")
                for seg in segments:
                    print(f"   {seg.speaker_id}: {seg.text[:50]}...")
            else:
                print(f"⚠️  No transcription returned (possibly silence)")

            return segments

        except httpx.HTTPStatusError as e:
            print(f"❌ ElevenLabs API error: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            # Update last_sent_time even on error to avoid spam
            if self.audio_buffer:
                self.last_sent_time = self.audio_buffer[-1].timestamp
            self.audio_buffer = []
            return []
        except Exception as e:
            print(f"❌ Error in ElevenLabs transcription: {e}")
            import traceback

            traceback.print_exc()
            # Update last_sent_time even on error
            if self.audio_buffer:
                self.last_sent_time = self.audio_buffer[-1].timestamp
            self.audio_buffer = []
            return []

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
