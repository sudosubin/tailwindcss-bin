# tailwindcss-bin

Monorepo of Python wheels for the [Tailwind CSS](https://tailwindcss.com)
standalone CLI and optional plugins.

## Development

```sh
prek install
uv sync
uvx --with tox-uv tox p
TAILWINDCSS_BIN_TARGET=linux-x64 uv build --wheel --package tailwindcss-bin
```
