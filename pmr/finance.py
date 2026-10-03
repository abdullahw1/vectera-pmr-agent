"""Deterministic financial rules, approval state and source-precedence checks."""
from __future__ import annotations

import re
from datetime import datetime

from .ingest import Sheet, bounds, entity, norm, quarter
from .numeric import MONEY_HEADERS, currency


def get(sheet, row, headers, key, *, optional=False, blank_zero=False):
    index = headers.get(norm(key))
    if index is None:
        if optional:
            return None, None
        raise ValueError(f"Column {key!r} missing in {sheet.ws.title}")
    if optional and row[index].value is None:
        return None, None
    return sheet.number(row[index], blank_zero=blank_zero, monetary=norm(key) in MONEY_HEADERS, metric=key)


def policy_from_prior(prior, ledger):
    _, path, pages = prior
    policy = {}
    patterns = {
        "sector": r"(?:<=|≤)\s*([\d.]+)%\s*per sector",
        "ex_us": r"(?:<=|≤)\s*([\d.]+)%\s*Ex-US",
        "leverage": r"(?:<=|≤)\s*([\d.]+)%\s*/\s*([\d.]+)%",
        "allocation": r"allocated\s+([\d.]+)%.*?allowable range of\s+([\d.]+)[–-]([\d.]+)%",
    }
    for key, pattern in patterns.items():
        for i, text in enumerate(pages):
            match = re.search(pattern, text, re.S | re.I)
            if match:
                values = [float(v) for v in match.groups()]
                policy[key] = values
                policy[key + "_id"] = ledger.add(values, {"file": path.name, "page": i + 1, "quote": match[0]})
                break
        if key not in policy:
            ledger.issue("policy_missing", f"Cannot extract {key} guideline from prior PMR", "blocker")
    return policy


def build_financials(sources, requested, client, ledger):
    book, path = sources["book"], sources["flash"]
    sheets = {name: Sheet(path, book[name], ledger) for name in book.sheetnames}
    funding = sheets["FundingStatus(Agg)"]
    _, fh = funding.headers()
    cash = sheets["CashActivity(Agg)"]
    _, ch = cash.headers()
    returns = sheets["ReturnsMultiples(Agg)"]
    _, rh = returns.headers(grouped=True)
    total_label = "Vectera Initiated Investments"
    total = funding.find(total_label, numeric=True)
    portfolio = {"name": sources["name"], "name_id": sources["name_id"]}
    for key, header in {"nav": "Market Value ($)", "commitment": "Commitment Amount",
                        "funded": "Funded Amount", "unfunded": "Unfunded Commitments"}.items():
        portfolio[key], portfolio[key + "_id"] = get(funding, total, fh, header)
    # Composition values are located by their labels, not the investment schedule.
    for label, key in [("Total Plan Assets", "plan"), ("Allocation", "target")]:
        label_cell = next(c for row in funding.rows() for c in row if norm(c.value) == norm(label))
        cell = funding.ws.cell(label_cell.row + 1, label_cell.column)
        portfolio[key], portfolio[key + "_id"] = funding.number(cell, monetary=True, metric=label, entity_name=sources["name"])
    # FundingStatus explicitly owns total-portfolio trailing returns (§1.9).
    header = next(r for r in funding.rows() if norm(r[0].value) == "performance summary")
    lower = funding.rows()[header[0].row]
    # A duplicated portfolio row also exists below the schedule; identify this row by its block.
    # find() is intentionally strict elsewhere; this summary selection is constrained by its header.
    summary = next(r for r in funding.rows() if r[0].row > header[0].row + 1
                   and norm(r[0].value) == norm(sources["name"] + " Portfolio"))
    group = ""
    for i, c in enumerate(header):
        if c.value is not None:
            group = norm(c.value)
        if norm(lower[i].value) == "tnet":
            key = "q_net" if group.startswith("quarter") else "one_net" if group.startswith("1 year") else None
            if key:
                portfolio[key], portfolio[key + "_id"] = funding.number(summary[i], metric=group + " " + str(lower[i].value))
        if norm(lower[i].value) == "tgrs" and group.startswith("quarter"):
            portfolio["q_gross"], portfolio["q_gross_id"] = funding.number(summary[i], metric=group + " gross return")
    funded_rows, sleeve = [], None
    sleeve_labels = {norm("Strategic Investments"): "Strategic", norm("Tactical Investments"): "Tactical"}
    start, _ = funding.headers()
    for row in funding.rows():
        if row[0].row <= start:
            continue
        label = str(row[0].value or "")
        if norm(label) in sleeve_labels:
            sleeve = sleeve_labels[norm(label)]
            if any(isinstance(c.value, (int, float)) for c in row[1:]):
                sleeve = None
            continue
        if sleeve and label and isinstance(row[fh[norm("Market Value ($)")]].value, (int, float)):
            funded_rows.append((sleeve, row))
    funds, sleeves = [], {}
    canonical = [entity(row[0].value) for _, row in funded_rows]
    if len(canonical) != len(set(canonical)):
        raise ValueError("Ambiguous canonical fund identities in flash")
    for sleeve, row in funded_rows:
        label = str(row[0].value)
        fund = {"name": label, "name_id": funding.fact(row[0]), "sleeve": sleeve, "roles": []}
        for key, header in [("nav", "Market Value ($)"), ("commitment", "Commitment Amount"),
                            ("funded", "Funded Amount"), ("unfunded", "Unfunded Commitments")]:
            fund[key], fund[key + "_id"] = get(funding, row, fh, header)
        cr = cash.find(label, numeric=True)
        for key, header in {"beginning": "Beginning Market Value ($)", "contributions": "Contributions",
                            "distributions": "Distributions", "withdrawals": "Withdrawals",
                            "income": "Gross Income", "fees": "Manager Fees", "appreciation": "Appreciation",
                            "ending": "Market Value ($)", "ltv": "LTV"}.items():
            fund[key], fund[key + "_id"] = get(cash, cr, ch, header, blank_zero=key in {
                "contributions", "distributions", "withdrawals"})
        fund["contribution"] = fund["income"] + fund["appreciation"] - fund["fees"]
        fund["contribution_id"] = ledger.add(fund["contribution"], {"file": path.name, "sheet": cash.ws.title},
                                             formula="income + appreciation - fees",
                                             inputs=[fund[k + "_id"] for k in ["income", "appreciation", "fees"]])
        rolled = fund["beginning"] + fund["contributions"] - fund["distributions"] - fund["withdrawals"] + fund["contribution"]
        ledger.check(label + " cash roll-forward", rolled, fund["ending"])
        ledger.check(label + " cross-sheet NAV", fund["ending"], fund["nav"])
        rr = returns.find(label, numeric=True)
        for key, header in [("q_net", "Quarter NET"), ("irr", "NET IRR"), ("multiple", "Net Multiple")]:
            # Single-level labels do not have a second-level subheader.
            column = next((v for h, v in rh.items() if h == norm(header)), None)
            if column is None:
                column = next(v for h, v in rh.items() if h.startswith(norm(header)))
            if rr[column].value is None:
                fund[key], fund[key + "_id"] = None, None
            else:
                fund[key], fund[key + "_id"] = returns.number(rr[column], metric=header)
        funds.append(fund)
    for sleeve in sorted(set(f["sleeve"] for f in funds)):
        label = sleeve + " Investments"
        fr, cr, rr = funding.find(label, numeric=True), cash.find(label, numeric=True), returns.find(label, numeric=True)
        data = {}
        for key, sheet, row, headers, header in [
            ("nav", funding, fr, fh, "Market Value ($)"), ("ltv", cash, cr, ch, "LTV"),
            ("q_net", returns, rr, rh, "Quarter NET")]:
            data[key], data[key + "_id"] = get(sheet, row, headers, header)
        members = [f for f in funds if f["sleeve"] == sleeve]
        ledger.check(sleeve + " NAV footing", sum(f["nav"] for f in members), data["nav"])
        for key, header in [("income", "Gross Income"), ("fees", "Manager Fees"), ("appreciation", "Appreciation"),
                            ("beginning", "Beginning Market Value ($)"), ("contributions", "Contributions"),
                            ("distributions", "Distributions"), ("withdrawals", "Withdrawals")]:
            value, identifier = get(cash, cr, ch, header)
            ledger.check(sleeve + " " + key + " footing", sum(f[key] for f in members), value)
        sleeves[sleeve] = data
    ledger.check("Portfolio NAV footing", sum(s["nav"] for s in sleeves.values()), portfolio["nav"])
    ledger.check("Commitment footing", sum(f["commitment"] for f in funds), portfolio["commitment"])
    for key in ["funded", "unfunded"]:
        ledger.check(key + " footing", sum(f[key] for f in funds), portfolio[key],
                     evidence=[f[key + "_id"] for f in funds] + [portfolio[key + "_id"]])
    for key, header in [("income", "Gross Income"), ("fees", "Manager Fees"), ("appreciation", "Appreciation"),
                        ("beginning", "Beginning Market Value ($)"), ("contributions", "Contributions"),
                        ("distributions", "Distributions"), ("withdrawals", "Withdrawals")]:
        portfolio[key], portfolio[key + "_id"] = get(cash, cash.find(total_label, numeric=True), ch, header)
        ledger.check("Portfolio " + key + " footing", sum(f[key] for f in funds), portfolio[key])
    ledger.check("Portfolio cash roll-forward", portfolio["beginning"] + portfolio["contributions"] -
                 portfolio["distributions"] - portfolio["withdrawals"] + portfolio["income"] +
                 portfolio["appreciation"] - portfolio["fees"], portfolio["nav"])
    for row in cash.rows():
        if norm(row[0].value) == norm("Realized Vectera Initiated Investments"):
            observed = {}
            refs = []
            for key, header in [("beginning", "Beginning Market Value ($)"), ("contributions", "Contributions"),
                                ("distributions", "Distributions"), ("withdrawals", "Withdrawals"),
                                ("income", "Gross Income"), ("appreciation", "Appreciation"),
                                ("fees", "Manager Fees"), ("ending", "Market Value ($)")]:
                observed[key], fid = get(cash, row, ch, header, blank_zero=key in {"contributions", "distributions", "withdrawals"})
                refs.append(fid)
            rolled = observed["beginning"] + observed["contributions"] - observed["distributions"] - observed["withdrawals"] + observed["income"] + observed["appreciation"] - observed["fees"]
            ledger.check("Out-of-portfolio realized-only roll-forward", rolled, observed["ending"], severity="warning", evidence=refs)
    tr = returns.find(total_label, numeric=True)
    for key, header in [("irr", "NET IRR"), ("multiple", "Net Multiple")]:
        portfolio[key], portfolio[key + "_id"] = get(returns, tr, rh, header)
    benchmark_row = next(r for r in returns.rows() if isinstance(r[0].value, str) and "benchmark" in r[0].value.lower())
    portfolio["benchmark"] = benchmark_row[0].value
    portfolio["benchmark_id"] = returns.fact(benchmark_row[0])
    portfolio["benchmark_q"], portfolio["benchmark_q_id"] = get(returns, benchmark_row, rh, "Quarter NET")
    annual = sheets["AnnReturns(Agg)"]
    _, ah = annual.headers(grouped=True)
    ar, br = annual.find(sources["name"] + " Portfolio"), annual.find(portfolio["benchmark"])
    portfolio["annual"] = []
    prior_chart = next((page for page in sources["prior"][2] if "Annualized Time-Weighted Return" in page
                        and re.search(r"\b\d+[- ]Yr\b", page)), "")
    horizons = sorted({int(v) for v in re.findall(r"\b(\d+)[- ]Yr\b", prior_chart)})
    if not horizons:
        ledger.issue("return_horizons", "Cannot identify annualized chart horizons in the prior report", "blocker")
    for horizon in horizons:
        value, fid = get(annual, ar, ah, f"{horizon} Year Net")
        bench, bid = get(annual, br, ah, f"{horizon} Year Net")
        portfolio["annual"].append(dict(horizon=horizon, value=value, value_id=fid, benchmark=bench, benchmark_id=bid))
    portfolio["benchmark_one"], portfolio["benchmark_one_id"] = get(annual, br, ah, "1 Year Net")
    portfolio["ex_us"], portfolio["ex_us_id"] = get(funding, funding.find("Ex-US Portfolio", numeric=True), fh, "Market Value (%)")
    diversification = {}
    for sheet_name, key in [("All Property", "property"), ("All Geographic", "geography")]:
        sheet = sheets[sheet_name]
        row = sheet.find(sources["name"] + " Portfolio")
        header = next(r for r in sheet.rows() if any(norm(c.value) in {"apartment", "northeast"} for c in r))
        values = []
        for i, c in enumerate(header):
            if i and c.value is not None:
                value, fid = sheet.number(row[i], metric=str(c.value)); values.append(dict(label=str(c.value), value=value, id=fid))
        ledger.check(key + " diversification sum", sum(v["value"] for v in values), 100, 0.02)
        diversification[key] = values
    for category, eligible, descending in [
        ("contributor", [f for f in funds if f["contribution"] > 0], True),
        ("detractor", [f for f in funds if f["contribution"] < 0], False),
        ("individual position", funds, True)]:
        key = "nav" if category == "individual position" else "contribution"
        ranked = sorted(eligible, key=lambda f: ((-1 if descending else 1) * f[key], entity(f["name"])))[:2]
        for rank, fund in enumerate(ranked):
            fund["roles"].append(("largest " if rank == 0 else "second-largest ") + category)
    for fund in funds:
        fund["roles_id"] = ledger.add(fund["roles"], {"kind": "ranking"},
                                      formula="top two positive and negative dollar contributions; top two NAVs; alphabetical tie-break",
                                      inputs=[f[k + "_id"] for f in funds for k in ["name", "contribution", "nav"]])
    policy = policy_from_prior(sources["prior"], ledger)
    largest = max(diversification["property"], key=lambda x: x["value"])
    compliance = []
    def rule(label, actual, limit, ids, passed):
        compliance.append(dict(label=label, actual=actual, limit=limit, evidence=ids,
                               status="In compliance" if passed else "Out of compliance"))
    if "sector" in policy:
        rule("Style / sector concentration", f"{largest['value']:.1f}% ({largest['label']})",
             f"<={policy['sector'][0]:g}% per sector", [largest["id"], policy["sector_id"]], largest["value"] <= policy["sector"][0])
    if "ex_us" in policy:
        rule("Location diversification", f"{portfolio['ex_us']:.1f}% Ex-US", f"<={policy['ex_us'][0]:g}% Ex-US",
             [portfolio["ex_us_id"], policy["ex_us_id"]], portfolio["ex_us"] <= policy["ex_us"][0])
    if "leverage" in policy:
        limits = policy["leverage"]
        rule("Leverage (loan-to-value)", " / ".join(f"{sleeves[s]['ltv']:.1f}% {s.lower()}" for s in ["Strategic", "Tactical"]),
             f"<={limits[0]:g}% / {limits[1]:g}%", [sleeves[s]["ltv_id"] for s in ["Strategic", "Tactical"]] + [policy["leverage_id"]],
             all(sleeves[s]["ltv"] <= limit for s, limit in zip(["Strategic", "Tactical"], limits)))
    rule("Return objective", f"{portfolio['one_net']:.2f}% vs {portfolio['benchmark_one']:.2f}% (1-Yr)", "Exceed benchmark",
         [portfolio["one_net_id"], portfolio["benchmark_one_id"]], portfolio["one_net"] > portfolio["benchmark_one"])
    return dict(portfolio=portfolio, funds=funds, sleeves=sleeves, diversification=diversification,
                policy=policy, compliance=compliance)


def commitments(sources, requested, client, funds, ledger):
    start, end = bounds(requested)
    events = []
    scope = []
    client_aliases = {norm(client), norm(sources["name"])}
    for path, ws in sources["logs"]:
        sheet = Sheet(path, ws, ledger)
        header_row, headers = sheet.headers("IC #")
        scope.append(dict(id=ledger.add(dict(client_aliases=sorted(client_aliases), start=start.isoformat(), end=end.isoformat(),
                                             rule="Commitment category; actions through quarter end; approvals minus withdrawals/lapses"),
                                       {"file": path.name, "sheet": ws.title, "cell": f"A{header_row}:J{ws.max_row}"})))
        for row in sheet.rows():
            def value(label): return row[headers[norm(label)]].value
            if norm(value("Client")) not in client_aliases or norm(value("Recommendation Category")) != "commitment":
                continue
            if not isinstance(value("Meeting Date"), datetime):
                ledger.issue("invalid_ic_date", f"Invalid relevant IC date in {path.name}/{ws.title}/{row[0].row}", "blocker")
                continue
            meeting = value("Meeting Date").date()
            if meeting >= end:
                continue
            action = norm(value("Committee Action"))
            if action not in {"approved", "withdrawn", "lapsed", "deferred"}:
                ledger.issue("unknown_ic_action", f"Unrecognized IC action {action!r}", "blocker")
                continue
            text = str(value("Recommendation"))
            # Monetary amounts in the log are text, but parsing their explicit units is deterministic.
            match = re.search(r"USD\s*([\d,.]+)\s*(million|billion)?", text, re.I)
            amount = currency(match[1].replace(",", "")) * ({"million": 1_000_000, "billion": 1_000_000_000}.get((match[2] or "").lower(), 1)) if match else None
            if amount is None and action == "approved":
                ledger.issue("ic_amount", f"Cannot parse approved amount for {value('Fund')}", "blocker")
            recommendation_id = sheet.fact(row[headers["recommendation"]])
            events.append(dict(name=str(value("Fund")), date=meeting.isoformat(), action=action, amount=amount,
                               id=sheet.fact(row[headers["fund"]]), date_id=sheet.fact(row[headers["meeting date"]]),
                               action_id=sheet.fact(row[headers["committee action"]]), recommendation=text,
                               amount_id=ledger.add(amount, {"file": path.name, "sheet": ws.title,
                                                            "cell": row[headers["recommendation"]].coordinate},
                                                    formula="parse explicit USD amount and unit", inputs=[recommendation_id])))
    events.sort(key=lambda e: (e["date"], entity(e["name"]), e["action"]))
    state = {}
    seen = {}
    unique_events = []
    for event in events:
        key = entity(event["name"])
        identity = (key, event["date"], event["action"])
        if identity in seen:
            if event["amount"] != seen[identity]["amount"]:
                ledger.issue("ambiguous_ic_event", f"Conflicting amounts for {event['name']} on {event['date']}", "blocker")
            continue
        seen[identity] = event
        unique_events.append(event)
        if event["action"] == "approved":
            state[key] = event
        elif event["action"] in {"withdrawn", "lapsed"}:
            if event["amount"] is None and key in state:
                approval = state[key]
                event["amount"] = approval["amount"]
                event["amount_id"] = ledger.add(event["amount"], {"kind": "calculation"},
                                                formula="carry original approved amount into reversal",
                                                inputs=[approval["amount_id"], event["action_id"]])
            state.pop(key, None)
    events = unique_events
    funded = {entity(f["name"]) for f in funds}
    opened = [e for key, e in state.items() if key not in funded]
    new = [e for e in events if e["action"] == "approved" and start.isoformat() <= e["date"] < end.isoformat()]
    previous = "\n".join(sources["prior"][2])
    reversed_events = [e for e in events if e["action"] in {"withdrawn", "lapsed"}
                       and start.isoformat() <= e["date"] < end.isoformat() and entity(e["name"]) in entity(previous)]
    for event in reversed_events:
        if event["amount"] is None:
            ledger.issue("reversal_amount", f"Cannot establish prior approved amount for {event['name']}", "blocker")
    order = lambda e: (-(e["amount"] or 0), entity(e["name"]))
    return dict(open=sorted(opened, key=order), new=sorted(new, key=order), reversed=reversed_events, events=events, scope=scope)
