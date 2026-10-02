"""Local evidence review, constrained corrections, and hash-bound approval."""
from __future__ import annotations

import html
import json
from pathlib import Path

from .evidence import digest


def write_review(output, data, sections, ledger, input_hashes):
    payload = dict(data=data, sections=sections, ledger=ledger.__dict__, input_hashes=input_hashes)
    payload["draft_hash"] = digest(payload)
    (output / "draft.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    encoded = json.dumps(payload, default=str).replace("<", "\\u003c")
    page = r"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PMR Evidence Review</title><style>
*{box-sizing:border-box}body{margin:0;font:14px Arial,sans-serif;color:#242b33;background:#fff}header{padding:20px 28px;border-bottom:1px solid #d9dfe5;display:flex;justify-content:space-between;gap:20px;align-items:center}h1{font-size:21px;margin:0 0 5px}h2{font-size:18px}h3{font-size:15px}button{cursor:pointer;padding:8px 12px;background:#1b2b49;color:white;border:0;border-radius:4px}button:disabled{opacity:.4;cursor:not-allowed}main{display:grid;grid-template-columns:minmax(0,3fr) minmax(300px,2fr);height:calc(100vh - 90px)}article,aside{overflow:auto;padding:24px}aside{border-left:1px solid #d9dfe5;background:#f7f9fa}section{margin-bottom:28px}p{line-height:1.6}.block{padding:10px 0;border-bottom:1px solid #edf0f3;cursor:pointer}.block:hover{background:#f3f6f8}table{border-collapse:collapse;width:100%;font-size:12px}td,th{padding:8px;text-align:left;border-bottom:1px solid #d9dfe5}th{background:#1b2b49;color:white}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}img{max-width:100%}.issue{padding:8px;border-left:3px solid #bc8534;margin:8px 0;background:white}.blocker{border-color:#b03434}.review{border-color:#377969}label{display:block;padding:8px 0}textarea{width:100%;min-height:140px;font:12px monospace}input[type=text]{width:100%;padding:8px}.ok{color:#287454}a{color:#245878}@media(max-width:800px){main{display:block;height:auto}aside{border-left:0;border-top:1px solid #ddd}header{align-items:flex-start;flex-direction:column}}
body{height:100vh;display:grid;grid-template-rows:auto minmax(0,1fr);overflow:hidden}main{height:auto;min-height:0}article,aside{min-height:0}@media(max-width:800px){main{display:flex;flex-direction:column;height:auto}article,aside{flex:1;overflow:auto}aside{border-top:1px solid #d9dfe5}}
</style><header><div><h1 id="title"></h1><span id="status"></span></div><div><a href="report.pdf" target="_blank">Open PMR</a> &nbsp; <button id="approve">Approve Draft</button></div></header><main><article id="report"></article><aside><h2>Verification</h2><div id="checks"></div><h2>Review Queue</h2><div id="issues"></div><h2>Evidence</h2><div id="evidence">Select a report paragraph, table, or chart.</div><h2>Approval</h2><label>Reviewer <input type="text" id="reviewer"></label><label><input type="checkbox" id="ack"> I reviewed the report, source evidence, and warnings.</label><p id="feedback"></p></aside></main>
<script>const D=PAYLOAD;const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
document.getElementById('title').textContent=D.data.client+' '+D.data.quarter+' Evidence Review';
document.getElementById('status').textContent='Draft '+D.draft_hash.slice(0,12);
const checks=D.ledger.checks;document.getElementById('checks').innerHTML='<p class="ok">'+checks.filter(c=>c.passed).length+' / '+checks.length+' checks passed</p>'+checks.filter(c=>!c.passed).map(c=>'<pre>'+esc(JSON.stringify(c,null,2))+'</pre>').join('');
const acknowledged=new Set();const corrections={};
function queue(){document.getElementById('issues').innerHTML=D.ledger.issues.map((x,i)=>'<div class="issue '+esc(x.severity)+'"><b>'+esc(x.severity.toUpperCase())+'</b><p>'+esc(x.message)+'</p>'+(x.fact_id?'<button onclick="show([\''+x.fact_id+'\'])">Inspect Chart</button>':'')+'</div>').join('');}queue();
function show(ids){let visited=new Set();function fact(id){if(visited.has(id))return '';visited.add(id);const f=D.ledger.facts[id];if(!f)return '';let out='<h3>'+esc(id)+'</h3><pre>'+esc(JSON.stringify(f,null,2))+'</pre>';if(f.source.asset){out+='<img src="'+esc(f.source.asset)+'"><label>Corrected chart extraction (JSON)</label><textarea id="edit_'+id+'">'+esc(JSON.stringify(corrections[id]||f.value,null,2))+'</textarea><button onclick="confirmChart(\''+id+'\')">Confirm Chart Values</button>';}return out+(f.inputs||[]).map(fact).join('');}const panel=document.getElementById('evidence');panel.innerHTML=ids.map(fact).join('');panel.scrollIntoView({block:'start'});}
window.show=show;window.confirmChart=id=>{try{const v=JSON.parse(document.getElementById('edit_'+id).value);if(!v||!Array.isArray(v.series)||!v.series.length||v.series.some(x=>typeof x.value!=='number'||!Number.isFinite(x.value)))throw Error('Each series requires a finite numeric value.');corrections[id]=v;acknowledged.add(id);document.getElementById('feedback').textContent='Chart confirmed. Corrections will be recorded with approval.';}catch(e){document.getElementById('feedback').textContent=e.message;}};
document.getElementById('report').innerHTML=D.sections.map(s=>'<section><h2>'+esc(s.title)+'</h2>'+s.blocks.map(b=>'<div class="block" onclick="show('+esc(JSON.stringify(b.evidence))+')">'+(b.type==='paragraph'?'<p>'+esc(b.text)+'</p>':b.type==='chart'?'<img src="assets/'+esc(b.kind)+'.png">':'<table><thead><tr>'+b.columns.map(c=>'<th>'+esc(c)+'</th>').join('')+'</tr></thead><tbody>'+b.rows.map(r=>'<tr>'+r.map(c=>'<td>'+esc(c)+'</td>').join('')+'</tr>').join('')+'</tbody></table>')+'</div>').join('')+'</section>').join('');
document.getElementById('approve').onclick=async()=>{const feedback=document.getElementById('feedback');if(!document.getElementById('ack').checked||!document.getElementById('reviewer').value.trim()){feedback.textContent='Enter reviewer name and confirm review first.';return;}try{let r=await fetch('/approve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({draft_hash:D.draft_hash,reviewer:document.getElementById('reviewer').value.trim(),confirmed_charts:[...acknowledged],corrections})});let v=await r.json();feedback.textContent=v.message;if(r.ok)document.getElementById('status').textContent='Approved; final report available as final_report.pdf';}catch(e){feedback.textContent='Launch the review server using the README command to record approval.';}};
</script></html>""".replace("PAYLOAD", encoded)
    (output / "review.html").write_text(page, encoding="utf-8")
    return payload


def approve(output, request):
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
    blockers = [x for x in payload["ledger"]["issues"] if x["severity"] == "blocker"]
    # Chart corrections cannot manufacture an initial extraction: unavailable pixels require a model rerun.
    if blockers:
        raise ValueError("Finalization blocked: " + "; ".join(x["message"] for x in blockers))
    chart_ids = {c["id"] for c in payload["data"]["charts"]}
    if not chart_ids <= set(request.get("confirmed_charts", [])):
        raise ValueError("Confirm all chart-image extractions before finalizing")
    for fid, correction in request.get("corrections", {}).items():
        if fid not in chart_ids or not isinstance(correction, dict) or not correction.get("series"):
            raise ValueError("Corrections must refer to extracted charts and contain series")
        for value in correction["series"]:
            import math
            if not isinstance(value.get("value"), (float, int)) or not math.isfinite(value["value"]):
                raise ValueError("Chart values must be finite numbers")
        for chart in payload["data"]["charts"]:
            if chart["id"] == fid:
                chart["data"] = correction
        fact = payload["ledger"]["facts"][fid]
        fact["original_extraction"] = fact["value"]
        fact["value"] = correction
        fact["reviewer"] = request["reviewer"]
    # Rebuild from the reviewed report data using the original source context saved at generation.
    ledger = Ledger(**payload["ledger"])
    context = payload["data"]["source_context"]
    sources = {"prior": (None, Path(context["prior_file"]), context["prior_pages"])}
    sections = build_sections(payload["data"], sources, ledger)
    appendix = output / context["appendix"] if context["appendix"] else None
    render_pdf(payload["data"], sections, output / "final_report.pdf", appendix, approved=True)
    record = dict(draft_hash=payload["draft_hash"], reviewer=request["reviewer"],
                  confirmed_charts=sorted(chart_ids), corrections=request.get("corrections", {}))
    from datetime import datetime, timezone
    record["approved_at"] = datetime.now(timezone.utc).isoformat()
    record["report_sha256"] = hashlib.sha256((output / "final_report.pdf").read_bytes()).hexdigest()
    (output / "approval.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    ledger.save(output / "final_evidence.json")
    (output / "final_sections.json").write_text(json.dumps(sections, indent=2), encoding="utf-8")


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
