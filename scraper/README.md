# Steam Scraper + Vectorización

Pipeline completo de scraping de juegos de Steam con generación automática de embeddings semánticos y sincronización remota para análisis RAG (Retrieval-Augmented Generation).

## 🎯 ¿Qué hace este proyecto?

1. **Scraping inteligente**: Descarga datos de ~5,000 juegos de Steam (trending + clásicos populares)
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
│   ├── sacar-datos-games.py       # Fase 2: Obtiene detalles completos (identificador de IDs ya procesados) + limpieza HTML
│   ├── filter-games.py            # Fase 2.5: Filtra DLC, soundtracks y contenido adulto
│   ├── clean-tags.py              # Fase 3: Limpia categorías/tags irrelevantes
│   ├── desc-changer.py            # Fase 3.5: Reemplaza descripciones con resúmenes IA
│   ├── vectorizador.py            # Fase 4: Genera embeddings (768 dims)
│   └── instalar_modelo.py         # Descargador de modelos SentenceTransformers
├── sh_test/                       # Scripts auxiliares
│   └── cp-vects.sh                # Sincronización manual a servidor remoto
├── data/                          # Datos generados (ignorados por git)
│   ├── steam-top-games.json       # IDs de juegos filtrados (5,001+)
│   ├── steam-games-data.ndjson    # Datos completos con descripciones resumidas
│   └── steam-games-data-vect.ndjson # Datos + embeddings 768-dim (listo para RAG)
├── backups/                       # Copias de seguridad (ej. steam-top-games-*.json)
├── logs/                          # Logs del pipeline (ignorados por git)
│   ├── scraper_metrics.log        # Logs de gameid-script.py
│   ├── scraper_full_data_metrics.log # Logs de sacar-datos-games.py
│   └── setup_fail.log             # Registro de fallos del instalador
├── .vscode/                       # Configuración local del editor
├── setup.sh                       # Instalador completo Linux (ejecuta pipeline)
├── requirements.txt               # Dependencias (requests, beautifulsoup4, torch CPU, sentence-transformers, openai, etc.)
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
1. ✅ Verificación de Python3 disponible
2. ✅ **Uso del venv global unificado** (`/home/g6/.venv`) - compartido con imp-futuras
3. ✅ Instalación de dependencias desde `requirements.txt` (torch CPU, sentence-transformers, openai)
4. ✅ Verificación de PyTorch CPU + sentence-transformers mediante import check
5. ✅ Descarga del modelo de embeddings (paraphrase-multilingual-mpnet-base-v2, con verificación de caché en `~/.cache/huggingface/`)
6. ✅ **Sincronización de datos con Elasticsearch** (fase nueva)
7. ✅ Scraping de Steam (run_pipeline.py)
8. ✅ Filtrado de DLC/soundtracks (filter-games.py)
9. ✅ Limpieza de categorías Steam (clean-tags.py)
10. ✅ Extracción de descripciones + resúmenes IA (flux.sh en imp-futuras)
11. ✅ Reemplazo de descripciones (desc-changer.py)
12. ✅ Vectorización semántica (vectorizador.py)
13. ✅ **Sincronización incremental de datos** (cargar IDs existentes, eliminar obsoletos, reprocesar válidos)
14. ✅ Sincronización SSH a servidor remoto con validación de directorio (`192.199.1.65:/home/g6/reto/datos/`)

### Instalación manual (paso a paso)

Si prefieres instalar manualmente:

```bash
# 1. Usar entorno virtual global (crear si no existe)
python3 -m venv /home/g6/.venv
source /home/g6/.venv/bin/activate

# 2. Instalar dependencias (incluye torch CPU, sentence-transformers, openai)
cd /home/g6/reto/scraper
pip install -r requirements.txt

# 3. Verificar instalación de librerías críticas
python -c "import torch, sentence_transformers, openai; print('✅ OK')"

# 4. Descargar modelo de embeddings (si no está en caché)
python scripts/instalar_modelo.py
```

### Actualización de un entorno existente

Si ya tienes `/home/g6/.venv` pero necesitas actualizar dependencias:

```bash
source /home/g6/.venv/bin/activate
cd /home/g6/reto/scraper
pip install --upgrade -r requirements.txt
```

## ▶️ Ejecución del Pipeline

### Ejecución completa (recomendado)
```bash
source /home/g6/.venv/bin/activate
python scripts/run_pipeline.py  # Scraping + limpieza
terminal -> /home/g6/reto/imp-futuras/flux.sh # Ejecucion del flujo (Resumenes LLM)
python scripts/desc-changer.py  # Cambio de descripciones viejas a nuevas
python scripts/vectorizador.py  # Generación de embeddings
bash sh_test/cp-vects.sh        # Sincronización remota (opcional)
```

### Ejecución individual de scripts

**Fase 1: Obtener IDs de juegos**
```bash
python scripts/gameid-script.py
# Salida: data/steam-top-games.json (~5k IDs)
```

**Fase 2: Descargar datos completos**
```bash
python scripts/sacar-datos-games.py
# Entrada: data/steam-top-games.json
# Salida: data/steam-games-data.ndjson (título, descripción, géneros, precio, etc.)
# 
# Cambios recientes:
# - Sincronización incremental: Compara IDs con archivo NDJSON existente
# - Elimina juegos obsoletos (ya no en top games)
# - Reprocesa todos los válidos para actualizar precios/métricas
# - Log de cambios: "SINCRONIZACIÓN | Eliminados:X | A reprocesar:Y"
```

**Fase 2.5: Filtrar DLC, soundtracks y contenido adulto**
```bash
python scripts/filter-games.py
# Entrada: data/steam-top-games.json
# Salida: data/steam-top-games-filtered.json (+ backup en backups/)
```

**Fase 3: Extracción de descripciones y generación de resúmenes IA (flux.sh)**
```bash
cd /home/g6/reto/imp-futuras
bash flux.sh  # Usa el mismo venv global /home/g6/.venv
# Salida: resúmenes IA en imp-futuras/data que luego usa desc-changer.py
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

## 🧭 Orden del pipeline (setup.sh)

1) Verificación de Python + venv global `/home/g6/.venv`
2) Instalación/verificación de dependencias (torch CPU, sentence-transformers, openai)
3) Descarga/validación del modelo de embeddings (cache HF)
4) `run_pipeline.py` → gameid-script.py + sacar-datos-games.py (con sincronización incremental)
5) `filter-games.py` → filtra DLC/adulto y guarda `steam-top-games-filtered.json`
6) `imp-futuras/flux.sh` → genera resúmenes IA (OpenRouter)
7) `desc-changer.py` → inserta resúmenes IA en NDJSON principal
8) `clean-tags.py` → limpia categorías/tags irrelevantes
9) `vectorizador.py` → genera embeddings 768D
10) `scp` opcional → sincroniza NDJSON vectorizado + logs a 192.199.1.65

## 📊 Formato de Salida (NDJSON)

Cada juego en `steam-games-data-vect.ndjson` es una línea JSON con:

```json
{
  "appid": 730,
  "name": "Counter-Strike 2",
  "scraped_at": "2025-12-10 08:20:50",
  "price_eur": 0.00,
  "price_initial_eur": 0.0, 
  "discount_pct": 0,
  "metacritic_score": 0, // no tiene score
  "recommendations_total": 4810260,
  "achievements_count": 1, 
  "is_free": true,
  "genres": ["Action", "FPS"],
  "categories": ["FPS", "Disparos", "Multijugador", "Competitivos" ...], 
  "developers": ["Valve"], 
  "publishers": ["Valve"], 
  "achievements_list": ["Una nueva era"],
  "short_description": "For over two decades...",
  "detailed_description": "Counter-Strike 2 es un videojuego de disparos competitivo...",
  "vector_embedding": [0.0234, -0.1234, ..., 0.0567]  // 768 floats
}

```

**Campo clave:** `vector_embedding` → Vector de 768 dimensiones para búsqueda semántica en Elasticsearch con modelo dense_vector.

**Nota:** `detailed_description` ahora contiene un resumen IA generado con OpenRouter GPT-4o-mini (más conciso que la descripción original).

## 🔧 Configuración

### Entorno Virtual Global

El proyecto utiliza un **venv unificado** en `/home/g6/.venv` compartido entre `scraper` e `imp-futuras`:

```bash
# Activar siempre desde aquí
source /home/g6/.venv/bin/activate

# Localización de binarios Python
/home/g6/.venv/bin/python
/home/g6/.venv/bin/pip

# Caché de modelos HuggingFace
~/.cache/huggingface/hub/  # (descargado automáticamente)
```

**Ventajas:**
- ✅ Una única instalación de librerías pesadas (torch, transformers)
- ✅ Ahorra ~3-4 GB de espacio en disco
- ✅ Coherencia en versiones entre scraper e API
- ✅ Facilita mantenimiento centralizado

### Sincronización Incremental de Datos

El script `sacar-datos-games.py` implementa sincronización inteligente:

```python
# Fase automática en cada ejecución:
1. cargar_ids_desde_ndjson()
   - Lee IDs existentes en steam-games-data.ndjson
   - Retorna set de IDs para comparación

2. sincronizar_datos(lista_entrada, archivo_salida)
   - Compara IDs nuevos vs existentes
   - Elimina registros de juegos que bajaron del top
   - Reprocesa TODO juegos válidos (actualizar precios/métricas)
   - Log de cambios realizados

# Resultado:
- Archivo NDJSON siempre contiene juegos del top actual
- Precios siempre actualizados (ninguno es saltado)
- Juegos obsoletos eliminados automáticamente
```

### Ajustar cantidad de juegos
- `scripts/gameid-script.py` → `CANTIDAD_POR_CRITERIO = 5000` (IDs por criterio)
- `scripts/sacar-datos-games.py` → `CANTIDAD_A_PROCESAR = 0` (0 = todos, cambiar a X para pruebas)

### Palabras clave para filtrado
Edita `scripts/filter-games.py` para cambiar qué se filtra (DLC, soundtracks, etc.)

### Configurar resúmenes IA
Configura la API key de OpenRouter en `/home/g6/reto/imp-futuras/.env` para activar generación automática de resúmenes

### Cambiar modelo de embeddings
Edita `scripts/instalar_modelo.py` y `scripts/vectorizador.py`:
```python
# Opciones:
# - 'all-mpnet-base-v2' (inglés, 768 dims)
# - 'paraphrase-multilingual-mpnet-base-v2' (multilingüe, 768 dims) ← ACTUAL
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
0 2 * * * cd /home/g6/reto/scraper && /home/g6/.venv/bin/python scripts/run_pipeline.py >> /home/g6/reto/scraper/logs/cron.log 2>&1 && /home/g6/.venv/bin/python scripts/vectorizador.py >> /home/g6/reto/scraper/logs/cron.log 2>&1
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
- **Espacio en disco**: ~5-6 GB (venv global 2GB + modelo 470MB + datos 2-3GB)
- **Python 3.8+** requerido (testeado con Python 3.12.3)
- **Venv global**: `/home/g6/.venv` **obligatorio** - compartido entre scraper e imp-futuras
- **Librerías CPU-only**: PyTorch sin CUDA para ahorrar espacio (~4 GB menos que versión GPU)
- **Modelos en caché**: `~/.cache/huggingface/hub/` se crea automáticamente (~470MB)

## 🛠️ Tecnologías

- **Scraping**: `requests` + `BeautifulSoup4`
- **Embeddings**: `sentence-transformers` (HuggingFace)
- **Modelo**: `paraphrase-multilingual-mpnet-base-v2` (278M parámetros, 768 dims)
- **Backend ML**: PyTorch (CPU-only)
- **Resúmenes IA**: OpenRouter (GPT-4o-mini) con parallelización
- **Formato de datos**: NDJSON (compatible con Filebeat/Logstash/Elasticsearch)


# Para ¡¡¡ VALIDACION !!!

- **Cambiar nombre de el .env.example  --->  .env  (/imp-futuras)**
- **poner API KEY de Openrouter en el .env**
- Cambiar en el archivo **/scraper/scripts/sacar-datos-games.py**
  
```python

# 0 = PROCESAR TODOS. Pon un número bajo (ej: 50) para validacion.
CANTIDAD_A_PROCESAR = 0 # --> 50

```

- Cambiar en el archivo **/scraper/scripts/gameid-scripts**

```python

# 5000 de cada tipo para asegurar variedad (Para Validacion poner 50 en los 2 primeros)
CANTIDAD_POR_CRITERIO = 5000  # --> 50
RESULTADOS_POR_PAGINA = 50 
TIMEOUT = 30
MAX_REINTENTOS = 3

```

- Por ultimo darle permisos al **setup.sh** y ejecutarlo

```bash

chmod 777 scraper/setup.sh
./setup.sh

```
