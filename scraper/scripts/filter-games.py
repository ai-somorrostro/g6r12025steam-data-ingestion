import json
import os
import sys

# Forzar que los prints se muestren inmediatamente (sin buffer)
sys.stdout.reconfigure(line_buffering=True)

# Obtener la ruta del directorio raíz del proyecto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración de archivos
ARCHIVO_ENTRADA = os.path.join(PROJECT_ROOT, 'scraper', 'data', 'steam-top-games.json')
ARCHIVO_SALIDA = os.path.join(PROJECT_ROOT, 'scraper', 'data', 'steam-top-games-filtered.json')
ARCHIVO_BACKUP = os.path.join(PROJECT_ROOT, 'scraper', 'backups', 'steam-top-games-backup.json')

# ==========================================
# PALABRAS CLAVE A FILTRAR
# ==========================================
# Añade aquí las palabras clave que quieras filtrar (no importa mayúsculas/minúsculas)
PALABRAS_CLAVE_FILTRO = [
    "soundtrack",
    "artbook",
    "soundtrack",
    "dlc",
    "expansion",
    "cosmetic",
    "cosmetics",
    "bundle",
    "bundle pack",
    "season pass",
    "adult",
    "sexual",
    "xxx",
]

def contiene_palabra_clave(nombre):
    """
    Verifica si el nombre contiene alguna palabra clave del filtro
    """
    nombre_lower = nombre.lower()
    for palabra in PALABRAS_CLAVE_FILTRO:
        if palabra.lower() in nombre_lower:
            return True
    return False

def main():
    print(f"[*] INICIANDO FILTRADO DE JUEGOS")
    print(f"[*] Entrada: {ARCHIVO_ENTRADA}")
    print(f"[*] Salida: {ARCHIVO_SALIDA}")
    print(f"[*] Backup: {ARCHIVO_BACKUP}")
    print(f"\n[INFO] Palabras clave a filtrar ({len(PALABRAS_CLAVE_FILTRO)}):")
    for palabra in PALABRAS_CLAVE_FILTRO:
        print(f"  - {palabra}")
    print()
    
    # Verificar que el archivo existe
    if not os.path.exists(ARCHIVO_ENTRADA):
        print(f"[ERROR] No se encuentra '{ARCHIVO_ENTRADA}'")
        return
    
    # Cargar JSON
    print("[*] Cargando archivo...")
    with open(ARCHIVO_ENTRADA, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    
    total_original = len(datos)
    print(f"[*] Total de juegos cargados: {total_original}")
    
    # Filtrar juegos
    print("[*] Filtrando juegos...")
    juegos_filtrados = []
    juegos_eliminados = []
    
    for juego in datos:
        nombre = juego.get('name', '')
        if contiene_palabra_clave(nombre):
            juegos_eliminados.append(juego)
            print(f"[REMOVE] {nombre}")
        else:
            juegos_filtrados.append(juego)
    
    total_eliminados = len(juegos_eliminados)
    total_restantes = len(juegos_filtrados)
    
    print("-" * 60)
    print(f"[DONE] Filtrado completado:")
    print(f"  Total original: {total_original}")
    print(f"  Eliminados: {total_eliminados}")
    print(f"  Restantes: {total_restantes}")
    
    # Crear backup del original
    print(f"\n[*] Creando backup...")
    with open(ARCHIVO_BACKUP, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print(f"[OK] Backup guardado en: {ARCHIVO_BACKUP}")
    
    # Guardar juegos filtrados directamente en el archivo original
    print(f"[*] Reemplazando archivo original...")
    with open(ARCHIVO_ENTRADA, 'w', encoding='utf-8') as f:
        json.dump(juegos_filtrados, f, ensure_ascii=False, indent=2)
    print(f"[OK] Archivo original actualizado: {ARCHIVO_ENTRADA}")
    
    print(f"\n[INFO] ✓ El archivo original ha sido actualizado con {total_restantes} juegos")
    print(f"[INFO] ✓ Backup del original guardado en: {ARCHIVO_BACKUP}")

if __name__ == "__main__":
    main()
