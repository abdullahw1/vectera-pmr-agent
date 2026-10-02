"""Render the submission write-up as a compact, reviewable two-page PDF."""
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak


def main():
    source = Path("docs/WRITEUP.md")
    output = Path("output/writeup.pdf"); output.parent.mkdir(exist_ok=True)
    styles = {
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=17, leading=20, textColor=colors.HexColor("#1b2b49"), spaceAfter=12),
        "heading": ParagraphStyle("heading", fontName="Helvetica-Bold", fontSize=11, leading=14, spaceBefore=10, spaceAfter=5),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=12.5, spaceAfter=7),
    }
    story = []
    for paragraph in source.read_text(encoding="utf-8").split("\n\n"):
        if paragraph.startswith("# "):
            style, text = "title", paragraph[2:]
        elif paragraph.startswith("## "):
            style, text = "heading", paragraph[3:]
            if text == "Next quarter and format changes":
                story.append(PageBreak())
        else:
            style, text = "body", paragraph
        story.append(Paragraph(escape(text.replace("\n", " ")), styles[style]))
    def footer(canvas, doc):
        canvas.setFont("Helvetica", 8); canvas.setFillColor(colors.grey)
        canvas.drawString(48, 25, "Vectera PMR | Implementation Rationale")
        canvas.drawRightString(564, 25, str(doc.page))
    SimpleDocTemplate(str(output), pagesize=(612, 792), leftMargin=48, rightMargin=48,
                      topMargin=40, bottomMargin=40, invariant=1).build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)


if __name__ == "__main__":
    main()
