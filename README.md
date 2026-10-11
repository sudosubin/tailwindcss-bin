# tailwindcss-bin

[![version](https://badgen.net/pypi/v/tailwindcss-bin?label=version)](https://pypi.org/project/tailwindcss-bin/)
[![license](https://badgen.net/github/license/sudosubin/tailwindcss-bin?color=green)](LICENSE)

The [Tailwind CSS](https://tailwindcss.com) standalone CLI and optional plugins,
packaged as Python wheels. Python 3.11 or newer is required; Node.js and npm are
not needed to run the bundled CLI.

```sh
uv add --dev 'tailwindcss-bin[tailwindcss-motion,tw-animate-css]'
uv run tailwindcss -i input.css -o output.css --minify
```

Run without adding a project dependency:

```sh
uvx tailwindcss-bin -i input.css -o output.css --minify
```

| Package | Bundled software |
| --- | --- |
| [tailwindcss-bin](packages/tailwindcss-bin/) | Tailwind CSS standalone CLI |
| [tailwindcss-bin-tailwindcss-motion](packages/tailwindcss-bin-tailwindcss-motion/) | `tailwindcss-motion` |
| [tailwindcss-bin-tw-animate-css](packages/tailwindcss-bin-tw-animate-css/) | `tw-animate-css` |

The Python version follows the bundled upstream version. Development builds use
`.devN`; packaging-only corrections use `.postN`. Pin a development version
explicitly when testing it, for example `tailwindcss-bin==4.3.3.dev2`.

## Platforms

| Platform | Architectures | Requirements |
| --- | --- | --- |
| Linux, glibc | x86_64, aarch64 | glibc 2.24 or newer with a compatible system `libstdc++` |
| Linux, musl | x86_64, aarch64 | musl 1.2; Alpine needs `libstdc++` and `libgcc` |
| macOS | x86_64, arm64 | Minimum OS version is recorded in each wheel tag |
| Windows | x86_64 | 64-bit Windows |

See the [CLI package README](packages/tailwindcss-bin/README.md) for command and
Python API usage.

## Development and releases

[CONTRIBUTING.md](CONTRIBUTING.md) describes local checks and versioning.
Upstream updates open pull requests; successful CI on `main` publishes new
stable or post-release versions. Maintainers review and merge changes before
publication.
