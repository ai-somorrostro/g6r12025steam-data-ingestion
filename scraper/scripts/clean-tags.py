#!/usr/bin/env python3
"""
Script para limpiar tags irrelevantes de steam-games-data.ndjson.
Elimina tags basura como "cromos de steam", "nube", "ajustes de sonido", etc.
Mantiene solo tags relevantes para búsqueda semántica (género, temática, mecánicas).
"""

import json
import os
from pathlib import Path

# Tags a eliminar (basura/metadatos Steam no relevantes)
TAGS_BASURA = {
    # Logros y cromos (91.9% y 76.6% de los juegos)
    "logros de steam", "steam achievements", "cromos de steam", "steam cards", 
    "steam trading cards", "tarjetas intercambiables de steam", "logros",
    "trading cards", "tarjetas intercambiables",
    
    # Almacenamiento y sincronización (85.2% y 62.4%)
    "préstamo familiar", "steam cloud", "cloud save", "cloud saves", "nube",
    "sincronización con la nube",
    
    # Controladores y dispositivos (45.1% y 19.0%)
    "compat. total con mando", "compat. parcial con mando", 
    "soporte total de controles", "full controller support",
    "compatible with steam controller", "gamepad", "controller",
    "detección de mov. en mando",
    
    # Audio (27.6%, 15.3%, 12.8%)
    "controles de volumen personalizados",
    "ajustes de sonido", "configuración de audio", 
    "audio adicional de alta calidad",
    
    # Accesibilidad (múltiples)
    "jugable sin eventos rápidos",
    "guardar en cualquier momento",
    "alternativas de color", "tamaño del texto ajustable",
    "opción solo ratón", "opción solo teclado", "opción solo táctil",
    "opciones de subtítulos", "subtítulos disponibles",
    "chat de voz convertido a texto", "chat de texto convertido a voz",
    "menús narrados",
    
    # Steam Features (múltiples porcentajes altos)
    "steam workshop", "workshop",
    "tablas de clasificación de steam", "estadísticas",
    "contenido descargable",
    "con sist. antitrampas de valve",
    "steam timeline",
    "notificaciones de turnos de steam",
    "incluye el sdk de source",
    "coleccionables de steamvr",
    
    # Remote Play (10.6%, 10.2%, 9.5%)
    "remote play en tableta", "remote play together",
    "remote play en tv", "remote play en móvil",
    
    # HDR y VR
    "hdr disponible", "compatible con rv", "compatibilidad con rv",
    "solo para rv",
    
    # Características técnicas Steam genéricas
    "steam community", "comunidad steam",
}

# Tags relevantes que SÍ queremos mantener (ejemplos de patrones)
TAGS_RELEVANTES_PATRONES = {
    # Géneros principales
    "action", "acción", "adventure", "aventura", "rpg", "rts", "strategy", "estrategia",
    "puzzle", "puzle", "platformer", "plataforma", "racing", "carreras", "sports", "deportes",
    "simulation", "simulador", "shooter", "disparos", "fighting", "lucha", "horror", "terror",
    "indie", "casual", "educational", "educativo",
    # Temáticas
    "fantasy", "fantasía", "sci-fi", "ciencia ficción", "medieval", "steampunk", "cyberpunk",
    "post-apocalyptic", "post-apocalíptico", "survival", "supervivencia", "detective",
    "mystery", "misterio", "psychological", "psicológico", "noir", "western", "historic",
    "histórico", "space", "espacio", "underwater", "submarino",
    # Mecánicas gameplay
    "turn-based", "por turnos", "real-time", "tiempo real", "sandbox", "open world",
    "mundo abierto", "crafting", "artesanía", "building", "construcción", "base building",
    "farming", "agricultura", "fishing", "pesca", "stealth", "sigilo", "parkour",
    "puzzle-solving", "resolución de puzles", "time management", "gestión de tiempo",
    # Características de juego
    "story-rich", "rico en historia", "narrative", "narrativa", "choice-driven",
    "driven by choice", "impulsado por elecciones", "romance", "romance", "exploration",
    "exploración", "boss battles", "batallas contra jefes", "dungeons", "mazmorras",
    "vr", "realidad virtual", "virtual reality",
    # Modalidades
    "singleplayer", "jugador único", "player vs player", "pvp", "team-based",
    "basado en equipos", "asynchronous", "asincrónico",
}

def limpiar_tags(tags_list):
    """
    Limpia una lista de tags eliminando solo los que están en la lista negra.
    
    Args:
        tags_list: Lista de strings con tags
    
    Returns:
        Lista de tags sin los elementos de la lista negra
    """
    if not tags_list:
        return []
    
    tags_limpios = []
    
    for tag in tags_list:
        tag_lower = tag.lower().strip()
        
        # Solo saltar si está en lista negra
        if tag_lower in TAGS_BASURA:
            continue
        
        # Mantener todos los demás
        tags_limpios.append(tag)
    
    return tags_limpios


def procesar_archivo(ruta_entrada, ruta_salida, ruta_backup=None):
    """
    Procesa archivo NDJSON limpiando tags irrelevantes.
    
    Args:
        ruta_entrada: Ruta al archivo original
        ruta_salida: Ruta al archivo limpio
        ruta_backup: (Opcional) Ruta para backup automático
    """
    
    if not os.path.exists(ruta_entrada):
        print(f"[ERROR] No existe {ruta_entrada}")
        return False
    
    # Crear backup si se especifica
    if ruta_backup and not os.path.exists(ruta_backup):
        import shutil
        shutil.copy2(ruta_entrada, ruta_backup)
        print(f"[OK] Backup creado: {ruta_backup}")
    
    juegos_procesados = 0
    juegos_sin_cambios = 0
    juegos_modificados = 0
    
    try:
        # Procesar línea por línea
        with open(ruta_entrada, 'r', encoding='utf-8') as f_in, \
             open(ruta_salida, 'w', encoding='utf-8') as f_out:
            
            for linea in f_in:
                try:
                    juego = json.loads(linea)
                    juegos_procesados += 1
                    
                    # Limpiar categories si existen
                    if 'categories' in juego and juego['categories']:
                        tags_originales = len(juego['categories'])
                        juego['categories'] = limpiar_tags(juego['categories'])
                        tags_nuevos = len(juego['categories'])
                        
                        if tags_originales != tags_nuevos:
                            juegos_modificados += 1
                        else:
                            juegos_sin_cambios += 1
                    else:
                        juegos_sin_cambios += 1
                    
                    # Escribir línea procesada
                    f_out.write(json.dumps(juego, ensure_ascii=False) + '\n')
                    
                except json.JSONDecodeError as e:
                    print(f"[WARN]  Error JSON en línea {juegos_procesados}: {e}")
                    continue
        
        print(f"\n[INFO] Procesamiento completado:")
        print(f"Juegos procesados: {juegos_procesados}")
        print(f"Juegos modificados: {juegos_modificados}")
        print(f"Sin cambios: {juegos_sin_cambios}")
        print(f"Output: {ruta_salida}")
        
        return True
        
    except Exception as e:
        print(f"Error al procesar archivo: {e}")
        return False


if __name__ == '__main__':
    # Rutas
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / 'data'
    backup_dir = script_dir.parent / 'backups'
    
    ruta_original = data_dir / 'steam-games-data.ndjson'
    ruta_limpia = data_dir / 'steam-games-data.ndjson'
    ruta_backup = backup_dir / 'steam-games-data-backup.ndjson'
    
    print("🧹 Limpiador de Categories Irrelevantes")
    print("=" * 50)
    print(f"Entrada: {ruta_original}")
    print(f"Backup: {ruta_backup}")
    print("=" * 50)
    
    # Crear archivo temporal para no sobrescribir durante procesamiento
    ruta_temp = data_dir / 'steam-games-data.ndjson.tmp'
    
    # Procesar a archivo temporal
    if procesar_archivo(str(ruta_original), str(ruta_temp), str(ruta_backup)):
        # Reemplazar original con limpio
        import shutil
        shutil.move(str(ruta_temp), str(ruta_limpia))
        print(f"\n[OK] Archivo original actualizado: {ruta_limpia}")
    else:
        # Limpiar temporal en caso de error
        if ruta_temp.exists():
            ruta_temp.unlink()
        print("[ERROR] Error: No se procesó el archivo")
