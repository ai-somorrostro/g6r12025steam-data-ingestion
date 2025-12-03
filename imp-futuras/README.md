# Implementaciones Futuras - Pipeline de Resúmenes IA

## 📌 Descripción
Pipeline experimental para generar resúmenes técnicos de videojuegos de Steam utilizando LLMs (Large Language Models) de OpenRouter.

**Objetivo**: Crear descripciones optimizadas para búsqueda semántica, eliminando marketing y centrándose en características técnicas relevantes.

---

## 🏗️ Estructura del Proyecto

```
imp-futuras/
├── scripts/
│   ├── extract-desc.py       # Extrae descripciones desde Steam API
│   └── openrouter-call.py    # Genera resúmenes con LLM
├── data/
│   ├── raw-desc.ndjson       # Descripciones originales (limpias de HTML)
│   └── summary.ndjson        # Resúmenes generados por IA
|
├── .env.example              # Plantilla de configuración
├── .gitignore                # Protección de archivos sensibles
└── requirements.txt          # Dependencias Python
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

**Script**: `scripts/extract-desc.py`

**Función**: 
- Consulta la API de Steam para cada juego
- Extrae: `steam_id`, `name`, `detailed_description`
- Limpia etiquetas HTML preservando UTF-8 (ñ, tildes)
- Omite juegos sin descripción

**Ejecución**:
```bash
source venv/bin/activate
python scripts/extract-desc.py
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

### **Fase 2: Generación de Resúmenes IA**

**Script**: `scripts/openrouter-call.py`

**Función**:
- Lee descripciones originales de `raw-desc.ndjson`
- Envía cada descripción a OpenRouter (modelo GPT-4o-mini)
- Genera resumen técnico en español (3-4 líneas)
- Enfoque: género, ambientación, mecánicas, tono
- Evita duplicados automáticamente
- Procesamiento paralelo (5 hilos)

**Ejecución**:
```bash
source venv/bin/activate
python scripts/openrouter-call.py
```

**Configuración**:
```python
CANTIDAD_A_PROCESAR = 100  # Límite de juegos por ejecución
MAX_HILOS = 5              # Hilos paralelos (rate limit)
```

**Output**: `data/summary.ndjson` (modo append)

**Formato**:
```json
{"steam_id": 730, "name": "Counter-Strike 2", "summary": "Shooter táctico multijugador en primera persona..."}
```

---

## 🔄 Flujo de Trabajo

```
Steam API
   ↓
extract-desc.py → raw-desc.ndjson
   ↓
openrouter-call.py → summary.ndjson
   ↓
(Futuro: Vectorización y RAG)
```

---

## ⚙️ Características Técnicas

### **Extract-desc.py**
- **Delay adaptativo**: 0.8s entre peticiones (optimizado para pocos campos)
- **Limpieza HTML**: Elimina tags, decodifica entidades, preserva UTF-8
- **Error handling**: Maneja rate limits (429), timeouts, errores de API
- **Formato**: NDJSON (Newline-Delimited JSON) para streaming

### **Openrouter-call.py**
- **Modelo**: `openai/gpt-4o-mini` (rápido y económico)
- **Paralelización**: ThreadPoolExecutor con 5 workers
- **Anti-duplicados**: Lee IDs ya procesados antes de empezar
- **Modo incremental**: Append mode, puedes ejecutar múltiples veces
- **Prompt engineering**: Instrucciones específicas para resúmenes técnicos
- **Seguridad**: API key desde `.env` (no hardcodeada)

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
# Procesar solo 10 juegos de prueba
# Editar en openrouter-call.py:
CANTIDAD_A_PROCESAR = 10

python scripts/openrouter-call.py
```

---

## 🔧 Troubleshooting

| Error | Solución |
|-------|----------|
| `OPENROUTER_API_KEY no encontrada` | Verifica que `.env` existe y tiene la clave correcta |
| `Connection refused` | Verifica conexión a internet o prueba con VPN |
| `Rate limit exceeded` | Reduce `MAX_HILOS` o aumenta `DELAY` |
| `No se encuentra raw-desc.ndjson` | Ejecuta primero `extract-desc.py` |

---

## 📈 Métricas de Rendimiento

**Extract-desc.py**:
- ~1.2s por juego (0.8s delay + 0.4s request)
- ~10,000 juegos en ~3.5 horas

**Openrouter-call.py**:
- ~2-3s por juego con 5 hilos
- ~100 juegos en ~1 minuto
- ~10,000 juegos en ~1 hora

---

## 🚧 Roadmap

- [ ] Vectorización de resúmenes con sentence-transformers
- [ ] Ingesta a Elasticsearch con embeddings
- [ ] Comparación de calidad: descripción original vs resumen IA
- [ ] Pipeline automático end-to-end
- [ ] A/B testing de diferentes prompts
- [ ] Soporte para múltiples idiomas

---

## 📦 Dependencias

- `openai>=1.0.0` - Cliente OpenRouter/OpenAI
- `python-dotenv>=1.0.0` - Gestión de variables de entorno
- `requests` - Peticiones HTTP a Steam API
- `concurrent.futures` - Paralelización (built-in)

---

## 📞 Integración con el Proyecto Principal

Este directorio está diseñado para integrarse con:
- `/home/g6/reto/scraper/` - Pipeline principal de scraping
- `/home/g6/API-Reto-1/` - API RAG con Elasticsearch

Los resúmenes generados pueden usarse como:
1. Sustitutos de descripciones largas en embeddings
2. Input para fine-tuning de modelos
3. Datos de entrenamiento para clasificación automática
