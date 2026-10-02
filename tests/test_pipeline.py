import json
from pathlib import Path

import fitz
import pytest

from pmr.pipeline import generate
from pmr.review import approve

INPUTS = Path(__file__).resolve().parents[1] / "inputs"


@pytest.fixture
def no_keys(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_no_key_complete_financial_draft_and_repeatability(tmp_path, no_keys):
    first, a = generate(INPUTS, tmp_path / "a", "CPERS", "4Q25")
    second, b = generate(INPUTS, tmp_path / "b", "CPERS", "4Q25")
    assert a["meaning_hash"] == b["meaning_hash"]
    assert a["financial_hash"] == b["financial_hash"]
    assert first["draft_hash"] == second["draft_hash"]
    assert a["checks_passed"] == a["checks_total"]
    with fitz.open(tmp_path / "a" / "report.pdf") as pdf:
        text = "\n".join(p.get_text() for p in pdf)
    assert "$456.8M" in text
    assert "5.46% vs 2.66%" in text
    assert "withdrawn" in text and "lapsed" in text
    assert len(first["sections"]) == 14
    assert len(first["data"]["charts"]) == 7
    with pytest.raises(ValueError, match="Finalization blocked"):
        approve(tmp_path / "a", dict(draft_hash=first["draft_hash"], reviewer="Test", confirmed_charts=[]))


def test_external_draft_edit_invalidates_approval(tmp_path, no_keys):
    payload, _ = generate(INPUTS, tmp_path, "CPERS", "4Q25")
    payload["data"]["portfolio"]["nav"] = 1
    (tmp_path / "draft.json").write_text(json.dumps(payload, default=str))
    with pytest.raises(ValueError, match="outside the review workflow"):
        approve(tmp_path, dict(draft_hash=payload["draft_hash"], reviewer="Test"))


def test_mocked_chart_review_and_finalization(tmp_path, no_keys, monkeypatch):
    def extraction(self, prompt, image=None):
        if image:
            return dict(title="Offline test exhibit", series=[dict(label="Test period", series="Test", value=1, unit="%")], highlights=[0])
        return None
    monkeypatch.setattr("pmr.models.Model.ask", extraction)
    payload, _ = generate(INPUTS, tmp_path, "CPERS", "4Q25")
    chart_ids = [c["id"] for c in payload["data"]["charts"]]
    with pytest.raises(ValueError, match="Confirm all chart"):
        approve(tmp_path, dict(draft_hash=payload["draft_hash"], reviewer="Test", confirmed_charts=[]))
    corrected = dict(title="Offline corrected exhibit", series=[dict(label="Test period", series="Test", value=2, unit="%")])
    approve(tmp_path, dict(draft_hash=payload["draft_hash"], reviewer="Test", confirmed_charts=chart_ids,
                           corrections={chart_ids[0]: corrected}))
    approval = json.loads((tmp_path / "approval.json").read_text())
    assert approval["draft_hash"] == payload["draft_hash"]
    assert len(approval["report_sha256"]) == 64
    evidence = json.loads((tmp_path / "final_evidence.json").read_text())
    assert evidence["facts"][chart_ids[0]]["value"] == corrected
    with fitz.open(tmp_path / "final_report.pdf") as pdf:
        assert "DRAFT" not in "\n".join(p.get_text() for p in pdf)
