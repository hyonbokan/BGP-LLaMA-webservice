"""Classify a natural-language BGP query into a validated `BgpIntent`.

A single structured LLM call (always GPT — reliable structured output) turns the
query into an analysis type plus any extracted parameters. It is best-effort: if
classification is disabled, no OpenAI key is configured, or the call fails, it
falls back to a substring heuristic so the request never breaks.
"""

from app.core.config import get_settings
from app.core.logging import get_logger
from app.llm.clients import get_client
from app.llm.providers import get_provider
from app.llm.schemas import AnalysisType, BgpIntent
from prompts.loader import PromptTemplate, load_prompt

logger = get_logger(__name__)

# The classifier system prompt is static (no per-request variables) → load once.
_CLASSIFY_SYSTEM = load_prompt(PromptTemplate.CLASSIFY_SYSTEM)

# Classification always runs on the hosted GPT provider; the fine-tuned LLaMA is
# not relied on for structured output.
_CLASSIFIER_PROVIDER = "gpt"


def _heuristic_intent(query: str) -> BgpIntent:
    """Route by substring — the preserved fallback when the LLM step is skipped."""
    q = query.lower()
    if "real-time" in q or "realtime" in q:
        analysis_type = AnalysisType.realtime
    elif "hijack" in q:
        analysis_type = AnalysisType.hijacking
    elif "outage" in q:
        analysis_type = AnalysisType.outage
    elif "as path" in q or "as-path" in q:
        analysis_type = AnalysisType.as_path
    else:
        analysis_type = AnalysisType.default
    return BgpIntent(analysis_type=analysis_type)


async def classify_intent(query: str) -> BgpIntent:
    """Return the `BgpIntent` for a query, falling back to the heuristic on any failure."""
    settings = get_settings()
    if not settings.classifier_enabled or not settings.openai_api_key:
        return _heuristic_intent(query)

    try:
        cfg = get_provider(_CLASSIFIER_PROVIDER)
        client = get_client(cfg.base_url, cfg.api_key)
        completion = await client.beta.chat.completions.parse(
            model=settings.classifier_model or settings.openai_model,
            messages=[
                {"role": "system", "content": _CLASSIFY_SYSTEM},
                {"role": "user", "content": query},
            ],
            response_format=BgpIntent,
            temperature=0,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            logger.warning("Classifier returned no parsed intent; using heuristic")
            return _heuristic_intent(query)
        logger.debug("Classified query as %s", parsed.analysis_type.value)
        return parsed
    except Exception:
        logger.warning("Classification failed; falling back to heuristic", exc_info=True)
        return _heuristic_intent(query)
