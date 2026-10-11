# tailwindcss-bin-tw-animate-css

[![version](https://badgen.net/pypi/v/tailwindcss-bin-tw-animate-css?label=version)](https://pypi.org/project/tailwindcss-bin-tw-animate-css/)
[![license](https://badgen.net/github/license/sudosubin/tailwindcss-bin?color=green)](https://github.com/sudosubin/tailwindcss-bin/blob/main/packages/tailwindcss-bin-tw-animate-css/LICENSE)

The [tw-animate-css](https://www.npmjs.com/package/tw-animate-css) plugin, bundled for
[tailwindcss-bin](https://github.com/sudosubin/tailwindcss-bin). No Node.js
installation is required.

```sh
uv add --dev 'tailwindcss-bin[tw-animate-css]'
uv run tailwindcss -i input.css -o output.css
```

Add this directive to your input stylesheet:

```css
@import "tw-animate-css";
```

The Python console command and `python -m tailwindcss_bin` discover installed
plugins automatically. When invoking the bundled executable directly, call
`tailwindcss_bin.apply_node_path()` before starting it.

The upstream version is pinned in `pyproject.toml`. Python `.devN` and `.postN`
versions identify development builds and packaging revisions of that version.
Requires Python 3.11 or newer. Wrapper and upstream MIT licenses are included.
