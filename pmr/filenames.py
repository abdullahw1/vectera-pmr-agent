"""Client-facing PDF names, separate from stable internal review paths."""

import json
from pathlib import Path
import re

from .ingest import quarter


def report_filename(client, period, *, approved=False):
    client = re.sub(r"[^A-Za-z0-9_-]+", "_", client.strip()).strip("_-")
    requested = quarter(period)
    if not client or not requested:
        raise ValueError("Report filename requires a client and valid quarter")
    year, number = requested
    suffix = "" if approved else "_DRAFT"
    return f"{client.upper()}_PMR_{number}Q{year % 100:02d}{suffix}.pdf"


def clear_named_reports(output):
    draft = Path(output) / "draft.json"
    if not draft.exists():
        return
    data = json.loads(draft.read_text(encoding="utf-8"))["data"]
    for approved in (False, True):
        name = report_filename(data["client"], data["quarter"], approved=approved)
        (Path(output) / name).unlink(missing_ok=True)


def export_report(output, data, *, approved=False):
    name = report_filename(data["client"], data["quarter"], approved=approved)
    source = Path(output) / ("final_report.pdf" if approved else "report.pdf")
    (Path(output) / name).write_bytes(source.read_bytes())
    return name
