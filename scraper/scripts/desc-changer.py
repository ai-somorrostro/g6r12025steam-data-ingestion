import json
import os
import sys

# Forzar que los prints se muestren inmediatamente (sin buffer)
sys.stdout.reconfigure(line_buffering=True)

# Obtener la ruta del directorio raíz del proyecto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración de archivos
ARCHIVO_SUMMARY = os.path.join(PROJECT_ROOT, 'imp-futuras', 'data', 'summary.ndjson')
ARCHIVO_STEAM_DATA = os.path.join(PROJECT_ROOT, 'scraper', 'data', 'steam-games-data.ndjson')
ARCHIVO_BACKUP = os.path.join(PROJECT_ROOT, 'scraper', 'backups', 'steam-games-data-backup.ndjson')

def main():
    print(f"[*] INICIANDO REEMPLAZO DE DESCRIPCIONES")
    print(f"[*] Summary source: {ARCHIVO_SUMMARY}")
    print(f"[*] Steam data target: {ARCHIVO_STEAM_DATA}")
    print(f"[*] Backup target: {ARCHIVO_BACKUP}")
    
    # Verificar que existen los archivos
    if not os.path.exists(ARCHIVO_SUMMARY):
        print(f"[ERROR] No se encuentra '{ARCHIVO_SUMMARY}'")
        return
    
    if not os.path.exists(ARCHIVO_STEAM_DATA):
        print(f"[ERROR] No se encuentra '{ARCHIVO_STEAM_DATA}'")
        return
    
    # Cargar resúmenes de summary.ndjson en un diccionario {steam_id: summary}
    print("\n[*] Cargando resúmenes de summary.ndjson...")
    summaries = {}
    
    with open(ARCHIVO_SUMMARY, 'r', encoding='utf-8') as f:
        for linea in f:
            try:
                doc = json.loads(linea)
                steam_id = doc.get('steam_id')
                summary = doc.get('summary')
                if steam_id and summary:
                    summaries[steam_id] = summary
            except:
                pass
    
    print(f"[OK] {len(summaries)} resúmenes cargados")
    
    # Cargar y procesar steam-games-data.ndjson
    print("\n[*] Cargando steam-games-data.ndjson...")
    steam_data = []
    
    with open(ARCHIVO_STEAM_DATA, 'r', encoding='utf-8') as f:
        for linea in f:
            try:
                doc = json.loads(linea)
                steam_data.append(doc)
            except:
                pass
    
    print(f"[OK] {len(steam_data)} entradas cargadas")
    
    # Comparar y reemplazar
    print("\n[*] Comparando IDs y reemplazando descripciones...")
    reemplazos = 0
    sin_cambios = 0
    
    for juego in steam_data:
        steam_id = juego.get('steam_id')
        
        if steam_id in summaries:
            # Reemplazar detailed_description con el summary
            juego['detailed_description'] = summaries[steam_id]
            reemplazos += 1
            print(f"[UPDATED] {steam_id} - {juego.get('name', 'Unknown')}")
        else:
            sin_cambios += 1
    
    # Crear backup
    print(f"\n[*] Creando backup de steam-games-data.ndjson...")
    with open(ARCHIVO_BACKUP, 'w', encoding='utf-8') as f:
        with open(ARCHIVO_STEAM_DATA, 'r', encoding='utf-8') as f_orig:
            f.write(f_orig.read())
    print(f"[OK] Backup guardado en: {ARCHIVO_BACKUP}")
    
    # Guardar el archivo actualizado
    print(f"\n[*] Guardando archivo actualizado...")
    with open(ARCHIVO_STEAM_DATA, 'w', encoding='utf-8') as f:
        for juego in steam_data:
            f.write(json.dumps(juego, ensure_ascii=False) + "\n")
    
    print(f"[OK] Archivo actualizado guardado")
    
    # Resumen
    print("\n" + "="*60)
    print(f"[DONE] PROCESO COMPLETADO")
    print(f"[INFO] Total de entradas: {len(steam_data)}")
    print(f"[INFO] Descripciones reemplazadas: {reemplazos}")
    print(f"[INFO] Sin cambios: {sin_cambios}")
    print(f"[INFO] Backup creado en: {ARCHIVO_BACKUP}")
    print("="*60)

if __name__ == "__main__":
    main()
