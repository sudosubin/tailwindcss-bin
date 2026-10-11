# Contributing

Use Python 3.11 or newer and [uv](https://docs.astral.sh/uv/). Run these commands
from the repository root:

```sh
uv python install 3.14
uv sync --frozen --only-group tox
uv run --frozen --only-group tox tox -c packages/tailwindcss-bin \
  -e build,3.14 --parallel 1
uv run --frozen --only-group dev prek run --all-files
```

The `build` environment rebuilds all three package wheels with locked, hashed
build dependencies. Tests install those wheels and both plugins from the local
wheelhouse. Run `build` again after changing package code.

For every supported Python version, install 3.11 through 3.15 and use
`-e build,3.15,3.14,3.13,3.12,3.11 --parallel 1` instead. Keep local tox runs
sequential.

Package versions follow upstream `X.Y.Z`. Use `.devN` for development releases
and `.postN` for packaging-only corrections. Update tool pins and `uv.lock`
together. Upstream updates open PRs; maintainers review and merge them before
successful CI on `main` publishes stable or post-release versions.
