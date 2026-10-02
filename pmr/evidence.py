"""Small evidence ledger shared by extraction, calculations and rendering."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


@dataclass
class Ledger:
    facts: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)
    matches: list = field(default_factory=list)
    checks: list = field(default_factory=list)

    def add(self, value, source, *, formula=None, inputs=None):
        record = {"value": value, "source": source}
        if formula:
            record.update(formula=formula, inputs=inputs or [])
        identifier = "f_" + digest(record)[:16]
        self.facts[identifier] = record
        return identifier

    def issue(self, code, message, severity="warning", **context):
        record = {"code": code, "message": message, "severity": severity, **context}
        if record not in self.issues:
            self.issues.append(record)

    def check(self, name, actual, expected, tolerance=0.02):
        delta = actual - expected
        passed = abs(delta) <= tolerance
        self.checks.append(dict(name=name, actual=actual, expected=expected,
                                delta=delta, tolerance=tolerance, passed=passed))
        if not passed:
            self.issue("reconciliation", f"{name}: difference {delta:,.4f}", "blocker")

    def save(self, path: Path):
        path.write_text(json.dumps(self.__dict__, indent=2, sort_keys=True, default=str), encoding="utf-8")
