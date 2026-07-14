"""Publish a locally-staged workspace directory to wherever the pod can read it.

The pod holds no state and shares no filesystem with this backend in a decoupled deployment, so a
gathered workspace must be handed over by reference. Two transports:

- ``file`` — return a ``file://`` path. The pod copies from a path it can already see, which assumes
  it shares this host's filesystem (single-host dev only).
- ``minio`` — archive the directory, upload it to an S3-compatible store, and return a pre-signed
  https URL the pod pulls over the network. The pod shares no disk with this backend.

Each publish returns the source string plus a cleanup to run after the run (delete the uploaded
object for ``minio``; a no-op for ``file``). The local directory's own lifecycle is the caller's.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import tarfile
import tempfile
import uuid
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def no_cleanup() -> None:
    """A cleanup that does nothing (the ``file`` transport leaves nothing to remove)."""


async def publish_workspace(
    local_dir: str | None, settings: Settings
) -> tuple[str | None, Callable[[], None]]:
    """Turn a local workspace directory into a source the pod can read, plus a post-run cleanup.

    Returns ``(None, no_cleanup)`` when there is no directory (a tool-less run). For ``minio`` the
    upload runs in a worker thread since the client is blocking.
    """
    if local_dir is None:
        return None, no_cleanup
    if settings.workspace_transport == "minio":
        return await asyncio.to_thread(_publish_minio, local_dir, settings)
    return f"file://{local_dir}", no_cleanup


def _publish_minio(local_dir: str, settings: Settings) -> tuple[str, Callable[[], None]]:
    """Archive the directory, upload it, and return a pre-signed GET URL plus an object-delete
    cleanup. Blocking — run off the event loop."""
    if not settings.minio_endpoint:
        raise RuntimeError("workspace_transport is 'minio' but MINIO_ENDPOINT is not set")
    client = _minio_client(settings)
    bucket = settings.minio_bucket
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    object_name = f"{uuid.uuid4()}.tar.gz"
    archive = _tar_dir(local_dir)
    try:
        client.fput_object(bucket, object_name, archive, content_type="application/gzip")
    finally:
        Path(archive).unlink(missing_ok=True)

    url = client.presigned_get_object(
        bucket, object_name, expires=timedelta(seconds=settings.minio_url_expiry_seconds)
    )
    logger.info(
        "published workspace to %s/%s (pre-signed, pod pulls over network)", bucket, object_name
    )

    def cleanup() -> None:
        with contextlib.suppress(Exception):
            client.remove_object(bucket, object_name)

    return url, cleanup


def _minio_client(settings: Settings) -> Any:
    from minio import Minio

    http_client = None
    if settings.minio_secure and not settings.minio_cert_check:
        import urllib3

        urllib3.disable_warnings()
        http_client = urllib3.PoolManager(cert_reqs="CERT_NONE")  # accept a self-signed dev cert
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
        http_client=http_client,
    )


def _tar_dir(local_dir: str) -> str:
    """Pack the directory's contents (flat, no wrapping top-level dir) into a temp .tar.gz, so the
    pod extracts the files straight into its working directory — matching the file:// copy."""
    fd, path = tempfile.mkstemp(suffix=".tar.gz", prefix="bgp-ws-")
    os.close(fd)
    with tarfile.open(path, "w:gz") as tar:
        for item in sorted(Path(local_dir).iterdir()):
            tar.add(item, arcname=item.name)
    return path
