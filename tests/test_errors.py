"""Actionable UI messages retain exact diagnostics for investigation."""
import pytest

from pmr.errors import explain_failure


@pytest.mark.parametrize("reason,title", [
    ("Expected one populated flash for UNKNOWN/(2025, 4), found 0", "Quarterly spreadsheet not found"),
    ("Expected one populated flash for CPERS/(2025, 4), found 2", "More than one matching spreadsheet"),
    ("No prior client PMR found; policy and format cannot be established", "Previous report is missing"),
    ("Ambiguous most recent prior client PMR", "Previous report is ambiguous"),
    ("Expected number at flash.xlsx/FundingStatus(Agg)/B8", "Invalid numerical data"),
    ("Currency must be finite with no fractions of a cent", "Invalid numerical data"),
    ("Source files changed during generation; regenerate", "Source documents changed during the run"),
    ("Implementation changed during generation; rerun", "Application updated during the run"),
    ("Unrecognized validation error", "Report generation stopped"),
])
def test_errors_are_actionable_and_keep_original_details(reason, title):
    result = explain_failure(reason, "UNKNOWN", "4Q25")
    assert result["error_title"] == title
    assert result["error_details"] == reason
    assert result["error_action"]
    assert "(2025, 4)" not in result["error"]


def test_historical_failure_is_explained_without_rewriting_history(tmp_path):
    from pmr.workspace import Workspace
    workspace = Workspace(tmp_path / "inputs", tmp_path / "output")
    original = "Expected one populated flash for UNKNOWN/(2025, 4), found 0"
    workspace.jobs["test"] = dict(id="test", client="UNKNOWN", quarter="4Q25", created=1, status="failed", error=original)
    result = workspace.state()["runs"][0]
    assert result["error_title"] == "Quarterly spreadsheet not found"
    assert "UNKNOWN, 4Q25" in result["error"]
    assert workspace.jobs["test"]["error"] == original
