from __future__ import annotations

import glob
import hashlib
import os
import shutil
import subprocess
import tarfile
import tomllib
import zipfile
from pathlib import Path

import pytest
from conftest import PKG_ROOT, WORKSPACE_ROOT
from packaging.version import Version

BUILD_CONSTRAINTS = WORKSPACE_ROOT / ".tox" / "build-constraints.txt"


@pytest.fixture(scope="session")
def distributions(tmp_path_factory):
    out = tmp_path_factory.mktemp("distributions")
    subprocess.run(
        [
            "uv",
            "build",
            "--all-packages",
            "--sdist",
            "--wheel",
            "--build-constraints",
            str(BUILD_CONSTRAINTS),
            "--require-hashes",
            "-o",
            str(out),
        ],
        cwd=WORKSPACE_ROOT,
        check=True,
        env={**os.environ, "TAILWINDCSS_BIN_TARGET": "linux-x64"},
    )
    return out


@pytest.fixture(scope="session")
def cli_wheel(distributions):
    return next(distributions.glob("tailwindcss_bin-*.whl"))


def license_basenames(names: list[str]) -> set[str]:
    return {n.split("/licenses/", 1)[1] for n in names if "/licenses/" in n}


def test_cli_wheel_licenses(cli_wheel, tmp_path):
    config = tomllib.loads((PKG_ROOT / "pyproject.toml").read_text())
    expected = {
        path.relative_to(PKG_ROOT).as_posix()
        for pattern in config["project"]["license-files"]
        for filename in glob.glob(str(PKG_ROOT / pattern), recursive=True)
        if (path := Path(filename)).is_file()
    }
    with zipfile.ZipFile(cli_wheel) as archive:
        names = archive.namelist()
    assert license_basenames(names) == expected
    assert not any(".." in n for n in names)

    dest = tmp_path / "extract"
    dest.mkdir()
    with zipfile.ZipFile(cli_wheel) as archive:
        archive.extractall(dest)
    licenses = next(dest.glob("tailwindcss_bin-*.dist-info/licenses"))
    for path in expected:
        assert (licenses / path).read_bytes() == (PKG_ROOT / path).read_bytes()


def _assert_plugin_wheel_licenses(distributions, package, upstream_license):
    dist = package.replace("-", "_")
    wheel = next(distributions.glob(f"{dist}-*.whl"))
    package_root = WORKSPACE_ROOT / "packages" / package
    config = tomllib.loads((package_root / "pyproject.toml").read_text())
    vendor = config["tool"]["hatch"]["build"]["targets"]["wheel"]["hooks"][
        "npm-vendor"
    ]["packages"][0]
    expected = (package_root / upstream_license).read_bytes()
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert license_basenames(names) == {"LICENSE", upstream_license}
        assert not any(".." in n for n in names)
        assert archive.read(f"{vendor['dest']}/LICENSE") == expected
        for name in names:
            if "/licenses/" in name:
                source = package_root / name.split("/licenses/", 1)[1]
                assert archive.read(name) == source.read_bytes()
    assert expected != (WORKSPACE_ROOT / "LICENSE").read_bytes()


@pytest.mark.parametrize(
    ("package", "upstream_license"),
    [
        ("tailwindcss-bin-tailwindcss-motion", "LICENSE-tailwindcss-motion"),
        ("tailwindcss-bin-tw-animate-css", "LICENSE-tw-animate-css"),
    ],
)
def test_plugin_wheel_licenses(distributions, package, upstream_license):
    _assert_plugin_wheel_licenses(distributions, package, upstream_license)


@pytest.mark.parametrize(
    "package",
    [
        "tailwindcss-bin",
        "tailwindcss-bin-tailwindcss-motion",
        "tailwindcss-bin-tw-animate-css",
    ],
)
def test_sdist_rebuilds_the_same_wheel(distributions, tmp_path, package):
    dist = package.replace("-", "_")
    sdist = next(distributions.glob(f"{dist}-*.tar.gz"))
    with tarfile.open(sdist) as archive:
        members = archive.getmembers()
        assert not any("/node_modules/" in member.name for member in members)
        license_member = next(
            member for member in members if member.name.endswith("/LICENSE")
        )
        assert license_member.isfile()
        archive.extractall(tmp_path / "source", filter="data")
    source = next((tmp_path / "source").iterdir())
    assert (source / "LICENSE").read_bytes() == (
        WORKSPACE_ROOT / "LICENSE"
    ).read_bytes()

    # Reuse the verified release binary, while still checking its pinned hash.
    if package == "tailwindcss-bin":
        config = tomllib.loads((source / "pyproject.toml").read_text())
        release = Version(config["project"]["version"]).base_version
        cache_dir = f".cache/v{release}"
        cached = PKG_ROOT / cache_dir / "tailwindcss-linux-x64"
        if cached.is_file():
            destination = source / cache_dir / cached.name
            destination.parent.mkdir(parents=True)
            try:
                os.link(cached, destination)
            except OSError:
                shutil.copyfile(cached, destination)

    out = tmp_path / "rebuilt"
    subprocess.run(
        [
            "uv",
            "build",
            str(source),
            "--wheel",
            "--build-constraints",
            str(BUILD_CONSTRAINTS),
            "--require-hashes",
            "-o",
            str(out),
        ],
        check=True,
        env={**os.environ, "TAILWINDCSS_BIN_TARGET": "linux-x64"},
    )
    original = next(distributions.glob(f"{dist}-*.whl"))
    rebuilt = out / original.name
    assert (
        hashlib.sha256(rebuilt.read_bytes()).digest()
        == hashlib.sha256(original.read_bytes()).digest()
    )
