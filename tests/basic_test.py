import glob
import os
import shutil
import subprocess
import sys
from os import chdir
from pathlib import Path

from py_app_standalone import build_python_env


def test_simple_env():
    target_dir = Path("./py-standalone")
    if target_dir.exists():
        shutil.rmtree(target_dir)
    new_python_root = Path("./renamed_root")
    if new_python_root.exists():
        shutil.rmtree(new_python_root)

    build_python_env(["cowsay"], target_dir, "3.13")

    assert target_dir.exists()
    assert target_dir.is_dir()

    python_roots = glob.glob(str(target_dir / "cpython-3.13.*"))
    assert len(python_roots) == 1
    python_root = Path(python_roots[0]).resolve()

    # Determine cowsay binary relative path based on platform
    bin_dir = "Scripts" if sys.platform == "win32" else "bin"
    cowsay_extension = ".exe" if sys.platform == "win32" else ""
    cowsay_rel_path = Path(bin_dir) / f"cowsay{cowsay_extension}"

    # Check for cowsay in the correct location
    assert (python_root / cowsay_rel_path).exists()
    assert (python_root / cowsay_rel_path).is_file()

    def run(cmd: list[str]):
        print(f"\nRunning: {cmd}")
        subprocess.run(cmd, check=True)

    run([str(python_root / cowsay_rel_path), "-t", "Hello, world!"])

    os.rename(python_root, new_python_root)

    run([str(new_python_root / cowsay_rel_path), "-t", "Hello, world from a new folder!"])

    # Confirm that the cwd doesn't matter.
    new_python_root = new_python_root.resolve()

    # Doesn't really matter where, just another dir.
    another_dir = new_python_root.parent.parent
    chdir(another_dir)
    run([str(new_python_root / cowsay_rel_path), "-t", "Hello, world from a different directory!"])
