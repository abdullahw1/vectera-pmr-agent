"""Presentation stays readable without bypassing saved-draft or PDF integrity."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from pmr.pipeline import generate
from pmr.review import approve, pdf_preview, render_review_page

INPUTS = Path(__file__).resolve().parents[1] / "inputs"


@pytest.fixture(scope="module")
def draft(tmp_path_factory):
    import os
    from unittest.mock import patch

    output = tmp_path_factory.mktemp("presentation")
    with patch.dict(os.environ, {"OPENAI_API_KEY": "", "ANTHROPIC_API_KEY": ""}):
        payload, _ = generate(INPUTS, output, "CPERS", "4Q25")
    return output, payload


def test_pdf_preview_comes_from_the_unchanged_report(draft):
    output, _ = draft
    before = hashlib.sha256((output / "report.pdf").read_bytes()).hexdigest()
    metadata = pdf_preview(output)
    assert metadata["pages"] == 15 and not metadata["approved"]
    assert metadata["width"] == 612 and metadata["height"] == 792
    assert pdf_preview(output, 2).startswith(b"\x89PNG\r\n\x1a\n")
    assert hashlib.sha256((output / "report.pdf").read_bytes()).hexdigest() == before
    assert not (output / "approval.json").exists()


@pytest.mark.parametrize("page", [-1, 100, True, "2"])
def test_preview_rejects_invalid_pages(draft, page):
    output, _ = draft
    with pytest.raises(ValueError, match="outside the report"):
        pdf_preview(output, page)


def test_current_presentation_does_not_modify_the_saved_payload(draft):
    _, payload = draft
    before = copy.deepcopy(payload)
    page = render_review_page(payload)
    assert payload == before
    assert "__PAYLOAD__" not in page and "__RUNTIME__" not in page
    assert '"implementation_current": true' in page
    assert 'id="source-drawer"' in page and 'id="technical-drawer"' in page
    assert 'id="release-panel"' in page
    assert "Not reported in the source" in page


def test_outdated_implementation_is_explicit_and_still_blocks_release(draft, monkeypatch):
    output, payload = draft
    monkeypatch.setattr("pmr.review.implementation_hashes", lambda: {"changed.py": "new-code"})
    page = render_review_page(payload)
    assert '"implementation_current": false' in page
    with pytest.raises(ValueError, match="Implementation changed"):
        approve(output, dict(draft_hash=payload["draft_hash"], reviewer="Automated test"))


def test_review_runtime_escapes_untrusted_text(draft):
    _, payload = draft
    record = dict(draft_hash=payload["draft_hash"], report_filename="CPERS_PMR_4Q25.pdf",
                  reviewer="</script><script>untrusted</script>")
    page = render_review_page(payload, approval=record)
    assert "</script><script>untrusted" not in page
    assert "\\u003c/script" in page


def test_mismatched_approval_does_not_mark_the_draft_final(draft):
    _, payload = draft
    page = render_review_page(payload, approval={"draft_hash": "another-draft", "report_filename": "other.pdf"})
    assert '"approval": null' in page


def test_tampered_pdf_or_draft_is_not_previewed(draft, tmp_path):
    output, payload = draft
    (tmp_path / "draft.json").write_text(json.dumps(payload, default=str))
    (tmp_path / "report.pdf").write_bytes(b"not the original PDF")
    with pytest.raises(ValueError, match="integrity check"):
        pdf_preview(tmp_path)
    tampered = copy.deepcopy(payload)
    tampered["data"]["portfolio"]["nav"] = 1
    with pytest.raises(ValueError, match="Saved draft changed"):
        render_review_page(tampered)
    (tmp_path / "draft.json").write_text(json.dumps(tampered, default=str))
    with pytest.raises(ValueError, match="Saved draft changed"):
        pdf_preview(tmp_path)


def test_approved_preview_uses_the_final_pdf_and_its_hash(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def extraction(self, prompt, image=None):
        return dict(title="Offline test exhibit", series=[dict(label="Test", series="Test", value=1, unit="%")]) if image else None

    monkeypatch.setattr("pmr.models.Model.ask", extraction)
    payload, _ = generate(INPUTS, tmp_path, "CPERS", "4Q25")
    approve(tmp_path, dict(draft_hash=payload["draft_hash"], reviewer="Automated test", acknowledged=True,
                          confirmed_charts=[c["id"] for c in payload["data"]["charts"]]))
    assert pdf_preview(tmp_path)["approved"]
    assert pdf_preview(tmp_path, 0).startswith(b"\x89PNG")
    (tmp_path / "final_report.pdf").write_bytes(b"changed final")
    with pytest.raises(ValueError, match="integrity check"):
        pdf_preview(tmp_path)
