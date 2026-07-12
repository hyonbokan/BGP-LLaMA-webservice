"""Gather-and-stage: staging output, collector merge, and the unavailable/timeout failure modes.

The pybgpstream stream is faked at the _open_stream seam, so these run without the native library.
Async entry points are driven with asyncio.run (this suite doesn't use pytest-asyncio).
"""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import app.bgp.gather as gather_mod
from app.bgp.fetch_plan import FetchSpec
from app.bgp.gather import GatherError, GatherUnavailable, gather_and_stage, reap_stage


class _Elem:
    """Duck-typed stand-in for a pybgpstream BGPElem."""

    def __init__(self, time, type_, peer_asn, fields):
        self.time = time
        self.type = type_
        self.peer_asn = peer_asn
        self.fields = fields


def _plan(collectors=("rrc00",)) -> FetchSpec:
    return FetchSpec(
        prefixes=["1.1.1.0/24"],
        target_asn=None,
        from_time="2026-07-12 03:30:00",
        until_time="2026-07-12 04:00:00",
        collectors=list(collectors),
    )


def _settings(tmp_path, **overrides):
    base = {
        "bgp_gather_max_records": 1000,
        "bgp_gather_timeout_seconds": 30,
        "bgp_stage_root": str(tmp_path),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_gather_and_stage_writes_records_and_manifest(monkeypatch, tmp_path):
    elems = [
        _Elem(1000, "A", 3333, {"prefix": "1.1.1.0/24", "as-path": "3356 13335"}),
        _Elem(1001, "A", 12654, {"prefix": "1.1.1.0/24", "as-path": "174 64500"}),
    ]
    monkeypatch.setattr(gather_mod, "_open_stream", lambda plan, collector: elems)

    stage = asyncio.run(gather_and_stage(_plan(), _settings(tmp_path)))

    updates = json.loads(Path(stage, "updates.json").read_text())
    manifest = json.loads(Path(stage, "manifest.json").read_text())
    assert [r["origin"] for r in updates] == ["13335", "64500"]
    assert manifest["record_count"] == 2
    assert manifest["prefixes"] == ["1.1.1.0/24"]
    assert manifest["collectors"] == ["rrc00"]
    assert manifest["files"] == ["updates.json"]
    assert manifest["truncated"] is False

    reap_stage(stage)
    assert not Path(stage).exists()


def test_gather_merges_collectors_time_ordered(monkeypatch, tmp_path):
    by_collector = {
        "rrc00": [_Elem(2000, "A", 1, {"prefix": "1.1.1.0/24", "as-path": "13335"})],
        "rrc01": [_Elem(1000, "A", 2, {"prefix": "1.1.1.0/24", "as-path": "13335"})],
    }
    monkeypatch.setattr(gather_mod, "_open_stream", lambda plan, collector: by_collector[collector])

    stage = asyncio.run(gather_and_stage(_plan(collectors=("rrc00", "rrc01")), _settings(tmp_path)))

    updates = json.loads(Path(stage, "updates.json").read_text())
    assert [r["time"] for r in updates] == [1000, 2000]  # both collectors, merged and time-sorted


def test_truncation_is_flagged(monkeypatch, tmp_path):
    elems = [_Elem(i, "A", 1, {"prefix": "1.1.1.0/24", "as-path": "13335"}) for i in range(5)]
    monkeypatch.setattr(gather_mod, "_open_stream", lambda plan, collector: elems)

    stage = asyncio.run(gather_and_stage(_plan(), _settings(tmp_path, bgp_gather_max_records=2)))

    manifest = json.loads(Path(stage, "manifest.json").read_text())
    assert manifest["record_count"] == 2
    assert manifest["truncated"] is True


def test_gather_unavailable_propagates(monkeypatch, tmp_path):
    def boom(plan, collector):
        raise GatherUnavailable("no pybgpstream")

    monkeypatch.setattr(gather_mod, "_open_stream", boom)
    with pytest.raises(GatherUnavailable):
        asyncio.run(gather_and_stage(_plan(), _settings(tmp_path)))


def test_gather_timeout_becomes_error(monkeypatch, tmp_path):
    async def slow(plan, settings):
        await asyncio.sleep(1)
        return [], False

    monkeypatch.setattr(gather_mod, "_gather_records", slow)
    with pytest.raises(GatherError, match="timed out"):
        asyncio.run(gather_and_stage(_plan(), _settings(tmp_path, bgp_gather_timeout_seconds=0.01)))
