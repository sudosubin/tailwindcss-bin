from __future__ import annotations

import sysconfig
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path


class TailwindcssNotFound(FileNotFoundError): ...


def bundled_cli_name() -> str:
    return "tailwindcss-bin" + (sysconfig.get_config_var("EXE") or "")


def find_tailwindcss_bin() -> str:
    """Return the path to the bundled tailwindcss binary."""
    exe = bundled_cli_name()
    for path in (_wheel_script(exe), _venv_script(exe), _target_script(exe)):
        if path is not None:
            return str(path)
    raise TailwindcssNotFound("Could not find the bundled tailwindcss CLI")


def _wheel_script(exe: str) -> Path | None:
    try:
        dist = distribution("tailwindcss-bin")
    except PackageNotFoundError:
        return None
    root = (
        Path(str(dist.locate_file("tailwindcss_bin/__init__.py")))
        .resolve()
        .parent.parent
    )
    for path in root.glob(f"tailwindcss_bin-*.data/scripts/{exe}"):
        if path.is_file():
            return path
    return None


def _venv_script(exe: str) -> Path | None:
    script = Path(sysconfig.get_path("scripts")) / exe
    if not script.is_file() or script.read_bytes()[:2] == b"#!":
        return None
    return script


def _target_script(exe: str) -> Path | None:
    package = Path(__file__).resolve().parent
    if package.name != "tailwindcss_bin":
        return None
    script = package.parent / "bin" / exe
    return script if script.is_file() else None
