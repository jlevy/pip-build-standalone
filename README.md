# py-app-standalone

py-app-standalone builds a standalone, relocatable Python installation with the given
packages installed. It's like a modern alternative to
[PyInstaller](https://github.com/pyinstaller/pyinstaller) that leverages the newer uv
ecosystem.

It's a wrapper around [uv](https://github.com/astral-sh/uv) that creates a standalone
Python installation, runs `uv pip install`, and then makes the required
platform-specific changes so you have a fully self-contained install directory
(packagable and runnable from any directory on a machine of the same platform).

## Background

Typically, Python installations are not relocatable or transferable between machines,
even if they are on the same platform, because scripts and libraries contain absolute
file paths (i.e., many scripts or libs include absolute paths that reference your home
folder or system paths on your machine).

Now [Gregory Szorc](https://github.com/indygreg)
[and Astral](https://astral.sh/blog/python-build-standalone) solved a lot of the
challenge with
[standalone Python distributions](https://github.com/astral-sh/python-build-standalone).
uv also supports [relocatable venvs](https://github.com/astral-sh/uv/pull/5515), so it's
possible to move a venv.
But at least currently, the actual Python installations created by uv can still have
absolute paths inside them in the dynamic libraries or scripts, as discussed in
[this issue](https://github.com/astral-sh/uv/issues/2389).

This tool is my quick attempt at fixing this.

It creates a fully self-contained installation of Python plus any desired packages.
The idea is this pre-built binary build for a given platform can now packaged for use
without any external dependencies, not even Python or uv.
And the the directory is relocatable.

This should work for any platform.
You just need to build on the same platform you want to run on.

Warning: Experimental!
This is a new tool. I've used it on macOS and it's very lightly tested on Ubuntu and
Windows, but obviously there are many possibilities for subtle incompatibilities within
a given platform.

## Alternatives

[PyInstaller](https://github.com/pyinstaller/pyinstaller) is the classic solution for
this and has a lot of features beyond this little tool, but is far more complex and does
not build on uv.

[shiv](https://github.com/linkedin/shiv) and [pex](https://github.com/pex-tool/pex) are
mature options that focus on zipping up your app, but not the Python installation.

[PyApp](https://github.com/ofek/pyapp) is a more recent effort on top of uv that creates
a Rust-built standalone binary that downloads/installs Python and dependencies at
runtime.

## Usage

Requires `uv` to run.
Do a `uv self update` to make sure you have a recent uv (I'm currently testing on
v0.6.14).

As an example, to create a full standalone Python 3.13 environment with the `cowsay`
package:

```sh
uvx py-app-standalone cowsay
```

Now the `./py-standalone` directory will work without being tied to a specific machine,
your home folder, or any other system-specific paths.

Binaries can now be put wherever and run:

```log
$ uvx py-app-standalone cowsay

▶ uv python install --managed-python --install-dir /Users/levy/wrk/github/py-app-standalone/py-standalone 3.13
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
...
Replaced shebang in: py-standalone/cpython-3.13.3-macos-aarch64-none/bin/pydoc3

Replacing all absolute paths in:
    py-standalone/cpython-3.13.3-macos-aarch64-none/bin/* py-standalone/cpython-3.13.3-macos-aarch64-none/lib/**/*.py:
    `/Users/levy/wrk/github/py-app-standalone/py-standalone` -> `py-standalone`
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

It uses a true (not venv) Python installation with the given packages installed, with
zero absolute paths encoded in any of the Python scripts or libraries.

After setting this up we:

- Ensure all scripts in `bin/` have relocatable shebangs (normally they are absolute)

- Clean up a few places source directories are baked into paths

- Do slightly different things on macOS, Linux, and Windows to make the binary libs are
  relocatable.

With those changes, it seems to work.
So *in theory*, the resulting binary folder should be installable as at any location on
a machine with compatible architecture.

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
