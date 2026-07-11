"""Shape BGPStream elements into compact, JSON-serializable update records.

Kept free of the pybgpstream and MCP imports so the record logic can be unit-tested
without the native BGPStream library installed.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def element_to_record(elem: Any) -> dict[str, Any]:
    """Flatten one BGPStream element (announcement or withdrawal) into a plain dict.

    Announcements carry an AS path and thus an origin; withdrawals do not, so those
    fields come back empty. Communities are stringified so the result stays JSON-safe.
    """
    fields = getattr(elem, "fields", None) or {}
    as_path = str(fields.get("as-path", "")).split()
    return {
        "time": getattr(elem, "time", None),
        "type": getattr(elem, "type", None),  # "A" announcement, "W" withdrawal
        "peer_asn": str(getattr(elem, "peer_asn", "")) or None,
        "prefix": fields.get("prefix"),
        "as_path": as_path,
        "origin": as_path[-1] if as_path else None,
        "communities": [str(c) for c in (fields.get("communities") or [])],
        "med": fields.get("med"),
    }


def collect_records(elements: Iterable[Any], max_records: int) -> tuple[list[dict[str, Any]], bool]:
    """Shape up to ``max_records`` elements into records, flagging truncation.

    Returns the records and whether the stream was cut short, so the caller can tell the
    agent to narrow its window rather than trust a partial result as complete.
    """
    records: list[dict[str, Any]] = []
    truncated = False
    for elem in elements:
        if len(records) >= max_records:
            truncated = True
            break
        records.append(element_to_record(elem))
    return records, truncated
