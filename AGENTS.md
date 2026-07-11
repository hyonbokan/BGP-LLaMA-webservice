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

> **History:** this was a Django (Daphne) + FastAPI two-process app. Django owned auth/ORM/admin but
> none of it was actually used (dead model, empty admin, no live auth), and Django already streamed
> SSE natively — so it was removed. The backend is now pure FastAPI. `requirements.legacy.txt`
> preserves the old full dependency set (Django + the torch/transformers/BGPStream training stack).

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
ran, and reaped it). What's still **not** built: real BGP-data staging (the smoke used a
hand-staged directory) and the live per-step tool trace (a pod dependency — see below). This section
documents the shape; see "How the agent run is wired" below.

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
  Follow-ups are new single-shot runs. **v1** shows *submit → running → terminal result only*,
  because the pod's live `token`/`tool` SSE events aren't built yet (pod DESIGN §9); the live
  step-by-step trace lands once the pod ships those events. Treat the live trace as a pod dependency,
  not something this repo can deliver alone.
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

- **Config (`app/core/config.py`, `.env.example`):** `AGENT_POD_URL`, `AGENT_POD_TOKEN`,
  `AGENT_MODEL`, `AGENT_TOOLS` (comma-separated → the `agent_tool_list` property),
  `AGENT_MAX_BUDGET_USD`, `AGENT_REQUEST_TIMEOUT`. Env-driven, never hardcoded.
- **Backend:** `app/llm/agent.py` — the pod client. `run_agent(query, prior_findings?)` classifies the
  query, renders a **dedicated autonomous system prompt** (`prompts/templates/agent_system.j2` via
  `_agent_system_prompt`) — *not* the generate-only chat template, which asks clarifying questions and
  assumes local files. The agent prompt tells the model to write and RUN pybgpstream code, pull data
  from the public collector broker (or staged local files), and report findings without asking. It
  POSTs one run with the bearer token and translates the pod's `event:`-framed SSE
  (`: keep-alive` → `cost` → `done`) into typed `Running` / `RunResult` events.
  `app/api/routes/agent.py` — `POST /api/agent/run`, mounted under `/api`, re-streams those as this
  backend's `data:{status}` frames.
- **BGP data via a thin MCP tool (`bgp_mcp/`).** Rather than have the LLM hand-write pybgpstream, a
  small MCP server (`bgp_mcp/`, backed by pybgpstream) exposes `fetch_bgp_updates(prefix, from_time,
  until_time, collectors, …)` returning raw update records; the agent calls the tool and analyzes the
  records in ordinary Python. This keeps the pybgpstream dependency and hallucination surface out of
  the LLM's output, and keeps the pod's own code domain-free (the pod just launches the server).
- **Deployment (not yet wired):** the pod must run the server — declare it in the pod's
  `AGENT_MCP_SERVERS` (`[{"name":"bgp","command":["python","-m","bgp_mcp"],"tools":["fetch_bgp_updates"]}]`,
  gated tool id `bgp_fetch_bgp_updates`) on an image that has `bgp_mcp` + `mcp` + **pybgpstream**
  (`docker/Dockerfile.bgpstream` is the base) and egress to the RIS/RouteViews broker. Until that
  runtime exists, the agent proceeds autonomously but reports the data tool is unavailable rather than
  producing analysis. (Fully removing pybgpstream from the pod image would need *remote* MCP — a pod
  registry extension, later.)
- **SSE vocab (v1):** `agent_started` → `running` (one frame per pod keep-alive) → `result` (the
  answer plus cost/turns/duration/subtype) → `error`. The per-step tool trace waits on the pod's live
  `token`/`tool` events (still deferred pod-side).
- **Frontend:** `hooks/use-bgp-agent.ts` (mirrors `use-bgp-chat.ts`; threads the last successful run's
  answer forward as `prior_findings`, the memory unit) + `pages/bgp-agent-page.tsx` (the console) +
  `components/agent/agent-run-card.tsx` (question → live "working" timer → result card with metadata
  badges). Errors use `destructive`; the reserved amber `anomaly` is untouched.
- **v1 sends no `response_schema`** (a free-text answer suits an execute-and-report agent better than
  the generate-only `BgpScript` schema); the pod contract allows adding a schema later. The client
  attaches `workspace: {source: "file://<BGP_DATA_ROOT>", mode: "ro"}` only when that directory
  exists, otherwise the run gets an empty scratch dir.
- **Run it locally:** `cd ../opencode-agent-pod && .venv/bin/python -m pod` — the pod now auto-loads
  that repo's `.env`, so just set `AGENT_POD_TOKEN` + a provider key there. A dev token
  (`local-dev-pod-token`) is already wired in both repos' `.env`; the matching `AGENT_POD_TOKEN` /
  `AGENT_POD_URL` are set here. Then a question at `/bgp_agent` runs end to end.
- **Two caveats from the 2026-07-12 smoke:** (1) the code default `AGENT_MODEL=gpt-5.4-mini-…` is
  **unverified** against the pinned opencode 1.17.11 (a 2026 model on an older binary); the local
  `.env` pins the smoke-verified `claude-haiku-4-5-20251001`. Revisit the default (or add the pod's
  version-gate) before relying on the GPT path. (2) Real BGP-data staging is still unbuilt — the smoke
  hand-staged a directory under `BGP_DATA_ROOT`.

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
- **`docker/Dockerfile.bgpstream`** is a **standalone** image (not in the compose stack) that compiles
  CAIDA wandio + libBGPStream and installs pybgpstream on the same `python:3.12-slim` base — the
  runtime the planned opencode-agent-pod script-execution path will build on. Multi-stage keeps it
  lean (~250 MB vs ~880 MB unsplit): a builder compiles the C libs, the final stage copies only the
  installed libraries + a prebuilt pybgpstream wheel + the runtime-only `.so` packages. Build once by
  hand: `docker build -f docker/Dockerfile.bgpstream -t bgpstream:local .` — it is not rebuilt by
  `make up-*`, and its heavy compile layers are Docker-cached so rebuilds are near-instant unless the
  recipe changes.

## Gotchas

- `staticfiles/` and `debug.log` are **orphaned Django leftovers** — safe to delete.
- `requirements.legacy.txt` is kept for reference only; nothing uses it.
- The frontend's fine-tuning page posts to `/api/finetuning`, which **has no backend** — it's an
  unimplemented feature, not a regression.
