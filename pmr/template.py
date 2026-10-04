"""Read reusable style and section order from the preceding report."""

from collections import Counter
import re
import fitz


def extract_template(path, ledger):
    spans = []
    headings = []
    with fitz.open(path) as document:
        cover = [span for block in document[0].get_text("dict")["blocks"] for line in block.get("lines", []) for span in line["spans"]]
        cover_names = [s["text"] for s in cover if s["size"] >= 20 and "Performance Measurement" not in s["text"]]
        for page in document:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    spans.extend(line["spans"])
            text = page.get_text()
            if "Contents" in text:
                headings = [match[1].strip() for match in re.finditer(r"^\d+\.\s+(.+)$", text, re.M)]
    # Weight by text length: many tiny table cells must not overwhelm the body typography.
    body, colored = Counter(), Counter()
    for span in spans:
        if span["color"] == 0 and "Bold" not in span["font"]:
            body[(span["font"], round(span["size"], 1))] += len(span["text"])
        if span["color"] not in {0, 0xFFFFFF, 0x666666, 0x555555}:
            colored[span["color"]] += len(span["text"])
    primary = colored.most_common(1)[0][0] if colored else 0x1B2B49
    heading_sizes = Counter(round(s["size"], 1) for s in spans if s["color"] == primary and s["size"] > 12)
    # ReportLab's built-in fonts are portable; unsupported embedded fonts are explicitly flagged.
    body_font, body_size = body.most_common(1)[0][0] if body else ("Helvetica", 9.2)
    supported = {"Helvetica", "Times-Roman", "Courier"}
    if body_font not in supported:
        ledger.issue("font_substitution", f"Template font {body_font} unavailable; using portable Helvetica")
        body_font = "Helvetica"
    result = dict(
        primary=f"#{primary:06x}",
        body_font=body_font,
        body_size=body_size,
        heading_size=heading_sizes.most_common(1)[0][0] if heading_sizes else 15,
        section_order=headings,
        cover_name_lines=cover_names,
    )
    result["id"] = ledger.add(
        result.copy(), {"file": path.name, "method": "PDF font spans and contents headings"}
    )
    return result
