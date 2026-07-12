"""Backend BGP data layer: gather-and-reduce plus record shaping.

The backend gathers BGP updates with pybgpstream, reduces them to an
analysis-ready dataset, and stages that as a read-only workspace for the
autonomous agent to analyze — the agent never fetches. `fetch_plan` turns a
classified intent into a bounded gather request, `gather` runs it and stages the
dataset, and `records` holds the pure element→dict shaping, kept import-light so
it unit-tests without the native BGPStream library.
"""

from app.bgp.fetch_plan import FetchSpec, build_fetch_plan
from app.bgp.gather import GatherError, GatherUnavailable, gather_and_stage, reap_stage
from app.bgp.records import collect_records, element_to_record

__all__ = [
    "FetchSpec",
    "GatherError",
    "GatherUnavailable",
    "build_fetch_plan",
    "collect_records",
    "element_to_record",
    "gather_and_stage",
    "reap_stage",
]
