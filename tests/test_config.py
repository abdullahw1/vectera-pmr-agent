"""Credential loading must preserve external keys and the no-key verification mode."""

import os

from pmr.config import load_environment


def test_local_env_loads_without_expanding_literal_credentials(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("PMR_LOAD_ENV", raising=False)
    path = tmp_path / ".env"
    path.write_text('OPENAI_API_KEY="test-${LITERAL}-key"\n')
    load_environment(path)
    assert os.environ["OPENAI_API_KEY"] == "test-${LITERAL}-key"


def test_external_key_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "external-test-key")
    monkeypatch.delenv("PMR_LOAD_ENV", raising=False)
    path = tmp_path / ".env"
    path.write_text('OPENAI_API_KEY="local-test-key"\n')
    load_environment(path)
    assert os.environ["OPENAI_API_KEY"] == "external-test-key"


def test_no_key_verification_does_not_load_env(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PMR_LOAD_ENV", "0")
    path = tmp_path / ".env"
    path.write_text('OPENAI_API_KEY="local-test-key"\n')
    load_environment(path)
    assert "OPENAI_API_KEY" not in os.environ
