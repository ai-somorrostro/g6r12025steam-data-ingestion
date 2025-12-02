#!/bin/bash

echo "=========================================="
echo "   Instalador de dependencias - Steam Scraper"
echo "=========================================="
echo ""

# Función para registrar fallo y salir
log_fail() {
    mkdir -p logs
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${ts} - FAIL - $1" >> logs/setup_fail.log
    echo "[ERROR] $1"
    exit 1
}

# Verificar que Python está instalado
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

# Verificar que venv está disponible
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

# Crear entorno virtual si no existe
if [ ! -d ".venv" ]; then
    echo "[*] Creando entorno virtual..."
    python3 -m venv .venv || log_fail "Fallo creando entorno virtual (.venv)"
    echo "[OK] Entorno virtual creado"
else
    echo "[INFO] Entorno virtual ya existe"
fi

echo ""

# Activar entorno virtual
echo "[*] Activando entorno virtual..."
source .venv/bin/activate || log_fail "No se pudo activar el entorno virtual"

echo ""

# Instalar dependencias
echo "[*] Instalando dependencias desde requirements.txt..."
pip install --upgrade pip || log_fail "Fallo actualizando pip"
pip install -r requirements.txt || log_fail "Fallo instalando requirements"

echo ""
# Instalar librería de embeddings (torch CPU-only) desde script dedicado
if [ -f "sh_test/instalar_lib_embeddings.sh" ]; then
    echo "[*] Instalando librería de embeddings (torch CPU)"
    bash sh_test/instalar_lib_embeddings.sh || log_fail "Fallo instalando librería de embeddings (torch CPU)"
    echo "[OK] Librería de embeddings instalada."
else
    echo "[INFO] No se encontró 'sh_test/instalar_lib_embeddings.sh'. Saltando instalación de embeddings."
fi

echo ""
# Descargar modelo de embeddings (con verificación de caché)
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

# Crear carpetas necesarias
echo "[*] Verificando carpetas necesarias..."
mkdir -p data logs
echo "[OK] Carpetas verificadas"
echo ""

# Ejecutar el script principal
echo "[*] Ejecutando run_pipeline.py..."
echo ""
python scripts/run_pipeline.py || log_fail "Fallo ejecutando run_pipeline.py"

echo ""
echo "[*] Ejecutando vectorizador.py..."
echo ""
python scripts/vectorizador.py || log_fail "Fallo ejecutando vectorizador.py"

echo ""
# Sincronizar datos vectorizados a máquina remota
ARCHIVO_VECT="data/steam-games-data-vect.ndjson"
LOG_METRICS="logs/scraper_metrics.log"
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
echo "[OK] Pipeline completo finalizado"
echo "=========================================="

