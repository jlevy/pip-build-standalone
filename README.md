# pip-build-standalone

pip-build-standalone builds a standalone, relocatable Python installation with the given
pips installed.

Typically, Python installations are not relocatable or transferable between machines, in
particular because scripts and libraries contain absolute file paths (such as your home
folder at the time Python or the venv was installed).

[uv](https://github.com/jlevy/uv) already uses
[standalone Python distributions](https://github.com/astral-sh/python-build-standalone)
and offers [relocatable venvs](https://github.com/astral-sh/uv/pull/5515). But Python
installations created by uv still do typically have absolute paths in libs and scripts.

This tool uses uv to set up a true (not venv) Python installation with the given pips
installed, with zero absolute paths encoded in any of the Python scripts or libraries.
So the resulting binary folder should be installable as at any location on a machine
with compatible architecture.

Warning: Experimental!
Built initially for macOS and not yet tested on Windows and Linux!

## Usage

This tool requires uv to run.

As an example, to create a full standalone Python 3.13 environment with the `cowsay`
package:

```sh
uvx pip-build-standalone cowsay
```

Now the `./py-standalone` directory should work on macOS without being tied to a
specific machine, your home folder, or any other system-specific paths.

Binaries should be run from the directory above this target directory:

```
mv ./py-standalone /tmp && cd /tmp

./py-standalone/cpython-3.13.2-macos-aarch64-none/bin/cowsay -t moo
```

* * *

*This project was built from
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv).*
