## Project Overview

BGP-LLaMA Webservice is an AI-powered platform for **BGP routing analysis and anomaly detection**.
It combines an instruction fine-tuned **LLaMA** model with **GPT-4o-mini**, streams model output to
the browser over SSE, and can execute the analysis code the model generates. It has three
components:

- **Django backend (ASGI/Daphne)** — REST API, auth/sessions, chat-history persistence, and serves
  the built React SPA. Code in `app_1/` (app) and `project_1/` (project config).
- **FastAPI agent** — LLaMA/GPT SSE streaming microservice. Code in `fastapi_agent/`.
- **React frontend** — Vite + React 18 + **TypeScript** SPA in `react_frontend/`, styled with
  Tailwind CSS + shadcn/ui. (Migrated off Create React App; MUI and Redux were removed.)

Backend Python (Django + FastAPI) lives at the repository root — there is **no** `backend/`
directory. See [README.md](README.md) for architecture and setup.

## Common Commands

### Docker (primary workflow)

```bash
make up-dev        # Build + start dev stack (web + fastapi + nginx + db), tail logs
make down-dev      # Stop dev stack
make up-prod       # Build + start prod stack
make down-prod     # Stop prod stack
make logs          # Tail all logs
make rebuild-dev   # Force a fresh dev rebuild
make clean         # Prune unused Docker resources
make help          # List targets
```

Uses Docker Compose **v2** (`docker compose`). Run migrations after first start:

```bash
docker compose -f docker-compose.base.yml -f docker-compose.dev.yml exec web python manage.py migrate
```

### Backend (manual, from repo root)

Always run Python tooling through the project virtualenv, never a global `python`.

```bash
python3.9 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py collectstatic --noinput
daphne -b 0.0.0.0 -p 8001 project_1.asgi:application        # Django (ASGI)
uvicorn fastapi_agent.main:app --host 0.0.0.0 --port 8002   # FastAPI agent
```

### Frontend (from `react_frontend/`)

```bash
yarn install      # Node 18+ (.yarnrc sets --ignore-engines for Node 23)
yarn dev          # Vite dev server on :3000, proxies /api -> :8001 and /agent -> :8002
yarn build        # production build -> build/ (served by Django under /static/)
yarn typecheck    # tsc --noEmit
yarn lint         # ESLint (--fix)
yarn prettier     # Prettier (--write)
```

Config lives in `src/config.ts`; backend origins are overridable via `VITE_API_URL` /
`VITE_AGENT_URL` (`.env.development`). No hardcoded backend hostnames.

### Linting (from repo root)

```bash
pre-commit install
pre-commit run --all-files
```

## Code Style

- **Backend:** Ruff for lint + format (line-length 100, target py39) and mypy, both configured in
  `pyproject.toml`. Do not add a `backend/` prefix to paths — Python is at the root.
- **Frontend:** TypeScript (strict), ESLint (flat config) + Prettier. Styling via Tailwind +
  shadcn/ui primitives in `src/components/ui/`; the `cn()` helper is in `src/lib/utils.ts`. Amber
  (`--anomaly` / the `anomaly` color) is reserved for routing anomalies/alerts — don't reuse it.
- Django settings are split: `project_1/settings/base.py` with `development.py` / `production.py`
  overrides, selected by `DJANGO_ENV` (or an explicit `DJANGO_SETTINGS_MODULE`).

## Development Guidelines

1. **Read existing code first** — match the patterns already in `app_1/` and `fastapi_agent/`.
2. **Reuse existing helpers** — check `app_1/utils/` (code extraction/execution, model loading,
   stop criteria) before writing new ones.
3. **Keep it simple** — this is a research codebase; prefer straightforward implementations.
4. **Two backends, one repo** — Django (`:8001`) and FastAPI (`:8002`) are separate services behind
   Nginx (`/agent/*` → FastAPI, everything else → Django). Keep that boundary clear.
5. **SSE is the live path; WebSockets are legacy** — new streaming work goes through the FastAPI
   agent, not the `app_1/consumers/` WebSocket consumers.

## Configuration & Secrets

- All config comes from `.env` (git-ignored); template in `.env.example`.
- `.env` is read by both Django (`project_1/settings/base.py`) and FastAPI (`fastapi_agent/main.py`)
  via `django-environ`.
- Keep `DB_*` (Django) and `POSTGRES_*` (Postgres container) values in sync.
- Model access needs `OPENAI_API_KEY` and `hf_token` (note the lowercase name, read in
  `app_1/utils/model_loader.py`).

## Deployment & DevOps

- Docker Compose: `docker-compose.base.yml` + a `dev`/`prod` override (via the Makefile).
- Nginx terminates TLS (Certbot / Let's Encrypt) and reverse-proxies both backends; SSE routes
  disable buffering.
- The FastAPI service is GPU-backed (NVIDIA runtime) and mounts a host Hugging Face cache
  (`HF_CACHE_DIR`).
- The React `build/` is git-ignored — run `yarn build` before `collectstatic` / Docker image builds
  so Django can serve the SPA under `/static/`.

## Gotchas

- Django migrations **must** be committed; `.gitignore` only excludes their bytecode.
- `staticfiles/` is generated by `collectstatic` and git-ignored — do not hand-edit it.
- Production channel layer uses Redis (`channels_redis`); the Redis service in compose is currently
  commented out — enable it before relying on WebSocket production features.
