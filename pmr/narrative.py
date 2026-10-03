"""Extract source passages, resolve entities conservatively, and retain evidence."""
from __future__ import annotations

import posixpath
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from decimal import Decimal

from .ingest import entity, norm, Sheet, quarter
from .charts import CHART_PROMPT, validate_chart

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def section(text, heading, endings):
    match = re.search(re.escape(heading) + r"\s+(.*?)(?=" + "|".join(re.escape(e) for e in endings) + r"|$)", text, re.S)
    return clean(match[1]) if match else ""


def supporting_documents(sources, financials, activity, ledger, model):
    targets = list(dict.fromkeys([f["name"] for f in financials["funds"]] + [e["name"] for e in activity["new"]]))
    support = {}
    for path, pages in sources["managers"]:
        text = "\n".join(pages)
        normalized_lines = [entity(line) for line in text.splitlines() if line.strip()]
        matches = [name for name in targets if entity(name) in normalized_lines]
        if len(matches) != 1:
            if matches:
                ledger.issue("ambiguous_entity", f"Multiple possible funds in {path.name}: {matches}", "blocker")
            ledger.matches.append(dict(file=path.name, candidates=matches, rule="normalized complete source line", accepted=False))
            continue
        name = matches[0]
        ledger.matches.append(dict(file=path.name, canonical=name, rule="punctuation/legal suffix/Roman numeral normalization", accepted=True))
        if name in support:
            ledger.issue("duplicate_manager", f"Multiple manager sources for {name}", "blocker")
            continue
        passages = []
        for page_no, page in enumerate(pages, 1):
            for heading, endings in [
                ("Investments Impacting Performance", ["Outlook", "Selected Portfolio Statistics"]),
                ("Fund Strategy", ["Investment Pipeline", "Terms", "Fund Terms"]),
                ("Status", ["Track Record", "Selected Portfolio Statistics"])]:
                if heading == "Status" and "Final Wind-Down Update" not in page:
                    continue
                excerpt = section(page, heading, endings)
                if excerpt:
                    if heading == "Fund Strategy":
                        excerpt = " ".join(re.split(r"(?<=[.!?])\s+(?=[A-Z])", excerpt)[:2])
                    # Extractive model selection provides automatic source verification, not an opaque entailment guess.
                    # Stable source excerpts fix the report's numeric inventory independently
                    # of agent focus choices. The agent investigates these registered passages.
                    selected = excerpt
                    fid = ledger.add(selected, {"file": str(path.relative_to(sources["root"])), "page": page_no,
                                                "quote": excerpt, "method": "heading-delimited extraction"})
                    if selected not in clean(page):
                        raise ValueError(f"Source excerpt failed page verification: {path.name}/{page_no}")
                    passages.append(dict(text=selected, id=fid, entity=name, heading=heading,
                                         source=ledger.facts[fid]["source"]))
        support[name] = passages
    for fund in financials["funds"]:
        if fund["roles"] and fund["name"] not in support:
            ledger.issue("missing_manager", f"No current manager report for ranked fund {fund['name']}; flash-only commentary", fund=fund["name"])
    for event in activity["new"]:
        if not support.get(event["name"]):
            ledger.issue("missing_strategy", f"No strategy evidence for new commitment {event['name']}", "blocker")
    return support


def deck_evidence(path, output, ledger, model):
    if path is None:
        return [], []
    slides, charts = [], []
    assets = output / "assets"
    assets.mkdir(exist_ok=True)
    with zipfile.ZipFile(path) as archive:
        names = sorted((n for n in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                       key=lambda n: int(re.search(r"slide(\d+)", n)[1]))
        for name in names:
            number = int(re.search(r"slide(\d+)", name)[1])
            root = ET.fromstring(archive.read(name))
            texts = [clean(t.text or "") for t in root.findall(".//a:t", NS) if t.text]
            if texts:
                fid = ledger.add(texts, {"file": path.name, "slide": number})
                slides.append(dict(number=number, title=texts[0], text=texts[1:], id=fid))
            rel_name = posixpath.join(posixpath.dirname(name), "_rels", posixpath.basename(name) + ".rels")
            if rel_name not in archive.namelist():
                continue
            rels = {r.attrib["Id"]: r.attrib["Target"] for r in ET.fromstring(archive.read(rel_name))}
            for chart_number, image in enumerate(root.findall(".//p:pic", NS), 1):
                blip = image.find(".//a:blip", NS)
                if blip is None:
                    continue
                target = rels[blip.attrib["{" + NS["r"] + "}embed"]]
                image_path = posixpath.normpath(posixpath.join(posixpath.dirname(name), target))
                data = archive.read(image_path)
                asset = f"slide_{number}_chart_{chart_number}.png"
                (assets / asset).write_bytes(data)
                result = model.ask(CHART_PROMPT, data)
                if result is not None:
                    try:
                        result = validate_chart(result)
                    except ValueError as error:
                        ledger.issue("invalid_chart_schema", f"Slide {number}, chart {chart_number}: {error}", "blocker")
                        result = None
                fid = ledger.add(result, {"file": path.name, "slide": number, "chart": chart_number,
                                          "asset": "assets/" + asset, "method": "model vision", "requires_review": True})
                charts.append(dict(slide=number, chart=chart_number, asset="assets/" + asset, id=fid, data=result))
                if result is None:
                    ledger.issue("chart_unavailable", f"Slide {number}, chart {chart_number}: image values unavailable without successful model access", "blocker", fact_id=fid)
                else:
                    ledger.issue("chart_review", f"Confirm image-extracted values on slide {number}, chart {chart_number}", "review", fact_id=fid)
    return slides, charts


def allocation_history(source, requested, ledger):
    if not source:
        return []
    path, ws = source
    sheet = Sheet(path, ws, ledger)
    start, headers = sheet.headers("Quarter")
    target = next(v for k, v in headers.items() if k.startswith("target allocation"))
    nav = next(v for k, v in headers.items() if k.startswith("net asset value"))
    result = []
    for row in sheet.rows():
        period = quarter(row[0].value)
        if row[0].row > start and period and period <= requested:
            target_value, target_id = sheet.number(row[target], metric="target allocation", unit="USD million")
            nav_value, nav_id = sheet.number(row[nav], metric="net asset value", unit="USD million")
            result.append(dict(quarter=str(row[0].value), target=target_value, nav=nav_value,
                               target_precision=max(0, -Decimal(str(row[target].value)).as_tuple().exponent),
                               nav_precision=max(0, -Decimal(str(row[nav].value)).as_tuple().exponent),
                               quarter_id=sheet.fact(row[0]), target_id=target_id, nav_id=nav_id))
    return sorted(result, key=lambda x: quarter(x["quarter"]))
