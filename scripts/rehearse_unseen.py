"""Build a disposable alternate client/period and run the entire no-key pipeline.

This is a test fixture generator, not production ingestion. Fixture names, dates
and invented approvals below are intentionally allowed golden-test data.
"""
import argparse
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import openpyxl
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
import html

from pmr.evidence import Ledger
from pmr.ingest import Sheet, pdf_pages, norm
from pmr.numeric import MONEY_HEADERS, currency
from pmr.pipeline import generate

OLD = "Cascadia Public Employees' Retirement System"
NEW = "Example Workers Retirement System"
CODE = "EWRS"
REMOVED = "Tidewater Distressed Realty Fund"
ADDED = ["Juniper Property Fund VII", "Ashford Logistics Fund I"]


def transform(text):
    text = re.sub(r"Cascadia\s+Public\s+Employees'\s+Retirement\s+System", NEW, text)
    return text.replace("CPERS", CODE).replace("Fourth Quarter 2025", "First Quarter 2026")


def make_pdf(path, pages):
    style = ParagraphStyle("Fixture", fontName="Helvetica", fontSize=8, leading=10)
    story = []
    for i, text in enumerate(pages):
        if i: story.append(PageBreak())
        for line in text.splitlines():
            if line.strip(): story.append(Paragraph(html.escape(line.strip()), style))
    SimpleDocTemplate(str(path), invariant=1).build(story)


def build_fixture(source, destination):
    shutil.copytree(source, destination)
    flash = destination / "flash_4Q25.xlsx"
    book = openpyxl.load_workbook(flash)
    removed_values = {}
    for name in ["FundingStatus(Agg)", "CashActivity(Agg)", "ReturnsMultiples(Agg)"]:
        ws = book[name]
        sheet = Sheet(flash, ws, Ledger())
        start, headers = sheet.headers(grouped=name.startswith("Returns"))
        removed = next(r for r in ws if r[0].value == REMOVED)
        values = [c.value for c in removed]
        if name.startswith("Funding"):
            removed_values["nav"] = currency(values[headers[norm("Market Value ($)")]])
        # Subtract only additive money columns from affected aggregates.
        for row in ws:
            if row[0].row > start and norm(row[0].value) in {norm("Tactical Investments"), norm("Vectera Initiated Investments"),
                                     norm(OLD + " Portfolio"), norm("US Portfolio")}:
                for header, column in headers.items():
                    if header in MONEY_HEADERS and isinstance(row[column].value, (int, float)):
                        # Synthetic auxiliary totals can carry Excel serialization dust;
                        # materialize newly authored fixture totals at currency precision.
                        original = Decimal(str(row[column].value)).quantize(Decimal("0.01"))
                        row[column].value = float(original - currency(values[column] or 0))
        index = removed[0].row
        ws.delete_rows(index)
        for offset, label in enumerate(ADDED):
            ws.insert_rows(index + offset)
            for column, value in enumerate(values, 1):
                ws.cell(index + offset, column, label if column == 1 else 0 if isinstance(value, (int, float)) else value)
        # An extra empty row shifts every downstream label without changing meaning.
        ws.insert_rows(1, 3)
    funding = book["FundingStatus(Agg)"]
    portfolio = next(r for r in funding if r[0].value == "Vectera Initiated Investments")
    nav = currency(portfolio[6].value)
    schedule_start = next(r[0].row for r in funding if r[0].value == "Investment")
    for row in funding:
        if row[0].row > schedule_start and isinstance(row[6].value, (int, float)) and isinstance(row[7].value, (int, float)) and row[0].value:
            row[7].value = float(currency(row[6].value) / nav * 100)
    for ws in book:
        for row in ws:
            for cell in row:
                if isinstance(cell.value, str):
                    cell.value = cell.value.replace(OLD, NEW).replace("CPERS", CODE).replace("Fourth Quarter 2025", "First Quarter 2026")
    book.save(flash)
    flash.rename(destination / "renamed_current_data.xlsx")
    # Supplied rendered sources are automatically re-read and rendered, not hand-transcribed.
    for path in list(destination.rglob("*.pdf")):
        pages = pdf_pages(path)
        if path.name == "prior_pmr_3Q25.pdf":
            pages = [transform(t).replace("Third Quarter 2025", "Fourth Quarter 2025") for t in pages]
            pages.append("Prior approved, not funded commitments: Northgate Logistics Partners; Ridgeline Value Fund IV.")
            make_pdf(path, pages)
        elif path.name == "prior_pmr_2Q25.pdf":
            continue
        elif path.name == "flash_4Q25.pdf":
            # Rebuild the exhibit from the mutated workbook, rather than attaching
            # the old period's holdings under a renamed title.
            make_pdf(path, ["\n".join([NEW, "First Quarter 2026", ws.title] +
                          [" | ".join(str(c.value) if c.value is not None else "" for c in row) for row in ws if any(c.value is not None for c in row)])
                          for ws in book])
        else:
            make_pdf(path, [transform(t) for t in pages])
    history_path = destination / "allocation_history.xlsx"
    history = openpyxl.load_workbook(history_path)
    history.active.append(["1Q26", 496, int(nav / 1_000_000 + Decimal("0.5"))])
    history.save(history_path)
    log_path = destination / "ic_log_2025.xlsx"
    log = openpyxl.load_workbook(log_path)
    for row in log.active:
        for cell in row:
            if isinstance(cell.value, str): cell.value = cell.value.replace("CPERS", CODE)
    log.save(log_path)
    new_log = openpyxl.Workbook(); ws = new_log.active; ws.title = "Log "
    ws.append([c.value for c in log.active[1]])
    ws.append(["NEW-1", datetime(2026, 2, 3), "IC", "Commitment", NEW,
               "Northgate Logistics Partners", "Withdraw USD40 million; investor withdrew", None, None, "Withdrawn"])
    ws.append(["NEW-2", datetime(2026, 1, 6), "IC", "Due Diligence", CODE,
               "Example Due Diligence Fund", "Explore investment", None, None, "Deferred"])
    new_log.save(destination / "ic_log_2026.xlsx")
    deck_path = destination / "market_outlook_4Q25.pptx"
    with zipfile.ZipFile(deck_path) as original:
        files = {n: original.read(n) for n in original.namelist()}
    with zipfile.ZipFile(deck_path, "w", zipfile.ZIP_DEFLATED) as output:
        for name, content in files.items():
            if name.startswith("ppt/slides/") and name.endswith(".xml"):
                content = content.decode().replace("Fourth Quarter 2025", "First Quarter 2026").replace("4Q25", "1Q26").encode()
            output.writestr(name, content)
    deck_path.rename(destination / "unfamiliar_outlook.pptx")
    return dict(client=CODE, quarter="1Q26", funded_count=13, removed=REMOVED, added=ADDED,
                nav=str(nav), open_names=["Ridgeline Value Fund IV"], new_count=0)


def rehearse(source, record):
    import os
    # This rehearsal deliberately tests deterministic behavior, not live vision accuracy.
    for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]: os.environ.pop(key, None)
    with tempfile.TemporaryDirectory(prefix="pmr-unseen-") as folder:
        root = Path(folder)
        expected = build_fixture(source, root / "inputs")
        payload, summary = generate(root / "inputs", root / "output", expected["client"], expected["quarter"])
        data = payload["data"]
        observed = dict(funded_count=len(data["funds"]), nav=str(data["portfolio"]["nav"]),
                        open_names=[e["name"] for e in data["activity"]["open"]], new_count=len(data["activity"]["new"]),
                        sections=len(payload["sections"]), checks_passed=summary["checks_passed"], checks_total=summary["checks_total"])
        passed = all(observed[k] == expected[k] for k in ["funded_count", "nav", "open_names", "new_count"])
        passed &= observed["sections"] == 14 and observed["checks_passed"] == observed["checks_total"]
        result = dict(passed=passed, mode="no-key full pipeline; not vision accuracy or Windows validation",
                      expected=expected, observed=observed, issues=summary["issues"])
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=Path("inputs"))
    parser.add_argument("--record", type=Path, default=Path("output/unseen_rehearsal.json"))
    args = parser.parse_args()
    result = rehearse(args.inputs, args.record)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
