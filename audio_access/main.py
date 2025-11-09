"""Main application loop."""

import asyncio
import time
from typing import Optional, Dict
import signal

from .config import Config
from .audio_capture import AudioCapture
from .elevenlabs import ElevenLabsTranscriber
from .recorder import Recorder
from .console_ui import ConsoleUI
from .summarization import SessionSummarizer
from .events import *


class DeafineApp:
    """Main Deafine application."""
    
    def __init__(
        self,
        config: Config,
        enable_recording: bool = False
    ):
        self.config = config
        self.enable_recording = enable_recording
        
        # Components
        self.audio_capture = AudioCapture(config)
        self.transcriber = ElevenLabsTranscriber(config)
        self.summarizer = SessionSummarizer(config)
        self.ui = ConsoleUI()
        
        # Optional components
        self.recorder: Optional[Recorder] = None
        
        # State
        self.running = False
        self.active_speakers: Dict[str, float] = {}  # speaker_id -> last_active_time
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n\nShutting down gracefully...")
        self.running = False
    
    async def setup(self):
        """Setup all components."""
        
        # Initialize recorder if enabled
        if self.enable_recording:
            self.recorder = Recorder(self.config)
            self.ui.print_info("Recording enabled")
        
        self.ui.print_info("Using ElevenLabs for transcription and diarization")
    
    def _check_overlap(self, current_time: float) -> bool:
        """Check if multiple speakers are active."""
        # Remove old speakers (not active in last 2 seconds)
        active = {
            spk: t for spk, t in self.active_speakers.items()
            if current_time - t < 2.0
        }
        return len(active) > 1
    
    async def run(self):
        """Main application loop."""
        
        await self.setup()
        
        # Start audio capture
        self.audio_capture.start()
        self.ui.start()
        self.running = True
        
        try:
            # Main processing loop
            for frame in self.audio_capture.frames():
                if not self.running:
                    break
                
                # Record audio if enabled
                if self.recorder:
                    self.recorder.write_audio(frame)
                
                # Add to transcriber buffer
                await self.transcriber.add_audio(frame)
                
                # Process transcription periodically
                if await self.transcriber.should_process(frame.timestamp):
                    segments = await self.transcriber.process_buffer()
                    
                    for segment in segments:
                        # Update UI
                        self.ui.add_speaker(segment.speaker_id)
                        self.ui.update_caption(segment.speaker_id, segment.text)
                        
                        # Track active speakers
                        self.active_speakers[segment.speaker_id] = frame.timestamp
                        
                        # Add to summarizer
                        self.summarizer.add_transcript(segment)
                        
                        # Record segment
                        if self.recorder:
                            self.recorder.log_transcript(segment)
                
                # Check for overlap
                if self._check_overlap(frame.timestamp):
                    active_list = list(self.active_speakers.keys())
                    self.ui.set_overlap(True, active_list)
                else:
                    self.ui.set_overlap(False)
                
                # Update UI
                self.ui.update()
                
                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.01)
        
        except Exception as e:
            self.ui.print_error(f"Error in main loop: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown all components."""
        
        self.ui.stop()
        self.audio_capture.stop()
        
        # Generate session summary before closing
        print("\n" + "="*70)
        print("📊 SESSION SUMMARY")
        print("="*70)
        
        summaries = self.summarizer.generate_session_summary()
        stats = self.summarizer.get_stats()
        
        # Print overall summary
        if "overall" in summaries:
            print("\n📝 Overall Conversation:")
            print(f"   {summaries['overall']}")
        
        # Print per-speaker summaries
        print("\n👥 Speaker Summaries:")
        for speaker_id in sorted(summaries.keys()):
            if speaker_id == "overall":
                continue
            
            print(f"\n   {speaker_id}:")
            print(f"      {summaries[speaker_id]}")
            
            if speaker_id in stats["speakers"]:
                speaker_stats = stats["speakers"][speaker_id]
                print(f"      ({speaker_stats['words']} words, "
                      f"{speaker_stats['duration_seconds']}s speaking time)")
        
        # Print statistics
        print(f"\n📈 Statistics:")
        print(f"   Total Speakers: {stats['total_speakers']}")
        print(f"   Total Segments: {stats['total_segments']}")
        
        print("\n" + "="*70)
        
        # Save summary to file if recording
        if self.recorder:
            self._save_summary_to_file(summaries, stats)
        
        # Close other components
        if self.recorder:
            self.recorder.close()
        
        await self.transcriber.close()
        
        print("\n✅ Deafine shutdown complete.")
    
    def _save_summary_to_file(self, summaries: Dict, stats: Dict):
        """Save summary to markdown file."""
        try:
            summary_file = self.recorder.output_dir / f"{self.recorder.session_id}_summary.md"
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"# Session Summary: {self.recorder.session_id}\n\n")
                
                # Overall summary
                f.write("## Overall Conversation\n\n")
                f.write(f"{summaries.get('overall', 'No summary available.')}\n\n")
                
                # Speaker summaries
                f.write("## Speaker Summaries\n\n")
                for speaker_id in sorted(summaries.keys()):
                    if speaker_id == "overall":
                        continue
                    
                    f.write(f"### {speaker_id}\n\n")
                    f.write(f"{summaries[speaker_id]}\n\n")
                    
                    if speaker_id in stats["speakers"]:
                        speaker_stats = stats["speakers"][speaker_id]
                        f.write(f"- **Words spoken:** {speaker_stats['words']}\n")
                        f.write(f"- **Speaking time:** {speaker_stats['duration_seconds']}s\n")
                        f.write(f"- **Segments:** {speaker_stats['segments']}\n\n")
                
                # Statistics
                f.write("## Session Statistics\n\n")
                f.write(f"- **Total Speakers:** {stats['total_speakers']}\n")
                f.write(f"- **Total Segments:** {stats['total_segments']}\n")
            
            print(f"💾 Summary saved: {summary_file}")
            
        except Exception as e:
            print(f"⚠️  Could not save summary: {e}")


async def run_app(record: bool = False):
    """Run the Deafine application."""
    
    # Create config
    config = Config()
    
    # Create and run app
    app = DeafineApp(
        config=config,
        enable_recording=record
    )
    
    await app.run()
