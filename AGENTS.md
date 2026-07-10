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
  utils/code_extract.py   # pull the ```python block out of a reply
  api/routes/
    health.py             # GET /api/health
    chat.py               # GET /api/chat/bgp_gpt, /api/chat/bgp_llama  (SSE)
    files.py              # GET /api/download                          (traversal-guarded)
prompts/                  # prompt strings (pure data, no heavy imports)
```

## Common Commands

### Docker (primary workflow)

```bash
make up-dev        # Build + start dev stack (vllm + api + nginx), tail logs
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

```bash
python3.9 -m venv .venv && source .venv/bin/activate
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
OpenAI or vLLM. Cover: config parsing, provider mapping, code extraction, the SSE
event sequence (incl. the error path), and the download traversal guard.

## Code Style

- **Backend:** Ruff for lint + format (line-length 100, target py39) and mypy, both in
  `pyproject.toml`. Python is at the root under `app/` — no `backend/` prefix.
- **Frontend:** TypeScript (strict), ESLint (flat config) + Prettier. Styling via Tailwind +
  shadcn/ui primitives in `src/components/ui/`; the `cn()` helper is in `src/lib/utils.ts`. Amber
  (`--anomaly` / the `anomaly` color) is reserved for routing anomalies/alerts — don't reuse it.

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
  `LLAMA_API_MODE`=`completion`|`chat`, …), the `VLLM_*` tuning block, and `hf_token` (lowercase —
  used by the vLLM container to pull weights).
- `LLAMA_API_MODE=completion` (default) sends a raw prompt to vLLM's `/v1/completions`, matching the
  fine-tune's training format; set `chat` if you serve with a chat template.

## Deployment & DevOps

- Docker Compose: `docker-compose.base.yml` + a `dev`/`prod` override (via the Makefile). Services:
  `vllm`, `api`, `nginx`.
- **`vllm`** is the only GPU-backed service (NVIDIA runtime); it serves the local model over an
  OpenAI-compatible `/v1` API and caches weights in the `hf_cache` volume. `api` reaches it at
  `http://vllm:8000/v1` (set via `LLAMA_BASE_URL` on the service). Tune via `VLLM_*`. On a GPU-less
  machine, skip `vllm` and point `LLAMA_BASE_URL` at a vLLM elsewhere (or use GPT only).
- **`api`** builds from `docker/Dockerfile.api` (slim: `requirements.txt` = fastapi/uvicorn/gunicorn/
  openai/httpx/pydantic-settings, no ML libs). Listens on `:8002`.
- **nginx** serves `react_frontend/build` at the web root (SPA fallback to `index.html`) and proxies
  `/api` → `api:8002` with buffering off for SSE. TLS is not wired in the base config — add a
  cert-aware server block + Let's Encrypt mounts in the prod override when deploying publicly.
- Run `yarn build` before `make up-*` so nginx has a build to serve (`react_frontend/build` is
  git-ignored).

## Gotchas

- `staticfiles/` and `debug.log` are **orphaned Django leftovers** — safe to delete.
- `requirements.legacy.txt` is kept for reference only; nothing uses it.
- The frontend's fine-tuning page posts to `/api/finetuning`, which **has no backend** — it's an
  unimplemented feature, not a regression.
