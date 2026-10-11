from __future__ import annotations

import sysconfig
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path


class TailwindcssNotFound(FileNotFoundError): ...


def bundled_cli_name() -> str:
    return "_tailwindcss-bin" + (sysconfig.get_config_var("EXE") or "")


def find_tailwindcss_bin() -> str:
    """Return the path to the bundled tailwindcss binary."""
    exe = bundled_cli_name()
    try:
        dist = distribution("tailwindcss-bin")
    except PackageNotFoundError:
        pass
    else:
        for file in dist.files or ():
            if file.name == exe:
                path = Path(str(dist.locate_file(file))).resolve()
                if path.is_file():
                    return str(path)
    raise TailwindcssNotFound("Could not find the bundled tailwindcss CLI")
