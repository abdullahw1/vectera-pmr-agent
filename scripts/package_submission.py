"""Package source and submission records without keys, caches or old run folders."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile


SOURCE_FOLDERS = {"pmr", "tests", "scripts", "inputs", "fixtures", ".github", "submission"}
SOURCE_FILES = {
    "README.md", "SPEC.md", "requirements.txt", "pyproject.toml",
    ".gitignore", ".gitattributes", ".env.example", "start.cmd",
}
EXCLUDED = {".venv", ".launcher-venv", ".git", "__pycache__", ".pytest_cache", "cache", ".DS_Store"}
RUN_FILES = {
    "report.pdf", "evidence.json", "verification.json", "draft.json", "review.html",
    "review.md", "appendix.pdf", "manifest.json", "semantic_manifest.json", "diagnostics.json",
    "flash-exhibit.zip",
}
FINAL_FILES = {
    "final_report.pdf", "approval.json", "final_evidence.json", "final_sections.json",
    "final_manifest.json", "final_semantic_manifest.json",
}


def safe_file(path):
    return not any(
        part in EXCLUDED or (part.startswith(".env") and part != ".env.example")
        or part.endswith((".swp", ".swo"))
        for part in path.parts
    )


def run_files(root, folder, final):
    sys.path.insert(0, str(root))
    from pmr.filenames import report_filename

    required = {"report.pdf", "manifest.json", "evidence.json", "verification.json", "draft.json"}
    if final:
        required |= FINAL_FILES - {"final_sections.json"}
    missing = sorted(name for name in required if not (folder / name).is_file())
    if missing:
        raise ValueError("Run package blocked: missing " + ", ".join(missing))
    data = json.loads((folder / "draft.json").read_text(encoding="utf-8"))["data"]
    names = RUN_FILES | {report_filename(data["client"], data["quarter"])}
    if final:
        from pmr.evidence import implementation_hashes

        approval = json.loads((folder / "approval.json").read_text(encoding="utf-8"))
        pdf = folder / "final_report.pdf"
        named = report_filename(data["client"], data["quarter"], approved=True)
        if hashlib.sha256(pdf.read_bytes()).hexdigest() != approval["report_sha256"]:
            raise ValueError("Final package blocked: approved PDF changed")
        if not (folder / named).is_file() or (folder / named).read_bytes() != pdf.read_bytes():
            raise ValueError("Final package blocked: named report missing or changed")
        current_inputs = {
            str(p.relative_to(root / "inputs")): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((root / "inputs").rglob("*")) if p.is_file()
        }
        if current_inputs != approval.get("input_hashes"):
            raise ValueError("Final package blocked: packaged inputs differ from approved inputs")
        if implementation_hashes() != approval.get("implementation_hashes"):
            raise ValueError("Final package blocked: implementation differs from approved draft")
        names |= FINAL_FILES | {named}
    return [
        (p, "run/" + p.relative_to(folder).as_posix())
        for p in sorted(folder.rglob("*"))
        if p.is_file() and safe_file(p.relative_to(folder))
        and (p.name in names and p.parent == folder or p.relative_to(folder).parts[0] == "assets")
    ]


def build_package(root, target, *, run_dir=None, final=False):
    root, target = root.resolve(), target.resolve()
    if final and run_dir is None:
        raise ValueError("Use --run-dir to select the approved run for --final")
    # Never sweep the whole working tree: only the named source folders are eligible.
    paths = [(root / name, name) for name in sorted(SOURCE_FILES) if (root / name).is_file()]
    for name in sorted(SOURCE_FOLDERS):
        paths.extend(
            (p, p.relative_to(root).as_posix())
            for p in sorted((root / name).rglob("*"))
            if p.is_file() and safe_file(p.relative_to(root)) and p.resolve() != target
        )
    if run_dir is not None:
        paths.extend(run_files(root, run_dir.resolve(), final))
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, name in paths:
            info = zipfile.ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, help="Optionally include one generated run")
    parser.add_argument("--final", action="store_true", help="Require a valid approved run")
    parser.add_argument("--destination", type=Path, default=Path("output/Vectera_PMR_Submission.zip"))
    args = parser.parse_args()
    try:
        target = build_package(
            Path(__file__).resolve().parents[1], args.destination,
            run_dir=args.run_dir, final=args.final,
        )
    except (ValueError, OSError, KeyError) as error:
        raise SystemExit(str(error)) from error
    print(f"{target} ({target.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
