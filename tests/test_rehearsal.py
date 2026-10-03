"""Full client/period adaptation, not only isolated spreadsheet parsing."""

from pathlib import Path
import os

from scripts.rehearse_unseen import build_fixture
from pmr.pipeline import generate


def test_coherent_next_quarter_with_cross_year_approval(tmp_path, monkeypatch):
    for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
    original = Path(__file__).resolve().parents[1] / "inputs"
    expected = build_fixture(original, tmp_path / "inputs")
    payload, summary = generate(tmp_path / "inputs", tmp_path / "output", "EWRS", "1Q26")
    data = payload["data"]
    assert data["portfolio"]["name"] == "Example Workers Retirement System"
    assert str(data["portfolio"]["nav"]) == expected["nav"]
    assert len(data["funds"]) == 13
    assert "Tidewater Distressed Realty Fund" not in {f["name"] for f in data["funds"]}
    assert set(expected["added"]) <= {f["name"] for f in data["funds"]}
    assert [e["name"] for e in data["activity"]["open"]] == expected["open_names"]
    assert any(e["name"] == "Northgate Logistics Partners" for e in data["activity"]["reversed"])
    assert not data["activity"]["new"]
    assert data["support"]["Redwood Logistics Trust"]
    assert summary["checks_passed"] == summary["checks_total"]
    assert len(payload["sections"]) == 14
    assert all(i["code"] == "chart_unavailable" for i in summary["issues"] if i["severity"] == "blocker")
