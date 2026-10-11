# tailwindcss-bin

Monorepo of Python wheels for the [Tailwind CSS](https://tailwindcss.com)
standalone CLI and optional plugins.

| Package | PyPI name |
| --- | --- |
| Core CLI | `tailwindcss-bin` |
| Plugins | `tailwindcss-bin-tailwindcss-motion`, `tailwindcss-bin-tw-animate-css` |

Optional extras on the core package: `tailwindcss-motion`, `tw-animate-css`.

## Releases

Push a tag that matches `project.version` in the package directory:

- `tailwindcss-bin@v4.3.3.dev1` — core (cibuildwheel)
- `tailwindcss-bin-tw-animate-css@v1.4.0.dev1` — plugin (`uv build`)

See `.github/workflows/release.yml`.
