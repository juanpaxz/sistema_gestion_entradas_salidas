.PHONY: help up down build destroy migrations migrate superuser

# -----------------------
# Help
# -----------------------
help: ## Muestra este mensaje de ayuda
ifeq ($(OS),Windows_NT)
	@powershell -NoProfile -Command "$$pattern = '^[a-zA-Z_-]+:.*?## (.*)$$'; Get-Content Makefile | Select-String $$pattern | ForEach-Object { $$parts = ($$_ -split ':'); if ($$parts.Length -gt 1) { $$name = $$parts[0].Trim(); $$desc = ($$_ -replace '.*## ', ''); Write-Host ('  ' + $$name.PadRight(25) + $$desc) } }"
else
	@echo 'Usage:'
	@echo '  make [target]'
	@echo
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-25s %s\n", $$1, $$2}'
endif

# -----------------------
# Docker
# -----------------------
up: ## Inicia la aplicacion
	docker compose up -d

down: ## Detiene la aplicacion
	docker compose down

build: ## Construye o reconstruye la imagen de docker, ademas de iniciar la aplicacion
	docker compose up -d --build

destroy: ## Remueve todos los contenedores y sus volumenes
	docker compose down -v

# -----------------------
# crear aplicacion
# -----------------------
createapp: ## Crea una nueva aplicacion Django dentro del proyecto gestion_de_entradas
	docker compose exec gestion_de_entradas bash -c "/env/bin/python manage.py startapp $(name)"

# -----------------------
# Makemigrations
# -----------------------
migrations: ## Crea las migraciones para gestion_de_entradas
	docker compose exec gestion_de_entradas bash -c "/env/bin/python manage.py makemigrations"
# -----------------------
# Migrate
# -----------------------
migrate: ## Aplica las migraciones para todas las aplicaciones
	docker compose exec gestion_de_entradas bash -c "/env/bin/python manage.py migrate"

# -----------------------
# Superusers
# -----------------------
superuser: ## Crea un superusuario para gestion_de_entradas
	docker compose exec gestion_de_entradas bash -c "/env/bin/python manage.py createsuperuser"

# Logs
logs:
	docker compose logs -f gestion_de_entradas