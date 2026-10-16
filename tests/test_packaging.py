"""Clean source packaging must work before generation and exclude local secrets."""

import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest


spec = importlib.util.spec_from_file_location(
    "package_submission", Path(__file__).parents[1] / "scripts/package_submission.py"
)
packaging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packaging)


def put(root, name, content="example"):
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def test_clean_checkout_packages_without_generated_output(tmp_path):
    for name in ["README.md", "pmr/web/index.html", "tests/test_example.py",
                 "inputs/manager_reports/fund.pdf", "submission/v1-execution.json"]:
        put(tmp_path, name)
    target = packaging.build_package(tmp_path, tmp_path / "output/submission.zip")
    with zipfile.ZipFile(target) as archive:
        names = archive.namelist()
        assert "inputs/manager_reports/fund.pdf" in names
        assert "submission/v1-execution.json" in names
        assert all("\\" not in name for name in names)
        assert not any(name.startswith("output/") for name in names)


@pytest.mark.parametrize("name", [
    ".env", "pmr/.env", "inputs/.env.local", "tests/__pycache__/test.pyc",
    "pmr/web/.DS_Store", "scripts/.edit.swp", "output/stale-report.pdf",
])
def test_package_excludes_secrets_and_scratch_files(tmp_path, name):
    put(tmp_path, name, "must not ship")
    put(tmp_path, ".env.example", "OPENAI_API_KEY=")
    target = packaging.build_package(tmp_path, tmp_path / "package.zip")
    with zipfile.ZipFile(target) as archive:
        assert name not in archive.namelist()
        assert ".env.example" in archive.namelist()


def test_final_package_requires_selected_run(tmp_path):
    with pytest.raises(ValueError, match="--run-dir"):
        packaging.build_package(tmp_path, tmp_path / "package.zip", final=True)


def test_incomplete_selected_run_is_not_packaged(tmp_path):
    with pytest.raises(ValueError, match="missing"):
        packaging.build_package(tmp_path, tmp_path / "package.zip", run_dir=tmp_path / "run")
    assert not (tmp_path / "package.zip").exists()


@pytest.mark.parametrize("change", [None, "pdf", "inputs", "implementation", "named"])
def test_final_package_checks_approval_bindings(tmp_path, monkeypatch, change):
    import pmr.evidence

    run = tmp_path / "generated"
    for name in packaging.RUN_FILES | packaging.FINAL_FILES:
        put(run, name)
    put(tmp_path, "inputs/source.txt", "source")
    put(run, "draft.json", json.dumps({"data": {"client": "CPERS", "quarter": "1Q26"}}))
    put(run, "CPERS_PMR_1Q26.pdf")
    code = {"report.py": "hash"}
    monkeypatch.setattr(pmr.evidence, "implementation_hashes", lambda: code)
    approval = {
        "report_sha256": hashlib.sha256((run / "final_report.pdf").read_bytes()).hexdigest(),
        "input_hashes": {"source.txt": hashlib.sha256((tmp_path / "inputs/source.txt").read_bytes()).hexdigest()},
        "implementation_hashes": dict(code),
    }
    put(run, "approval.json", json.dumps(approval))
    if change == "pdf":
        put(run, "final_report.pdf", "changed")
    elif change == "inputs":
        put(tmp_path, "inputs/source.txt", "changed")
    elif change == "implementation":
        code["report.py"] = "changed"
    elif change == "named":
        put(run, "CPERS_PMR_1Q26.pdf", "changed")
    if change:
        with pytest.raises(ValueError, match="Final package blocked"):
            packaging.build_package(tmp_path, tmp_path / "package.zip", run_dir=run, final=True)
    else:
        target = packaging.build_package(tmp_path, tmp_path / "package.zip", run_dir=run, final=True)
        with zipfile.ZipFile(target) as archive:
            assert "run/CPERS_PMR_1Q26.pdf" in archive.namelist()
