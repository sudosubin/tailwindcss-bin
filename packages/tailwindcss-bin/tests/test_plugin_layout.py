from __future__ import annotations

import sys
from pathlib import Path

import pytest
import tomllib
from conftest import WORKSPACE_ROOT

if sys.version_info < (3, 11):
    pytest.skip("tomllib required", allow_module_level=True)


def npm_vendor_dest(module: str, npm: str) -> str:
    return f"tailwindcss_bin/plugins/{module}/node_modules/{npm}"


def _plugin_packages() -> list[Path]:
    return sorted(
        path.parent
        for path in WORKSPACE_ROOT.glob(
            "packages/tailwindcss-bin-*/pyproject.toml"
        )
    )


@pytest.mark.parametrize(
    "package_dir", _plugin_packages(), ids=lambda p: p.name
)
def test_plugin_pyproject_conventions(package_dir: Path):
    pyproject = package_dir / "pyproject.toml"
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    plugin = data["tool"]["tailwindcss-bin"]["plugin"]
    module = plugin["module"]
    npm = plugin["npm"]
    project_version = data["project"]["version"]
    vendor = data["tool"]["hatch"]["build"]["targets"]["wheel"]["hooks"][
        "npm-vendor"
    ]["packages"][0]
    assert vendor["dest"] == npm_vendor_dest(module, npm)
    assert vendor["package"] == npm
    assert vendor["version"] == project_version
