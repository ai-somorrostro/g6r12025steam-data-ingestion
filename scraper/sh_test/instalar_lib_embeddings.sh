#!/bin/bash

echo "=========================================="
echo "   Instalador de librería de embeddings"
echo "=========================================="
echo ""

# Definir directorio del proyecto
PROJECT_ROOT="/home/g6/reto/scraper"

# Verificar que el directorio del proyecto existe
if [ ! -d "$PROJECT_ROOT" ]; then
    echo "[ERROR] No se encuentra el directorio del proyecto: $PROJECT_ROOT"
    exit 1
fi

# Cambiar al directorio del proyecto
cd "$PROJECT_ROOT" || exit 1

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    echo "[*] Activando entorno virtual..."
    source .venv/bin/activate
else
    echo "[ERROR] No existe el entorno virtual .venv"
    echo "[INFO] Ejecuta primero: ./setup.sh"
    exit 1
fi

echo ""

# Verificar e instalar librerías requeridas (PyTorch CPU-only + sentence-transformers)
echo "[*] Verificando librería 'torch' (CPU)..."
if ! python -c "import torch" &> /dev/null; then
    echo "[*] Instalando torch (CPU-only) sin usar caché..."
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
    if [ $? -ne 0 ]; then
        echo "[ERROR] Falló la instalación de torch (CPU)."
        exit 1
    fi
    echo "[OK] 'torch' (CPU) instalado."
else
    echo "[OK] 'torch' ya está instalado en el entorno."
fi

echo ""
echo "[*] Verificando librería 'sentence-transformers'..."
if ! python -c "import sentence_transformers" &> /dev/null; then
    echo "[*] Instalando sentence-transformers sin usar caché..."
    pip install --no-cache-dir sentence-transformers
    if [ $? -ne 0 ]; then
        echo "[ERROR] Falló la instalación de sentence-transformers."
        exit 1
    fi
    echo "[OK] 'sentence-transformers' instalado."
else
    echo "[OK] 'sentence-transformers' ya está instalado en el entorno."
fi

echo ""
echo "=========================================="
echo "[OK] Proceso completado: librerías instaladas"
echo "=========================================="
