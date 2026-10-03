"""Stable, portfolio-relevant condensation of validated chart observations."""
import re
from decimal import Decimal

from .ingest import norm, quarter


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
