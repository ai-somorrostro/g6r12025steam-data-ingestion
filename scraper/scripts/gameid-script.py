import requests
import json
import time
import logging
import sys
import os
from bs4 import BeautifulSoup

# Forzar que los prints se muestren inmediatamente (sin buffer)
sys.stdout.reconfigure(line_buffering=True)

# Obtener la ruta del directorio raíz del proyecto (un nivel arriba)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =================================================================
# CONFIGURACION
# =================================================================
logging.basicConfig(
    filename=os.path.join(PROJECT_ROOT, 'logs', 'scraper_metrics.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

URL_SEARCH = "https://store.steampowered.com/search/results/"
NOMBRE_ARCHIVO_SALIDA = os.path.join(PROJECT_ROOT, 'data', 'steam-top-games.json')

# 5000 de cada tipo para asegurar variedad
CANTIDAD_POR_CRITERIO = 5000 
RESULTADOS_POR_PAGINA = 50
TIMEOUT = 30
MAX_REINTENTOS = 3

# =================================================================
# FUNCION DE BUSQUEDA GENERICA
# =================================================================
def obtener_lista_steam(criterio_sort, total_objetivo, nombre_etapa):
    """
    criterio_sort: 
      - 'CCU_DESC' -> Mas Jugados (Trafico actual)
      - '' (vacio) -> Relevancia (Algoritmo de Steam: Ventas + Valoracion)
    """
    juegos_encontrados = {}
    offset = 0
    
    print(f"\n>>> [ETAPA]: {nombre_etapa} (Objetivo: {total_objetivo})")
    
    # Limite de seguridad para no entrar en bucle infinito
    limit_safety = total_objetivo * 2 
    
    while len(juegos_encontrados) < total_objetivo and offset < limit_safety:
        
        params = {
            'query': '',
            'start': offset,
            'count': RESULTADOS_POR_PAGINA,
            'sort_by': criterio_sort, # Aqui esta la clave
            'infinite': 1,
            'ignore_preferences': 1,
            'cc': 'us' # USA para estandarizar
        }

        # Intentos de conexion
        resp = None
        start_time = time.time()  # Inicio medición
        status_code = 0
        
        for _ in range(MAX_REINTENTOS):
            try:
                resp = requests.get(URL_SEARCH, params=params, timeout=TIMEOUT)
                status_code = resp.status_code
                if resp.status_code == 200: break
            except requests.exceptions.Timeout:
                logging.error(f"TIMEOUT | URL:{URL_SEARCH} | OFFSET:{offset}")
            except requests.exceptions.RequestException as e:
                logging.error(f"CONNECTION_ERROR | URL:{URL_SEARCH} | ERROR:{str(e)}")
                time.sleep(1)
        
        end_time = time.time()
        duration = round(end_time - start_time, 4)
        
        # Log de la petición
        if resp:
            logging.info(f"REQUEST_URL:{resp.url} | STATUS:{status_code} | LATENCY:{duration}s | OFFSET:{offset}")
        
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                soup = BeautifulSoup(data.get('results_html', ''), 'html.parser')
                rows = soup.find_all('a', class_='search_result_row')
                
                if not rows:
                    print("[WARN] Fin de resultados en Steam.")
                    break

                for row in rows:
                    if len(juegos_encontrados) >= total_objetivo: break
                    
                    appid = row.get('data-ds-appid')
                    title = row.find('span', class_='title').text.strip()
                    
                    if appid:
                        # A veces vienen ids dobles "123,456", cogemos el primero
                        first_id = appid.split(',')[0]
                        juegos_encontrados[first_id] = title
                
                print(f"   [OK] Offset {offset}: Acumulados {len(juegos_encontrados)} juegos en esta etapa.")
                
            except Exception as e:
                logging.error(f"PARSE_ERROR | OFFSET:{offset} | ERROR:{e}")
        
        else:
            print(f"[ERR] Error conexion o bloqueo. Esperando 5s...")
            time.sleep(5)

        offset += RESULTADOS_POR_PAGINA
        time.sleep(1.0) # Pausa para no ser baneado

    return juegos_encontrados

# =================================================================
# EJECUCION
# =================================================================
if __name__ == "__main__":
    diccionario_maestro = {}

    # --- FASE 1: LOS MAS JUGADOS (Tendencia y Multijugador) ---
    # Captura: CS2, Dota, Apex, juegos virales del momento.
    top_played = obtener_lista_steam('CCU_DESC', CANTIDAD_POR_CRITERIO, "Mas Jugados (Trends)")
    diccionario_maestro.update(top_played)
    
    print(f"[INFO] Total tras Fase 1: {len(diccionario_maestro)} juegos unicos.")

    # --- FASE 2: RELEVANCIA (Historicos y Calidad) ---
    # Al dejar sort_by vacio, Steam usa su algoritmo de "Relevancia".
    # Captura: Witcher 3, Skyrim, Portal, Red Dead Redemption 2 (Juegos que venden siempre).
    top_relevance = obtener_lista_steam('', CANTIDAD_POR_CRITERIO, "Por Relevancia (Iconicos)")
    
    # Fusionar (El diccionario evita duplicados automaticamente)
    antes = len(diccionario_maestro)
    diccionario_maestro.update(top_relevance)
    despues = len(diccionario_maestro)
    
    print(f"[INFO] Se anadieron {despues - antes} juegos iconicos que no estaban en el Top Jugados.")
    print(f"[INFO] TOTAL FINAL: {despues} JUEGOS UNICOS.")

    # --- GUARDAR ---
    lista_final = [{"appid": int(aid), "name": name} for aid, name in diccionario_maestro.items()]
    
    with open(NOMBRE_ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=4)

    print(f"\n[DONE] Guardado en: {NOMBRE_ARCHIVO_SALIDA}")