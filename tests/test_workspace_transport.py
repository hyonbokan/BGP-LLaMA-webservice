"""Publishing a staged workspace to the pod: the file:// path and the MinIO upload.

The MinIO client is faked at the _minio_client seam, so these run without the native library or a
live store. Async entry points are driven with asyncio.run (this suite doesn't use pytest-asyncio).
"""

import asyncio
import tarfile
from types import SimpleNamespace

import pytest

import app.llm.workspace as workspace_mod
from app.llm.workspace import no_cleanup, publish_workspace


def _settings(**overrides):
    base = {
        "workspace_transport": "file",
        "minio_endpoint": "",
        "minio_access_key": "",
        "minio_secret_key": "",
        "minio_bucket": "bgp-workspaces",
        "minio_secure": True,
        "minio_url_expiry_seconds": 3600,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


class _FakeMinio:
    """Records the calls _publish_minio makes, and inspects the archive it uploads."""

    def __init__(self):
        self.buckets: set[str] = set()
        self.objects: dict[tuple[str, str], str] = {}
        self.removed: list[tuple[str, str]] = []
        self.tar_members: list[str] | None = None

    def bucket_exists(self, bucket):
        return bucket in self.buckets

    def make_bucket(self, bucket):
        self.buckets.add(bucket)

    def fput_object(self, bucket, name, path, content_type=None):
        with tarfile.open(path) as tar:
            self.tar_members = sorted(m.name for m in tar.getmembers())
        self.objects[(bucket, name)] = path

    def presigned_get_object(self, bucket, name, expires=None):
        return f"https://minio:9000/{bucket}/{name}?X-Amz-Signature=fake"

    def remove_object(self, bucket, name):
        self.removed.append((bucket, name))


def test_no_workspace_returns_none_and_a_noop_cleanup():
    source, cleanup = asyncio.run(publish_workspace(None, _settings()))
    assert source is None
    assert cleanup is no_cleanup


def test_file_transport_returns_a_file_uri(tmp_path):
    source, cleanup = asyncio.run(publish_workspace(str(tmp_path), _settings()))
    assert source == f"file://{tmp_path}"
    assert cleanup is no_cleanup


def test_minio_transport_uploads_flat_archive_and_presigns(monkeypatch, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "updates.json").write_text("[]")
    (ws / "manifest.json").write_text("{}")

    fake = _FakeMinio()
    monkeypatch.setattr(workspace_mod, "_minio_client", lambda settings: fake)

    source, cleanup = asyncio.run(
        publish_workspace(str(ws), _settings(workspace_transport="minio", minio_endpoint="minio:9000"))
    )

    assert source.startswith("https://minio:9000/bgp-workspaces/")
    assert "bgp-workspaces" in fake.buckets
    # Files are packed flat, so the pod extracts them straight into its working directory.
    assert fake.tar_members == ["manifest.json", "updates.json"]

    uploaded = next(iter(fake.objects))
    cleanup()
    assert fake.removed == [uploaded]  # the cleanup drops the uploaded object


def test_minio_transport_without_endpoint_raises():
    with pytest.raises(RuntimeError, match="MINIO_ENDPOINT"):
        asyncio.run(publish_workspace("/some/dir", _settings(workspace_transport="minio")))
