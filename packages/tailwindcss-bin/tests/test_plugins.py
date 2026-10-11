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
def plugin_project(tmp_path, monkeypatch):
    monkeypatch.delenv("NODE_PATH", raising=False)
    (tmp_path / "input.css").write_text(
        '@import "tailwindcss";\n'
        '@import "tw-animate-css";\n'
        '@plugin "tailwindcss-motion";\n',
        encoding="utf-8",
    )
    (tmp_path / "index.html").write_text(
        '<p class="animate-in motion-preset-fade bg-red-500 md:flex"></p>',
        encoding="utf-8",
    )
    return tmp_path


def assert_plugin_css(css):
    for selector in (
        ".animate-in",
        ".motion-preset-fade",
        ".bg-red-500",
        r".md\:flex",
    ):
        assert selector in css


def test_plugins_compile(cli_command, plugin_project):
    if Path(cli_command[0]).name == bundled_cli_name():
        apply_node_path()
    out = run_cmd(
        cli_command + ["-i", "input.css"],
        cwd=plugin_project,
        env=os.environ.copy(),
        check=True,
    ).stdout
    assert_plugin_css(out)


def test_plugins_minify(native_cli_command, plugin_project):
    apply_node_path()
    out = run_cmd(
        native_cli_command + ["-i", "input.css", "--minify"],
        cwd=plugin_project,
        check=True,
    ).stdout
    assert_plugin_css(out)


def test_plugins_watch(native_cli_command, plugin_project):
    apply_node_path()
    output = plugin_project / "output.css"
    with (plugin_project / "watch.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            native_cli_command
            + ["-i", "input.css", "-o", "output.css", "--watch=always"],
            cwd=plugin_project,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
        )
        try:
            assert_plugin_css(wait_for_css(process, output, ".bg-red-500"))
            (plugin_project / "index.html").write_text(
                '<p class="animate-in motion-preset-fade bg-blue-500"></p>',
                encoding="utf-8",
            )
            css = wait_for_css(process, output, ".bg-blue-500")
            assert ".animate-in" in css
            assert ".motion-preset-fade" in css
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
