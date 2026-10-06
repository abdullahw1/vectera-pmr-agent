"""Unavailable aggregate track records preserve the draft, evidence, and release gate."""

import json
from pathlib import Path
import shutil

import fitz
import openpyxl
import pytest

from pmr.evidence import Ledger
from pmr.finance import build_financials
from pmr.ingest import Sheet, discover, norm
from pmr.pipeline import generate
from pmr.review import approve

INPUTS = Path(__file__).resolve().parents[1] / "inputs"
METRICS = {"irr": "NET IRR", "multiple": "Net Multiple"}


@pytest.fixture
def offline_charts(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def extraction(self, prompt, image=None):
        if image:
            return dict(
                title="Offline regression exhibit",
                series=[dict(label="Test period", series="Test", value=1, unit="%")],
            )
        return None

    monkeypatch.setattr("pmr.models.Model.ask", extraction)


def altered_flash(tmp_path, values, *, shifted=False):
    root = tmp_path / "inputs"
    shutil.copytree(INPUTS, root)
    path = root / "flash_4Q25.xlsx"
    book = openpyxl.load_workbook(path)
    if shifted:
        for worksheet in book:
            worksheet.insert_rows(1, 3)
    sheet = Sheet(path, book["ReturnsMultiples(Agg)"], Ledger())
    _, headers = sheet.headers(grouped=True)
    row = sheet.find("Vectera Initiated Investments", numeric=True)
    cells = {}
    for key, value in values.items():
        cell = row[headers[norm(METRICS[key])]]
        cell.value = value
        cells[key] = cell.coordinate
    book.save(path)
    if shifted:
        path = path.rename(root / "renamed_current_workbook.xlsx")
    return root, path, cells


@pytest.mark.parametrize("missing", [("irr",), ("multiple",), ("irr", "multiple")])
def test_missing_aggregate_figures_render_with_evidence_and_block_approval(
    tmp_path, offline_charts, missing
):
    root, flash, cells = altered_flash(tmp_path, {key: None for key in missing})
    output = tmp_path / "output"
    payload, summary = generate(root, output, "CPERS", "4Q25")
    portfolio = payload["data"]["portfolio"]
    issues = [i for i in summary["issues"] if i["severity"] == "blocker"]
    assert len(issues) == len(missing)
    assert all(i["code"] == "portfolio_value_missing" for i in issues)
    assert summary["checks_passed"] == summary["checks_total"]
    manifest = json.loads((output / "manifest.json").read_text())
    stats = next(s for s in payload["sections"] if s["title"] == "Investment Guidelines & Fund Statistics")
    rows = dict(stats["blocks"][0]["rows"])
    labels = {"irr": "Since-inception net IRR", "multiple": "Since-inception net equity multiple"}
    for key in missing:
        assert portfolio[key] is None
        identifier = portfolio[key + "_id"]
        fact = manifest["facts"][identifier]
        assert fact["value"] is None
        assert fact["source"]["file"] == flash.name
        assert fact["source"]["sheet"] == "ReturnsMultiples(Agg)"
        assert fact["source"]["cell"] == cells[key]
        assert fact["source"]["metric"] == METRICS[key]
        assert fact["source"]["status"] == "unavailable"
        assert rows[labels[key]] == "not available"
        assert any(identifier in c["resolved_evidence"] for c in manifest["claims"] if c["section"] == "Portfolio Overview")
        assert any(identifier in c["evidence"] and c["value"] == "not available"
                   for claim in manifest["claims"] for c in claim.get("cells", []))
        assert any(identifier in i["evidence"] for i in issues)
    with fitz.open(output / "report.pdf") as pdf:
        text = "\n".join(p.get_text() for p in pdf)
        assert "DRAFT" in text and "not available" in text
        assert "None" not in text
    assert all(METRICS[k] in (output / "review.md").read_text() for k in missing)
    assert len(summary["ranked_funds"]) == 4
    with pytest.raises(ValueError, match="Finalization blocked.*missing at ReturnsMultiples"):
        approve(output, dict(
            draft_hash=payload["draft_hash"], reviewer="Automated test",
            confirmed_charts=[c["id"] for c in payload["data"]["charts"]], acknowledged=True,
        ))
    assert not (output / "approval.json").exists()
    assert not (output / "final_report.pdf").exists()


def test_real_zero_is_not_missing_and_does_not_block_approval(tmp_path, offline_charts):
    root, _, _ = altered_flash(tmp_path, dict(irr=0, multiple=0))
    output = tmp_path / "output"
    payload, summary = generate(root, output, "CPERS", "4Q25")
    assert payload["data"]["portfolio"]["irr"] == 0
    assert payload["data"]["portfolio"]["multiple"] == 0
    assert not [i for i in summary["issues"] if i["severity"] == "blocker"]
    overview = next(s for s in payload["sections"] if s["title"] == "Portfolio Overview")
    text = " ".join(b.get("text", "") for b in overview["blocks"])
    assert "net IRR of 0.0%" in text and "0.00x net equity multiple" in text
    approve(output, dict(
        draft_hash=payload["draft_hash"], reviewer="Automated test",
        confirmed_charts=[c["id"] for c in payload["data"]["charts"]], acknowledged=True,
    ))
    assert (output / "final_report.pdf").exists()


def test_missing_totals_are_not_bound_to_a_filename_or_cell(tmp_path):
    root, flash, cells = altered_flash(tmp_path, dict(irr=None, multiple=None), shifted=True)
    ledger = Ledger()
    sources = discover(root, "CPERS", (2025, 4), ledger)
    data = build_financials(sources, (2025, 4), "CPERS", ledger)
    for key in METRICS:
        fact = ledger.facts[data["portfolio"][key + "_id"]]
        assert fact["source"]["file"] == flash.name
        assert fact["source"]["cell"] == cells[key]
    assert len([i for i in ledger.issues if i["code"] == "portfolio_value_missing"]) == 2


def test_malformed_aggregate_return_is_not_treated_as_a_blank(tmp_path):
    root, _, cells = altered_flash(tmp_path, dict(irr="not a number"))
    ledger = Ledger()
    sources = discover(root, "CPERS", (2025, 4), ledger)
    with pytest.raises(ValueError, match="Expected number.*" + cells["irr"]):
        build_financials(sources, (2025, 4), "CPERS", ledger)
