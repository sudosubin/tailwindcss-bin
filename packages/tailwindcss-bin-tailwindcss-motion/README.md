# tailwindcss-bin-tailwindcss-motion

[![version](https://badgen.net/pypi/v/tailwindcss-bin-tailwindcss-motion?label=version)](https://pypi.org/project/tailwindcss-bin-tailwindcss-motion/)
[![license](https://badgen.net/github/license/sudosubin/tailwindcss-bin?color=green)](https://github.com/sudosubin/tailwindcss-bin/blob/main/packages/tailwindcss-bin-tailwindcss-motion/LICENSE)

The [tailwindcss-motion](https://www.npmjs.com/package/tailwindcss-motion) plugin, bundled for
[tailwindcss-bin](https://github.com/sudosubin/tailwindcss-bin). No Node.js
installation is required.

```sh
uv add --dev 'tailwindcss-bin[tailwindcss-motion]'
uv run tailwindcss -i input.css -o output.css
```

Add this directive to your input stylesheet:

```css
@plugin "tailwindcss-motion";
```

The Python console command and `python -m tailwindcss_bin` discover installed
plugins automatically. When invoking the bundled executable directly, call
`tailwindcss_bin.apply_node_path()` before starting it.

The upstream version is pinned in `pyproject.toml`. Python `.devN` and `.postN`
versions identify development builds and packaging revisions of that version.
Requires Python 3.11 or newer. Wrapper and upstream MIT licenses are included.
