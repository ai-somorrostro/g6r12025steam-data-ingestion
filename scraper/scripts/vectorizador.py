import json
import os
import re
import tempfile
import shutil
from sentence_transformers import SentenceTransformer

# --- CONFIGURACION (RUTAS RELATIVAS) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_DIR = os.path.dirname(SCRIPT_DIR)  # Sube a /scraper
DATA_DIR = os.path.join(SCRAPER_DIR, "data")

ARCHIVO_RAW = os.path.join(DATA_DIR, "steam-games-data.ndjson")
ARCHIVO_FINAL = os.path.join(DATA_DIR, "steam-games-data-vect.ndjson")

# Nombre del modelo (Multilingue)
MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2'

print(f"Cargando modelo IA ({MODEL_NAME})...")
try:
    modelo = SentenceTransformer(MODEL_NAME)
    print("Modelo cargado.")
except Exception as e:
    print(f"Error cargando modelo: {e}")
    exit(1)

def limpiar_html(texto):
    if not texto: return ""
    return re.sub(r'<[^>]+>', '', texto).strip()

def procesar_pipeline():
    if not os.path.exists(ARCHIVO_RAW):
        print(f"ERROR: No encuentro el archivo origen: {ARCHIVO_RAW}")
        return

    print(f"Leyendo datos crudos de {ARCHIVO_RAW}...")
    
    # --- ESTRATEGIA DE ESCRITURA ATOMICA ---
    archivo_temporal = ARCHIVO_FINAL + ".tmp"
    
    contador = 0
    errores = 0

    with open(ARCHIVO_RAW, 'r', encoding='utf-8') as f_in, \
         open(archivo_temporal, 'w', encoding='utf-8') as f_out:
        
        for i, linea in enumerate(f_in):
            try:
                if not linea.strip(): continue
                juego = json.loads(linea)
                
                # --- PREPARACION DE DATOS ---
                
                nombre = juego.get('name') or "Sin Nombre"
                genres = ", ".join((juego.get('genres') or [])[:5])
                tags = ", ".join((juego.get('categories') or [])[:10])
                
                # 1. LIMPIEZA DE LA DESCRIPCION LARGA (Para el JSON final)
                # La limpiamos para que OpenRouter no lea HTML basura, pero NO la metemos al vector.
                desc_larga_limpia = limpiar_html(juego.get('detailed_description'))
                juego['detailed_description'] = desc_larga_limpia # Actualizamos el objeto original

                # --- CONSTRUCCION DEL TEXTO SEMANTICO (VECTOR) ---
                # Solo: Título, Géneros, Tags y Descripción IA (sin developer ni short_description)
                texto_vector = (
                    f"Title: {nombre}. "
                    f"Genres: {genres}. "
                    f"Tags: {tags}. "
                    f"Details: {desc_larga_limpia}"
                )

                # --- VECTORIZACION ---
                vector = modelo.encode(texto_vector)
                
                # Inyectamos el vector en el JSON original
                juego['vector_embedding'] = vector.tolist()
                
                # Escribimos AL VUELO
                json.dump(juego, f_out, ensure_ascii=False)
                f_out.write('\n')
                
                contador += 1
                if contador % 100 == 0:
                    print(f"Procesados: {contador} juegos...", end='\r')

            except Exception as e:
                errores += 1
                print(f"\nError en linea {i}: {e}")

    print(f"\nFinalizado. Procesados: {contador}. Errores: {errores}")
    
    # --- MOVER ARCHIVO FINAL ---
    print("Moviendo archivo temporal a destino final...")
    shutil.move(archivo_temporal, ARCHIVO_FINAL)
    print(f"Listo! Archivo generado en: {ARCHIVO_FINAL}")

if __name__ == "__main__":
    procesar_pipeline()