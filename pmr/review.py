"""Local evidence review, constrained corrections, and hash-bound approval."""
from __future__ import annotations

import html
import json
from pathlib import Path

from .evidence import digest


def write_review(output, data, sections, ledger, input_hashes, diagnostics=None):
    import hashlib
    assets = {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((output / "assets").glob("*.png")) if not p.name.startswith("qa_")}
    if (output / "appendix.pdf").exists():
        assets["appendix.pdf"] = hashlib.sha256((output / "appendix.pdf").read_bytes()).hexdigest()
    payload = dict(data=data, sections=sections, ledger=ledger.__dict__, input_hashes=input_hashes, asset_hashes=assets)
    payload["draft_hash"] = digest(payload)
    (output / "draft.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    encoded = json.dumps(payload, default=str).replace("<", "\\u003c")
    page = r"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PMR Evidence Review</title><style>
*{box-sizing:border-box}body{margin:0;font:14px Arial,sans-serif;color:#242b33;background:#fff}header{padding:20px 28px;border-bottom:1px solid #d9dfe5;display:flex;justify-content:space-between;gap:20px;align-items:center}h1{font-size:21px;margin:0 0 5px}h2{font-size:18px}h3{font-size:15px}button{cursor:pointer;padding:8px 12px;background:#1b2b49;color:white;border:0;border-radius:4px}button:disabled{opacity:.4;cursor:not-allowed}main{display:grid;grid-template-columns:minmax(0,3fr) minmax(300px,2fr);height:calc(100vh - 90px)}article,aside{overflow:auto;padding:24px}aside{border-left:1px solid #d9dfe5;background:#f7f9fa}section{margin-bottom:28px}p{line-height:1.6}.block{padding:10px 0;border-bottom:1px solid #edf0f3;cursor:pointer}.block:hover{background:#f3f6f8}table{border-collapse:collapse;width:100%;font-size:12px}td,th{padding:8px;text-align:left;border-bottom:1px solid #d9dfe5}th{background:#1b2b49;color:white}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}img{max-width:100%}.issue{padding:8px;border-left:3px solid #bc8534;margin:8px 0;background:white}.blocker{border-color:#b03434}.review{border-color:#377969}label{display:block;padding:8px 0}textarea{width:100%;min-height:140px;font:12px monospace}input[type=text]{width:100%;padding:8px}.ok{color:#287454}a{color:#245878}@media(max-width:800px){main{display:block;height:auto}aside{border-left:0;border-top:1px solid #ddd}header{align-items:flex-start;flex-direction:column}}
body{height:100vh;display:grid;grid-template-columns:minmax(0,1fr);grid-template-rows:auto minmax(0,1fr);overflow:hidden}main{height:auto;min-height:0;min-width:0}article,aside{min-height:0;min-width:0}.block{overflow-x:auto}td,th{overflow-wrap:anywhere}@media(max-width:800px){body{height:auto;overflow:auto}main{display:flex;flex-direction:column;height:auto}article,aside{flex:none;overflow:visible;padding:16px}aside{border-top:1px solid #d9dfe5}header{padding:16px}h1{overflow-wrap:anywhere}}
</style><header><div><h1 id="title"></h1><span id="status"></span></div><div><a href="report.pdf" target="_blank">Open PMR</a> &nbsp; <button id="approve">Approve Draft</button></div></header><main><article id="report"></article><aside><h2>Verification</h2><div id="checks"></div><h2>Review Queue</h2><div id="issues"></div><h2>Evidence</h2><div id="evidence">Select a report paragraph, table, or chart.</div><h2>Approval</h2><label>Reviewer <input type="text" id="reviewer"></label><label><input type="checkbox" id="ack"> I reviewed the report, source evidence, and warnings.</label><p id="feedback"></p></aside></main>
<script>const D=PAYLOAD;const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
document.getElementById('title').textContent=D.data.client+' '+D.data.quarter+' Evidence Review';
document.getElementById('status').textContent='Draft '+D.draft_hash.slice(0,12);
const checks=D.ledger.checks.filter(c=>c.severity==='blocker');document.getElementById('checks').innerHTML='<p class="ok">'+checks.filter(c=>c.passed).length+' / '+checks.length+' critical checks passed</p>'+checks.filter(c=>!c.passed).map(c=>'<pre>'+esc(JSON.stringify(c,null,2))+'</pre>').join('');
const acknowledged=new Set();const corrections={};
function queue(){document.getElementById('issues').innerHTML=D.ledger.issues.map(x=>'<div class="issue '+esc(x.severity)+'"><b>'+esc(acknowledged.has(x.fact_id)?'CONFIRMED':x.severity.toUpperCase())+'</b><p>'+esc(x.message)+'</p>'+(x.fact_id?'<button onclick="show([\''+x.fact_id+'\'])">Inspect Chart</button>':'')+'</div>').join('');}queue();
function show(ids){let visited=new Set();function fact(id){if(visited.has(id))return '';visited.add(id);const f=D.ledger.facts[id];if(!f)return '';let out='<h3>'+esc(id)+'</h3><pre>'+esc(JSON.stringify(f,null,2))+'</pre>';if(f.source.asset){out+='<img src="'+esc(f.source.asset)+'"><label>Corrected chart extraction (JSON)</label><textarea id="edit_'+id+'">'+esc(JSON.stringify(corrections[id]||f.value,null,2))+'</textarea><button onclick="confirmChart(\''+id+'\')">Confirm Chart Values</button>';}return out+(f.inputs||[]).map(fact).join('');}const panel=document.getElementById('evidence');panel.innerHTML=ids.map(fact).join('');panel.scrollIntoView({block:'start'});}
window.show=show;window.confirmChart=id=>{try{const v=JSON.parse(document.getElementById('edit_'+id).value);if(!v||!Array.isArray(v.series)||!v.series.length||v.series.some(x=>typeof x.value!=='number'||!Number.isFinite(x.value)))throw Error('Each series requires a finite numeric value.');if(JSON.stringify(v)!==JSON.stringify(D.ledger.facts[id].value)){const reason=prompt('Reason for correction, including the visible label or gridline:');if(!reason||!reason.trim())throw Error('A correction reason is required.');corrections[id]={data:v,reason:reason.trim()};}acknowledged.add(id);document.getElementById('feedback').textContent='Chart confirmed. Corrections will be recorded with approval.';}catch(e){document.getElementById('feedback').textContent=e.message;}};
document.getElementById('report').innerHTML=D.sections.map(s=>'<section><h2>'+esc(s.title)+'</h2>'+s.blocks.map(b=>'<div class="block" onclick="show('+esc(JSON.stringify(b.evidence))+')">'+(b.type==='paragraph'?'<p>'+esc(b.text)+'</p>':b.type==='chart'?'<img src="assets/'+esc(b.kind)+'.png">':'<table><thead><tr>'+b.columns.map(c=>'<th>'+esc(c)+'</th>').join('')+'</tr></thead><tbody>'+b.rows.map(r=>'<tr>'+r.map(c=>'<td>'+esc(c)+'</td>').join('')+'</tr>').join('')+'</tbody></table>')+'</div>').join('')+'</section>').join('');
document.getElementById('approve').onclick=async()=>{const feedback=document.getElementById('feedback');if(!document.getElementById('ack').checked||!document.getElementById('reviewer').value.trim()){feedback.textContent='Enter reviewer name and confirm review first.';return;}try{let r=await fetch('/approve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({draft_hash:D.draft_hash,reviewer:document.getElementById('reviewer').value.trim(),acknowledged:true,confirmed_charts:[...acknowledged],corrections})});let v=await r.json();feedback.textContent=v.message;if(r.ok)document.getElementById('status').textContent='Approved; final report available as final_report.pdf';}catch(e){feedback.textContent='Launch the review server using the README command to record approval.';}};
</script></html>""".replace("PAYLOAD", encoded)
    page = page.replace("fetch('/approve'", "fetch('approve'")
    page = page.replace("'Content-Type':'application/json'", "'Content-Type':'application/json','X-PMR-Token':window.PMR_CSRF||''")
    page = page.replace('corrections[id]||f.value', '(corrections[id]&&corrections[id].data)||f.value')
    page = page.replace('acknowledged.add(id);', "acknowledged.add(id);queue();document.getElementById('status').textContent='Draft '+D.draft_hash.slice(0,12)+'; '+D.ledger.issues.filter(x=>x.severity==='review'&&!acknowledged.has(x.fact_id)).length+' chart confirmations remaining';")
    page = page.replace("feedback.textContent='Enter reviewer name and confirm review first.';return;", "feedback.textContent='Enter reviewer name and confirm review first.';feedback.scrollIntoView({block:'center'});return;")
    page = page.replace('feedback.textContent=v.message;', "feedback.textContent=v.message;feedback.scrollIntoView({block:'center'});")
    page = page.replace("panel.scrollIntoView({block:'start'});", "panel.tabIndex=-1;panel.focus();panel.scrollIntoView({block:'start'});")
    if diagnostics:
        safe = html.escape(json.dumps(diagnostics, indent=2))
        page = page.replace('<h2>Approval</h2>', '<h2>Run Diagnostics</h2><details><summary>Stages, usage and agent timeline</summary><pre>' + safe + '</pre></details><h2>Approval</h2>')
    (output / "review.html").write_text(page, encoding="utf-8")
    (output / "review.md").write_text("# Review Queue\n\n" + "\n".join(
        f"- {i['severity'].upper()}: {i['message']}" for i in ledger.issues), encoding="utf-8")
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
    if not str(request.get("reviewer", "")).strip():
        raise ValueError("Reviewer name is required")
    import hashlib
    root = Path(payload["data"]["source_context"]["input_root"])
    current = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(root.rglob("*")) if p.is_file()}
    if current != payload["input_hashes"]:
        raise ValueError("Source inputs changed; regenerate and review the new draft")
    for path, expected in payload["asset_hashes"].items():
        file = output / path
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            raise ValueError("Source exhibit or rendered asset changed; regenerate the draft")
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
    for fid, record in request.get("corrections", {}).items():
        if fid not in chart_ids or not isinstance(record, dict) or not isinstance(record.get("reason"), str) or not record["reason"].strip():
            raise ValueError("Chart corrections require a registered ID and a reason")
        correction = validate_chart(record.get("data"))
        for chart in payload["data"]["charts"]:
            if chart["id"] == fid:
                chart["data"] = correction
        fact = payload["ledger"]["facts"][fid]
        fact["original_extraction"] = fact["value"]
        fact["value"] = correction
        fact["reviewer"] = request["reviewer"]
        fact["correction_reason"] = record["reason"]
    # Rebuild from the reviewed report data using the original source context saved at generation.
    ledger = Ledger(**payload["ledger"])
    from .numeric import restore_money
    restore_money(payload["data"])
    from .crosschecks import cap_rate_signals
    payload["data"]["market_signals"] = cap_rate_signals(payload["data"]["charts"], ledger)
    context = payload["data"]["source_context"]
    sources = {"prior": (None, Path(context["prior_file"]), context["prior_pages"])}
    sections = build_sections(payload["data"], sources, ledger)
    from .verification import write_manifests
    final_semantic_hash = write_manifests(output, payload["data"], sections, ledger, prefix="final_")
    appendix = output / context["appendix"] if context["appendix"] else None
    render_pdf(payload["data"], sections, output / "final_report.pdf", appendix, approved=True)
    record = dict(draft_hash=payload["draft_hash"], reviewer=request["reviewer"],
                  acknowledged=True, semantic_hash=final_semantic_hash,
                  input_hashes=payload["input_hashes"], asset_hashes=payload["asset_hashes"],
                  confirmed_charts=sorted(chart_ids), corrections=request.get("corrections", {}))
    from datetime import datetime, timezone
    record["approved_at"] = datetime.now(timezone.utc).isoformat()
    record["report_sha256"] = hashlib.sha256((output / "final_report.pdf").read_bytes()).hexdigest()
    (output / "approval.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    ledger.save(output / "final_evidence.json")
    (output / "final_sections.json").write_text(json.dumps(sections, indent=2, default=str), encoding="utf-8")


def serve(output, port, open_browser=False):
    from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(output), **kwargs)
        def do_POST(self):
            if self.path != "/approve":
                self.send_error(404); return
            try:
                length = int(self.headers.get("Content-Length", 0))
                if not 0 < length < 1_000_000:
                    raise ValueError("Invalid request size")
                approve(output, json.loads(self.rfile.read(length)))
                status, message = 200, "Approved. final_report.pdf and approval.json have been saved."
            except (ValueError, KeyError, TypeError) as error:
                status, message = 400, str(error)
            self.send_response(status); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(dict(message=message)).encode())
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
