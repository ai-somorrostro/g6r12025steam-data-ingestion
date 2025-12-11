#!/bin/bash
set -e

echo "=========================================="
echo "    Steam Scraper + IA Pipeline"
echo "=========================================="
echo "Inicio: $(date)"
echo ""

cd /app/scraper

# =======================
# FASE 1: SCRAPING DE STEAM API
# =======================
echo "[*] FASE 1: Ejecutando scraping de Steam API..."
echo ""
python scripts/run_pipeline.py || { echo "[ERROR] Fallo ejecutando run_pipeline.py"; exit 1; }
echo ""

# =======================
# FASE 2: FILTRADO DE JUEGOS
# =======================
echo "[*] FASE 2: Filtrando DLC, soundtracks y contenido adulto..."
echo ""
python scripts/filter-games.py || { echo "[ERROR] Fallo ejecutando filter-games.py"; exit 1; }
echo ""

# =======================
# FASE 3: RESÚMENES IA (flux.sh)
# =======================
echo "[*] FASE 3: Ejecutando pipeline de extracción y resumen IA..."
echo ""
cd /app/imp-futuras

if [ ! -f .env ]; then
    echo "[WARN] .env no encontrado en imp-futuras. Saltando generación de resúmenes IA."
else
    echo "Extrayendo descripciones nuevas..."
    python scripts/extract-desc-nuevas.py || { echo "[ERROR] Fallo en extract-desc-nuevas.py"; exit 1; }
    
    echo "Generando resúmenes con IA..."
    python scripts/openrouter-call.py || { echo "[ERROR] Fallo en openrouter-call.py"; exit 1; }
    
    echo "Limpiando JSON..."
    bash scripts/clean-summary.sh || { echo "[ERROR] Fallo en clean-summary.sh"; exit 1; }
    
    echo "[OK] Resúmenes IA generados"
fi

echo ""

# =======================
# FASE 4: INTEGRACIÓN DE RESÚMENES
# =======================
echo "[*] FASE 4: Reemplazando descripciones con resúmenes IA..."
echo ""
cd /app/scraper
python scripts/desc-changer.py || { echo "[ERROR] Fallo ejecutando desc-changer.py"; exit 1; }
echo ""

# =======================
# FASE 5: LIMPIEZA DE TAGS
# =======================
echo "[*] FASE 5: Limpiando categorías irrelevantes..."
echo ""
python scripts/clean-tags.py || { echo "[ERROR] Fallo ejecutando clean-tags.py"; exit 1; }
echo ""

# =======================
# FASE 6: VECTORIZACIÓN
# =======================
echo "[*] FASE 6: Generando embeddings semánticos (768 dims)..."
echo ""
python scripts/vectorizador.py || { echo "[ERROR] Fallo ejecutando vectorizador.py"; exit 1; }
echo ""

# =======================
# FASE 7: SINCRONIZACIÓN REMOTA (SCP)
# =======================
echo "[*] FASE 7: Sincronizando datos a máquina remota..."
echo ""

ARCHIVO_VECT="/app/scraper/data/steam-games-data-vect.ndjson"
LOG_METRICS="/app/scraper/logs/scraper_metrics.log"
MAQUINA_REMOTA="192.199.1.65"
RUTA_REMOTA="/home/g6/reto/datos"

# Añadir servidor a known_hosts (evitar prompt SSH)
mkdir -p /root/.ssh
ssh-keyscan -H "$MAQUINA_REMOTA" >> /root/.ssh/known_hosts 2>/dev/null || true

if [ -f "$ARCHIVO_VECT" ]; then
    echo "Copiando datos vectorizados a $MAQUINA_REMOTA:$RUTA_REMOTA ..."
    scp "$ARCHIVO_VECT" "$MAQUINA_REMOTA:$RUTA_REMOTA/" || { echo "[ERROR] Fallo copiando archivo vectorizado"; exit 1; }
    echo "[OK] Datos sincronizados: steam-games-data-vect.ndjson"
else
    echo "[WARN] No se encontró el archivo vectorizado. Saltando sincronización."
fi

if [ -f "$LOG_METRICS" ]; then
    echo "Copiando log de métricas a $MAQUINA_REMOTA:$RUTA_REMOTA ..."
    scp "$LOG_METRICS" "$MAQUINA_REMOTA:$RUTA_REMOTA/" || { echo "[WARN] Fallo copiando log (continuando)"; }
    echo "[OK] Log sincronizado: scraper_metrics.log"
fi

echo ""
echo "=========================================="
echo "[OK] Pipeline completo finalizado"
echo "=========================================="
echo "Fin: $(date)"
echo ""
echo "Datos disponibles (local):"
echo "  - Vectorizados: /app/scraper/data/steam-games-data-vect.ndjson"
echo "  - Logs: /app/scraper/logs/"
echo "  - Resúmenes IA: /app/imp-futuras/data/summary.ndjson"
echo ""
echo "Datos sincronizados (remoto):"
echo "  - $MAQUINA_REMOTA:$RUTA_REMOTA/steam-games-data-vect.ndjson"
echo "  - $MAQUINA_REMOTA:$RUTA_REMOTA/scraper_metrics.log"
echo "=========================================="
