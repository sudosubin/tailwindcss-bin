from __future__ import annotations

import struct
from pathlib import Path

import hatch_build
import pytest
from auditwheel.architecture import Architecture
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


@pytest.mark.parametrize("arch", [Architecture.x86_64, Architecture.aarch64])
@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (elf(), (2, 17)),
        (elf(b"GLIBC_2.17\0GLIBCXX_TUNABLES\0"), (2, 17)),
        (elf(b"GLIBC_2.17\0GLIBCXX_3.4.19\0CXXABI_1.3.7\0"), (2, 17)),
        (elf(b"GLIBC_2.17\0GLIBCXX_3.4.22\0CXXABI_1.3.9\0"), (2, 24)),
        (elf(b"GLIBC_2.17\0CXXABI_1.3.8\0"), (2, 24)),
        (elf(b"GLIBC_2.28\0GLIBCXX_3.4.22\0"), (2, 28)),
        (elf(b"GLIBC_2.17\0GLIBCXX_3.4.28\0"), (2, 31)),
        (elf(b"GLIBC_2.17\0GLIBCXX_3.4.9\0"), (2, 17)),
        (
            elf(b"GLIBC_2.17\0") + elf(b"GLIBCXX_3.4.22\0CXXABI_1.3.9\0"),
            (2, 24),
        ),
    ],
)
def test_min_os_linux(data, expected, arch):
    assert hatch_build.min_os(data, arch) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (elf(b"GLIBC_2.2.5\0GLIBC_2.28\0"), (2, 28)),
        (elf(b"GLIBC_2.5\0"), (2, 17)),
    ],
)
def test_min_os_x86_64_legacy_glibc(data, expected):
    assert hatch_build.min_os(data, Architecture.x86_64) == expected


def test_min_os_preserves_aarch64_glibc_requirement():
    data = elf(b"GLIBC_2.18\0")
    assert hatch_build.min_os(data, Architecture.aarch64) == (2, 18)


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (macho((10, 15)), (10, 15)),
        (macho((13, 0)), (13, 0)),
        (macho((13, 3)), (14, 0)),
    ],
)
def test_min_os_macos(data, expected):
    assert hatch_build.min_os(data, Architecture.aarch64) == expected


@pytest.mark.parametrize("arch", [Architecture.x86_64, Architecture.aarch64])
@pytest.mark.parametrize(
    "symbol", [b"GLIBC_2.99", b"GLIBCXX_3.4.35", b"CXXABI_1.3.16"]
)
def test_min_os_rejects_unknown_manylinux_policy(symbol, arch):
    with pytest.raises(ValueError, match="no compatible manylinux policy"):
        hatch_build.min_os(elf(symbol), arch)


@pytest.mark.parametrize("host", ["darwin", "win32"])
@pytest.mark.parametrize(
    ("target", "tag"),
    [
        ("linux-x64", "manylinux_2_27_x86_64"),
        ("linux-arm64", "manylinux_2_26_aarch64"),
    ],
)
def test_linux_target_override_uses_target_architecture(
    monkeypatch, tmp_path, host, target, tag
):
    binary = tmp_path / "tailwindcss"
    binary.write_bytes(elf(b"GLIBC_2.17\0GLIBCXX_3.4.24\0CXXABI_1.3.11\0"))
    monkeypatch.setenv("TAILWINDCSS_BIN_TARGET", target)
    monkeypatch.setattr(hatch_build.sys, "platform", host)
    monkeypatch.setattr(
        hatch_build.platform,
        "machine",
        lambda: "arm64" if target == "linux-x64" else "x86_64",
    )
    monkeypatch.setattr(hatch_build, "fetch", lambda *_: binary)
    builder = WheelBuilder(str(ROOT))
    hook = hatch_build.CustomBuildHook(
        str(ROOT), {}, builder.config, builder.metadata, str(tmp_path), "wheel"
    )
    build_data = {"shared_scripts": {}}
    hook.initialize("standard", build_data)
    assert build_data["tag"] == f"py3-none-{tag}"


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
