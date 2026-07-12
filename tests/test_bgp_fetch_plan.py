"""The gather guardrail: scope required, window defaulted + clamped, collectors capped."""

from datetime import UTC, datetime

from app.bgp.fetch_plan import build_fetch_plan
from app.core.config import Settings
from app.llm.schemas import BgpIntent, TimeWindow

NOW = datetime(2026, 7, 12, 4, 0, 0, tzinfo=UTC)


def _settings(**overrides) -> Settings:
    """Real Settings with code defaults (no .env), optionally overridden."""
    return Settings(_env_file=None, **overrides)


def test_no_scope_returns_none():
    # Neither a prefix nor an ASN → nothing safe to gather, so skip.
    assert build_fetch_plan(BgpIntent(), _settings(), now=NOW) is None


def test_prefix_scope_defaults_window_and_collectors():
    plan = build_fetch_plan(BgpIntent(prefixes=["1.1.1.0/24"]), _settings(), now=NOW)
    assert plan is not None
    assert plan.prefixes == ["1.1.1.0/24"]
    assert plan.target_asn is None
    assert plan.collectors == ["rrc00"]  # default
    assert plan.from_time == "2026-07-12 03:30:00"  # last 30 min ending now
    assert plan.until_time == "2026-07-12 04:00:00"


def test_asn_only_scope_is_valid():
    plan = build_fetch_plan(BgpIntent(target_asn="15169"), _settings(), now=NOW)
    assert plan is not None
    assert plan.target_asn == "15169"
    assert plan.prefixes == []


def test_explicit_window_used_as_given():
    tw = TimeWindow(from_time="2026-07-12 03:00:00", until_time="2026-07-12 03:20:00")
    plan = build_fetch_plan(
        BgpIntent(prefixes=["1.1.1.0/24"], time_window=tw), _settings(), now=NOW
    )
    assert plan is not None
    assert plan.from_time == "2026-07-12 03:00:00"
    assert plan.until_time == "2026-07-12 03:20:00"


def test_over_max_window_is_clamped():
    # A 6-hour window is clamped to the max span (default 120 min) from the start.
    tw = TimeWindow(from_time="2026-07-12 00:00:00", until_time="2026-07-12 06:00:00")
    plan = build_fetch_plan(
        BgpIntent(prefixes=["1.1.1.0/24"], time_window=tw), _settings(), now=NOW
    )
    assert plan is not None
    assert plan.from_time == "2026-07-12 00:00:00"
    assert plan.until_time == "2026-07-12 02:00:00"


def test_open_ended_window_extended_by_default_span():
    tw = TimeWindow(from_time="2026-07-12 03:00:00")  # no until
    plan = build_fetch_plan(
        BgpIntent(prefixes=["1.1.1.0/24"], time_window=tw), _settings(), now=NOW
    )
    assert plan is not None
    assert plan.from_time == "2026-07-12 03:00:00"
    assert plan.until_time == "2026-07-12 03:30:00"


def test_collectors_are_capped():
    intent = BgpIntent(prefixes=["1.1.1.0/24"], collectors=["rrc00", "rrc01", "rrc02", "rrc03"])
    plan = build_fetch_plan(intent, _settings(bgp_gather_max_collectors=3), now=NOW)
    assert plan is not None
    assert plan.collectors == ["rrc00", "rrc01", "rrc02"]
