"""
INDEXADOR INFOLEG — QDRANT
============================
Indexa legislación nacional (InfoLeg) en Qdrant Cloud.
"""

import os
import sys
import csv
import json
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / '.env')

from indexador.qdrant_store import (
    get_qdrant_client,
    embed_textos, embed_query,
    crear_coleccion_si_no_existe,
    QuotaExhaustedError
)

try:
    from qdrant_client.models import PointStruct
except ImportError:
    pass

COLECCION = "legislacion_nacional"
BATCH_SIZE = 50

KEYWORDS_RAMA = {
    'civil_comercial': ['civil', 'comercial', 'contrato', 'sociedad', 'familia', 'sucesion', 'propiedad'],
    'penal': ['penal', 'delito', 'crimen', 'pena', 'procesado', 'imputado'],
    'laboral': ['laboral', 'trabajo', 'empleo', 'sindical', 'obrero', 'salario', 'despido'],
    'administrativo': ['administrativo', 'estado', 'servicio publico', 'concesion', 'licitacion'],
    'tributario': ['tributario', 'impuesto', 'fiscal', 'afip', 'iva', 'ganancias', 'tasa'],
    'constitucional': ['constitucional', 'derechos', 'garantias', 'amparo', 'habeas'],
    'procesal': ['procesal', 'proceso', 'procedimiento', 'recurso', 'apelacion'],
}


def clasificar_norma_rama(titulo: str, tipo: str) -> str:
    titulo_lower = (titulo or '').lower()
    for rama, kws in KEYWORDS_RAMA.items():
        if any(kw in titulo_lower for kw in kws):
            return rama
    return 'general'


class IndexadorInfoLegQdrant:
    """Indexa y busca legislación InfoLeg en Qdrant Cloud"""

    def __init__(self):
        self.client = get_qdrant_client()
        self.disponible = self.client is not None
        if not self.disponible:
            raise RuntimeError("Faltan credenciales Qdrant")

    def indexar(self, csv_path: str = None, solo_prioritarios: bool = False,
                max_registros: int = None, checkpoint_path: str = None):
        """Indexa el CSV de InfoLeg con soporte de checkpoint."""
        if csv_path is None:
            csv_path = str(Path(__file__).parent.parent.parent /
                          'datos' / 'base-infoleg-normativa-nacional.csv')
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV no encontrado: {csv_path}")

        # Cargar checkpoint si existe
        cp_path = Path(checkpoint_path) if checkpoint_path else None
        fila_inicio = 0
        indexados = 0
        if cp_path and cp_path.exists():
            with open(cp_path, 'r', encoding='utf-8') as f:
                cp = json.load(f)
            fila_inicio = cp.get('fila', 0)
            indexados = cp.get('indexados', 0)
            print(f"Retomando InfoLeg desde fila {fila_inicio} ({indexados} ya indexados)")
        else:
            print(f"Indexando InfoLeg en Qdrant Cloud...")

        crear_coleccion_si_no_existe(self.client, COLECCION)

        total = 0
        buffer = []

        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for num_fila, row in enumerate(reader):
                if num_fila < fila_inicio:
                    continue
                if max_registros and (num_fila - fila_inicio) >= max_registros:
                    break

                tipo = row.get('tipo_norma', row.get('TIPO_NORMA', '')).strip()
                if solo_prioritarios and tipo not in ('Ley', 'Decreto', 'LEY', 'DECRETO'):
                    continue

                total += 1
                numero = row.get('numero_norma', row.get('NUMERO_NORMA', '')).strip()
                titulo = (row.get('titulo_sumario') or row.get('titulo_resumido') or
                          row.get('titulo', '')).strip()
                texto = row.get('texto_resumido', row.get('TEXTO_RESUMIDO',
                         row.get('sumario', ''))).strip()

                if not titulo and not texto:
                    continue

                contenido = f"{tipo} {numero}: {titulo}"
                if texto:
                    contenido += f"\n{texto[:1000]}"

                rama = clasificar_norma_rama(titulo, tipo)
                metadata = {
                    'tipo': tipo,
                    'numero': numero,
                    'titulo': titulo[:200],
                    'rama': rama,
                    'fecha': row.get('fecha_sancion', row.get('FECHA_SANCION', ''))[:20],
                }

                buffer.append((contenido, metadata))

                if len(buffer) >= BATCH_SIZE:
                    indexados += self._indexar_buffer(buffer)
                    buffer = []
                    print(f"  Fila: {num_fila} | Indexados: {indexados}")
                    if cp_path:
                        with open(cp_path, 'w', encoding='utf-8') as f_cp:
                            json.dump({'fila': num_fila + 1, 'indexados': indexados}, f_cp)

        if buffer:
            indexados += self._indexar_buffer(buffer)
            if cp_path:
                with open(cp_path, 'w', encoding='utf-8') as f_cp:
                    json.dump({'fila': total, 'indexados': indexados, 'completo': True}, f_cp)

        print(f"InfoLeg completado: {total} leídos, {indexados} indexados.")
        return indexados

    def _indexar_buffer(self, buffer: list) -> int:
        textos = [item[0] for item in buffer]
        try:
            embeddings = embed_textos(textos)
        except Exception as e:
            print(f"Error embeddings InfoLeg: {e}")
            return 0

        points = []
        for i, (texto, metadata) in enumerate(buffer):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=embeddings[i],
                payload={**metadata, 'texto': texto[:1500]}
            ))

        self.client.upsert(collection_name=COLECCION, points=points)
        return len(points)

    def buscar_normas(self, query: str, rama: str = None, n_results: int = 5) -> list:
        """Busca normas aplicables en InfoLeg"""
        try:
            query_vector = embed_query(query)
        except Exception as e:
            print(f"Error embedding query InfoLeg: {e}")
            return []

        try:
            result = self.client.query_points(
                collection_name=COLECCION,
                query=query_vector,
                limit=n_results
            )
            resultados = []
            for hit in result.points:
                payload = hit.payload or {}
                resultados.append({
                    'texto': payload.get('texto', ''),
                    'metadata': {k: v for k, v in payload.items() if k != 'texto'},
                    'score': hit.score,
                })
            return resultados
        except Exception as e:
            print(f"Error buscando normas: {e}")
            return []
