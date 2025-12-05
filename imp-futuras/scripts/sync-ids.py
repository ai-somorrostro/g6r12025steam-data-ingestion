import json
import os
import sys

# Forzar que los prints se muestren inmediatamente (sin buffer)
sys.stdout.reconfigure(line_buffering=True)

# Obtener la ruta del directorio raíz del proyecto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración de archivos
ARCHIVO_STEAM = os.path.join(PROJECT_ROOT, 'scraper', 'data', 'steam-top-games.json')
ARCHIVO_RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw-desc.ndjson')
ARCHIVO_RAW_BACKUP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw-desc-backup.ndjson')

def main():
    print(f"[*] SINCRONIZANDO IDs ENTRE ARCHIVOS")
    print(f"[*] Steam IDs desde: {ARCHIVO_STEAM}")
    print(f"[*] Raw descriptions: {ARCHIVO_RAW}")
    
    # Verificar que existen los archivos
    if not os.path.exists(ARCHIVO_STEAM):
        print(f"[ERROR] No se encuentra '{ARCHIVO_STEAM}'")
        return
    
    if not os.path.exists(ARCHIVO_RAW):
        print(f"[ERROR] No se encuentra '{ARCHIVO_RAW}'")
        return
    
    # Cargar IDs de steam-top-games.json
    print("\n[*] Cargando IDs de steam-top-games.json...")
    with open(ARCHIVO_STEAM, 'r', encoding='utf-8') as f:
        steam_data = json.load(f)
    
    steam_ids = set(juego.get('appid') for juego in steam_data if juego.get('appid'))
    print(f"[OK] {len(steam_ids)} IDs cargados desde steam-top-games.json")
    
    # Cargar entradas de raw-desc.ndjson
    print("\n[*] Cargando entradas de raw-desc.ndjson...")
    raw_entries = []
    raw_ids = set()
    
    with open(ARCHIVO_RAW, 'r', encoding='utf-8') as f:
        for linea in f:
            try:
                doc = json.loads(linea)
                steam_id = doc.get('steam_id')
                raw_entries.append(doc)
                if steam_id:
                    raw_ids.add(steam_id)
            except:
                pass
    
    print(f"[OK] {len(raw_entries)} entradas cargadas desde raw-desc.ndjson")
    
    # Comparar IDs
    ids_a_eliminar = raw_ids - steam_ids
    ids_validos = raw_ids & steam_ids
    
    print(f"\n[INFO] Estadísticas:")
    print(f"  IDs en steam-top-games.json: {len(steam_ids)}")
    print(f"  IDs en raw-desc.ndjson: {len(raw_ids)}")
    print(f"  IDs válidos (en ambos): {len(ids_validos)}")
    print(f"  IDs a eliminar: {len(ids_a_eliminar)}")
    
    if ids_a_eliminar:
        print(f"\n[*] IDs a eliminar:")
        for steam_id in sorted(ids_a_eliminar):
            print(f"  - {steam_id}")
        
        # Crear backup
        print(f"\n[*] Creando backup de raw-desc.ndjson...")
        with open(ARCHIVO_RAW_BACKUP, 'w', encoding='utf-8') as f:
            for doc in raw_entries:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        print(f"[OK] Backup guardado en: {ARCHIVO_RAW_BACKUP}")
        
        # Filtrar y guardar
        print(f"\n[*] Filtrando raw-desc.ndjson...")
        raw_filtrado = [doc for doc in raw_entries if doc.get('steam_id') in steam_ids]
        
        with open(ARCHIVO_RAW, 'w', encoding='utf-8') as f:
            for doc in raw_filtrado:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        
        print(f"[OK] raw-desc.ndjson actualizado")
        print(f"[INFO] Entradas antes: {len(raw_entries)}")
        print(f"[INFO] Entradas después: {len(raw_filtrado)}")
        print(f"[INFO] Entradas eliminadas: {len(ids_a_eliminar)}")
    else:
        print(f"\n[OK] No hay IDs para eliminar. Archivos sincronizados.")
    
    print("\n[DONE] Sincronización completada.")

if __name__ == "__main__":
    main()
