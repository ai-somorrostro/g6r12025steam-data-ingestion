#!/bin/bash

# Script para ejecutar la pipeline completa de extracción y resumen de datos

set -e  # Salir si algún comando falla

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"

echo "=========================================="
echo "INICIANDO PIPELINE DE DATOS"
echo "=========================================="
echo ""

# Verificar/crear entorno virtual
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creando entorno virtual..."
    python3 -m venv "$VENV_DIR"
    echo "[OK] Entorno virtual creado"
fi

# Activar el entorno virtual
echo "[INFO] Activando entorno virtual..."
source "$VENV_DIR/bin/activate"

# Instalar/actualizar dependencias
if [ -f "$REQUIREMENTS" ]; then
    echo "[INFO] Instalando/actualizando dependencias..."
    pip install --upgrade pip -q
    pip install -r "$REQUIREMENTS" -q
    echo "[OK] Dependencias instaladas"
else
    echo "[WARN] No se encuentra requirements.txt, instalando paquetes básicos..."
    pip install --upgrade pip -q
    pip install requests openai python-dotenv -q
    echo "[OK] Paquetes básicos instalados"
fi

echo ""

# 1. Ejecutar extract-desc-reverse.py (extracción de nuevas entradas)
echo "[1/3] Ejecutando extracción de descripciones (nuevas entradas)..."
echo "=========================================="
python "$SCRIPT_DIR/scripts/extract-desc-nuevas.py"
echo ""
if [ $? -eq 0 ]; then
    echo "[OK] Extracción completada exitosamente"
else
    echo "[ERROR] Fallo en la extracción de descripciones"
    exit 1
fi
echo ""

# 2. Ejecutar openrouter-call.py (generación de resúmenes IA)
echo "[2/3] Ejecutando generación de resúmenes IA..."
echo "=========================================="
python "$SCRIPT_DIR/scripts/openrouter-call.py"
echo ""
if [ $? -eq 0 ]; then
    echo "[OK] Generación de resúmenes completada exitosamente"
else
    echo "[ERROR] Fallo en la generación de resúmenes"
    exit 1
fi
echo ""

# 3. Ejecutar clean-summary.sh (limpieza de caracteres de escape)
echo "[3/3] Ejecutando limpieza de caracteres de escape..."
echo "=========================================="
bash "$SCRIPT_DIR/scripts/clean-summary.sh"
echo ""
if [ $? -eq 0 ]; then
    echo "[OK] Limpieza completada exitosamente"
else
    echo "[ERROR] Fallo en la limpieza"
    exit 1
fi
echo ""

echo "=========================================="
echo "PIPELINE COMPLETADA EXITOSAMENTE"
echo "=========================================="
echo ""
echo "Resumen final:"
echo "  - Descripciones extraídas: raw-desc.ndjson"
echo "  - Resúmenes generados: summary.ndjson"
echo "  - Archivos limpios: summary.ndjson (sin escapes)"
echo ""
