# Reassadsúmenes IA - Pipeline de Descripciones Steam
assad
Pipeline automatizado para generar resúmenes técnicos de juegos de Steam usando OpenRouter GPT-4o-mini. Extrae descripciones desde Steam API y genera resúmenes optimizados para búsqueda semántica (RAG).

## 📁 Estructura

```
imp-futuras/
├── scripts/
│   ├── extract-desc.py           # Extrae todas las descripciones Steam API
│   ├── extract-desc-nuevas.py    # Extrae solo nuevas (validado vs top-games)
│   ├── enrich-raw-desc.py        # Enriquece descripciones existentes
│   ├── sync-ids.py               # Sincroniza IDs con steam-top-games.json
│   ├── openrouter-call.py        # Genera resúmenes IA (7 hilos paralelos)
│   └── clean-summary.sh          # Limpia caracteres escape JSON
├── data/
│   ├── raw-desc.ndjson           # Descripciones originales (HTML limpio)
│   └── summary.ndjson            # Resúmenes generados por IA
├── backup/
│   └── raw-desc-backup.ndjson    # Respaldo automático
├── flux.sh                        # Orquestador del pipeline completo
├── .env.example                  # Plantilla configuración API key
├── requirements.txt              # Dependencias (openai, requests, bs4, dotenv)
└── README.md
```

## 🚀 Setup

**Usar venv global** (compartido con `/home/g6/reto/scraper`):
```bash
source /home/g6/.venv/bin/activate
cd /home/g6/reto/imp-futuras
pip install -r requirements.txt
```

**Configurar API key**:
```bash
cp .env.example .env
nano .env  # Añadir: OPENROUTER_API_KEY=sk-or-v1-...
```

## ▶️ Ejecución

**Pipeline completo (recomendado)**:
```bash
bash flux.sh
```

Ejecuta automáticamente:
1. `extract-desc-nuevas.py` → Extrae descripciones nuevas
2. `openrouter-call.py` → Genera resúmenes IA (paralelo)
3. `clean-summary.sh` → Limpia JSON

**Scripts individuales**:
```bash
# 1. Extraer descripciones
python scripts/extract-desc-nuevas.py  # Solo nuevas (rápido)
python scripts/extract-desc.py         # Todas (completo)

# 2. Sincronizar IDs (elimina obsoletos)
python scripts/sync-ids.py

# 3. Generar resúmenes IA
python scripts/openrouter-call.py

# 4. Limpiar JSON
bash scripts/clean-summary.sh
```

## 📊 Flujo de Datos

```
Steam API → extract-desc-nuevas.py → raw-desc.ndjson
                                          ↓
                                    sync-ids.py (sincroniza IDs)
                                          ↓
                              openrouter-call.py (7 hilos)
                                          ↓
                                    summary.ndjson
                                          ↓
                              clean-summary.sh (limpia JSON)
                                          ↓
                    /reto/scraper/scripts/desc-changer.py
                                          ↓
                              steam-games-data.ndjson
```

## ⚙️ Características

- **Extracción incremental**: Solo procesa juegos nuevos (compara vs `raw-desc.ndjson` existente)
- **Sincronización de IDs**: Elimina juegos que bajaron del top (`sync-ids.py`)
- **Paralelización**: 7 hilos simultáneos para resúmenes IA
- **Modelo IA**: `openai/gpt-4o-mini` (~$1-2 USD por 10k juegos)
- **Anti-duplicados**: Previene reprocesar juegos ya resumidos
- **Backup automático**: Respaldo en `/backup` antes de modificaciones
- **Formato NDJSON**: Compatible con Elasticsearch/Logstash

## 🔒 Configuración

**Variables de entorno** (`.env`):
```env
OPENROUTER_API_KEY=sk-or-v1-tu-clave-aqui
OPENROUTER_MODEL=openai/gpt-4o-mini
```

**Ajustes en scripts** (opcional):
```python
# openrouter-call.py
CANTIDAD_A_PROCESAR = 0  # 0 = todos, N = primeros N
MAX_HILOS = 7            # Hilos paralelos
DELAY = 0.8              # Segundos entre requests

# extract-desc-nuevas.py
DELAY = 0.8              # Delay Steam API
```

## 📝 Formato de Salida

**raw-desc.ndjson** (descripciones):
```json
{"steam_id": 730, "name": "Counter-Strike 2", "detailed_description": "Juego de disparos táctico..."}
```

**summary.ndjson** (resúmenes):
```json
{"steam_id": 730, "name": "Counter-Strike 2", "summary": "Shooter táctico multijugador en primera persona..."}
```

## 🔗 Integración

Los resúmenes generados se integran en el pipeline principal:
1. **flux.sh** → genera `summary.ndjson`
2. **desc-changer.py** → inserta resúmenes en `steam-games-data.ndjson`
3. **vectorizador.py** → genera embeddings 768D
4. **json-a-elasticsearch.py** → ingesta en Elasticsearch para RAG

## 📈 Rendimiento

- **extract-desc-nuevas.py**: ~1.2s/juego (~1.5h para 4.7k juegos)
- **openrouter-call.py**: ~1-2s/juego paralelo (~1h para 4.7k juegos)
- **flux.sh completo**: ~3-4 horas (extracción + resúmenes + limpieza)
