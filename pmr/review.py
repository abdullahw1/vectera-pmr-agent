"""Local evidence review, constrained corrections, and hash-bound approval."""

from __future__ import annotations

import html
import json
from pathlib import Path

from .evidence import digest, implementation_hashes


def write_review(output, data, sections, ledger, input_hashes, diagnostics=None, code_hashes=None):
    import hashlib

    assets = {
        str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((output / "assets").glob("*.png"))
        if not p.name.startswith("qa_")
    }
    if (output / "appendix.pdf").exists():
        assets["appendix.pdf"] = hashlib.sha256((output / "appendix.pdf").read_bytes()).hexdigest()
    if not (output / "report.pdf").is_file():
        raise ValueError("Draft PDF is missing; render it before creating the review package")
    assets["report.pdf"] = hashlib.sha256((output / "report.pdf").read_bytes()).hexdigest()
    payload = dict(
        data=data,
        sections=sections,
        ledger=ledger.__dict__,
        input_hashes=input_hashes,
        asset_hashes=assets,
        implementation_hashes=code_hashes if code_hashes is not None else implementation_hashes(),
    )
    payload["draft_hash"] = digest(payload)
    (output / "draft.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    # "<" is escaped so source text inside the payload can never close the script tag.
    encoded = json.dumps(payload, default=str).replace("<", "\\u003c")
    page = (
        (Path(__file__).parent / "web" / "review.html")
        .read_text(encoding="utf-8")
        .replace("__PAYLOAD__", encoded)
    )
    if diagnostics:
        details = (
            "<h2>Run Diagnostics</h2><details><summary>Stages, model usage and cache</summary><pre>"
            + html.escape(json.dumps(diagnostics, indent=2))
            + "</pre></details>"
        )
        page = page.replace("<!--DIAGNOSTICS-->", details)
    (output / "review.html").write_text(page, encoding="utf-8")
    (output / "review.md").write_text(
        "# Review Queue\n\n" + "\n".join(f"- {i['severity'].upper()}: {i['message']}" for i in ledger.issues),
        encoding="utf-8",
    )
    return payload


def approve(output, request):
    if not isinstance(request, dict):
        raise ValueError("Approval request must be an object")
    from .report import build_sections, render_pdf
    from .evidence import Ledger

    payload = json.loads((output / "draft.json").read_text(encoding="utf-8"))
    stored_hash = payload.pop("draft_hash")
    if digest(payload) != stored_hash:
        raise ValueError("Draft contents changed outside the review workflow; regenerate it")
    payload["draft_hash"] = stored_hash
    if request.get("draft_hash") != payload["draft_hash"]:
        raise ValueError("Draft changed; reload and review the current draft")
    if payload.get("implementation_hashes") != implementation_hashes():
        raise ValueError("Implementation changed; regenerate and review the new draft")
    if not str(request.get("reviewer", "")).strip():
        raise ValueError("Reviewer name is required")
    import hashlib

    root = Path(payload["data"]["source_context"]["input_root"])
    current = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }
    if current != payload["input_hashes"]:
        raise ValueError("Source inputs changed; regenerate and review the new draft")
    for path, expected in payload["asset_hashes"].items():
        file = output / path
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            raise ValueError(
                "Draft PDF changed; regenerate and review it" if path == "report.pdf"
                else "Source exhibit or rendered asset changed; regenerate the draft"
            )
    if "report.pdf" not in payload["asset_hashes"]:
        raise ValueError("Draft PDF integrity record is missing; regenerate and review it")
    blockers = [x for x in payload["ledger"]["issues"] if x["severity"] == "blocker"]
    # Chart corrections cannot manufacture an initial extraction: unavailable pixels require a model rerun.
    if blockers:
        raise ValueError("Finalization blocked: " + "; ".join(x["message"] for x in blockers))
    chart_ids = {c["id"] for c in payload["data"]["charts"]}
    confirmed = request.get("confirmed_charts", [])
    if not isinstance(confirmed, list) or any(not isinstance(v, str) for v in confirmed):
        raise ValueError("Confirmed charts must be a list of registered evidence IDs")
    if not chart_ids <= set(confirmed):
        raise ValueError("Confirm all chart-image extractions before finalizing")
    if set(confirmed) - chart_ids:
        raise ValueError("Unknown confirmed chart ID")
    if not isinstance(request.get("corrections", {}), dict):
        raise ValueError("Corrections must be an object")
    if request.get("acknowledged") is not True:
        raise ValueError("Explicit report, evidence and warning review acknowledgment is required")
    from .charts import validate_chart

    for chart in payload["data"]["charts"]:
        validate_chart(chart["data"])
    changed = False
    for fid, record in request.get("corrections", {}).items():
        if (
            fid not in chart_ids
            or not isinstance(record, dict)
            or not isinstance(record.get("reason"), str)
            or not record["reason"].strip()
        ):
            raise ValueError("Chart corrections require a registered ID and a reason")
        correction = validate_chart(record.get("data"))
        for chart in payload["data"]["charts"]:
            if chart["id"] == fid:
                if correction == chart["data"]:
                    continue
                changed = True
                chart["data"] = correction
                payload["data"].setdefault("chart_corrections", {})[fid] = {
                    **record, "reviewer": request["reviewer"],
                }
        fact = payload["ledger"]["facts"][fid]
        fact.setdefault("original_extraction", fact["value"])
        fact["value"] = correction
        fact["reviewer"] = request["reviewer"]
        fact["correction_reason"] = record["reason"]
    # Rebuild from the reviewed report data using the original source context saved at generation.
    ledger = Ledger(**payload["ledger"])
    from .numeric import restore_money

    restore_money(payload["data"])
    from .crosschecks import cap_rate_signals

    payload["data"]["market_signals"] = cap_rate_signals(payload["data"]["charts"], ledger)
    from .synthesis import refresh_market_narrative

    if changed:
        from .models import Model

        model = Model(output / "cache", ledger)
        refresh_market_narrative(payload["data"], ledger, model)
    else:
        refresh_market_narrative(payload["data"], ledger)
    context = payload["data"]["source_context"]
    sources = {"prior": (None, Path(context["prior_file"]), context["prior_pages"])}
    sections = build_sections(payload["data"], sources, ledger)
    from .verification import write_manifests

    appendix = output / context["appendix"] if context["appendix"] else None
    if changed:
        # A correction creates a new draft, never an unseen approved document.
        render_pdf(payload["data"], sections, output / "report.pdf", appendix)
        semantic_hash = write_manifests(output, payload["data"], sections, ledger)
        ledger.save(output / "evidence.json")
        diagnostics = (
            json.loads((output / "diagnostics.json").read_text(encoding="utf-8"))
            if (output / "diagnostics.json").exists() else {}
        )
        diagnostics.update(
            correction_api_calls=model.calls,
            correction_token_usage=model.usage,
            blockers=sum(i["severity"] == "blocker" for i in ledger.issues),
            warnings=sum(i["severity"] == "warning" for i in ledger.issues),
        )
        (output / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
        revised = write_review(
            output, payload["data"], sections, ledger, payload["input_hashes"],
            diagnostics, payload["implementation_hashes"],
        )
        for name in (
            "approval.json", "final_report.pdf", "final_evidence.json",
            "final_sections.json", "final_manifest.json", "final_semantic_manifest.json",
        ):
            (output / name).unlink(missing_ok=True)
        verification = output / "verification.json"
        if verification.exists():
            summary = json.loads(verification.read_text(encoding="utf-8"))
            summary.update(
                semantic_hash=semantic_hash,
                meaning_hash=digest(dict(data=payload["data"], sections=sections)),
                issues=ledger.issues,
            )
            verification.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
        return dict(
            status="review_required", draft_hash=revised["draft_hash"],
            message="Corrections saved as a new DRAFT, not approved. Reload review, inspect the corrected report, "
            "reconfirm charts and acknowledge it before approving.",
        )

    final_semantic_hash = write_manifests(output, payload["data"], sections, ledger, prefix="final_")
    render_pdf(payload["data"], sections, output / "final_report.pdf", appendix, approved=True)
    record = dict(
        draft_hash=payload["draft_hash"],
        reviewer=request["reviewer"],
        acknowledged=True,
        semantic_hash=final_semantic_hash,
        input_hashes=payload["input_hashes"],
        asset_hashes=payload["asset_hashes"],
        implementation_hashes=payload["implementation_hashes"],
        confirmed_charts=sorted(chart_ids),
        corrections={**payload["data"].get("chart_corrections", {}), **request.get("corrections", {})},
    )
    from datetime import datetime, timezone

    record["approved_at"] = datetime.now(timezone.utc).isoformat()
    record["report_sha256"] = hashlib.sha256((output / "final_report.pdf").read_bytes()).hexdigest()
    (output / "approval.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    ledger.save(output / "final_evidence.json")
    (output / "final_sections.json").write_text(json.dumps(sections, indent=2, default=str), encoding="utf-8")
    return dict(status="approved", message="Approved. The final PDF and approval record are saved.")


def serve(output, port, open_browser=False):
    from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(output), **kwargs)

        def do_POST(self):
            if self.path != "/approve":
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                if not 0 < length < 1_000_000:
                    raise ValueError("Invalid request size")
                result = approve(output, json.loads(self.rfile.read(length)))
                status = 200
            except (ValueError, KeyError, TypeError) as error:
                status, result = 400, dict(message=str(error))
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as server:
        url = f"http://127.0.0.1:{server.server_port}/review.html"
        print(f"Review: {url}", flush=True)
        if open_browser:
            import webbrowser

            try:
                webbrowser.open(url)
            except webbrowser.Error:
                print("Could not open a browser automatically; use the review URL above.")
        server.serve_forever()
