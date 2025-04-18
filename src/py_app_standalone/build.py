import compileall
import glob
import os
import shutil
import sys
from pathlib import Path

from prettyfmt import fmt_path

from py_app_standalone.cli_utils import fail, info, run, success
from py_app_standalone.search_replace_files import search_replace_in_files
from py_app_standalone.shebangs import RELOCATABLE_PYTHON3_SHEBANG, replace_shebangs


def build_python_env(
    package_list: list[str],
    target_dir: Path,
    python_version: str,
    source_only: bool = False,
    force: bool = False,
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

    # XXX There is currently no option to run `uv pip install --relocatable` but
    # there is an option to do it with `uv venv --relocatable`.
    # So let's get a config file that marks a venv as relocatable.
    bare_venv_dir = target_dir / "bare-venv"
    temp_pyvenv_cfg = install_root / "pyvenv.cfg"
    run(
        [
            "uv",
            "venv",
            "--relocatable",
            "--python",
            str(install_root),
            str(bare_venv_dir),
        ]
    )
    os.rename(bare_venv_dir / "pyvenv.cfg", temp_pyvenv_cfg)
    shutil.rmtree(bare_venv_dir)
    info(f"Created relocatable venv config at: {fmt_path(temp_pyvenv_cfg)}")

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

    # Now we don't need the temp pyvenv.cfg file anymore.
    # It has absolute paths so better to just remove it.
    os.remove(temp_pyvenv_cfg)

    # Note we could compile everything like this, but it would add absolute paths within the pyc files:
    # compileall.compile_dir(target_absolute, quiet=1)

    # First handle binaries with possible absolute paths.
    if sys.platform == "darwin":
        update_macos_dylib_ids(install_root)

    # Make all the scripts relocatable.
    # This may not actually be necessary anymore since we've done the pyvenv.cfg hack
    # above, but it's no harm to have it here too.
    replace_shebangs([f"{install_root}/bin/*"], RELOCATABLE_PYTHON3_SHEBANG)

    # Then handle text files with absolute paths.
    replace_absolute_paths(install_root, str(target_absolute), str(target_dir))

    if source_only:
        info("Ensuring no .pyc files are included...")
        clean_pycache_dirs(target_absolute)
    else:
        info(f"Compiling all python files in: {fmt_path(target_absolute)}...")
        # Important to include stripdir to avoid absolute paths.
        compileall.compile_dir(target_absolute, quiet=1, stripdir=target_absolute)

    # Double check there are no absolute paths left.
    sanity_check_absolute_paths(install_root, str(target_absolute))

    success(
        f"Created standalone Python environment for packages {package_list} at: {fmt_path(target_dir)}"
    )


def update_macos_dylib_ids(python_root: Path):
    """
    macOS: Update the dylib ids of all the dylibs in the given root directory.
    It seems uv patches them with absolute paths using `install_name_tool`, which means
    they are tied to the user's install location.

    So we reset this but use `@executable_path` to ensure the dylibs are relocatable.
    See:
    https://github.com/astral-sh/uv/blob/main/crates/uv-python/src/managed.rs#L545-L567
    https://github.com/astral-sh/uv/blob/main/crates/uv-python/src/macos_dylib.rs
    """
    # Should be something like: py-standalone/cpython-3.13.2-macos-aarch64-none/lib/libpython3.13.dylib
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
    info(
        "Replacing all absolute paths in:\n"
        f"    {' '.join(text_glob)}:\n"
        f"    `{old_path_str}` -> `{new_path_str}`"
    )
    matches, _files_changed = search_replace_in_files(
        text_glob, old_path_str.encode(), new_path_str.encode()
    )
    info(f"Replaced {matches} total occurrences in {len(_files_changed)} files total")


def sanity_check_absolute_paths(python_root: Path, old_path_str: str):
    info()
    info("Sanity checking if any absolute paths remain...")
    all_files_glob = [f"{python_root}/**/*"]
    matches, _files_changed = search_replace_in_files(all_files_glob, old_path_str.encode(), None)
    if matches:
        fail(f"Found {matches} matches of `{old_path_str}` in binary files (see above)")
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
