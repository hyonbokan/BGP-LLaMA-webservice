import asyncio

import app.llm.memory as memory
from app.llm.memory import Compaction, approx_tokens, compact_history, conversation_tokens
from app.llm.providers import ProviderConfig
from app.llm.schemas import Turn


def _turns(n: int) -> list[Turn]:
    return [
        Turn(role="user" if i % 2 == 0 else "assistant", content=f"message number {i} " * 20)
        for i in range(n)
    ]


def test_approx_tokens_is_char_quarter():
    assert approx_tokens("a" * 40) == 10
    assert conversation_tokens([Turn(role="user", content="a" * 40)]) == 10


def test_history_within_budget_is_unchanged(monkeypatch):
    monkeypatch.setattr(
        memory,
        "get_provider",
        lambda _p: ProviderConfig(model="m", api_key="k", history_max_tokens=10_000),
    )
    history = _turns(4)
    result = asyncio.run(compact_history(history, "gpt"))
    assert result == Compaction(turns=history, summary=None, dropped=0)


def test_overflow_summarizes_and_keeps_recent(monkeypatch):
    monkeypatch.setattr(
        memory,
        "get_provider",
        lambda _p: ProviderConfig(model="m", api_key="k", history_max_tokens=1),
    )

    async def fake_summary(turns, cfg):
        return "SUMMARY"

    monkeypatch.setattr(memory, "_summarize", fake_summary)

    # Default keep-recent is 4, so 6 turns → keep the last 4, summarize 2.
    history = _turns(6)
    result = asyncio.run(compact_history(history, "gpt"))
    assert result.dropped == 2
    assert result.summary == "SUMMARY"
    assert result.turns == history[-4:]


def test_overflow_without_key_truncates(monkeypatch):
    monkeypatch.setattr(
        memory,
        "get_provider",
        lambda _p: ProviderConfig(model="m", api_key="k", history_max_tokens=1),
    )

    async def no_summary(turns, cfg):
        return None

    monkeypatch.setattr(memory, "_summarize", no_summary)

    history = _turns(6)
    result = asyncio.run(compact_history(history, "gpt"))
    assert result.dropped > 0
    assert result.summary is None
