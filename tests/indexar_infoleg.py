"""
Indexa la base InfoLeg (legislación nacional) en Qdrant Cloud.
Usa la key de testing para no consumir cuota de producción.
"""
import sys, os
sys.path.insert(0, 'L:/JusticiaArgentina/src')

from dotenv import load_dotenv
load_dotenv('L:/JusticiaArgentina/.env')

# Usar key de testing para embeddings
os.environ['GEMINI_API_KEY'] = 'AIzaSyDwQp6HcIiqamO0KFeiexL2T560-zvw0_w'

from indexador.infoleg_qdrant import IndexadorInfoLegQdrant

CSV_PATH = 'L:/JusticiaArgentina/datos/base-infoleg-normativa-nacional.csv'
MAX_REGISTROS = 200  # Empezamos con 200 para no agotar cuota de embeddings

print('=' * 55)
print('INDEXANDO InfoLeg en Qdrant Cloud')
print(f'Archivo: {CSV_PATH}')
print(f'Máximo: {MAX_REGISTROS} registros')
print('=' * 55)

try:
    idx = IndexadorInfoLegQdrant()
    idx.indexar(csv_path=CSV_PATH, max_registros=MAX_REGISTROS)
    print('\nIndexación completada.')
except Exception as e:
    print(f'Error: {e}')
    import traceback; traceback.print_exc()
