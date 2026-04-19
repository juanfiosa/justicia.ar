"""
Indexa el dataset SAIJ de jurisprudencia en Qdrant Cloud.
Usa la API key de testing para no consumir cuota de producción.
"""
import os
import sys
from pathlib import Path

# API key de testing (proyecto separado)
os.environ['GEMINI_API_KEY'] = 'AIzaSyDwQp6HcIiqamO0KFeiexL2T560-zvw0_w'
os.environ['QDRANT_URL'] = 'https://6da9fe5d-d90c-4214-8668-2d4e4f952dee.sa-east-1-0.aws.cloud.qdrant.io'
os.environ['QDRANT_API_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.HkXTBhLkSpgtuiAS_AtxeCYL8FC8YH3HZLCHZTEJ7A4'

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from indexador.pipeline_qdrant import IndexadorJurisprudenciaQdrant

DATASET = str(Path(__file__).parent.parent / 'datos' / 'jurisprudencia_saij' / 'dataset.jsonl')
CHECKPOINT = str(Path(__file__).parent.parent / 'datos' / 'checkpoint_saij.json')

print(f"Dataset: {DATASET}")
print(f"Checkpoint: {CHECKPOINT}")
print("=" * 50)

indexador = IndexadorJurisprudenciaQdrant()
total = indexador.indexar_dataset(DATASET, checkpoint_path=CHECKPOINT)

print("=" * 50)
print(f"COMPLETADO: {total} documentos indexados en Qdrant")
print("\nEstadísticas por colección:")
stats = indexador.estadisticas()
for col, count in stats.items():
    print(f"  {col}: {count} docs")
