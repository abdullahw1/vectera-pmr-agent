"""The round-two checkout includes the received inputs, not substituted source data."""

import hashlib
import json
from pathlib import Path

from pmr.pipeline import generate


ROOT = Path(__file__).resolve().parents[1]


def test_delivered_1q26_inputs_match_original_execution_record():
    record = json.loads((ROOT / "submission/v1-execution.json").read_text(encoding="utf-8"))
    expected = record["input_file_sha256"]
    files = {
        path.relative_to(ROOT / "inputs").as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (ROOT / "inputs").rglob("*")
        if path.is_file()
    }
    assert files == expected


def test_delivered_1q26_generates_source_blocked_draft(tmp_path, monkeypatch):
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    payload, summary = generate(ROOT / "inputs", tmp_path / "run", "CPERS", "1Q26")
    portfolio = payload["data"]["portfolio"]
    assert portfolio["irr"] is None and portfolio["multiple"] is None
    assert str(portfolio["nav"]) == "456961449.16"
    assert summary["checks_passed"] == 62 and summary["checks_total"] == 63
    missing = [i for i in summary["issues"] if i["code"] == "portfolio_value_missing"]
    assert len(missing) == 2
    assert all(i["severity"] == "blocker" for i in missing)
    assert (tmp_path / "run/CPERS_PMR_1Q26_DRAFT.pdf").is_file()
