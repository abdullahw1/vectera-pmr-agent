"""Canonical report meaning and a machine-walkable claim-to-evidence manifest."""

import json
import re
from decimal import Decimal

from .charts import semantic_charts
from .evidence import digest
from .numeric import display

NUMBER = re.compile(r"(?<![\w])[-+]?\d[\d,]*(?:\.\d+)?")


def numeric_tokens(text):
    return NUMBER.findall(str(text))


def reachable(ids, facts):
    visited = set()

    def walk(identifier):
        if identifier in visited:
            return
        if identifier not in facts:
            raise ValueError(f"Unknown evidence reference {identifier}")
        visited.add(identifier)
        for child in facts[identifier].get("inputs", []):
            walk(child)

    for identifier in ids:
        walk(identifier)
    return sorted(visited)


def validate_numeric_quote(quote, fact, *, entity=None):
    """Scoped verbatim evidence, not global 'this number appears somewhere' membership."""
    source = fact["source"]
    if entity is not None and fact.get("entity", fact.get("numeric", {}).get("entity")) != entity:
        raise ValueError("Quote belongs to a different entity")
    if not isinstance(quote, str) or quote not in str(source.get("quote", "")):
        raise ValueError("Quote and its numbers must occur in the cited source passage")
    return True


def semantic_manifest(data, sections):
    financials = {
        key: data[key]
        for key in [
            "portfolio",
            "funds",
            "sleeves",
            "activity",
            "policy",
            "compliance",
            "history",
            "diversification",
        ]
    }
    structure = [
        {
            "title": s["title"],
            "blocks": [
                {
                    "type": b["type"],
                    "kind": b.get("kind"),
                    "columns": b.get("columns"),
                    "rows": b.get("rows"),
                    "numbers": numeric_tokens(b.get("text", "")),
                }
                for b in s["blocks"]
            ],
        }
        for s in sections
    ]
    return json.loads(
        json.dumps(
            dict(
                client=data["client"],
                quarter=data["quarter"],
                financials=financials,
                charts=semantic_charts(data["charts"]),
                structure=structure,
            ),
            default=str,
        )
    )


def claim_manifest(sections, ledger):
    claims = []
    for section_no, section in enumerate(sections):
        for block_no, block in enumerate(section["blocks"]):
            ids = block.get("evidence", [])
            resolved = reachable(ids, ledger.facts)
            claims.append(
                dict(
                    id=f"s{section_no + 1}.b{block_no + 1}",
                    section=section["title"],
                    type=block["type"],
                    text=block.get("text"),
                    rows=block.get("rows"),
                    numbers=(
                        numeric_tokens(block.get("text", ""))
                        if block["type"] == "paragraph"
                        else [numeric_tokens(cell) for row in block.get("rows", []) for cell in row]
                    ),
                    evidence=ids,
                    resolved_evidence=resolved,
                    locators=[
                        ledger.facts[i]["source"] for i in resolved if ledger.facts[i]["source"].get("file")
                    ],
                    status="source_linked" if ids else "nonfactual_process_notice",
                )
            )
            if block.get("cell_evidence"):
                claims[-1]["cells"] = [
                    dict(
                        row=row_no,
                        column=column_no,
                        value=block["rows"][row_no][column_no],
                        evidence=cell_ids,
                        resolved_evidence=reachable(cell_ids, ledger.facts),
                    )
                    for row_no, row in enumerate(block["cell_evidence"])
                    for column_no, cell_ids in enumerate(row)
                ]
    return claims


def write_manifests(output, data, sections, ledger, prefix=""):
    meaning = semantic_manifest(data, sections)
    claims = claim_manifest(sections, ledger)
    (output / (prefix + "semantic_manifest.json")).write_text(
        json.dumps(meaning, indent=2, sort_keys=True), encoding="utf-8"
    )
    (output / (prefix + "manifest.json")).write_text(
        json.dumps(dict(claims=claims, facts=ledger.facts), indent=2, default=str), encoding="utf-8"
    )
    return digest(meaning)
