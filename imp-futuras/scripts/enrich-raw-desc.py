#!/usr/bin/env python3
"""
Enrich raw-desc.ndjson with genres and categories from steam-games-data.ndjson
"""

import json
import os

def main():
    # Define paths
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_desc_path = os.path.join(base_path, 'data', 'raw-desc.ndjson')
    games_data_path = os.path.join(base_path, '..', 'scraper', 'data', 'steam-games-data.ndjson')
    temp_path = os.path.join(base_path, 'data', '.raw-desc.tmp')
    
    print(f"[*] Leyendo datos de juegos desde: {games_data_path}")
    
    # Load game data into a dictionary keyed by steam_id
    games_dict = {}
    try:
        with open(games_data_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    game = json.loads(line)
                    steam_id = game.get('steam_id')
                    if steam_id:
                        games_dict[steam_id] = {
                            'genres': game.get('genres', []),
                            'categories': game.get('categories', [])
                        }
                except json.JSONDecodeError as e:
                    print(f"[WARN] Error en línea {line_num}: {e}")
    except FileNotFoundError:
        print(f"[ERROR] No se encontró {games_data_path}")
        return
    
    print(f"[OK] Cargados {len(games_dict)} juegos con datos de géneros y categorías")
    print(f"[*] Enriqueciendo {raw_desc_path}")
    
    # Process raw-desc and add genres/categories
    enriched_count = 0
    missing_count = 0
    
    with open(raw_desc_path, 'r', encoding='utf-8') as f_in, \
         open(temp_path, 'w', encoding='utf-8') as f_out:
        
        for line_num, line in enumerate(f_in, 1):
            if not line.strip():
                continue
            
            try:
                record = json.loads(line)
                steam_id = record.get('steam_id')
                
                if steam_id in games_dict:
                    record['genres'] = games_dict[steam_id]['genres']
                    record['categories'] = games_dict[steam_id]['categories']
                    enriched_count += 1
                else:
                    missing_count += 1
                    print(f"[WARN] steam_id {steam_id} no encontrado en steam-games-data")
                
                f_out.write(json.dumps(record, ensure_ascii=False) + '\n')
            except json.JSONDecodeError as e:
                print(f"[ERROR] Error en línea {line_num}: {e}")
    
    # Reemplazar archivo original con el temporal
    import shutil
    shutil.move(temp_path, raw_desc_path)
    
    print(f"\n[OK] Enriquecimiento completado:")
    print(f"    - Registros enriquecidos: {enriched_count}")
    print(f"    - Registros sin datos: {missing_count}")
    print(f"    - Archivo actualizado: {raw_desc_path}")

if __name__ == "__main__":
    main()
