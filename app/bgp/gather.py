"""Gather scoped BGP updates with pybgpstream and stage them for the agent.

The agent never fetches; the backend does it here, up front, so a slow network read
happens under the backend's own timeout rather than inside a tool call. Each collector
is read concurrently in a worker thread (the native stream read is blocking), the
elements are reduced to compact records, and the result is written as ``updates.json``
plus a manifest into a throwaway directory the caller stages as the workspace.

pybgpstream is imported lazily, so this module loads and unit-tests without the native
BGPStream library; a host that lacks it raises GatherUnavailable and the caller falls
back to a statically staged directory.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from app.bgp.fetch_plan import FetchSpec
from app.bgp.records import collect_records
from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_UPDATES_FILE = "updates.json"
_MANIFEST_FILE = "manifest.json"
_RECORD_FIELDS = ["time", "type", "peer_asn", "prefix", "as_path", "origin", "communities", "med"]


class GatherUnavailable(RuntimeError):
    """The pybgpstream runtime is not installed, so a live gather can't run on this host."""


class GatherError(RuntimeError):
    """A live gather was attempted but failed (stream error, timeout, or a staging write)."""


async def gather_and_stage(plan: FetchSpec, settings: Settings) -> str:
    """Gather the plan's updates, reduce them to records, and stage them in a fresh directory.

    Reads every collector concurrently under the configured wall-clock timeout, then writes
    ``updates.json`` and a manifest describing the scope. Returns the staging directory path
    for the caller to hand to the pod as a read-only workspace and reap afterward. Raises
    GatherUnavailable when pybgpstream is absent, or GatherError on any gather or write failure.
    """
    try:
        records, truncated = await asyncio.wait_for(
            _gather_records(plan, settings), timeout=settings.bgp_gather_timeout_seconds
        )
    except GatherUnavailable:
        raise
    except TimeoutError as e:
        raise GatherError(f"gather timed out after {settings.bgp_gather_timeout_seconds}s") from e
    except Exception as e:
        raise GatherError(str(e)) from e

    stage_dir = _new_stage_dir(settings)
    try:
        _write_dataset(stage_dir, plan, records, truncated)
    except OSError as e:
        reap_stage(stage_dir)
        raise GatherError(f"failed to stage dataset: {e}") from e

    logger.info(
        "staged %d BGP record(s) for %s at %s (truncated=%s)",
        len(records),
        plan.prefixes or f"AS{plan.target_asn}",
        stage_dir,
        truncated,
    )
    return stage_dir


def reap_stage(stage_dir: str) -> None:
    """Remove a staged dataset directory. Best-effort — a failed reap must not crash a run."""
    shutil.rmtree(stage_dir, ignore_errors=True)


async def _gather_records(plan: FetchSpec, settings: Settings) -> tuple[list[dict[str, Any]], bool]:
    """Read every collector concurrently and merge their records, time-ordered."""
    reads = [
        asyncio.to_thread(_read_collector, plan, collector, settings)
        for collector in plan.collectors
    ]
    per_collector = await asyncio.gather(*reads)
    records: list[dict[str, Any]] = []
    truncated = False
    for recs, trunc in per_collector:
        records.extend(recs)
        truncated = truncated or trunc
    records.sort(key=lambda record: record.get("time") or 0)
    return records, truncated


def _read_collector(
    plan: FetchSpec, collector: str, settings: Settings
) -> tuple[list[dict[str, Any]], bool]:
    """Blocking: open a stream for one collector and shape its elements into records."""
    stream = _open_stream(plan, collector)
    return collect_records(stream, settings.bgp_gather_max_records)


def _open_stream(plan: FetchSpec, collector: str) -> Any:
    """Build a configured pybgpstream stream, filtered to the plan's scope.

    Filters by prefix (matching the prefix, its more- and less-specifics, so a sub-prefix
    hijack is caught); when only an ASN is scoped, filters by that origin instead.
    """
    try:
        import pybgpstream
    except ImportError as e:
        raise GatherUnavailable("pybgpstream is not installed on this host") from e

    stream = pybgpstream.BGPStream(
        from_time=plan.from_time,
        until_time=plan.until_time,
        collectors=[collector],
        record_type="updates",
    )
    for prefix in plan.prefixes:
        stream.add_filter("prefix-any", prefix)
    if plan.target_asn and not plan.prefixes:
        stream.add_filter("path", f"_{plan.target_asn}$")
    return stream


def _new_stage_dir(settings: Settings) -> str:
    """Create a fresh staging directory under the configured root (or the system temp)."""
    root = settings.bgp_stage_root or None
    if root:
        Path(root).mkdir(parents=True, exist_ok=True)
    return tempfile.mkdtemp(prefix="bgp-agent-", dir=root)


def _write_dataset(
    stage_dir: str, plan: FetchSpec, records: list[dict[str, Any]], truncated: bool
) -> None:
    """Write the records plus a scope manifest into the staging directory."""
    Path(stage_dir, _UPDATES_FILE).write_text(json.dumps(records, indent=2))
    manifest = {
        "note": "Gathered via pybgpstream and reduced to compact update records.",
        "prefixes": plan.prefixes,
        "target_asn": plan.target_asn,
        "from": plan.from_time,
        "until": plan.until_time,
        "collectors": plan.collectors,
        "record_count": len(records),
        "truncated": truncated,
        "record_fields": _RECORD_FIELDS,
        "files": [_UPDATES_FILE],
    }
    Path(stage_dir, _MANIFEST_FILE).write_text(json.dumps(manifest, indent=2))
