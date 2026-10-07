"""Local evidence review, constrained corrections, and hash-bound approval."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from .evidence import digest, implementation_hashes
from .filenames import clear_named_reports, export_report, report_filename


def pdf_preview(output, page=None):
    """Render the protected report itself; preview images never become source facts."""
    import fitz
    import hashlib

    payload = json.loads((output / "draft.json").read_text(encoding="utf-8"))
    if digest({k: v for k, v in payload.items() if k != "draft_hash"}) != payload.get("draft_hash"):
        raise ValueError("Saved draft changed; regenerate before preview")
    approval_file = output / "approval.json"
    approval = json.loads(approval_file.read_text(encoding="utf-8")) if approval_file.is_file() else None
    approved = bool(approval and approval.get("draft_hash") == payload["draft_hash"])
    path = output / ("final_report.pdf" if approved else "report.pdf")
    content = path.read_bytes()
    expected = approval.get("report_sha256") if approved else payload.get("asset_hashes", {}).get("report.pdf")
    if not expected or hashlib.sha256(content).hexdigest() != expected:
        raise ValueError("PDF integrity check failed; regenerate the report")
    try:
        with fitz.open(stream=content, filetype="pdf") as document:
            if page is None:
                first = document[0].rect
                return dict(pages=len(document), width=first.width, height=first.height, approved=approved)
            if isinstance(page, bool) or not isinstance(page, int) or not 0 <= page < len(document):
                raise ValueError("Preview page is outside the report")
            return document[page].get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False).tobytes("png")
    except (fitz.FileDataError, fitz.EmptyFileError) as error:
        raise ValueError("PDF preview is unreadable") from error


def diagnostics_summary(diagnostics):
    provider = {"openai": "OpenAI", "anthropic": "Anthropic"}.get(diagnostics.get("provider"), "No model access")
    usage = diagnostics.get("token_usage", [])
    tokens = sum(u.get("input_tokens", u.get("prompt_tokens", 0)) + u.get("output_tokens", u.get("completion_tokens", 0)) for u in usage)
    rows = [
        ("AI provider", provider),
        ("Writing model", diagnostics.get("model") or "Source excerpts only"),
        ("Chart-reading model", diagnostics.get("vision_model") or "Unavailable"),
        ("API requests", diagnostics.get("api_calls", 0)),
        ("Saved responses reused", diagnostics.get("cache_hits", 0)),
        ("Failed API requests", diagnostics.get("failed_calls", 0)),
        ("Tokens used", f"{tokens:,}"),
    ]
    names = dict(discovery="Find source files", exact_finance="Check financial figures", source_passages="Read source passages", chart_vision="Read charts", cross_source_checks="Compare sources", grounded_narrative="Write and check prose", report_render="Create PDF", source_integrity="Check unchanged inputs")
    stages = "".join(
        f"<li>{html.escape(names.get(s['stage'], s['stage']))}: {html.escape(str(s.get('status', 'unknown')))} ({html.escape(str(s.get('seconds', '?')))} seconds)</li>"
        for s in diagnostics.get("stages", [])
    )
    return '<h2>Run Summary</h2><dl class="run-summary">' + "".join(
        f"<dt>{html.escape(label)}</dt><dd>{html.escape(str(value))}</dd>" for label, value in rows
    ) + '</dl><details><summary>Processing steps</summary><ul>' + stages + '</ul></details><a href="diagnostics.json" target="_blank">Technical log</a>'


def render_review_page(payload, diagnostics=None, approval=None):
    """Serve current presentation without modifying the saved, hash-bound draft."""
    if digest({k: v for k, v in payload.items() if k != "draft_hash"}) != payload.get("draft_hash"):
        raise ValueError("Saved draft changed; regenerate before review")
    data = payload["data"]
    encoded = json.dumps(payload, default=str).replace("<", "\\u003c")
    approved = approval if approval and approval.get("draft_hash") == payload["draft_hash"] else None
    runtime = dict(
        implementation_current=payload.get("implementation_hashes") == implementation_hashes(),
        approval=({k: approved.get(k) for k in ("report_filename", "reviewer", "approved_at")} if approved else None),
    )
    page = (Path(__file__).parent / "web" / "review.html").read_text(encoding="utf-8")
    page = page.replace("__PAYLOAD__", encoded).replace("__RUNTIME__", json.dumps(runtime).replace("<", "\\u003c"))
    page = page.replace('href="report.pdf"', f'href="{report_filename(data["client"], data["quarter"])}"')
    page = page.replace('href="final_report.pdf"', f'href="{report_filename(data["client"], data["quarter"], approved=True)}"')
    return page.replace("<!--DIAGNOSTICS-->", diagnostics_summary(diagnostics or {}))


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
    # A new review package cannot inherit approval from an earlier draft.
    for name in ("approval.json", "final_report.pdf", "final_evidence.json", "final_sections.json"):
        (output / name).unlink(missing_ok=True)
    assets["report.pdf"] = hashlib.sha256((output / "report.pdf").read_bytes()).hexdigest()
    clear_named_reports(output)
    draft_name = export_report(output, data)
    assets[draft_name] = assets["report.pdf"]
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
    page = render_review_page(payload, diagnostics)
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
    final_name = export_report(output, payload["data"], approved=True)
    record = dict(
        draft_hash=payload["draft_hash"],
        reviewer=request["reviewer"],
        report_filename=final_name,
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
    return dict(status="approved", report_filename=final_name, message="Approved. Your final PDF is ready to download.")


def serve(output, port, open_browser=False):
    from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(output), **kwargs)

        def do_GET(self):
            from urllib.parse import urlparse

            path = urlparse(self.path).path
            match = re.fullmatch(r"/pdf-page-(\d+)\.png", path)
            if path == "/pdf-preview.json" or match:
                try:
                    result = pdf_preview(output, int(match[1]) if match else None)
                    content = result if match else json.dumps(result).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png" if match else "application/json")
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(content)
                except (ValueError, KeyError, OSError):
                    self.send_error(404, "PDF preview is not available")
                return
            if path.startswith("/icons/"):
                icons = Path(__file__).parent / "web" / "icons"
                file = (icons / path.removeprefix("/icons/")).resolve()
                if not file.is_relative_to(icons.resolve()) or file.suffix != ".svg" or not file.is_file():
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "image/svg+xml")
                self.end_headers()
                self.wfile.write(file.read_bytes())
                return
            if path == "/review.html" and (output / "draft.json").is_file():
                def record(name):
                    file = output / name
                    return json.loads(file.read_text(encoding="utf-8")) if file.is_file() else None

                page = render_review_page(record("draft.json"), record("diagnostics.json"), record("approval.json"))
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(page.encode("utf-8"))
                return
            super().do_GET()

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
