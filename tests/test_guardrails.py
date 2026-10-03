"""Adversarial boundaries: money, entity-scoped quotes, pixels and agent privileges."""
from decimal import Decimal
import copy
import json
from pathlib import Path

import openpyxl
import pytest

from pmr.agent import EvidenceAgent
from pmr.charts import validate_chart
from pmr.evidence import Ledger, digest
from pmr.numeric import currency
from pmr.verification import validate_numeric_quote, semantic_manifest
from test_finance import calculate, copied
import shutil


@pytest.mark.parametrize("bad", [True, False, float("nan"), float("inf"), "0.001", "not money"])
def test_currency_rejects_invalid_source(bad):
    with pytest.raises(ValueError):
        currency(bad)


def test_one_cent_error_blocks_and_exact_serialization(tmp_path):
    root = copied(tmp_path)
    path = root / "flash_4Q25.xlsx"
    book = openpyxl.load_workbook(path)
    cell = next(r for r in book["CashActivity(Agg)"] if r[0].value == "Cornerstone Core Property Fund")[5]
    cell.value = float(currency(cell.value) + Decimal("0.01"))
    book.save(path)
    data, _, ledger = calculate(root)
    assert any(c["severity"] == "blocker" and not c["passed"] and abs(c["delta"]) == Decimal("0.01") for c in ledger.checks)
    ledger.save(tmp_path / "ledger.json")
    assert '436116069.16' in (tmp_path / "ledger.json").read_text()


def test_plan_facts_have_client_scope_not_adjacent_numeric_cell():
    data, _, ledger = calculate()
    for key in ["plan", "target"]:
        assert ledger.facts[data["portfolio"][key + "_id"]]["numeric"]["entity"] == data["portfolio"]["name"]


def test_quote_numbers_cannot_borrow_another_entity():
    fact = dict(entity="Fund A", source=dict(quote="Fund A returned 2.7% in 2025."))
    assert validate_numeric_quote("returned 2.7%", fact, entity="Fund A")
    with pytest.raises(ValueError, match="different entity"):
        validate_numeric_quote("returned 2.7%", fact, entity="Fund B")
    with pytest.raises(ValueError, match="cited source"):
        validate_numeric_quote("returned 7.2%", fact, entity="Fund A")


def chart():
    return dict(title="Exhibit", series=[dict(label="Period", series="NAV", value=1.2, unit="%")])


@pytest.mark.parametrize("mutation", ["boolean", "duplicate", "no_label", "range", "axis_without_bounds"])
def test_chart_schema_rejects_unsafe_observations(mutation):
    data = chart()
    if mutation == "boolean": data["series"][0]["value"] = True
    if mutation == "duplicate": data["series"] *= 2
    if mutation == "no_label": data["series"][0]["label"] = ""
    if mutation == "range": data["axis"] = dict(min=0, max=1, unit="%")
    if mutation == "axis_without_bounds":
        data["series"][0].update(method="axis_read", precision=.1)
    with pytest.raises(ValueError): validate_chart(data)


def test_mixed_chart_confidence_is_conservatively_approximate():
    from pmr.charts import validate_chart
    result = validate_chart(dict(title="Mixed", axis=dict(min=0, max=3, unit="%"), series=[
        dict(label="A", series="Test", value=1.2, unit="%", method="axis_read", precision=.1),
        dict(label="B", series="Test", value=2.2, unit="%", method="label")]))
    assert all(row["method"] == "axis_read" for row in result["series"])
    assert result["uncertainties"]


def test_approximation_is_disclosed_even_if_provider_omits_note():
    data = chart()
    data["axis"] = dict(min=0, max=3, unit="%")
    data["series"][0].update(method="axis_read", precision=.1)
    assert validate_chart(data)["uncertainties"]


def test_agent_uses_validation_feedback_before_finish():
    passage = dict(id="p1", entity="A", heading="Performance", text="Leasing improved.", source=dict(file="manager.pdf", page=1))
    class Model:
        provider = "mock"
        def __init__(self): self.step = 0
        def ask(self, prompt):
            self.step += 1
            if self.step == 1: return dict(tool="inspect_passage", args=dict(id="p1"))
            if self.step == 2: return dict(tool="validate_claim", args=dict(id="p1", quote="Invented asset."))
            if self.step == 3:
                assert "Quote must exist verbatim" in prompt
                return dict(tool="validate_claim", args=dict(id="p1", quote="Leasing improved."))
            return dict(tool="finish", args={})
    result = EvidenceAgent(Model(), {"p1": passage}, Ledger()).run()
    assert result["status"] == "finished"
    assert [s["valid"] for s in result["steps"]] == [True, False, True, True]
    assert result["validated_claims"][0]["quote"] == "Leasing improved."


def test_agent_cannot_read_paths_or_override_finance():
    agent = EvidenceAgent(None, {}, Ledger())
    for action in [dict(tool="inspect_passage", args=dict(id="../../.env")),
                   dict(tool="set_nav", args=dict(value=1)), dict(tool="finish", args={})]:
        with pytest.raises(ValueError): agent.tool(action)


def test_agent_stops_repeated_actions():
    class Model:
        provider = "mock"
        def ask(self, prompt): return dict(tool="list_evidence", args={})
    result = EvidenceAgent(Model(), {}, Ledger()).run()
    assert result["status"] == "repeated_action"
    assert len(result["steps"]) == 1


def test_chart_and_quote_numeric_changes_affect_semantic_hash():
    data = {k: {} for k in ["portfolio", "funds", "sleeves", "activity", "policy", "compliance", "history", "diversification"]}
    data.update(client="A", quarter="1Q26", charts=[dict(slide=4, chart=1, data=validate_chart(chart()))])
    sections = [dict(title="Market", blocks=[dict(type="paragraph", text="Yield was 1.2%.")])]
    original = digest(semantic_manifest(data, sections))
    data["charts"][0]["data"]["series"][0]["value"] = 1.3
    assert digest(semantic_manifest(data, sections)) != original
    data["charts"][0]["data"]["series"][0]["value"] = 1.2
    sections[0]["blocks"][0]["text"] = "Yield was 2.1%."
    assert digest(semantic_manifest(data, sections)) != original


def test_relevant_invalid_ic_date_and_full_client_name(tmp_path):
    root = copied(tmp_path); path = root / "ic_log_2025.xlsx"
    book = openpyxl.load_workbook(path); sheet = book.active
    row = next(r for r in sheet if r[5].value == "Northgate Logistics Partners")
    row[4].value = "Cascadia Public Employees' Retirement System"
    book.save(path)
    _, activity, ledger = calculate(root)
    assert any(e["name"] == "Northgate Logistics Partners" for e in activity["new"])
    row[1].value = "not a date"; book.save(path)
    _, _, ledger = calculate(root)
    assert any(i["code"] == "invalid_ic_date" and i["severity"] == "blocker" for i in ledger.issues)


def test_duplicate_flash_is_not_chosen_by_filename(tmp_path):
    root = copied(tmp_path)
    shutil.copy2(root / "flash_4Q25.xlsx", root / "looks_like_archive.xlsx")
    with pytest.raises(ValueError, match="found 2"): calculate(root)


def test_empty_workbook_is_explicit_blocker(tmp_path):
    root = copied(tmp_path)
    (root / "empty.xlsx").write_bytes(b"")
    _, _, ledger = calculate(root)
    assert any(i["code"] == "unreadable_input" for i in ledger.issues)
    assert any(i["status"] == "failed" and i["file"] == "empty.xlsx" for i in ledger.discovery)
