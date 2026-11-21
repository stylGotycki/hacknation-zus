.PHONY: up down restart logs ps seed reset-db test check-routes fmt shell-backend shell-db

up:            ## Build and start the whole stack (http://localhost)
	docker compose up -d --build
	@echo "App: http://localhost   API docs: http://localhost/api/docs"

down:          ## Stop containers (database volume is kept)
	docker compose down

restart: down up

logs:          ## Follow logs of all services
	docker compose logs -f --tail=100

ps:
	docker compose ps

seed:          ## Re-run the idempotent seed of legal parameters
	docker compose exec backend python -m app.seed

reset-db:      ## Drop the database volume and start fresh
	docker compose down -v
	docker compose up -d --build

test:          ## Run backend tests (in-memory SQLite, no running stack needed)
	docker compose run --rm --no-deps backend pytest -q

check-routes:  ## Verify nginx URL table, routes.ts and app folders agree
	docker compose run --rm --no-deps -v $(CURDIR):/repo:ro backend python /repo/scripts/check_routes.py

fmt:           ## Format and lint backend code
	docker compose run --rm --no-deps backend sh -c "ruff format app && ruff check --fix app"

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec db psql -U app -d parent_guide
