"""Supporting documents corroborate, but never overwrite, authoritative flash facts."""

import re
from decimal import Decimal

from .ingest import entity, norm, quarter
from .numeric import display


def supporting_checks(sources, data, ledger):
    funds = {entity(f["name"]): f for f in data["funds"]}
    approvals = {entity(e["name"]): e for e in data["activity"]["new"]}
    for path, pages in sources["managers"]:
        lines = {entity(line) for page in pages for line in page.splitlines() if line.strip()}
        candidates = [key for key in funds.keys() | approvals.keys() if key in lines]
        if len(candidates) != 1:
            continue
        key = candidates[0]
        for page_no, page in enumerate(pages, 1):
            for metric, pattern in [
                ("nav", r"Net Asset Value\s+\$([\d,]+(?:\.\d+)?)"),
                ("q_net", r"Quarter Total Net Return\s+([+-]?[\d.]+)%"),
                ("ltv", r"Loan-to-Value\s+([\d.]+)%"),
            ]:
                match = re.search(pattern, page)
                if key not in funds or not match or funds[key].get(metric) is None:
                    continue
                value = Decimal(match[1].replace(",", ""))
                # Half the last displayed unit reflects source rounding, not a monetary
                # tolerance on the flash. A manager statistic is not an authoritative total.
                tolerance = Decimal(1).scaleb(value.as_tuple().exponent) / 2
                fid = ledger.add(
                    value,
                    {"file": str(path.relative_to(sources["root"])), "page": page_no, "quote": match[0]},
                    numeric=dict(
                        entity=funds[key]["name"],
                        metric=metric,
                        unit="USD" if metric == "nav" else "%",
                        authority="supporting",
                        precision=str(tolerance * 2),
                        period=data["quarter"],
                    ),
                )
                ledger.check(
                    funds[key]["name"] + " manager " + metric,
                    Decimal(str(funds[key][metric])),
                    value,
                    tolerance,
                    severity="warning",
                    evidence=[funds[key][metric + "_id"], fid],
                )
            match = re.search(r"Commitment\s*\(this investor\)\s*\$([\d,]+(?:\.\d+)?)", page)
            # An unresolved IC amount is already a blocker; there is nothing to compare.
            if key in approvals and match and approvals[key]["amount"] is not None:
                value = Decimal(match[1].replace(",", ""))
                fid = ledger.add(
                    value,
                    {"file": str(path.relative_to(sources["root"])), "page": page_no, "quote": match[0]},
                )
                ledger.check(
                    approvals[key]["name"] + " one-pager/IC commitment",
                    approvals[key]["amount"],
                    value,
                    evidence=[approvals[key]["amount_id"], fid],
                )
    requested = quarter(data["quarter"])
    current = [r for r in data["history"] if quarter(r["quarter"]) == requested]
    if len(current) != 1:
        ledger.issue(
            "history_period", "Allocation history must contain exactly one requested-period row", "blocker"
        )
    else:
        row = current[0]
        for key in ["nav", "target"]:
            value = Decimal(str(row[key]))
            places = row[key + "_precision"]
            expected = Decimal(display(data["portfolio"][key] / 1_000_000, places).replace(",", ""))
            ledger.check(
                "Allocation history/flash " + key + " at USD-million display precision",
                value,
                expected,
                evidence=[row[key + "_id"], data["portfolio"][key + "_id"]],
            )
        ledger.issue(
            "history_ownership",
            "Allocation workbook has no client column. Requested-period rounded NAV/target were checked against the flash; client ownership remains an explicit assumption.",
            evidence=[row["nav_id"], row["target_id"]],
        )
    # Compare like-defined quarter-end NAV to current beginning NAV, only where the
    # prior text explicitly supplies a rounded market value. Missing evidence is not guessed.
    for page_no, page in enumerate(sources["prior"][2], 1):
        match = re.search(r"Market [Vv]alue\s+\$([\d.]+)M", page)
        if match:
            value = Decimal(match[1]) * 1_000_000
            tolerance = Decimal(1).scaleb(Decimal(match[1]).as_tuple().exponent) * 1_000_000 / 2
            fid = ledger.add(value, {"file": sources["prior"][1].name, "page": page_no, "quote": match[0]})
            ledger.check(
                "Prior ending/current beginning NAV (rounded prior display)",
                data["portfolio"]["beginning"],
                value,
                tolerance,
                severity="warning",
                evidence=[data["portfolio"]["beginning_id"], fid],
            )
            break


def cap_rate_signals(charts, ledger):
    """Compare the transaction/appraisal gap for the last two chart periods."""
    signals = []
    for chart in charts:
        if not chart["data"]:
            continue
        categories = {}
        for row in chart["data"]["series"]:
            if row["unit"] == "%":
                categories.setdefault(row["label"], []).append(row)
        gaps = []
        for category, rows in categories.items():
            appraisal = [r for r in rows if "appraisal" in norm(r["series"])]
            transaction = [r for r in rows if "transaction" in norm(r["series"])]
            period = re.fullmatch(r"(\d{2})Q([1-4])", category)
            if len(appraisal) == len(transaction) == 1 and period:
                gap = Decimal(str(transaction[0]["value"])) - Decimal(str(appraisal[0]["value"]))
                gaps.append(((int(period[1]), int(period[2])), category, gap))
        if len(gaps) >= 2:
            earlier, later = sorted(gaps)[-2:]
            change = later[2] - earlier[2]
            fid = ledger.add(
                dict(earlier=str(earlier[2]), later=str(later[2]), change=str(change)),
                {"kind": "calculation"},
                formula="transaction - appraisal, latest and preceding chart periods",
                inputs=[chart["id"]],
            )
            signals.append(
                dict(
                    title=chart["data"]["title"],
                    earlier=earlier[1],
                    later=later[1],
                    old_gap=earlier[2],
                    new_gap=later[2],
                    difference=change,
                    direction="widened" if change > 0 else "narrowed" if change < 0 else "was unchanged",
                    id=fid,
                )
            )
    return signals


def contextual_checks(sources, data, ledger):
    """Surface status changes and older observations without changing flash figures."""
    for fund in data["funds"]:
        status = [p for p in data["support"].get(fund["name"], [])
                  if re.search(r"\b(?:the )?fund (?:has been|was|is) dissolved\b", p["text"], re.I)]
        if status:
            fund["termination"] = status[0]
            evidence = [status[0]["id"], fund["nav_id"], fund["q_net_id"]]
            for path, pages in sources["managers"]:
                if str(path.relative_to(sources["root"])) != status[0]["source"]["file"]:
                    continue
                for number, page in enumerate(pages, 1):
                    match = re.search(r"No quarterly performance percentages are presented[^.]*\.", page)
                    if match:
                        fid = ledger.add(match[0], dict(file=status[0]["source"]["file"], page=number, quote=match[0]))
                        fund["termination_return_note_id"] = fid
                        evidence.append(fid)
            ledger.issue("terminated_fund", fund["name"] +
                         ": manager reports dissolution. Flash holdings and returns are retained; review the termination and performance-period treatment.",
                         evidence=[i for i in evidence if i])
        threshold = data["policy"]["leverage"][0 if fund["sleeve"] == "Strategic" else 1]
        if fund.get("ltv") is not None and fund["ltv"] > threshold:
            fund["ltv_risk_threshold"] = threshold
            ledger.issue("fund_leverage_risk", fund["name"] +
                         ": individual LTV exceeds its sleeve's numeric threshold; SPEC tests compliance at sleeve level, not per fund.",
                         evidence=[fund["ltv_id"], data["policy"]["leverage_id"]])
        if fund.get("beginning") == 0 and fund.get("contributions") is not None and fund["contributions"] > 0:
            fund["newly_funded"] = True

    data["historical_revisions"] = []
    history = {quarter(row["quarter"]): row for row in data["history"]}
    for number, page in enumerate(sources["prior"][2], 1):
        for match in re.finditer(r"(?m)^\s*([1-4]Q\d{2})\s+([\d,]+(?:\.\d+)?)\s+([\d,]+(?:\.\d+)?)[ \t]*$", page):
            row = history.get(quarter(match[1]))
            if not row:
                continue
            prior = ledger.add(match[0], dict(file=sources["prior"][1].name, page=number, quote=match[0]))
            for metric, old in zip(["target", "nav"], match.groups()[1:]):
                if Decimal(str(row[metric])) != Decimal(old.replace(",", "")):
                    evidence = [row[metric + "_id"], prior]
                    ledger.issue("historical_revision", f"{row['quarter']} {metric} differs between allocation history and the prior PMR; confirm whether this is an intended restatement.", evidence=evidence)
                    data["historical_revisions"].append(dict(quarter=row["quarter"], metric=metric, evidence=evidence))
    periods, evidence = [], []
    for chart in data["charts"]:
        for observation in (chart.get("data") or {}).get("series", []):
            match = re.fullmatch(r"(\d{2})Q([1-4])", observation["label"])
            if match:
                periods.append((2000 + int(match[1]), int(match[2])))
                evidence.append(chart["id"])
    if periods and max(periods) < quarter(data["quarter"]):
        latest = max(periods)
        data["market_observation_period"] = f"{latest[1]}Q{str(latest[0])[-2:]}"
        data["market_period_evidence"] = list(dict.fromkeys(evidence))
        ledger.issue("market_data_lag", f"Latest explicitly quarter-labelled chart observations are {data['market_observation_period']}, earlier than {data['quarter']}. Confirm the reporting lag; a renamed deck is not evidence of updated observations.", evidence=data["market_period_evidence"])
