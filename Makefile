# Uses Docker Compose v2 (`docker compose`, no hyphen). The compose files omit
# the obsolete `version:` key and rely on v2 healthcheck conditions.
COMPOSE=docker compose
BASE_COMPOSE=docker-compose.base.yml
DEV_COMPOSE=docker-compose.dev.yml
PROD_COMPOSE=docker-compose.prod.yml

DEV=$(COMPOSE) -f $(BASE_COMPOSE) -f $(DEV_COMPOSE)
PROD=$(COMPOSE) -f $(BASE_COMPOSE) -f $(PROD_COMPOSE)

.PHONY: up-dev down-dev up-prod down-prod logs rebuild-dev clean help

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

up-dev:  ## Build and start dev containers (detached), then tail logs
	$(DEV) up --build -d && $(DEV) logs -f

down-dev:  ## Stop dev containers
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
