# tailwindcss-bin

The [Tailwind CSS](https://tailwindcss.com) standalone CLI, packaged as Python wheels.

## Usage

```sh
uv add --dev tailwindcss-bin
uv run tailwindcss -i input.css -o output.css --minify
# or, with optional plugins: uv run python -m tailwindcss_bin ...
```

Optional plugins:

```sh
uv add --dev 'tailwindcss-bin[tw-animate-css,motion]'
```

```css
@import "tailwindcss";
@import "tw-animate-css";
@plugin "tailwindcss-motion";
```

```python
from tailwindcss_bin import find_tailwindcss_bin
```

The package version matches the bundled Tailwind CSS version.

## Supported platforms

| Platform | Architectures |
| --- | --- |
| Linux (glibc) | x86_64, aarch64 |
| Linux (musl) | x86_64, aarch64 |
| macOS | x86_64, arm64 |
| Windows | x86_64 |

The minimum glibc and macOS versions in the wheel tags are read from each
binary. On Alpine, install `libstdc++` and `libgcc`.

## Development

```sh
direnv allow
prek install
uvx --with tox-uv tox p
TAILWINDCSS_BIN_TARGET=linux-x64 uv build --wheel --package tailwindcss-bin
```

To bump Tailwind CSS, change `project.version` in this package, refresh the upstream
file named in `license-files` (for example `LICENSE-tailwindcss`), and pin the
release digests in `[tool.tailwindcss-bin]`:

```sh
version=4.3.3
curl -fsSL "https://raw.githubusercontent.com/tailwindlabs/tailwindcss/v$version/LICENSE" \
  -o LICENSE-tailwindcss
gh release view "v$version" --repo tailwindlabs/tailwindcss --json assets \
  --jq '.assets[] | select(.name | startswith("tailwindcss-"))
    | "sha256.\(.name[12:] | rtrimstr(".exe")) = \"\(.digest[7:])\""'
```

## License

This wheel lists `LICENSE` (symlink to the repo root) and `LICENSE-tailwindcss`
(synced with the pinned Tailwind release) in `license-files`.
