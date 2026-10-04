"""Orchestrate extraction, validation, evidence, draft generation and review."""

from __future__ import annotations

import hashlib
import json
import time
from contextlib import contextmanager
from pathlib import Path

from .evidence import Ledger, digest, implementation_hashes
from .finance import build_financials, commitments
from .ingest import discover, quarter
from .models import Model
from .narrative import supporting_documents, deck_evidence, allocation_history
from .report import build_sections, render_pdf, chart_bytes
from .review import write_review
from .template import extract_template
from .synthesis import build_narratives
from .verification import write_manifests
from .crosschecks import supporting_checks, cap_rate_signals
from .appendix import register_exhibits
from .filenames import clear_named_reports


def generate(root: Path, output: Path, client: str, period: str):
    requested = quarter(period)
    if not requested:
        raise ValueError("Quarter must be in 4Q25-style format")
    output.mkdir(parents=True, exist_ok=True)
    clear_named_reports(output)
    # A regenerated draft must not leave a stale approved report beside it.
    for name in [
        "final_report.pdf",
        "approval.json",
        "final_evidence.json",
        "final_sections.json",
        "final_manifest.json",
        "final_semantic_manifest.json",
    ]:
        if (output / name).exists():
            (output / name).unlink()
    ledger = Ledger(reporting_period=period.upper())

    def source_hashes():
        return {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*"))
            if p.is_file()
        }

    input_hashes = source_hashes()
    code_hashes = implementation_hashes()
    stages = []

    def progress():
        temporary = output / "progress.tmp"
        temporary.write_text(json.dumps(dict(stages=stages)), encoding="utf-8")
        temporary.replace(output / "progress.json")

    @contextmanager
    def stage(name):
        started = time.monotonic()
        record = dict(stage=name, status="running")
        stages.append(record)
        progress()
        try:
            yield
            record["status"] = "completed"
        except Exception:
            record["status"] = "failed"
            raise
        finally:
            record["seconds"] = round(time.monotonic() - started, 3)
            progress()
            if record["status"] == "failed":
                (output / "diagnostics.json").write_text(
                    json.dumps(dict(status="blocked", stages=stages), indent=2), encoding="utf-8"
                )

    with stage("discovery"):
        sources = discover(root, client, requested, ledger)
    with stage("exact_finance"):
        data = build_financials(sources, requested, client, ledger)
    data["template"] = extract_template(sources["prior"][1], ledger)
    data.update(
        client=client,
        quarter=period.upper(),
        period_label=["First", "Second", "Third", "Fourth"][requested[1] - 1] + f" Quarter {requested[0]}",
    )
    data["activity"] = commitments(sources, requested, client, data["funds"], ledger)
    model = Model(output / "cache", ledger)
    with stage("source_passages"):
        data["support"] = supporting_documents(sources, data, data["activity"], ledger, model)
    with stage("chart_vision"):
        data["slides"], data["charts"] = deck_evidence(sources["deck"], output, ledger, model)
    data["history"] = allocation_history(sources["history"], requested, ledger)
    with stage("cross_source_checks"):
        supporting_checks(sources, data, ledger)
        data["market_signals"] = cap_rate_signals(data["charts"], ledger)
    with stage("grounded_narrative"):
        data["narratives"] = build_narratives(data, model, ledger)
    data["source_context"] = dict(
        prior_file=sources["prior"][1].name,
        prior_pages=sources["prior"][2],
        appendix="appendix.pdf" if sources["appendix"] else None,
        input_root=str(root.resolve()),
    )
    if sources["appendix"]:
        (output / "appendix.pdf").write_bytes(sources["appendix"].read_bytes())
        data["appendix_exhibits"] = register_exhibits(sources["appendix"], ledger)
    sections = build_sections(data, sources, ledger)
    assets = output / "assets"
    assets.mkdir(exist_ok=True)
    for kind in ["annual", "allocation", "property", "geography"]:
        (assets / (kind + ".png")).write_bytes(chart_bytes(kind, data).getvalue())
    with stage("report_render"):
        render_pdf(data, sections, output / "report.pdf", sources["appendix"])
    semantic_hash = write_manifests(output, data, sections, ledger)
    diagnostics = dict(
        stages=stages,
        provider=model.provider,
        model=model.name if model.provider else None,
        vision_model=model.vision_name if model.provider else None,
        api_calls=model.calls,
        token_usage=model.usage,
        cache_hits=model.cache_hits,
        cache_misses=model.cache_misses,
        failed_calls=model.failures,
        blockers=sum(i["severity"] == "blocker" for i in ledger.issues),
        warnings=sum(i["severity"] == "warning" for i in ledger.issues),
        review_items=sum(i["severity"] == "review" for i in ledger.issues),
    )
    (output / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    ledger.save(output / "evidence.json")
    with stage("source_integrity"):
        if source_hashes() != input_hashes:
            raise ValueError(
                "Source files changed during generation; regenerate from an unchanged input package"
            )
        if implementation_hashes() != code_hashes:
            raise ValueError("Implementation changed during generation; regenerate the draft")
    payload = write_review(output, data, sections, ledger, input_hashes, diagnostics, code_hashes)
    # Runtime paths and model-selected wording are not part of financial reproducibility.
    financial_signature = {
        key: data[key]
        for key in [
            "portfolio",
            "funds",
            "sleeves",
            "activity",
            "policy",
            "compliance",
            "history",
            "diversification",
        ]
    }
    financial_signature["section_order"] = [s["title"] for s in sections]
    summary = dict(
        client=client,
        quarter=period.upper(),
        meaning_hash=digest(dict(data=data, sections=sections)),
        semantic_hash=semantic_hash,
        financial_hash=digest(financial_signature),
        source_hashes=input_hashes,
        implementation_hashes=code_hashes,
        checks_passed=sum(c["passed"] for c in ledger.checks if c["severity"] == "blocker"),
        checks_total=sum(c["severity"] == "blocker" for c in ledger.checks),
        supporting_checks_failed=sum(not c["passed"] for c in ledger.checks if c["severity"] == "warning"),
        issues=ledger.issues,
        ranked_funds=[
            dict(name=f["name"], roles=f["roles"], contribution=f["contribution"], nav=f["nav"])
            for f in data["funds"]
            if f["roles"]
        ],
        model_provider=model.provider,
        model_name=model.name if model.provider else None,
        api_calls=model.calls,
        api_usage=model.usage,
    )
    (output / "verification.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return payload, summary
