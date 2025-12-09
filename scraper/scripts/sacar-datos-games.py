import requests
import json
import time
import logging
import os
import html
import re
import sys
from datetime import datetime

# Forzar que los prints se muestren inmediatamente (sin buffer)
sys.stdout.reconfigure(line_buffering=True)

# Obtener la ruta del directorio raíz del proyecto (un nivel arriba)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =================================================================
# 1. CONFIGURACIÓN DEL LOGGER
# =================================================================
logging.basicConfig(
    filename=os.path.join(PROJECT_ROOT, 'logs', 'scraper_full_data_metrics.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 0 = PROCESAR TODOS. Pon un número bajo (ej: 10) para probar.
CANTIDAD_A_PROCESAR = 0

ARCHIVO_ENTRADA = os.path.join(PROJECT_ROOT, 'data', 'steam-top-games.json')
ARCHIVO_SALIDA = os.path.join(PROJECT_ROOT, 'data', 'steam-games-data.ndjson') 

URL_DETALLES = "https://store.steampowered.com/api/appdetails/"
PARAMS_BASE = {"cc": "es", "l": "spanish"}
DELAY = 1.3 
URL_STORE_PAGE = "https://store.steampowered.com/app/{appid}/?l=spanish&cc=es"

# =================================================================
# 2. FUNCIONES DE SINCRONIZACIÓN
# =================================================================
def cargar_ids_desde_ndjson(filepath):
    """Carga todos los IDs del archivo NDJSON existente."""
    ids = set()
    if not os.path.exists(filepath):
        return ids
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for linea in f:
                if linea.strip():
                    doc = json.loads(linea)
                    ids.add(doc.get('steam_id'))
    except Exception as e:
        logging.error(f"Error al cargar IDs desde NDJSON: {e}")
    
    return ids

def sincronizar_datos(lista_entrada, archivo_salida):
    """
    Sincroniza los datos:
    1. Si no existe archivo_salida: procesar todos
    2. Si existe: elimina obsoletos, reprocesa todo para actualizar precios
    
    Retorna: lista de IDs a procesar
    """
    ids_nuevos = set(juego.get('appid') for juego in lista_entrada)
    ids_existentes = cargar_ids_desde_ndjson(archivo_salida)
    ids_a_eliminar = ids_existentes - ids_nuevos
    
    print(f"\n[SINCRONIZACIÓN]")
    print(f"  Total IDs en steam-top-games.json: {len(ids_nuevos)}")
    print(f"  Total IDs en steam-games-data.ndjson: {len(ids_existentes)}")
    print(f"  IDs a reprocesar (actualizar precios): {len(ids_nuevos)}")
    print(f"  IDs obsoletos a eliminar: {len(ids_a_eliminar)}")
    print()
    
    # Eliminar obsoletos si existen
    if len(ids_a_eliminar) > 0:
        print(f"[*] Eliminando {len(ids_a_eliminar)} registros obsoletos...")
        datos_validos = []
        try:
            with open(archivo_salida, 'r', encoding='utf-8') as f:
                for linea in f:
                    if linea.strip():
                        doc = json.loads(linea)
                        if doc.get('steam_id') in ids_nuevos:
                            datos_validos.append(doc)
        except Exception as e:
            logging.error(f"Error al leer datos: {e}")
        
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            for doc in datos_validos:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        
        logging.info(f"SINCRONIZACIÓN | Eliminados:{len(ids_a_eliminar)} | A reprocesar:{len(ids_nuevos)}")
    else:
        # Vaciar archivo para reprocesar todo
        if os.path.exists(archivo_salida):
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                pass
    
    return list(ids_nuevos)
def limpiar_html_respetando_utf8(texto):
    """
    Elimina las etiquetas HTML
    """
    if not texto or not isinstance(texto, str): return ""
    
    # 1. Reemplazar saltos de línea HTML por espacios para que no se peguen las palabras
    texto = texto.replace('<br>', ' ').replace('<br/>', ' ').replace('</p>', ' ')
    
    # 2. Eliminar cualquier etiqueta HTML (<...>) usando Expresiones Regulares
    texto_limpio = re.sub(r'<[^>]+>', ' ', texto)
    
    # 3. Decodificar entidades HTML (Ej: convierte "&quot;" en comillas reales, "&amp;" en &)
    texto_limpio = html.unescape(texto_limpio)
    
    # 4. Eliminar espacios dobles o triples que hayan quedado
    return " ".join(texto_limpio.split())

def extraer_tags_populares(html, max_tags=10):
    try:
        crudos = re.findall(r'class="app_tag"[^>]*>([^<]+)<', html, flags=re.IGNORECASE | re.DOTALL)
        tags = []
        vistos = set()
        for bruto in crudos:
            tag = bruto.strip()
            if not tag or tag == "+":
                continue
            if tag not in vistos:
                vistos.add(tag)
                tags.append(tag)
            if len(tags) >= max_tags:
                break
        return tags
    except Exception as e:
        logging.warning(f"Error al extraer tags populares: {e}")
        return []

def obtener_tags_populares(appid):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(URL_STORE_PAGE.format(appid=appid), headers=headers, timeout=10)
        if resp.status_code == 200:
            return extraer_tags_populares(resp.text)
        logging.warning(f"Fallo al pedir tags populares {appid}: status {resp.status_code}")
    except Exception as e:
        logging.warning(f"Excepcion al pedir tags populares {appid}: {e}")
    return []
def normalizar_fecha(fecha_texto):
    if not fecha_texto: return None
    meses = {
        "ENE": "01", "FEB": "02", "MAR": "03", "ABR": "04", "MAY": "05", "JUN": "06",
        "JUL": "07", "AGO": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DIC": "12"
    }
    try:
        partes = fecha_texto.upper().replace(".", "").split()
        if len(partes) == 3:
            dia = partes[0].zfill(2)
            mes = meses.get(partes[1][:3], "01")
            anio = partes[2]
            return f"{anio}-{mes}-{dia}"
    except:
        return None
    return None

# =================================================================
# 3. PROCESAMIENTO DE DATOS
# =================================================================
def procesar_juego_elk(appid, data):
    is_free = data.get('is_free', False)
    price_data = data.get('price_overview', {})
    
    if is_free:
        p_final, p_initial, desc = 0.0, 0.0, 0
    else:
        p_final = float(price_data.get('final', 0)) / 100
        p_initial = float(price_data.get('initial', 0)) / 100
        desc = int(price_data.get('discount_percent', 0))

    # --- TEXTOS (Aquí aplicamos la limpieza suave) ---
    short_desc_raw = data.get('short_description', '')
    short_desc_clean = limpiar_html_respetando_utf8(short_desc_raw)
    
    detailed_desc_raw = data.get('detailed_description', '')
    detailed_desc_clean = limpiar_html_respetando_utf8(detailed_desc_raw)

    pc_req = data.get('pc_requirements', {})
    req_min_raw = pc_req.get('minimum', "") if isinstance(pc_req, dict) else ""
    req_min_clean = limpiar_html_respetando_utf8(req_min_raw)
    
    # --- LISTAS ---
    genres = [g['description'] for g in data.get('genres', [])]
    categories_raw = [c['description'] for c in data.get('categories', [])]
    categories_populares = obtener_tags_populares(appid)
    categories = categories_populares if categories_populares else categories_raw
    devs = data.get('developers', [])
    pubs = data.get('publishers', [])
    
    ach_data = data.get('achievements', {})
    ach_list = [ach.get('name') for ach in ach_data.get('highlighted', [])]

    # --- FECHAS ---
    raw_date = data.get('release_date', {}).get('date', '')
    iso_date = normalizar_fecha(raw_date)
    now_clean = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    return {
        "steam_id": int(appid),
        "name": data.get('name'),
        "scraped_at": now_clean, 
        
        # Métricas
        "price_eur": p_final,
        "price_initial_eur": p_initial,
        "discount_pct": desc,
        "metacritic_score": int(data.get('metacritic', {}).get('score', 0)),
        "recommendations_total": int(data.get('recommendations', {}).get('total', 0)),
        "achievements_count": int(ach_data.get('total', 0)),
        "is_free": is_free,
        
        # Listas
        "genres": genres,
        "categories": categories,
        "developers": devs,
        "publishers": pubs,
        "achievements_list": ach_list,
        
        # Textos (Limpios de HTML, pero con tildes y ñ)
        "short_description": short_desc_clean,
        "detailed_description": detailed_desc_clean, 
        "pc_requirements_min": req_min_clean,
        
        # Datos raw visuales
        "release_date_text": raw_date,
        "release_date": iso_date,
        "header_image": data.get('header_image'),
        "website": data.get('website')
    }

# =================================================================
# 4. EJECUCIÓN PRINCIPAL
# =================================================================
def main():
    print(f"[*] INICIANDO SCRAPER (Output: {ARCHIVO_SALIDA})")
    print(f"[*] Logs: scraper_full_data_metrics.log")
    
    if not os.path.exists(ARCHIVO_ENTRADA):
        print(f"[ERROR] No encuentro '{ARCHIVO_ENTRADA}'.")
        return
        
    with open(ARCHIVO_ENTRADA, 'r', encoding='utf-8') as f:
        lista = json.load(f)

    # SINCRONIZAR: eliminar obsoletos y reprocesar todo
    print("\n[SINCRONIZACIÓN DE DATOS]")
    ids_a_procesar = sincronizar_datos(lista, ARCHIVO_SALIDA)
    lista = [j for j in lista if j.get('appid') in ids_a_procesar]

    if CANTIDAD_A_PROCESAR > 0: 
        lista = lista[:CANTIDAD_A_PROCESAR]
    
    total = len(lista)
    print(f"[*] Procesando {total} juegos...")

    # Limpiamos archivo JSON de salida (Modo 'w' vacía el archivo)
    with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f: pass 
    
    # Escribimos en modo Append ('a')
    with open(ARCHIVO_SALIDA, 'a', encoding='utf-8') as f_out:
        
        for i, juego in enumerate(lista):
            appid = juego.get('appid')
            
            # Inicio medición tiempo
            start_time = time.time()
            
            try:
                r = requests.get(f"{URL_DETALLES}?appids={appid}", params=PARAMS_BASE, timeout=10)
                status_code = r.status_code
                
                # Calculamos duración
                end_time = time.time()
                duration = round(end_time - start_time, 4)

                if status_code == 200:
                    d = r.json()
                    if d and str(appid) in d and d[str(appid)]['success']:
                        # Procesar datos
                        doc = procesar_juego_elk(appid, d[str(appid)]['data'])
                        
                        # Escribir JSON NDJSON (ensure_ascii=False mantiene la ñ)
                        f_out.write(json.dumps(doc, ensure_ascii=False) + "\n")
                        f_out.flush()
                        
                        # Log
                        logging.info(f"SUCCESS | ID:{appid} | NAME:{doc['name']} | PRICE:{doc['price_eur']} | LATENCY:{duration}s")
                        
                        print(f"[OK] [{i+1}/{total}] {doc['name']} ({doc['price_eur']}\u20ac)")
                    else:
                        print(f"[SKIP] [{i+1}/{total}] No disponible: {appid}")
                        logging.warning(f"UNAVAILABLE | ID:{appid} | LATENCY:{duration}s")
                
                elif status_code == 429:
                    print("[WARN] RATE LIMIT. Pausando 60s...")
                    logging.error(f"RATE_LIMIT_429 | ID:{appid}")
                    time.sleep(60)
                
                else:
                     logging.error(f"HTTP_ERROR | STATUS:{status_code} | ID:{appid}")

            except Exception as e:
                logging.error(f"EXCEPTION | ID:{appid} | ERROR:{e}")
            
            time.sleep(DELAY)

    print("-" * 60)
    print(f"[DONE] FINALIZADO el Json y el log.")

if __name__ == "__main__":
    main()