"""Standard-library bootstrap: install once, then launch the local PMR workflow."""
import hashlib
from pathlib import Path
import subprocess
import sys
import venv


def prepare(root):
    """Use a dedicated environment; reinstall only when the manifest changes."""
    environment = root / ".launcher-venv"
    python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    marker = environment / ".requirements.sha256"
    requirements = root / "requirements.txt"
    digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
    if not python.exists():
        print("Preparing the local Python environment...", flush=True)
        venv.EnvBuilder(with_pip=True).create(environment)
    if not marker.exists() or marker.read_text().strip() != digest:
        print("Installing pinned dependencies (first launch or manifest update)...", flush=True)
        subprocess.run([str(python), "-m", "pip", "install", "-r", str(requirements)], check=True, cwd=root)
        # Write only after successful installation so failed setups are retried.
        marker.write_text(digest, encoding="ascii")
    return python


def main():
    if sys.version_info < (3, 12):
        print("Python 3.12 or newer is required.", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parents[1]
    try:
        python = prepare(root)
        return subprocess.run([str(python), "-m", "pmr", "start", *sys.argv[1:]], cwd=root).returncode
    except subprocess.CalledProcessError:
        print("Dependency installation failed. Check internet access and retry; setup will resume.", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"Local setup could not complete: {error}. Check that the extracted folder is writable.", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
