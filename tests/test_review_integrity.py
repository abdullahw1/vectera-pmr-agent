"""A UI checkbox is not a security boundary; enforce review rules in the backend."""
from pathlib import Path
import pytest

from pmr.pipeline import generate
from pmr.review import approve

INPUTS = Path(__file__).resolve().parents[1] / "inputs"


@pytest.fixture
def extracted(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    def mock(self, prompt, image=None):
        return dict(title="Test", series=[dict(label="Test", series="Test", value=1, unit="%")]) if image else None
    monkeypatch.setattr("pmr.models.Model.ask", mock)
    payload, _ = generate(INPUTS, tmp_path, "CPERS", "4Q25")
    request = dict(draft_hash=payload["draft_hash"], reviewer="Test reviewer", acknowledged=True,
                   confirmed_charts=[c["id"] for c in payload["data"]["charts"]])
    return tmp_path, payload, request


def test_acknowledgment_is_required_by_backend(extracted):
    output, _, request = extracted
    request.pop("acknowledged")
    with pytest.raises(ValueError, match="acknowledgment"): approve(output, request)
    assert not (output / "approval.json").exists()


def test_changed_asset_blocks_approval(extracted):
    output, payload, request = extracted
    asset = output / payload["data"]["charts"][0]["asset"]
    asset.write_bytes(b"changed image")
    with pytest.raises(ValueError, match="asset changed"): approve(output, request)


def test_correction_requires_reason_and_full_schema(extracted):
    output, payload, request = extracted
    identifier = payload["data"]["charts"][0]["id"]
    request["corrections"] = {identifier: dict(data=dict(series=[dict(value=1)]))}
    with pytest.raises(ValueError, match="reason"): approve(output, request)
    request["corrections"][identifier]["reason"] = "Correct displayed value"
    with pytest.raises(ValueError, match="labels"): approve(output, request)


def test_unknown_chart_id_cannot_be_confirmed(extracted):
    output, _, request = extracted
    request["confirmed_charts"].append("made-up")
    with pytest.raises(ValueError, match="Unknown confirmed"): approve(output, request)


def test_final_semantics_and_evidence_are_saved(extracted):
    output, _, request = extracted
    approve(output, request)
    assert (output / "final_semantic_manifest.json").is_file()
    assert (output / "final_manifest.json").is_file()
    assert (output / "final_evidence.json").is_file()
