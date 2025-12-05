#!/bin/bash

# Script para limpiar caracteres de escape del archivo summary.ndjson

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$(dirname "$SCRIPT_DIR")/data"
SUMMARY_FILE="$DATA_DIR/summary.ndjson"

echo "[*] Limpiando caracteres de escape en summary.ndjson..."

if [ ! -f "$SUMMARY_FILE" ]; then
    echo "[ERROR] No se encuentra el archivo: $SUMMARY_FILE"
    exit 1
fi

python3 << EOF
import json

# Leer el archivo y corregir los escapes
lineas_corregidas = []
with open('$SUMMARY_FILE', 'r', encoding='utf-8') as f:
    for linea in f:
        try:
            # Cargar el JSON (esto maneja los escapes correctamente)
            obj = json.loads(linea)
            # Reescribirlo sin escapes innecesarios
            lineas_corregidas.append(json.dumps(obj, ensure_ascii=False))
        except:
            pass

# Escribir de vuelta
with open('$SUMMARY_FILE', 'w', encoding='utf-8') as f:
    for linea in lineas_corregidas:
        f.write(linea + '\n')

print(f"[OK] {len(lineas_corregidas)} líneas procesadas y limpiadas")
EOF

echo "[DONE] Limpieza completada."
