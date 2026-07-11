"""The MCP server process: a `fetch_bgp_updates` tool backed by pybgpstream.

Runs as a local stdio MCP server the agent pod launches. pybgpstream is imported lazily
inside the tool so the module loads (for registration/introspection) even where the
native library is only needed at call time.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from bgp_mcp.records import collect_records

mcp = FastMCP("bgp")

_DEFAULT_COLLECTORS = ["rrc00"]
_MAX_RECORDS_CAP = 5000


@mcp.tool()
def fetch_bgp_updates(
    prefix: str,
    from_time: str,
    until_time: str,
    collectors: list[str] | None = None,
    record_type: str = "updates",
    max_records: int = 1000,
) -> dict[str, Any]:
    """Fetch BGP updates for a prefix from public collectors over a time window.

    Returns raw update records for you to analyze — origin changes, MOAS conflicts, AS-path
    shifts, announcement/withdrawal counts — in ordinary Python. You do NOT write pybgpstream.

    Args:
        prefix: target CIDR, e.g. "8.8.8.0/24".
        from_time: window start, UTC "YYYY-MM-DD HH:MM:SS".
        until_time: window end, UTC "YYYY-MM-DD HH:MM:SS".
        collectors: collector names (default ["rrc00"]), e.g. "rrc00", "route-views2".
        record_type: "updates" (default) or "ribs".
        max_records: cap on returned records; the server hard-caps this regardless.

    Returns a dict with `records` (each: time, type A/W, peer_asn, prefix, as_path, origin,
    communities, med), `count`, `truncated` (narrow the window if true), and `window`.
    """
    import pybgpstream

    chosen = collectors or _DEFAULT_COLLECTORS
    limit = min(max_records, _MAX_RECORDS_CAP)
    stream = pybgpstream.BGPStream(
        from_time=from_time, until_time=until_time, collectors=chosen, record_type=record_type
    )
    if prefix:
        stream.add_filter("prefix", prefix)
    records, truncated = collect_records(stream, limit)
    return {
        "records": records,
        "count": len(records),
        "truncated": truncated,
        "window": {
            "prefix": prefix,
            "from_time": from_time,
            "until_time": until_time,
            "collectors": chosen,
            "record_type": record_type,
        },
    }


def main() -> None:
    """Run the server over stdio (the transport the agent pod connects on)."""
    mcp.run()
