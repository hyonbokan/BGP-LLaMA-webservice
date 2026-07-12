"""Turn a classified intent into a bounded, deterministic gather plan.

The classifier extracts what the user asked for, but its schema is deliberately
tolerant — it will happily return a 30-day window or a dozen collectors. This
module is the guardrail: it requires a real scope (a prefix or an ASN), defaults
and hard-caps the window and the collector set, and returns None when there is
nothing safe to gather. The bounds live here in code, never in the classifier.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.config import Settings
from app.llm.schemas import BgpIntent, TimeWindow

_TIME_FMT = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class FetchSpec:
    """A bounded request to gather updates: the scope, the window, and the collectors.

    ``prefixes`` and ``target_asn`` are the scope (at least one is always set). The
    times are canonical ``YYYY-MM-DD HH:MM:SS`` UTC strings, and ``collectors`` is
    non-empty and capped.
    """

    prefixes: list[str]
    target_asn: str | None
    from_time: str
    until_time: str
    collectors: list[str]


def build_fetch_plan(
    intent: BgpIntent, settings: Settings, now: datetime | None = None
) -> FetchSpec | None:
    """Build a bounded gather plan from a classified intent, or None to skip the gather.

    Returns None when the intent names no scope (neither a prefix nor an ASN), since a
    scope-less gather would scan everything. Otherwise the window is taken from the intent
    when given (else defaulted to the last N minutes) and clamped to the max span, and the
    collectors are taken from the intent (else defaulted) and capped.
    """
    now = now or datetime.now(UTC)
    prefixes = list(intent.prefixes or [])
    target_asn = intent.target_asn or None
    if not prefixes and not target_asn:
        return None

    from_time, until_time = _resolve_window(intent.time_window, settings, now)
    collectors = _resolve_collectors(intent.collectors, settings)
    return FetchSpec(
        prefixes=prefixes,
        target_asn=target_asn,
        from_time=from_time,
        until_time=until_time,
        collectors=collectors,
    )


def _resolve_window(
    window: TimeWindow | None, settings: Settings, now: datetime
) -> tuple[str, str]:
    """Resolve the gather window to a bounded (from, until) pair of canonical UTC strings.

    A valid pair from the intent is used as given; a single bound is extended by the
    default span; anything missing or malformed falls back to the last default-span minutes
    ending now. The final span is clamped to the configured maximum.
    """
    default = timedelta(minutes=settings.bgp_gather_default_window_minutes)
    maximum = timedelta(minutes=settings.bgp_gather_max_window_minutes)
    start = _parse(window.from_time) if window else None
    end = _parse(window.until_time) if window else None

    if start and end and end > start:
        pass
    elif start and not end:
        end = start + default
    elif end and not start:
        start = end - default
    else:
        end = now
        start = now - default

    if end - start > maximum:
        end = start + maximum
    return _format(start), _format(end)


def _resolve_collectors(collectors: list[str] | None, settings: Settings) -> list[str]:
    """The collectors to read: the intent's, else the default, capped to the max count."""
    chosen = [c for c in (collectors or []) if c] or list(settings.bgp_gather_default_collectors)
    return chosen[: settings.bgp_gather_max_collectors]


def _parse(value: str | None) -> datetime | None:
    """Parse a canonical UTC timestamp string to an aware datetime, or None if it can't."""
    if not value:
        return None
    try:
        return datetime.strptime(value, _TIME_FMT).replace(tzinfo=UTC)
    except ValueError:
        return None


def _format(value: datetime) -> str:
    return value.astimezone(UTC).strftime(_TIME_FMT)
