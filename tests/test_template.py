from pathlib import Path

from pmr.evidence import Ledger
from pmr.template import extract_template


def test_template_uses_readable_body_and_visible_primary_color():
    root = Path(__file__).resolve().parents[1]
    template = extract_template(root / "inputs" / "prior_pmr_3Q25.pdf", Ledger())
    assert template["body_size"] == 9.2
    assert template["heading_size"] == 15
    assert template["primary"] != "#ffffff"
    assert len(template["section_order"]) == 14
