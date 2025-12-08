#!/bin/bash
set -e

# Script de arranque para el servicio cron dentro del contenedor
# Instala cron si es necesario, configura la crontab y lanza cron en primer plano.

LOGFILE=/var/log/cron.log
CRONTAB_FILE=/etc/cron.d/gestion_notificaciones

# Instalar cron si no está instalado (imagen basada en debian)
if ! command -v crond >/dev/null 2>&1 && ! command -v cron >/dev/null 2>&1; then
  apt-get update || true
  apt-get install -y cron || true
fi

# Crear fichero de cron que ejecute la tarea el día 1 a las 00:05
# Redirigimos la salida a /var/log/cron.log
cat > ${CRONTAB_FILE} <<'CRON'
# Ejecutar comando de notificaciones el día 1 a las 00:05
5 0 1 * * root /env/bin/python /app/manage.py generar_notificaciones_mensuales >> /var/log/cron.log 2>&1
CRON

# Ajustar permisos
chmod 0644 ${CRONTAB_FILE}
# Registrar crontab
crontab ${CRONTAB_FILE} || true

# Asegurar que el logfile existe
touch ${LOGFILE}

# Lanzar cron en primer plano
if command -v cron >/dev/null 2>&1; then
  cron -f
elif command -v crond >/dev/null 2>&1; then
  crond -f
else
  echo "cron no disponible"
  tail -f ${LOGFILE}
fi
