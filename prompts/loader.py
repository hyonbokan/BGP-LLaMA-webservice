"""Load and render the ``.j2`` prompt templates under ``templates/``.

``load_prompt(name, **vars)`` renders ``templates/<name>.j2`` with the given
variables. ``StrictUndefined`` is on, so a template that references a variable
the caller did not pass raises ``jinja2.UndefinedError`` at render time instead
of silently leaking a placeholder — callers must pass the full variable set
(missing values as ``None``) and guard optional sections with ``{% if %}``.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from prompts.jinja_env import build_prompt_environment

_TEMPLATES_DIR = Path(__file__).parent / "templates"


class PromptTemplate(StrEnum):
    """Fixed template stems that aren't analysis types (those live in ``AnalysisType``).

    The value is the file stem under ``templates/`` (without ``.j2``). Referencing a
    prompt through this enum keeps the name in one place instead of scattered string
    literals, so a rename or typo is caught rather than failing at render time.
    """

    AGENT_SYSTEM = "agent_system"
    BASE_SETUP = "base_setup"
    CLASSIFY_SYSTEM = "classify_system"
    COMPACT_SYSTEM = "compact_system"


@lru_cache(maxsize=1)
def _env() -> Environment:
    """The template environment, rooted at ``templates/`` (built once)."""
    return build_prompt_environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


def load_prompt(name: str, **variables: object) -> str:
    """Render ``templates/<name>.j2`` with ``variables`` and return the text.

    ``name`` is the template stem without the ``.j2`` suffix (e.g. ``"hijacking"``).
    An unknown name raises ``jinja2.TemplateNotFound``.
    """
    return _env().get_template(f"{name}.j2").render(**variables)
