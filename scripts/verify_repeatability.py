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
    parser.add_argument("--online", action="store_true", help="Retain API keys and compare independent model runs")
    args = parser.parse_args()
    environment = os.environ.copy()
    if not args.online:
        environment["PMR_LOAD_ENV"] = "0"
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            environment.pop(key, None)
    with tempfile.TemporaryDirectory(prefix="pmr-repeatability-") as folder:
        summaries = []
        for name in ["first", "second"]:
            output = Path(folder) / name
            subprocess.run([sys.executable, "-m", "pmr", "generate", "--client", args.client, "--quarter", args.quarter,
                            "--inputs", str(args.inputs.resolve()), "--output", str(output)], check=True, env=environment)
            summaries.append(json.loads((output / "verification.json").read_text()))
        equal = summaries[0]["financial_hash"] == summaries[1]["financial_hash"]
        result = dict(passed=equal, mode="online" if args.online else "no-key", runs=summaries,
                      full_report_equal=summaries[0]["meaning_hash"] == summaries[1]["meaning_hash"],
                      scope="Separate Python processes; pinned dependencies; new output folders and model caches")
        args.record.parent.mkdir(parents=True, exist_ok=True)
        args.record.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("Repeatability: " + ("PASS" if equal else "FAIL"))
        raise SystemExit(0 if equal else 1)


if __name__ == "__main__":
    main()
