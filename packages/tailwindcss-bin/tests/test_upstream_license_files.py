from __future__ import annotations

import base64
import hashlib
import json
import tarfile
import urllib.request
from io import BytesIO
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[3]


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


def test_plugin_upstream_license_matches_npm():
    cases = [
        (
            "tailwindcss-bin-tw-animate-css",
            "tw-animate-css",
            "LICENSE-tw-animate-css",
        ),
        (
            "tailwindcss-bin-tailwindcss-motion",
            "tailwindcss-motion",
            "LICENSE-tailwindcss-motion",
        ),
    ]
    root_license = (ROOT / "LICENSE").read_bytes()
    for pkg_dir, npm_name, license_name in cases:
        package = ROOT / "packages" / pkg_dir
        with package.joinpath("pyproject.toml").open("rb") as handle:
            version = tomllib.load(handle)["project"]["version"]
        on_disk = package.joinpath(license_name).read_bytes()
        upstream = npm_license(npm_name, version)
        assert on_disk == upstream
        assert on_disk != root_license
