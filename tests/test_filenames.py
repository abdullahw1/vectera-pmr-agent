import pytest

from pmr.filenames import clear_named_reports, report_filename


@pytest.mark.parametrize("client,period,expected", [
    ("CPERS", "4Q25", "CPERS_PMR_4Q25.pdf"),
    ("ewrs", "1Q26", "EWRS_PMR_1Q26.pdf"),
    ("Example / Plan", "2Q26", "EXAMPLE_PLAN_PMR_2Q26.pdf"),
])
def test_report_names_follow_client_and_period(client, period, expected):
    assert report_filename(client, period, approved=True) == expected
    assert report_filename(client, period) == expected.replace(".pdf", "_DRAFT.pdf")


@pytest.mark.parametrize("client,period", [("../", "4Q25"), ("CPERS", "bad")])
def test_invalid_report_names_are_rejected(client, period):
    with pytest.raises(ValueError):
        report_filename(client, period)


def test_regeneration_removes_previous_named_exports(tmp_path):
    import json

    (tmp_path / "draft.json").write_text(json.dumps({"data": {"client": "EWRS", "quarter": "1Q26"}}))
    for approved in (False, True):
        (tmp_path / report_filename("EWRS", "1Q26", approved=approved)).write_bytes(b"old report")
    unrelated = tmp_path / "source.pdf"
    unrelated.write_bytes(b"source")
    clear_named_reports(tmp_path)
    assert not (tmp_path / "EWRS_PMR_1Q26.pdf").exists()
    assert not (tmp_path / "EWRS_PMR_1Q26_DRAFT.pdf").exists()
    assert unrelated.read_bytes() == b"source"
