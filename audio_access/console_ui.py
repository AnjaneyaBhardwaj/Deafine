"""Rich console UI for live speaker board."""

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from typing import Dict
import time

from .events import TranscriptSegment


class SpeakerDisplay:
    """Display information for a single speaker."""
    
    def __init__(self, speaker_id: str):
        self.speaker_id = speaker_id
        self.current_caption = ""
        self.last_updated = time.time()
        
        # Color mapping for speakers
        colors = ["cyan", "green", "yellow", "magenta", "blue", "red"]
        idx = int(speaker_id[1:]) - 1 if speaker_id.startswith("S") else 0
        self.color = colors[idx % len(colors)]
    
    def update_caption(self, text: str):
        """Update current caption."""
        self.current_caption = text
        self.last_updated = time.time()


class ConsoleUI:
    """Live console UI using Rich."""
    
    def __init__(self):
        self.console = Console()
        self.speakers: Dict[str, SpeakerDisplay] = {}
        self.overlap_active = False
        self.overlap_speakers = []
        self.live = None
        self.start_time = time.time()
        
    def add_speaker(self, speaker_id: str):
        """Add a new speaker to display."""
        if speaker_id not in self.speakers:
            self.speakers[speaker_id] = SpeakerDisplay(speaker_id)
    
    def update_caption(self, speaker_id: str, text: str):
        """Update live caption for a speaker."""
        self.add_speaker(speaker_id)
        self.speakers[speaker_id].update_caption(text)
    
    def set_overlap(self, active: bool, speakers: list = None):
        """Set overlap indicator."""
        self.overlap_active = active
        self.overlap_speakers = speakers or []
    
    def generate_display(self) -> Panel:
        """Generate the display panel."""
        
        # Create main table
        table = Table(show_header=True, header_style="bold white", box=None)
        table.add_column("Speaker", style="bold", width=12)
        table.add_column("Live Transcript", width=100)
        
        # Sort speakers by ID
        sorted_speakers = sorted(self.speakers.items(), key=lambda x: x[0])
        
        for speaker_id, display in sorted_speakers:
            # Create styled speaker label
            speaker_label = Text(speaker_id, style=f"bold {display.color}")
            
            # Caption (truncate if too long)
            caption = display.current_caption[-300:] if display.current_caption else "[dim]waiting...[/dim]"
            
            table.add_row(speaker_label, caption)
        
        # Add overlap indicator if active
        if self.overlap_active:
            overlap_text = Text(f"[OVERLAP] {', '.join(self.overlap_speakers)}", style="bold red blink")
            table.add_row("", overlap_text)
        
        # Create panel with title
        elapsed = time.time() - self.start_time
        mins, secs = divmod(int(elapsed), 60)
        title = f"🎤 Audio Access - Live Transcription (ElevenLabs) [{mins:02d}:{secs:02d}]"
        
        panel = Panel(
            table,
            title=title,
            border_style="bright_blue",
            padding=(1, 2)
        )
        
        return panel
    
    def start(self):
        """Start live display."""
        self.live = Live(
            self.generate_display(),
            console=self.console,
            refresh_per_second=4,
            screen=False
        )
        self.live.start()
        
        # Print welcome message
        self.console.print("\n[bold green]🎤 Audio Access started with ElevenLabs![/bold green]")
        self.console.print("[dim]Listening for speakers...[/dim]\n")
    
    def update(self):
        """Update the live display."""
        if self.live:
            self.live.update(self.generate_display())
    
    def stop(self):
        """Stop live display."""
        if self.live:
            self.live.stop()
        
        self.console.print("\n[bold yellow]🛑 Audio Access stopped[/bold yellow]")
    
    def print_info(self, message: str):
        """Print info message."""
        if not self.live:
            self.console.print(f"[blue]ℹ️ {message}[/blue]")
    
    def print_error(self, message: str):
        """Print error message."""
        if not self.live:
            self.console.print(f"[red]❌ {message}[/red]")
