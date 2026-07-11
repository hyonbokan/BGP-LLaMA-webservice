from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, env-driven configuration (replaces the Django settings split).

    Field names map to upper-case env vars case-insensitively, e.g.
    ``openai_api_key`` <- ``OPENAI_API_KEY``. Unknown env keys are ignored so a
    shared .env carrying leftover vars doesn't break startup.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # Logging
    log_level: str = "INFO"

    # HTTP / CORS. Kept as a raw comma-separated string (django-environ style)
    # and split via the `cors_origins` property — a plain str avoids
    # pydantic-settings' JSON-decoding of List fields from env.
    cors_allowed_origins: str = "http://localhost:3000"

    # Shared LLM client
    llm_request_timeout: int = 120

    # Conversation memory. History is threaded into each request; when it grows
    # past a provider's window the oldest turns are summarized (Claude-Code
    # style) into a running summary, keeping the most recent turns verbatim.
    # Thresholds are provider-aware: GPT has a large context, the local LLaMA a
    # much smaller one. Token counts are estimated (~4 chars/token), so no
    # tokenizer dependency is pulled into the slim API image.
    gpt_history_max_tokens: int = 100_000
    llama_history_max_tokens: int = 6_000
    history_keep_recent_turns: int = 4

    # Hosted GPT (OpenAI, or any OpenAI-compatible gateway via OPENAI_BASE_URL)
    openai_api_key: str = ""
    openai_model: str = "gpt-5.4-mini-2026-03-17"
    openai_base_url: str | None = None
    gpt_temperature: float = 0.7
    gpt_max_tokens: int = 2000

    # Query classification (structured LLM call, always GPT-backed). When
    # disabled or when no OpenAI key is set, chat falls back to a substring
    # heuristic — same routing as before, so nothing regresses.
    classifier_enabled: bool = True
    classifier_model: str | None = None  # None => use openai_model

    # Local fine-tuned BGP-LLaMA served by vLLM
    llama_base_url: str = "http://host.docker.internal:8000/v1"
    llama_api_key: str = "EMPTY"
    llama_model: str = "hyonbokan/bgp-llama-3.1-instruct-10kSteps-2kDataset"
    llama_temperature: float = 0.1
    llama_max_tokens: int = 912
    llama_repetition_penalty: float = 1.1
    llama_api_mode: str = "completion"  # "completion" (raw prompt) or "chat"

    # Agentic BGP analysis (opencode-agent-pod). The pod runs an autonomous agent
    # that writes a BGP script, runs it against staged data, and streams a result;
    # provider keys live in the pod, so this backend sends a rendered task and a
    # bearer token, never a key. agent_model is any id the pod resolves (a bare
    # catalog id like the GPT default, or a qualified "provider/model"). The
    # timeout is generous: an autonomous run can take minutes.
    agent_pod_url: str = "http://localhost:8080"
    agent_pod_token: str = ""
    agent_model: str = "gpt-5.4-mini-2026-03-17"
    # bgp_fetch_bgp_updates is the pod's MCP data tool (declared in the pod's
    # AGENT_MCP_SERVERS); Bash/Read/Write let the agent analyze the records.
    agent_tools: str = "bgp_fetch_bgp_updates,Bash,Read,Write"
    agent_max_budget_usd: float | None = None
    agent_request_timeout: int = 600

    # File download root (served by /api/download) — the fine-tuning corpus
    dataset_root: str = "finetuning-dataset"

    # Root directory generated pybgpstream scripts read BGP update files from.
    # Filled into the prompt templates and used to rewrite any personal data
    # path the fine-tuned model reproduces from its training data, so no such
    # path leaks into returned code.
    bgp_data_root: str = "/data/bgp"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def agent_tool_list(self) -> list[str]:
        """The tools the agent may use, parsed from the comma-separated env value."""
        return [t.strip() for t in self.agent_tools.split(",") if t.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
