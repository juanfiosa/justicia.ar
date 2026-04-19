"""Indexa todas las normas InfoLeg en Qdrant Cloud."""
import sys, os
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv('.env')

from indexador.infoleg_qdrant import IndexadorInfoLegQdrant

print("Iniciando indexado InfoLeg (todas las normas)...")
idx = IndexadorInfoLegQdrant()
n = idx.indexar(
    csv_path='datos/base-infoleg-normativa-nacional.csv',
    solo_prioritarios=False,   # todas, no solo Leyes/Decretos
    max_registros=None
)
print(f"\nFinalizado: {n} normas indexadas")
