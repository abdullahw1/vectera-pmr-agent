"""Orchestrate extraction, validation, evidence, draft generation and review."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .evidence import Ledger, digest
from .finance import build_financials, commitments
from .ingest import discover, quarter
from .models import Model
from .narrative import supporting_documents, deck_evidence, allocation_history
from .report import build_sections, render_pdf, chart_bytes
from .review import write_review
from .template import extract_template


def generate(root: Path, output: Path, client: str, period: str):
    requested = quarter(period)
    if not requested:
        raise ValueError("Quarter must be in 4Q25-style format")
    output.mkdir(parents=True, exist_ok=True)
    ledger = Ledger()
    sources = discover(root, client, requested, ledger)
    data = build_financials(sources, requested, client, ledger)
    data["template"] = extract_template(sources["prior"][1], ledger)
    data.update(client=client, quarter=period.upper(),
                period_label=["First", "Second", "Third", "Fourth"][requested[1] - 1] + f" Quarter {requested[0]}")
    data["activity"] = commitments(sources, requested, client, data["funds"], ledger)
    model = Model(output / "cache", ledger)
    data["support"] = supporting_documents(sources, data, data["activity"], ledger, model)
    data["slides"], data["charts"] = deck_evidence(sources["deck"], output, ledger, model)
    data["history"] = allocation_history(sources["history"], requested, ledger)
    data["source_context"] = dict(prior_file=sources["prior"][1].name, prior_pages=sources["prior"][2],
                                   appendix="appendix.pdf" if sources["appendix"] else None,
                                   input_root=str(root.resolve()))
    if sources["appendix"]:
        (output / "appendix.pdf").write_bytes(sources["appendix"].read_bytes())
    sections = build_sections(data, sources, ledger)
    assets = output / "assets"; assets.mkdir(exist_ok=True)
    for kind in ["annual", "allocation", "property", "geography"]:
        (assets / (kind + ".png")).write_bytes(chart_bytes(kind, data).getvalue())
    render_pdf(data, sections, output / "report.pdf", sources["appendix"])
    ledger.save(output / "evidence.json")
    input_hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(root.rglob("*")) if p.is_file()}
    payload = write_review(output, data, sections, ledger, input_hashes)
    # Runtime paths and model-selected wording are not part of financial reproducibility.
    financial_signature = {key: data[key] for key in ["portfolio", "funds", "sleeves", "activity", "policy", "compliance", "history", "diversification"]}
    financial_signature["section_order"] = [s["title"] for s in sections]
    summary = dict(client=client, quarter=period.upper(), meaning_hash=digest(dict(data=data, sections=sections)),
                   financial_hash=digest(financial_signature),
                   source_hashes=input_hashes, checks_passed=sum(c["passed"] for c in ledger.checks),
                   checks_total=len(ledger.checks), issues=ledger.issues,
                   ranked_funds=[dict(name=f["name"], roles=f["roles"], contribution=f["contribution"], nav=f["nav"])
                                 for f in data["funds"] if f["roles"]],
                   model_provider=model.provider, model_name=model.name if model.provider else None,
                   api_calls=model.calls, api_usage=model.usage)
    (output / "verification.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return payload, summary
