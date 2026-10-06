"""One report model feeds the PDF and an inspectable HTML evidence review."""

from __future__ import annotations

import html
import io
import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import fitz

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)

from .ingest import norm
from .numeric import display, sum_if_known
from .market import observation_sentence
from .appendix import append_exhibits
from .synthesis import source_excerpt
from .visuals import chart_drawing, chart_preview

NAVY = "#1b2a4a"
GOLD = "#c7a14a"


def money(value):
    if value is None:
        return "n/m"
    return f"${number(Decimal(str(value)) / 1_000_000, 1)}M"


def number(value, places=1):
    """Use financial half-up rounding, including values exactly between display ticks."""
    return "n/m" if value is None else display(value, places)


def dollars(value):
    if value is None:
        return "unavailable"
    return ("-$" if value < 0 else "$") + number(abs(value), 0)


def accounting(value):
    if value is None:
        return "unavailable"
    text = number(abs(value), 0)
    return f"({text})" if value < 0 else text


def billions(value):
    return f"${number(Decimal(str(value)) / 1_000_000_000, 2)} billion"


def build_sections(data, sources, ledger):
    p, funds, activity = data["portfolio"], data["funds"], data["activity"]
    if any(p[key] <= 0 for key in ["nav", "plan", "target"]):
        raise ValueError(
            "Required allocation ratios need positive portfolio NAV, plan assets and target; source values are not invented"
        )
    sections = []

    def add(title):
        section = dict(title=title, blocks=[])
        sections.append(section)
        return section

    def para(section, text, ids, kind=None, numeric_bindings=None, style=None):
        block = dict(type="paragraph", text=text, evidence=list(dict.fromkeys(i for i in ids if i)))
        if kind:
            block["kind"] = kind
        if style:
            block["style"] = style
        if numeric_bindings is not None:
            block["numeric_bindings"] = numeric_bindings
        section["blocks"].append(block)

    def table(section, columns, rows, evidence, cell_evidence=None):
        block = dict(type="table", columns=columns, rows=rows, evidence=list(dict.fromkeys(evidence)))
        if cell_evidence:
            block["cell_evidence"] = cell_evidence
        section["blocks"].append(block)

    def derived(key, value, formula, inputs):
        p[key] = value
        p[key + "_id"] = ledger.add(
            value,
            {"kind": "calculation"},
            formula=formula,
            inputs=inputs,
            numeric=dict(
                entity=p["name"],
                metric=key,
                period=data["quarter"],
                unit=(
                    "USD"
                    if key == "approved_total"
                    else "count" if key.endswith("count") or key == "positions" else "%"
                ),
                authority="deterministic calculation",
                permitted_formats=[] if value is None else [str(value), number(value, 1)],
            ),
        )

    open_total = sum_if_known(e["amount"] for e in activity["open"])
    if open_total is None:
        ledger.issue(
            "approved_total_unavailable",
            "Total committed or approved is unavailable until every open IC approval amount is resolved.",
            "blocker",
            evidence=[e["amount_id"] for e in activity["open"] if e["amount"] is None],
        )
    derived(
        "approved_total",
        None if open_total is None else p["commitment"] + open_total,
        "flash commitments + open approvals",
        [p["commitment_id"]] + [e["amount_id"] for e in activity["open"]],
    )
    count_ids = [f["name_id"] for f in funds] + [e["id"] for e in activity["open"]]
    derived(
        "positions",
        len(funds) + len(activity["open"]),
        "count flash investments + count open approvals",
        count_ids,
    )
    derived("funded_count", len(funds), "count flash investments", [f["name_id"] for f in funds])
    scope_ids = [e["id"] for e in activity["scope"]]
    derived(
        "open_count",
        len(activity["open"]),
        "count open approvals",
        [e["id"] for e in activity["open"]] + scope_ids,
    )
    derived(
        "new_count",
        len(activity["new"]),
        "count current-quarter approvals",
        [e["id"] for e in activity["new"]] + scope_ids,
    )
    derived(
        "plan_pct", p["nav"] / p["plan"] * 100, "NAV / total plan assets * 100", [p["nav_id"], p["plan_id"]]
    )
    derived(
        "target_pct",
        p["nav"] / p["target"] * 100,
        "NAV / target allocation * 100",
        [p["nav_id"], p["target_id"]],
    )
    prior_pages = sources["prior"][2]
    prior_file = sources["prior"][1].name
    # Carry forward static mandate history only; quarterly facts are always regenerated.
    overview_page = next((t for t in prior_pages if "retained Vectera" in t), "")
    match = re.search(r"(.+?retained Vectera.*?beginning in \d{4}\.)", overview_page, re.S)
    static_intro = re.sub(r"^.*?Portfolio Overview\s*", "", match[1], flags=re.S).strip() if match else ""
    s = add("Portfolio Overview")
    if static_intro:
        fid = ledger.add(
            static_intro,
            {"file": prior_file, "page": prior_pages.index(overview_page) + 1, "quote": static_intro},
        )
        para(s, re.sub(r"\s+", " ", static_intro), [fid])
    irr_text = "not available" if p["irr"] is None else f"{p['irr']:.1f}%"
    multiple_text = "not available" if p["multiple"] is None else f"{p['multiple']:.2f}x"
    if p["irr"] is not None and p["multiple"] is not None:
        track_record = (
            f"The funded investments have generated a since-inception net IRR of {irr_text} "
            f"and a {multiple_text} net equity multiple."
        )
    else:
        track_record = (
            f"Since-inception net IRR is {irr_text}; the net equity multiple is {multiple_text}. "
            "Missing track-record figures are not reported in the current flash."
        )
    para(
        s,
        (
            f"Since inception, approximately {billions(p['approved_total'])} has been committed or approved for commitment across "
            if p["approved_total"] is not None
            else "Total committed or approved is unavailable pending resolution of an IC amount. The Portfolio comprises "
        )
        + f"{p['positions']} individual investment positions: {len(funds)} funded and carried in the flash, plus "
        f"{len(activity['open'])} open approvals not funded by Quarter-end. " + track_record,
        [
            p[k + "_id"]
            for k in ["approved_total", "positions", "funded_count", "open_count", "irr", "multiple"]
        ],
    )
    allocation_text, allocation_ids = "", []
    if "allocation" in data["policy"]:
        target, low, high = data["policy"]["allocation"]
        allocation_text = (
            f"{data['client']} has allocated {target:.1f}% of total plan assets to real estate, "
            f"with an allowable range of {low:g}-{high:g}%. "
        )
        allocation_ids = [data["policy"]["allocation_id"]]
    para(
        s,
        allocation_text + f"At Quarter-end, portfolio NAV was {billions(p['nav'])}, or {p['plan_pct']:.1f}% of the "
        f"{billions(p['plan'])} total plan and {p['target_pct']:.1f}% of its {billions(p['target'])} target real estate allocation. "
        f"The return objective is to exceed the {p['benchmark']}.",
        allocation_ids + [p[k + "_id"] for k in ["nav", "plan_pct", "plan", "target_pct", "target", "benchmark"]],
    )
    para(
        s,
        f"The Portfolio returned {p['q_net']:.2f}% net during the Quarter and {p['one_net']:.2f}% over one year, "
        f"against {p['benchmark_q']:.2f}% and {p['benchmark_one']:.2f}%, respectively, for the {p['benchmark']}.",
        [p[k + "_id"] for k in ["q_net", "one_net", "benchmark_q", "benchmark_one", "benchmark"]],
    )
    s = add("Investment Guidelines & Fund Statistics")
    stats = [
        ["Funded investments", str(len(funds))],
        ["Approved, not yet funded", str(len(activity["open"]))],
        [
            "Total committed or approved",
            (
                money(p["approved_total"])
                if p["approved_total"] is not None
                else "Unavailable: unresolved IC amount"
            ),
        ],
        ["Flash commitment total", money(p["commitment"])],
        ["Market value (NAV)", money(p["nav"])],
        ["Real estate as % of plan assets", f"{p['plan_pct']:.1f}%"],
        ["NAV as % of target", f"{p['target_pct']:.1f}%"],
        ["Since-inception net IRR", irr_text],
        ["Since-inception net equity multiple", multiple_text],
    ]
    split = " / ".join(
        number(data["sleeves"][s]["nav"] / p["nav"] * 100) + "%" for s in ["Strategic", "Tactical"]
    )
    split_id = ledger.add(
        split,
        {"kind": "calculation"},
        formula="Strategic/Tactical NAV / total NAV * 100",
        inputs=[data["sleeves"][s]["nav_id"] for s in ["Strategic", "Tactical"]] + [p["nav_id"]],
    )
    stats.insert(7, ["Strategic / Tactical split", split])
    stat_ids = [
        p[k + "_id"]
        for k in [
            "funded_count",
            "open_count",
            "approved_total",
            "commitment",
            "nav",
            "plan_pct",
            "target_pct",
            "irr",
            "multiple",
        ]
    ]
    stat_ids.insert(7, split_id)
    table(
        s,
        ["Statistic", "Value"],
        stats,
        [v for k, v in p.items() if k.endswith("_id")] + count_ids + [split_id],
        cell_evidence=[[[identifier], [identifier]] for identifier in stat_ids],
    )
    s = add("Portfolio Managers")
    for i, page in enumerate(prior_pages):
        match = re.search(r"Portfolio Managers\s*(.*?)(?:Vectera Advisors\s*\||$)", page, re.S)
        if match and "@" in match[1]:
            text = match[1].strip()
            fid = ledger.add(text, {"file": prior_file, "page": i + 1, "quote": text})
            lines = re.findall(r"[^@]+@[\w.-]+", re.sub(r"\s+", " ", text))
            for line in lines or [text]:
                para(s, line.strip(), [fid])
            break
    s = add("Annualized Time-Weighted Return")
    s["blocks"].append(
        dict(
            type="chart",
            kind="annual",
            evidence=[v[k] for v in p["annual"] for k in ["value_id", "benchmark_id"]],
        )
    )
    comparisons = [v["value"] > v["benchmark"] for v in p["annual"]]
    annual_summary = (
        "The Portfolio outperformed the " + p["benchmark"] + " across all horizons shown above. "
        if comparisons and all(comparisons)
        else "The chart shows the Portfolio's net time-weighted returns alongside the " + p["benchmark"] + ". "
    )
    annual_summary += f"Over the trailing year, the Portfolio returned {p['one_net']:.2f}% net against {p['benchmark_one']:.2f}% for the benchmark."
    para(s, annual_summary, [p["benchmark_id"], p["one_net_id"], p["benchmark_one_id"]] + [v[k] for v in p["annual"] for k in ["value_id", "benchmark_id"]])
    s = add("Performance Update")
    para(
        s,
        f"The Portfolio generated {money(p['income'])} of gross income and {money(p['appreciation'])} of appreciation. "
        f"Manager fees were {money(p['fees'])}. The Quarter's return was {p['q_gross']:.2f}% gross and {p['q_net']:.2f}% net.",
        [p[k + "_id"] for k in ["income", "appreciation", "fees", "q_gross", "q_net"]],
    )
    featured = sorted(
        (f for f in funds if f["roles"]),
        key=lambda f: (f["contribution"] is None, -(f["contribution"] or 0), f["name"]),
    )
    rows = [
        [
            f["name"],
            "; ".join(f["roles"]),
            accounting(f["income"]),
            accounting(f["appreciation"]),
            accounting(f["fees"]),
            accounting(f["contribution"]),
        ]
        for f in featured
    ]
    table(
        s,
        ["Fund", "Role", "Income", "Apprec.", "Fees", "Contribution"],
        rows,
        [
            f[k + "_id"]
            for f in featured
            for k in ["name", "roles", "income", "appreciation", "fees", "contribution"]
        ],
        cell_evidence=[
            [[f[k + "_id"]] for k in ["name", "roles", "income", "appreciation", "fees", "contribution"]]
            for f in featured
        ],
    )
    s["blocks"][-1]["title"] = "Attribution - Quarterly Dollar Contribution"
    para(
        s,
        "Dollar figures are rounded independently to the nearest dollar; displayed components may not sum exactly.",
        [],
        style="footnote",
    )
    para(
        s,
        " ".join(
            f"{f['name']} was the Portfolio's {' and '.join(f['roles'])}, "
            f"contributing {dollars(f['contribution'])} during the Quarter."
            for f in featured
            if f["contribution"] is not None
        ),
        [f[k + "_id"] for f in featured for k in ["name", "roles", "contribution"]],
    )
    if not data.get("attribution_complete", True):
        para(
            s,
            "Dollar contributor and detractor rankings are unavailable because required cash activity is missing. NAV position rankings require complete NAV data; no partial performance ranking has been substituted.",
            [f["contribution_id"] for f in funds if f["contribution"] is None],
        )
    elif len([f for f in funds if f["contribution"] < 0]) < 2:
        para(
            s,
            "Every other fund contributed positively or had zero dollar contribution during the quarter.",
            [f["contribution_id"] for f in funds],
        )
    if any(f["nav"] is None for f in funds):
        para(
            s,
            "Individual position rankings are unavailable because a funded holding's NAV is missing. The holding remains in the inventory; no partial position ranking has been substituted.",
            [f["nav_id"] for f in funds if f["nav"] is None],
        )
    # Prior narrative is a baseline, never a source of current-period asset drivers.
    match = re.search(r"Portfolio returned\s+([\d.-]+)% net.*?Quarter", overview_page, re.S)
    if match:
        old = float(match[1])
        fid = ledger.add(
            old, {"file": prior_file, "page": prior_pages.index(overview_page) + 1, "quote": match[0]}
        )
        delta = (p["q_net"] - old) * 100
        did = ledger.add(
            delta,
            {"kind": "calculation"},
            formula="(current quarter return - prior displayed quarter return) * 100",
            inputs=[p["q_net_id"], fid],
        )
        para(
            s,
            f"The quarterly net return changed from {old:.2f}% in the prior report to {p['q_net']:.2f}%, "
            f"a change of {delta:+.1f} basis points, using the prior report's displayed precision.",
            [fid, p["q_net_id"], did],
        )
    for sleeve in ["Strategic", "Tactical"]:
        s = add(
            "Strategic Portfolio" if sleeve == "Strategic" else "Tactical and Special Situations Portfolio"
        )
        sl = data["sleeves"][sleeve]
        share = sl["nav"] / p["nav"] * 100
        fid = ledger.add(
            share,
            {"kind": "calculation"},
            formula="sleeve NAV / portfolio NAV * 100",
            inputs=[sl["nav_id"], p["nav_id"]],
        )
        para(
            s,
            f"The {sleeve} sleeve represented {share:.1f}% of portfolio market value and returned {sl['q_net']:.2f}% net during the Quarter.",
            [fid, sl["q_net_id"]],
        )
        for fund in [f for f in funds if f["sleeve"] == sleeve]:
            return_text = (
                f"returned {fund['q_net']:.2f}% net"
                if fund["q_net"] is not None
                else "had a quarterly net return of n/m (not reported in the flash)"
            )
            role = " was the Portfolio's " + " and ".join(fund["roles"]) + "." if fund["roles"] else "."
            text = (
                fund["name"]
                + role
                + f" The Fund {return_text}, with Quarter-end NAV of {money(fund['nav'])} and {number(fund['ltv'])}% LTV."
            )
            ids = [fund[k + "_id"] for k in ["name", "roles", "q_net", "nav", "ltv"]]
            if fund["roles"] and fund["contribution"] is not None:
                fee_text = (
                    f"a fee credit of {dollars(abs(fund['fees']))}"
                    if fund["fees"] < 0
                    else f"fees of {dollars(fund['fees'])}"
                )
                text += f" Income of {dollars(fund['income'])}, appreciation of {dollars(fund['appreciation'])} and {fee_text} resulted in a {dollars(fund['contribution'])} dollar contribution."
                ids += [fund[k + "_id"] for k in ["income", "appreciation", "fees", "contribution"]]
            elif fund["contribution"] is None:
                text += " Cash activity is unavailable; no dollar contribution has been inferred."
            para(s, text, ids)
            if fund["roles"]:
                passages = data["support"].get(fund["name"], [])
                narrative = data.get("narratives", {}).get(fund["name"])
                if narrative:
                    para(
                        s,
                        narrative["text"],
                        narrative["evidence"],
                        kind="model_prose",
                        numeric_bindings=narrative.get("numeric_bindings", []),
                    )
                elif passages:
                    excerpt = source_excerpt(passages)
                    para(s, excerpt["text"], excerpt["evidence"], kind="source_excerpt", numeric_bindings=excerpt["numeric_bindings"])
                if not passages:
                    found = fund["name"] in data["support"]
                    text = (
                        "A current manager report was supplied, but asset-level commentary could not be extracted."
                        if found
                        else (
                            "No matched current manager evidence is available. Unresolved supporting documents require review before absence can be established."
                            if data.get("unmatched_reports")
                            else "No manager report was supplied for this Fund for the Quarter; no asset-level drivers are reported."
                        )
                    )
                    para(s, text, [fund["name_id"]] + data.get("unparsed_reports", {}).get(fund["name"], []))
    s = add("Recent Investment Activity")
    para(
        s,
        (
            f"The Investment Committee approved {len(activity['new'])} new commitments for {data['client']} during the Quarter."
            if activity["new"]
            else "No new commitments were approved for this client during the Quarter."
        ),
        [p["new_count_id"]],
    )
    for e in activity["new"]:
        approved_month = date.fromisoformat(str(e["date"])[:10]).strftime("%B %Y")
        para(
            s,
            f"{e['name']} - {money(e['amount'])}, approved {approved_month}.",
            [e[k] for k in ["id", "amount_id", "date_id", "action_id"]],
        )
        if any(opened["name"] == e["name"] for opened in activity["open"]):
            s["blocks"][-1]["text"] += " Not yet funded at Quarter-end."
            s["blocks"][-1]["evidence"] += [fund["name_id"] for fund in funds]
        s["blocks"][-1]["style"] = "activity_title"
        narrative = data.get("narratives", {}).get(e["name"])
        passages = data["support"].get(e["name"], [])
        if narrative:
            para(
                s,
                narrative["text"],
                narrative["evidence"],
                kind="model_prose",
                numeric_bindings=narrative.get("numeric_bindings", []),
            )
        elif passages:
            excerpt = source_excerpt(passages)
            para(s, excerpt["text"], excerpt["evidence"], kind="source_excerpt", numeric_bindings=excerpt["numeric_bindings"])
    for e in activity["reversed"]:
        explanation = e["recommendation"].split(";", 1)[1].strip() if ";" in e["recommendation"] else ""
        action_text = "lapsed" if e["action"] == "lapsed" else "was " + e["action"]
        para(
            s,
            f"The previously approved {money(e['amount'])} commitment to {e['name']} {action_text} during the Quarter. "
            + (explanation[:1].upper() + explanation[1:] + "." if explanation else ""),
            [e[k] for k in ["id", "amount_id", "action_id", "date_id"]],
        )
    s = add("Market Update")
    narrative = data.get("narratives", {}).get("market")
    if narrative:
        para(
            s,
            narrative["text"],
            narrative["evidence"],
            kind="model_prose",
            numeric_bindings=narrative.get("numeric_bindings", []),
        )
    else:
        bundle = data.get("market_passages", [])
        if bundle:
            excerpt = source_excerpt(bundle, "Market synthesis is pending review. Complete source excerpts: ")
            para(s, excerpt["text"], excerpt["evidence"], kind="source_excerpt", numeric_bindings=excerpt["numeric_bindings"])
        else:
            para(s, "Market narrative is unavailable in this run; source evidence remains available for review.", [])
    available = [c for c in data["charts"] if c["data"]]
    if any(v.get("method") == "axis_read" for c in available for v in c["data"]["series"]):
        para(
            s,
            "Values marked ~ are approximate gridline readings at their declared precision, not exact underlying observations.",
            [c["id"] for c in available],
            style="footnote",
        )
    if data["charts"] and not available:
        para(
            s,
            "Quantitative chart-image extraction is unavailable in this run. The house-view chart images are retained in the review package for inspection; no pixel values have been guessed.",
            [],
        )
    para(
        s,
        f"House-view market indices and the {p['benchmark']} are distinct series; "
        "the client benchmark is used for the return-objective test.",
        [p["benchmark_id"]],
        style="footnote",
    )
    s = add("Allocation Over Time")
    history_ids = [r[k] for r in data["history"] for k in ["quarter_id", "target_id", "nav_id"]]
    para(
        s,
        f"The Portfolio's net asset value has moved from {money(data['history'][0]['nav'] * 1_000_000)} "
        f"at {data['history'][0]['quarter']} to {money(p['nav'])} at Quarter-end, "
        f"against a target allocation of {money(p['target'])}.",
        history_ids + [p["nav_id"], p["target_id"]],
    )
    s["blocks"].append(
        dict(
            type="chart",
            kind="allocation",
            evidence=[r[k] for r in data["history"] for k in ["quarter_id", "target_id", "nav_id"]],
        )
    )
    s = add("Diversification")
    for kind in ["property", "geography"]:
        s["blocks"].append(
            dict(type="chart", kind=kind, evidence=[v["id"] for v in data["diversification"][kind]])
        )
    look = next(v for v in data["diversification"]["geography"] if norm(v["label"]) == "ex us")
    para(
        s,
        f"Look-through Ex-US property exposure was {look['value']:.1f}%. The compliance test uses the separate "
        f"fund-level Ex-US classification, {p['ex_us']:.1f}%. These measure property location and fund classification, respectively.",
        [look["id"], p["ex_us_id"]],
        style="footnote",
    )
    s = add("Compliance")
    table(
        s,
        ["Guideline", "Limit", "Actual", "Status"],
        [[r[k] for k in ["label", "limit", "actual", "status"]] for r in data["compliance"]],
        [fid for r in data["compliance"] for fid in r["evidence"]],
        cell_evidence=[
            [
                r["evidence"],
                r["evidence"],
                r["evidence"],
                [
                    ledger.add(
                        r["status"],
                        {"kind": "calculation"},
                        formula="deterministic guideline comparison: " + r["label"],
                        inputs=r["evidence"],
                    )
                ],
            ]
            for r in data["compliance"]
        ],
    )
    para(
        s,
        "Leverage uses the flash's precomputed sleeve LTV subtotals, rather than averaging individual fund ratios.",
        [v["ltv_id"] for v in data["sleeves"].values()],
    )
    s = add("Disclosure Statements")
    for i, page in enumerate(prior_pages):
        match = re.search(
            r"Disclosure Statements\s*(This Performance.*?)(?=Vectera Advisors\s*\||$)", page, re.S
        )
        if match:
            text = re.sub(r"\s+", " ", match[1]).strip()
            fid = ledger.add(text, {"file": prior_file, "page": i + 1, "quote": match[1]})
            para(s, text, [fid])
            break
    s = add("Appendix A: Quarterly Flash Report")
    para(
        s,
        "The following pages retypeset the supplied flash on portrait Letter paper with single-row table headers. The original PDF is retained separately; the workbook remains authoritative for portfolio calculations.",
        [],
    )
    s["blocks"].extend(data.get("appendix_exhibits", []))
    order = data.get("template", {}).get("section_order", [])
    lookup = {norm(s["title"]): s for s in sections}
    if order and all(norm(title) in lookup for title in order) and len(order) == len(sections):
        sections = [{**lookup[norm(title)], "title": title} for title in order]
    elif order:
        ledger.issue(
            "template_structure",
            "Prior contents differ from supported financial sections; standard structure retained for review",
        )
    return sections


def chart_bytes(kind, data):
    return chart_preview(kind, data)


def styled_text(text, data, section=""):
    """Escape source text before adding presentation-only emphasis."""
    names = [f["name"] for f in data["funds"]] + [e["name"] for rows in data["activity"].values() if isinstance(rows, list) for e in rows if isinstance(e, dict) and "name" in e]
    if section == "Portfolio Managers" and "," in text:
        names.append(text.split(",", 1)[0])
    patterns = [re.escape(name) for name in sorted(set(names), key=len, reverse=True)]
    if section in {"Portfolio Overview", "Market Update", "Allocation Over Time"}:
        patterns += [r"[-+~]?\$[\d,.]+(?:M| billion)?", r"[-+~]?[\d.]+%", r"[\d.]+x\b"]
    if not patterns:
        return html.escape(text)
    matcher = re.compile("|".join(patterns))
    result, end = [], 0
    for match in matcher.finditer(text):
        result.extend([html.escape(text[end:match.start()]), "<b>" + html.escape(match[0]) + "</b>"])
        end = match.end()
    return "".join(result) + html.escape(text[end:])


def market_paragraphs(text):
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    if len(sentences) < 4:
        return [text]
    count = 3 if len(sentences) >= 6 else 2
    return [" ".join(sentences[i * len(sentences) // count:(i + 1) * len(sentences) // count]) for i in range(count)]


def render_pdf(data, sections, path, appendix, approved=False):
    template = data.get("template", {})
    primary = template.get("primary", NAVY)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BodyPMR",
            fontName=template.get("body_font", "Helvetica"),
            fontSize=9,
            leading=13,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TitlePMR",
            fontName="Helvetica-Bold",
            fontSize=23,
            leading=28,
            textColor=colors.HexColor(NAVY),
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="HeadingPMR",
            fontName="Helvetica-Bold",
            fontSize=template.get("heading_size", 15),
            leading=18,
            textColor=colors.HexColor(primary),
            spaceBefore=6,
            spaceAfter=7,
        )
    )
    styles.add(ParagraphStyle(name="CellPMR", fontName="Helvetica", fontSize=7.2, leading=8.6))
    styles.add(ParagraphStyle(name="StatsCellPMR", fontName="Helvetica", fontSize=8, leading=10))
    styles.add(ParagraphStyle(name="ManagerPMR", parent=styles["BodyPMR"], spaceAfter=0))
    styles.add(ParagraphStyle(name="SubheadingPMR", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=colors.HexColor(primary), spaceBefore=6, spaceAfter=5, keepWithNext=True))
    styles.add(ParagraphStyle(name="FootnotePMR", fontName="Helvetica-Oblique", fontSize=7.5, leading=10, spaceAfter=6))
    styles.add(ParagraphStyle(name="CoverQuarter", fontName="Helvetica", fontSize=13, leading=16, textColor=colors.HexColor("#444444")))
    styles.add(ParagraphStyle(name="CoverConfidential", fontName="Helvetica", fontSize=7.5, leading=10, textColor=colors.HexColor("#444444")))
    name_lines = template.get("cover_name_lines", [])
    cover_name = "<br/>".join(html.escape(line) for line in name_lines) if norm(" ".join(name_lines)) == norm(data["portfolio"]["name"]) else html.escape(data["portfolio"]["name"])
    story = [
        Spacer(1, 108),
        Paragraph(cover_name, styles["TitlePMR"]),
        Spacer(1, 8),
        Paragraph("Performance Measurement Report", styles["TitlePMR"]),
        Spacer(1, 8),
        Paragraph(data["period_label"], styles["CoverQuarter"]),
        Spacer(1, 188),
        Paragraph("Prepared by Vectera Advisors", styles["CoverQuarter"]),
        Spacer(1, 10),
        Paragraph("Trade Secret &amp; Confidential", styles["CoverConfidential"]),
        PageBreak(),
    ]
    story += [Paragraph("Contents", styles["HeadingPMR"]), HRFlowable(width="100%", thickness=0.6, color=colors.HexColor(primary), spaceAfter=8)]
    for i, s in enumerate(sections, 1):
        story.append(Paragraph(f"{i}. {html.escape(s['title'])}", styles["BodyPMR"]))
    story.append(PageBreak())
    # Preserve the sample's grouping while allowing text to flow onto extra pages when necessary.
    page_starts = {
        "Portfolio Overview",
        "Annualized Time-Weighted Return",
        "Strategic Portfolio",
        "Tactical and Special Situations Portfolio",
        "Recent Investment Activity",
        "Allocation Over Time",
        "Diversification",
        "Compliance",
    }
    for index, section in enumerate(sections):
        if section["title"] == "Appendix A: Quarterly Flash Report" and appendix:
            continue  # The appendix renderer supplies its heading, not an extra introduction page.
        if index and section["title"] in page_starts:
            story.append(PageBreak())
        subheading = section["title"] in {"Investment Guidelines & Fund Statistics", "Portfolio Managers"}
        story.append(Paragraph(html.escape(section["title"]), styles["SubheadingPMR"] if subheading else styles["HeadingPMR"]))
        if not subheading:
            story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor(primary), spaceAfter=6))
        blocks = list(section["blocks"])
        if section["title"] == "Portfolio Overview" and len(blocks) >= 4:
            blocks = [{**blocks[0], "text": blocks[0]["text"] + " " + blocks[1]["text"]}] + blocks[2:]
        for block in blocks:
            if block["type"] == "paragraph":
                style = styles["ManagerPMR"] if section["title"] == "Portfolio Managers" else styles["FootnotePMR"] if block.get("style") == "footnote" else styles["SubheadingPMR"] if block.get("style") == "activity_title" else styles["BodyPMR"]
                texts = market_paragraphs(block["text"]) if section["title"] == "Market Update" and block.get("kind") in {"model_prose", "source_excerpt"} else [block["text"]]
                story.extend(Paragraph(styled_text(text, data, section["title"]), style) for text in texts)
            elif block["type"] == "chart":
                story.append(chart_drawing(block["kind"], data))
                story.append(Spacer(1, 6))
            else:
                if block.get("title"):
                    story.append(Paragraph(html.escape(block["title"]), styles["SubheadingPMR"]))
                count = len(block["columns"])
                widths = (
                    [111.6, 133.2, 54, 57.6, 43.2, 61.2]
                    if count == 6
                    else [140.4, 97.2, 133.2, 90] if count == 4 else [230.4, 230.4] if count == 2 else [180, 205, 75.8]
                )
                cell_style = styles["CellPMR"] if count == 6 else styles["StatsCellPMR"]
                cells = [
                    [Paragraph(html.escape(str(c)), cell_style) for c in row]
                    for row in [block["columns"]] + block["rows"]
                ]
                table = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#edf0f6")]),
                            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd1dd")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor(NAVY)),
                            ("LEFTPADDING", (0, 0), (-1, -1), 5),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ]
                    )
                )
                # Paragraphs have their own styles, so header color must be set on their text.
                table._cellvalues[0] = [
                    Paragraph(
                        '<font color="white"><b>' + html.escape(str(c)) + "</b></font>", cell_style
                    )
                    for c in block["columns"]
                ]
                story.extend(
                    [
                        (
                            KeepTogether([table])
                            if section["title"] == "Market Update" and len(block["rows"]) <= 8
                            else table
                        ),
                        Spacer(1, 12),
                    ]
                )

    def footer(canvas, doc):
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.grey)
        canvas.drawString(45, 28, "Vectera Advisors | Trade Secret & Confidential")
        canvas.drawRightString(567, 28, f"Page {doc.page}" + (" | DRAFT" if not approved else ""))

    buffer = io.BytesIO()
    SimpleDocTemplate(
        buffer,
        pagesize=(612, 792),
        leftMargin=50.4,
        rightMargin=50.4,
        topMargin=48,
        bottomMargin=48,
        title=f"{data['client']} {data['quarter']} Performance Measurement Report",
        invariant=1,
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    with fitz.open(stream=buffer.getvalue(), filetype="pdf") as result:
        if appendix:
            append_exhibits(result, appendix, approved=approved)
        # Retain ReportLab's invariant document ID instead of generating a random one.
        result.save(path, no_new_id=True)
