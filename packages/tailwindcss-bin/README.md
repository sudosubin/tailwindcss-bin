# tailwindcss-bin

The [Tailwind CSS](https://tailwindcss.com) standalone CLI, packaged as Python wheels.

## Usage

```sh
uv add --dev tailwindcss-bin
uv run tailwindcss -i input.css -o output.css --minify
# `tailwindcss` applies plugin NODE_PATH; `python -m tailwindcss_bin` is equivalent
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

## License

This wheel lists `LICENSE` (symlink to the repo root) and `LICENSE-tailwindcss`
(synced with the pinned Tailwind release) in `license-files`.
