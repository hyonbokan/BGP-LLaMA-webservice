from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root (app/core/config.py → repo root), used to locate the bundled sample dataset.
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Typed, env-driven configuration — the app's single settings source.

    Field names map to upper-case env vars case-insensitively, e.g.
    ``openai_api_key`` <- ``OPENAI_API_KEY``. Unknown env keys are ignored so a
    shared .env carrying leftover vars doesn't break startup.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # Logging
    log_level: str = "INFO"

    # HTTP / CORS. A list[str] read from env as a JSON array, e.g.
    # CORS_ALLOWED_ORIGINS=["http://localhost:3000","https://app.example.com"].
    cors_allowed_origins: list[str] = ["http://localhost:3000"]

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

    # Hosted GPT (OpenAI, or any OpenAI-compatible gateway via OPENAI_BASE_URL).
    # No temperature / max-tokens knobs: reasoning models ignore them, so the GPT
    # path sends neither (see app/llm/providers.py + generation.py).
    openai_api_key: str = ""
    openai_model: str = "gpt-5.4-mini-2026-03-17"
    openai_base_url: str | None = None

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
    # that analyzes the backend-staged BGP data and streams a result; provider keys
    # live in the pod, so this backend sends a rendered task and a bearer token,
    # never a key. agent_model is any id the pod resolves (a bare catalog id like
    # the GPT default, or a qualified "provider/model"). The timeout is generous:
    # an autonomous run can take minutes.
    agent_pod_url: str = "http://localhost:8080"
    agent_pod_token: str = ""
    agent_model: str = "gpt-5.4-mini-2026-03-17"
    # The agent analyzes BGP data the backend has already gathered and staged as a
    # read-only workspace; Bash/Read/Write are all it needs. It does not fetch (no
    # data tool) — see AGENTS.md, BGP agent. A list[str] read from env as a JSON
    # array, e.g. AGENT_TOOLS=["Bash","Read","Write"].
    agent_tools: list[str] = ["Bash", "Read", "Write"]
    agent_max_budget_usd: float | None = None
    agent_request_timeout: int = 600

    # How the gathered workspace reaches the pod. "file" passes a file:// path, which assumes the
    # pod shares this host's filesystem (single-host dev). "minio" uploads the workspace as an
    # archive to an S3-compatible store and passes a pre-signed https URL the pod pulls over the
    # network, so the pod shares no disk with this backend — the mode for a decoupled deployment.
    workspace_transport: str = "file"  # "file" | "minio"
    minio_endpoint: str = ""  # host:port of the S3-compatible store, e.g. "minio:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "bgp-workspaces"
    minio_secure: bool = True  # https to the store (a self-signed dev cert still works)
    minio_cert_check: bool = True  # verify the store's TLS cert; off accepts a self-signed dev cert
    minio_url_expiry_seconds: int = 3600

    # File download root (served by /api/download) — the fine-tuning corpus
    dataset_root: str = "finetuning-dataset"

    # Root directory generated pybgpstream scripts read BGP update files from.
    # Filled into the prompt templates and used to rewrite any personal data
    # path the fine-tuned model reproduces from its training data, so no such
    # path leaks into returned code. On the agent path it is also the fallback
    # workspace when a live gather is skipped or unavailable (see below).
    bgp_data_root: str = "/data/bgp"

    # BGP gather (agent path). Before an agent run, the backend fetches the
    # scoped updates with pybgpstream, reduces them to records, and stages them
    # as the agent's read-only workspace. These are the hard bounds on that
    # gather — enforced in code, never by the classifier, since an LLM will fill
    # a "required" window with a 30-day span. The window is defaulted to the last
    # N minutes when the query names none and clamped to the max; collectors are
    # defaulted and capped likewise. Staged runs land under bgp_stage_root (empty
    # => the system temp dir), each in its own directory, reaped after the run.
    bgp_gather_default_window_minutes: int = 30
    bgp_gather_max_window_minutes: int = 120
    bgp_gather_default_collectors: list[str] = ["rrc00"]
    bgp_gather_max_collectors: int = 3
    bgp_gather_max_records: int = 50_000
    bgp_gather_timeout_seconds: int = 180
    bgp_stage_root: str = ""

    # Last-resort workspace when a live gather can't run (no pybgpstream) and no real
    # BGP_DATA_ROOT is present: a bundled SYNTHETIC sample so the agent demo works out of the
    # box on a dev host. Defaults to the repo's sample_bgp_data/; set empty to disable (e.g. in
    # production, where an empty workspace is preferable to fake data).
    bgp_sample_data_root: str = str(_REPO_ROOT / "sample_bgp_data")


@lru_cache
def get_settings() -> Settings:
    return Settings()
