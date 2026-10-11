from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError, PathDistribution
from pathlib import Path

import pytest
from tailwindcss_bin import _find_tailwindcss as find


def test_finds_installed_binary():
    path = find.find_tailwindcss_bin()
    assert os.path.basename(path) == find.bundled_cli_name()
    assert os.access(path, os.X_OK)


@pytest.mark.parametrize(
    ("site", "scripts"),
    [
        ("lib/python3.11/site-packages", "bin"),
        ("user/lib/python3.11/site-packages", "user/bin"),
        ("target", "target/bin"),
        ("wheel", "wheel/tailwindcss_bin-4.3.3.data/scripts"),
        ("windows/Lib/site-packages", "windows/Scripts"),
    ],
    ids=["prefix", "user", "target", "extracted-wheel", "windows"],
)
def test_finds_recorded_binary(monkeypatch, tmp_path, site, scripts):
    binary = tmp_path / scripts / find.bundled_cli_name()
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"\x7fELF")
    wrapper = binary.with_name(binary.name.removeprefix("_"))
    wrapper.write_text("Python entry point")
    site = tmp_path / site
    info = site / "tailwindcss_bin-4.3.3.dist-info"
    info.mkdir(parents=True)
    info.joinpath("METADATA").write_text(
        "Metadata-Version: 2.4\nName: tailwindcss-bin\nVersion: 4.3.3\n"
    )
    relative = Path(os.path.relpath(binary, site)).as_posix()
    wrapper_relative = Path(os.path.relpath(wrapper, site)).as_posix()
    info.joinpath("RECORD").write_text(f"{wrapper_relative},,\n{relative},,\n")
    monkeypatch.setattr(find, "distribution", lambda _: PathDistribution(info))

    # An unrelated interpreter installation must not take precedence.
    stale = tmp_path / "stale" / find.bundled_cli_name()
    stale.parent.mkdir()
    stale.write_bytes(b"\x7fELF")
    monkeypatch.setattr(find.sysconfig, "get_path", lambda _: str(stale.parent))
    assert find.find_tailwindcss_bin() == str(binary.resolve())


def test_does_not_read_binary(monkeypatch):
    def reject_read(path):
        pytest.fail(f"Discovery must not read the binary: {path}")

    monkeypatch.setattr(Path, "read_bytes", reject_read)
    assert Path(find.find_tailwindcss_bin()).is_file()


def test_missing_distribution(monkeypatch):
    def missing(name):
        raise PackageNotFoundError(name)

    monkeypatch.setattr(find, "distribution", missing)
    with pytest.raises(find.TailwindcssNotFound, match="bundled"):
        find.find_tailwindcss_bin()


@pytest.mark.parametrize("record", [None, "missing/_tailwindcss-bin,,\n"])
def test_missing_installed_binary(monkeypatch, tmp_path, record):
    info = tmp_path / "tailwindcss_bin-4.3.3.dist-info"
    info.mkdir()
    info.joinpath("METADATA").write_text("Name: tailwindcss-bin\n")
    if record is not None:
        info.joinpath("RECORD").write_text(record)
    monkeypatch.setattr(find, "distribution", lambda _: PathDistribution(info))
    with pytest.raises(find.TailwindcssNotFound, match="bundled"):
        find.find_tailwindcss_bin()
