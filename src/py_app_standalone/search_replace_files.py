import glob
import os
from pathlib import Path

from prettyfmt import fmt_path
from strif import atomic_output_file

from py_app_standalone.cli_utils import info


def search_replace_in_files(
    glob_patterns: list[str],
    search_bytes: bytes,
    replace_bytes: bytes | None,
    backup_suffix: str | None = None,
) -> tuple[int, list[Path]]:
    """
    Search or replace occurrences of `search_bytes` with `replace_bytes` in all files
    matching the glob pattern.
    """
    files_with_replacements: list[Path] = []
    total_replacements = 0

    for glob_pattern in glob_patterns:
        for file_path in glob.glob(glob_pattern, recursive=True):
            file_path = Path(file_path)
            if file_path.is_file():
                replacements = search_replace_in_file(
                    file_path, search_bytes, replace_bytes, backup_suffix
                )
                if replacements > 0:
                    op = "Replaced" if replace_bytes else "Found"
                    info(f"{op} {replacements} occurrences in: {fmt_path(file_path)}")
                    total_replacements += replacements
                    files_with_replacements.append(file_path)
    return total_replacements, files_with_replacements


def search_replace_in_file(
    path: Path,
    search_bytes: bytes,
    replace_bytes: bytes | None,
    backup_suffix: str | None = None,
) -> int:
    """
    Search or replace occurrences of `search_bytes` with `replace_bytes` in a file,
    atomically and in place.
    Reads entire file into memory!
    Returns the number of matches found or replacements made.
    """
    with path.open("rb") as file:
        content = file.read()

    replacements = content.count(search_bytes)
    if replacements > 0 and replace_bytes:
        original_permissions = os.stat(path).st_mode

        content = content.replace(search_bytes, replace_bytes)
        with atomic_output_file(path, backup_suffix=backup_suffix) as file:
            with file.open("wb") as f:
                f.write(content)

        # Restore the original file permissions.
        os.chmod(path, original_permissions)

    return replacements
