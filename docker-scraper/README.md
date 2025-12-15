# Docker Scraper - Pipeline Completo Steam + IA

Pipeline dockerizado: Scraping Steam → Resúmenes IA → Vectorización → SCP automático.

## 🚀 Setup

```bash
cd /home/g6/reto/docker-scraper
docker compose build
docker compose up -d
```

✅ Ofelia + Scraper listos | ⏰ Ejecuta a las **03:00 AM** diarias

## 📊 Verificación

```bash
docker logs ofelia-scraper-scheduler  # Debe decir "New job registered"
```

## ▶️ Test manual

```bash
docker exec ofelia-scraper-scheduler ofelia-cli run scraper-daily
```

## 📁 Datos

- **Local**: `volumes/scraper/data/steam-games-data-vect.ndjson`
- **Remoto**: `192.199.1.65:/home/g6/reto/datos/` (SCP automático)

## ⚙️ Configuración

### Cambiar hora (editar docker-compose.yml)
```yaml
ofelia.job-exec.scraper-daily.schedule: "0 3 * * *"
```
Ejemplos: `0 2 * * *` (2 AM), `0 3 * * 1` (Lunes 3 AM)

### Windows/Mac (editar .env)
```env
SSH_PATH=${USERPROFILE}/.ssh  # Windows
# SSH_PATH=/Users/usuario/.ssh  # Mac
```

# Para la validación (testing rápido)

Durante la validación, el pipeline tarda mucho (3-4 horas). Para testear rápido con pocos juegos:

**Edita `scraper/scripts/sacar-datos-games.py`, busca:**
```python
CANTIDAD_A_PROCESAR = 0  # 0 = procesa todos
```

**Cambia a un número pequeño para testing:**
```python
CANTIDAD_A_PROCESAR = 50  # Solo procesa los primeros 50 juegos (~10 minutos)
# O: CANTIDAD_A_PROCESAR = 100  # (~20 minutos)
```

**Luego actualiza el código en Docker:**
```bash
cp -r ../scraper ./scraper
rm -rf ./scraper/{data,logs,backups,.vscode,__pycache__}
docker compose build
docker compose up -d
```

**⚠️ IMPORTANTE**: Cuando termines de validar, **cambia de nuevo a `0`** en el script original antes de hacer commit:
```python
CANTIDAD_A_PROCESAR = 0  # Volver a producción
```

### Ejecutar inmediatamente al levantar (editar Dockerfile)

**Si quieres ejecutar inmediatamente** (útil cuando descargas el proyecto en una máquina nueva):

1. Abre `Dockerfile` y cambia la última línea:

```dockerfile
# Actual (espera hasta las 3 AM):
CMD ["tail", "-f", "/dev/null"]

# Cambiar a (ejecuta ahora + espera siguientes ejecuciones):
CMD ["/bin/bash", "-c", "/app/entrypoint.sh && tail -f /dev/null"]
```

2. Reconstruye y levanta:
```bash
docker compose build
docker compose up -d
```

Ahora el contenedor:
- ✅ Ejecuta `/app/entrypoint.sh` inmediatamente (flujo completo)
- ✅ Al terminar, queda esperando las 3 AM para la siguiente ejecución automática

**⚠️ Nota**: Si haces `docker compose restart`, volverá a ejecutar el flujo completo.


### Actualizar código
```bash
cp -r ../scraper ./scraper && rm -rf ./scraper/{data,logs,backups,.vscode,__pycache__}
cp -r ../imp-futuras ./imp-futuras && rm -rf ./imp-futuras/{data,backup,__pycache__}
docker compose build
docker compose up -d
```

## 🛑 Limpieza

```bash
docker compose down
docker rmi steam-scraper-complete:latest
rm -rf volumes/
```

## 📊 Flujo del Pipeline

1. Scraping Steam (`run_pipeline.py`)
2. Filtrado (`filter-games.py`)
3. Resúmenes IA (`flux.sh` en imp-futuras)
4. Integración (`desc-changer.py`)
5. Limpieza tags (`clean-tags.py`)
6. Vectorización (`vectorizador.py`)
7. SCP remoto (automático)
