"""Audio capture with optional VAD."""

import sounddevice as sd
import numpy as np
import queue
import time
from typing import Generator

# Try to import webrtcvad (optional)
try:
    import webrtcvad

    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False

from .config import Config
from .events import AudioFrame


class AudioCapture:
    """Captures audio from microphone with optional VAD."""

    def __init__(self, config: Config):
        self.config = config
        self.audio_queue = queue.Queue()
        self.running = False
        self.stream = None
        self.buffer = np.array([], dtype=np.int16)

        # Frame settings
        self.chunk_size = int(config.sample_rate * config.chunk_ms / 1000)
        self.hop_size = int(config.sample_rate * config.hop_ms / 1000)

        # Initialize VAD if available and enabled
        self.vad = None
        if config.use_vad and VAD_AVAILABLE:
            self.vad = webrtcvad.Vad(config.vad_aggressiveness)
            print("✅ VAD filtering enabled (bandwidth saver mode)")
        elif config.use_vad and not VAD_AVAILABLE:
            print("⚠️  webrtcvad not installed - VAD disabled")
            print("   To enable VAD: pip install webrtcvad")
        else:
            print("ℹ️  VAD filtering disabled (sending all audio)")

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for sounddevice stream."""
        if status:
            print(f"Audio callback status: {status}")

        # Convert float32 to int16
        audio_int16 = (indata[:, 0] * 32767).astype(np.int16)
        self.audio_queue.put((time_info.currentTime, audio_int16))

    def _is_speech(self, chunk: np.ndarray) -> bool:
        """Check if chunk contains speech using VAD."""
        if not self.vad:
            return True  # No VAD available, accept all audio

        try:
            # VAD requires 10, 20, or 30ms frames
            vad_frame_size = int(self.config.sample_rate * 0.03)  # 30ms

            # Check multiple sub-frames
            for i in range(0, len(chunk), vad_frame_size):
                if i + vad_frame_size <= len(chunk):
                    vad_frame = chunk[i : i + vad_frame_size].tobytes()
                    if self.vad.is_speech(vad_frame, self.config.sample_rate):
                        return True

            return False
        except Exception:
            # On error, accept audio
            return True

    def start(self):
        """Start audio capture."""
        self.running = True
        self.stream = sd.InputStream(
            samplerate=self.config.sample_rate,
            channels=self.config.channels,
            dtype="float32",
            blocksize=self.hop_size,
            callback=self._audio_callback,
        )
        self.stream.start()

    def stop(self):
        """Stop audio capture."""
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()

    def frames(self) -> Generator[AudioFrame, None, None]:
        """Generate audio frames with optional VAD filtering."""
        start_time = time.time()

        while self.running:
            try:
                timestamp, audio_chunk = self.audio_queue.get(timeout=0.1)

                if self.vad:
                    # VAD mode: Buffer and filter
                    self.buffer = np.concatenate([self.buffer, audio_chunk])

                    # Process chunks with hop
                    while len(self.buffer) >= self.chunk_size:
                        chunk = self.buffer[: self.chunk_size]
                        self.buffer = self.buffer[self.hop_size :]

                        # Check for speech
                        if self._is_speech(chunk):
                            pcm_bytes = chunk.tobytes()
                            relative_timestamp = time.time() - start_time

                            yield AudioFrame(
                                timestamp=relative_timestamp,
                                pcm_bytes=pcm_bytes,
                                sample_rate=self.config.sample_rate,
                            )
                else:
                    # No VAD mode: Send all audio directly
                    pcm_bytes = audio_chunk.tobytes()
                    relative_timestamp = time.time() - start_time

                    yield AudioFrame(
                        timestamp=relative_timestamp,
                        pcm_bytes=pcm_bytes,
                        sample_rate=self.config.sample_rate,
                    )

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in audio capture: {e}")
                continue
