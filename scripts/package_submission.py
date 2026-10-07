"""Build a small, reproducible zip without keys, environments or scratch files."""

from pathlib import Path
import zipfile
import argparse
import hashlib
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--final", action="store_true", help="Require approved PDF and source-bound approval artifacts"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    target = root / "output" / "Vectera_PMR_Submission.zip"
    allowed_roots = {"pmr", "tests", "scripts", "docs", "inputs", ".github"}
    allowed_files = {
        "README.md",
        "SPEC.md",
        "requirements.txt",
        "pyproject.toml",
        ".gitignore",
        ".gitattributes",
        ".env.example",
        "start.cmd",
    }
    output_files = {
        "report.pdf",
        "evidence.json",
        "verification.json",
        "draft.json",
        "review.html",
        "review.md",
        "appendix.pdf",
        "repeatability.json",
        "live_repeatability.json",
        "live_repeatability_before_fallback_fix.json",
        "test-results.xml",
        "manifest.json",
        "semantic_manifest.json",
        "diagnostics.json",
        "unseen_rehearsal.json",
        "regression_matrix.json",
        "clean_install_verification.json",
        "review_ui_verification.json",
        "final_report.pdf",
        "approval.json",
        "final_evidence.json",
        "final_sections.json",
        "final_manifest.json",
        "final_semantic_manifest.json",
    }
    if not args.final:
        output_files = {n for n in output_files if not n.startswith("final_") and n != "approval.json"}
        for name in ["report.pdf", "manifest.json", "evidence.json", "verification.json"]:
            if not (root / "output" / name).is_file():
                raise SystemExit(
                    f"Draft package blocked: missing {name}. Generate the draft first."
                )
    draft_path = root / "output" / "draft.json"
    if draft_path.is_file():
        import sys

        sys.path.insert(0, str(root))
        from pmr.filenames import report_filename

        data = json.loads(draft_path.read_text(encoding="utf-8"))["data"]
        output_files.add(report_filename(data["client"], data["quarter"]))
        if args.final:
            final_name = report_filename(data["client"], data["quarter"], approved=True)
            named_pdf = root / "output" / final_name
            if not named_pdf.is_file() or named_pdf.read_bytes() != (root / "output" / "final_report.pdf").read_bytes():
                raise SystemExit("Final package blocked: named report missing or changed")
            output_files.add(final_name)
    if args.final:
        for name in [
            "final_report.pdf",
            "approval.json",
            "final_evidence.json",
            "final_manifest.json",
            "final_semantic_manifest.json",
        ]:
            if not (root / "output" / name).is_file():
                raise SystemExit(f"Final package blocked: missing {name}. Review and approve first.")
        approval = json.loads((root / "output" / "approval.json").read_text(encoding="utf-8"))
        if (
            hashlib.sha256((root / "output" / "final_report.pdf").read_bytes()).hexdigest()
            != approval["report_sha256"]
        ):
            raise SystemExit("Final package blocked: approved PDF changed")
        current_inputs = {
            str(p.relative_to(root / "inputs")): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((root / "inputs").rglob("*"))
            if p.is_file()
        }
        if current_inputs != approval.get("input_hashes"):
            raise SystemExit("Final package blocked: packaged inputs differ from approved inputs")
        import sys

        sys.path.insert(0, str(root))
        from pmr.evidence import implementation_hashes

        if implementation_hashes() != approval.get("implementation_hashes"):
            raise SystemExit("Final package blocked: implementation differs from approved draft")
    paths = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if path.name == ".env" or path.name.startswith(".env.") and path.name != ".env.example":
            continue
        if any(
            part in {".venv", ".launcher-venv", ".git", "__pycache__", ".pytest_cache", "cache"}
            for part in relative.parts
        ):
            continue
        include = relative.parts[0] in allowed_roots or str(relative) in allowed_files
        include |= relative.parts[0] == "output" and (
            len(relative.parts) == 2
            and relative.name in output_files
            or (
                len(relative.parts) > 2
                and relative.parts[1] == "assets"
                and not relative.name.startswith("qa_")
            )
        )
        if include:
            paths.append(path)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            info = zipfile.ZipInfo(
                str(path.relative_to(root)).replace("\\", "/"), date_time=(2025, 1, 1, 0, 0, 0)
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    print(f"{target} ({target.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
