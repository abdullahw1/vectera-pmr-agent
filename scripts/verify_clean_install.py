"""Unpack the submission, install pinned dependencies in a fresh venv, and verify it.

This deliberately excludes development environments and API keys. It validates
the current host only; a macOS pass is not evidence of a Windows pass.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import zipfile


def verify(package, record):
    if sys.version_info[:2] != (3, 12):
        raise ValueError("Run this verification using Python 3.12, the required evaluator version")
    environment = os.environ.copy()
    environment["PMR_LOAD_ENV"] = "0"
    for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "PYTHONPATH", "PYTHONHOME"]:
        environment.pop(key, None)
    result = dict(
        passed=False,
        python=sys.version.split()[0],
        platform=platform.platform(),
        package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),
        scope="Fresh Python 3.12 venv, pinned install, full tests and no-key generation; this host only",
    )
    try:
        with tempfile.TemporaryDirectory(prefix="pmr-clean-install-") as temporary:
            root = Path(temporary)
            project = root / "submission"
            with zipfile.ZipFile(package) as archive:
                for name in archive.namelist():
                    target = (project / name).resolve()
                    if not target.is_relative_to(project.resolve()):
                        raise ValueError("Package contains an unsafe extraction path")
                    if Path(name).name == ".env":
                        raise ValueError("Package must not contain API secrets")
                archive.extractall(project)
            subprocess.run([sys.executable, "-m", "venv", str(root / "venv")], check=True, env=environment)
            python = root / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

            def run(*arguments):
                subprocess.run([str(python), *arguments], cwd=project, env=environment, check=True)

            run("-m", "pip", "install", "--disable-pip-version-check", "-r", "requirements.txt")
            result["dependency_install_passed"] = True
            run("-m", "pytest", "-q", "--junitxml=clean-tests.xml")
            from xml.etree import ElementTree

            suites = ElementTree.parse(project / "clean-tests.xml").getroot().findall("testsuite")
            result["tests"] = sum(int(s.attrib["tests"]) for s in suites)
            result["tests_passed"] = True
            run("-m", "pmr", "generate", "--client", "CPERS", "--quarter", "4Q25", "--output", "clean-output")
            summary = json.loads((project / "clean-output/verification.json").read_text(encoding="utf-8"))
            result.update(
                checks_passed=summary["checks_passed"],
                checks_total=summary["checks_total"],
                implementation_hashes=summary["implementation_hashes"],
                expected_no_key_blockers=[i["code"] for i in summary["issues"] if i["severity"] == "blocker"],
            )
            result["passed"] = summary["checks_passed"] == summary["checks_total"]
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        result["error"] = str(error)
    finally:
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=Path("output/Vectera_PMR_Submission.zip"))
    parser.add_argument("--record", type=Path, default=Path("output/clean_install_verification.json"))
    args = parser.parse_args()
    result = verify(args.package, args.record)
    print("Clean install: " + ("PASS" if result["passed"] else "FAIL"))
    raise SystemExit(0 if result["passed"] else 1)
