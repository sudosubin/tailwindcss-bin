from __future__ import annotations

import base64
import hashlib
import json
import tarfile
import tomllib
import urllib.request
from io import BytesIO

import pytest
from conftest import WORKSPACE_ROOT


def npm_license(package: str, version: str) -> bytes:
    with urllib.request.urlopen(
        f"https://registry.npmjs.org/{package}/{version}"
    ) as response:
        meta = json.load(response)
    with urllib.request.urlopen(meta["dist"]["tarball"]) as response:
        data = response.read()
    integrity = meta["dist"]["integrity"]
    algo, digest = integrity.split("-", 1)
    if algo != "sha512":
        raise RuntimeError(integrity)
    expected = base64.b64decode(digest)
    if hashlib.sha512(data).digest() != expected:
        raise RuntimeError("integrity mismatch")
    with tarfile.open(fileobj=BytesIO(data), mode="r:gz") as archive:
        member = archive.extractfile("package/LICENSE")
        if member is None:
            raise RuntimeError("package/LICENSE missing")
        return member.read()


def _plugin_cases() -> list[tuple[str, str, str]]:
    cases = []
    for pyproject in sorted(
        WORKSPACE_ROOT.glob("packages/tailwindcss-bin-*/pyproject.toml")
    ):
        with pyproject.open("rb") as handle:
            data = tomllib.load(handle)
        plugin = data["tool"]["tailwindcss-bin"]["plugin"]
        cases.append(
            (
                pyproject.parent.name,
                plugin["npm"],
                plugin["upstream-license"],
            )
        )
    return cases


@pytest.mark.parametrize(
    ("pkg_dir", "npm_name", "license_name"),
    _plugin_cases(),
    ids=lambda row: row[0],
)
def test_plugin_upstream_license_matches_npm(pkg_dir, npm_name, license_name):
    package = WORKSPACE_ROOT / "packages" / pkg_dir
    with package.joinpath("pyproject.toml").open("rb") as handle:
        version = tomllib.load(handle)["project"]["version"]
    on_disk = package.joinpath(license_name).read_bytes()
    upstream = npm_license(npm_name, version)
    root_license = (WORKSPACE_ROOT / "LICENSE").read_bytes()
    assert on_disk == upstream
    assert on_disk != root_license
