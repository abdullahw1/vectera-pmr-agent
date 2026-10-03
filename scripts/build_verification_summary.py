"""Publish observed pytest outcomes as a compact, machine-readable regression matrix."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def main():
    root = Path(__file__).resolve().parents[1]
    suites = ET.parse(root / "output" / "test-results.xml").getroot()
    cases = []
    for case in suites.iter("testcase"):
        outcome = "failed" if case.find("failure") is not None or case.find("error") is not None else "skipped" if case.find("skipped") is not None else "passed"
        cases.append(dict(test=case.attrib["name"], module=case.attrib["classname"], expected="passed",
                          observed=outcome, seconds=float(case.attrib.get("time", 0))))
    result = dict(passed=all(c["observed"] == "passed" for c in cases), total=len(cases), cases=cases)
    (root / "output" / "regression_matrix.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Regression matrix: {len(cases)} cases; passed={result['passed']}")


if __name__ == "__main__": main()
