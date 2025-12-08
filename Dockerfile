# Imagen base ligera
FROM debian:bookworm-slim

# Actualiza sistema e instala dependencias
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    libmariadb-dev \
    pkg-config \
    gcc \
    mariadb-client \
    netcat-openbsd \
    cron && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Configurar zona horaria
ENV TZ=America/Mexico_City
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Directorio de trabajo
WORKDIR /app

# Copiar dependencias y crear entorno virtual
COPY ./requirements.txt /app/requirements.txt
RUN python3 -m venv /env && \
    /env/bin/pip install --upgrade pip && \
    /env/bin/pip install -r /app/requirements.txt

# Copiar el resto del código
COPY . /app

# Asegurar que el script de cron es ejecutable
RUN if [ -f /app/scripts/cron_start.sh ]; then chmod +x /app/scripts/cron_start.sh; fi

# Puerto de escucha
EXPOSE 80

# Comando de inicio (Django)
CMD ["/env/bin/python", "manage.py", "runserver", "0:80"]
