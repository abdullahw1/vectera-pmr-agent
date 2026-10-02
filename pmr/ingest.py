"""Content-based discovery and label-based parsers; never fixed workbook cells."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import fitz
import openpyxl


QUARTER_WORDS = {"first": 1, "second": 2, "third": 3, "fourth": 4}
ROMANS = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6"}


def norm(text):
    text = str(text or "").lower().replace("%", " percent ").replace("$", " dollars ")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def entity(text):
    text = re.sub(r"\bU\.\s*S\.", "US", str(text), flags=re.I)
    tokens = norm(text).split()
    if tokens[-2:] == ["l", "p"]:
        tokens = tokens[:-2]
    while tokens and tokens[-1] in {"llc", "lp", "limited"}:
        tokens.pop()
    return " ".join(ROMANS.get(t, t) for t in tokens)


def quarter(text):
    match = re.search(r"\b(First|Second|Third|Fourth) Quarter\s+(\d{4})", str(text), re.I)
    if match:
        return int(match[2]), QUARTER_WORDS[match[1].lower()]
    match = re.search(r"\b([1-4])\s*Q\s*(\d{2}|\d{4})\b", str(text), re.I)
    if match:
        year = int(match[2]); return (year + 2000 if year < 100 else year, int(match[1]))
    return None


def bounds(q):
    year, number = q
    start = date(year, 3 * number - 2, 1)
    end = date(year + 1, 1, 1) if number == 4 else date(year, 3 * number + 1, 1)
    return start, end


def pdf_pages(path):
    with fitz.open(path) as doc:
        return [page.get_text(sort=True) for page in doc]


class Sheet:
    def __init__(self, path, worksheet, ledger):
        self.path, self.ws, self.ledger = path, worksheet, ledger

    def rows(self):
        return list(self.ws.iter_rows())

    def find(self, label, *, numeric=False):
        matches = [r for r in self.rows() if norm(r[0].value) == norm(label)
                   and (not numeric or any(isinstance(c.value, (int, float)) for c in r[1:]))]
        if len(matches) != 1:
            raise ValueError(f"{self.path.name}/{self.ws.title}: {label!r} matched {len(matches)} rows")
        return matches[0]

    def fact(self, cell):
        return self.ledger.add(cell.value, {"file": self.path.name, "sheet": self.ws.title, "cell": cell.coordinate})

    def number(self, cell, *, blank_zero=False):
        if cell.value is None and blank_zero:
            return 0.0, self.ledger.add(0, {"file": self.path.name, "sheet": self.ws.title,
                                        "cell": cell.coordinate, "interpretation": "blank capital flow = zero"})
        if not isinstance(cell.value, (int, float)):
            raise ValueError(f"Expected number at {self.path.name}/{self.ws.title}/{cell.coordinate}")
        return float(cell.value), self.fact(cell)

    def headers(self, marker="Investment", grouped=False):
        row = next((r for r in self.rows() if norm(r[0].value) == norm(marker)), None)
        if row is None:
            raise ValueError(f"Header {marker!r} missing in {self.ws.title}")
        result, group = {}, ""
        lower = list(self.ws.iter_rows(min_row=row[0].row + 1, max_row=row[0].row + 1))[0]
        for i, c in enumerate(row):
            if c.value is not None:
                group = str(c.value)
            key = norm(group + " " + str(lower[i].value or "")) if grouped and i else norm(c.value)
            if key:
                result[key] = i
        return row[0].row, result


def discover(root, client, requested, ledger):
    candidates = []
    for path in sorted(root.rglob("*.xlsx")):
        book = openpyxl.load_workbook(path, data_only=True)
        if "FundingStatus(Agg)" not in book.sheetnames:
            continue
        text = "\n".join(str(c.value) for row in book["FundingStatus(Agg)"] for c in row if isinstance(c.value, str))
        labels = [str(c.value) for ws in book for row in ws for c in row
                  if isinstance(c.value, str) and "benchmark" in c.value.lower()]
        # The short code is present in the benchmark label; content outranks filenames.
        belongs = any(re.search(r"\b" + re.escape(client) + r"\b", label, re.I) for label in labels)
        if belongs and quarter(text) == requested:
            candidates.append((path, book))
    if len(candidates) != 1:
        raise ValueError(f"Expected one populated flash for {client}/{requested}, found {len(candidates)}")
    flash, book = candidates[0]
    ws = book["FundingStatus(Agg)"]
    # The workbook contract places its identity above the first labelled data section.
    identity = next(c for row in ws for c in row if isinstance(c.value, str)
                    and not quarter(c.value) and c.value.strip())
    name = re.sub(r"\s+Portfolio$", "", identity.value)
    name_id = Sheet(flash, ws, ledger).fact(identity)
    prior, managers, appendix, logs, history, deck = [], [], [], [], [], []
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() == ".pdf":
            pages = pdf_pages(path); text = "\n".join(pages); period = quarter(text)
            belongs = norm(name) in norm(text)
            if "Performance Measurement Report" in text and belongs:
                if period and period < requested:
                    prior.append((period, path, pages))
            elif period == requested:
                if "Portfolio Composition" in text and belongs:
                    appendix.append(path)
                else:
                    managers.append((path, pages))
        elif path.suffix.lower() == ".xlsx" and path != flash:
            other = openpyxl.load_workbook(path, data_only=True)
            for sheet in other:
                strings = {norm(c.value) for row in sheet for c in row if isinstance(c.value, str)}
                if {"meeting date", "committee action", "client"} <= strings:
                    logs.append((path, sheet))
                if any("target allocation" in v for v in strings) and any("net asset value" in v for v in strings):
                    history.append((path, sheet))
        elif path.suffix.lower() == ".pptx":
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(path) as archive:
                text = " ".join(" ".join(ET.fromstring(archive.read(n)).itertext()) for n in archive.namelist()
                                if re.fullmatch(r"ppt/slides/slide\d+\.xml", n))
            if quarter(text) == requested:
                deck.append(path)
    if not prior:
        raise ValueError("No prior client PMR found; policy and format cannot be established")
    if not logs:
        ledger.issue("ic_log_missing", "No investment committee log found; approval totals cannot be finalized", "blocker")
    prior.sort(key=lambda item: item[0], reverse=True)
    if len(deck) != 1 or len(history) != 1 or len(appendix) != 1:
        ledger.issue("source_discovery", "Market deck, history or flash appendix is missing or ambiguous", "blocker")
    return dict(flash=flash, book=book, name=name, name_id=name_id, prior=prior[0], managers=managers,
                appendix=appendix[0] if len(appendix) == 1 else None, logs=logs,
                history=history[0] if len(history) == 1 else None, deck=deck[0] if len(deck) == 1 else None)
