"""Local browser workflow; report generation stays in an isolated Python process."""
from __future__ import annotations

import base64
import io
import json
import mimetypes
import os
from pathlib import Path, PurePosixPath
import secrets
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse
import uuid
import zipfile

from .ingest import quarter
from .review import approve
from .errors import explain_failure

ARTIFACTS = {"report.pdf", "final_report.pdf", "appendix.pdf", "review.html", "review.md", "draft.json",
             "evidence.json", "verification.json", "manifest.json", "semantic_manifest.json", "agent_trace.json",
             "diagnostics.json", "approval.json", "final_evidence.json", "final_sections.json",
             "final_manifest.json", "final_semantic_manifest.json"}
MAX_BODY = 40_000_000


def read_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


class Workspace:
    def __init__(self, inputs, output, client=None, period=None):
        self.inputs, self.output = inputs.resolve(), output.resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.active = None
        self.process = None
        self.jobs = {}
        for path in (self.output / "runs").glob("*/.run.json"):
            job = read_json(path)
            if job and path.parent.name == job.get("id"):
                if job["status"] in {"queued", "running"}:
                    job.update(status="failed", error="Application stopped during this run; generate a new draft.")
                self.jobs[job["id"]] = job
        draft = read_json(self.output / "draft.json", {})
        self.defaults = dict(client=client or draft.get("data", {}).get("client", ""),
                             quarter=period or draft.get("data", {}).get("quarter", ""), inputs=str(self.inputs))
        if draft:
            self.jobs["current"] = dict(id="current", client=draft["data"]["client"], quarter=draft["data"]["quarter"],
                                        inputs=str(self.inputs), status="draft", created=(self.output / "draft.json").stat().st_mtime, existing=True)

    def directory(self, identifier):
        if identifier not in self.jobs:
            raise ValueError("Unknown run")
        return self.output if identifier == "current" else self.output / "runs" / identifier

    def snapshot(self, job):
        result = dict(job)
        if job.get("error") and not job.get("error_details"):
            result.update(explain_failure(job["error"], job.get("client", ""), job.get("quarter", "")))
        folder = self.directory(job["id"])
        result["progress"] = read_json(folder / "progress.json", {})
        summary = read_json(folder / "verification.json")
        if summary:
            issues = summary["issues"]
            result.update(checks_passed=summary["checks_passed"], checks_total=summary["checks_total"],
                          blockers=sum(i["severity"] == "blocker" for i in issues),
                          warnings=sum(i["severity"] == "warning" for i in issues),
                          charts=sum(i["severity"] == "review" for i in issues))
        if (folder / "approval.json").exists():
            result["status"] = "approved"
        return result

    def state(self):
        with self.lock:
            return dict(defaults=self.defaults, active=self.active,
                        runs=[self.snapshot(j) for j in sorted(self.jobs.values(), key=lambda j: j["created"], reverse=True)])

    def create(self, request):
        client = str(request.get("client", "")).strip()
        period = str(request.get("quarter", "")).strip().upper()
        if not client or len(client) > 80 or not quarter(period) or len(period) != 4:
            raise ValueError("Enter a client code and quarter in 4Q25 format")
        source = Path(str(request.get("inputs") or self.inputs)).expanduser().resolve()
        if not source.is_dir():
            raise ValueError("The source folder does not exist on this computer")
        if not any(source.rglob("*.xlsx")) or not any(source.rglob("*.pdf")):
            raise ValueError("Choose the document package folder containing spreadsheets and PDFs")
        with self.lock:
            if self.active:
                raise ValueError("A report is already running. Wait for it to finish before starting another.")
            identifier = uuid.uuid4().hex[:12]
            job = dict(id=identifier, client=client, quarter=period, inputs=str(source), status="queued", created=time.time())
            self.jobs[identifier] = job
            self.active = identifier
            folder = self.directory(identifier)
            folder.mkdir(parents=True)
            self.save(job)
        threading.Thread(target=self.run, args=(identifier,), daemon=True).start()
        return dict(job)

    def save(self, job):
        if job["id"] != "current":
            (self.directory(job["id"]) / ".run.json").write_text(json.dumps(job), encoding="utf-8")

    def run(self, identifier):
        job = self.jobs[identifier]
        folder = self.directory(identifier)
        try:
            with self.lock:
                job["status"] = "running"
                self.save(job)
            # No shell interpolation; credentials are inherited, never sent to the browser.
            command = [sys.executable, "-m", "pmr", "generate", "--client", job["client"], "--quarter", job["quarter"],
                       "--inputs", job["inputs"], "--output", str(folder)]
            with (folder / "run.log").open("w", encoding="utf-8") as log:
                process = subprocess.Popen(command, cwd=Path(__file__).resolve().parents[1], stdout=log, stderr=log,
                                           env=os.environ.copy())
                with self.lock:
                    self.process = process
                result = process.wait()
            failure = read_json(folder / "failure.json", {})
            with self.lock:
                job["status"] = "draft" if result == 0 else "failed"
                if result:
                    job.update(explain_failure(failure.get("reason", "Generation failed. Inspect the local run.log for diagnostics."), job["client"], job["quarter"]))
        except OSError:
            with self.lock:
                job.update(status="failed", error="The local Python worker could not start or save its output.")
        finally:
            with self.lock:
                self.active = None
                self.process = None
                self.save(job)

    def upload(self, request):
        files = request.get("files")
        if not isinstance(files, list) or not 0 < len(files) <= 100:
            raise ValueError("Select a source folder with 1-100 supported documents")
        decoded = []
        total = 0
        seen = set()
        for item in files:
            if not isinstance(item, dict):
                raise ValueError("Each uploaded document must include a path and data")
            path = PurePosixPath(str(item.get("path", "")))
            if path.is_absolute() or any(p in {"..", "."} or p.startswith(".") for p in path.parts) or "\\" in str(path):
                raise ValueError("Invalid uploaded document path")
            if path.suffix.lower() not in {".pdf", ".xlsx", ".pptx"} or str(path) in seen:
                raise ValueError("Upload only unique PDF, XLSX and PPTX documents")
            seen.add(str(path))
            try:
                content = base64.b64decode(item["data"], validate=True)
            except (ValueError, KeyError, TypeError):
                raise ValueError("Invalid uploaded document data") from None
            total += len(content)
            if total > 25_000_000:
                raise ValueError("The document package exceeds the 25 MB upload limit; use its local folder path instead")
            decoded.append((path, content))
        folder = self.output / "uploads" / uuid.uuid4().hex[:12]
        for path, content in decoded:
            target = folder / str(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        return dict(inputs=str(folder), count=len(decoded))

    def artifact(self, identifier, relative):
        folder = self.directory(identifier)
        path = (folder / relative).resolve()
        if not path.is_relative_to(folder.resolve()):
            raise ValueError("Invalid artifact path")
        if relative not in ARTIFACTS and not (relative.startswith("assets/") and path.suffix == ".png"):
            raise ValueError("Artifact is not available through the browser")
        if not path.is_file():
            raise ValueError("Artifact is not available yet")
        return path

    def bundle(self, identifier):
        folder = self.directory(identifier)
        if self.jobs[identifier]["status"] not in {"draft", "approved"}:
            raise ValueError("Wait for a draft before downloading its audit bundle")
        result = io.BytesIO()
        with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as archive:
            for name in sorted(ARTIFACTS - {"review.html"}):
                if (folder / name).is_file():
                    archive.write(folder / name, name)
            for path in (folder / "assets").glob("*.png"):
                archive.write(path, "assets/" + path.name)
        return result.getvalue()

    def stop(self):
        with self.lock:
            process = self.process
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def make_server(workspace, port=0):
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    token = secrets.token_urlsafe(32)
    web = Path(__file__).parent / "web"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, content, content_type="application/json"):
            if isinstance(content, dict):
                content = json.dumps(content).encode()
            elif isinstance(content, str):
                content = content.encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(content)

        def valid_host(self):
            return self.headers.get("Host") in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

        def do_GET(self):
            if not self.valid_host():
                self.reply(403, dict(message="Invalid local host")); return
            path = urlparse(self.path).path
            try:
                if path in {"/", "/index.html"}:
                    boot = json.dumps(dict(token=token)).replace("<", "\\u003c")
                    self.reply(200, (web / "index.html").read_text().replace("__BOOT__", boot), "text/html; charset=utf-8")
                elif path == "/api/state":
                    self.reply(200, workspace.state())
                elif path.startswith("/icons/"):
                    icon = (web / path.lstrip("/")).resolve()
                    if not icon.is_relative_to((web / "icons").resolve()) or icon.suffix != ".svg":
                        raise ValueError("Invalid icon")
                    self.reply(200, icon.read_bytes(), "image/svg+xml")
                elif path.startswith("/runs/"):
                    _, _, identifier, relative = path.split("/", 3)
                    if relative == "bundle.zip":
                        self.reply(200, workspace.bundle(identifier), "application/zip")
                    else:
                        file = workspace.artifact(identifier, relative)
                        if relative == "review.html":
                            page = file.read_text().replace("fetch('/approve'", "fetch('approve'")
                            if "X-PMR-Token" not in page:
                                page = page.replace("'Content-Type':'application/json'", "'Content-Type':'application/json','X-PMR-Token':window.PMR_CSRF||''")
                            page = page.replace("<script>", "<script>window.PMR_CSRF=" + json.dumps(token) + ";</script><script>", 1)
                            self.reply(200, page, "text/html; charset=utf-8")
                        else:
                            self.reply(200, file.read_bytes(), mimetypes.guess_type(file.name)[0] or "application/octet-stream")
                else:
                    self.reply(404, dict(message="Not found"))
            except (ValueError, KeyError, OSError):
                self.reply(404, dict(message="Requested artifact is not available"))

        def do_POST(self):
            origin = self.headers.get("Origin")
            if not self.valid_host() or self.headers.get("X-PMR-Token") != token or origin and origin != "http://" + self.headers["Host"]:
                self.reply(403, dict(message="Reload the local workspace before making changes")); return
            try:
                length = int(self.headers.get("Content-Length", 0))
                if not 0 < length <= MAX_BODY:
                    raise ValueError("Invalid request size")
                request = json.loads(self.rfile.read(length))
                if not isinstance(request, dict):
                    raise ValueError("Request must be an object")
                path = urlparse(self.path).path
                if path == "/api/generate":
                    self.reply(202, workspace.create(request))
                elif path == "/api/upload":
                    self.reply(200, workspace.upload(request))
                elif path.startswith("/runs/") and path.endswith("/approve"):
                    identifier = path.split("/")[2]
                    approve(workspace.directory(identifier), request)
                    self.reply(200, dict(message="Approved. The final PDF and approval record are saved."))
                else:
                    self.reply(404, dict(message="Not found"))
            except (ValueError, KeyError, TypeError):
                error = sys.exc_info()[1]
                self.reply(400, dict(message=str(error)))
            except OSError:
                self.reply(500, dict(message="The local file operation failed. Check folder permissions and available disk space."))

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve_workspace(inputs, output, client=None, period=None, port=0, open_browser=True):
    workspace = Workspace(inputs, output, client, period)
    try:
        with make_server(workspace, port) as server:
            url = f"http://127.0.0.1:{server.server_port}/"
            print(f"PMR workspace: {url}\nKeep this terminal open. Press Ctrl+C to stop.", flush=True)
            if open_browser:
                import webbrowser
                webbrowser.open(url)
            server.serve_forever()
    finally:
        workspace.stop()
