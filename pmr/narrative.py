"""Extract source passages, resolve entities conservatively, and retain evidence."""

from __future__ import annotations

import posixpath
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from decimal import Decimal
from difflib import SequenceMatcher

from .ingest import entity, norm, Sheet, quarter
from .charts import CHART_PROMPT, validate_chart

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


# Manager documents put a short heading above each prose paragraph. Sections are chosen by
# what the heading is about, so a renamed heading still works; the order sets preference.
SECTION_PREFERENCE = [
    ("drivers", r"impact|driver|asset|attribution"),
    ("strategy", r"strategy|overview"),
    ("status", r"status|wind.?down"),
]
NOT_NARRATIVE = r"outlook|term|pipeline|statistic|confidential|metric"


def is_heading(line):
    """A short Title Case line without digits or a closing period, e.g. 'Investments Impacting Performance'.

    Wrapped prose lines contain lowercase words; subtitles and table rows contain digits.
    """
    words = re.findall(r"[A-Za-z][\w'-]*", line)
    return (
        0 < len(line.split()) <= 8
        and not re.search(r"\d|[.!?]$", line)
        and all(w[0].isupper() for w in words if len(w) > 3)
    )


def prose_sections(pages):
    """(page, heading, paragraph) for each heading line followed by prose.

    Works on text lines, not PDF blocks, because PDF generators split paragraphs differently.
    """
    sections = []
    for page_no, page in enumerate(pages, 1):
        lines = [line.strip() for line in page.splitlines() if line.strip()]
        starts = [i for i, line in enumerate(lines) if is_heading(line)]
        for i, j in zip(starts, starts[1:] + [len(lines)]):
            # Footers ("Confidential ...") must not lend a table its only full sentence.
            body = clean(
                " ".join(line for line in lines[i + 1 : j] if not re.match(NOT_NARRATIVE, line, re.I))
            )
            if len(body) >= 60 and re.search(r"[a-z]\.(\s|$)", body):
                sections.append((page_no, clean(lines[i]), body))
    return sections


def choose_sections(sections):
    for rule, pattern in SECTION_PREFERENCE:
        chosen = [s for s in sections if re.search(pattern, s[1], re.I)]
        if chosen:
            return chosen, rule
    return [s for s in sections if not re.search(NOT_NARRATIVE, s[1], re.I)], "fallback"


def supporting_documents(sources, financials, activity, ledger, model):
    targets = list(
        dict.fromkeys([f["name"] for f in financials["funds"]] + [e["name"] for e in activity["new"]])
    )
    support = {}
    financials["unmatched_reports"] = []
    for path, pages in sources["managers"]:
        text = "\n".join(pages)
        normalized_lines = [entity(line) for line in text.splitlines() if line.strip()]
        matches = [name for name in targets if entity(name) in normalized_lines]
        if len(matches) != 1:
            if matches:
                ledger.issue(
                    "ambiguous_entity", f"Multiple possible funds in {path.name}: {matches}", "blocker"
                )
            ledger.matches.append(
                dict(
                    file=path.name, candidates=matches, rule="normalized complete source line", accepted=False
                )
            )
            suggestions = sorted(
                targets,
                key=lambda name: -max(
                    (SequenceMatcher(None, entity(name), line).ratio() for line in normalized_lines),
                    default=0,
                ),
            )[:3]
            financials["unmatched_reports"].append(dict(file=path.name, suggestions=suggestions))
            ledger.issue(
                "unmatched_manager",
                f"Unresolved supporting document {path.name}; possible funds: {', '.join(suggestions)}. Suggestions are not accepted matches.",
                candidates=suggestions,
            )
            continue
        name = matches[0]
        ledger.matches.append(
            dict(
                file=path.name,
                canonical=name,
                rule="complete-line match after legal suffix, word/Roman/Arabic vintage, ampersand and explicit abbreviation normalization",
                accepted=True,
            )
        )
        if name in support:
            ledger.issue("duplicate_manager", f"Multiple manager sources for {name}", "blocker")
            continue
        sections = prose_sections(pages)
        chosen, rule = choose_sections(sections)
        if rule == "fallback":
            ledger.issue(
                "manager_extraction",
                f"{path.name}: no performance, strategy or status heading recognised; using all prose sections "
                f"({', '.join(h for _, h, _ in chosen) or 'none'}) for review",
                fund=name,
            )
        passages = []
        for page_no, heading, text in chosen:
            if rule == "strategy":
                # SPEC 1.6 asks for a one-to-two sentence strategy description.
                text = " ".join(re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)[:2])
            if text not in clean(pages[page_no - 1]):
                ledger.issue(
                    "manager_extraction", f"{path.name} p{page_no}: excerpt failed page verification"
                )
                continue
            source = {
                "file": str(path.relative_to(sources["root"])),
                "page": page_no,
                "quote": text,
                "method": f"prose section under heading '{heading}'",
            }
            fid = ledger.add(text, source)
            passages.append(
                dict(text=text, id=fid, entity=name, heading=heading, source=ledger.facts[fid]["source"])
            )
        support[name] = passages
    for fund in financials["funds"]:
        if fund["fees"] < 0:
            ledger.issue(
                "negative_fees",
                f"{fund['name']} has negative manager fees in the flash; shown as a fee credit, not normalized",
                evidence=[fund["fees_id"]],
            )
        if fund["roles"] and fund["name"] not in support:
            ledger.issue(
                "missing_manager",
                f"No matched current manager evidence for ranked fund {fund['name']}; flash-only commentary",
                fund=fund["name"],
            )
    for event in activity["new"]:
        if not support.get(event["name"]):
            ledger.issue(
                "missing_strategy", f"No strategy evidence for new commitment {event['name']}", "blocker"
            )
    return support


def deck_evidence(path, output, ledger, model):
    if path is None:
        return [], []
    slides, charts = [], []
    assets = output / "assets"
    assets.mkdir(exist_ok=True)
    with zipfile.ZipFile(path) as archive:
        names = sorted(
            (n for n in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
            key=lambda n: int(re.search(r"slide(\d+)", n)[1]),
        )
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
                        repaired = model.ask(
                            CHART_PROMPT
                            + "\nYour extraction failed validation: "
                            + str(error)
                            + ". Re-read the image, including axis bounds and all points. Do not clamp values to pass validation.",
                            data,
                        )
                        try:
                            result = validate_chart(repaired)
                            ledger.issue(
                                "chart_repaired",
                                f"Slide {number}, chart {chart_number}: extraction corrected after schema validation; confirm against image",
                            )
                        except ValueError:
                            ledger.issue(
                                "invalid_chart_schema",
                                f"Slide {number}, chart {chart_number}: {error}",
                                "blocker",
                            )
                            result = None
                fid = ledger.add(
                    result,
                    {
                        "file": path.name,
                        "slide": number,
                        "chart": chart_number,
                        "asset": "assets/" + asset,
                        "method": "model vision",
                        "requires_review": True,
                    },
                )
                charts.append(
                    dict(slide=number, chart=chart_number, asset="assets/" + asset, id=fid, data=result)
                )
                if result is None:
                    ledger.issue(
                        "chart_unavailable",
                        f"Slide {number}, chart {chart_number}: image values unavailable without successful model access",
                        "blocker",
                        fact_id=fid,
                    )
                else:
                    ledger.issue(
                        "chart_review",
                        f"Confirm image-extracted values on slide {number}, chart {chart_number}",
                        "review",
                        fact_id=fid,
                    )
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
            target_value, target_id = sheet.number(
                row[target], metric="target allocation", unit="USD million"
            )
            nav_value, nav_id = sheet.number(row[nav], metric="net asset value", unit="USD million")
            result.append(
                dict(
                    quarter=str(row[0].value),
                    target=target_value,
                    nav=nav_value,
                    target_precision=max(0, -Decimal(str(row[target].value)).as_tuple().exponent),
                    nav_precision=max(0, -Decimal(str(row[nav].value)).as_tuple().exponent),
                    quarter_id=sheet.fact(row[0]),
                    target_id=target_id,
                    nav_id=nav_id,
                )
            )
    return sorted(result, key=lambda x: quarter(x["quarter"]))
