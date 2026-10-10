from __future__ import annotations

import struct
from pathlib import Path

import hatch_build
import pytest
from hatchling.metadata.core import ProjectMetadata

ROOT = Path(__file__).resolve().parents[1]


def macho(minos: tuple[int, int]) -> bytes:
    header = struct.pack("<IiiIIIII", 0xFEEDFACF, 0, 0, 2, 1, 24, 0, 0)
    version = minos[0] << 16 | minos[1] << 8
    return header + struct.pack("<IIIIII", 0x32, 24, 1, version, 0, 0)


def elf(extra: bytes = b"") -> bytes:
    return b"\x7fELF" + bytes(80) + extra


def test_detect_target():
    assert hatch_build.detect_target() in hatch_build.TARGETS


def test_every_target_is_pinned():
    config = ProjectMetadata(str(ROOT), None).config
    pins = config["tool"]["tailwindcss-bin"]["sha256"]
    assert set(hatch_build.TARGETS) <= set(pins)


def test_fetch_rejects_mismatch(monkeypatch, tmp_path):
    monkeypatch.setattr(hatch_build, "CACHE", tmp_path)
    cached = tmp_path / "v1.0.0" / "tailwindcss-linux-x64"
    cached.parent.mkdir()
    cached.write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="pinned sha256"):
        hatch_build.fetch("1.0.0", "linux-x64", "0" * 64)
    assert not cached.exists()


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (elf(b"GLIBC_2.2.5\0GLIBC_2.28\0"), (2, 28)),
        (elf(b"GLIBC_2.5\0"), (2, 17)),
        (elf(), (2, 17)),
        (macho((10, 15)), (10, 15)),
        (macho((13, 0)), (13, 0)),
        (macho((13, 3)), (14, 0)),
    ],
)
def test_min_os(data, expected):
    assert hatch_build.min_os(data) == expected
