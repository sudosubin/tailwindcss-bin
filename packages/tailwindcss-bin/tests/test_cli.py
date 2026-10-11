from __future__ import annotations

import subprocess
import time
from importlib.metadata import version

import pytest
from conftest import run_cmd
from packaging.version import Version


def test_reports_bundled_version(cli_command):
    expected = Version(version("tailwindcss-bin")).base_version
    result = run_cmd(cli_command + ["--help"], check=True)
    assert f"tailwindcss v{expected}" in result.stdout


def test_compiles_css(tmp_path, cli_command):
    (tmp_path / "input.css").write_text('@import "tailwindcss";')
    (tmp_path / "index.html").write_text('<p class="p-4 md:flex"></p>')
    result = run_cmd(
        cli_command + ["-i", "input.css"], cwd=tmp_path, check=True
    )
    assert ".p-4" in result.stdout
    assert r".md\:flex" in result.stdout


def test_propagates_exit_code(tmp_path, cli_command):
    result = run_cmd(cli_command + ["-i", "missing.css"], cwd=tmp_path)
    assert result.returncode == 1


def _wait_for_css(process, output, selector):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if output.is_file() and selector in output.read_text():
            return
        assert process.poll() is None, "CSS watcher exited unexpectedly"
        time.sleep(0.05)
    pytest.fail(f"CSS watcher did not generate {selector}")


def test_watch_rebuilds_and_exits_on_stdin_close(tmp_path, cli_command):
    (tmp_path / "input.css").write_text('@import "tailwindcss";')
    html = tmp_path / "index.html"
    html.write_text('<p class="p-4"></p>')
    output = tmp_path / "output.css"
    with (tmp_path / "watch.log").open("w") as log:
        process = subprocess.Popen(
            cli_command + ["-i", "input.css", "-o", "output.css", "--watch"],
            cwd=tmp_path,
            stdin=subprocess.PIPE,
            stdout=log,
            stderr=log,
        )
        assert process.stdin is not None
        try:
            _wait_for_css(process, output, ".p-4")
            html.write_text('<p class="p-8"></p>')
            _wait_for_css(process, output, ".p-8")
            process.stdin.close()
            assert process.wait(timeout=10) == 0
        finally:
            process.stdin.close()
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
