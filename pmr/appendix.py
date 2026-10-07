"""Retypeset parsed flash exhibits, preserving displayed values and blank cells."""

import html
import io
import statistics
import re
from decimal import Decimal

import fitz
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.platypus import HRFlowable

NAVY = colors.HexColor("#1b2a4a")
HEADER_ALIASES = {
    "Commitment Am": "Commitment ($)",
    "Unfunded Comm": "Unfunded ($)",
    "Beginning Marke": "Beginning value ($)",
    "tContributions": "Capital in ($)",
    "Distributions": "Distrib. ($)",
    "Withdrawals": "Withdraw. ($)",
    "Appreciation": "Apprec. ($)",
    "Gross Income": "Income ($)",
    "Manager Fees": "Fees ($)",
    "East North Centr": "E. North Central",
    "aWest North Cent": "W. North Central",
    "Northeast": "NE",
    "Southeast": "SE",
    "Southwest": "SW",
    "Various-US": "Various US",
}


def presentation_header(header):
    """Expand source abbreviations without changing their metric or horizon."""
    header = HEADER_ALIASES.get(header, header)
    names = {
        "Commitment ($)": "Commitment", "Funded Amount": "Funded", "Unfunded ($)": "Unfunded",
        "Capital Returned": "Returned", "Market Value ($)": "Market Value", "Market Value (%)": "% NAV",
        "Beginning value ($)": "Beginning MV", "Capital in ($)": "Contrib.", "Distrib. ($)": "Distrib.",
        "Withdraw. ($)": "Withdrawals", "Income ($)": "Income", "Fees ($)": "Fees", "Apprec. ($)": "Apprec.",
        "NET IRR": "Net IRR", "TWR Calculation": "TWR Inception",
    }
    header = names.get(header, header)
    header = re.sub(r"\s*\(%\)", "", header)
    header = re.sub(r"\bTGRS\b", "GRS", header)
    header = re.sub(r"\bTNET\b", "NET", header)
    header = re.sub(r"\b(\d+) Year(?:\(s\))?", r"\1 Yr", header)
    return header


def display_cell(exhibit, column, value):
    """Unit decoration only; retain original PDF precision and blank cells."""
    if not value:
        return ""
    header = exhibit["headers"][column]
    monetary = header in {
        "Total Plan Assets", "Target Allocation", "Market Value", "Unfunded", "Remaining",
        "Commitment", "Funded", "Returned", "Beginning MV", "Contrib.", "Distrib.",
        "Withdrawals", "Income", "Fees", "Apprec.",
    }
    if header == "Allocation / plan":
        percent = format(Decimal(value.replace(',', '')) * 100, "f")
        if "." in percent:
            percent = percent.rstrip("0").rstrip(".")
        return percent + (".0" if "." not in percent else "") + "%"
    if monetary and re.fullmatch(r"-?\d[\d,]*(?:\.\d+)?", value):
        amount = Decimal(value.replace(",", ""))
        return f"(${abs(amount):,f})" if amount < 0 else f"${amount:,f}"
    return value


class UnsupportedExhibitLayout(ValueError):
    """Retain an unfamiliar source layout instead of guessing column boundaries."""


def append_original_pages(result, source, approved):
    with fitz.open(source) as document:
        for index, original in enumerate(document):
            spans = [
                span
                for block in original.get_text("dict")["blocks"]
                for line in block.get("lines", [])
                for span in line["spans"]
                if span["text"].strip()
            ]
            if not spans:
                raise ValueError(
                    "Unrecognized flash layout has no readable text; manual source review required"
                )
            bounds = fitz.Rect(spans[0]["bbox"])
            for span in spans[1:]:
                bounds |= fitz.Rect(span["bbox"])
            bounds = (bounds + (-8, -8, 8, 8)) & original.rect
            scale = min(540 / bounds.width, 674 / bounds.height, 1)
            if statistics.median(s["size"] for s in spans) * scale < 7:
                raise ValueError(
                    "Unrecognized flash layout cannot fit portrait paper readably; a reviewed layout adapter is required"
                )
            page = result.new_page(width=612, height=792)
            page.insert_text(
                (36, 32), f"Appendix A | Flash source page {index + 1} (original layout)", fontsize=9
            )
            page.show_pdf_page(
                fitz.Rect(36, 55, 36 + bounds.width * scale, 55 + bounds.height * scale),
                document,
                index,
                clip=bounds,
            )
            page.insert_text(
                (36, 767), f"Page {len(result)}" + (" | DRAFT" if not approved else ""), fontsize=7
            )


def clean_rows(rows):
    # Empty spreadsheet padding and section-only labels are not financial rows.
    return [
        [str(value or "") for value in row]
        for row in rows
        if any(value not in {None, ""} for value in row[1:])
    ]


def flatten_headers(top, lower):
    headers, group = [], ""
    for title, metric in zip(top, lower):
        if title:
            group = title
        headers.append((group + " " + metric).strip() if metric else str(title or ""))
    return headers


def extract_exhibits(source, *, compact=True):
    """Return projections with original row/column locators; no money conversion."""
    exhibits = []
    with fitz.open(source) as document:
        for page_number, page in enumerate(document, 1):
            tables = page.find_tables().tables
            if len(tables) != 1:
                raise UnsupportedExhibitLayout(
                    "Flash appendix requires one identifiable source table per page"
                )
            rows = tables[0].extract()
            starts = [
                i
                for i, row in enumerate(rows)
                if row[0]
                and (
                    row[0] in {"Investment", "Performance Summary", "Portfolio Composition ($)"}
                    or "Diversification (%)" in row[0]
                )
            ]
            if not starts:
                raise UnsupportedExhibitLayout("Flash appendix table headers could not be identified")
            for position, start in enumerate(starts):
                end = starts[position + 1] if position + 1 < len(starts) else len(rows)
                title = rows[start][0]
                if title == "Portfolio Composition ($)":
                    # These are the source's paired dollars/ratio columns, not inferred values.
                    headers = [
                        "Total Plan Assets",
                        "Target Allocation",
                        "Allocation / plan",
                        "Market Value",
                        "NAV / plan",
                        "Unfunded",
                        "Unfunded / plan",
                        "Remaining",
                    ]
                    data_start = start + 2
                else:
                    headers = rows[start]
                    data_start = start + 1
                grouped = (
                    data_start < end
                    and not rows[data_start][0]
                    and any(
                        str(v or "").upper() in {"INC", "APP", "GRS", "NET", "TGRS", "TNET"}
                        for v in rows[data_start]
                    )
                )
                if grouped:
                    headers = flatten_headers(headers, rows[data_start])
                    data_start += 1
                headers = [HEADER_ALIASES.get(h, h) for h in headers]
                if title == "Investment" and "Vintage" in headers:
                    title = "Investment Schedule"
                elif title == "Investment" and "Beginning value ($)" in headers:
                    title = "Quarterly cash activity"
                elif title != "Investment":
                    headers[0] = "Portfolio" if title != "Portfolio Composition ($)" else headers[0]
                data = clean_rows(rows[data_start:end])
                source_rows = [
                    i for i in range(data_start, end) if any(value not in {None, ""} for value in rows[i][1:])
                ]
                if not data:
                    continue
                projections = [(title, list(range(len(headers))))]
                if len(headers) > 11:
                    # Adjacent horizons share a table; scalar metrics remain separate.
                    groups, scalar, group_title = [], [], ""
                    for column in range(1, len(headers)):
                        if rows[start][column]:
                            group_title = rows[start][column]
                        if grouped and rows[start + 1][column]:
                            if not groups or groups[-1][0] != group_title:
                                groups.append((group_title, []))
                            groups[-1][1].append(column)
                        else:
                            scalar.append(column)
                    projections, pending, names = [], [], []
                    for name, columns in groups:
                        if pending and len(pending) + len(columns) > 8:
                            projections.append(("Returns: " + " / ".join(names), [0] + pending))
                            pending, names = [], []
                        pending.extend(columns)
                        names.append(name)
                    if pending:
                        projections.append(("Returns: " + " / ".join(names), [0] + pending))
                    if scalar:
                        projections.append(("Valuation and inception statistics", [0] + scalar))
                fund_returns = any(h in {"NET IRR", "Net Multiple"} for h in headers)
                for name, columns in projections:
                    if name.startswith("Returns:"):
                        name = ("Returns and Multiples (%) - " if fund_returns else "Annualized Time-Weighted Returns (%) - ") + name.removeprefix("Returns: ")
                    elif name == "Valuation and inception statistics":
                        name = "Valuation, IRR and Net Multiples" if fund_returns else "Annual Returns - TWR Inception"
                    elif name == "Performance Summary":
                        name += " (%)"
                    exhibits.append(
                        dict(
                            title=name,
                            source_page=page_number,
                            source_rows=[i + 1 for i in source_rows],
                            source_headers=list(range(start + 1, data_start + 1)),
                            columns=columns,
                            identity=" | ".join(str(v) for row in rows[:2] for v in row if v),
                            headers=[presentation_header(headers[c]) for c in columns],
                            rows=[[row[c] for c in columns] for row in data],
                        )
                    )
                if grouped and not fund_returns and "TWR Calculation" in headers:
                    net_columns = [i for i, header in enumerate(headers) if header.lower().endswith(" net")]
                    if net_columns:
                        # Keep gross-only series in the full exhibit, not an empty net-only row.
                        net_rows = [i for i, row in enumerate(data) if any(row[c] for c in net_columns)]
                        exhibits.append(dict(
                            title="Annualized Net Time-Weighted Return (%)",
                            source_page=page_number,
                            source_rows=[source_rows[i] + 1 for i in net_rows],
                            source_headers=list(range(start + 1, data_start + 1)),
                            columns=[0] + net_columns,
                            identity=" | ".join(str(v) for row in rows[:2] for v in row if v),
                            headers=["Investment"] + [presentation_header(headers[i]).removesuffix(" Net").removesuffix(" NET") for i in net_columns],
                            rows=[[data[i][c] for c in [0] + net_columns] for i in net_rows],
                        ))
    return compact_report_exhibits(exhibits) if compact else exhibits


def compact_report_exhibits(exhibits):
    """Follow the sample's core flash tables; retain full projections in the audit."""
    core = {"Portfolio Composition ($)", "Performance Summary (%)", "Investment Schedule",
            "Quarterly cash activity", "Property Type Diversification (%)",
            "Geographic Diversification (%)", "Annualized Net Time-Weighted Return (%)"}
    valuation = next((e for e in exhibits if e["title"] == "Valuation, IRR and Net Multiples"), None)
    selected, geographic = [], []

    def project(exhibit, indices, row_indices=None):
        indices = list(indices)
        row_indices = list(range(len(exhibit["rows"]))) if row_indices is None else row_indices
        return dict(exhibit, headers=[exhibit["headers"][i] for i in indices],
                    columns=[exhibit["columns"][i] for i in indices],
                    rows=[[exhibit["rows"][r][i] for i in indices] for r in row_indices],
                    source_rows=[exhibit["source_rows"][r] for r in row_indices])

    for exhibit in exhibits:
        title = exhibit["title"]
        quarter = title.startswith("Returns and Multiples") and any(h.startswith("Quarter ") for h in exhibit["headers"])
        if title not in core and not quarter:
            continue
        if title == "Portfolio Composition ($)":
            names = {"Total Plan Assets", "Target Allocation", "Market Value", "Unfunded", "Remaining"}
            exhibit = project(exhibit, [i for i, h in enumerate(exhibit["headers"]) if h in names])
        elif title == "Investment Schedule":
            geographic = [(r, exhibit["source_rows"][i], exhibit) for i, r in enumerate(exhibit["rows"])
                          if r[0] in {"US Portfolio", "Ex-US Portfolio"}]
            keep = [i for i, r in enumerate(exhibit["rows"])
                    if r[0] not in {"US Portfolio", "Ex-US Portfolio"}]
            # Duplicate totals are detected from their financial cells, not a client name.
            total = next((r for r in exhibit["rows"] if r[0] == "Vectera Initiated Investments"), None)
            if total:
                identity = {name for part in exhibit["identity"].split("|")
                            for name in [part.strip(), part.strip() + " Portfolio"]}
                keep = [i for i in keep if exhibit["rows"][i][0] not in identity
                        or exhibit["rows"][i][2:] != total[2:]]
            exhibit = project(exhibit, range(len(exhibit["headers"])), keep)
        elif quarter:
            if "Market Value" not in exhibit["headers"] and valuation and (
                    valuation["source_page"] == exhibit["source_page"]
                    and valuation["source_rows"] == exhibit["source_rows"]):
                nav = valuation["headers"].index("Market Value")
                exhibit = dict(exhibit, headers=exhibit["headers"] + ["Market Value"],
                               columns=exhibit["columns"] + [valuation["columns"][nav]],
                               rows=[r + [v[nav]] for r, v in zip(exhibit["rows"], valuation["rows"])])
            indices = [0] + [i for i, h in enumerate(exhibit["headers"]) if h.startswith("Quarter ")]
            if "Market Value" in exhibit["headers"]:
                indices.append(exhibit["headers"].index("Market Value"))
            exhibit = project(exhibit, indices)
            exhibit["title"] = "Returns and Multiples (%)"
            total = next((r for r in exhibit["rows"] if r[0] == "Vectera Initiated Investments"), None)
            if total:
                identity = {name for part in exhibit["identity"].split("|")
                            for name in [part.strip(), part.strip() + " Portfolio"]}
                exhibit = project(exhibit, range(len(exhibit["headers"])),
                                  [i for i, r in enumerate(exhibit["rows"])
                                   if r[0] not in identity or r[1:] != total[1:]])
        elif title == "Annualized Net Time-Weighted Return (%)":
            exhibit = project(exhibit, [0] + [i for i, h in enumerate(exhibit["headers"])
                                            if h in {"1 Yr", "3 Yr", "5 Yr"}])
        elif title == "Quarterly cash activity":
            total = next((r for r in exhibit["rows"] if r[0] == "Vectera Initiated Investments"), None)
            if total:
                identity = {name for part in exhibit["identity"].split("|")
                            for name in [part.strip(), part.strip() + " Portfolio"]}
                exhibit = project(exhibit, range(len(exhibit["headers"])),
                                  [i for i, r in enumerate(exhibit["rows"])
                                   if r[0] not in identity or r[1:] != total[1:]])
        selected.append(exhibit)
    for exhibit in selected:
        if exhibit["title"] == "Geographic Diversification (%)" and geographic:
            pieces, refs = [], []
            for row, source_row, source in geographic:
                column = source["headers"].index("% NAV")
                pieces.append(f"{row[0]}: {row[column]} of market value")
                refs.append(dict(page=source["source_page"], row=source_row,
                                 column=source["columns"][column] + 1, raw_value=row[column]))
            exhibit["note"] = "Fund-level classification: " + "; ".join(pieces) + ". These are separate from the look-through exposures above."
            exhibit["note_sources"] = refs
    order = ["Portfolio Composition ($)", "Performance Summary (%)", "Investment Schedule",
             "Quarterly cash activity", "Returns and Multiples (%)", "Property Type Diversification (%)",
             "Geographic Diversification (%)", "Annualized Net Time-Weighted Return (%)"]
    return sorted(selected, key=lambda e: order.index(e["title"]))


def register_exhibits(source, ledger):
    """Register the exact exhibits the PDF renderer uses, with original cell locators."""
    try:
        exhibits = extract_exhibits(source)
    except UnsupportedExhibitLayout:
        # The renderer retains unfamiliar readable pages. Keep their text-span evidence too.
        blocks = []
        with fitz.open(source) as document:
            for page_no, page in enumerate(document, 1):
                ids, text = [], []
                for block in page.get_text("dict")["blocks"]:
                    for line in block.get("lines", []):
                        for span in line["spans"]:
                            if span["text"].strip():
                                text.append(span["text"])
                                ids.append(
                                    ledger.add(
                                        span["text"],
                                        {
                                            "file": source.name,
                                            "page": page_no,
                                            "bbox": list(span["bbox"]),
                                            "method": "original PDF text span",
                                        },
                                    )
                                )
                blocks.append(dict(type="paragraph", text=" ".join(text), evidence=ids))
        return blocks
    blocks = []
    with fitz.open(source) as document:
        tables = {page.number + 1: page.find_tables().tables[0] for page in document}
        audit = extract_exhibits(source, compact=False)
        for visible, exhibit in [(False, e) for e in audit] + [(True, e) for e in exhibits]:
            table = tables[exhibit["source_page"]]
            cells = []
            for row_number, row in zip(exhibit["source_rows"], exhibit["rows"]):
                cell_ids = []
                for column, value in zip(exhibit["columns"], row):
                    locator = dict(
                        file=source.name,
                        page=exhibit["source_page"],
                        table=1,
                        row=row_number,
                        column=column + 1,
                        raw_value=value,
                    )
                    bbox = table.rows[row_number - 1].cells[column]
                    if bbox:
                        locator["bbox"] = list(bbox)
                    displayed = display_cell(exhibit, len(cell_ids), value)
                    cell_ids.append([ledger.add(displayed, locator, formula="source PDF value with displayed unit decoration", inputs=[])])
                cells.append(cell_ids)
            if not visible:
                continue
            blocks.append(
                dict(
                    type="table",
                    title=exhibit["title"],
                    columns=exhibit["headers"],
                    rows=[[display_cell(exhibit, column, value) for column, value in enumerate(row)] for row in exhibit["rows"]],
                    cell_evidence=cells,
                    evidence=list(dict.fromkeys(i for row in cells for cell in row for i in cell)),
                )
            )
            if exhibit.get("note"):
                ids = [ledger.add(ref["raw_value"], dict(file=source.name, **ref))
                       for ref in exhibit.get("note_sources", [])]
                if not ids:
                    ids = [ledger.add(exhibit["note"], dict(
                        file=source.name, page=exhibit["source_page"], method="parsed exhibit presentation summary"))]
                blocks.append(dict(type="paragraph", text=exhibit["note"], evidence=ids))
    return blocks


def append_exhibits(result, source, approved=False):
    try:
        exhibits = extract_exhibits(source)
    except UnsupportedExhibitLayout:
        append_original_pages(result, source, approved)
        return
    body = ParagraphStyle("AppendixCell", fontName="Helvetica", fontSize=6.8, leading=8.2)
    heading = ParagraphStyle(
        "AppendixHeading",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=NAVY,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True,
    )
    caption = ParagraphStyle(
        "AppendixCaption", fontName="Helvetica", fontSize=7.2, leading=10, spaceAfter=4, keepWithNext=True
    )
    omission_note = ParagraphStyle("AppendixOmissionNote", parent=caption, keepWithNext=False)
    section_heading = ParagraphStyle("AppendixSection", parent=heading, fontSize=15, leading=18, spaceBefore=0)
    story = [
        Paragraph("Appendix A: Quarterly Flash Report", section_heading),
        HRFlowable(width="100%", thickness=0.6, color=NAVY, spaceAfter=6),
        Paragraph(html.escape(exhibits[0]["identity"]), caption),
        Paragraph(
            "Selected flash exhibits follow the sample PMR. Values retain the source PDF's displayed precision; "
            "blank figures are not estimated. The complete flash is available as appendix.pdf in the audit package.",
            caption,
        ),
    ]
    diversification_started = False
    for exhibit in exhibits:
        if "Diversification" in exhibit["title"] and not diversification_started:
            divider = HRFlowable(width="100%", thickness=0.6, color=NAVY, spaceAfter=6)
            divider.keepWithNext = True
            story.extend([
                Paragraph("Diversification and Annual Returns", heading),
                divider,
            ])
            diversification_started = True
        story.append(Paragraph(html.escape(exhibit["title"]), heading))
        story.append(Paragraph(f"Flash source page {exhibit['source_page']}", caption))
        if "Geographic Diversification" in exhibit["title"]:
            story.append(
                Paragraph(
                    "NE: Northeast; SE: Southeast; SW: Southwest. Central-region labels are abbreviated.",
                    caption,
                )
            )
        count = len(exhibit["headers"])
        widths = [134] + [364 / (count - 1)] * (count - 1)
        if exhibit["title"] == "Portfolio Composition ($)":
            widths = [498 / count] * count
        elif exhibit["title"].startswith("Returns and Multiples") and "Market Value" in exhibit["headers"]:
            nav = exhibit["headers"].index("Market Value")
            nav_width = max(stringWidth(display_cell(exhibit, nav, row[nav]), "Helvetica", body.fontSize)
                            for row in exhibit["rows"]) + 7
            widths = [134] + [(364 - nav_width) / (count - 2)] * (count - 1)
            widths[nav] = nav_width
        elif exhibit["title"] == "Quarterly cash activity" and count == 10:
            # Reserve enough space for each actual amount, including its currency sign.
            numeric_widths = [max(
                34,
                max(stringWidth(display_cell(exhibit, c, row[c]), "Helvetica", body.fontSize) for row in exhibit["rows"]) + 5,
                max(stringWidth(word, "Helvetica-Bold", body.fontSize) for word in exhibit["headers"][c].split()) + 5,
            ) for c in range(1, count)]
            widths = [498 - sum(numeric_widths)] + numeric_widths
        header = [
            Paragraph('<font color="white"><b>' + html.escape(str(c)) + "</b></font>", body)
            for c in exhibit["headers"]
        ]
        cells = [header] + [[Paragraph(html.escape(display_cell(exhibit, column, c)), body) for column, c in enumerate(row)] for row in exhibit["rows"]]
        table = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#edf0f6")]),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd1dd")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.extend([table, Spacer(1, 8)])
        if exhibit.get("note"):
            story.append(Paragraph(html.escape(exhibit["note"]), omission_note))
    first_page = len(result)

    def footer(canvas, doc):
        canvas.setFont("Helvetica", 7)
        canvas.drawString(36, 28, "Vectera Advisors | Trade Secret & Confidential")
        canvas.drawRightString(
            576, 28, f"Page {first_page + doc.page}" + (" | DRAFT" if not approved else "")
        )

    buffer = io.BytesIO()
    SimpleDocTemplate(
        buffer, pagesize=(612, 792), leftMargin=50.4, rightMargin=50.4, topMargin=48, bottomMargin=44, invariant=1
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    with fitz.open(stream=buffer.getvalue(), filetype="pdf") as appendix:
        result.insert_pdf(appendix)
