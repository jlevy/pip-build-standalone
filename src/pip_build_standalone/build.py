import glob
import os
import shutil
import sys
from pathlib import Path

from prettyfmt import fmt_path

from pip_build_standalone.cli_utils import info, run, success, warn
from pip_build_standalone.search_replace_files import search_replace_in_files


def build_python_env(
    package_list: list[str], target_dir: Path, python_version: str, force: bool = False
):
    """
    Use uv to create a standalone Python environment with the given module installed.
    Packages can be listed as they would be to pip.
    """

    # This is the absolute path to the venv, which will be used by pip.
    target_absolute = target_dir.resolve()

    if target_dir.exists() and not force:
        raise FileExistsError(
            f"target directory already exists (run with --force to run anyway): {target_dir}"
        )

    run(
        [
            "uv",
            "python",
            "install",
            # These are the uv-managed standalone Python binaries.
            "--managed-python",
            "--install-dir",
            str(target_absolute),
            python_version,
        ]
    )

    # Find the root directory of the environment.
    install_root_pat = os.path.join(target_dir, f"cpython-{python_version}.*")
    install_root_paths = glob.glob(install_root_pat)
    if not install_root_paths:
        raise FileNotFoundError(f"Failed to find venv root at: {install_root_pat}")

    install_root = Path(install_root_paths[0])  # Use the first match

    pip_path = install_root / "bin" / "pip"
    if not pip_path.exists():
        raise FileNotFoundError(f"Failed to find pip at: {fmt_path(pip_path)}")

    run(
        [
            "uv",
            "pip",
            "install",
            *package_list,
            "--python",
            str(install_root),
            "--break-system-packages",
        ]
    )

    clean_pycache_dirs(target_absolute)

    # First handle binaries with possible absolute paths.
    if sys.platform == "darwin":
        update_macos_dylib_ids(install_root)

    # Then handle text files with absolute paths.
    replace_absolute_paths(install_root, str(target_absolute), str(target_dir))

    success(
        f"Created standalone Python environment for packages {package_list} at: {fmt_path(target_dir)}"
    )


def update_macos_dylib_ids(python_root: Path):
    """
    Update the dylib ids of all the dylibs in the given root directory.
    """
    glob_pattern = f"{python_root}/lib/**/*.dylib"
    for dylib_path in glob.glob(glob_pattern, recursive=True):
        info(f"Found macos dylib, will update its id to remove any absolute paths: {dylib_path}")
        rel_path = Path(dylib_path).relative_to(python_root)
        run(["install_name_tool", "-id", f"@executable_path/../{rel_path}", dylib_path])


def replace_absolute_paths(python_root: Path, old_path_str: str, new_path_str: str):
    """
    Replace all old (absolute) paths with the new (relative) path.
    This works fine on all text files. We skip binary libs but most do not have absolute paths.
    """
    text_glob = [f"{python_root}/bin/*", f"{python_root}/lib/**/*.py"]

    info()
    info(f"Replacing all absolute paths in: {text_glob}: `{old_path_str}` -> `{new_path_str}`")
    search_replace_in_files(text_glob, old_path_str.encode(), new_path_str.encode())

    info()
    info("Sanity checking if any absolute paths remain...")
    all_files_glob = [f"{python_root}/**/*"]
    matches = search_replace_in_files(all_files_glob, old_path_str.encode(), None)
    if matches:
        warn(f"Found {matches} matches of `{old_path_str}` in binary files (see above)")
    else:
        info("Great! No absolute paths found in the installed files.")


def clean_pycache_dirs(dir_path: Path):
    """
    Remove all __pycache__ directories within the given root directory.
    """
    for dirpath, dirnames, _filenames in os.walk(dir_path):
        if "__pycache__" in dirnames:
            pycache_path = os.path.join(dirpath, "__pycache__")
            shutil.rmtree(pycache_path)
            info(f"Removed: {fmt_path(pycache_path)}")
