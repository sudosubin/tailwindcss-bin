from __future__ import annotations

import struct
from pathlib import Path

import hatch_build
import pytest
from hatchling.builders.wheel import WheelBuilder
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


@pytest.mark.parametrize(
    ("system", "build_platform", "libc", "expected"),
    [
        ("linux", "linux-x86_64", "glibc", "linux-x64"),
        ("linux", "linux-aarch64", "glibc", "linux-arm64"),
        ("linux", "linux-x86_64", "", "linux-x64-musl"),
        ("linux", "linux-aarch64", "", "linux-arm64-musl"),
        ("darwin", "macosx-13.0-x86_64", "", "macos-x64"),
        ("darwin", "macosx-13.0-arm64", "", "macos-arm64"),
        ("darwin", "macosx-13.0-universal2", "", "macos-arm64"),
        ("win32", "win-amd64", "", "windows-x64"),
    ],
)
def test_detect_supported_targets(
    monkeypatch, system, build_platform, libc, expected
):
    monkeypatch.setattr(hatch_build.sys, "platform", system)
    monkeypatch.setattr(
        hatch_build.sysconfig, "get_platform", lambda: build_platform
    )
    monkeypatch.setattr(hatch_build.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(hatch_build.platform, "libc_ver", lambda: (libc, ""))
    assert hatch_build.detect_target() == expected


@pytest.mark.parametrize(
    ("system", "build_platform"),
    [
        ("linux", "linux-riscv64"),
        ("linux", "linux-ppc64le"),
        ("linux", "linux-armv7l"),
        ("win32", "win32"),
        ("win32", "win-arm64"),
        ("freebsd14", "freebsd-14.0-amd64"),
    ],
)
def test_detect_rejects_unsupported_targets(
    monkeypatch, system, build_platform
):
    monkeypatch.setattr(hatch_build.sys, "platform", system)
    monkeypatch.setattr(
        hatch_build.sysconfig, "get_platform", lambda: build_platform
    )
    with pytest.raises(ValueError, match="unsupported"):
        hatch_build.detect_target()


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
        (elf(b"GLIBC_2.17\0GLIBCXX_3.4.19\0CXXABI_1.3.7\0"), (2, 17)),
        (elf(b"GLIBC_2.17\0GLIBCXX_3.4.22\0CXXABI_1.3.9\0"), (2, 24)),
        (elf(b"GLIBC_2.17\0CXXABI_1.3.8\0"), (2, 24)),
        (elf(b"GLIBC_2.28\0GLIBCXX_3.4.22\0"), (2, 28)),
        (elf(b"GLIBC_2.17\0GLIBCXX_3.4.28\0"), (2, 31)),
        (elf(b"GLIBC_2.17\0GLIBCXX_3.4.9\0"), (2, 17)),
        (macho((10, 15)), (10, 15)),
        (macho((13, 0)), (13, 0)),
        (macho((13, 3)), (14, 0)),
    ],
)
def test_min_os(data, expected):
    assert hatch_build.min_os(data) == expected


@pytest.mark.parametrize("symbol", [b"GLIBCXX_3.4.35", b"CXXABI_1.3.16"])
def test_min_os_rejects_unknown_cxx_policy(symbol):
    with pytest.raises(ValueError, match="update the manylinux policy"):
        hatch_build.min_os(elf(symbol))


@pytest.mark.parametrize(
    ("target", "tag"),
    [
        ("linux-x64-musl", "musllinux_1_2_x86_64"),
        ("linux-arm64-musl", "musllinux_1_2_aarch64"),
        ("windows-x64", "win_amd64"),
    ],
)
def test_fixed_tags_skip_manylinux_policy(monkeypatch, tmp_path, target, tag):
    binary = tmp_path / "tailwindcss"
    binary.write_bytes(b"GLIBCXX_9.99.999")
    monkeypatch.setenv("TAILWINDCSS_BIN_TARGET", target)
    monkeypatch.setattr(hatch_build, "fetch", lambda *_: binary)
    builder = WheelBuilder(str(ROOT))
    hook = hatch_build.CustomBuildHook(
        str(ROOT), {}, builder.config, builder.metadata, str(tmp_path), "wheel"
    )
    build_data = {"shared_scripts": {}}
    hook.initialize("standard", build_data)
    assert build_data["tag"] == f"py3-none-{tag}"
