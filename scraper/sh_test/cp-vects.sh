#!/bin/bash

echo "=========================================="
echo "   Sincronización de datos a máquina 2"
echo "=========================================="
echo ""

ARCHIVO_VECT="/home/g6/reto/scraper/data/steam-games-data-vect.ndjson"
LOG_METRICS="/home/g6/reto/scraper/logs/scraper_metrics.log"
MAQUINA_REMOTA="192.199.1.65"
RUTA_REMOTA="/home/g6/reto/datos"

if [ -f "$ARCHIVO_VECT" ]; then
    echo "[*] Copiando datos vectorizados a $MAQUINA_REMOTA:$RUTA_REMOTA ..."
    scp "$ARCHIVO_VECT" "$MAQUINA_REMOTA:$RUTA_REMOTA/" || log_fail "Fallo copiando archivo a máquina remota"
    echo "[OK] Datos sincronizados en $MAQUINA_REMOTA:$RUTA_REMOTA/steam-games-data-vect.ndjson"
else
    echo "[WARN] No se encontró el archivo vectorizado. Saltando sincronización."
fi

if [ -f "$LOG_METRICS" ]; then
    echo "[*] Copiando log de métricas a $MAQUINA_REMOTA:$RUTA_REMOTA ..."
    scp "$LOG_METRICS" "$MAQUINA_REMOTA:$RUTA_REMOTA/" || log_fail "Fallo copiando log a máquina remota"
    echo "[OK] Log sincronizado en $MAQUINA_REMOTA:$RUTA_REMOTA/scraper_metrics.log"
else
    echo "[WARN] No se encontró el log de métricas. Saltando sincronización."
fi

echo ""
echo "=========================================="
echo "[OK] Sincronización completada"
echo "=========================================="
