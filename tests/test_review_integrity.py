"""A UI checkbox is not a security boundary; enforce review rules in the backend."""

from pathlib import Path
import pytest

from pmr.pipeline import generate
from pmr.review import approve

INPUTS = Path(__file__).resolve().parents[1] / "inputs"


@pytest.fixture
def extracted(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def mock(self, prompt, image=None):
        return (
            dict(title="Test", series=[dict(label="Test", series="Test", value=1, unit="%")])
            if image
            else None
        )

    monkeypatch.setattr("pmr.models.Model.ask", mock)
    payload, _ = generate(INPUTS, tmp_path, "CPERS", "4Q25")
    request = dict(
        draft_hash=payload["draft_hash"],
        reviewer="Test reviewer",
        acknowledged=True,
        confirmed_charts=[c["id"] for c in payload["data"]["charts"]],
    )
    return tmp_path, payload, request


def test_acknowledgment_is_required_by_backend(extracted):
    output, _, request = extracted
    request.pop("acknowledged")
    with pytest.raises(ValueError, match="acknowledgment"):
        approve(output, request)
    assert not (output / "approval.json").exists()


def test_changed_asset_blocks_approval(extracted):
    output, payload, request = extracted
    asset = output / payload["data"]["charts"][0]["asset"]
    asset.write_bytes(b"changed image")
    with pytest.raises(ValueError, match="asset changed"):
        approve(output, request)


@pytest.mark.parametrize("removed", [False, True])
def test_changed_or_missing_displayed_pdf_blocks_approval(extracted, removed):
    output, payload, request = extracted
    assert "report.pdf" in payload["asset_hashes"]
    if removed:
        (output / "report.pdf").unlink()
    else:
        (output / "report.pdf").write_bytes(b"tampered displayed PDF")
    with pytest.raises(ValueError, match="Draft PDF changed"):
        approve(output, request)
    assert not (output / "approval.json").exists()


def test_named_draft_pdf_tampering_blocks_approval(extracted):
    output, _, request = extracted
    (output / "CPERS_PMR_4Q25_DRAFT.pdf").write_bytes(b"changed client-facing PDF")
    with pytest.raises(ValueError, match="asset changed"):
        approve(output, request)
    assert not (output / "CPERS_PMR_4Q25.pdf").exists()


def test_pdf_integrity_cannot_be_omitted(extracted):
    import json
    from pmr.evidence import digest

    output, payload, request = extracted
    payload.pop("draft_hash")
    payload["asset_hashes"].pop("report.pdf")
    payload["draft_hash"] = digest(payload)
    request["draft_hash"] = payload["draft_hash"]
    (output / "draft.json").write_text(json.dumps(payload, default=str))
    with pytest.raises(ValueError, match="integrity record is missing"):
        approve(output, request)
    assert not (output / "approval.json").exists()


def test_correction_requires_new_draft_review_not_immediate_release(extracted):
    import json
    import copy

    output, payload, request = extracted
    corrected = copy.deepcopy(payload["data"]["charts"][0]["data"])
    corrected["series"][0]["value"] = -1
    request["corrections"] = {payload["data"]["charts"][0]["id"]: dict(data=corrected, reason="Visible label is negative")}
    result = approve(output, request)
    assert result["status"] == "review_required"
    assert result["draft_hash"] != payload["draft_hash"]
    assert not (output / "approval.json").exists()
    assert not (output / "final_report.pdf").exists()
    with pytest.raises(ValueError, match="Draft changed"):
        approve(output, request)
    revised = json.loads((output / "draft.json").read_text())
    assert revised["data"]["charts"][0]["data"]["series"][0]["value"] == -1
    request.update(draft_hash=revised["draft_hash"], corrections={})
    assert approve(output, request)["status"] == "approved"
    record = json.loads((output / "approval.json").read_text())
    assert record["corrections"][payload["data"]["charts"][0]["id"]]["reason"] == "Visible label is negative"
    assert record["asset_hashes"]["report.pdf"] == revised["asset_hashes"]["report.pdf"]


def test_noop_correction_does_not_create_an_endless_review_cycle(extracted):
    output, payload, request = extracted
    chart = payload["data"]["charts"][0]
    request["corrections"] = {chart["id"]: dict(data=chart["data"], reason="Confirmed unchanged")}
    assert approve(output, request)["status"] == "approved"


def test_correction_requires_reason_and_full_schema(extracted):
    output, payload, request = extracted
    identifier = payload["data"]["charts"][0]["id"]
    request["corrections"] = {identifier: dict(data=dict(series=[dict(value=1)]))}
    with pytest.raises(ValueError, match="reason"):
        approve(output, request)
    request["corrections"][identifier]["reason"] = "Correct displayed value"
    with pytest.raises(ValueError, match="labels"):
        approve(output, request)


def test_unknown_chart_id_cannot_be_confirmed(extracted):
    output, _, request = extracted
    request["confirmed_charts"].append("made-up")
    with pytest.raises(ValueError, match="Unknown confirmed"):
        approve(output, request)


def test_one_unconfirmed_chart_blocks_approval(extracted):
    output, _, request = extracted
    request["confirmed_charts"].pop()
    with pytest.raises(ValueError, match="Confirm all"):
        approve(output, request)
    assert not (output / "approval.json").exists()


def test_changed_implementation_blocks_approval(extracted, monkeypatch):
    output, _, request = extracted
    monkeypatch.setattr("pmr.review.implementation_hashes", lambda: {"report.py": "changed"})
    with pytest.raises(ValueError, match="Implementation changed"):
        approve(output, request)
    assert not (output / "approval.json").exists()


def test_final_semantics_and_evidence_are_saved(extracted):
    output, _, request = extracted
    approve(output, request)
    assert (output / "final_semantic_manifest.json").is_file()
    assert (output / "final_manifest.json").is_file()
    assert (output / "final_evidence.json").is_file()
