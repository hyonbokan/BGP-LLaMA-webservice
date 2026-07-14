## Project Overview

BGP-LLaMA Webservice is an AI-powered platform for **BGP routing analysis and anomaly detection**.
It combines an instruction fine-tuned **LLaMA** model with **GPT (gpt-5.4-mini)** and streams model
output to the browser over SSE. Both models are reached through one OpenAI-compatible client — the
local LLaMA is served by **vLLM**, GPT by OpenAI — so they differ only by base URL / key / model.
Two components:

- **FastAPI backend** — the single Python service (`app/`). Streams LLaMA/GPT over SSE and serves
  file downloads. CPU-only: it proxies to vLLM (local model) and OpenAI (GPT) over HTTP — **no
  in-process inference**. Runs under gunicorn + uvicorn workers.
- **React frontend** — Vite + React 18 + **TypeScript** SPA in `react_frontend/`, styled with
  Tailwind CSS + shadcn/ui. (Migrated off Create React App; MUI and Redux were removed.)

Backend Python lives at the repository root under `app/` — there is **no** `backend/` directory.

### Backend layout (`app/`)

```
app/
  main.py                 # app factory: CORS, router mounts (everything under /api)
  core/config.py          # pydantic-settings Settings (single env-driven config source)
  llm/providers.py        # ProviderConfig + get_provider("gpt"|"llama")
  llm/service.py          # stream_chat() — the unified OpenAI-compatible streaming client
  llm/agent.py            # pod client: classify -> render task -> POST /agent/run, relay SSE
  utils/code_extract.py   # pull the ```python block out of a reply
  api/routes/
    health.py             # GET /api/health
    chat.py               # POST /api/chat/bgp_gpt, /api/chat/bgp_llama (SSE; body = query + history)
    agent.py              # POST /api/agent/run (SSE; proxies one autonomous run to opencode-agent-pod)
    files.py              # GET /api/download                          (traversal-guarded)
prompts/                  # prompt strings (pure data, no heavy imports)
```

## Agentic BGP analysis via opencode-agent-pod (built + e2e-verified)

**Status.** Built and verified end to end (2026-07-12). The `POST /api/agent/run` endpoint
(`app/api/routes/agent.py`), the pod client (`app/llm/agent.py`), and the run-and-observe console
(`react_frontend/src/pages/bgp-agent-page.tsx` + `hooks/use-bgp-agent.ts` +
`components/agent/agent-run-card.tsx`) are all in place. A live smoke drove a real question through
this backend to a locally-running pod and back: a natural-language query returned an answer, and a
`Bash`-tool run analyzed a hand-staged workspace over 3 turns (the pod staged the `file://` pointer,
ran, and reaped it). **The live per-step trace is now built and verified end to end (2026-07-12):**
the pod streams `token`/`tool` events, this backend's `_relay` turns them into typed
`Token`/`ToolCall` events, the route re-emits them as `token`/`tool` SSE frames, and the console
renders a live tool-call trace (pending→running→completed with input/output) plus the streaming
answer — verified by driving `run_agent` against a live pod (two tool calls traced, answer streamed,
terminal result). **Real BGP-data gather-and-stage is now built too (2026-07-12):** `app/bgp/` turns a
classified intent into a bounded plan (`build_fetch_plan`), gathers the scoped updates with pybgpstream,
reduces them, and stages `updates.json` + a manifest as the agent's workspace, reaped after the run —
with a lazy pybgpstream import so a dev host without it falls back to a static `BGP_DATA_ROOT`. This
section documents the shape; see "How the agent run is wired" below.

Today the backend streams model **text** (`llm/service.py` → `stream_chat()`): the chat feature
*generates* a pybgpstream script but never runs it. The planned next step adds a **code-executing**
path backed by a sibling service, **opencode-agent-pod** (`../opencode-agent-pod`) — a standalone,
deployable container running an autonomous agent that writes a BGP analysis script, runs it (`Bash`)
against staged RIB/pybgpstream data, observes, self-corrects, and streams the reason-execute-observe
trace.

- **Separate feature, not folded into chat.** This ships as its own thing: a new nav entry (**"BGP
  Agent"**), its own route (`/bgp_agent`), and its own backend endpoint (**`POST /api/agent/run`**,
  distinct from `/api/chat/*`). The existing generate-only BGP Chat (`bgp_llama`/`bgp_gpt`) stays
  exactly as is — the agent is an addition, not a replacement.
- **Feature-page shape — a run-and-observe console, not a two-bubble chat.** A user poses a question;
  the assistant "turn" expands into the agent's **step / tool-call (`Bash`,`Read`,`Write`) / output
  trace**, ending in a result card (the answer plus run metadata: cost, turns, duration, subtype).
  Follow-ups are new single-shot runs. The pod now ships live `token`/`tool` SSE events (pod DESIGN
  §9), so the console renders the live step trace — each tool call as it transitions
  pending→running→completed (with its input/output) and the answer text as it streams — ahead of the
  result card. Built and verified end to end 2026-07-12.
- **Reuse the existing pipeline for the prompt.** The classify → jinja-template machinery
  (`classify_intent` + `prompts/templates/*`) renders the pod's `system_prompt`/`prompt`; the agent
  receives a *rendered task*, not the raw query. `BgpScript` (or a purpose-built schema) can be passed
  as the pod's `response_schema` for structured output.
- **Contract:** `POST /api/agent/run` on this backend proxies to the pod's `POST /agent/run` (bearer
  token), body `{model, system_prompt?, prompt, tools:["Bash","Read","Write"], response_schema?,
  max_budget_usd?, workspace:{source,mode}}` → `text/event-stream`; the terminal `done` event carries
  the `OpencodeResult` (free text or structured output, plus cost/turns/subtype). Re-stream it over
  this backend's SSE (same frame format as `/api/chat/*`).
- **Workspace by reference — an unbuilt prerequisite.** The pod holds no state: this backend must
  stage BGP data (RIB/pybgpstream) to storage and pass a *pointer* (not bytes). **No staging layer
  exists yet** (data provisioning was explicitly deferred). `BGP_DATA_ROOT` is the seam — it is both
  what generated scripts read and where staged data would land, i.e. it maps onto the pod's ephemeral
  workspace cwd. Note the pod's **v1 stages only local `file://`/bare paths (not `s3://`)** — so a
  single-host deploy shares a local directory; object storage is a later extension.
- **Multi-turn memory:** thread the pod's structured output / a distilled summary forward as *prior
  findings*, **not** the raw agent transcript (pod DESIGN §5). This lines up with the chat's
  compaction-summary unit — the summary *is* the memory unit.
- **Keys & security:** provider keys live inside the pod (a key-injecting proxy keeps them out of the
  agent's shell); this backend never sends or receives a provider key to/from the pod. The pod's
  egress lockdown is a deploy-time network policy.
- **Model path:** use the **GPT/Anthropic** path first. The pod can address a local vLLM model, but
  that is deferred (no GPU) — the same constraint as this repo's LLaMA-via-vLLM story.
- **Authoritative design** lives in the pod's own `DESIGN.md` / `PLAN.md` (kept local in that repo):
  DESIGN §4 (workspace by reference), §5 (multi-turn), §8 (response), §9 (API surface), §12 (this
  consumer), and the PLAN "Phase consumer" section.

### Frontend shell (built)

The app uses a **left icon rail** (global feature nav) + each feature's own contextual sidebar — the
VS Code / Linear pattern, so the chat/agent workspaces don't stack two unrelated sidebars. Pieces:

- `components/layout/nav-links.ts` — `NAV_GROUPS`, the single source for both rail and mobile drawer:
  **Analyze** (BGP Chat · BGP Agent) and **Explore** (Dataset · Fine-tuning · Download model).
- `components/layout/side-rail.tsx` — desktop rail (icon + short label, grouped, tooltips). Active
  state is set via `aria-current` variants (a *function* `className` on `NavLink` breaks inside the
  tooltip's `asChild` slot — don't reintroduce it).
- `components/layout/mobile-bar.tsx` — the `md:hidden` top bar + grouped drawer.
- `components/layout/layouts.tsx` — `ContentLayout` (rail + scrolling content + footer) and
  `WorkspaceLayout` (rail + full-height, no footer, used by `/bgp_chat` and `/bgp_agent`).
- `components/logo.tsx` — the AS-path mark as one theme-aware inline SVG (edges/relay nodes on
  `currentColor`, destination node on `--primary`); `public/favicon.svg` is the matching favicon.

The chat and agent pages keep their per-feature sidebars (chat tabs / agent runs) to the right of the
rail.

### How the agent run is wired (built)

> **Current status (2026-07-12): caller-side gather-and-stage is BUILT.** `app/bgp/` now gathers the
> scoped updates with pybgpstream, reduces them via `records.py`, and stages `updates.json` + a
> manifest as the agent's read-only workspace; `build_fetch_plan` is the deterministic guardrail and
> `run_agent` wires gather → stage → workspace → reap. pybgpstream is imported lazily, so a dev host
> without the native library (or a failed gather) **falls back to a statically staged `BGP_DATA_ROOT`**
> — verified end to end 2026-07-12 (a scoped MOAS query gathered-or-fell-back, then the agent analyzed
> the staged records and reported the conflict). The real network gather runs where BGPStream is
> installed (the `docker/Dockerfile.bgpstream` image); the slim `api` image and macOS dev hosts use the
> fallback. **Config env format:** `AGENT_TOOLS` and `CORS_ALLOWED_ORIGINS` are `list[str]` read as
> **JSON arrays** (pydantic-settings' native format), e.g. `AGENT_TOOLS=["Bash","Read","Write"]`. A
> stale comma-separated value fails at boot — migrate any live `.env` to JSON (see `.env.example`).

- **Config (`app/core/config.py`, `.env.example`):** `AGENT_POD_URL`, `AGENT_POD_TOKEN`,
  `AGENT_MODEL`, `AGENT_TOOLS`, `AGENT_MAX_BUDGET_USD`, `AGENT_REQUEST_TIMEOUT`. Env-driven, never
  hardcoded. List fields (`AGENT_TOOLS`, `CORS_ALLOWED_ORIGINS`) are JSON arrays.
- **Workspace transport (`WORKSPACE_TRANSPORT`, `MINIO_*`):** how the gathered workspace reaches the
  pod. `file` (default) passes a `file://` path — the pod must share this host's filesystem
  (single-host dev). `minio` uploads the workspace as an archive to an S3-compatible store
  (`MINIO_ENDPOINT`/`MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY`/`MINIO_BUCKET`/`MINIO_SECURE`/
  `MINIO_CERT_CHECK`) and hands the pod a pre-signed https URL it pulls over the network, so the pod
  shares **no filesystem** with this backend. `app/llm/workspace.py` `publish_workspace(local_dir,
  settings)` does this (and returns the post-run cleanup); `_prepare_workspace` produces the local
  dir, `run_agent` publishes then reaps. Tested in `tests/test_workspace_transport.py`.
- **Backend:** `app/llm/agent.py` — the pod client. `run_agent(query, prior_findings?)` classifies the
  query, renders a **dedicated autonomous system prompt** (`prompts/templates/agent_system.j2` via
  `_agent_system_prompt`) — *not* the generate-only chat template, which asks clarifying questions and
  assumes local files. The agent prompt tells the model to analyze the BGP data the backend has already
  gathered and staged as a read-only workspace, in ordinary Python, and report findings without asking —
  it does not fetch and does not write pybgpstream. It
  POSTs one run with the bearer token and translates the pod's `event:`-framed SSE
  (`: keep-alive` → `cost` → `done`) into typed `Running` / `RunResult` events.
  `app/api/routes/agent.py` — `POST /api/agent/run`, mounted under `/api`, re-streams those as this
  backend's `data:{status}` frames.
- **BGP data: the backend gathers and stages it; the agent only analyzes (architecture decision,
  2026-07-12).** An earlier version gave the agent a thin MCP fetch tool (`bgp_mcp/`, backed by
  pybgpstream) it called at runtime — **now removed.** Why: a BGP fetch is slow network I/O (tens of
  seconds — see latency below), and opencode caps a single MCP tool call with an internal timeout the
  pod does not surface, so wide fetches were aborted mid-call. The fix follows the `ai-auditor`
  isolated-scan-pod pattern (`~/Desktop/ai-auditor`, `backend/isolated_scanner`): **stage the slow data
  before the run; let the agent work over local files.** `app/bgp/` gathers updates with pybgpstream
  (in-process, async, parallelizable across windows/collectors, under the backend's *own* timeout — no
  per-tool-call ceiling) and reduces them to an analysis-ready dataset (`app/bgp/records.py` shapes each
  element into a compact JSON record — the reusable piece kept from `bgp_mcp/`). `run_agent` stages that
  dir and passes it as the pod's read-only `workspace` (`file://` by reference; the pod copies it into a
  throwaway cwd per run, via its `stage_workspace`). The agent reads the staged files with
  Bash/Read/Write — no fetch, no pybgpstream, no MCP. This keeps the pod domain-free and the slow work
  under the backend's control, where longer ranges and multiple timelines become "gather more windows in
  parallel before dispatch." **Built (2026-07-12):** `app/bgp/gather.py` `gather_and_stage(plan, settings)`
  reads each collector concurrently in worker threads under `bgp_gather_timeout_seconds`, reduces via
  `records.py`, writes `updates.json` + `manifest.json` to a throwaway dir, and returns it; `run_agent`
  passes `file://<dir>` as the workspace and reaps it after the run. pybgpstream is a lazy import — its
  absence raises `GatherUnavailable` and `run_agent` falls back to a statically staged `BGP_DATA_ROOT`.
- **The fetch is a guarded plan, not the agent's free choice.** The shared `classify_intent → BgpIntent`
  step (used by both chat `service.py` and agent `agent.py`) extracts the filter (prefixes, target_asn,
  time_window, collectors) via structured output; its field `description`s steer the classifier LLM at
  no prompt-token cost. `BgpIntent` is deliberately tolerant (bad param → None, never raises) so chat
  can't fail on it — so it is **not** the guardrail. A deterministic gate on the agent branch
  (`app/bgp/fetch_plan.py` `build_fetch_plan(intent, settings) → FetchSpec | None`, built) enforces the
  gather bounds: scope required (prefix or ASN, else None → skip gather), window defaulted + capped
  (`bgp_gather_default/max_window_minutes`), collectors defaulted + capped (`bgp_gather_default/max_collectors`).
  Required
  schema fields only make the LLM *fill* a value; the hard bounds must be code (an LLM will fill a
  "required" window with a 30-day span). Chat is untouched — it generates a script the user runs; the
  two flows share the front and diverge at execution.
- **Gather latency (measured — why staging wins):** network-bound, ~30 s fixed floor (broker + archive
  open) + ~3 s/min of window (1 min ≈ 31 s, 5 min ≈ 41 s, 20 min ≈ 88 s; sparse windows still scan fully
  because the prefix filter runs in libBGPStream). A prefix-filtered gather *emits* only matching records
  (KBs–MBs) even though it *scans* GBs — the GBs live and die inside the gather step and never cross to
  the pod, so the staged workspace stays small. Because the backend owns this wait (not a tool call), a
  long or multi-timeline analysis is bounded only by the pod's env-configurable `AGENT_POD_SESSION_TIMEOUT`
  / `AGENT_POD_MAX_TURNS`, never by opencode's hidden tool-call timeout.
- **SSE vocab:** `agent_started` → `token` (an answer-text chunk) / `tool` (a tool-call transition:
  `id`, `name`, `state`, `input`, `output`) / `running` (one frame per pod keep-alive) → `result`
  (the answer plus cost/turns/duration/subtype) → `error`. The `token`/`tool` frames are the pod's
  live events, relayed one-for-one (`app/llm/agent.py` `_relay` → typed `Token`/`ToolCall` →
  `app/api/routes/agent.py`).
- **Frontend:** `hooks/use-bgp-agent.ts` (mirrors `use-bgp-chat.ts`; threads the last successful run's
  answer forward as `prior_findings`, the memory unit; merges `token`/`tool` frames into a per-run
  `trace`) + `pages/bgp-agent-page.tsx` (the console) + `components/agent/agent-run-card.tsx`
  (question → live tool-call trace + streaming answer → result card with metadata badges). Errors use
  `destructive`; the reserved amber `anomaly` is untouched.
- **v1 sends no `response_schema`** (a free-text answer suits an execute-and-report agent better than
  the generate-only `BgpScript` schema); the pod contract allows adding a schema later. The workspace
  is the freshly gathered-and-staged dataset (`_prepare_workspace` → `gather_and_stage`), passed as
  `workspace: {source: "file://<staged-dir>", mode: "ro"}`; on a no-scope query or a gather miss it
  falls back to a static `BGP_DATA_ROOT` (attached only when that directory exists, else an empty
  scratch dir).
- **Run it locally:** `cd ../opencode-agent-pod && .venv/bin/python -m pod` — the pod now auto-loads
  that repo's `.env`, so just set `AGENT_POD_TOKEN` + a provider key there. A dev token
  (`local-dev-pod-token`) is already wired in both repos' `.env`; the matching `AGENT_POD_TOKEN` /
  `AGENT_POD_URL` are set here. Then a question at `/bgp_agent` runs end to end.
- **Runtime note (not a caveat — built):** live gather needs pybgpstream at runtime. It's excluded
  from the slim `api` image and won't `pip install` on macOS. So `_prepare_workspace` gathers when
  pybgpstream is importable; otherwise it falls back, in order, to a configured `BGP_DATA_ROOT` (if the
  dir exists) then the **bundled synthetic `sample_bgp_data/`** (`bgp_sample_data_root`, default on) —
  so the demo works out of the box on a dev host with no config, logging a loud "SYNTHETIC sample"
  warning. Set `BGP_SAMPLE_DATA_ROOT=` empty to disable the fallback (an empty workspace is then
  preferable to fake data). Verified 2026-07-12: with default `BGP_DATA_ROOT=/data/bgp` (absent) and no
  pybgpstream, a scoped MOAS query auto-staged the sample and the agent reported the AS13335→AS64500
  conflict. In production, run the gather where BGPStream is installed — the `docker/Dockerfile.bgpstream`
  runtime. (The earlier "is the GPT default verified?" caveat is now
  **closed**: with a real `OPENAI_API_KEY` in the pod's `.env`, `AGENT_MODEL=gpt-5.4-mini-2026-03-17`
  ran end to end on opencode 1.17.11 — verified 2026-07-12 via the pod's `scripts/live_events_probe.py`:
  a real multi-turn tool loop, live token/tool trace, success in 3 turns for ~$0.007. Anthropic
  (`claude-haiku-4-5-20251001`) works too. The pod loads `.env` once at startup, so a running pod must
  be restarted to pick up changed keys.)

### Isolated deployment (`make up-agent`) — built + verified 2026-07-14

For the decoupled, security-correct topology (pod shares no filesystem or network with this
backend), `docker-compose.pod.yml` overlays the dev stack with three services and an internal
network:

- **pod** — the `opencode-agent-pod`, built from `../opencode-agent-pod`, on an `internal` network
  with **no route to the internet**. It reaches providers only through the egress proxy
  (`HTTP(S)_PROXY`), pulls workspaces from MinIO directly (`NO_PROXY`), and accepts MinIO's
  self-signed cert (`AGENT_POD_WORKSPACE_TLS_VERIFY=0`, `AGENT_POD_WORKSPACE_HOST_ALLOWLIST=minio`).
- **minio** — neutral S3-compatible workspace storage over TLS (self-signed dev cert from
  `./scripts/gen_minio_cert.sh`). The backend uploads here and the pod pulls a pre-signed URL.
- **egress** — a deny-by-default `tinyproxy` allowlisting only the provider hosts
  (`docker/egress/filter`); the only egress hole from the pod's internal network.

The overlay also mounts `./sample_bgp_data` into the api container at `/app/sample_bgp_data:ro`.
The image ships no BGP data and has no `pybgpstream`, so the agent path falls back to the bundled
synthetic sample — without the mount the fallback yields `None`, no workspace is staged, and the
MinIO transport is skipped (the pod gets an empty cwd). Mount it so a real workspace is actually
pushed through MinIO.

Run: `./scripts/gen_minio_cert.sh` once, set `AGENT_POD_TOKEN` + a provider key in `.env`, then
`make up-agent` (GPT path, no GPU).

**Verified end to end 2026-07-14.** A real `POST /api/agent/run` (anomaly query on `8.8.8.0/24`)
completed with `subtype=success` in 5 turns / $0.024, and the agent correctly identified the
sample's designed AS7922 origin hijack. All three isolation properties were exercised in that one
run: the api tarred the workspace and published a pre-signed object to MinIO; the pod fetched that
exact `https://minio:9000/...` URL over the internal net (TLS-verify-off warning as designed); and
the GPT call reached OpenAI only through the egress proxy (the pod has no other route out). Isolation
mechanics were separately probed: `example.com` refused (proxy `403`), no direct internet without the
proxy (DNS fails). Arch note: the amd64 `tinyproxy` image runs emulated on arm64 (restart policy
covers the occasional hiccup); use a native-arm64 proxy image for steadiness.

## Common Commands

### Docker (primary workflow)

```bash
make up-dev        # Build + start dev stack (vllm + api + nginx), tail logs
make up-nogpu      # api + nginx only, no vllm (--no-deps): GPT path, no GPU needed
make down-dev      # Stop dev stack
make up-prod       # Build + start prod stack
make down-prod     # Stop prod stack
make logs          # Tail all logs
make rebuild-dev   # Force a fresh dev rebuild
make clean         # Prune unused Docker resources
```

Uses Docker Compose **v2** (`docker compose`). No migrations / collectstatic step anymore.
`vllm` needs an NVIDIA GPU host (see Deployment).

### Backend (manual, from repo root)

Always run Python tooling through the project virtualenv, never a global `python`.

`make dev` (→ `scripts/dev.sh`) runs the backend (:8002) and the Vite frontend (:3000) together for
local no-Docker work; open http://localhost:3000 and Ctrl-C stops both. The steps it wraps:

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Dev (reload): needs a reachable model server — set LLAMA_BASE_URL / OPENAI_API_KEY in .env
uvicorn app.main:app --reload --port 8002
# Prod-style:
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8002 --timeout 300
```

### Frontend (from `react_frontend/`)

```bash
yarn install      # Node 18+ (.yarnrc sets --ignore-engines for Node 23)
yarn dev          # Vite dev server on :3000, proxies /api -> :8002
yarn build        # production build -> build/ (served by nginx at web root)
yarn typecheck    # tsc --noEmit
yarn lint         # ESLint (--fix)
yarn prettier     # Prettier (--write)
```

Config lives in `src/config.ts`; the backend origin is overridable via `VITE_API_URL`. No hardcoded
backend hostnames.

### Tests & linting (from repo root)

```bash
pip install -r requirements-dev.txt
pytest                      # unit tests in tests/ (LLM is mocked — no network)

pre-commit install
pre-commit run --all-files  # ruff (lint+fix), ruff-format, mypy
```

Tests use FastAPI's `TestClient` and monkeypatch `stream_chat`, so they never hit
OpenAI or vLLM. Cover: config parsing, provider mapping, query classification (with a
faked LLM + the heuristic fallback), prompt-template rendering, the SSE event sequence
(incl. the error path), and the download traversal guard.

## Code Style

- **Backend:** Python 3.12. Ruff for lint + format (line-length 100, target py312) and mypy, both in
  `pyproject.toml`. Python is at the root under `app/` — no `backend/` prefix.
- **Frontend:** TypeScript (strict), ESLint (flat config) + Prettier. Styling via Tailwind +
  shadcn/ui primitives in `src/components/ui/`; the `cn()` helper is in `src/lib/utils.ts`. Amber
  (`--anomaly` / the `anomaly` color) is reserved for routing anomalies/alerts — don't reuse it.

### Docstrings, comments & coding style

These mirror the conventions in the sibling `opencode-agent-pod` (the most recently maintained of
these projects); keep them consistent.

- **Docstrings and comments are self-contained and describe behaviour, not the repo.** A docstring
  says, clearly and concisely, what the thing does; a function's docstring describes what that
  function does. Don't reference design/plan/PR notes ("as decided…", "see the plan") and don't name
  other functions, variables, or modules to explain a line — if the reader has to go elsewhere to
  understand it, rewrite it to stand alone. Env var names and external tools (`vLLM`, `opencode`) are
  fine; they are the interface, not cross-references. Terse and plain: one line where it fits, no
  `Args:`/`Returns:` restating the signature.
- **Favor readability over brevity.** Descriptive names, no cryptic abbreviations; code should read
  as its own explanation. Flatten deep nesting, preferring early returns over pyramids of
  `if`/`try`. Keep private helpers at the bottom of the file, and split them into a dedicated module
  once there are many, letting the larger function coordinate them.
- **Error-handling posture: critical paths fail loudly, non-critical fail soft.** Auth, config, and
  the request path surface failures rather than swallowing them; best-effort work (query
  classification, teardown, tracing) may suppress and log at warning level with a sensible fallback,
  never crashing a request over it.
- **Match the surrounding file** — comment density, naming, and idiom — and reuse an existing helper
  before adding a new one.

## Development Guidelines

1. **Read existing code first** — match the patterns already in `app/`.
2. **Config is env-driven** — add settings to `app/core/config.py` (pydantic-settings), never
   hardcode URLs / keys / model names.
3. **One provider path** — GPT and LLaMA both flow through `stream_chat()` in `app/llm/service.py`;
   per-model differences belong in `app/llm/providers.py`, not in the routes.
4. **Everything under `/api`** — routers are mounted with the `/api` prefix; nginx serves the SPA and
   proxies `/api` to the backend.
5. **Keep it simple** — this is a research codebase; prefer straightforward implementations.

## Configuration & Secrets

- All config comes from `.env` (git-ignored); template in `.env.example`. Read via
  `pydantic-settings` in `app/core/config.py`; unknown keys are ignored.
- Key vars: `OPENAI_API_KEY`, `OPENAI_MODEL`, the `LLAMA_*` block (`LLAMA_BASE_URL`, `LLAMA_MODEL`,
  `LLAMA_API_MODE`=`completion`|`chat`, …), the classifier controls (`CLASSIFIER_ENABLED`,
  `CLASSIFIER_MODEL`), the `VLLM_*` tuning block, the conversation-memory controls
  (`GPT_HISTORY_MAX_TOKENS`, `LLAMA_HISTORY_MAX_TOKENS`, `HISTORY_KEEP_RECENT_TURNS`), and `hf_token`
  (lowercase — used by the vLLM container to pull weights).
- Query classification is a best-effort GPT call: with `CLASSIFIER_ENABLED=false` or no
  `OPENAI_API_KEY`, chat falls back to a substring heuristic (same routing as before).
- `LLAMA_API_MODE=completion` (default) sends a raw prompt to vLLM's `/v1/completions`, matching the
  fine-tune's training format; set `chat` if you serve with a chat template.

## Conversation memory

- **The chat request is a POST** (`{query, history}`) streamed back as SSE — the frontend reads the
  stream with `fetch` + a reader, not native `EventSource` (which is GET-only and can't carry
  history). The SSE frame format is unchanged.
- The frontend holds the whole conversation and sends prior turns as `history` on every request, so
  the model can refine across turns. `app/llm/memory.py` estimates the size (~4 chars/token, no
  tokenizer dependency) and, once it exceeds the provider's window (`*_HISTORY_MAX_TOKENS`),
  summarizes the oldest turns into a running summary while keeping the last `HISTORY_KEEP_RECENT_TURNS`
  verbatim (Claude-Code-style compaction). Summarization is best-effort GPT; on failure or no key it
  degrades to plain truncation. When compaction happens the stream emits a `compacted` event and the
  UI shows a notice.
- Generated scripts are syntax-checked (`ast.parse`, never run) before `code_ready`; a bad parse
  ships the code with a `warning` field, surfaced as a UI notice. Running the script (and repairing
  runtime errors) belongs to the planned opencode-agent-pod, not this backend.
- Generated scripts read BGP update files from `BGP_DATA_ROOT` (filled into the prompt templates).
  Because the fine-tuned LLaMA has its training data directory (`/home/<user>/ris_bgp_updates`) baked
  into its weights and reproduces it regardless of the prompt, `sanitize_script` rewrites that prefix
  to `BGP_DATA_ROOT` before the script is returned — so no personal path leaks into output on either
  model path.

## Deployment & DevOps

- Docker Compose: `docker-compose.base.yml` + a `dev`/`prod` override (via the Makefile). Services:
  `vllm`, `api`, `nginx`.
- **`vllm`** is the only GPU-backed service (NVIDIA runtime); it serves the local model over an
  OpenAI-compatible `/v1` API and caches weights in the `hf_cache` volume. `api` reaches it at
  `http://vllm:8000/v1` (set via `LLAMA_BASE_URL` on the service). Tune via `VLLM_*`. On a GPU-less
  machine, skip `vllm` and point `LLAMA_BASE_URL` at a vLLM elsewhere (or use GPT only).
- **`api`** builds from `docker/Dockerfile.api` (`python:3.12-slim`; `requirements.txt` = fastapi/
  uvicorn/gunicorn/openai/httpx/pydantic-settings, no ML libs). Listens on `:8002`.
- **nginx** builds from `docker/Dockerfile.web` — a multi-stage image that runs `yarn install` +
  `yarn build` (Node only in the build stage) and serves the SPA at the web root (fallback to
  `index.html`), proxying `/api` → `api:8002` with buffering off for SSE. So `make up-*` needs no
  host Node and no manual `yarn build`. TLS is not wired in the base config — add a cert-aware server
  block + Let's Encrypt mounts in the prod override when deploying publicly.
- **`docker/Dockerfile.bgpstream`** is a **standalone** image (not in the compose stack) that provides
  the pybgpstream runtime for the backend's BGP gather step (see the BGP agent section). Multi-stage:
  the builder compiles CAIDA wandio + libBGPStream 2.2.0 from source (glibc-2.36 workaround — rewrite
  `pthread_yield` → `sched_yield` and neutralize the `configure` abort) and builds a pybgpstream wheel;
  the final stage carries only the runtime shared libs + that wheel, so no toolchain ships. The `api`
  image stays slim and BGPStream-free. The **pod** runs the plain domain-free `opencode-agent-pod` image
  — no BGP runtime in it; egress to the RIS/RouteViews broker is needed only where gather runs (the
  backend). For a separate-host (K8s) deploy where a `file://` workspace isn't shared between backend and
  pod, add a generic object-store (`s3://`) source to the pod's `stage_workspace` (domain-agnostic) and
  hand off by key. (The removed MCP path had a `bgp-pod.Dockerfile` + `run-bgp-pod.bash` that layered
  pybgpstream + `bgp_mcp` onto the pod base; both are deleted.)

## Gotchas

- The frontend's fine-tuning page posts to `/api/finetuning`, which **has no backend** — it's an
  unimplemented feature, not a regression.
