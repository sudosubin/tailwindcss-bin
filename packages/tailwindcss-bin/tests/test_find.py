from __future__ import annotations

import os

import pytest
from tailwindcss_bin import _find_tailwindcss as find


def test_finds_installed_binary():
    path = find.find_tailwindcss_bin()
    exe = find.bundled_cli_name()
    assert os.path.basename(path) == exe
    assert os.access(path, os.X_OK)


def test_finds_target_install(monkeypatch, tmp_path):
    exe = tmp_path / "bin" / find.bundled_cli_name()
    exe.parent.mkdir()
    exe.touch()
    monkeypatch.setattr(find, "_wheel_script", lambda _: None)
    monkeypatch.setattr(find, "_venv_script", lambda _: None)
    monkeypatch.setattr(find, "_target_script", lambda _exe: exe)
    assert find.find_tailwindcss_bin() == str(exe)


def test_lists_locations_when_missing(monkeypatch):
    monkeypatch.setattr(find, "_wheel_script", lambda _: None)
    monkeypatch.setattr(find, "_venv_script", lambda _: None)
    monkeypatch.setattr(find, "_target_script", lambda _: None)
    with pytest.raises(find.TailwindcssNotFound):
        find.find_tailwindcss_bin()
