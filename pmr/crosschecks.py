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
