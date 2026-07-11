# Uses Docker Compose v2 (`docker compose`, no hyphen). The compose files omit
# the obsolete `version:` key and rely on v2 healthcheck conditions.
COMPOSE=docker compose
BASE_COMPOSE=docker-compose.base.yml
DEV_COMPOSE=docker-compose.dev.yml
PROD_COMPOSE=docker-compose.prod.yml

DEV=$(COMPOSE) -f $(BASE_COMPOSE) -f $(DEV_COMPOSE)
PROD=$(COMPOSE) -f $(BASE_COMPOSE) -f $(PROD_COMPOSE)

.PHONY: dev up-dev up-nogpu down-dev up-prod down-prod logs rebuild-dev clean help

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

dev:  ## Run backend (:8002) + frontend (:3000) locally without Docker; Ctrl-C stops both
	./scripts/dev.sh

up-dev:  ## Build and start dev containers (detached), then tail logs
	$(DEV) up --build -d && $(DEV) logs -f

up-nogpu:  ## Start api + nginx only, skipping the GPU-only vLLM (GPT path only); no GPU needed
	$(DEV) up --build -d --no-deps api nginx && $(DEV) logs -f api nginx

down-dev:  ## Stop dev containers (also tears down anything started by up-nogpu)
	$(DEV) down

up-prod:  ## Build and start prod containers (detached), then tail logs
	$(PROD) up --build -d && $(PROD) logs -f

down-prod:  ## Stop prod containers
	$(PROD) down

logs:  ## Tail logs from all prod containers
	$(PROD) logs -f

rebuild-dev:  ## Force a fresh dev rebuild and restart
	$(DEV) up --build --force-recreate

clean:  ## Remove unused Docker resources
	docker system prune -f
