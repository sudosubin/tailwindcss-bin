from __future__ import annotations

import os
import subprocess
from importlib import import_module
from pathlib import Path

import pytest
from conftest import run_cmd, wait_for_css
from tailwindcss_bin import apply_node_path
from tailwindcss_bin._find_tailwindcss import bundled_cli_name


def test_both_plugins_are_installed():
    for name in ("tailwindcss_motion", "tw_animate_css"):
        module = import_module(f"tailwindcss_bin.plugins.{name}")
        assert module.__file__ is not None
        assert (Path(module.__file__).parent / "node_modules").is_dir()


@pytest.fixture
def plugin_project(write_source, monkeypatch):
    monkeypatch.delenv("NODE_PATH", raising=False)
    write_source(
        "input.css",
        '@import "tailwindcss";\n'
        '@import "tw-animate-css";\n'
        '@plugin "tailwindcss-motion";\n',
    )
    write_source(
        "index.html",
        '<p class="animate-in motion-preset-fade bg-red-500 md:flex"></p>',
    )
    return write_source


def assert_plugin_css(css):
    for selector in (
        ".animate-in",
        ".motion-preset-fade",
        ".bg-red-500",
        r".md\:flex",
    ):
        assert selector in css


def test_plugins_compile(tmp_path, cli_command, plugin_project):
    if Path(cli_command[0]).name == bundled_cli_name():
        apply_node_path()
    out = run_cmd(
        cli_command + ["-i", "input.css"],
        cwd=tmp_path,
        env=os.environ.copy(),
        check=True,
    ).stdout
    assert_plugin_css(out)


def test_plugins_minify(tmp_path, native_cli_command, plugin_project):
    apply_node_path()
    out = run_cmd(
        native_cli_command + ["-i", "input.css", "--minify"],
        cwd=tmp_path,
        check=True,
    ).stdout
    assert_plugin_css(out)


def test_plugins_watch(tmp_path, native_cli_command, plugin_project):
    apply_node_path()
    output = tmp_path / "output.css"
    with (tmp_path / "watch.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            native_cli_command
            + ["-i", "input.css", "-o", "output.css", "--watch=always"],
            cwd=tmp_path,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
        )
        try:
            assert_plugin_css(wait_for_css(process, output, ".bg-red-500"))
            plugin_project(
                "index.html",
                '<p class="animate-in motion-preset-fade bg-blue-500"></p>',
            )
            css = wait_for_css(process, output, ".bg-blue-500")
            assert ".animate-in" in css
            assert ".motion-preset-fade" in css
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
