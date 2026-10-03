"""Verify setup reuse, retry behavior, and the two-input launch workflow."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import pytest


spec = importlib.util.spec_from_file_location("bootstrap", Path(__file__).parents[1] / "scripts" / "launch.py")
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


def environment(tmp_path):
    (tmp_path / "requirements.txt").write_text("example==1.0\n")
    folder = tmp_path / ".launcher-venv"
    python = folder / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    python.parent.mkdir(parents=True)
    python.touch()
    return folder


def test_setup_installs_once_and_reinstalls_manifest_change(tmp_path, monkeypatch):
    folder = environment(tmp_path)
    run = Mock()
    monkeypatch.setattr(bootstrap.subprocess, "run", run)
    bootstrap.prepare(tmp_path)
    bootstrap.prepare(tmp_path)
    assert run.call_count == 1
    assert (folder / ".requirements.sha256").read_text() == hashlib.sha256((tmp_path / "requirements.txt").read_bytes()).hexdigest()
    (tmp_path / "requirements.txt").write_text("example==2.0\n")
    bootstrap.prepare(tmp_path)
    assert run.call_count == 2


def test_failed_install_does_not_mark_setup_complete(tmp_path, monkeypatch):
    folder = environment(tmp_path)
    monkeypatch.setattr(bootstrap.subprocess, "run", Mock(side_effect=subprocess.CalledProcessError(1, "pip")))
    with pytest.raises(subprocess.CalledProcessError):
        bootstrap.prepare(tmp_path)
    assert not (folder / ".requirements.sha256").exists()


def test_start_opens_workspace_without_prompts_or_generation(tmp_path, monkeypatch):
    import pmr.__main__ as cli
    monkeypatch.setattr(sys, "argv", ["pmr", "start", "--output", str(tmp_path)])
    monkeypatch.setattr(cli, "load_environment", lambda: None)
    generate = Mock(return_value=(None, {"checks_passed": 1, "checks_total": 1, "issues": []}))
    serve = Mock()
    monkeypatch.setattr(cli, "generate", generate)
    monkeypatch.setattr(cli, "serve_workspace", serve)
    cli.main()
    generate.assert_not_called()
    serve.assert_called_once_with(Path("inputs"), tmp_path, None, None, 0, open_browser=True)
