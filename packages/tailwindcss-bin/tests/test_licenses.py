from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def license_basenames(names: list[str]) -> set[str]:
    return {n.split("/licenses/", 1)[1] for n in names if "/licenses/" in n}


def test_cli_wheel_includes_license_files(tmp_path):
    out = tmp_path / "wheels"
    out.mkdir()
    subprocess.run(
        [
            "uv",
            "build",
            "--wheel",
            "--package",
            "tailwindcss-bin",
            "-o",
            str(out),
        ],
        cwd=ROOT,
        check=True,
        env={
            **__import__("os").environ,
            "TAILWINDCSS_BIN_TARGET": "linux-x64",
        },
    )
    wheel = next(out.glob("tailwindcss_bin-*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    assert license_basenames(names) == {"LICENSE", "LICENSE-tailwindcss"}
    assert not any(".." in n for n in names)


def test_cli_wheel_extracts_without_license_conflict(tmp_path):
    out = tmp_path / "wheels"
    out.mkdir()
    subprocess.run(
        [
            "uv",
            "build",
            "--wheel",
            "--package",
            "tailwindcss-bin",
            "-o",
            str(out),
        ],
        cwd=ROOT,
        check=True,
        env={
            **__import__("os").environ,
            "TAILWINDCSS_BIN_TARGET": "linux-x64",
        },
    )
    wheel = next(out.glob("tailwindcss_bin-*.whl"))
    dest = tmp_path / "extract"
    dest.mkdir()
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(dest)
    licenses = next(dest.glob("tailwindcss_bin-*.dist-info/licenses"))
    assert (licenses / "LICENSE").read_bytes() == (
        ROOT / "LICENSE"
    ).read_bytes()
    assert (licenses / "LICENSE-tailwindcss").is_file()


def _assert_plugin_wheel_licenses(tmp_path, package, upstream_license):
    out = tmp_path / "wheels"
    out.mkdir()
    subprocess.run(
        ["uv", "build", "--wheel", "--package", package, "-o", str(out)],
        cwd=ROOT,
        check=True,
    )
    dist = package.replace("-", "_")
    wheel = next(out.glob(f"{dist}-*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    assert license_basenames(names) == {"LICENSE", upstream_license}
    assert not any(".." in n for n in names)
    assert any("/node_modules/" in n and n.endswith("/LICENSE") for n in names)


def test_tw_animate_css_wheel_licenses(tmp_path):
    _assert_plugin_wheel_licenses(
        tmp_path,
        "tailwindcss-bin-tw-animate-css",
        "LICENSE-tw-animate-css",
    )


def test_tailwindcss_motion_wheel_licenses(tmp_path):
    _assert_plugin_wheel_licenses(
        tmp_path,
        "tailwindcss-bin-tailwindcss-motion",
        "LICENSE-tailwindcss-motion",
    )
