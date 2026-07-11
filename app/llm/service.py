"""Chat pipeline: classify the query, build a routed prompt, stream the analysis.

`stream_chat` is the single entry point for both providers. It classifies the
natural-language query into a `BgpIntent`, renders the system prompt for that
analysis type (with the extracted parameters filled in), and streams the
generation events. GPT and LLaMA differ only in which template is used and how
generation streams — both handled downstream.
"""

from collections.abc import AsyncIterator

from app.core.logging import get_logger
from app.llm.classifier import classify_intent
from app.llm.generation import Event, generate
from app.llm.schemas import BgpIntent
from prompts.loader import load_prompt

logger = get_logger(__name__)


def _render_vars(intent: BgpIntent) -> dict:
    """The variable set every template is rendered with (missing values as None)."""
    window = intent.time_window
    return {
        "target_asn": intent.target_asn,
        "prefixes": intent.prefixes,
        "from_time": window.from_time if window else None,
        "until_time": window.until_time if window else None,
        "collectors": intent.collectors,
        "collection_duration": None,
    }


def build_prompt(provider: str, intent: BgpIntent) -> str:
    """Render the system prompt for a run.

    The fine-tuned LLaMA always gets the shared base setup (the format it was
    trained on); GPT gets the template routed by analysis type. Extracted
    parameters are filled into either.
    """
    template = "base_setup" if provider == "llama" else intent.analysis_type.value
    return load_prompt(template, **_render_vars(intent))


async def stream_chat(provider: str, query: str, context: str = "") -> AsyncIterator[Event]:
    """Stream the analysis for a query.

    Yields `TextDelta` chunks of the natural-language analysis as it is written,
    then a terminal `Result` carrying the generated pybgpstream script (or None).
    """
    intent = await classify_intent(query)
    system_prompt = build_prompt(provider, intent)
    user_content = f"{context}\n\n{query}" if context else query
    logger.debug("stream provider=%s analysis_type=%s", provider, intent.analysis_type.value)

    async for event in generate(provider, system_prompt, user_content):
        yield event
