# Steam Scraper + Vectorización

Pipeline completo de scraping de juegos de Steam con generación automática de embeddings semánticos y sincronización remota para análisis RAG (Retrieval-Augmented Generation).

## 🎯 ¿Qué hace este proyecto?

1. **Scraping inteligente**: Descarga datos de ~10,000 juegos de Steam (trending + clásicos populares)
2. **Filtrado automático**: Elimina DLC, soundtracks y contenido adulto (filter-games.py)
3. **Extracción de descripciones**: Obtiene descripciones detalladas de la Steam API (imp-futuras)
4. **Resúmenes IA**: Genera resúmenes con OpenRouter GPT-4o-mini (imp-futuras)
5. **Reemplazo inteligente**: Integra descripciones resumidas en los datos principales (desc-changer.py)
6. **Vectorización semántica**: Genera embeddings de 768 dimensiones con modelos multilingües para búsqueda por similitud
7. **Pipeline automatizado**: Orquesta todas las fases → limpieza → vectorización → sincronización remota
8. **Sincronización SSH**: Copia automática de datos vectorizados y logs a servidor remoto para ingestión en Elasticsearch/Logstash

## 📁 Estructura del Proyecto

```
scraper/
├── scripts/                       # Scripts del pipeline
│   ├── run_pipeline.py            # Orquestador principal (scraping → limpieza)
│   ├── gameid-script.py           # Fase 1: Descarga IDs de juegos populares
│   ├── sacar-datos-games.py       # Fase 2: Obtiene detalles completos + limpieza HTML
│   ├── filter-games.py            # Fase 2.5: Filtra DLC, soundtracks y contenido adulto
│   ├── desc-changer.py            # Fase 3.5: Reemplaza descripciones con resúmenes IA
│   ├── vectorizador.py            # Fase 4: Genera embeddings (768 dims)
│   ├── vectorizador2.py           # Alternativa: modelo multilingüe paraphrase-multilingual
│   └── instalar_modelo.py         # Descargador de modelos SentenceTransformers
├── sh_test/                       # Scripts auxiliares de setup
│   ├── instalar_lib_embeddings.sh # Instala PyTorch CPU + sentence-transformers
│   └── cp-vects.sh                # Sincronización manual a servidor remoto
├── data/                          # Datos generados (ignorados por git)
│   ├── steam-top-games.json       # IDs de juegos filtrados (5,001+)
│   ├── steam-games-data.ndjson    # Datos completos con descripciones resumidas
│   └── steam-games-data-vect.ndjson # Datos + embeddings 768-dim (listo para RAG)
├── logs/                          # Logs del pipeline (ignorados por git)
│   ├── scraper_metrics.log        # Logs de gameid-script.py
│   ├── scraper_full_data_metrics.log # Logs de sacar-datos-games.py
│   └── setup_fail.log             # Registro de fallos del instalador
├── .venv/                         # Entorno virtual Python
├── setup.sh                       # Instalador completo Linux/Mac (ejecuta pipeline)
├── requirements.txt               # Dependencias base (requests, beautifulsoup4, etc.)
├── .gitignore                     # Ignora data/, logs/, .venv/, caches
└── README.md                      # Este archivo
```

## 🚀 Instalación Rápida

### Linux/Mac (Setup completo)
```bash
cd /home/g6/reto/scraper
chmod +x setup.sh
./setup.sh
```

**El script `setup.sh` ejecuta automáticamente:**
1. ✅ Verificación de Python3 y venv
2. ✅ Creación de `.venv/` y activación
3. ✅ Instalación de dependencias (`requirements.txt`)
4. ✅ Instalación de PyTorch CPU + sentence-transformers
5. ✅ Descarga del modelo de embeddings (paraphrase-multilingual-mpnet-base-v2)
6. ✅ Scraping de Steam (run_pipeline.py)
7. ✅ Filtrado de DLC/soundtracks (filter-games.py)
8. ✅ Extracción de descripciones + resúmenes IA (carpeta imp-futuras)
9. ✅ Reemplazo de descripciones (desc-changer.py)
10. ✅ Vectorización semántica (vectorizador.py)
11. ✅ Sincronización SSH a servidor remoto (`192.199.1.65:/home/g6/reto/datos/`)

### Instalación manual (paso a paso)

Si prefieres instalar manualmente:

```bash
# 1. Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependencias base
pip install -r requirements.txt

# 3. Instalar librerías de embeddings (PyTorch CPU + SentenceTransformers)
bash sh_test/instalar_lib_embeddings.sh

# 4. Descargar modelo de embeddings
python scripts/instalar_modelo.py
```

## ▶️ Ejecución del Pipeline

### Ejecución completa (recomendado)
```bash
source .venv/bin/activate
python scripts/run_pipeline.py  # Scraping + limpieza
python scripts/vectorizador.py  # Generación de embeddings
bash sh_test/cp-vects.sh        # Sincronización remota (opcional)
```

### Ejecución individual de scripts

**Fase 1: Obtener IDs de juegos**
```bash
python scripts/gameid-script.py
# Salida: data/steam-top-games.json (~10k IDs)
```

**Fase 2: Descargar datos completos**
```bash
python scripts/sacar-datos-games.py
# Entrada: data/steam-top-games.json
# Salida: data/steam-games-data.ndjson (título, descripción, géneros, precio, etc.)
```

**Fase 2.5: Filtrar DLC, soundtracks y contenido adulto**
```bash
python scripts/filter-games.py
# Entrada: data/steam-top-games.json
# Salida: data/steam-top-games.json (filtrada, ~5,001 juegos)
```

**Fase 3: Extracción de descripciones y generación de resúmenes IA**
```bash
# Ejecutado desde la carpeta imp-futuras (scripts de extracción + OpenRouter)
```

**Fase 3.5: Reemplazar descripciones con resúmenes IA**
```bash
python scripts/desc-changer.py
# Entrada: data/steam-games-data.ndjson + resúmenes IA de imp-futuras
# Salida: data/steam-games-data.ndjson (actualizado con resúmenes)
```

**Fase 4: Generar embeddings**
```bash
python scripts/vectorizador.py
# Entrada: data/steam-games-data.ndjson
# Salida: data/steam-games-data-vect.ndjson (+ campo vector_embedding: float[768])
```

## 📊 Formato de Salida (NDJSON)

Cada juego en `steam-games-data-vect.ndjson` es una línea JSON con:

```json
{
  "appid": 730,
  "name": "Counter-Strike 2",
  "short_description": "For over two decades...",
  "detailed_description": "Counter-Strike 2 es un videojuego de disparos competitivo...",
  "genres": ["Action", "FPS"],
  "categories": ["Multi-player", "Online PvP"],
  "developers": ["Valve"],
  "price_eur": "0.00",
  "vector_embedding": [0.0234, -0.1234, ..., 0.0567]  // 768 floats
}
```

**Campo clave:** `vector_embedding` → Vector de 768 dimensiones para búsqueda semántica en Elasticsearch con modelo dense_vector.

**Nota:** `detailed_description` ahora contiene un resumen IA generado con OpenRouter GPT-4o-mini (más conciso que la descripción original).

## 🔧 Configuración

### Ajustar cantidad de juegos
- `scripts/gameid-script.py` → `CANTIDAD_POR_CRITERIO = 5000` (IDs por criterio)
- `scripts/sacar-datos-games.py` → `CANTIDAD_A_PROCESAR = 25` (0 = todos)

### Palabras clave para filtrado
Edita `scripts/filter-games.py` para cambiar qué se filtra (DLC, soundtracks, etc.)

### Configurar resúmenes IA
Configura la API key de OpenRouter en `/home/g6/reto/imp-futuras/.env` para activar generación automática de resúmenes

### Cambiar modelo de embeddings
Edita `scripts/instalar_modelo.py` y `scripts/vectorizador.py`:
```python
# Opciones:
# - 'all-mpnet-base-v2' (inglés, 768 dims)
# - 'paraphrase-multilingual-mpnet-base-v2' (multilingüe, 768 dims)
# - 'all-MiniLM-L6-v2' (inglés, 384 dims, más rápido)
MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2'
```

### Configurar sincronización remota
Edita `setup.sh` o `sh_test/cp-vects.sh`:
```bash
MAQUINA_REMOTA="192.199.1.65"
RUTA_REMOTA="/home/g6/reto/datos"
```

## 🤖 Automatización con Crontab

Ejecutar pipeline diario a las 2:00 AM:
```bash
crontab -e
```

Añade:
```cron
0 2 * * * cd /home/g6/reto/scraper && /home/g6/reto/scraper/.venv/bin/python scripts/run_pipeline.py >> /home/g6/reto/scraper/logs/cron.log 2>&1 && /home/g6/reto/scraper/.venv/bin/python scripts/vectorizador.py >> /home/g6/reto/scraper/logs/cron.log 2>&1
```

O ejecuta el setup completo (verifica instalaciones + ejecuta pipeline):
```cron
0 2 * * * cd /home/g6/reto/scraper && bash setup.sh >> /home/g6/reto/scraper/logs/cron.log 2>&1
```

## 📝 Logs y Debugging

- `logs/scraper_metrics.log` → Peticiones HTTP, latencias, errores de conexión (Fase 1)
- `logs/scraper_full_data_metrics.log` → Peticiones HTTP, parseos exitosos (Fase 2)
- `logs/setup_fail.log` → Fallos del instalador (setup.sh)
- Logs en consola: `tail -f logs/scraper_metrics.log`

## 🔒 Seguridad y Requisitos

- **SSH sin contraseña** requerido para sincronización remota (usa `ssh-copy-id 192.199.1.65`)
- **Espacio en disco**: ~4-5 GB (modelo + datos + cache pip/huggingface)
- **Python 3.8+** requerido
- **Librerías CPU-only**: PyTorch sin CUDA para ahorrar espacio (~2 GB menos que versión GPU)

## 🛠️ Tecnologías

- **Scraping**: `requests` + `BeautifulSoup4`
- **Embeddings**: `sentence-transformers` (HuggingFace)
- **Modelo**: `paraphrase-multilingual-mpnet-base-v2` (278M parámetros, 768 dims)
- **Backend ML**: PyTorch (CPU-only)
- **Resúmenes IA**: OpenRouter (GPT-4o-mini) con parallelización
- **Formato de datos**: NDJSON (compatible con Filebeat/Logstash/Elasticsearch)
