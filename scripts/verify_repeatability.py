"""Run two isolated CLI processes with empty caches and compare meaningful output."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", required=True)
    parser.add_argument("--quarter", required=True)
    parser.add_argument("--inputs", type=Path, default=Path("inputs"))
    parser.add_argument("--record", type=Path, default=Path("output/repeatability.json"))
    parser.add_argument(
        "--online", action="store_true", help="Retain API keys and compare independent model runs"
    )
    args = parser.parse_args()
    environment = os.environ.copy()
    if not args.online:
        environment["PMR_LOAD_ENV"] = "0"
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            environment.pop(key, None)
    with tempfile.TemporaryDirectory(prefix="pmr-repeatability-") as folder:
        summaries = []
        manifests = []
        for name in ["first", "second"]:
            output = Path(folder) / name
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pmr",
                    "generate",
                    "--client",
                    args.client,
                    "--quarter",
                    args.quarter,
                    "--inputs",
                    str(args.inputs.resolve()),
                    "--output",
                    str(output),
                ],
                check=True,
                env=environment,
            )
            summaries.append(json.loads((output / "verification.json").read_text(encoding="utf-8")))
            manifests.append(json.loads((output / "semantic_manifest.json").read_text(encoding="utf-8")))
        meaningful_equal = summaries[0]["semantic_hash"] == summaries[1]["semantic_hash"]
        revision_equal = summaries[0]["implementation_hashes"] == summaries[1]["implementation_hashes"]
        complete = all(s["checks_passed"] == s["checks_total"] for s in summaries)
        if args.online:
            complete &= all(
                m["charts"] and all(c["observations"] is not None for c in m["charts"]) for m in manifests
            )
            complete &= all(not any(i["severity"] == "blocker" for i in s["issues"]) for s in summaries)
        equal = meaningful_equal and revision_equal and complete
        result = dict(
            passed=equal,
            mode="online" if args.online else "no-key",
            runs=summaries,
            meaningful_equal=meaningful_equal,
            revision_equal=revision_equal,
            required_output_complete=complete,
            semantic_manifests=manifests,
            full_report_equal=summaries[0]["meaning_hash"] == summaries[1]["meaning_hash"],
            scope="Separate Python processes and empty caches; every reported figure, chart observation, fund/role/order/compliance and section structure",
        )
        args.record.parent.mkdir(parents=True, exist_ok=True)
        args.record.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("Repeatability: " + ("PASS" if equal else "FAIL"))
        raise SystemExit(0 if equal else 1)


if __name__ == "__main__":
    main()
