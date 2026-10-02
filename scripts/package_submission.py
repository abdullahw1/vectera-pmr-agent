"""Build a small, reproducible zip without keys, environments or scratch files."""
from pathlib import Path
import zipfile


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / "output" / "Vectera_PMR_Submission.zip"
    allowed_roots = {"pmr", "tests", "scripts", "docs", "inputs", ".github"}
    allowed_files = {"README.md", "RUNNING.md", "SPEC.md", "requirements.txt", "pyproject.toml", ".gitignore", ".env.example", "start.cmd"}
    output_files = {"report.pdf", "writeup.pdf", "evidence.json", "verification.json", "draft.json", "review.html", "appendix.pdf", "repeatability.json", "test-results.xml"}
    paths = []
    for path in root.rglob("*"):
        if not path.is_file(): continue
        relative = path.relative_to(root)
        if any(part in {".venv", ".launcher-venv", ".git", "__pycache__", ".pytest_cache", "cache"} for part in relative.parts): continue
        include = relative.parts[0] in allowed_roots or str(relative) in allowed_files
        include |= relative.parts[0] == "output" and (relative.name in output_files or
                    (len(relative.parts) > 2 and relative.parts[1] == "assets" and not relative.name.startswith("qa_")))
        if include: paths.append(path)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            info = zipfile.ZipInfo(str(path.relative_to(root)).replace("\\", "/"), date_time=(2025, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    print(f"{target} ({target.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__": main()
