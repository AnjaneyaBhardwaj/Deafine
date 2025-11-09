"""Generate summaries at end of session or periodically."""

from typing import Dict, List, Optional
from collections import defaultdict
import os

from .config import Config
from .events import TranscriptSegment

# Try to import OpenAI (optional)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class SessionSummarizer:
    """Generates summaries of conversation transcripts."""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Store all transcripts by speaker
        self.transcripts: Dict[str, List[TranscriptSegment]] = defaultdict(list)
        
        # OpenAI client (if available)
        self.openai_client = None
        openai_key = os.getenv("OPENAI_API_KEY", "")
        
        if openai_key and OPENAI_AVAILABLE:
            try:
                self.openai_client = OpenAI(api_key=openai_key)
                print("✅ OpenAI available for summaries")
            except Exception as e:
                print(f"⚠️  Could not initialize OpenAI: {e}")
        elif not OPENAI_AVAILABLE:
            print("ℹ️  OpenAI not installed (pip install openai for AI summaries)")
        else:
            print("ℹ️  OPENAI_API_KEY not set (summaries will be extractive)")
    
    def add_transcript(self, segment: TranscriptSegment):
        """Add a transcript segment."""
        self.transcripts[segment.speaker_id].append(segment)
    
    def get_speaker_text(self, speaker_id: str) -> str:
        """Get all text for a speaker."""
        segments = self.transcripts.get(speaker_id, [])
        return " ".join(seg.text for seg in segments if seg.text)
    
    def get_all_text(self) -> str:
        """Get all text from all speakers in chronological order."""
        all_segments = []
        for segments in self.transcripts.values():
            all_segments.extend(segments)
        
        # Sort by start time
        all_segments.sort(key=lambda s: s.start_time)
        
        # Format as conversation
        lines = []
        for seg in all_segments:
            lines.append(f"{seg.speaker_id}: {seg.text}")
        
        return "\n".join(lines)
    
    def generate_session_summary(self) -> Dict[str, str]:
        """Generate summary at end of session."""
        
        if not self.transcripts:
            return {"overall": "No conversation recorded."}
        
        summaries = {}
        
        # Overall conversation summary
        full_text = self.get_all_text()
        
        if self.openai_client:
            # AI summary
            summaries["overall"] = self._generate_ai_summary(full_text, summary_type="overall")
        else:
            # Extractive summary
            summaries["overall"] = self._generate_extractive_summary(full_text)
        
        # Per-speaker summaries
        for speaker_id in sorted(self.transcripts.keys()):
            speaker_text = self.get_speaker_text(speaker_id)
            
            if len(speaker_text.split()) < 5:
                summaries[speaker_id] = "Brief contribution"
                continue
            
            if self.openai_client:
                summaries[speaker_id] = self._generate_ai_summary(
                    speaker_text, 
                    summary_type="speaker",
                    speaker_id=speaker_id
                )
            else:
                summaries[speaker_id] = self._generate_extractive_summary(speaker_text, max_words=50)
        
        return summaries
    
    def _generate_ai_summary(
        self, 
        text: str, 
        summary_type: str = "overall",
        speaker_id: Optional[str] = None
    ) -> str:
        """Generate AI summary using OpenAI."""
        
        try:
            if summary_type == "overall":
                system_prompt = (
                    "Summarize this conversation in 2-3 sentences. "
                    "Focus on key topics discussed and main points. "
                    "Be concise but informative."
                )
            else:  # speaker
                system_prompt = (
                    f"Summarize what {speaker_id} said in 1-2 sentences. "
                    "Focus on their main points and contributions."
                )
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️  Error generating AI summary: {e}")
            return self._generate_extractive_summary(text)
    
    def _generate_extractive_summary(self, text: str, max_words: int = 100) -> str:
        """Generate simple extractive summary."""
        
        words = text.split()
        
        if len(words) <= max_words:
            return text
        
        # Take first and last portions
        first_half = words[:max_words // 2]
        last_half = words[-(max_words // 2):]
        
        return " ".join(first_half) + " [...] " + " ".join(last_half)
    
    def get_stats(self) -> Dict[str, any]:
        """Get session statistics."""
        
        stats = {
            "total_speakers": len(self.transcripts),
            "total_segments": sum(len(segs) for segs in self.transcripts.values()),
            "speakers": {}
        }
        
        for speaker_id, segments in self.transcripts.items():
            word_count = sum(len(seg.text.split()) for seg in segments)
            duration = sum(seg.end_time - seg.start_time for seg in segments)
            
            stats["speakers"][speaker_id] = {
                "segments": len(segments),
                "words": word_count,
                "duration_seconds": round(duration, 1)
            }
        
        return stats

