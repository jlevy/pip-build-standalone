import glob
import shutil
import subprocess
from pathlib import Path

from pip_build_standalone import build_python_env


def test_simple_env():
    target_dir = Path("./py-standalone")
    if target_dir.exists():
        shutil.rmtree(target_dir)

    build_python_env(["cowsay"], target_dir, "3.13")

    assert target_dir.exists()
    assert target_dir.is_dir()

    python_roots = glob.glob(str(target_dir / "cpython-3.13.*"))
    assert len(python_roots) == 1
    python_root = Path(python_roots[0])

    # Check for cowsay in the correct location
    assert (python_root / "bin" / "cowsay").exists()
    assert (python_root / "bin" / "cowsay").is_file()

    subprocess.run(
        [str(python_root / "bin" / "cowsay"), "-t", "Hello, world!"],
        text=True,
        check=True,
    )
