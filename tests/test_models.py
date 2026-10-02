"""Provider adapters are tested offline with mocked transport, not fabricated live results."""
import json

from pmr.evidence import Ledger
from pmr.models import Model, selected_quotes


def test_unverifiable_model_quote_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    model = Model(tmp_path, Ledger())
    model.ask = lambda prompt: {"quotes": ["The fund bought an invented asset.", "Income supported returns."]}
    assert selected_quotes("Income supported returns.", model) == ["Income supported returns."]


def test_api_failure_preserves_draft_and_redacts_key(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    ledger = Ledger(); model = Model(tmp_path, ledger)
    def fail(*args, **kwargs):
        raise RuntimeError("test-secret must not be printed")
    monkeypatch.setattr("urllib.request.urlopen", fail)
    assert model.ask("Return JSON") is None
    assert "test-secret" not in json.dumps(ledger.__dict__)


def test_cache_avoids_second_api_call(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    model = Model(tmp_path, Ledger())
    calls = []
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return json.dumps({"choices": [{"message": {"content": '{"quotes":["Evidence."]}'}}]}).encode()
    def respond(request, timeout):
        calls.append(request); return Response()
    monkeypatch.setattr("urllib.request.urlopen", respond)
    assert model.ask("Return JSON") == {"quotes": ["Evidence."]}
    assert model.ask("Return JSON") == {"quotes": ["Evidence."]}
    assert len(calls) == 1
