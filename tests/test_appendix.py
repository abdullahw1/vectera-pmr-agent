"""Presentation regression: Letter paper, readable source values and repeated labels."""

from pathlib import Path
import re

import fitz

from pmr.appendix import append_exhibits, extract_exhibits


def test_source_exhibits_keep_values_on_letter_pages():
    source = Path(__file__).resolve().parents[1] / "inputs/flash_4Q25.pdf"
    result = fitz.open()
    append_exhibits(result, source)
    assert len(result) <= 6  # Source padding and merged titles must not inflate the appendix.
    combined = "\n".join(p.get_text() for p in result)
    with fitz.open(source) as original:
        for page in original:
            for token in re.findall(r"(?<!\w)[+-]?\d[\d,.]*%?", page.get_text()):
                assert token in combined
    for page in result:
        assert (page.rect.width, page.rect.height) == (612, 792)
        assert "DRAFT" in page.get_text()
        assert "Flash source page" in page.get_text()
    assert "CPERS Custom Benchmark" in combined
    assert "10 Year Net" in combined


def test_each_projection_has_one_complete_header_and_unchanged_values():
    source = Path(__file__).resolve().parents[1] / "inputs/flash_4Q25.pdf"
    exhibits = extract_exhibits(source)
    with fitz.open(source) as original:
        for exhibit in exhibits:
            assert all(exhibit["headers"])
            assert all(len(row) == len(exhibit["headers"]) for row in exhibit["rows"])
            raw = original[exhibit["source_page"] - 1].find_tables().tables[0].extract()
            for row in exhibit["rows"]:
                assert any([str(candidate[c] or "") for c in exhibit["columns"]] == row for candidate in raw)


def test_unrecognized_readable_source_layout_is_retained(tmp_path):
    path = tmp_path / "flash.pdf"
    with fitz.open() as source:
        page = source.new_page()
        page.insert_text((40, 70), "Other Client 1Q26\nInvestment A NAV 123,456.78", fontsize=11)
        source.save(path)
    result = fitz.open()
    append_exhibits(result, path)
    assert len(result) == 1
    assert "123,456.78" in result[0].get_text()
    assert "original layout" in result[0].get_text()
    assert result[0].rect == fitz.Rect(0, 0, 612, 792)
