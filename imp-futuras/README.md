# Implementaciones Futuras - Pipeline de Resúmenes IA

## 📌 Descripción
Pipeline experimental para generar resúmenes técnicos de videojuegos de Steam utilizando LLMs (Large Language Models) de OpenRouter.

**Objetivo**: Crear descripciones optimizadas para búsqueda semántica, eliminando marketing y centrándose en características técnicas relevantes.

---

## 🏗️ Estructura del Proyecto

```
imp-futuras/
├── scripts/
│   ├── extract-desc.py           # Extrae descripciones desde Steam API
│   ├── extract-desc-nuevas.py    # Extrae solo nuevas descripciones (validadas)
│   ├── extract-desc-reverse.py   # Extrae en orden inverso (de abajo a arriba)
│   ├── openrouter-call.py        # Genera resúmenes con OpenRouter GPT-4o-mini
│   ├── clean-summary.sh          # Limpia caracteres escape del JSON
│   └── sync-ids.py               # Sincroniza IDs entre archivos
├── data/
│   ├── raw-desc.ndjson           # Descripciones originales (limpias de HTML)
│   ├── raw-desc-backup.ndjson    # Respaldo de descripciones
│   ├── summary.ndjson            # Resúmenes generados por IA
│   └── .gitkeep                  # Preserva carpeta en Git
├── flux.sh                        # Orquestador del pipeline completo
├── .env.example                  # Plantilla de configuración
├── .gitignore                    # Protección de archivos sensibles
├── requirements.txt              # Dependencias Python
└── README.md                     # Este archivo
```

---

## 🚀 Instalación

### 1. Crear entorno virtual
```bash
cd /home/g6/reto/imp-futuras
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
Copia `.env.example` a `.env` y configura tu API key:

```bash
cp .env.example .env
nano .env
```

Contenido de `.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-tu-clave-aqui
OPENROUTER_MODEL=openai/gpt-4o-mini
```

---

## 📡 Pipeline de Ejecución

### **Fase 1: Extracción de Descripciones**

**Scripts principales**:
- `extract-desc.py` - Extrae todas las descripciones
- `extract-desc-nuevas.py` - Extrae solo juegos nuevos (con validación contra steam-top-games.json)
- `extract-desc-reverse.py` - Extrae en orden inverso (de abajo a arriba)

**Función**: 
- Consulta la API de Steam para cada juego
- Extrae: `steam_id`, `name`, `detailed_description`
- Limpia etiquetas HTML preservando UTF-8 (ñ, tildes)
- Omite juegos sin descripción
- Valida IDs contra lista de juegos filtrados (opcionalmente)
- Previene duplicados

**Ejecución (individual)**:
```bash
source venv/bin/activate
python scripts/extract-desc-nuevas.py  # Recomendado: solo nuevas
```

**Configuración**:
```python
CANTIDAD_A_PROCESAR = 0  # 0 = todos, o número específico
DELAY = 0.8              # Segundos entre peticiones
```

**Output**: `data/raw-desc.ndjson`

**Formato**:
```json
{"steam_id": 730, "name": "Counter-Strike 2", "detailed_description": "Juego de disparos táctico..."}
```

---

### **Fase 1.5: Sincronización de IDs**

**Script**: `sync-ids.py`

**Función**:
- Compara IDs en `raw-desc.ndjson` con la lista válida de `steam-top-games.json`
- Elimina descripciones de juegos que ya no están en la lista principal
- Crea backup automático antes de modificar
- Reporta estadísticas

**Ejecución**:
```bash
source venv/bin/activate
python scripts/sync-ids.py
```

**Output**: `raw-desc.ndjson` (sincronizado) + `raw-desc-backup.ndjson` (respaldo)

### **Fase 2: Generación de Resúmenes IA**

**Script**: `scripts/openrouter-call.py`

**Función**:
- Lee descripciones originales de `raw-desc.ndjson`
- Envía cada descripción a OpenRouter (modelo GPT-4o-mini)
- Genera resumen técnico en español (3-4 líneas)
- Enfoque: género, ambientación, mecánicas, tono
- Detecta DLC, expansiones y contenido adulto
- Evita duplicados automáticamente
- Procesamiento paralelo (7 hilos)

**Ejecución (individual)**:
```bash
source venv/bin/activate
python scripts/openrouter-call.py
```

**Configuración**:
```python
CANTIDAD_A_PROCESAR = 0   # 0 = todos, o número específico
MAX_HILOS = 7             # Hilos paralelos (rate limit)
DELAY = 0.8               # Segundos entre peticiones
```

**Output**: `data/summary.ndjson` (modo append)

**Formato**:
```json
{"steam_id": 730, "name": "Counter-Strike 2", "summary": "Shooter táctico multijugador en primera persona..."}
```

---

### **Fase 2.5: Limpieza de JSON**

**Script**: `scripts/clean-summary.sh`

**Función**:
- Elimina caracteres de escape (`\"`) del JSON
- Re-serializa cada línea de forma limpia
- Garantiza compatibilidad con parsers JSON estrictos

**Ejecución**:
```bash
bash scripts/clean-summary.sh
```

**Output**: `data/summary.ndjson` (limpio)

---

## 🚀 Ejecución Automática (Flux.sh)

**Script orquestador**: `flux.sh`

**Función**: Ejecuta el pipeline completo en secuencia:
1. Extrae nuevas descripciones (`extract-desc-nuevas.py`)
2. Genera resúmenes IA (`openrouter-call.py`)
3. Limpia JSON (`clean-summary.sh`)

**Ejecución**:
```bash
bash flux.sh
```

**Características**:
- Auto-crea y activa venv si no existe
- Instala dependencias automáticamente
- Sale si algún paso falla (set -e)
- Logs en consola para debugging

**Output**: `raw-desc.ndjson` + `summary.ndjson` (listos para usar)

---

## 🔄 Flujo de Trabajo

```
Steam API
   ↓
extract-desc-nuevas.py → raw-desc.ndjson
   ↓
sync-ids.py → raw-desc.ndjson (sincronizado)
   ↓
openrouter-call.py → summary.ndjson (7 hilos)
   ↓
clean-summary.sh → summary.ndjson (limpio)
   ↓
(O automático: bash flux.sh)
   ↓
→ /home/g6/reto/scraper/scripts/desc-changer.py
   ↓
steam-games-data.ndjson (con resúmenes IA)
```

---

## ⚙️ Características Técnicas

### **Extract-desc.py** (y variantes)
- **Versiones disponibles**:
  - `extract-desc.py` - Extrae todas las descripciones
  - `extract-desc-nuevas.py` - Solo nuevos juegos (recomendado, más rápido)
  - `extract-desc-reverse.py` - En orden inverso (flexible scheduling)
- **Delay adaptativo**: 0.8s entre peticiones (optimizado para pocos campos)
- **Limpieza HTML**: Elimina tags, decodifica entidades, preserva UTF-8
- **Validación**: Comprueba contra lista de juegos filtrados (steam-top-games.json)
- **Anti-duplicados**: Previene reextraer descripciones ya obtenidas
- **Error handling**: Maneja rate limits (429), timeouts, errores de API
- **Formato**: NDJSON (Newline-Delimited JSON) para streaming

### **Sync-ids.py**
- **Sincronización**: Compara IDs contra steam-top-games.json
- **Limpieza**: Elimina descripciones de juegos removidos
- **Backup**: Crea respaldo automático antes de modificar
- **Reportes**: Estadísticas de cambios realizados

### **Openrouter-call.py**
- **Modelo**: `openai/gpt-4o-mini` (rápido y económico)
- **Paralelización**: ThreadPoolExecutor con 7 workers (configurable)
- **Anti-duplicados**: Lee IDs ya procesados antes de empezar
- **Modo incremental**: Append mode, puedes ejecutar múltiples veces
- **Prompt engineering**: Instrucciones específicas para resúmenes técnicos
- **Detección**: Identifica DLC, expansiones, contenido adulto
- **Rate limiting**: Respeta límites de OpenRouter con delays
- **Seguridad**: API key desde `.env` (no hardcodeada)

### **Clean-summary.sh**
- **Limpieza JSON**: Elimina caracteres escape (`\"`)
- **Re-serialización**: Recrea JSON válido línea por línea
- **Compatibilidad**: Garantiza parseo correcto en downstream

---

## 📊 Ejemplo de Transformación

**Input** (raw-desc.ndjson):
```json
{
  "steam_id": 413150,
  "name": "Stardew Valley",
  "detailed_description": "Heredas la vieja granja de tu abuelo en Stardew Valley. Con herramientas de segunda mano y unas pocas monedas, te dispones a comenzar tu nueva vida. ¿Puedes aprender a vivir de la tierra y convertir estos campos cubiertos de maleza en un hogar próspero? No será fácil. Desde que Joja Corporation llegó a la ciudad, las antiguas formas de vida han desaparecido..."
}
```

**Output** (summary.ndjson):
```json
{
  "steam_id": 413150,
  "name": "Stardew Valley",
  "summary": "Simulador de granja con elementos RPG y gestión de recursos. Ambientación rural pixel-art con mecánicas de cultivo, ganadería, minería, pesca y relaciones sociales. Tono relajado y nostálgico con progresión a largo plazo."
}
```

---

## 🔒 Seguridad

### Archivos protegidos por `.gitignore`:
- `.env` - API keys
- `venv/` - Entorno virtual
- `data/*.ndjson` - Datasets

### ⚠️ IMPORTANTE:
- **NUNCA** subas `.env` a Git
- Usa `.env.example` como plantilla para otros colaboradores
- Revisa que `.gitignore` esté correcto antes de hacer commit

---

## 💰 Costos Estimados

**Modelo**: `openai/gpt-4o-mini`
- ~$0.15 por 1M tokens input
- ~$0.60 por 1M tokens output

**Por juego**:
- Input: ~500 tokens (descripción)
- Output: ~100 tokens (resumen)
- Costo: ~$0.0001 por juego

**10,000 juegos**: ~$1-2 USD

---

## 🧪 Testing

```bash
# Opción 1: Procesar solo 10 juegos de prueba
# Editar en openrouter-call.py:
CANTIDAD_A_PROCESAR = 10

python scripts/openrouter-call.py

# Opción 2: Ejecutar flux.sh completo (recomendado)
bash flux.sh
```

---

## 🔧 Troubleshooting

| Error | Solución |
|-------|----------|
| `OPENROUTER_API_KEY no encontrada` | Verifica que `.env` existe y tiene la clave correcta |
| `Connection refused` | Verifica conexión a internet o prueba con VPN |
| `Rate limit exceeded` | Reduce `MAX_HILOS` o aumenta `DELAY` |
| `No se encuentra raw-desc.ndjson` | Ejecuta primero `extract-desc-nuevas.py` |
| `clean-summary.sh no funciona` | Verifica permisos: `chmod +x scripts/clean-summary.sh` |
| `flux.sh falla a mitad` | Revisa logs en consola, algún script anterior falló |

---

## 📈 Métricas de Rendimiento

**Extract-desc-nuevas.py** (solo nuevas):
- ~1.2s por juego (0.8s delay + 0.4s request)
- ~4,700+ juegos en ~1.5 horas
- Más rápido porque salta duplicados

**Openrouter-call.py** (con 7 hilos):
- ~1-2s por juego (parallelizado)
- ~100 juegos en ~30 segundos
- ~4,700 juegos en ~1 hora

**Clean-summary.sh**:
- Instantáneo (~1-2 segundos para 4,700+ líneas)

**flux.sh (completo)**:
- ~3-4 horas para pipeline entero con nuevas descripciones + resúmenes

---

## 🚧 Roadmap

- [x] Extracción flexible (forward, reverse, solo nuevas)
- [x] Sincronización de IDs con steam-top-games.json
- [x] Generación de resúmenes IA (7 hilos)
- [x] Limpieza de caracteres escape JSON
- [x] Orquestador automático (flux.sh)
- [ ] Vectorización de resúmenes (integrada en scraper)
- [ ] Ingesta a Elasticsearch con embeddings (en /API-Reto-1/)
- [ ] Comparación de calidad: descripción original vs resumen IA
- [ ] Pipeline automático end-to-end
- [ ] A/B testing de diferentes prompts
- [ ] Soporte para múltiples idiomas

---

## 📦 Dependencias

- `openai>=1.0.0` - Cliente OpenRouter/OpenAI
- `python-dotenv>=1.0.0` - Gestión de variables de entorno
- `requests` - Peticiones HTTP a Steam API (extract scripts)
- `beautifulsoup4` - Parsing HTML de descripciones
- `concurrent.futures` - Paralelización (built-in)
- `subprocess` - Ejecución de scripts shell (built-in)

---

## 📞 Integración con Proyecto Principal

**Carpeta scraper** (`/home/g6/reto/scraper/`):
- Los resúmenes generados en `summary.ndjson` se integran vía `desc-changer.py`
- El script busca coincidencias por `steam_id` y reemplaza `detailed_description`
- Luego el flujo continúa con vectorización en `vectorizador.py`

**Carpeta API** (`/home/g6/API-Reto-1/`):
- Los datos vectorizados se ingestan en Elasticsearch vía `json-a-elasticsearch.py`
- El campo `vector_embedding` (768 dims) permite búsqueda kNN semántica
- Los resúmenes IA mejoran la calidad del RAG al ser más concisos

**Flujo end-to-end**:
```
imp-futuras/
  ├─ flux.sh (extrae + resume)
  │
/reto/scraper/
  ├─ desc-changer.py (integra resúmenes)
  ├─ vectorizador.py (genera embeddings)
  │
/API-Reto-1/
  └─ json-a-elasticsearch.py (ingesta en ES)
     └─ RAG Query API (búsqueda + respuesta con LLM)
```
