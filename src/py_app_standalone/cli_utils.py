import subprocess
import sys

from funlog import log_calls
from rich import get_console, reconfigure
from rich import print as rprint

reconfigure(emoji=not get_console().options.legacy_windows)  # No emojis on legacy windows.


@log_calls(level="warning", show_timing_only=True)
def run(cmd: list[str]):
    rprint()
    rprint(f"[bold green]:arrow_forward: {' '.join(cmd)}[/bold green]")
    subprocess.run(cmd, text=True, check=True)
    rprint()


def info(msg: str = ""):
    rprint(f"[blue]{msg}[/blue]")


def warn(msg: str):
    rprint()
    rprint(f"[bold yellow]Warning: {msg}[/bold yellow]")
    rprint()


def success(msg: str):
    rprint()
    rprint(f"[bold green]:heavy_check_mark: Success: {msg}[/bold green]")
    rprint()


def fail(msg: str):
    rprint()
    rprint(f"[bold red]:x: Error: {msg}[/bold red]")
    rprint()
    sys.exit(1)
