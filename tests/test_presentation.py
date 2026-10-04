"""Reference typography and vector-chart checks without paid model calls."""

import fitz

from pmr.report import market_paragraphs, render_pdf, styled_text
from pmr.visuals import chart_drawing


def test_emphasis_is_dynamic_and_escapes_source_markup():
    data = dict(funds=[dict(name="Different Fund & Partners")], activity=dict(new=[]))
    text = "Different Fund & Partners holds $12.3M and 8.8%. <script>"
    formatted = styled_text(text, data, "Portfolio Overview")
    assert "<b>Different Fund &amp; Partners</b>" in formatted
    assert "<b>$12.3M</b>" in formatted and "<b>8.8%</b>" in formatted
    assert "&lt;script&gt;" in formatted and "<script>" not in formatted
    assert "<b>Jane Analyst</b>" in styled_text("Jane Analyst, Portfolio Manager", data, "Portfolio Managers")


def test_market_display_paragraphs_preserve_every_sentence():
    text = "Industrial demand improved. Office remained weak. Pricing changed. Supply slowed. Lending tightened. Investors stayed cautious."
    paragraphs = market_paragraphs(text)
    assert len(paragraphs) == 3
    assert " ".join(paragraphs) == text


def test_reference_cover_headings_borders_and_native_charts(tmp_path):
    data = dict(
        client="OTHER", quarter="1Q26",
        period_label="First Quarter 2026",
        template={},
        portfolio=dict(name="Different Retirement System", benchmark="Client Benchmark", annual=[
            dict(horizon=1, value=5.46, benchmark=2.66),
            dict(horizon=3, value=-0.47, benchmark=-2.99),
            dict(horizon=5, value=5.58, benchmark=2.49),
        ]),
        funds=[dict(name="Different Fund & Partners")], activity=dict(new=[]),
        history=[dict(quarter="4Q25", target=490, nav=430), dict(quarter="1Q26", target=500, nav=440)],
        diversification=dict(
            property=[dict(label="Industrial", value=60), dict(label="Other", value=40)],
            geography=[dict(label="Pacific", value=70), dict(label="Ex-US", value=30)],
        ),
    )
    sections = [
        dict(title="Portfolio Overview", blocks=[dict(type="paragraph", text="Different Fund & Partners holds $12.3M and 8.8%.")]),
        dict(title="Investment Guidelines & Fund Statistics", blocks=[dict(type="table", columns=["Metric", "Value"], rows=[["NAV", "$12.3M"]])]),
        dict(title="Portfolio Managers", blocks=[dict(type="paragraph", text="Jane Analyst, Portfolio Manager")]),
        dict(title="Annualized Time-Weighted Return", blocks=[dict(type="chart", kind="annual")]),
        dict(title="Allocation Over Time", blocks=[dict(type="chart", kind="allocation")]),
        dict(title="Diversification", blocks=[dict(type="chart", kind="property"), dict(type="chart", kind="geography"), dict(type="paragraph", text="Look-through exposure is a distinct measure.", style="footnote")]),
    ]
    path = tmp_path / "report.pdf"
    render_pdf(data, sections, path, appendix=None)
    with fitz.open(path) as pdf:
        def spans(page):
            return [s for b in page.get_text("dict")["blocks"] for line in b.get("lines", []) for s in line["spans"]]

        cover = spans(pdf[0])
        title = next(s for s in cover if "Performance Measurement Report" in s["text"])
        assert title["size"] == 23 and "Bold" in title["font"]
        assert abs(title["bbox"][0] - 56.4) < 0.2
        for text, size in [("First Quarter 2026", 13), ("Prepared by Vectera Advisors", 13), ("Trade Secret & Confidential", 7.5)]:
            span = next(s for s in cover if s["text"] == text)
            assert span["size"] == size and "Bold" not in span["font"]
        assert len(pdf[1].get_drawings()) > 0  # Contents underline.
        overview = spans(pdf[2])
        stats = next(s for s in overview if s["text"] == "Investment Guidelines & Fund Statistics")
        assert stats["size"] == 10 and "Bold" in stats["font"]
        assert any("Bold" in s["font"] and "$12.3M" in s["text"] for s in overview)
        assert any("Bold" in s["font"] and "Jane Analyst" in s["text"] for s in overview)
        assert len(pdf[2].get_drawings()) >= 8  # Grid lines, not just a colored header.
        all_text = "\n".join(page.get_text() for page in pdf)
        assert "Target Allocation vs Net Asset Value ($MM)" in all_text
        for page in pdf:
            assert page.rect == fitz.Rect(0, 0, 612, 792)
            assert not page.get_images()  # Main charts remain vector, not raster screenshots.
            for span in spans(page):
                assert span["bbox"][0] >= 0 and span["bbox"][2] <= 612
                if "Look-through exposure" in span["text"]:
                    assert span["size"] == 7.5 and "Oblique" in span["font"]
    assert chart_drawing("property", data).hAlign == "LEFT"
