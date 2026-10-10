from __future__ import annotations

import sysconfig
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path


class TailwindcssNotFound(FileNotFoundError): ...


def find_tailwindcss_bin() -> str:
    """Return the path to the bundled tailwindcss binary."""
    exe = "tailwindcss" + (sysconfig.get_config_var("EXE") or "")
    candidates: list[Path] = []
    for path in (_wheel_script(exe), _venv_script(exe), _target_script(exe)):
        if path:
            candidates.append(path)
    for path in candidates:
        if path.is_file():
            return str(path)

    locations = "\n".join(f" - {path}" for path in candidates)
    raise TailwindcssNotFound(f"Could not find tailwindcss in:\n{locations}")


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
