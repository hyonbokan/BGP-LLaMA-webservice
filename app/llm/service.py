"""Chat pipeline: classify the query, build a routed prompt, stream the analysis.

`stream_chat` is the single entry point for both providers. It classifies the
natural-language query into a `BgpIntent`, renders the system prompt for that
analysis type (with the extracted parameters filled in), and streams the
generation events. GPT and LLaMA differ only in which template is used and how
generation streams — both handled downstream.
"""

from collections.abc import AsyncIterator

from app.core.config import get_settings
from app.core.logging import get_logger
from app.llm.classifier import classify_intent
from app.llm.generation import Compacted, Event, generate
from app.llm.memory import compact_history
from app.llm.schemas import BgpIntent, Turn
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
        "data_root": get_settings().bgp_data_root,
    }


def build_prompt(provider: str, intent: BgpIntent, summary: str | None = None) -> str:
    """Render the system prompt for a run.

    The fine-tuned LLaMA always gets the shared base setup (the format it was
    trained on); GPT gets the template routed by analysis type. Extracted
    parameters are filled into either. A compaction `summary` of earlier turns,
    when present, is appended so the model retains that context.
    """
    template = "base_setup" if provider == "llama" else intent.analysis_type.value
    prompt = load_prompt(template, **_render_vars(intent))
    if summary:
        prompt = f"{prompt}\n\n## Earlier conversation (summarized)\n{summary}"
    return prompt


async def stream_chat(
    provider: str, query: str, history: list[Turn] | None = None
) -> AsyncIterator[Event]:
    """Stream the analysis for a query, threading prior conversation turns.

    Classifies the query, compacts overflowing history (emitting a `Compacted`
    event when it does), builds the routed system prompt, then yields
    `TextDelta` chunks of the analysis and a terminal `Result` carrying the
    generated pybgpstream script (or None).
    """
    history = history or []
    intent = await classify_intent(query)

    compaction = await compact_history(history, provider)
    if compaction.dropped:
        yield Compacted(dropped=compaction.dropped, summarized=compaction.summary is not None)

    system_prompt = build_prompt(provider, intent, compaction.summary)
    turns = [*compaction.turns, Turn(role="user", content=query)]
    logger.debug("stream provider=%s analysis_type=%s", provider, intent.analysis_type.value)

    async for event in generate(provider, system_prompt, turns):
        yield event
