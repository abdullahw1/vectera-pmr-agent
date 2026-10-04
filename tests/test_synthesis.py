import pytest
from pmr.synthesis import validate_sentences, synthesize, qualitative_fallback, prepare
from pmr.synthesis import source_excerpt
from pmr.evidence import Ledger
from pmr.report import accounting, dollars, billions
from decimal import Decimal
from pathlib import Path
import fitz
from pmr.ingest import pdf_pages
from pmr.narrative import supporting_documents

PASSAGES = [
    dict(
        id="source",
        text="Leasing demand improved while refinancing remained a risk.",
        source=dict(file="manager.pdf", page=1),
    )
]


def response(text="The manager reports improved leasing demand.", quote=PASSAGES[0]["text"]):
    return dict(sentences=[dict(text=text, source_id="source", quote=quote)])


def test_scoped_quote_and_number_firewall():
    assert validate_sentences(response(), PASSAGES)
    for text in ["The fund returned 9%.", "The fund gained one million dollars.", "The fund gained $500."]:
        with pytest.raises(ValueError, match="Numerical"):
            validate_sentences(response(text), PASSAGES)
    with pytest.raises(ValueError, match="verbatim"):
        validate_sentences(response(quote="The manager expects exceptional growth."), PASSAGES)


def test_display_does_not_change_exact_values():
    value = Decimal("-557954.40")
    assert accounting(value) == "(557,954)"
    assert dollars(Decimal("1367035.55")) == "$1,367,036"
    assert billions(Decimal("4955900000")) == "$4.96 billion"
    assert value == Decimal("-557954.40")


def manager_pdf(path, blocks):
    document = fitz.open()
    page = document.new_page()
    y = 50
    for text in blocks:
        page.insert_textbox(fitz.Rect(50, y, 550, y + 60), text, fontsize=10)
        y += 70
    document.save(path)


def test_renamed_heading_is_not_a_missing_report(tmp_path):
    ledger = Ledger()
    name = "Cornerstone Core Property Fund"
    path = tmp_path / "manager.pdf"
    prose = "Leasing demand improved at the logistics assets while refinancing remained a risk for office."
    manager_pdf(
        path, [name, "Quarterly Operating Review", prose, "Outlook", "The Manager expects stable income."]
    )
    sources = dict(root=tmp_path, managers=[(path, pdf_pages(path))])
    funds = [dict(name=name, roles=["largest position"], fees=Decimal("0"), fees_id="fee")]
    support = supporting_documents(sources, dict(funds=funds), dict(new=[]), ledger, None)
    # The unknown heading is used, the outlook is not, and the gap is flagged instead of called "missing".
    assert [p["text"] for p in support[name]] == [prose]
    assert any(i["code"] == "manager_extraction" for i in ledger.issues)
    assert not any(i["code"] == "missing_manager" for i in ledger.issues)


def test_matched_report_without_extractable_sections_retains_page_evidence():
    name = "Cornerstone Core Property Fund"
    ledger, data = Ledger(), dict(funds=[dict(name=name, roles=["largest position"], fees=Decimal("0"))])
    sources = dict(root=Path("inputs"), managers=[(Path("inputs/manager.pdf"), [name])])
    support = supporting_documents(sources, data, dict(new=[]), ledger, None)
    assert support[name] == []
    identifiers = data["unparsed_reports"][name]
    assert ledger.facts[identifiers[0]]["source"]["page"] == 1
    issue = next(i for i in ledger.issues if i["code"] == "manager_extraction")
    assert issue["evidence"] == identifiers
    assert "no commentary inferred" in issue["message"]
    assert not any(i["code"] == "missing_manager" for i in ledger.issues)


def test_section_preference_picks_drivers_over_commentary(tmp_path):
    ledger = Ledger()
    name = "Redwood Logistics Trust"
    path = tmp_path / "manager.pdf"
    drivers = "Gateway Logistics Center was marked up after lease-up completed at rents ahead of plan."
    manager_pdf(
        path,
        [
            name,
            "Portfolio Manager Commentary",
            "The Fund had a good quarter overall and did well.",
            "Key Asset Drivers",
            drivers,
        ],
    )
    sources = dict(root=tmp_path, managers=[(path, pdf_pages(path))])
    funds = [dict(name=name, roles=["largest contributor"], fees=Decimal("0"), fees_id="fee")]
    support = supporting_documents(sources, dict(funds=funds), dict(new=[]), ledger, None)
    assert [p["text"] for p in support[name]] == [drivers]
    assert not any(i["code"] == "manager_extraction" for i in ledger.issues)


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
    text = qualitative_fallback(
        [dict(text="Leasing improved to 97% occupancy. Cedar Ridge was held flat pending expansion.")]
    )
    assert "pending review" in text and "97% occupancy" in text
    assert "Cedar Ridge was held flat pending expansion." in text
    assert qualitative_fallback([dict(text="Return was 9%.")])


def test_source_fallback_and_writer_preserve_identical_scoped_meaning():
    from pmr.verification import semantic_manifest
    from pmr.evidence import digest

    passages = [
        dict(id="risk", text="Refinancing 2020-2021 debt remains a risk.", source=dict(file="deck.pdf", slide=3), qualitative_only=True),
        dict(id="return", text="Broad funds returned 1.0% in the latest quarter.", source=dict(file="deck.pdf", slide=4)),
    ]
    masked, _, _ = prepare(passages)
    writer = validate_sentences(dict(sentences=[dict(text=p["text"], source_id=p["id"]) for p in masked]), passages)
    excerpt = source_excerpt(passages, "Verified source excerpts: ")
    assert "2020-2021" in excerpt["text"]
    assert len(excerpt["numeric_bindings"]) == 2
    keys = ["portfolio", "funds", "sleeves", "activity", "policy", "compliance", "history", "diversification"]
    data = {k: {} for k in keys}
    data.update(client="OTHER", quarter="1Q26", charts=[])
    model_block = dict(type="paragraph", kind="model_prose", text=" ".join(s["text"] for s in writer), numeric_bindings=[b for s in writer for b in s["numeric_bindings"]])
    fallback_block = dict(type="paragraph", kind="source_excerpt", **excerpt)
    signature = lambda block: digest(semantic_manifest(data, [dict(title="Market", blocks=[block])]))
    assert signature(model_block) == signature(fallback_block)
    fallback_block["numeric_bindings"][0]["source_context"] = "A different risk period."
    assert signature(model_block) != signature(fallback_block)


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
        validate_sentences(
            response(masked[0]["text"].replace(required[0], "-" + required[0]), masked[0]["text"]), passages
        )


def test_slots_cannot_borrow_numbers_from_another_source():
    passages = [
        dict(id="a", text="The manager reports 97% occupancy."),
        dict(id="b", text="The manager reports 40% occupancy."),
    ]
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
    sources = dict(
        root=Path("inputs"),
        managers=[(Path("inputs/manager.pdf"), ["Cornrstone Property Fund\nQuarterly review"])],
    )
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
    passages = [
        *PASSAGES,
        dict(id="risks", text="Refinancing pressure remains a risk.", qualitative_only=True),
    ]
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
        validate_sentences(
            dict(sentences=[dict(text="The deck describes repricing.", source_id="source")]), passages
        )


def test_numeric_mask_excludes_punctuation_and_binds_periods():
    from pmr.synthesis import NUMBER

    text = "At 25Q4, forecast 2026-27 is 1.3%, after 2023–2024 repricing. NAV $1,367,035.55."
    assert NUMBER.findall(text) == ["25Q4", "2026-27", "1.3%", "2023–2024", "$1,367,035.55"]
    passage = dict(id="source", text=text)
    masked, _, _ = prepare([passage])
    assert (
        validate_sentences(dict(sentences=[dict(text=masked[0]["text"], source_id="source")]), [passage])[0][
            "text"
        ]
        == text
    )


def test_manager_claim_cannot_be_attributed_to_market_deck():
    class Model:
        provider = "test"

        def ask(self, prompt):
            return response("The market deck reports improved leasing demand.")

    ledger = Ledger()
    assert synthesize(PASSAGES, "Performance drivers for a fund", Model(), ledger) is None
    assert any("attributed to the market deck" in i["message"] for i in ledger.issues)


def test_corrected_negative_return_cannot_rebind_positive_prose(monkeypatch):
    from pmr.synthesis import refresh_market_narrative

    old = dict(id="old", text="The market return was 1.0%.", source=dict(file="deck.pdf", slide=4))
    corrected = dict(id="new", text="The market return was -1.0%.", source=old["source"])
    data = dict(market_passages=[old], narratives={"market": dict(
        text="The market delivered a positive return of 1.0%.",
        source_order=["old"],
        masked_response=dict(sentences=[dict(text="The market delivered a positive return of [[VALUE_A]].", source_id="old")]),
    )})
    monkeypatch.setattr("pmr.synthesis.market_passages", lambda data, ledger: [corrected])
    ledger = Ledger()
    refresh_market_narrative(data, ledger)
    assert "market" not in data["narratives"]
    assert data["market_passages"] == [corrected]
    assert any(i["code"] == "corrected_narrative_review" for i in ledger.issues)


def test_corrected_market_prose_is_rewritten_and_semantically_checked(monkeypatch):
    from pmr.synthesis import refresh_market_narrative

    source = dict(file="deck.pdf", slide=4)
    corrected = dict(id="new", text="The market return was -1.0%.", source=source)
    data = dict(market_passages=[dict(id="old", text="The market return was 1.0%.", source=source)], narratives={"market": {"text": "Stale positive return."}})
    monkeypatch.setattr("pmr.synthesis.market_passages", lambda data, ledger: [corrected])

    class Model:
        provider = "test"
        checks = 0

        def ask(self, prompt):
            if prompt.startswith("CHECK_PARAPHRASES"):
                self.checks += 1
                return dict(supported=[True], reason="Supports negative return")
            return dict(sentences=[dict(text="The market recorded a negative return of [[VALUE_A]].", source_id="new")])

    model = Model()
    refresh_market_narrative(data, Ledger(), model)
    assert model.checks == 1
    assert data["narratives"]["market"]["text"] == "The market recorded a negative return of -1.0%."


def test_unchanged_market_evidence_can_rebind_transient_ids(monkeypatch):
    from pmr.synthesis import refresh_market_narrative

    old = dict(id="old", text="The market return was 1.0%.", source=dict(file="deck.pdf", slide=4))
    new = {**old, "id": "new"}
    data = dict(market_passages=[old], narratives={"market": dict(
        source_order=["old"], masked_response=dict(sentences=[dict(text="The market return was [[VALUE_A]].", source_id="old")]),
    )})
    monkeypatch.setattr("pmr.synthesis.market_passages", lambda data, ledger: [new])
    refresh_market_narrative(data, Ledger())
    assert data["narratives"]["market"]["text"] == "The market return was 1.0%."
