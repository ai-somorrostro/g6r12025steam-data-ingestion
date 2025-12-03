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

def main():
    print(f"[*] INICIANDO EXTRACCIÓN DE DESCRIPCIONES")
    print(f"[*] Output: {ARCHIVO_SALIDA}")
    
    if not os.path.exists(ARCHIVO_ENTRADA):
        print(f"[ERROR] No encuentro '{ARCHIVO_ENTRADA}'.")
        return
    
    with open(ARCHIVO_ENTRADA, 'r', encoding='utf-8') as f:
        lista = json.load(f)
    
    if CANTIDAD_A_PROCESAR > 0:
        lista = lista[:CANTIDAD_A_PROCESAR]
    
    total = len(lista)
    print(f"[*] Procesando {total} juegos...")
    
    # Crear directorio de salida si no existe
    os.makedirs(os.path.dirname(ARCHIVO_SALIDA), exist_ok=True)
    
    # Limpiar archivo de salida
    with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
        pass
    
    # Escribir en modo append
    with open(ARCHIVO_SALIDA, 'a', encoding='utf-8') as f_out:
        
        for i, juego in enumerate(lista):
            appid = juego.get('appid')
            
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
                            
                            print(f"[OK] [{i+1}/{total}] {registro['name']}")
                    else:
                        print(f"[SKIP] [{i+1}/{total}] No disponible: {appid}")
                
                elif status_code == 429:
                    print("[WARN] RATE LIMIT. Pausando 60s...")
                    time.sleep(60)
                
            except Exception as e:
                print(f"[ERROR] [{i+1}/{total}] ID:{appid} | {e}")
            
            time.sleep(DELAY)
    
    print("-" * 60)
    print(f"[DONE] FINALIZADO. Archivo guardado en: {ARCHIVO_SALIDA}")

if __name__ == "__main__":
    main()
