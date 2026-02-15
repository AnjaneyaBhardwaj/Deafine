"""Configuration management for Deafine."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Application configuration."""

    # API Key (required)
    eleven_api_key: str = os.getenv("ELEVEN_API_KEY", "")

    # Audio chunk settings
    chunk_ms: int = int(os.getenv("DEAFINE_CHUNK_MS", "320"))
    hop_ms: int = int(os.getenv("DEAFINE_HOP_MS", "160"))

    # VAD settings (optional - only if webrtcvad is installed)
    use_vad: bool = os.getenv("DEAFINE_USE_VAD", "true").lower() == "true"
    vad_aggressiveness: int = int(os.getenv("DEAFINE_VAD_AGGRESSIVENESS", "2"))

    # ElevenLabs settings
    elevenlabs_chunk_duration: int = int(
        os.getenv("DEAFINE_ELEVENLABS_CHUNK_SECS", "5")
    )
    use_voice_isolation: bool = (
        os.getenv("DEAFINE_USE_VOICE_ISOLATION", "true").lower() == "true"
    )
    num_speakers: int = int(os.getenv("DEAFINE_NUM_SPEAKERS", "2"))

    # Audio settings
    sample_rate: int = 16000
    channels: int = 1

    # Translation settings
    target_language: str = os.getenv("DEAFINE_TARGET_LANGUAGE", "en")
    auto_translate: bool = (
        os.getenv("DEAFINE_AUTO_TRANSLATE", "false").lower() == "true"
    )
    translation_email: str = os.getenv("DEAFINE_TRANSLATION_EMAIL", "")

    def __post_init__(self):
        """Validate configuration."""
        if not self.eleven_api_key:
            raise ValueError("ELEVEN_API_KEY is required. Set it in your .env file")

        if self.vad_aggressiveness not in [0, 1, 2, 3]:
            self.vad_aggressiveness = 2  # Default to medium


def get_config(**overrides) -> Config:
    """Get configuration with optional overrides."""
    config = Config()
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config
