"""Pydantic models for the chat pipeline: classification input and generation output.

`BgpIntent` is what the classifier extracts from a natural-language query (the
analysis type plus any concrete parameters). `BgpScript` is what the generation
step returns — the streamed natural-language `explanation` the user sees, plus
the pybgpstream `script` as a dedicated field (no fenced-block parsing). Both are
used as OpenAI structured-output schemas, so every field is present and the
shapes stay flat.

Validators are deliberately tolerant: a malformed parameter is repaired to
`None`/dropped rather than raising, because classification is a best-effort,
non-critical step — a bad param must never fail the whole request.
"""

import ipaddress
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator

_TIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
)
_CANONICAL_TIME = "%Y-%m-%d %H:%M:%S"


class AnalysisType(StrEnum):
    """The kind of BGP analysis a query asks for. The value is the template stem."""

    prefix = "prefix"
    as_path = "as_path"
    moas = "moas"
    med_community = "med_community"
    hijacking = "hijacking"
    outage = "outage"
    realtime = "realtime"
    knowledge = "knowledge"
    default = "default"


def _normalize_time(value: object) -> str | None:
    """Parse a timestamp in any accepted format to the canonical one, else None."""
    if not isinstance(value, str) or not value.strip():
        return None
    for fmt in _TIME_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).strftime(_CANONICAL_TIME)
        except ValueError:
            continue
    return None


class TimeWindow(BaseModel):
    """A historical analysis window; each bound is a canonical timestamp or None."""

    from_time: str | None = None
    until_time: str | None = None

    @field_validator("from_time", "until_time", mode="before")
    @classmethod
    def _repair_time(cls, value: object) -> str | None:
        return _normalize_time(value)


class BgpIntent(BaseModel):
    """The classified analysis type plus any parameters extracted from the query."""

    model_config = ConfigDict(extra="ignore")

    analysis_type: AnalysisType = AnalysisType.default
    target_asn: str | None = None
    prefixes: list[str] = []
    time_window: TimeWindow | None = None
    collectors: list[str] = []

    @field_validator("analysis_type", mode="before")
    @classmethod
    def _coerce_type(cls, value: object) -> object:
        """Fall back to `default` for a missing or unrecognized analysis type."""
        if value is None:
            return AnalysisType.default
        if isinstance(value, AnalysisType):
            return value
        try:
            return AnalysisType(str(value).strip().lower())
        except ValueError:
            return AnalysisType.default

    @field_validator("target_asn", mode="before")
    @classmethod
    def _clean_asn(cls, value: object) -> str | None:
        """Keep a bare AS number (digits only), stripping a leading 'AS'."""
        if value is None:
            return None
        text = str(value).strip().upper()
        if text.startswith("AS"):
            text = text[2:]
        return text if text.isdigit() else None

    @field_validator("prefixes", mode="before")
    @classmethod
    def _clean_prefixes(cls, value: object) -> list[str]:
        """Keep only valid IP prefixes, deduped in first-seen order."""
        if not value:
            return []
        items = value if isinstance(value, (list, tuple)) else [value]
        seen: dict[str, None] = {}
        for item in items:
            text = str(item).strip()
            try:
                ipaddress.ip_network(text, strict=False)
            except ValueError:
                continue
            seen.setdefault(text, None)
        return list(seen)

    @field_validator("collectors", mode="before")
    @classmethod
    def _clean_collectors(cls, value: object) -> list[str]:
        """Strip, drop blanks, and dedupe collector names in first-seen order."""
        if not value:
            return []
        items = value if isinstance(value, (list, tuple)) else [value]
        seen: dict[str, None] = {}
        for item in items:
            text = str(item).strip()
            if text:
                seen.setdefault(text, None)
        return list(seen)


class BgpScript(BaseModel):
    """The generation result: the NL analysis and the pybgpstream script (if any).

    `explanation` is listed first so it streams before `script`. `script` is None
    for knowledge answers that need no code.
    """

    analysis_type: AnalysisType = AnalysisType.default
    explanation: str = ""
    script: str | None = None
