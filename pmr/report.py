"""One report model feeds the PDF and an inspectable HTML evidence review."""

from __future__ import annotations

import html
import io
import os
import re
import tempfile
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import fitz

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "vectera-matplotlib"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
    HRFlowable,
)

from .ingest import norm
from .numeric import display
from .market import observation_sentence
from .appendix import append_exhibits
from .synthesis import qualitative_fallback

NAVY = "#1b2a4a"
GOLD = "#c8a24b"


def money(value):
    if value is None:
        return "n/m"
    return f"${number(Decimal(str(value)) / 1_000_000, 1)}M"


def number(value, places=1):
    """Use financial half-up rounding, including values exactly between display ticks."""
    return display(value, places)


def dollars(value):
    return ("-$" if value < 0 else "$") + number(abs(value), 0)


def accounting(value):
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

    def para(section, text, ids):
        section["blocks"].append(
            dict(type="paragraph", text=text, evidence=list(dict.fromkeys(i for i in ids if i)))
        )

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
                permitted_formats=[str(value), number(value, 1)],
            ),
        )

    open_total = sum(e["amount"] or 0 for e in activity["open"])
    derived(
        "approved_total",
        p["commitment"] + open_total,
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
    para(
        s,
        f"Since inception, approximately {billions(p['approved_total'])} has been committed or approved for commitment across "
        f"{p['positions']} individual investment positions: {len(funds)} funded and carried in the flash, plus "
        f"{len(activity['open'])} open approvals not funded by Quarter-end. The funded investments have generated "
        f"a since-inception net IRR of {p['irr']:.1f}% and a {p['multiple']:.2f}x net equity multiple.",
        [
            p[k + "_id"]
            for k in ["approved_total", "positions", "funded_count", "open_count", "irr", "multiple"]
        ],
    )
    para(
        s,
        f"At Quarter-end, portfolio NAV was {billions(p['nav'])}, or {p['plan_pct']:.1f}% of the "
        f"{billions(p['plan'])} total plan and {p['target_pct']:.1f}% of its {billions(p['target'])} target real estate allocation.",
        [p[k + "_id"] for k in ["nav", "plan_pct", "plan", "target_pct", "target"]],
    )
    para(
        s,
        f"The Portfolio returned {p['q_net']:.2f}% net during the Quarter and {p['one_net']:.2f}% over one year, "
        f"against {p['benchmark_q']:.2f}% and {p['benchmark_one']:.2f}%, respectively, for the {p['benchmark']}.",
        [p[k + "_id"] for k in ["q_net", "one_net", "benchmark_q", "benchmark_one", "benchmark"]],
    )
    s = add("Investment Guidelines & Fund Statistics")
    if "allocation" in data["policy"]:
        target, low, high = data["policy"]["allocation"]
        para(
            s,
            f"The policy allocation to real estate is {target:g}% of total plan assets, with an allowable range of "
            f"{low:g}-{high:g}%. The return objective is to exceed the {p['benchmark']}.",
            [data["policy"]["allocation_id"], p["benchmark_id"]],
        )
    stats = [
        ["Funded investments", str(len(funds))],
        ["Approved, not yet funded", str(len(activity["open"]))],
        ["Total committed or approved", money(p["approved_total"])],
        ["Flash commitment total", money(p["commitment"])],
        ["Market value (NAV)", money(p["nav"])],
        ["Real estate as % of plan assets", f"{p['plan_pct']:.1f}%"],
        ["NAV as % of target", f"{p['target_pct']:.1f}%"],
        ["Since-inception net IRR", f"{p['irr']:.1f}%"],
        ["Since-inception net equity multiple", f"{p['multiple']:.2f}x"],
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
    table(
        s,
        ["Statistic", "Value"],
        stats,
        [v for k, v in p.items() if k.endswith("_id")] + count_ids + [split_id],
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
    para(
        s,
        f"The chart compares the Portfolio's net time-weighted returns with the {p['benchmark']}.",
        [p["benchmark_id"]],
    )
    s = add("Performance Update")
    para(
        s,
        f"The Portfolio generated {money(p['income'])} of gross income and {money(p['appreciation'])} of appreciation. "
        f"Manager fees were {money(p['fees'])}. The Quarter's return was {p['q_gross']:.2f}% gross and {p['q_net']:.2f}% net.",
        [p[k + "_id"] for k in ["income", "appreciation", "fees", "q_gross", "q_net"]],
    )
    featured = sorted((f for f in funds if f["roles"]), key=lambda f: (-f["contribution"], f["name"]))
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
    para(
        s,
        "Dollar figures are rounded independently to the nearest dollar; displayed components may not sum exactly.",
        [],
    )
    para(
        s,
        " ".join(
            f"{f['name']} was the Portfolio's {' and '.join(f['roles'])}, "
            f"contributing {dollars(f['contribution'])} during the Quarter."
            for f in featured
        ),
        [f[k + "_id"] for f in featured for k in ["name", "roles", "contribution"]],
    )
    if len([f for f in funds if f["contribution"] < 0]) < 2:
        para(
            s,
            "Every other fund contributed positively or had zero dollar contribution during the quarter.",
            [f["contribution_id"] for f in funds],
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
            if fund["roles"]:
                fee_text = (
                    f"a fee credit of {dollars(abs(fund['fees']))}"
                    if fund["fees"] < 0
                    else f"fees of {dollars(fund['fees'])}"
                )
                text += f" Income of {dollars(fund['income'])}, appreciation of {dollars(fund['appreciation'])} and {fee_text} resulted in a {dollars(fund['contribution'])} dollar contribution."
                ids += [fund[k + "_id"] for k in ["income", "appreciation", "fees", "contribution"]]
            para(s, text, ids)
            if fund["roles"]:
                passages = data["support"].get(fund["name"], [])
                narrative = data.get("narratives", {}).get(fund["name"])
                if narrative:
                    para(s, narrative["text"], narrative["evidence"])
                elif passages:
                    if all(p["heading"] == "Unclassified manager page" for p in passages):
                        para(
                            s,
                            "A current manager report was supplied, but its narrative requires review before asset-level commentary can be included.",
                            [p["id"] for p in passages],
                        )
                    else:
                        para(s, qualitative_fallback(passages), [p["id"] for p in passages])
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
                    para(s, text, [fund["name_id"]])
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
            para(
                s,
                "The approval remained open and was not carried as a funded holding at Quarter-end. No performance figures are assigned to this commitment.",
                [e["id"], e["action_id"]] + [fund["name_id"] for fund in funds],
            )
        narrative = data.get("narratives", {}).get(e["name"])
        passages = data["support"].get(e["name"], [])
        if narrative:
            para(s, narrative["text"], narrative["evidence"])
        elif passages:
            para(s, qualitative_fallback(passages), [p["id"] for p in passages])
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
        para(s, narrative["text"], narrative["evidence"])
    else:
        bundle = [p for p in data.get("market_passages", []) if not p.get("qualitative_only")]
        para(
            s,
            (
                "Market synthesis is pending review. Verified source observations: "
                + " ".join(p["text"] for p in bundle)
                if bundle
                else "Market narrative is unavailable in this run; source evidence remains available for review."
            ),
            [p["id"] for p in bundle],
        )
    available = [c for c in data["charts"] if c["data"]]
    if any(v.get("method") == "axis_read" for c in available for v in c["data"]["series"]):
        para(
            s,
            "Values marked ~ are approximate gridline readings at their declared precision, not exact underlying observations.",
            [c["id"] for c in available],
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
    )
    s = add("Allocation Over Time")
    s["blocks"].append(
        dict(
            type="chart",
            kind="allocation",
            evidence=[r[k] for r in data["history"] for k in ["quarter_id", "target_id", "nav_id"]],
        )
    )
    para(
        s,
        f"Quarter-end NAV was {money(p['nav'])} against a target allocation of {money(p['target'])}.",
        [p["nav_id"], p["target_id"]],
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
    )
    s = add("Compliance")
    table(
        s,
        ["Guideline", "Limit", "Actual", "Status"],
        [[r[k] for k in ["label", "limit", "actual", "status"]] for r in data["compliance"]],
        [fid for r in data["compliance"] for fid in r["evidence"]],
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
    primary = data.get("template", {}).get("primary", NAVY)
    plt.rcParams.update(
        {"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False}
    )
    fig, ax = plt.subplots(figsize=(7.1, 3.0))
    if kind == "annual":
        ax.set_title("Annualized Time-Weighted Return (net, %)", pad=30)
        annual = data["portfolio"]["annual"]
        xs = list(range(len(annual)))
        ax.bar([x - 0.18 for x in xs], [v["value"] for v in annual], 0.36, color=primary, label="Portfolio")
        ax.bar(
            [x + 0.18 for x in xs],
            [v["benchmark"] for v in annual],
            0.36,
            color=GOLD,
            label=data["portfolio"]["benchmark"],
        )
        ax.set_xticks(xs, [f"{v['horizon']}-Yr" for v in annual])
        ax.set_ylabel("Net return (%)")
        ax.axhline(0, color="#555555", lw=0.7)
        for container in ax.containers:
            ax.bar_label(container, fmt="%.1f", padding=3, fontsize=8)
        ax.margins(y=0.15)
        ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.2), ncol=2)
    elif kind == "allocation":
        ax.set_title("Real Estate Allocation Over Time")
        rows = data["history"]
        ax.plot(
            [r["quarter"] for r in rows],
            [r["target"] for r in rows],
            color=GOLD,
            marker="o",
            label="Target allocation",
        )
        ax.plot([r["quarter"] for r in rows], [r["nav"] for r in rows], color=NAVY, marker="o", label="NAV")
        ax.set_ylabel("USD million")
        ax.legend(frameon=False)
    else:
        rows = data["diversification"][kind]
        if kind == "property":
            ax.set_title("Property Type Diversification (%)")
            wedges, _ = ax.pie(
                [r["value"] for r in rows], colors=[NAVY, GOLD, "#527c8c", "#897c66", "#65745f", "#a4adb5"]
            )
            ax.legend(
                wedges,
                [f"{r['label']} {r['value']:.1f}%" for r in rows],
                loc="center left",
                bbox_to_anchor=(1, 0.5),
                frameon=False,
                fontsize=8,
            )
        else:
            ax.set_title("Geographic Diversification (%)")
            rows = sorted(rows, key=lambda r: r["value"])
            ax.barh([r["label"] for r in rows], [r["value"] for r in rows], color=NAVY)
            ax.set_xlabel("% of market value")
            for container in ax.containers:
                ax.bar_label(container, fmt="%.1f%%", padding=3, fontsize=8)
            ax.set_xlim(0, max(r["value"] for r in rows) * 1.22)
    ax.grid(axis="x" if kind == "geography" else "y", alpha=0.18)
    ax.set_axisbelow(True)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160)
    plt.close(fig)
    buf.seek(0)
    return buf


def render_pdf(data, sections, path, appendix, approved=False):
    template = data.get("template", {})
    primary = template.get("primary", NAVY)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BodyPMR",
            fontName=template.get("body_font", "Helvetica"),
            fontSize=template.get("body_size", 9.2),
            leading=12,
            spaceAfter=9,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TitlePMR",
            fontName="Helvetica-Bold",
            fontSize=25,
            leading=31,
            textColor=colors.HexColor(NAVY),
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            name="HeadingPMR",
            fontName="Helvetica-Bold",
            fontSize=template.get("heading_size", 15),
            leading=18,
            textColor=colors.HexColor(primary),
            spaceBefore=12,
            spaceAfter=7,
        )
    )
    styles.add(ParagraphStyle(name="CellPMR", fontName="Helvetica", fontSize=7, leading=9))
    story = [
        Spacer(1, 140),
        Paragraph(html.escape(data["portfolio"]["name"]), styles["TitlePMR"]),
        Spacer(1, 25),
        Paragraph("Performance Measurement Report", styles["TitlePMR"]),
        Spacer(1, 20),
        Paragraph(data["period_label"], styles["BodyPMR"]),
        Paragraph("Prepared by Vectera Advisors", styles["BodyPMR"]),
        Paragraph("Trade Secret &amp; Confidential", styles["BodyPMR"]),
        Paragraph(
            "APPROVED" if approved else "DRAFT - pending evidence review and approval", styles["BodyPMR"]
        ),
        PageBreak(),
    ]
    story += [Paragraph("Contents", styles["HeadingPMR"])]
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
        story.append(Paragraph(html.escape(section["title"]), styles["HeadingPMR"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor(NAVY), spaceAfter=8))
        for block in section["blocks"]:
            if block["type"] == "paragraph":
                story.append(Paragraph(html.escape(block["text"]), styles["BodyPMR"]))
            elif block["type"] == "chart":
                story.append(Image(chart_bytes(block["kind"], data), width=495, height=209))
                story.append(Spacer(1, 10))
            else:
                count = len(block["columns"])
                widths = (
                    [110, 135, 60, 60, 55, 75]
                    if count == 6
                    else [125, 105, 170, 95] if count == 4 else [300, 195] if count == 2 else [200, 220, 75]
                )
                cells = [
                    [Paragraph(html.escape(str(c)), styles["CellPMR"]) for c in row]
                    for row in [block["columns"]] + block["rows"]
                ]
                table = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef1f6")]),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor(NAVY)),
                            ("LEFTPADDING", (0, 0), (-1, -1), 5),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                            ("TOPPADDING", (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ]
                    )
                )
                # Paragraphs have their own styles, so header color must be set on their text.
                table._cellvalues[0] = [
                    Paragraph(
                        '<font color="white"><b>' + html.escape(str(c)) + "</b></font>", styles["CellPMR"]
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
        leftMargin=57,
        rightMargin=60,
        topMargin=48,
        bottomMargin=48,
        title=f"{data['client']} {data['quarter']} Performance Measurement Report",
        invariant=1,
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    with fitz.open(stream=buffer.getvalue(), filetype="pdf") as result:
        if appendix:
            append_exhibits(result, appendix, approved=approved)
        result.save(path)
