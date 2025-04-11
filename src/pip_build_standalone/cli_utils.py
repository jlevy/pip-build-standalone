import subprocess
import sys

from funlog import log_calls
from rich import print as rprint


@log_calls(level="warning", show_timing_only=True)
def run(cmd: list[str]):
    rprint()
    rprint(f"[bold green]❯ {' '.join(cmd)}[/bold green]")
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
    rprint(f"[bold green]✔️ Success: {msg}[/bold green]")
    rprint()


def fail(msg: str):
    rprint()
    rprint(f"[bold red]✗ Error: {msg}[/bold red]")
    rprint()
    sys.exit(1)
