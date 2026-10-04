"""Local workspace routing and document isolation; no provider calls required."""

import base64
import io
import json
import zipfile
from unittest.mock import Mock

import pytest

from pmr.workspace import Workspace


@pytest.fixture
def workspace(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / "flash.xlsx").touch()
    (inputs / "prior.pdf").touch()
    return Workspace(inputs, tmp_path / "output")


def document(path="manager_reports/report.pdf"):
    return dict(path=path, data=base64.b64encode(b"synthetic source").decode())


def test_upload_preserves_folders(workspace):
    result = workspace.upload(dict(files=[document()]))
    assert result["count"] == 1
    assert (workspace.output / "uploads").is_relative_to(workspace.output)
    from pathlib import Path

    assert (Path(result["inputs"]) / "manager_reports/report.pdf").read_bytes() == b"synthetic source"


@pytest.mark.parametrize(
    "path", ["../secret.pdf", "/secret.pdf", ".env", "nested/.private.pdf", "a\\report.pdf", "report.txt"]
)
def test_upload_rejects_unsafe_paths(workspace, path):
    with pytest.raises(ValueError):
        workspace.upload(dict(files=[document(path)]))
    assert not (workspace.output / "uploads").exists()


@pytest.mark.parametrize(
    "files", [[], [None], [document(), document()], [dict(path="x.pdf", data="invalid!")]]
)
def test_upload_rejects_invalid_packages(workspace, files):
    with pytest.raises(ValueError):
        workspace.upload(dict(files=files))


def test_generate_validates_before_starting_worker(workspace, monkeypatch):
    worker = Mock()
    monkeypatch.setattr("pmr.workspace.threading.Thread", worker)
    for request in [
        dict(client="", quarter="4Q25"),
        dict(client="CPERS", quarter="5Q25"),
        dict(client="CPERS", quarter="4Q25", inputs="/does/not/exist"),
    ]:
        with pytest.raises(ValueError):
            workspace.create(request)
    worker.assert_not_called()
    job = workspace.create(dict(client="CPERS", quarter="4q25"))
    assert job["quarter"] == "4Q25"
    assert workspace.state()["active"] == job["id"]
    with pytest.raises(ValueError, match="already running"):
        workspace.create(dict(client="CPERS", quarter="4Q25"))
    worker.return_value.start.assert_called_once()


def test_restart_marks_interrupted_runs_failed(workspace, monkeypatch):
    monkeypatch.setattr("pmr.workspace.threading.Thread", Mock())
    job = workspace.create(dict(client="CPERS", quarter="4Q25"))
    restored = Workspace(workspace.inputs, workspace.output)
    assert restored.state()["active"] is None
    assert restored.jobs[job["id"]]["status"] == "failed"


def test_browser_artifacts_and_bundle_exclude_secrets(workspace):
    workspace.jobs["current"] = dict(id="current", status="draft", created=1)
    (workspace.output / "report.pdf").write_bytes(b"report")
    (workspace.output / ".env").write_text("PRIVATE=value")
    (workspace.output / "run.log").write_text("private diagnostics")
    for path in [".env", "run.log", "../report.pdf", "cache/provider.json"]:
        with pytest.raises(ValueError):
            workspace.artifact("current", path)
    with pytest.raises(ValueError):
        workspace.artifact("unknown", "report.pdf")
    assert workspace.artifact("current", "report.pdf").read_bytes() == b"report"
    with zipfile.ZipFile(io.BytesIO(workspace.bundle("current"))) as bundle:
        assert bundle.namelist() == ["report.pdf"]


def test_named_report_downloads_and_bundle(workspace):
    import json

    workspace.jobs["current"] = dict(id="current", client="CPERS", quarter="4Q25", status="draft", created=1)
    (workspace.output / "draft.json").write_text(json.dumps({"data": {"client": "CPERS", "quarter": "4Q25"}}))
    name = "CPERS_PMR_4Q25_DRAFT.pdf"
    (workspace.output / name).write_bytes(b"named draft")
    assert workspace.artifact("current", name).read_bytes() == b"named draft"
    assert workspace.snapshot(workspace.jobs["current"])["report_filename"] == name
    with pytest.raises(ValueError):
        workspace.artifact("current", "OTHER_PMR_4Q25.pdf")
    with zipfile.ZipFile(io.BytesIO(workspace.bundle("current"))) as bundle:
        assert name in bundle.namelist()


def test_worker_failure_is_visible_and_releases_active(workspace, monkeypatch):
    monkeypatch.setattr("pmr.workspace.threading.Thread", Mock())
    job = workspace.create(dict(client="CPERS", quarter="4Q25"))
    process = Mock()
    process.wait.return_value = 1
    monkeypatch.setattr("pmr.workspace.subprocess.Popen", Mock(return_value=process))
    (workspace.directory(job["id"]) / "failure.json").write_text(
        json.dumps(dict(reason="No matching client"))
    )
    workspace.run(job["id"])
    result = workspace.state()["runs"][0]
    assert result["status"] == "failed"
    assert result["error_details"] == "No matching client"
    assert result["error_title"] == "Report generation stopped"
    assert workspace.active is None


@pytest.fixture
def handler(workspace, monkeypatch):
    # Exercise routing without opening a socket in restricted development sandboxes.
    from pmr.workspace import make_server

    server = Mock()
    monkeypatch.setattr("http.server.ThreadingHTTPServer", server)
    monkeypatch.setattr("pmr.workspace.secrets.token_urlsafe", lambda _: "test-token")
    make_server(workspace, 8888)
    instance = object.__new__(server.call_args.args[1])
    instance.server = Mock(server_port=8888)
    instance.reply = Mock()
    instance.headers = {"Host": "127.0.0.1:8888", "X-PMR-Token": "test-token"}
    return instance


@pytest.mark.parametrize(
    "headers",
    [
        {"Host": "external.example:8888", "X-PMR-Token": "test-token"},
        {"Host": "127.0.0.1:8888"},
        {"Host": "127.0.0.1:8888", "X-PMR-Token": "test-token", "Origin": "https://external.example"},
    ],
)
def test_write_routes_require_local_host_token_and_origin(handler, headers):
    handler.headers = headers
    handler.do_POST()
    assert handler.reply.call_args.args[0] == 403


@pytest.mark.parametrize("body", [b"not json", b"[]", b'{"files":[null]}'])
def test_bad_requests_return_explicit_error(handler, body):
    handler.path = "/api/upload"
    handler.headers["Content-Length"] = str(len(body))
    handler.rfile = io.BytesIO(body)
    handler.do_POST()
    assert handler.reply.call_args.args[0] == 400


def test_http_upload_accepts_valid_document(handler):
    body = json.dumps(dict(files=[document()])).encode()
    handler.path = "/api/upload"
    handler.headers["Content-Length"] = str(len(body))
    handler.rfile = io.BytesIO(body)
    handler.do_POST()
    assert handler.reply.call_args.args[0] == 200
    assert handler.reply.call_args.args[1]["count"] == 1


def test_unknown_bundle_is_404(handler):
    handler.path = "/runs/missing/bundle.zip"
    handler.do_GET()
    assert handler.reply.call_args.args[0] == 404
