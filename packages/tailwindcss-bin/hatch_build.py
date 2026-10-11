from __future__ import annotations

import hashlib
import os
import platform
import re
import struct
import sys
import sysconfig
import urllib.request
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from packaging.version import Version

CACHE = Path(__file__).parent / ".cache"
TARGETS = {
    "linux-arm64": "manylinux_{}_{}_aarch64",
    "linux-arm64-musl": "musllinux_1_2_aarch64",
    "linux-x64": "manylinux_{}_{}_x86_64",
    "linux-x64-musl": "musllinux_1_2_x86_64",
    "macos-arm64": "macosx_{}_{}_arm64",
    "macos-x64": "macosx_{}_{}_x86_64",
    "windows-x64": "win_amd64",
}
# Shared x86_64/aarch64 C++ limits from auditwheel's manylinux policies.
MANYLINUX_CXX = (
    ((2, 17), (3, 4, 19), (1, 3, 7)),
    ((2, 24), (3, 4, 22), (1, 3, 10)),
    ((2, 27), (3, 4, 24), (1, 3, 11)),
    ((2, 31), (3, 4, 28), (1, 3, 12)),
    ((2, 34), (3, 4, 29), (1, 3, 13)),
    ((2, 35), (3, 4, 30), (1, 3, 13)),
    ((2, 39), (3, 4, 33), (1, 3, 15)),
    ((2, 42), (3, 4, 34), (1, 3, 15)),
)


def detect_target() -> str:
    systems = {"darwin": "macos", "win32": "windows", "linux": "linux"}
    if sys.platform not in systems:
        raise ValueError(f"unsupported operating system {sys.platform!r}")
    # Honors `_PYTHON_HOST_PLATFORM`, set by cibuildwheel when cross-building.
    machine = sysconfig.get_platform().split("-")[-1]
    if machine == "universal2":
        machine = platform.machine()
    architectures = {
        "arm64": "arm64",
        "aarch64": "arm64",
        "x86_64": "x64",
        "amd64": "x64",
    }
    if machine.lower() not in architectures:
        raise ValueError(f"unsupported architecture {machine!r}")
    target = f"{systems[sys.platform]}-{architectures[machine.lower()]}"
    if sys.platform == "linux" and platform.libc_ver()[0] != "glibc":
        target += "-musl"
    if target not in TARGETS:
        raise ValueError(f"unsupported target {target!r}")
    return target


def _github_get(url: str) -> bytes:
    request = urllib.request.Request(url)
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request) as response:
        return response.read()


def fetch(release: str, target: str, sha256: str) -> Path:
    exe = ".exe" if target.startswith("windows") else ""
    path = CACHE / f"v{release}" / f"tailwindcss-{target}{exe}"
    if not path.is_file():
        url = f"https://github.com/tailwindlabs/tailwindcss/releases/download/v{release}"
        data = _github_get(f"{url}/{path.name}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    if hashlib.sha256(path.read_bytes()).hexdigest() != sha256:
        path.unlink()
        raise RuntimeError(
            f"{path.name} does not match the pinned sha256; verify and pin "
            f"the digests from `gh release view v{release} --repo "
            f"tailwindlabs/tailwindcss --json assets`"
        )
    path.chmod(0o755)
    return path


def min_os(data: bytes) -> tuple[int, int]:
    """Return the minimum macOS or manylinux baseline for the binary."""
    if data[:4] == b"\xcf\xfa\xed\xfe":
        (ncmds,) = struct.unpack_from("<I", data, 16)
        offset = 32
        for _ in range(ncmds):
            cmd, size = struct.unpack_from("<II", data, offset)
            if cmd == 0x32:  # LC_BUILD_VERSION
                (v,) = struct.unpack_from("<I", data, offset + 12)
                major, minor = v >> 16, v >> 8 & 0xFF
                # Since macOS 11, installers only match `<major>_0` tags.
                if major >= 11 and minor:
                    return major + 1, 0
                return major, minor
            offset += size
        raise ValueError("no minimum macOS version")

    glibc = re.findall(rb"GLIBC_(\d+)\.(\d+)", data)
    requirements = []
    for family in (b"GLIBCXX", b"CXXABI"):
        versions = re.findall(family + rb"_(\d+(?:\.\d+)+)", data)
        requirements.append(
            max(
                (tuple(map(int, value.split(b"."))) for value in versions),
                default=(0,),
            )
        )
    glibcxx, cxxabi = requirements
    for baseline, max_glibcxx, max_cxxabi in MANYLINUX_CXX:
        if glibcxx <= max_glibcxx and cxxabi <= max_cxxabi:
            return max([baseline, *((int(a), int(b)) for a, b in glibc)])
    raise ValueError(
        "binary requires a newer C++ ABI; update the manylinux policy limits"
    )


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict) -> None:
        target = os.environ.get("TAILWINDCSS_BIN_TARGET") or detect_target()
        if target not in TARGETS:
            raise ValueError(f"unknown target {target!r}: {', '.join(TARGETS)}")

        release = Version(self.metadata.version).base_version
        pins = self.metadata.config["tool"]["tailwindcss-bin"]["sha256"]
        binary = fetch(release, target, pins[target])
        tag = TARGETS[target]
        if "{}" in tag:
            tag = tag.format(*min_os(binary.read_bytes()))

        build_data["shared_scripts"][str(binary)] = (
            f"tailwindcss-bin{binary.suffix}"
        )
        build_data["pure_python"] = False
        build_data["tag"] = f"py3-none-{tag}"
