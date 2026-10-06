"""python -m pmr generate --client CODE --quarter 4Q25"""

import argparse
import json
import os
from pathlib import Path
import sys
import traceback
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError

from .pipeline import generate
from .review import serve
from .config import load_environment
from .workspace import serve_workspace


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
    start = commands.add_parser("start", help="Open the local browser workspace")
    start.add_argument("--client")
    start.add_argument("--quarter")
    start.add_argument("--inputs", type=Path, default=Path("inputs"))
    start.add_argument("--output", type=Path, default=Path("output"))
    start.add_argument("--no-browser", action="store_true")
    start.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    load_environment()
    if args.command == "review":
        serve(args.output.resolve(), args.port)
        return
    if args.command == "start":
        try:
            serve_workspace(
                args.inputs,
                args.output,
                args.client,
                args.quarter,
                args.port,
                open_browser=not args.no_browser,
            )
        except KeyboardInterrupt:
            print("Workspace stopped.")
        return
    try:
        _, summary = generate(args.inputs.resolve(), args.output.resolve(), args.client, args.quarter)
    except Exception as error:
        known = isinstance(error, (ValueError, StopIteration, KeyError, OSError, BadZipFile, ParseError))
        reason = str(error) if known and str(error) else (
            f"Unexpected generation failure ({type(error).__name__}); inspect the stage diagnostics"
        )
        if isinstance(error, OSError):
            reason = f"Local file operation failed ({type(error).__name__})" + (
                f": {error.filename}" if error.filename else ""
            )
        for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
            secret = os.getenv(key)
            if secret:
                reason = reason.replace(secret, "[redacted]")
        category = "filesystem" if isinstance(error, OSError) else "source_data" if known else "unexpected"
        from .errors import explain_failure

        failure = dict(status="blocked", reason=reason, error_type=type(error).__name__, category=category,
                       **explain_failure(reason, args.client, args.quarter))
        if not known:
            failure["frames"] = [dict(file=f.filename, line=f.lineno, function=f.name)
                                 for f in traceback.extract_tb(error.__traceback__)]
        try:
            if args.inputs.resolve() == args.output.resolve() or args.inputs.resolve() in args.output.resolve().parents:
                raise OSError("Failure records must not be written inside the input folder")
            args.output.mkdir(parents=True, exist_ok=True)
            (args.output / "failure.json").write_text(json.dumps(failure, indent=2), encoding="utf-8")
        except OSError as save_error:
            print(f"Could not save failure record ({type(save_error).__name__}); check output-folder access.", file=sys.stderr)
        print(f"Report generation stopped: {reason}", file=sys.stderr)
        raise SystemExit(2 if known else 3)
    from .filenames import report_filename

    print(f"Draft saved: {args.output / report_filename(args.client, args.quarter)}")
    print(f"Verification: {summary['checks_passed']}/{summary['checks_total']} checks passed")
    print(f"Review queue: {len(summary['issues'])} items; launch python -m pmr review")


if __name__ == "__main__":
    main()
