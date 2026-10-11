# tailwindcss-bin

The [Tailwind CSS](https://tailwindcss.com) standalone CLI, packaged as Python wheels.
Requires Python 3.11 or newer. The bundled CLI runs without Node.js or npm.

## Usage

```sh
uv add --dev tailwindcss-bin
uv run tailwindcss -i input.css -o output.css --minify
uv run tailwindcss -i input.css -o output.css --watch
```

Run without adding a project dependency:

```sh
uvx tailwindcss-bin -i input.css -o output.css --minify
```

Optional plugins:

```sh
uv add --dev 'tailwindcss-bin[tailwindcss-motion,tw-animate-css]'
```

```css
@import "tailwindcss";
@import "tw-animate-css";
@plugin "tailwindcss-motion";
```

`tailwindcss`, `tailwindcss-bin`, and `python -m tailwindcss_bin` configure
`NODE_PATH` for installed plugin wheels. Run commands from the directory
containing your CSS and templates, or use the Tailwind CLI's `--cwd` option.

For pip:

```sh
python -m pip install 'tailwindcss-bin[tailwindcss-motion,tw-animate-css]'
python -m tailwindcss_bin -i input.css -o output.css --minify
```

The package version follows the bundled Tailwind CSS version. Development
versions such as `4.3.3.dev2` require an explicit version pin or your installer's
pre-release option. A `.postN` suffix identifies a packaging-only correction.

## Python API

```python
import subprocess

from tailwindcss_bin import apply_node_path, find_tailwindcss_bin

apply_node_path()
subprocess.run([find_tailwindcss_bin(), "-i", "input.css"], check=True)
```

`find_tailwindcss_bin()` returns the installed binary's path. `apply_node_path()`
adds installed plugin directories to the current process environment for child
processes. It preserves existing `NODE_PATH` entries.

## Supported platforms

| Platform | Architectures | Requirements |
| --- | --- | --- |
| Linux (glibc) | x86_64, aarch64 | glibc 2.24 or newer; compatible `libstdc++` |
| Linux (musl) | x86_64, aarch64 | musl 1.2; `libstdc++` and `libgcc` |
| macOS | x86_64, arm64 | Minimum version is recorded in each wheel tag |
| Windows | x86_64 | 64-bit Windows |

The Linux wheel tags account for both glibc and the executable's embedded C++
libraries. Native file watching currently needs `GLIBCXX_3.4.22` and
`CXXABI_1.3.9`.

On Alpine:

```sh
apk add --no-cache libstdc++ libgcc
```
