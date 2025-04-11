# pip-build-standalone

pip-build-standalone builds a fully standalone, relocatable Python installation with the
given pips installed.

Typically, Python installations are not relocatable or transferable between machines, in
particular because scripts and libraries are tied to absolute file paths, such as your
home folder at the time Python or the venv was installed.

The Python installation created by pip-build-standalone has no absolute paths encoded in
any of the Python scripts or libraries, so should be installable as a binary folder at
any location on a machine with compatible architecture.

Warning: Built initially for macOS and not yet tested on Windows and Linux!

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
