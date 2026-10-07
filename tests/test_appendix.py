"""Presentation regression: Letter paper, readable source values and repeated labels."""

from pathlib import Path
import re

import fitz

from pmr.appendix import append_exhibits, display_cell, extract_exhibits, presentation_header
from pmr.appendix import register_exhibits, compact_report_exhibits
from pmr.evidence import Ledger
from pmr.verification import claim_manifest


def test_source_exhibits_keep_values_on_letter_pages():
    source = Path(__file__).resolve().parents[1] / "inputs/flash_4Q25.pdf"
    result = fitz.open()
    append_exhibits(result, source)
    assert len(result) <= 6  # Source padding and merged titles must not inflate the appendix.
    combined = "\n".join(p.get_text() for p in result)
    # Rendered currency signs/accounting negatives may differ from source spelling,
    # but every numeric cell must retain its precision and declared unit.
    for exhibit in extract_exhibits(source):
        for row in exhibit["rows"]:
            for column, value in enumerate(row):
                if value and re.fullmatch(r"-?\d[\d,.]*%?x?", value):
                    assert display_cell(exhibit, column, value) in combined
    for page in result:
        assert (page.rect.width, page.rect.height) == (612, 792)
        assert "DRAFT" in page.get_text()
        assert "Flash source page" in page.get_text()
    assert "CPERS Custom Benchmark" in combined
    assert "2025" in combined
    assert "Annual Returns - TWR Inception" not in combined
    assert "% NAV" in combined
    assert "Annualized Net Time-Weighted Return (%)" in combined
    assert "Diversification and Annual Returns" in combined
    assert "Returns and Multiples (%)" in combined
    assert "TGRS" not in combined and "TNET" not in combined


def test_each_projection_has_one_complete_header_and_unchanged_values():
    source = Path(__file__).resolve().parents[1] / "inputs/flash_4Q25.pdf"
    exhibits = extract_exhibits(source)
    with fitz.open(source) as original:
        for exhibit in exhibits:
            assert all(exhibit["headers"])
            assert all(len(row) == len(exhibit["headers"]) for row in exhibit["rows"])
            raw = original[exhibit["source_page"] - 1].find_tables().tables[0].extract()
            for row in exhibit["rows"]:
                assert any([str(candidate[c] or "") for c in exhibit["columns"]] == row for candidate in raw)


def test_appendix_manifest_maps_every_cell_to_its_source():
    source = Path(__file__).resolve().parents[1] / "inputs/flash_4Q25.pdf"
    ledger = Ledger()
    blocks = register_exhibits(source, ledger)
    blocks = [b for b in blocks if b["type"] == "table"]
    claims = claim_manifest([dict(title="Appendix", blocks=blocks)], ledger)
    with fitz.open(source) as document:
        raw_pages = {page.number + 1: page.find_tables().tables[0].extract() for page in document}
        for exhibit, block, claim in zip(extract_exhibits(source), blocks, claims):
            assert len(claim["cells"]) == sum(len(row) for row in block["rows"])
            for cell in claim["cells"]:
                fact = ledger.facts[cell["evidence"][0]]
                locator = fact["source"]
                raw = raw_pages[locator["page"]]
                raw_value = str(raw[locator["row"] - 1][locator["column"] - 1] or "")
                assert locator["raw_value"] == raw_value
                assert cell["value"] == fact["value"]
                assert cell["value"] == display_cell(exhibit, cell["column"], raw_value)
                assert locator["file"] == source.name
                assert "bbox" in locator


def test_display_decoration_preserves_cents_and_missing_values():
    exhibit = dict(headers=["Market Value", "Fees", "Allocation / plan", "Quarter NET"])
    assert display_cell(exhibit, 0, "1,367,035.55") == "$1,367,035.55"
    assert display_cell(exhibit, 0, "95000") == "$95,000"
    assert display_cell(exhibit, 1, "-31,290.15") == "($31,290.15)"
    assert display_cell(exhibit, 2, "0.1") == "10.0%"
    assert display_cell(exhibit, 2, "0.12345") == "12.345%"
    assert display_cell(exhibit, 2, "1") == "100.0%"
    assert display_cell(exhibit, 3, "") == ""
    assert display_cell(exhibit, 3, "1.28%") == "1.28%"
    assert presentation_header("3 Year(s) (%) TNET") == "3 Yr NET"


def test_net_summary_omits_gross_only_series_but_full_exhibits_keep_them():
    source = Path(__file__).resolve().parents[1] / "inputs/flash_4Q25.pdf"
    exhibits = extract_exhibits(source)
    summary = next(e for e in exhibits if e["title"] == "Annualized Net Time-Weighted Return (%)")
    assert [row[0] for row in summary["rows"]] == [
        "CPERS Custom Benchmark", "Cascadia Public Employees' Retirement System Portfolio",
    ]
    assert all(any(row[1:]) for row in summary["rows"])
    with fitz.open(source) as original:
        raw = original[summary["source_page"] - 1].find_tables().tables[0].extract()
        for row, source_row in zip(summary["rows"], summary["source_rows"]):
            assert row == [str(raw[source_row - 1][c] or "") for c in summary["columns"]]
    full = next(e for e in extract_exhibits(source, compact=False) if e["title"] == "Annualized Time-Weighted Returns (%) - 1 Year / 2 Year")
    npi = next(row for row in full["rows"] if row[0] == "NPI + 50 BPS")
    assert "5.44%" in npi and "3.16%" in npi


def test_exhibit_titles_follow_metrics_not_source_page_numbers(tmp_path):
    source = Path(__file__).resolve().parents[1] / "inputs/flash_4Q25.pdf"
    shuffled = tmp_path / "shuffled.pdf"
    with fitz.open(source) as original:
        original.select([5, 0, 1, 2, 3, 4])
        original.save(shuffled)
    expected = extract_exhibits(source)
    actual = extract_exhibits(shuffled)
    canonical = lambda rows: sorted((e["title"], e["headers"], e["rows"]) for e in rows)
    assert canonical(actual) == canonical(expected)


def test_unrecognized_readable_source_layout_is_retained(tmp_path):
    path = tmp_path / "flash.pdf"
    with fitz.open() as source:
        page = source.new_page()
        page.insert_text((40, 70), "Other Client 1Q26\nInvestment A NAV 123,456.78", fontsize=11)
        source.save(path)
    result = fitz.open()
    append_exhibits(result, path)
    assert len(result) == 1
    assert "123,456.78" in result[0].get_text()
    assert "original layout" in result[0].get_text()
    assert result[0].rect == fitz.Rect(0, 0, 612, 792)


def test_empty_and_duplicate_return_tables_are_omitted_without_losing_values():
    source = Path(__file__).resolve().parents[1] / "inputs/flash_4Q25.pdf"
    exhibits = extract_exhibits(source)
    assert len(exhibits) == 8
    assert not any("Since Inception" in e["title"] or "Valuation" in e["title"] for e in exhibits)
    schedule = next(e for e in exhibits if e["title"] == "Investment Schedule")
    assert not any(r[0] in {"US Portfolio", "Ex-US Portfolio"} for r in schedule["rows"])
    assert schedule["headers"][-1] == "% NAV"
    total = next(r for r in schedule["rows"] if r[0] == "Vectera Initiated Investments")
    assert sum(r[2:] == total[2:] for r in schedule["rows"]) == 1


def test_unique_fund_returns_and_real_zero_statistics_are_retained():
    source = Path(__file__).resolve().parents[1] / "inputs/flash_4Q25.pdf"
    ledger = Ledger()
    register_exhibits(source, ledger)
    recorded = {(f["source"].get("page"), f["source"].get("row"), f["source"].get("column"),
                 f["source"].get("raw_value")) for f in ledger.facts.values()}
    for exhibit in extract_exhibits(source, compact=False):
        for row, source_row in zip(exhibit["rows"], exhibit["source_rows"]):
            for value, column in zip(row, exhibit["columns"]):
                assert (exhibit["source_page"], source_row, column + 1, value) in recorded


def test_nav_only_statistics_merge_into_quarter_table_with_source_columns():
    metadata = dict(source_page=2, source_rows=[6, 32])
    quarter = dict(metadata, title="Returns and Multiples (%) - Quarter", columns=[0, 5],
                   headers=["Investment", "Quarter NET"], rows=[["Fund A", "1.00%"], ["Benchmark", "0.74%"]])
    valuation = dict(metadata, title="Valuation, IRR and Net Multiples", columns=[0, 1, 21, 22],
                     headers=["Investment", "Market Value", "Net IRR", "Net Multiple"],
                     rows=[["Fund A", "100", "", ""], ["Benchmark", "0", "", ""]])
    result = compact_report_exhibits([quarter, valuation])
    assert len(result) == 1
    assert result[0]["headers"] == ["Investment", "Quarter NET", "Market Value"]
    assert result[0]["columns"] == [0, 5, 1]
    assert result[0]["rows"] == [["Fund A", "1.00%", "100"], ["Benchmark", "0.74%", "0"]]
    assert quarter["headers"] == ["Investment", "Quarter NET"]
