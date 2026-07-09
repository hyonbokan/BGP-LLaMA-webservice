# BGP-LLaMA Webservice

AI-powered web application for **BGP routing analysis and anomaly detection**. It pairs an
instruction fine-tuned **LLaMA** model with **GPT-4o-mini** to turn natural-language questions
into BGP insights, streams the reasoning back live, and can execute the analysis code it
generates for deeper investigation.

🔗 **Live demo:** [llama.cnu.ac.kr](https://llama.cnu.ac.kr/)

> **Original codebase:** 2024-01-25 → 2025-04-04 is master's thesis work.
> **Update & Refactor:** 2026-07-09 onward is refactoring

---

## Architecture

```
                       ┌─────────────────────────────┐
   Browser  ──────────▶│  Nginx (reverse proxy, SSL)  │
                       └──────────────┬──────────────┘
             /, /ws/, /static/ │              │ /agent/  (SSE, buffering off)
                               ▼              ▼
        ┌──────────────────────────┐   ┌──────────────────────────┐
        │  Django ASGI (Daphne)     │   │  FastAPI agent            │
        │  :8001                    │   │  :8002                    │
        │  REST API + WebSockets    │   │  LLaMA / GPT SSE streaming│
        │  serves React build       │   │  code extraction          │
        └────────────┬─────────────┘   └────────────┬─────────────┘
                     │                               │
                     ▼                               ▼
              ┌────────────┐                  ┌──────────────────┐
              │ PostgreSQL │                  │ HF Transformers  │
              │ (chat log) │                  │ + GPU (CUDA)     │
              └────────────┘                  └──────────────────┘
```

- **Django (Daphne, ASGI)** — REST API, session/auth, chat-history persistence, and serves the
  built React SPA. WebSocket consumers in [`app_1/consumers/`](./app_1/consumers/) are **legacy**;
  production streaming now goes through FastAPI SSE.
- **FastAPI agent** ([`fastapi_agent/`](./fastapi_agent/)) — SSE streaming for the LLaMA and GPT
  chatbots, plus extraction of runnable code from model replies.
- **React SPA** ([`react_frontend/`](./react_frontend/)) — Create React App + Redux Toolkit + MUI.
- **PostgreSQL** — stores conversation IDs and chat history.
- **Nginx** — TLS termination and routing between the two backends (`/agent/*` → FastAPI, rest → Django).

## Tech stack

| Layer     | Technologies                                                                    |
| --------- | ------------------------------------------------------------------------------- |
| Backend   | Django 4.2 (ASGI), Daphne, FastAPI, Django REST Framework, Channels             |
| ML        | Hugging Face Transformers, PEFT, bitsandbytes, OpenAI API (GPT-4o-mini)         |
| Frontend  | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, Axios                      |
| Data      | PostgreSQL 13                                                                   |
| Streaming | Server-Sent Events (current), WebSockets (legacy Django consumers)              |
| DevOps    | Docker Compose, Nginx, Certbot, NVIDIA CUDA runtime                             |

## Repository layout

```
.
├── app_1/                 # Main Django app (models, views, consumers, LLM utils)
│   ├── consumers/         #   Legacy WebSocket consumers
│   ├── utils/             #   Model loading, code extraction/execution, stop criteria
│   └── views/             #   ASGI views
├── project_1/             # Django project (asgi/wsgi, urls, settings package)
│   └── settings/          #   base.py + development.py / production.py
├── fastapi_agent/         # FastAPI SSE microservice
│   ├── routers/           #   llama_routes.py, gpt_routes.py
│   └── services/          #   llama_agent.py, gpt_agent.py, gpt_service.py
├── prompts/               # Prompt templates for LLaMA / GPT
├── scripts/               # Data loading helpers
├── react_frontend/        # React + TS SPA (Vite; build/ served by Django)
├── docker/                # Dockerfiles (daphne, fastapi) + nginx config
├── docker-compose.*.yml   # base + dev/prod overrides
├── pyproject.toml         # ruff + mypy config (backend)
└── requirements.txt       # Python dependencies (pinned)
```

## Prerequisites

- Docker & Docker Compose **v2** (`docker compose`)
- NVIDIA GPU + drivers + NVIDIA Container Toolkit (for the LLaMA/FastAPI service)
- For manual (non-Docker) setup: Python 3.9, Node.js 18+, PostgreSQL 14+

## Quickstart (Docker)

```bash
# 1. Configure environment
cp .env.example .env
#    then edit .env — set SECRET_KEY, DB/POSTGRES credentials, OPENAI_API_KEY, hf_token

# 2. Build and start the dev stack (web + fastapi + nginx + db), tailing logs
make up-dev

# 3. Apply database migrations (first run)
docker compose -f docker-compose.base.yml -f docker-compose.dev.yml \
  exec web python manage.py migrate

# Stop it
make down-dev
```

Run `make help` to list all targets (`up-dev`, `down-dev`, `up-prod`, `down-prod`, `logs`,
`rebuild-dev`, `clean`).

Services once up:

| Service       | URL / port              |
| ------------- | ----------------------- |
| Django (API)  | http://localhost:8001   |
| FastAPI agent | http://localhost:8002   |
| Nginx         | http://localhost:80     |

## Manual setup (without Docker)

```bash
# --- Backend ---
python3.9 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # edit values; set DB_HOST=localhost

python manage.py migrate
python manage.py collectstatic --noinput
daphne -b 0.0.0.0 -p 8001 project_1.asgi:application        # Django (ASGI)
uvicorn fastapi_agent.main:app --host 0.0.0.0 --port 8002   # FastAPI (separate shell)

# --- Frontend (Vite + TypeScript) ---
cd react_frontend
yarn install
yarn dev          # dev server on :3000, proxies /api -> :8001 and /agent -> :8002
yarn build        # production build -> react_frontend/build (served by Django under /static/)
yarn typecheck    # tsc --noEmit
yarn lint         # ESLint (--fix)
```

> The dev server proxies API/SSE calls to the backends, so you can run just the frontend
> (`yarn dev`) against a running Django + FastAPI and iterate without CORS setup. Backend base
> URLs are configurable via `VITE_API_URL` / `VITE_AGENT_URL` (see `.env.development`).

## Environment variables

All configuration is read from `.env` (git-ignored). See [`.env.example`](./.env.example) for the
full, documented list. Key groups:

- **Django** — `SECRET_KEY`, `DEBUG`, `DJANGO_ENV`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`
- **Database** — `DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT` (Django) and the matching
  `POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD` (Postgres container)
- **Models** — `OPENAI_API_KEY`, `hf_token`, `HF_CACHE_DIR`

## Development tooling

```bash
pip install pre-commit
pre-commit install          # install the git hook
pre-commit run --all-files  # ruff (lint+format), mypy, hygiene, frontend prettier/eslint
```

- **Backend:** [ruff](https://docs.astral.sh/ruff/) for lint + format and mypy for type checks,
  configured in [`pyproject.toml`](./pyproject.toml).
- **Frontend:** ESLint + Prettier (`cd react_frontend && yarn lint && yarn prettier`).

## Notes

- The React SPA is built with Vite to `react_frontend/build/` and served by Django under
  `/static/` (see `TEMPLATES` / `STATICFILES_DIRS` in `project_1/settings/base.py`). The build
  output is **not** committed (git-ignored) — run `yarn build` before `collectstatic` / Docker.
- WebSocket consumers under `app_1/consumers/` are retained for reference but superseded by FastAPI SSE.
