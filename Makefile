# Base Docker Compose file
BASE_COMPOSE=docker-compose.base.yml

# Development override
DEV_COMPOSE=docker-compose.dev.yml

# Production override
PROD_COMPOSE=docker-compose.prod.yml

# Build and start dev environment, then stream logs
up-dev:
	docker-compose -f $(BASE_COMPOSE) -f $(DEV_COMPOSE) up --build -d && \
	docker-compose -f $(BASE_COMPOSE) -f $(DEV_COMPOSE) logs -f

# Stop dev environment
down-dev:
	docker-compose -f $(BASE_COMPOSE) -f $(DEV_COMPOSE) down

# Build and start prod environment, then stream logs
up-prod:
	docker-compose -f $(BASE_COMPOSE) -f $(PROD_COMPOSE) up --build -d && \
	docker-compose -f $(BASE_COMPOSE) -f $(PROD_COMPOSE) logs -f

# Stop prod environment
down-prod:
	docker-compose -f $(BASE_COMPOSE) -f $(PROD_COMPOSE) down

# View logs from all containers
logs:
	docker-compose -f $(BASE_COMPOSE) -f $(PROD_COMPOSE) logs -f

# Rebuild and restart dev environment (force fresh image)
rebuild-dev:
	docker-compose -f $(BASE_COMPOSE) -f $(DEV_COMPOSE) up --build --force-recreate

# Clean up unused containers and volumes
clean:
	docker system prune -f