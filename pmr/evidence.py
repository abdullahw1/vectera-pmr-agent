"""Small evidence ledger shared by extraction, calculations and rendering."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from decimal import Decimal


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


@dataclass
class Ledger:
    facts: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)
    matches: list = field(default_factory=list)
    checks: list = field(default_factory=list)
    discovery: list = field(default_factory=list)
    reporting_period: str | None = None

    def add(self, value, source, *, formula=None, inputs=None, numeric=None):
        record = {"value": value, "source": source}
        if numeric:
            record["numeric"] = numeric
        if formula:
            record.update(formula=formula, inputs=inputs or [])
        identifier = "f_" + digest(record)[:16]
        self.facts[identifier] = record
        return identifier

    def issue(self, code, message, severity="warning", **context):
        record = {"code": code, "message": message, "severity": severity, **context}
        if record not in self.issues:
            self.issues.append(record)

    def check(self, name, actual, expected, tolerance=0, *, severity="blocker", evidence=None):
        if isinstance(actual, Decimal) or isinstance(expected, Decimal):
            actual, expected, tolerance = (Decimal(str(v)) for v in (actual, expected, tolerance))
        delta = actual - expected
        passed = abs(delta) <= tolerance
        self.checks.append(dict(name=name, actual=actual, expected=expected,
                                delta=delta, tolerance=tolerance, passed=passed,
                                severity=severity, evidence=evidence or []))
        if not passed:
            self.issue("reconciliation", f"{name}: difference {delta:,.4f}", severity, evidence=evidence or [])

    def save(self, path: Path):
        path.write_text(json.dumps(self.__dict__, indent=2, sort_keys=True, default=str), encoding="utf-8")
