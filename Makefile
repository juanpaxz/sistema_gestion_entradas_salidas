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

#-----------------------
#Crear comando django
#-----------------------
comando_faltas: ## Crea un nuevo comando de django dentro de la aplicacion gestion_de_entradas
	docker compose exec gestion_de_entradas bash -c "/env/bin/python manage.py generar_faltas"
#-----------------------
# Crear comando notificaciones
comando_notificaciones: ## Crea un nuevo comando de django dentro de la aplicacion gestion_de_entradas
	docker compose exec gestion_de_entradas bash -c "/env/bin/python manage.py generar_notificaciones_mensuales"

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

shell: ## Abre una terminal bash dentro del contenedor gestion_de_entradas
	docker compose exec gestion_de_entradas bash -c "/env/bin/python manage.py shell"

# Logs
logs:
	docker compose logs -f gestion_de_entradas

#consultas a la base de datos

# -----------------------
# ver tablas de la base de datos
# -----------------------
view_tables: ## Muestra las tablas de la base de datos
	docker compose exec gestion_db mariadb -uuser -padmin1234 -e "USE geston_db; SHOW TABLES;"

# -----------------------
# ver asistencias
# -----------------------
view_asistencias: ## Muestra todas las asistencias en la base de datos
	docker compose exec gestion_db mariadb -uuser -padmin1234 -e "USE geston_db; SELECT * FROM control_asistencia;"

# -----------------------
# eliminar todas las asistencias
# -----------------------
delete_asistencias: ## Elimina todas las entradas de la tabla control_asistencia
	docker compose exec gestion_db mariadb -uuser -padmin1234 -e "USE geston_db; DELETE FROM control_asistencia;"

# -----------------------
# ver horarios
# -----------------------

view_horarios: ## Muestra todos los horarios en la base de datos
	docker compose exec gestion_db mariadb -uuser -padmin1234 -e "USE geston_db; SELECT * FROM control_horario;"

# -----------------------
# ver empleados
# -----------------------
view_empleados: ## Muestra todos los empleados en la base de datos
	docker compose exec gestion_db mariadb -uuser -padmin1234 -e "USE geston_db; SELECT * FROM control_empleado;"

# -----------------------
# control control_empleado_horarios
# -----------------------
view_control_asistencia: ## Muestra todos los registros de control de asistencia en la base de datos
	docker compose exec gestion_db mariadb -uuser -padmin1234 -e "USE geston_db; SELECT * FROM control_empleado_horarios;"

# -----------------------
# ver justificaciones
view_justificaciones: ## Muestra todas las justificaciones en la base de datos
	docker compose exec gestion_db mariadb -uuser -padmin1234 -e "USE geston_db; SELECT * FROM control_justificante;"
# -----------------------
# eliminar justificaciones
# -----------------------
delete_justificaciones: ## Elimina todas las justificaciones de la tabla control_justificacion
	docker compose exec gestion_db mariadb -uuser -padmin1234 -e "USE geston_db; DELETE FROM control_justificante;"	

# -----------------------
#eliminar notificacion
# -----------------------
delete_notificaciones: ## Elimina todas las notificaciones de la tabla control_notificacion
	docker compose exec gestion_db mariadb -uuser -padmin1234 -e "USE geston_db; DELETE FROM control_notificacion;"

# -----------------------
# ver configuraciones del sistema
# -----------------------
view_config: ## Muestra todas las configuraciones del sistema en la base de datos
	docker compose exec gestion_db mariadb -uuser -padmin1234 -e "USE geston_db; SELECT * FROM control_systemconfig;"	

# -----------------------
# insertar datos
# -----------------------

insert_data: ## Inserta datos de prueba en la base de datos desde los fixtures
	docker compose exec gestion_de_entradas /env/bin/python manage.py loaddata control/fixtures/asistencias.json