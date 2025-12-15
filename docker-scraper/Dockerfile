FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements de ambos proyectos
COPY scraper/requirements.txt /app/scraper-requirements.txt
COPY imp-futuras/requirements.txt /app/imp-futuras-requirements.txt

# Instalar todas las dependencias Python
RUN pip install --no-cache-dir -r /app/scraper-requirements.txt && \
    pip install --no-cache-dir -r /app/imp-futuras-requirements.txt

# Copiar código del scraper
COPY scraper/scripts/ /app/scraper/scripts/
COPY scraper/sh_test/ /app/scraper/sh_test/
COPY scraper/setup.sh /app/scraper/

# Copiar código de imp-futuras
COPY imp-futuras/scripts/ /app/imp-futuras/scripts/
COPY imp-futuras/flux.sh /app/imp-futuras/
COPY imp-futuras/.env /app/imp-futuras/.env

# Crear directorios necesarios
RUN mkdir -p /app/scraper/data /app/scraper/logs /app/scraper/backups && \
    mkdir -p /app/imp-futuras/data /app/imp-futuras/backup

# Copiar script de entrada
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh /app/imp-futuras/flux.sh

# Comando por defecto: mantener contenedor vivo para job-exec
CMD ["tail", "-f", "/dev/null"]
