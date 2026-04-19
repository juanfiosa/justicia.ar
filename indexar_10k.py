"""Script para indexar 10k docs SAIJ con throttling correcto."""
import sys, os
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv('.env')

from indexador.pipeline_qdrant import IndexadorJurisprudenciaQdrant

print("Iniciando indexado de 10k docs...")
idx = IndexadorJurisprudenciaQdrant()
n = idx.indexar_dataset(
    'datos/jurisprudencia_saij/dataset.jsonl',
    max_registros=10000,
    checkpoint_path='datos/checkpoint_saij.json'
)
print(f"\nFinalizado: {n} docs indexados")
print("Estadísticas:", idx.estadisticas())
