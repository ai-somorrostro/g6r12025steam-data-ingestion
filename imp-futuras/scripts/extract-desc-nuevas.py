import requests
import json
import time
import os
import sys
import html
import re

# Forzar que los prints se muestren inmediatamente (sin buffer)
sys.stdout.reconfigure(line_buffering=True)

# Obtener la ruta del directorio raíz del proyecto (dos niveles arriba desde scripts/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración
CANTIDAD_A_PROCESAR = 0  # 0 = procesar todos
ARCHIVO_ENTRADA = os.path.join(PROJECT_ROOT, 'scraper', 'data', 'steam-top-games.json')
ARCHIVO_STEAM_ACTUAL = os.path.join(PROJECT_ROOT, 'scraper', 'data', 'steam-top-games.json')
ARCHIVO_SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw-desc.ndjson')

URL_DETALLES = "https://store.steampowered.com/api/appdetails/"
PARAMS_BASE = {"cc": "es", "l": "spanish"}
DELAY = 0.8  # Reducido porque solo extraemos 3 campos

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

def cargar_ids_ya_procesados():
    """
    Lee el archivo de salida y devuelve un set con los steam_id ya procesados
    """
    ids_procesados = set()
    if os.path.exists(ARCHIVO_SALIDA):
        print("[INFO] Escaneando IDs ya procesados...")
        try:
            with open(ARCHIVO_SALIDA, 'r', encoding='utf-8') as f:
                for linea in f:
                    try:
                        doc = json.loads(linea)
                        steam_id = doc.get('steam_id')
                        if steam_id:
                            ids_procesados.add(steam_id)
                    except:
                        pass
        except:
            pass
        print(f"[INFO] {len(ids_procesados)} IDs ya procesados cargados")
    return ids_procesados

def cargar_steam_ids_validos():
    """
    Lee steam-top-games.json y devuelve un set con los IDs válidos actuales
    """
    ids_validos = set()
    if os.path.exists(ARCHIVO_STEAM_ACTUAL):
        print("[INFO] Cargando IDs válidos de steam-top-games.json...")
        try:
            with open(ARCHIVO_STEAM_ACTUAL, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ids_validos = set(juego.get('appid') for juego in data if juego.get('appid'))
        except Exception as e:
            print(f"[ERROR] No se pudo cargar steam-top-games.json: {e}")
        print(f"[INFO] {len(ids_validos)} IDs válidos cargados")
    return ids_validos

def main():
    print(f"[*] INICIANDO EXTRACCIÓN DE DESCRIPCIONES (DE ABAJO A ARRIBA)")
    print(f"[*] Fuente: {ARCHIVO_ENTRADA}")
    print(f"[*] Validador: {ARCHIVO_STEAM_ACTUAL}")
    print(f"[*] Output: {ARCHIVO_SALIDA}")
    
    if not os.path.exists(ARCHIVO_ENTRADA):
        print(f"[ERROR] No encuentro '{ARCHIVO_ENTRADA}'.")
        return
    
    # Cargar IDs válidos de steam-top-games.json actual
    ids_validos = cargar_steam_ids_validos()
    if not ids_validos:
        print("[ERROR] No hay IDs válidos en steam-top-games.json")
        return
    
    # Cargar IDs ya procesados
    ids_ya_procesados = cargar_ids_ya_procesados()
    
    with open(ARCHIVO_ENTRADA, 'r', encoding='utf-8') as f:
        lista = json.load(f)
    
    # Invertir la lista para procesar de abajo a arriba
    lista = list(reversed(lista))
    
    if CANTIDAD_A_PROCESAR > 0:
        lista = lista[:CANTIDAD_A_PROCESAR]
    
    total = len(lista)
    print(f"[*] Procesando {total} juegos (de abajo a arriba)...")
    
    # Crear directorio de salida si no existe
    os.makedirs(os.path.dirname(ARCHIVO_SALIDA), exist_ok=True)
    
    # Escribir en modo append (NO borra lo anterior)
    procesados = 0
    saltados = 0
    nuevos_encontrados = 0
    
    with open(ARCHIVO_SALIDA, 'a', encoding='utf-8') as f_out:
        
        for i, juego in enumerate(lista):
            appid = juego.get('appid')
            
            # Verificar si el ID está en steam-top-games.json válido
            if appid not in ids_validos:
                print(f"[SKIP] [{i+1}/{total}] NO en lista válida: {appid}")
                saltados += 1
                continue
            
            # Verificar si ya está procesado
            if appid in ids_ya_procesados:
                print(f"[SKIP] [{i+1}/{total}] Ya procesado: {appid}")
                saltados += 1
                continue
            
            # Marcar como nueva entrada
            nuevos_encontrados += 1
            
            try:
                r = requests.get(f"{URL_DETALLES}?appids={appid}", params=PARAMS_BASE, timeout=10)
                status_code = r.status_code
                
                if status_code == 200:
                    d = r.json()
                    if d and str(appid) in d and d[str(appid)]['success']:
                        data = d[str(appid)]['data']
                        
                        # Obtener descripción larga y limpiar HTML
                        detailed_desc_raw = data.get('detailed_description', '')
                        detailed_desc_clean = limpiar_html_respetando_utf8(detailed_desc_raw).strip()
                        
                        # Si no hay descripción larga, saltar
                        if not detailed_desc_clean:
                            print(f"[SKIP] [{i+1}/{total}] Sin descripción: {data.get('name')}")
                            saltados += 1
                        else:
                            # Extraer solo ID, nombre y descripción larga
                            registro = {
                                "steam_id": int(appid),
                                "name": data.get('name'),
                                "detailed_description": detailed_desc_clean
                            }
                            
                            # Escribir NDJSON
                            f_out.write(json.dumps(registro, ensure_ascii=False) + "\n")
                            f_out.flush()
                            
                            print(f"[OK] [{i+1}/{total}] [NUEVO] {registro['name']}")
                            procesados += 1
                    else:
                        print(f"[SKIP] [{i+1}/{total}] No disponible: {appid}")
                        saltados += 1
                
                elif status_code == 429:
                    print("[WARN] RATE LIMIT. Pausando 60s...")
                    time.sleep(60)
                
            except Exception as e:
                print(f"[ERROR] [{i+1}/{total}] ID:{appid} | {e}")
            
            time.sleep(DELAY)
    
    print("-" * 60)
    print(f"[DONE] FINALIZADO.")
    print(f"[INFO] Nuevos encontrados: {nuevos_encontrados}")
    print(f"[INFO] Procesados: {procesados}")
    print(f"[INFO] Saltados/Duplicados: {saltados}")
    print(f"[INFO] Archivo guardado en: {ARCHIVO_SALIDA}")

if __name__ == "__main__":
    main()
