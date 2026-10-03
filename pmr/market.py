"""Stable, portfolio-relevant condensation of validated chart observations."""

import re
from decimal import Decimal

from .ingest import norm, quarter
from .numeric import display


def observation_sentence(chart, property_mix, reporting_year=None):
    """Condense source observations without adding an investment recommendation."""
    values = select_observations(chart["data"].get("series", []), property_mix)
    if not values:
        return ""

    def formatted(v):
        return ("~" if v.get("method") == "axis_read" else "") + (
            "$" + display(v["value"], 0) + "/month"
            if v["unit"] == "USD/month"
            else display(v["value"], 1) + v["unit"]
        )

    title = norm(chart["data"]["title"])
    if "fund total return" in title:
        latest = [v for v in values if "latest" in norm(v["label"])]
        trailing = [v for v in values if "yr" in norm(v["label"])]
        if len(latest) == len(trailing) == 1:
            return f"Broad private real-estate funds returned {formatted(latest[0])} net in the latest quarter and {formatted(trailing[0])} over {trailing[0]['label']}."
    if "treasury" in title and len(values) == 2:
        cap = [v for v in values if "cap rate" in norm(v["series"])]
        treasury = [v for v in values if "treasury" in norm(v["series"])]
        if len(cap) == len(treasury) == 1:
            return f"At {cap[0]['label']}, the NPI value-weighted cap rate was {formatted(cap[0])}, against {formatted(treasury[0])} for the 10-year Treasury yield."
    if "noi growth" in title:
        periods = sorted(
            {v["series"] for v in values},
            key=lambda s: int(re.search(r"\d{4}", s)[0]) if re.search(r"\d{4}", s) else 9999,
        )
        forward = [
            s
            for s in periods
            if reporting_year is not None
            and re.search(r"\d{4}", s)
            and int(re.search(r"\d{4}", s)[0]) > reporting_year
        ]
        first = forward[0] if forward else periods[0]
        forecasts = [v for v in values if v["series"] == first]
        return (
            f"The deck forecasts {first} NOI growth of "
            + " and ".join(formatted(v) + " for " + v["label"].lower() for v in forecasts)
            + "."
        )
    if "industrial" in title and "total return" in title and len(values) == 2:
        return (
            f"For {values[0]['label']}, net industrial returns were "
            + " and ".join(formatted(v) + " for " + v["series"] for v in values)
            + "."
        )
    if "cost to own" in title and len(values) == 2:
        return (
            f"At {values[0]['label']}, monthly housing costs were "
            + " versus ".join(formatted(v) + " (" + v["series"].lower() + ")" for v in values)
            + "."
        )
    if "office" in title and "cap rate" in title and len(values) == 2:
        return (
            f"The office exhibit reports, at {values[0]['label']}, "
            + " versus ".join(v["series"].lower() + " " + formatted(v) for v in values)
            + "."
        )
    if "population" in title and "inventory" in title:
        groups = {}
        for value in values:
            groups.setdefault(value["label"], []).append(value)
        period = re.search(r"\d{4}[-\u2013]\d{4}", chart["data"]["title"])
        return (
            "The retail exhibit"
            + (" for " + period[0] if period else "")
            + " shows "
            + "; ".join(
                city + ": " + " versus ".join(formatted(v) + " " + v["series"].lower() for v in items)
                for city, items in groups.items()
            )
            + "."
        )
    group_by = (
        "series" if len({v["series"] for v in values}) <= len({v["label"] for v in values}) else "label"
    )
    other = "label" if group_by == "series" else "series"
    groups = {}
    for value in values:
        formatted = "~" if value.get("method") == "axis_read" else ""
        formatted += (
            "$" + display(value["value"], 0) + "/month"
            if value["unit"] == "USD/month"
            else display(value["value"], 1) + value["unit"]
        )
        groups.setdefault(value[group_by], []).append(value[other] + " " + formatted)
    return (
        chart["data"]["title"]
        + ": "
        + "; ".join(key + " (" + ", ".join(items) + ")" for key, items in groups.items())
        + "."
    )


def market_passages(data, ledger):
    """A small auditable writing bundle, not an enumeration of every exhibit.

    Keep broad returns, financing conditions, forward NOI for material sectors,
    and the computed office valuation risk. Full charts remain in the audit.
    """
    passages = []
    for slide in data["slides"]:
        if any(word in norm(slide["title"]) for word in ["key themes", "risks", "positioning"]):
            passages.append(
                dict(
                    id=slide["id"],
                    text=" ".join(slide["text"]),
                    source=ledger.facts[slide["id"]]["source"],
                    qualitative_only=True,
                )
            )
    weights = sorted(data["diversification"]["property"], key=lambda p: (-p["value"], p["label"]))[:2]
    year = quarter(data["quarter"])[0]
    for chart in data["charts"]:
        if not chart["data"]:
            continue
        title = norm(chart["data"]["title"])
        if not any(term in title for term in ["fund total return", "treasury", "noi growth", "office"]):
            continue
        text = observation_sentence(chart, data["diversification"]["property"], year)
        ids = [chart["id"]]
        words = []
        if "noi growth" in title:
            text = (
                "The Portfolio's largest property exposures are "
                + " and ".join(f"{p['label']} at {p['value']:.1f}%" for p in weights)
                + ". "
                + text
            )
            ids += [p["id"] for p in weights]
            positioning = next(
                (
                    (slide, bullet)
                    for slide in data["slides"]
                    for bullet in slide["text"]
                    if any(word in norm(slide["title"]) for word in ["key themes", "positioning"])
                    and any(term in norm(bullet) for term in ["favor", "favour", "tilt toward"])
                ),
                None,
            )
            if positioning:
                text += " House-view positioning: " + positioning[1]
                ids.append(positioning[0]["id"])
        for signal in data.get("market_signals", []):
            if signal["title"] == chart["data"]["title"]:
                text += f" The transaction/appraisal gap {signal['direction']} from {signal['old_gap']} to {signal['new_gap']} percentage points."
                words.append(signal["direction"])
                ids.append(signal["id"])
        if text:
            fid = ledger.add(
                text,
                {"kind": "verified market writing bundle"},
                formula="deterministically selected chart observations and portfolio exposures",
                inputs=ids,
            )
            passages.append(dict(id=fid, text=text, source=ledger.facts[fid]["source"], required_words=words))
    return passages


def period_key(label):
    period = quarter(label)
    if period:
        return period
    match = re.fullmatch(r"(\d{2})Q([1-4])", label)
    return (2000 + int(match[1]), int(match[2])) if match else None


def select_observations(values, property_mix):
    """Latest period, short-horizon returns, or current portfolio's largest sectors.

    All observations remain in evidence/semantic manifests. Selection is code-owned,
    never a model's 'highlights' field; aliases below are category vocabulary only.
    """
    dates = {period_key(v["label"]) for v in values if period_key(v["label"])}
    if dates:
        latest = max(dates)
        return [v for v in values if period_key(v["label"]) == latest]
    horizons = [(int(m[1]), v) for v in values if (m := re.fullmatch(r"(\d+)[ -]Yr", v["label"], re.I))]
    if horizons:
        shortest = min(h for h, _ in horizons)
        return [v for v in values if "latest" in norm(v["label"])] + [v for h, v in horizons if h == shortest]
    vocabulary = {"residential": "apartment", "multifamily": "apartment"}
    weights = {norm(p["label"]): p["value"] for p in property_mix}
    categories = {v["label"] for v in values}
    recognized = [c for c in categories if vocabulary.get(norm(c), norm(c)) in weights]
    if recognized:
        material = sorted(recognized, key=lambda c: (-weights[vocabulary.get(norm(c), norm(c))], norm(c)))[:2]
        return [v for v in values if v["label"] in material]
    # Paired population/inventory exhibits: strongest imbalance, not first cities.
    pairs = []
    for category in categories:
        population = [v for v in values if v["label"] == category and "population" in norm(v["series"])]
        inventory = [v for v in values if v["label"] == category and "inventory" in norm(v["series"])]
        if len(population) == len(inventory) == 1:
            gap = abs(Decimal(str(population[0]["value"])) - Decimal(str(inventory[0]["value"])))
            pairs.append((gap, category))
    if pairs:
        material = {c for _, c in sorted(pairs, key=lambda p: (-p[0], norm(p[1])))[:2]}
        return [v for v in values if v["label"] in material]
    return values[:4]
