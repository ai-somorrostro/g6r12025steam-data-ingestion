import json
import os
import concurrent.futures
import time
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ==========================================
# CONFIGURACION
# ==========================================

# Rutas de archivos (relativas al directorio del script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROYECTO_DIR = os.path.dirname(SCRIPT_DIR)
ARCHIVO_RAW = os.path.join(PROYECTO_DIR, "data", "raw-desc.ndjson")
ARCHIVO_SALIDA = os.path.join(PROYECTO_DIR, "data", "summary.ndjson")

# Configuracion de OpenRouter / API
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODELO = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

if not OPENROUTER_API_KEY:
    raise ValueError("[ERROR] OPENROUTER_API_KEY no encontrada en .env")

# Configuracion de rendimiento
# Elegir menos hilos para no saturar el Rate Limit de la API (max 10)
MAX_HILOS = 7

# Limite de juegos a procesar (0 = todos)
CANTIDAD_A_PROCESAR = 0  # Cambia esto al numero que quieras 

# Inicializar cliente
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# ==========================================
# LOGICA DE NEGOCIO
# ==========================================

def generar_resumen_ia(juego):
    """
    Construye el prompt y llama a la API para obtener el resumen.
    """
    nombre = juego.get('name', 'Juego Desconocido')
    descripcion_larga = juego.get('detailed_description', '')
    if not descripcion_larga.strip():
        return None
    prompt = f"""
    Actúa como un experto en catalogación de videojuegos.
    Tu tarea es generar un resumen técnico y denso en ESPAÑOL (Castellano) para ser usado en un motor de búsqueda semántico.
    
    INPUT:
    - Juego: {nombre}
    - Texto original: {descripcion_larga}
    
    INSTRUCCIONES DE SALIDA:
    1. Escribe un párrafo de máximo 3 o 4 líneas.
    2. Céntrate OBLIGATORIAMENTE en: Género, Ambientación, Mecánicas principales y Tono.
    3. Usa palabras clave específicas.
    4. NO uses frases de marketing ni premios. Ve al grano.
    5. Traduce todo al español si el original está en otro idioma.
    6. Si detectas que es un paquete de mejora o DLC, indícalo claramente al inicio del resumen.
    7. Si detectas que es un juego para adultos, indícalo claramente al final del resumen.
    
    RESUMEN:
    """
    try:
        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": "Eres un asistente de resumen de datos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR API] Fallo al resumir '{nombre}': {e}")
        return None

def procesar_linea(linea):
    """
    Funcion worker que ejecuta cada hilo.
    Toma una linea de texto (JSON), la procesa y devuelve la linea enriquecida.
    """
    if not linea.strip():
        return None

    try:
        juego = json.loads(linea)
        
        # Solo procesar si tiene nombre y descripción larga
        nombre = juego.get('name', '').strip()
        descripcion_larga = juego.get('detailed_description', '').strip()
        if not nombre or not descripcion_larga:
            return None
        resumen = generar_resumen_ia(juego)
        if resumen:
            salida = {
                "steam_id": juego.get("steam_id"),
                "name": nombre,
                "summary": resumen
            }
            return json.dumps(salida, ensure_ascii=False)
        else:
            return None

    except json.JSONDecodeError:
        print("[ERROR JSON] Linea corrupta ignorada.")
        return None
    except Exception as e:
        print(f"[ERROR GENERICO] {e}")
        return linea.strip() # Devolvemos la linea original en caso de error fatal

# ==========================================
# EJECUCION PRINCIPAL
# ==========================================

def main():
    if not os.path.exists(ARCHIVO_RAW):
        print(f"[ERROR] No se encuentra el archivo de entrada: {ARCHIVO_RAW}")
        return

    print(f"[INFO] Iniciando proceso de resumen IA.")
    print(f"[INFO] Entrada: {ARCHIVO_RAW}")
    print(f"[INFO] Salida:  {ARCHIVO_SALIDA}")
    print(f"[INFO] Hilos paralelos: {MAX_HILOS}")
    
    # Cargar IDs ya procesados para evitar duplicados
    ids_procesados = set()
    if os.path.exists(ARCHIVO_SALIDA):
        print("[INFO] Cargando IDs ya procesados...")
        with open(ARCHIVO_SALIDA, 'r', encoding='utf-8') as f:
            for linea in f:
                try:
                    doc = json.loads(linea)
                    steam_id = doc.get('steam_id')
                    if steam_id:
                        ids_procesados.add(steam_id)
                except:
                    pass
        print(f"[INFO] {len(ids_procesados)} juegos ya procesados (se omitirán)")
    
    print("[INFO] Leyendo archivo en memoria...")
    with open(ARCHIVO_RAW, 'r', encoding='utf-8') as f:
        lineas = f.readlines()
    
    # Filtrar juegos ya procesados
    lineas_a_procesar = []
    for linea in lineas:
        try:
            juego = json.loads(linea)
            if juego.get('steam_id') not in ids_procesados:
                lineas_a_procesar.append(linea)
        except:
            pass
    
    # Aplicar limite de cantidad
    if CANTIDAD_A_PROCESAR > 0 and len(lineas_a_procesar) > CANTIDAD_A_PROCESAR:
        lineas_a_procesar = lineas_a_procesar[:CANTIDAD_A_PROCESAR]
    
    total_lineas = len(lineas_a_procesar)
    print(f"[INFO] Total de juegos a procesar: {total_lineas}")
    procesados = 0
    # Usar modo 'a' (append) para no sobrescribir juegos ya procesados
    with open(ARCHIVO_SALIDA, 'a', encoding='utf-8') as f_out:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_HILOS) as executor:
            resultados = executor.map(procesar_linea, lineas_a_procesar)
            for resultado in resultados:
                if resultado:
                    f_out.write(resultado + '\n')
                    f_out.flush()
                    procesados += 1
                    if procesados % 50 == 0:
                        porcentaje = (procesados / total_lineas) * 100
                        print(f"[PROGRESO] {procesados}/{total_lineas} juegos ({porcentaje:.2f}%)", end='\r')
    print(f"\n[EXITO] Proceso finalizado.")
    print(f"[INFO] Archivo guardado en: {ARCHIVO_SALIDA}")

if __name__ == "__main__":
    main()