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
        assert len(pdf) <= 16
        assert all((p.rect.width, p.rect.height) == (612, 792) for p in pdf)
        text = "\n".join(p.get_text() for p in pdf)
    assert "$456.8M" in text
    assert "5.46% vs 2.66%" in text
    assert "withdrawn" in text and "lapsed" in text
    assert len(first["sections"]) == 14
    market = next(s for s in first["sections"] if s["title"] == "Market Update")
    assert all(block["type"] == "paragraph" for block in market["blocks"])
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
                           acknowledged=True, corrections={chart_ids[0]: dict(data=corrected, reason="Test corrected visible value")}))
    approval = json.loads((tmp_path / "approval.json").read_text())
    assert approval["draft_hash"] == payload["draft_hash"]
    assert len(approval["report_sha256"]) == 64
    evidence = json.loads((tmp_path / "final_evidence.json").read_text())
    assert evidence["facts"][chart_ids[0]]["value"]["series"][0]["value"] == 2
    with fitz.open(tmp_path / "final_report.pdf") as pdf:
        assert "DRAFT" not in "\n".join(p.get_text() for p in pdf)


def test_source_change_during_model_enrichment_is_rejected(tmp_path, no_keys, monkeypatch):
    import shutil
    import openpyxl
    root = tmp_path / "inputs"
    shutil.copytree(INPUTS, root)
    changed = False
    def extraction(self, prompt, image=None):
        nonlocal changed
        if image:
            if not changed:
                path = root / "flash_4Q25.xlsx"
                book = openpyxl.load_workbook(path)
                row = next(r for r in book["CashActivity(Agg)"] if r[0].value == "Cornerstone Core Property Fund")
                row[5].value += 1
                book.save(path)
                changed = True
            return dict(title="Test", series=[dict(label="Test", series="Test", value=1, unit="%")])
        return None
    monkeypatch.setattr("pmr.models.Model.ask", extraction)
    with pytest.raises(ValueError, match="changed during generation"):
        generate(root, tmp_path / "output", "CPERS", "4Q25")
    assert not (tmp_path / "output" / "draft.json").exists()
    assert json.loads((tmp_path / "output" / "diagnostics.json").read_text())["status"] == "blocked"


def test_word_numeral_and_changed_heading_end_to_end(tmp_path, no_keys):
    import shutil
    root = tmp_path / "inputs"
    shutil.copytree(INPUTS, root)
    report = root / "manager_reports" / "ironwood_value_add_fund_3_4Q25.pdf"
    with fitz.open(report) as original:
        text = "\n".join(page.get_text() for page in original)
    text = text.replace("Ironwood Value-Add Fund 3, L.P.", "Ironwood Value-Add Fund Three, L.P.")
    text = text.replace("Investments Impacting Performance", "Quarterly Operating Review")
    with fitz.open() as changed:
        page = changed.new_page()
        assert page.insert_textbox(fitz.Rect(35, 35, 560, 780), text, fontsize=9) >= 0
        changed.save(report)
    payload, summary = generate(root, tmp_path / "output", "CPERS", "4Q25")
    assert summary["checks_passed"] == summary["checks_total"]
    name = "Ironwood Value-Add Fund III"
    assert name in payload["data"]["support"]
    assert any(i["code"] == "manager_extraction" and i.get("fund") == name for i in payload["ledger"]["issues"])
    section = next(s for s in payload["sections"] if s["title"] == "Tactical and Special Situations Portfolio")
    assert any("A current manager report was supplied" in b.get("text", "") for b in section["blocks"])
