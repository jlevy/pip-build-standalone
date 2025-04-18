"""
py-app-standalone builds a standalone, relocatable Python installation with the
given pips installed.

More info: https://github.com/jlevy/py-app-standalone
"""

import argparse
import shutil
import subprocess
from importlib.metadata import version
from pathlib import Path
from typing import Any

from rich import get_console
from rich_argparse.contrib import ParagraphRichHelpFormatter

from py_app_standalone.build import build_python_env
from py_app_standalone.cli_utils import fail

APP_NAME = "py-app-standalone"

DEFAULT_PYTHON_VERSION = "3.13"

DEFAULT_TARGET_DIR = "py-standalone"


def get_app_version() -> str:
    try:
        return "v" + version(APP_NAME)
    except Exception:
        return "unknown"


def main() -> int:
    """
    Main entry point for the CLI.
    """
    parser = build_parser()
    args = parser.parse_args()

    if not shutil.which("uv"):
        fail("Could not find uv. Follow instructions to install at: https://docs.astral.sh/uv/")

    try:
        build_python_env(
            args.packages,
            args.target,
            args.python_version,
            source_only=args.source_only,
            force=args.force,
        )
    except (FileNotFoundError, FileExistsError, subprocess.CalledProcessError) as e:
        fail(f"{e}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    class CustomFormatter(ParagraphRichHelpFormatter):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            width = max(40, min(88, get_console().width))
            super().__init__(*args, width=width, **kwargs)

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=CustomFormatter,
    )

    parser.add_argument("--version", action="version", version=f"{APP_NAME} {get_app_version()}")

    parser.add_argument(
        "packages",
        type=str,
        nargs="+",
        help="Packages to install in the virtual environment, in the same format as to pip.",
    )

    parser.add_argument(
        "--source-only",
        action="store_true",
        help="Only install source .py files, ensure no .pyc files are included. Without this flag, "
        "all sources are also compiled.",
    )

    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET_DIR,
        help="Target directory for the virtual environment, in the format used "
        f"by uv. Default: {DEFAULT_TARGET_DIR}",
    )

    parser.add_argument(
        "--python-version",
        type=str,
        default=DEFAULT_PYTHON_VERSION,
        help=f"Python version to use for the virtual environment. Default: {DEFAULT_PYTHON_VERSION}",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite of existing target directory.",
    )

    return parser


if __name__ == "__main__":
    main()
