"""Retypeset parsed flash exhibits, preserving displayed values and blank cells."""

import html
import io
import statistics

import fitz
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

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
}


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


def extract_exhibits(source):
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
                        "Plan assets ($)",
                        "Allocation ($)",
                        "Allocation / plan",
                        "Market value ($)",
                        "Market value (%)",
                        "Unfunded ($)",
                        "Unfunded (%)",
                        "Remaining allocation ($)",
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
                    title = "Investment funding"
                elif title == "Investment" and "Beginning value ($)" in headers:
                    title = "Quarterly cash activity"
                elif title != "Investment":
                    headers[0] = "Portfolio" if title != "Portfolio Composition ($)" else headers[0]
                data = clean_rows(rows[data_start:end])
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
                for name, columns in projections:
                    exhibits.append(
                        dict(
                            title=name,
                            source_page=page_number,
                            columns=columns,
                            identity=" | ".join(str(v) for row in rows[:2] for v in row if v),
                            headers=[headers[c] for c in columns],
                            rows=[[row[c] for c in columns] for row in data],
                        )
                    )
    return exhibits


def append_exhibits(result, source, approved=False):
    try:
        exhibits = extract_exhibits(source)
    except UnsupportedExhibitLayout:
        append_original_pages(result, source, approved)
        return
    body = ParagraphStyle("AppendixCell", fontName="Helvetica", fontSize=7.2, leading=8.6)
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
    story = [
        Paragraph("Appendix A: Quarterly Flash Report", heading),
        Paragraph(
            "Retypeset from the supplied flash PDF. Values retain the source exhibit's displayed precision; "
            "blank cells remain blank. The original PDF is retained in the audit package.",
            caption,
        ),
    ]
    story.append(Paragraph(html.escape(exhibits[0]["identity"]), caption))
    for exhibit in exhibits:
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
        widths = [160] + [380 / (count - 1)] * (count - 1)
        if exhibit["title"] == "Portfolio Composition ($)":
            widths = [540 / count] * count
        elif exhibit["title"] == "Quarterly cash activity" and count == 10:
            widths = [148] + [44.5] * 8 + [36]
        header = [
            Paragraph('<font color="white"><b>' + html.escape(str(c)) + "</b></font>", body)
            for c in exhibit["headers"]
        ]
        cells = [header] + [[Paragraph(html.escape(c), body) for c in row] for row in exhibit["rows"]]
        table = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#edf0f6")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.extend([table, Spacer(1, 8)])
    first_page = len(result)

    def footer(canvas, doc):
        canvas.setFont("Helvetica", 7)
        canvas.drawString(36, 28, "Vectera Advisors | Trade Secret & Confidential")
        canvas.drawRightString(
            576, 28, f"Page {first_page + doc.page}" + (" | DRAFT" if not approved else "")
        )

    buffer = io.BytesIO()
    SimpleDocTemplate(
        buffer, pagesize=(612, 792), leftMargin=36, rightMargin=36, topMargin=38, bottomMargin=44, invariant=1
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    with fitz.open(stream=buffer.getvalue(), filetype="pdf") as appendix:
        result.insert_pdf(appendix)
