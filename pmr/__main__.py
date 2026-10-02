"""python -m pmr generate --client CODE --quarter 4Q25"""
import argparse
import json
from pathlib import Path
import sys

from .pipeline import generate
from .review import serve
from .config import load_environment


def main():
    parser = argparse.ArgumentParser(description="Generate and review an evidence-grounded quarterly PMR")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("generate")
    run.add_argument("--client", required=True)
    run.add_argument("--quarter", required=True)
    run.add_argument("--inputs", type=Path, default=Path("inputs"))
    run.add_argument("--output", type=Path, default=Path("output"))
    review = commands.add_parser("review")
    review.add_argument("--output", type=Path, default=Path("output"))
    review.add_argument("--port", type=int, default=8765)
    start = commands.add_parser("start", help="Generate a report and open its local review page")
    start.add_argument("--client")
    start.add_argument("--quarter")
    start.add_argument("--inputs", type=Path, default=Path("inputs"))
    start.add_argument("--output", type=Path, default=Path("output"))
    start.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    load_environment()
    if args.command == "review":
        serve(args.output.resolve(), args.port)
        return
    if args.command == "start":
        args.client = args.client or input("Client code: ").strip()
        args.quarter = args.quarter or input("Reporting quarter (for example 4Q25): ").strip()
        if not args.client or not args.quarter:
            parser.error("Client and reporting quarter cannot be blank")
        print("Generating the report and checking its source evidence...", flush=True)
    try:
        _, summary = generate(args.inputs.resolve(), args.output.resolve(), args.client, args.quarter)
    except (ValueError, StopIteration, KeyError) as error:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "failure.json").write_text(json.dumps(dict(status="blocked", reason=str(error)), indent=2), encoding="utf-8")
        print(f"Required source data could not be resolved: {error}", file=sys.stderr)
        raise SystemExit(2)
    print(f"Draft saved: {args.output / 'report.pdf'}")
    print(f"Verification: {summary['checks_passed']}/{summary['checks_total']} checks passed")
    print(f"Review queue: {len(summary['issues'])} items; launch python -m pmr review")
    if args.command == "start":
        print("Keep this window open during review. Press Ctrl+C to stop.", flush=True)
        try:
            serve(args.output.resolve(), 0, open_browser=not args.no_browser)
        except KeyboardInterrupt:
            print("Review server stopped.")
        except OSError as error:
            print(f"The draft is saved, but the local review server could not start: {error}. "
                  f"Open {args.output / 'review.html'} for read-only review, or retry the review command.", file=sys.stderr)
            raise SystemExit(2)


if __name__ == "__main__":
    main()
