import app.api.routes.files as files_module
from app.core.config import Settings


def _use_dataset_root(monkeypatch, path):
    monkeypatch.setattr(
        files_module, "get_settings", lambda: Settings(_env_file=None, dataset_root=str(path))
    )


def test_download_success(client, tmp_path, monkeypatch):
    (tmp_path / "report.txt").write_text("hello")
    _use_dataset_root(monkeypatch, tmp_path)

    resp = client.get("/api/download?file=report.txt")
    assert resp.status_code == 200
    assert resp.content == b"hello"


def test_download_missing_is_404(client, tmp_path, monkeypatch):
    _use_dataset_root(monkeypatch, tmp_path)
    assert client.get("/api/download?file=nope.txt").status_code == 404


def test_download_traversal_blocked(client, tmp_path, monkeypatch):
    _use_dataset_root(monkeypatch, tmp_path)
    assert client.get("/api/download?file=../../etc/passwd").status_code == 404


def test_download_absolute_path_contained(client, tmp_path, monkeypatch):
    _use_dataset_root(monkeypatch, tmp_path)
    # Leading slash is stripped, so this resolves inside DATASET_ROOT (and 404s).
    assert client.get("/api/download?file=/etc/passwd").status_code == 404
