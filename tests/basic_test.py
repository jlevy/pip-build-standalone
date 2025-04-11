import glob
import os
import shutil
import subprocess
from os import chdir
from pathlib import Path

from pip_build_standalone import build_python_env


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

    # Check for cowsay in the correct location
    assert (python_root / "bin" / "cowsay").exists()
    assert (python_root / "bin" / "cowsay").is_file()

    def run(cmd: list[str]):
        print(f"\nRunning: {cmd}")
        subprocess.run(cmd, check=True)

    run([str(python_root / "bin" / "cowsay"), "-t", "Hello, world!"])

    os.rename(python_root, new_python_root)

    run([str(new_python_root / "bin" / "cowsay"), "-t", "Hello, world from a new folder!"])

    # Confirm that the cwd doesn't matter.
    new_python_root = new_python_root.resolve()
    chdir("/")
    run([str(new_python_root / "bin" / "cowsay"), "-t", "Hello, world from a different directory!"])
