import glob
import os
from pathlib import Path

from prettyfmt import fmt_path
from strif import atomic_output_file

from py_app_standalone.cli_utils import info

# Relocatable shebang for posix.
# This is what uv does, which is based on pip's distlib. See:
# https://github.com/astral-sh/uv/blob/main/crates/uv-install-wheel/src/wheel.rs#L105-L140
# https://github.com/pypa/pip/blob/0ad4c94be74cc24874c6feb5bb3c2152c398a18e/src/pip/_vendor/distlib/scripts.py#L136-L165
RELOCATABLE_PYTHON3_SHEBANG = """
#!/bin/sh
'''exec' "$(dirname -- "$(realpath -- "$0")")"/'python3' "$0" "$@"
' '''
""".lstrip()


def add_shebang(
    path: Path,
    new_shebang: str,
    backup_suffix: str | None = None,
) -> str | None:
    """
    Replace the shebang in a script file and return the old shebang if present.
    Handles both single-line and multi-line shebangs.
    """
    if not path.is_file():
        return None

    with path.open("rb") as file:
        content = file.read()

    # Split into lines with line endings preserved.
    lines = content.splitlines(True)

    # Check if there's a shebang.
    if not lines or not lines[0].startswith(b"#!"):
        return None

    # Determine if it's a multi-line shebang.
    is_multiline = len(lines) >= 3 and lines[1].startswith(b"'") and lines[2].startswith(b"'")

    # Determine how many lines to replace.
    lines_to_replace = 3 if is_multiline else 1

    # Capture the old shebang.
    old_shebang = b"".join(lines[:lines_to_replace]).decode()

    # Combine the new shebang with the rest of the file.
    new_content = new_shebang.encode()
    if lines_to_replace < len(lines):
        new_content += b"".join(lines[lines_to_replace:])

    # Store the original permissions.
    original_permissions = os.stat(path).st_mode

    # Write back using atomic file operations.
    with atomic_output_file(path, backup_suffix=backup_suffix) as file:
        with file.open("wb") as f:
            f.write(new_content)

    # Restore the original file permissions.
    os.chmod(path, original_permissions)

    return old_shebang


def replace_shebangs(
    glob_patterns: list[str],
    new_shebang: str,
    backup_suffix: str | None = None,
) -> int:
    """
    Replace shebangs in all files matching the glob patterns with the new shebang.
    Returns the total number of replacements made.
    """
    total_replacements = 0

    info()
    info("Inserting relocatable shebangs on scripts in:\n" + f"    {', '.join(glob_patterns)}")
    for glob_pattern in glob_patterns:
        for file_path in glob.glob(glob_pattern, recursive=True):
            path = Path(file_path)
            if path.is_file():
                old_shebang = add_shebang(path, new_shebang, backup_suffix)
                if old_shebang is not None:
                    info(f"Replaced shebang in: {fmt_path(file_path)}")
                    total_replacements += 1

    return total_replacements
