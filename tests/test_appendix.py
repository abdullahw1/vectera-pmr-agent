"""Presentation regression: Letter paper, readable source values and repeated labels."""
from pathlib import Path
import re

import fitz

from pmr.appendix import append_exhibits


def test_source_exhibits_keep_values_on_letter_pages():
    source = Path(__file__).resolve().parents[1] / "inputs/flash_4Q25.pdf"
    result = fitz.open()
    append_exhibits(result, source)
    assert len(result) > 6  # Tall, wide tables need multiple pages; short panels can share a page.
    combined = "\n".join(p.get_text() for p in result)
    with fitz.open(source) as original:
        for page in original:
            for token in re.findall(r"(?<!\w)[+-]?\d[\d,.]*%?", page.get_text()):
                assert token in combined
    for page in result:
        assert (page.rect.width, page.rect.height) == (612, 792)
        assert "DRAFT" in page.get_text()
        assert "Flash source page" in page.get_text()
    annual = [p for p in result if "Flash source page 6" in p.get_text()]
    assert "Panel 3 of" in "\n".join(p.get_text() for p in annual)
    assert all("CPERS Custom Benchmark" in p.get_text() for p in annual)
