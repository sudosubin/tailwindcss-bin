from __future__ import annotations

import os
from importlib.metadata import entry_points
from pathlib import Path


def node_module_paths() -> list[str]:
    paths = []
    plugins = entry_points(group="tailwindcss_bin.plugins")
    for ep in plugins:
        mod = ep.load()
        if mod.__file__ is None:
            continue
        paths.append(str(Path(mod.__file__).resolve().parent / "node_modules"))
    return paths


def apply_node_path() -> None:
    paths = node_module_paths()
    if not paths:
        return
    current = os.environ.get("NODE_PATH", "")
    parts = [p for p in current.split(os.pathsep) if p]
    if all(p in parts for p in paths):
        return
    head = os.pathsep.join(paths)
    os.environ["NODE_PATH"] = head + (os.pathsep + current if current else "")
