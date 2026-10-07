"""Context warnings do not overwrite flash returns or sleeve compliance."""

from pathlib import Path
from decimal import Decimal
import pytest

from pmr.crosschecks import contextual_checks
from pmr.evidence import Ledger


def setup_case(tmp_path):
    ledger = Ledger()
    fact = ledger.add("source", {"file": "flash.xlsx", "sheet": "cash", "cell": "A1"})
    fund = dict(name="Example Fund", sleeve="Strategic", nav=Decimal("0"), nav_id=fact,
                q_net=5.25, q_net_id=fact, ltv=50.8, ltv_id=fact,
                beginning=Decimal("0"), contributions=Decimal("100"))
    data = dict(funds=[fund], support={}, policy=dict(leverage=[50, 75], leverage_id=fact),
                history=[], charts=[], quarter="1Q26")
    sources = dict(root=tmp_path, managers=[], prior=(None, Path("prior.pdf"), []))
    return ledger, fact, fund, data, sources


def test_terminated_status_and_return_notice_are_flagged(tmp_path):
    ledger, fact, fund, data, sources = setup_case(tmp_path)
    quote = "The Fund has been dissolved."
    status = dict(text=quote, heading="Final notice", id=fact,
                  source=dict(file="manager.pdf", page=1, quote=quote))
    data["support"][fund["name"]] = [status]
    sources["managers"] = [(tmp_path / "manager.pdf", [quote + " No quarterly performance percentages are presented."])]
    contextual_checks(sources, data, ledger)
    assert fund["termination"] == status
    assert fund["termination_return_note_id"] in ledger.facts
    assert fund["q_net"] == 5.25
    assert any(i["code"] == "terminated_fund" for i in ledger.issues)


def test_fund_level_risk_and_funding_are_separate_from_compliance(tmp_path):
    ledger, _, fund, data, sources = setup_case(tmp_path)
    contextual_checks(sources, data, ledger)
    assert fund["newly_funded"] and fund["ltv_risk_threshold"] == 50
    assert any(i["code"] == "fund_leverage_risk" and i["severity"] == "warning" for i in ledger.issues)
    fund["contributions"] = None
    contextual_checks(sources, data, ledger)  # An unavailable cash value is not treated as new funding.


@pytest.mark.parametrize("text", ["Quarter\n4Q25\n496\n436\n", "Quarter\n 4Q25       496       436\n"])
def test_historical_restatement_records_both_sources(tmp_path, text):
    ledger, fact, _, data, sources = setup_case(tmp_path)
    data["history"] = [dict(quarter="4Q25", target=Decimal("512"), nav=Decimal("436"),
                            target_id=fact, nav_id=fact)]
    sources["prior"] = (None, Path("prior.pdf"), [text])
    contextual_checks(sources, data, ledger)
    revisions = data["historical_revisions"]
    assert len(revisions) == 1 and revisions[0]["metric"] == "target"
    assert len(revisions[0]["evidence"]) == 2
    assert all(i in ledger.facts for i in revisions[0]["evidence"])


def test_chart_observation_period_not_deck_name_controls_lag_warning(tmp_path):
    ledger, fact, _, data, sources = setup_case(tmp_path)
    data["charts"] = [dict(id=fact, data=dict(series=[dict(label="25Q4")]))]
    contextual_checks(sources, data, ledger)
    assert data["market_observation_period"] == "4Q25"
    assert any(i["code"] == "market_data_lag" for i in ledger.issues)
    data["quarter"] = "4Q25"
    fresh = Ledger()
    contextual_checks(sources, data, fresh)
    assert not any(i["code"] == "market_data_lag" for i in fresh.issues)


def test_terminated_ranked_fund_keeps_its_attribution_roles(tmp_path, monkeypatch):
    import copy
    import fitz
    from pmr.pipeline import generate

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    inputs = Path(__file__).resolve().parents[1] / "inputs"
    payload, _ = generate(inputs, tmp_path / "base", "CPERS", "4Q25")
    from pmr.report import build_sections
    from pmr.ingest import discover, quarter

    ledger = Ledger()
    sources = discover(inputs, "CPERS", quarter("4Q25"), ledger)
    data = copy.deepcopy(payload["data"])
    fund = next(f for f in data["funds"] if "largest individual position" in f["roles"])
    quote = "The Fund has been dissolved."
    fid = ledger.add(quote, dict(file="manager.pdf", page=1, quote=quote))
    fund["termination"] = dict(text=quote, id=fid)
    sections = build_sections(data, sources, ledger)
    text = next(b["text"] for s in sections for b in s["blocks"]
                if b.get("type") == "paragraph" and quote in b.get("text", ""))
    assert "largest individual position" in text
    assert all(role in text for role in fund["roles"])
