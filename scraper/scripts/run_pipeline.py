#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pipeline de scraping de Steam
Ejecuta dos scripts en secuencia:
  1. gameid-script.py  -> Obtiene lista de IDs de juegos populares
  2. sacar-datos-games.py -> Obtiene detalles completos de cada juego

Si el primer script falla, el segundo no se ejecuta.
"""

import subprocess
import sys
import os
from datetime import datetime

# =================================================================
# CONFIGURACIÓN
# =================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXECUTABLE = sys.executable  # Usa el mismo Python que ejecuta este script

# Scripts a ejecutar en orden
SCRIPTS = [
    {
        "nombre": "gameid-script.py",
        "descripcion": "Descarga de IDs de juegos populares",
        "archivo_salida": "/home/g6/reto/scraper/data/steam-top-games.json"
    },
    {
        "nombre": "sacar-datos-games.py", 
        "descripcion": "Descarga de datos completos de juegos",
        "archivo_salida": "/home/g6/reto/scraper/data/steam-games-data.ndjson"
    }
]

# =================================================================
# FUNCIONES
# =================================================================

def log(mensaje, tipo="INFO"):
    """Imprime mensaje con timestamp y tipo"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    simbolo = {
        "INFO": "•",
        "SUCCESS": "✓",
        "ERROR": "✗",
        "WARNING": "!",
        "START": "►"
    }.get(tipo, "•")
    print(f"[{timestamp}] {simbolo} {mensaje}")

def verificar_archivo(ruta):
    """Verifica si un archivo existe"""
    if not os.path.exists(ruta):
        return False, f"No se encontró el archivo: {ruta}"
    return True, None

def ejecutar_script(script_info):
    """
    Ejecuta un script Python y retorna si fue exitoso
    Muestra el output en tiempo real línea por línea
    """
    nombre = script_info["nombre"]
    descripcion = script_info["descripcion"]
    ruta_completa = os.path.join(SCRIPT_DIR, nombre)
    
    # Verificar que el script existe
    existe, error = verificar_archivo(ruta_completa)
    if not existe:
        log(error, "ERROR")
        return False
    
    log(f"Iniciando: {descripcion}", "START")
    log(f"Ejecutando: {nombre}", "INFO")
    print("-" * 70)
    
    try:
        # Ejecutar el script con output en tiempo real
        # -u fuerza unbuffered output para ver el progreso inmediatamente
        proceso = subprocess.Popen(
            [PYTHON_EXECUTABLE, "-u", ruta_completa],
            cwd=SCRIPT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combinar stderr con stdout
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,  # Buffer de línea
            universal_newlines=True
        )
        
        # Mostrar output en tiempo real línea por línea
        for linea in proceso.stdout:
            print(linea, end='')  # Ya viene con \n
            sys.stdout.flush()  # Forzar que se muestre inmediatamente
        
        # Esperar a que termine el proceso
        proceso.wait()
        returncode = proceso.returncode
        
        print("-" * 70)
        
        # Verificar código de salida
        if returncode != 0:
            log(f"El script falló con código de salida: {returncode}", "ERROR")
            return False
        
        # Verificar que se generó el archivo de salida esperado (si aplica)
        if "archivo_salida" in script_info:
            archivo_salida = os.path.join(SCRIPT_DIR, script_info["archivo_salida"])
            existe, error = verificar_archivo(archivo_salida)
            if not existe:
                log(f"Advertencia: No se generó el archivo esperado: {script_info['archivo_salida']}", "WARNING")
                # No lo consideramos un error crítico, algunos scripts pueden no generar salida
            else:
                tamaño = os.path.getsize(archivo_salida)
                log(f"Archivo generado: {script_info['archivo_salida']} ({tamaño:,} bytes)", "SUCCESS")
        
        log(f"Completado exitosamente: {nombre}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"Error al ejecutar {nombre}: {str(e)}", "ERROR")
        return False

# =================================================================
# MAIN
# =================================================================

def main():
    """Ejecuta el pipeline completo"""
    log("=" * 70, "INFO")
    log("PIPELINE DE SCRAPING DE STEAM", "START")
    log("=" * 70, "INFO")
    log(f"Directorio de trabajo: {SCRIPT_DIR}", "INFO")
    log(f"Python: {PYTHON_EXECUTABLE}", "INFO")
    log(f"Scripts a ejecutar: {len(SCRIPTS)}", "INFO")
    log("=" * 70, "INFO")
    
    inicio_total = datetime.now()
    scripts_exitosos = 0
    
    for i, script in enumerate(SCRIPTS, 1):
        log(f"\n[{i}/{len(SCRIPTS)}] {script['descripcion']}", "INFO")
        log("-" * 70, "INFO")
        
        inicio = datetime.now()
        exito = ejecutar_script(script)
        fin = datetime.now()
        duracion = (fin - inicio).total_seconds()
        
        log(f"Duración: {duracion:.2f} segundos", "INFO")
        
        if not exito:
            log(f"\n❌ PIPELINE DETENIDO: Falló el script {i}/{len(SCRIPTS)}", "ERROR")
            log(f"No se ejecutarán los {len(SCRIPTS) - i} scripts restantes", "WARNING")
            return 1  # Código de error
        
        scripts_exitosos += 1
        log("-" * 70, "INFO")
    
    # Resumen final
    fin_total = datetime.now()
    duracion_total = (fin_total - inicio_total).total_seconds()
    
    log("\n" + "=" * 70, "INFO")
    log("PIPELINE COMPLETADO EXITOSAMENTE", "SUCCESS")
    log("=" * 70, "INFO")
    log(f"Scripts ejecutados: {scripts_exitosos}/{len(SCRIPTS)}", "SUCCESS")
    log(f"Duración total: {duracion_total:.2f} segundos ({duracion_total/60:.2f} minutos)", "INFO")
    log("=" * 70, "INFO")
    
    return 0  # Código de éxito

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log("\n\nPipeline interrumpido por el usuario (Ctrl+C)", "WARNING")
        sys.exit(130)
    except Exception as e:
        log(f"\n\nError inesperado en el pipeline: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
