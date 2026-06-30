"""CLI entry point for AI Embedded Company.

Usage:
    aiteam serve          Start the FastAPI server
    aiteam mcp            Start the MCP server
    aiteam install        Run the installer
    aiteam info           Show system info
"""

from __future__ import annotations

import typer

app = typer.Typer(
    name="aiteam",
    help="AI Embedded Systems Company CLI",
    no_args_is_help=True,
)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="API server host"),
    port: int = typer.Option(8765, help="API server port"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
):
    """Start the FastAPI REST server."""
    import uvicorn

    typer.echo(f"Starting AI Embedded Company API on http://{host}:{port}")
    uvicorn.run(
        "ai_embedded_company.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@app.command()
def mcp():
    """Start the MCP server (stdio mode for Claude Code)."""
    from ai_embedded_company.mcp.server import main

    main()


@app.command()
def install():
    """Run the one-click installer."""
    import subprocess
    import sys
    from pathlib import Path

    install_script = Path(__file__).parent.parent.parent.parent / "install.py"
    if not install_script.exists():
        typer.echo("install.py not found. Run this command from the project root.", err=True)
        raise typer.Exit(1)

    result = subprocess.run([sys.executable, str(install_script)])
    raise typer.Exit(result.returncode)


@app.command()
def info():
    """Show system information."""
    from ai_embedded_company.__init__ import __version__

    typer.echo(f"AI Embedded Company v{__version__}")
    typer.echo("Multi-agent embedded systems + full-stack development OS")
    typer.echo("")
    typer.echo("Supported hardware: M5Stack Core S3, ESP32, STM32, RP2040, nRF52")
    typer.echo("Pipeline types: embedded-firmware, embedded-linux, web-fullstack, quick-prototype, research-spike")
    typer.echo("Agent templates: 18")
    typer.echo("")
    typer.echo("Commands:")
    typer.echo("  aiteam serve    Start the REST API server")
    typer.echo("  aiteam mcp      Start the MCP server")
    typer.echo("  aiteam install  Run the installer")


if __name__ == "__main__":
    app()
