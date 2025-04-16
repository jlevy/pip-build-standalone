# pip-build-standalone

pip-build-standalone builds a standalone, relocatable Python installation with the given
pips installed. It's like a modern alternative to
[PyInstaller](https://github.com/pyinstaller/pyinstaller) that leverages
[uv](https://github.com/astral-sh/uv).

## Background

Typically, Python installations are not relocatable or transferable between machines,
even if they are on the same platform, because scripts and libraries contain absolute
file paths (i.e., many scripts or libs include absolute paths that reference your home
folder or system paths on your machine).

Now uv has solved a lot of the challenge by providing
[standalone Python distributions](https://github.com/astral-sh/python-build-standalone).
It also supports [relocatable venvs](https://github.com/astral-sh/uv/pull/5515), so it's
possible to move a venv.
But the actual Python installations created by uv can still have absolute paths inside
them in the dynamic libraries or scripts, as discussed in
[this issue](https://github.com/astral-sh/uv/issues/2389).

This tool is my quick attempt at fixing this.

It creates a fully self-contained installation of Python plus any desired pips.
The idea is this pre-built binary build for a given platform can now packaged for use
without any external dependencies, not even Python or uv.
And the the directory is relocatable.

This should work for any platform.
You just need to build on the same platform you want to run on.

## Usage

This tool requires uv to run.
Do a `uv self update` to make sure you have a recent uv (I'm currently testing on
v0.6.14).

As an example, to create a full standalone Python 3.13 environment with the `cowsay`
package:

```sh
uvx pip-build-standalone cowsay
```

Now the `./py-standalone` directory will work without being tied to a specific machine,
your home folder, or any other system-specific paths.

Binaries can now be put wherever and run:

```log
$ uvx pip-build-standalone cowsay

▶ uv python install --managed-python --install-dir /Users/levy/wrk/github/pip-build-standalone/py-standalone 3.13
Installed Python 3.13.3 in 2.35s
 + cpython-3.13.3-macos-aarch64-none

⏱ Call to run took 2.37s

▶ uv venv --relocatable --python py-standalone/cpython-3.13.3-macos-aarch64-none py-standalone/bare-venv
Using CPython 3.13.3 interpreter at: py-standalone/cpython-3.13.3-macos-aarch64-none/bin/python3
Creating virtual environment at: py-standalone/bare-venv
Activate with: source py-standalone/bare-venv/bin/activate

⏱ Call to run took 590ms
Created relocatable venv config at: py-standalone/cpython-3.13.3-macos-aarch64-none/pyvenv.cfg

▶ uv pip install cowsay --python py-standalone/cpython-3.13.3-macos-aarch64-none --break-system-packages
Using Python 3.13.3 environment at: py-standalone/cpython-3.13.3-macos-aarch64-none
Resolved 1 package in 0.82ms
Installed 1 package in 2ms
 + cowsay==6.1

⏱ Call to run took 11.67ms
Found macos dylib, will update its id to remove any absolute paths: py-standalone/cpython-3.13.3-macos-aarch64-none/lib/libpython3.13.dylib

▶ install_name_tool -id @executable_path/../lib/libpython3.13.dylib py-standalone/cpython-3.13.3-macos-aarch64-none/lib/libpython3.13.dylib

⏱ Call to run took 34.11ms

Inserting relocatable shebangs on scripts in:
    py-standalone/cpython-3.13.3-macos-aarch64-none/bin/*
Replaced shebang in: py-standalone/cpython-3.13.3-macos-aarch64-none/bin/cowsay
Replaced shebang in: py-standalone/cpython-3.13.3-macos-aarch64-none/bin/pydoc3.13
Replaced shebang in: py-standalone/cpython-3.13.3-macos-aarch64-none/bin/pip3.13
Replaced shebang in: py-standalone/cpython-3.13.3-macos-aarch64-none/bin/pip3
Replaced shebang in: py-standalone/cpython-3.13.3-macos-aarch64-none/bin/idle3
Replaced shebang in: py-standalone/cpython-3.13.3-macos-aarch64-none/bin/python3-config
Replaced shebang in: py-standalone/cpython-3.13.3-macos-aarch64-none/bin/pip
Replaced shebang in: py-standalone/cpython-3.13.3-macos-aarch64-none/bin/idle3.13
Replaced shebang in: py-standalone/cpython-3.13.3-macos-aarch64-none/bin/python3.13-config
Replaced shebang in: py-standalone/cpython-3.13.3-macos-aarch64-none/bin/pydoc3

Replacing all absolute paths in:
    py-standalone/cpython-3.13.3-macos-aarch64-none/bin/* py-standalone/cpython-3.13.3-macos-aarch64-none/lib/**/*.py:
    `/Users/levy/wrk/github/pip-build-standalone/py-standalone` -> `py-standalone`
Replaced 27 occurrences in: py-standalone/cpython-3.13.3-macos-aarch64-none/lib/python3.13/_sysconfigdata__darwin_darwin.py
Replaced 27 total occurrences in 1 files total
Compiling all python files in: py-standalone...

Sanity checking if any absolute paths remain...
Great! No absolute paths found in the installed files.

✔ Success: Created standalone Python environment for packages ['cowsay'] at: py-standalone

$ ./py-standalone/cpython-3.13.3-macos-aarch64-none/bin/cowsay -t 'im moobile'
  __________
| im moobile |
  ==========
          \
           \
             ^__^
             (oo)\_______
             (__)\       )\/\
                 ||----w |
                 ||     ||

$ # Now let's confirm it runs in a different location!
$ mv ./py-standalone /tmp

$ /tmp/py-standalone/cpython-3.13.3-macos-aarch64-none/bin/cowsay -t 'udderly moobile'
  _______________
| udderly moobile |
  ===============
               \
                \
                  ^__^
                  (oo)\_______
                  (__)\       )\/\
                      ||----w |
                      ||     ||

$
```

## How it Works

It uses a true (not venv) Python installation with the given pips installed, with zero
absolute paths encoded in any of the Python scripts or libraries.

After setting this up we:

- Ensure all scripts in `bin/` have relocatable shebangs (normally they are absolute)

- Clean up a few places source directories are baked into paths

- Do slightly different things on macOS, Linux, and Windows to make the binary libs are
  relocatable.

With those changes, it seems to work.
So *in theory*, the resulting binary folder should be installable as at any location on
a machine with compatible architecture.

Warning: Experimental!
No promises this works or is even a good idea.
It is lightly tested on macOS, ubuntu, and Windows, but obviously there are
possibilities for subtle incompatibilities within a given platform.

## More Notes

- The good thing is this *does* work to encapsulate binary builds and libraries, as long
  as the binaries are included in the pip.
  It *doesn't* the problem of external dependencies that traditionally need to be
  installed outside the Python ecosystem (like ffmpeg).
  (For this, [pixi](https://github.com/prefix-dev/pixi/) seems promising.)

- This by default pre-compiles all files to create `__pycache__` .pyc files.
  This means the build should start faster and could run on a read-only filesystem.
  Use `--source-only` to have a source-only build.

- For now, we assume you are packaging a pip already on PyPI but of course the same
  approach could work for unpublished code.

* * *

*This project was built from
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv).*
