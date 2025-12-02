from sentence_transformers import SentenceTransformer
import os
import sys

CACHE_DIR = os.path.expanduser('~/.cache/huggingface/hub')
MODEL_CACHE_DIR = os.path.join(CACHE_DIR, 'models--sentence-transformers--paraphrase-multilingual-mpnet-base-v2')

# Si el modelo ya está instalado en caché, salir con error
if os.path.isdir(MODEL_CACHE_DIR):
	print(f"[WARN] El modelo ya está instalado en caché: {MODEL_CACHE_DIR}")
	sys.exit(1)

print("Iniciando descarga del modelo 'paraphrase-multilingual-mpnet-base-v2'...")
print("Esto puede tardar un poco (aprox 400-500 MB)...")

# Al ejecutar esta línea, Python busca el modelo en caché. Si no está, lo descarga.
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
print("[OK] ¡Modelo descargado e instalado correctamente!")
print(f"Ubicación del caché: {os.path.expanduser('~/.cache/huggingface/hub/')}")