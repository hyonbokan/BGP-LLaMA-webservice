"""Shared Jinja2 configuration for plain-text LLM prompt rendering.

The templates under ``templates/`` render plain-text prompts — Python snippets,
regexes, angle brackets — never browser HTML. This builder centralises the
conventions so they cannot drift: block trimming on, and autoescape OFF (HTML
escaping would corrupt the Python/regex/brace content embedded in prompts).
Callers override only what they need, e.g. ``loader``, ``undefined``, or
``keep_trailing_newline``.
"""

from __future__ import annotations

from typing import Any

from jinja2 import Environment


def build_prompt_environment(**overrides: Any) -> Environment:
    """Build a Jinja2 ``Environment`` configured for plain-text prompt rendering.

    Applies ``trim_blocks`` and ``lstrip_blocks`` (so ``{% %}`` control lines
    leave no stray whitespace) and turns ``autoescape`` off (prompts embed
    Python and regexes, not HTML). Pass ``**overrides`` for anything else, e.g.
    a ``loader`` or ``undefined=StrictUndefined``.
    """
    kwargs: dict[str, Any] = {
        "trim_blocks": True,
        "lstrip_blocks": True,
        "autoescape": False,
    }
    kwargs.update(overrides)
    return Environment(**kwargs)
