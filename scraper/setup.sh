#!/bin/bash

echo "=========================================="
echo "   Instalador de dependencias - Steam Scraper"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SCRAPER_DIR="${ROOT_DIR}/scraper"

cd "$SCRAPER_DIR"

# Función para registrar fallo y salir
log_fail() {
    mkdir -p logs
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${ts} - FAIL - $1" >> logs/setup_fail.log
    echo "[ERROR] $1"
    exit 1
}

# 1. Verificar que Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 no está instalado."
    echo "[INFO] Instala Python3 antes de ejecutar este script:"
    echo ""
    echo "Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-venv python3-pip"
    echo "Fedora/RHEL: sudo dnf install python3 python3-pip"
    echo "macOS: brew install python3"
    echo ""
    log_fail "Python3 no encontrado en el sistema"
fi

echo "[INFO] Python encontrado: $(python3 --version)"
echo ""

# 2. Verificar que venv está disponible
echo "[*] Verificando módulo venv..."
if ! python3 -m venv --help &> /dev/null; then
    echo "[WARN] El módulo venv no está instalado"
    echo "[*] Instalando python3-venv..."
    
    # Detectar el sistema operativo e instalar
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y python3-venv
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y python3-virtualenv
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-virtualenv
        else
            echo "[ERROR] No se pudo detectar el gestor de paquetes"
            echo "[INFO] Instala python3-venv manualmente para tu distribución"
            log_fail "No se pudo instalar/el detectar soporte para venv"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - venv viene incluido con Python3 normalmente
        python3 -m pip install --upgrade pip
        python3 -m pip install virtualenv
    fi
    echo "[OK] Módulo instalado"
else
    echo "[OK] Módulo venv disponible"
fi
echo ""

# 3. Usar entorno virtual global unificado
VENV_GLOBAL="${HOME}/.venv"

if [ ! -d "$VENV_GLOBAL" ]; then
    echo "[*] Creando entorno virtual global en $VENV_GLOBAL..."
    python3 -m venv "$VENV_GLOBAL" || log_fail "Fallo creando entorno virtual global"
    echo "[OK] Entorno virtual global creado"
else
    echo "[INFO] Entorno virtual global ya existe en $VENV_GLOBAL"
fi

echo ""


# 4. Activar entorno virtual global
echo "[*] Activando entorno virtual global..."
source "$VENV_GLOBAL/bin/activate" || log_fail "No se pudo activar el entorno virtual global"

echo ""


# 5. Instalar dependencias base
echo "[*] Instalando dependencias desde requirements.txt..."
pip install --upgrade pip || log_fail "Fallo actualizando pip"
pip install -r requirements.txt || log_fail "Fallo instalando requirements"

echo ""


# 6. Verificar librerías de embeddings (ya instaladas con requirements.txt)
echo "[*] Verificando torch y sentence-transformers..."
if python -c "import torch, sentence_transformers" 2>/dev/null; then
    echo "[OK] Librerías de embeddings disponibles."
else
    log_fail "Torch o sentence-transformers no disponibles tras instalar requirements"
fi

echo ""


# 7. Descargar modelo de embeddings (con verificación de caché)
if [ -f "scripts/instalar_modelo.py" ]; then
    echo "[*] Verificando/descargando modelo de embeddings..."
    python scripts/instalar_modelo.py
    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "[OK] Modelo de embeddings descargado."
    elif [ $exit_code -eq 1 ]; then
        echo "[INFO] Modelo ya estaba en caché."
    else
        log_fail "Fallo descargando modelo de embeddings"
    fi
else
    echo "[INFO] No se encontró 'scripts/instalar_modelo.py'. Saltando descarga del modelo."
fi

echo ""
echo "=========================================="
echo "[OK] Instalación completada"
echo "=========================================="
echo ""



# 8. Crear carpetas necesarias
echo "[*] Verificando carpetas necesarias..."
mkdir -p data logs
echo "[OK] Carpetas verificadas"
echo ""



# 9. Ejecutar scraping de Steam API
echo "[*] Ejecutando run_pipeline.py..."
echo ""
python scripts/run_pipeline.py || log_fail "Fallo ejecutando run_pipeline.py"


# 9.5. Filtrar juegos (DLC, soundtracks, contenido adulto)
echo ""
echo "[*] Ejecutando filter-games.py para filtrar juegos irrelevantes..."
echo ""
python scripts/filter-games.py || log_fail "Fallo ejecutando filter-games.py"


# 10. Ejecutar pipeline de extracción y resumen IA
echo ""
echo "[*] Ejecutando pipeline de extracción y resumen (flux.sh)..."
echo ""
bash "${ROOT_DIR}/imp-futuras/flux.sh" || log_fail "Fallo ejecutando flux.sh"


# 11. Reemplazar descripciones con resúmenes IA
echo ""
echo "[*] Ejecutando desc-changer.py para reemplazar descripciones..."
echo ""
python "${SCRAPER_DIR}/scripts/desc-changer.py" || log_fail "Fallo ejecutando desc-changer.py"


# 12. Limpiar categorías irrelevantes (Steam metadata)
echo ""
echo "[*] Ejecutando clean-tags.py para limpiar categorías irrelevantes..."
echo ""
python scripts/clean-tags.py || log_fail "Fallo ejecutando clean-tags.py"


# 13. Generar embeddings semánticos (768 dims)
echo ""
echo "[*] Ejecutando vectorizador.py..."
echo ""
python scripts/vectorizador.py || log_fail "Fallo ejecutando vectorizador.py"
echo ""


# 14. Sincronizar datos vectorizados a máquina remota
ARCHIVO_VECT="${SCRAPER_DIR}/data/steam-games-data-vect.ndjson"
LOG_METRICS="${SCRAPER_DIR}/logs/scraper_metrics.log"
MAQUINA_REMOTA="192.199.1.65"
RUTA_REMOTA="/home/g6/reto/datos"

if [ -f "$ARCHIVO_VECT" ]; then
    echo "[*] Copiando datos vectorizados a $MAQUINA_REMOTA:$RUTA_REMOTA ..."
    scp "$ARCHIVO_VECT" "$MAQUINA_REMOTA:$RUTA_REMOTA/" || log_fail "Fallo copiando archivo a máquina remota"
    echo "[OK] Datos sincronizados en $MAQUINA_REMOTA:$RUTA_REMOTA/steam-games-data-vect.ndjson"
else
    echo "[WARN] No se encontró el archivo vectorizado. Saltando sincronización."
fi

# 15. Sincronizar logs a máquina remota
if [ -f "$LOG_METRICS" ]; then
    echo "[*] Copiando log de métricas a $MAQUINA_REMOTA:$RUTA_REMOTA ..."
    scp "$LOG_METRICS" "$MAQUINA_REMOTA:$RUTA_REMOTA/" || log_fail "Fallo copiando log a máquina remota"
    echo "[OK] Log sincronizado en $MAQUINA_REMOTA:$RUTA_REMOTA/scraper_metrics.log"
else
    echo "[WARN] No se encontró el log de métricas. Saltando sincronización."
fi

echo ""
echo "=========================================="
echo "[OK] Pipeline completo finalizado"
echo "=========================================="

