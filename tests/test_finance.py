"""Golden expectations live only in tests; mutations exercise unseen-run behavior."""
from pathlib import Path
import shutil

import openpyxl
import pytest

from pmr.evidence import Ledger
from pmr.ingest import discover, quarter, entity
from pmr.finance import build_financials, commitments

INPUTS = Path(__file__).resolve().parents[1] / "inputs"


def calculate(root=INPUTS, client="CPERS"):
    ledger = Ledger()
    sources = discover(root, client, (2025, 4), ledger)
    data = build_financials(sources, (2025, 4), client, ledger)
    activity = commitments(sources, (2025, 4), client, data["funds"], ledger)
    return data, activity, ledger


def copied(tmp_path):
    root = tmp_path / "inputs"
    shutil.copytree(INPUTS, root)
    return root


def test_golden_financial_results():
    data, activity, ledger = calculate()
    assert not [x for x in ledger.issues if x["severity"] == "blocker"]
    assert all(x["passed"] for x in ledger.checks)
    assert data["portfolio"]["nav"] == pytest.approx(436116069.16)
    assert data["portfolio"]["one_net"] == pytest.approx(5.4568960063)
    assert data["portfolio"]["ex_us"] == pytest.approx(9.6199045052)
    roles = {f["name"]: f["roles"] for f in data["funds"]}
    assert roles["Redwood Logistics Trust"] == ["largest contributor", "second-largest individual position"]
    assert roles["Cornerstone Core Property Fund"] == ["second-largest detractor", "largest individual position"]
    assert roles["Ironwood Value-Add Fund III"] == ["second-largest contributor"]
    assert roles["Meridian Opportunity Fund V"] == ["largest detractor"]
    assert sum(e["amount"] for e in activity["open"]) == 65_000_000
    assert len(activity["new"]) == 2
    assert {e["action"] for e in activity["reversed"]} == {"withdrawn", "lapsed"}


def test_rows_move_and_filenames_change(tmp_path):
    root = copied(tmp_path)
    path = root / "flash_4Q25.xlsx"
    book = openpyxl.load_workbook(path)
    for sheet in book:
        sheet.insert_rows(1, 4)
    book.save(path)
    path.rename(root / "unhelpful_name.xlsx")
    data, activity, ledger = calculate(root)
    assert data["portfolio"]["nav"] == pytest.approx(436116069.16)
    assert len(data["funds"]) == 12
    assert all(c["passed"] for c in ledger.checks)
    assert len(activity["new"]) == 2


def test_ic_order_does_not_define_chronology(tmp_path):
    root = copied(tmp_path)
    path = root / "ic_log_2025.xlsx"
    book = openpyxl.load_workbook(path); sheet = book.active
    rows = list(sheet.values)
    for index, row in enumerate(reversed(rows[1:]), 2):
        for column, value in enumerate(row, 1):
            sheet.cell(index, column, value)
    book.save(path)
    _, activity, _ = calculate(root)
    assert [e["name"] for e in activity["open"]] == ["Northgate Logistics Partners", "Ridgeline Value Fund IV"]


def test_bad_cash_value_is_a_blocker(tmp_path):
    root = copied(tmp_path)
    path = root / "flash_4Q25.xlsx"
    book = openpyxl.load_workbook(path); sheet = book["CashActivity(Agg)"]
    row = next(r for r in sheet if r[0].value == "Cornerstone Core Property Fund")
    row[5].value += 1000
    book.save(path)
    _, _, ledger = calculate(root)
    assert any(x["code"] == "reconciliation" and x["severity"] == "blocker" for x in ledger.issues)


def test_entity_normalization_is_conservative():
    assert entity("Ironwood Value-Add Fund 3, L.P.") == entity("Ironwood Value-Add Fund III")
    assert entity("Ridgeline Value Fund IV") != entity("Ridgeline Value Fund V")
    assert entity("Kestrel U.S. Real Estate Fund") == entity("Kestrel US Real Estate Fund")


def test_document_date_wins_over_inception_quarter():
    assert quarter("Third Quarter 2025, inception 4Q 10") == (2025, 3)
    assert quarter("1Q26") == (2026, 1)


def test_unknown_committee_action_blocks_finalization(tmp_path):
    root = copied(tmp_path)
    path = root / "ic_log_2025.xlsx"
    book = openpyxl.load_workbook(path); sheet = book.active
    row = next(r for r in sheet if r[5].value == "Northgate Logistics Partners")
    row[9].value = "maybe approved"
    book.save(path)
    _, activity, ledger = calculate(root)
    assert len(activity["new"]) == 1
    assert any(x["code"] == "unknown_ic_action" for x in ledger.issues)


def test_zero_balance_fund_can_be_added_without_code_edits(tmp_path):
    root = copied(tmp_path)
    path = root / "flash_4Q25.xlsx"
    book = openpyxl.load_workbook(path)
    for name in ["FundingStatus(Agg)", "CashActivity(Agg)", "ReturnsMultiples(Agg)"]:
        sheet = book[name]
        row = next(r for r in sheet if r[0].value == "Tidewater Distressed Realty Fund")
        values = [c.value for c in row]
        values[0] = "Additional Real Estate Fund VII"
        for i in range(1, len(values)):
            if isinstance(values[i], (int, float)):
                values[i] = 0
        sheet.insert_rows(row[0].row + 1)
        for column, value in enumerate(values, 1):
            sheet.cell(row[0].row + 1, column, value)
    book.save(path)
    data, _, ledger = calculate(root)
    assert len(data["funds"]) == 13
    assert all(c["passed"] for c in ledger.checks)
    assert not next(f for f in data["funds"] if f["name"].startswith("Additional"))["roles"]


def test_different_client_identity_benchmark_and_policy(tmp_path):
    import fitz
    root = copied(tmp_path)
    path = root / "flash_4Q25.xlsx"
    book = openpyxl.load_workbook(path)
    old_name = "Cascadia Public Employees' Retirement System"
    new_name = "Example Workers Retirement System"
    for sheet in book:
        for row in sheet:
            for cell in row:
                if isinstance(cell.value, str):
                    cell.value = cell.value.replace(old_name, new_name).replace("CPERS Custom Benchmark", "EWRS Custom Benchmark")
    book.save(path)
    document = fitz.open(); page = document.new_page()
    page.insert_text((50, 50), new_name + "\nPerformance Measurement Report\nThird Quarter 2025\n"
                     "allocated 12% of total plan assets with an allowable range of 6-22%\n"
                     "<=42% per sector\n<=30% Ex-US\n<=45% / 70%", fontsize=10)
    document.save(root / "unfamiliar_prior.pdf")
    data, _, ledger = calculate(root, "EWRS")
    assert data["portfolio"]["name"] == new_name
    assert data["portfolio"]["benchmark"] == "EWRS Custom Benchmark"
    assert data["policy"]["sector"] == [42]
    assert data["policy"]["leverage"] == [45, 70]
    assert all(c["passed"] for c in ledger.checks)


def test_after_quarter_approval_excluded(tmp_path):
    from datetime import datetime
    root = copied(tmp_path); path = root / "ic_log_2025.xlsx"
    book = openpyxl.load_workbook(path); sheet = book.active
    sheet.append([9999, datetime(2026, 1, 5), "IC", "Commitment", "CPERS", "Future Fund", "Approve USD99 million", None, None, "approved"])
    book.save(path)
    _, activity, _ = calculate(root)
    assert all(e["name"] != "Future Fund" for e in activity["events"])
