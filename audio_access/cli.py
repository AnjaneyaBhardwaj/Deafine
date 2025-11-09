"""CLI interface using Typer."""

import typer
import asyncio

from .main import run_app


app = typer.Typer(
    name="audio-access",
    help="Real-time audio transcription for deaf and hard-of-hearing users",
    add_completion=False
)


@app.command()
def run(
    record: bool = typer.Option(
        False,
        "--record",
        help="Save audio and transcript to disk"
    )
):
    """
    Run Audio Access real-time transcription with ElevenLabs.
    
    Examples:
    
        # Basic usage:
        audio-access run
        
        # With recording:
        audio-access run --record
    
    Requirements:
        - ELEVEN_API_KEY must be set in .env file
    """
    
    typer.echo("🎤 Starting Audio Access with ElevenLabs...")
    typer.echo(f"   Recording: {'enabled' if record else 'disabled'}")
    typer.echo()
    
    # Run the async app
    try:
        asyncio.run(run_app(record=record))
    except KeyboardInterrupt:
        typer.echo("\n\n👋 Goodbye!")
    except Exception as e:
        typer.echo(f"\n❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    from . import __version__
    typer.echo(f"Audio Access v{__version__}")


if __name__ == "__main__":
    app()
