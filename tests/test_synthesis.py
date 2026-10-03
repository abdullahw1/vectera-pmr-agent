import pytest
from pmr.synthesis import validate_sentences, synthesize, qualitative_fallback, prepare
from pmr.evidence import Ledger
from pmr.report import accounting, dollars, billions
from decimal import Decimal
from pathlib import Path
from pmr.narrative import supporting_documents


PASSAGES = [dict(id="source", text="Leasing demand improved while refinancing remained a risk.",
                 source=dict(file="manager.pdf", page=1))]


def response(text="The manager reports improved leasing demand.", quote=PASSAGES[0]["text"]):
    return dict(sentences=[dict(text=text, source_id="source", quote=quote)])


def test_scoped_quote_and_number_firewall():
    assert validate_sentences(response(), PASSAGES)
    for text in ["The fund returned 9%.", "The fund gained one million dollars.", "The fund gained $500."]:
        with pytest.raises(ValueError, match="Numerical"):
            validate_sentences(response(text), PASSAGES)
    with pytest.raises(ValueError, match="verbatim"):
        validate_sentences(response(quote="The manager expects exceptional growth."), PASSAGES)


def test_agent_focus_must_be_used():
    class Model:
        provider = "test"
        def ask(self, prompt):
            if prompt.startswith("CHECK_PARAPHRASES"):
                return dict(supported=[True], reason="Supported")
            return response()
    ledger = Ledger()
    assert synthesize(PASSAGES, "Drivers", Model(), ledger,
                      [dict(id="source", quote=PASSAGES[0]["text"])])
    assert synthesize(PASSAGES, "Drivers", Model(), ledger,
                      [dict(id="other_source", quote="Leasing demand improved")]) is None
    assert any(i["code"] == "narrative_rejected" for i in ledger.issues)


def test_display_does_not_change_exact_values():
    value = Decimal("-557954.40")
    assert accounting(value) == "(557,954)"
    assert dollars(Decimal("1367035.55")) == "$1,367,036"
    assert billions(Decimal("4955900000")) == "$4.96 billion"
    assert value == Decimal("-557954.40")


def test_renamed_heading_is_not_a_missing_report():
    ledger = Ledger()
    name = "Cornerstone Core Property Fund"
    sources = dict(root=Path("inputs"), managers=[(Path("inputs/manager.pdf"),
                   [name + "\nQuarterly Operating Review\nLeasing demand improved while refinancing remained a risk."])])
    funds = [dict(name=name, roles=["largest position"], fees=Decimal("0"), fees_id="fee")]
    support = supporting_documents(sources, dict(funds=funds), dict(new=[]), ledger, None)
    assert support[name]
    assert support[name][0]["heading"] == "Unclassified manager page"
    assert any(i["code"] == "manager_extraction" for i in ledger.issues)
    assert not any(i["code"] == "missing_manager" for i in ledger.issues)


def test_invalid_prose_gets_one_bounded_repair():
    class Model:
        provider = "test"
        calls = 0
        def ask(self, prompt):
            self.calls += 1
            if prompt.startswith("CHECK_PARAPHRASES"):
                return dict(supported=[True], reason="Supported")
            return response("The fund returned 9%.") if self.calls == 1 else response()
    model, ledger = Model(), Ledger()
    assert synthesize(PASSAGES, "Drivers", model, ledger)
    assert model.calls == 3


def test_fallback_cannot_change_numerical_inventory():
    text = qualitative_fallback([dict(text="Leasing improved to 97% occupancy. Cedar Ridge was held flat pending expansion.")])
    assert "pending review" in text and "97% occupancy" in text
    assert "Cedar Ridge was held flat pending expansion." in text
    assert qualitative_fallback([dict(text="Return was 9%.")])


def test_numbers_and_asset_names_are_bound_to_exact_source():
    source = "Gateway Logistics Center (Dallas) reached 97% occupancy. Harbor 40 Distribution (Savannah) signed a 10-year lease."
    passages = [dict(id="source", text=source)]
    masked, _, required = prepare(passages)
    result = response(masked[0]["text"], masked[0]["text"])
    assert validate_sentences(result, passages)[0]["text"] == source
    assert len(required) == 3
    with pytest.raises(ValueError, match="placeholders"):
        validate_sentences(response(source, source), passages)
    with pytest.raises(ValueError, match="exactly once"):
        validate_sentences(response(masked[0]["text"].replace(required[0], ""), masked[0]["text"]), passages)
    with pytest.raises(ValueError, match="signs"):
        validate_sentences(response(masked[0]["text"].replace(required[0], "-"+required[0]), masked[0]["text"]), passages)


def test_slots_cannot_borrow_numbers_from_another_source():
    passages = [dict(id="a", text="The manager reports 97% occupancy."),
                dict(id="b", text="The manager reports 40% occupancy.")]
    masked, _, _ = prepare(passages)
    result = dict(sentences=[dict(text=masked[1]["text"], quote=masked[1]["text"], source_id="a")])
    with pytest.raises(ValueError, match="quoted source"):
        validate_sentences(result, passages)


def test_word_numeral_and_ampersand_matching():
    from pmr.ingest import entity
    assert entity("Ironwood Value-Add Fund Three, L.P.") == entity("Ironwood Value-Add Fund III")
    assert entity("Income & Growth Fund Two") == entity("Income and Growth Fund II")
    assert entity("One Financial Plaza") == "one financial plaza"


def test_unmatched_report_is_flagged_not_silently_dropped():
    ledger = Ledger()
    name = "Cornerstone Core Property Fund"
    sources = dict(root=Path("inputs"), managers=[(Path("inputs/manager.pdf"), ["Cornrstone Property Fund\nQuarterly review"])])
    data = dict(funds=[dict(name=name, roles=["largest position"], fees=Decimal("0"), fees_id="fee")])
    supporting_documents(sources, data, dict(new=[]), ledger, None)
    assert data["unmatched_reports"]
    issue = next(i for i in ledger.issues if i["code"] == "unmatched_manager")
    assert name in issue["candidates"]


def test_unsupported_meaning_is_rejected_even_with_real_quote():
    class Model:
        provider = "test"
        def ask(self, prompt):
            if prompt.startswith("CHECK_PARAPHRASES"):
                return dict(supported=[False], reason="Invented recommendation")
            return response("The manager recommends increasing allocations.")
    ledger = Ledger()
    assert synthesize(PASSAGES, "Drivers", Model(), ledger) is None
    assert any("Claim-versus-quote" in i["message"] for i in ledger.issues)


def test_market_cannot_omit_house_view_risk_sources():
    passages = [*PASSAGES, dict(id="risks", text="Refinancing pressure remains a risk.", qualitative_only=True)]
    with pytest.raises(ValueError, match="house-view"):
        validate_sentences(response(), passages)


def test_host_attaches_exact_quote_without_model_transcription():
    result = dict(sentences=[dict(text="The manager reports improved leasing demand.", source_id="source")])
    assert validate_sentences(result, PASSAGES)[0]["quote"] == PASSAGES[0]["text"]


def test_natural_reordering_preserves_exact_inventory():
    passages = [dict(id="source", text="Return was 3.3% over 1-Yr.")]
    result = dict(sentences=[dict(text="Over [[VALUE_B]]-Yr, return was [[VALUE_A]].", source_id="source")])
    assert validate_sentences(result, passages)[0]["text"] == "Over 1-Yr, return was 3.3%."
    result["sentences"][0]["text"] += " Return was [[VALUE_A]]."
    with pytest.raises(ValueError, match="exactly once"):
        validate_sentences(result, passages)


def test_house_view_dates_are_not_optional_numeric_inventory():
    passages = [dict(id="source", text="Values repriced in 2023-2024.", qualitative_only=True)]
    with pytest.raises(ValueError, match="exactly once"):
        validate_sentences(dict(sentences=[dict(text="The deck describes repricing.", source_id="source")]), passages)


def test_numeric_mask_excludes_punctuation_and_binds_periods():
    from pmr.synthesis import NUMBER
    text = "At 25Q4, forecast 2026-27 is 1.3%, after 2023–2024 repricing. NAV $1,367,035.55."
    assert NUMBER.findall(text) == ["25Q4", "2026-27", "1.3%", "2023–2024", "$1,367,035.55"]
    passage = dict(id="source", text=text)
    masked, _, _ = prepare([passage])
    assert validate_sentences(dict(sentences=[dict(text=masked[0]["text"], source_id="source")]), [passage])[0]["text"] == text


def test_manager_claim_cannot_be_attributed_to_market_deck():
    class Model:
        provider = "test"
        def ask(self, prompt):
            return response("The market deck reports improved leasing demand.")
    ledger = Ledger()
    assert synthesize(PASSAGES, "Performance drivers for a fund", Model(), ledger) is None
    assert any("attributed to the market deck" in i["message"] for i in ledger.issues)
