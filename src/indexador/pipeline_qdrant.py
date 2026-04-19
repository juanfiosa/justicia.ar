"""
INDEXADOR DE JURISPRUDENCIA — QDRANT
======================================
Indexa el dataset SAIJ en Qdrant Cloud usando embeddings de Gemini.
"""

import os
import sys
import json
import uuid
import re
import hashlib
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / '.env')

from indexador.qdrant_store import (
    get_qdrant_client,
    embed_textos, embed_query,
    crear_coleccion_si_no_existe, QDRANT_DISPONIBLE
)

try:
    from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
except ImportError:
    pass

try:
    from arquitectura.ramas_derecho import normalizar_materia_saij
except ImportError:
    def normalizar_materia_saij(m): return ["sin_clasificar"]

COLECCION_BASE = "jurisprudencia"
BATCH_SIZE = 100  # documentos por ciclo (internamente se divide en lotes de 10)


def limpiar_texto(texto: str) -> str:
    """Limpia markup SAIJ del texto"""
    if not texto:
        return ""
    texto = re.sub(r'\[\[p\]\]', '\n', texto)
    texto = re.sub(r'\[\[r uuid:[^\]]+\]\]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto[:6000]


class IndexadorJurisprudenciaQdrant:
    """Indexa y busca jurisprudencia SAIJ en Qdrant Cloud"""

    def __init__(self):
        self.client = get_qdrant_client()
        self.disponible = self.client is not None
        if not self.disponible:
            raise RuntimeError("Faltan variables: QDRANT_URL/QDRANT_API_KEY")

    def _nombre_coleccion(self, rama: str) -> str:
        return f"{COLECCION_BASE}_{rama}"

    def indexar_dataset(self, dataset_path: str, max_registros: int = None,
                        solo_rama: str = None, checkpoint_path: str = None):
        """Indexa el dataset SAIJ en Qdrant con soporte de checkpoint.

        Si se interrumpe, retoma automáticamente desde donde quedó.
        Los IDs son determinísticos: re-runs no crean duplicados.
        """
        path = Path(dataset_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset no encontrado: {dataset_path}")

        # Cargar checkpoint si existe
        cp_path = Path(checkpoint_path) if checkpoint_path else None
        linea_inicio = 0
        indexados = 0
        if cp_path and cp_path.exists():
            with open(cp_path, 'r', encoding='utf-8') as f:
                cp = json.load(f)
            linea_inicio = cp.get('linea', 0)
            indexados = cp.get('indexados', 0)
            print(f"Retomando desde línea {linea_inicio:,} ({indexados:,} ya indexados)")
        else:
            print(f"Indexando {dataset_path} en Qdrant Cloud...")

        total = linea_inicio
        buffer = []  # [(rama, texto, metadata, doc_id)]

        with open(path, 'r', encoding='utf-8') as f:
            for num_linea, line in enumerate(f):
                # Saltar líneas ya procesadas
                if num_linea < linea_inicio:
                    continue
                if max_registros and (num_linea - linea_inicio) >= max_registros:
                    break
                total += 1

                try:
                    doc = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue

                # Extraer texto — priorizamos el texto completo sobre el sumario (que suele ser breve)
                texto_raw = (doc.get('texto', '') or
                             doc.get('sumario', '') or
                             doc.get('resumen', ''))
                texto = limpiar_texto(texto_raw)
                if len(texto) < 50:
                    continue

                # ID determinístico basado en contenido (evita duplicados en re-runs)
                clave = (texto[:500] + str(doc.get('caratula', ''))).encode('utf-8', errors='ignore')
                hash_bytes = hashlib.sha256(clave).digest()[:16]
                doc_id = str(uuid.UUID(bytes=hash_bytes))

                # Clasificar rama
                materia = doc.get('materia', '') or doc.get('rama', '')
                ramas = normalizar_materia_saij(materia)
                rama = ramas[0] if ramas else 'sin_clasificar'

                if solo_rama and rama != solo_rama:
                    continue

                metadata = {
                    'rama': rama,
                    'caratula': str(doc.get('caratula', doc.get('titulo', 'N/A')))[:200],
                    'tribunal_tipo': str(doc.get('tribunal', doc.get('organismo', 'N/A')))[:100],
                    'fecha': str(doc.get('fecha', doc.get('año', 'N/A')))[:20],
                    'jurisdiccion': str(doc.get('jurisdiccion', 'Nacional'))[:50],
                    'materia_original': str(materia)[:100],
                }

                buffer.append((rama, texto, metadata, doc_id))

                # Procesar en lotes
                if len(buffer) >= BATCH_SIZE:
                    indexados += self._indexar_buffer(buffer)
                    buffer = []
                    print(f"  Línea: {num_linea:,} | Indexados: {indexados:,}")
                    if cp_path:
                        with open(cp_path, 'w', encoding='utf-8') as f_cp:
                            json.dump({'linea': num_linea + 1, 'indexados': indexados}, f_cp)

        # Último lote
        if buffer:
            indexados += self._indexar_buffer(buffer)
            if cp_path:
                with open(cp_path, 'w', encoding='utf-8') as f_cp:
                    json.dump({'linea': total, 'indexados': indexados, 'completo': True}, f_cp)

        print(f"Completado: {total:,} leídos, {indexados:,} indexados.")
        return indexados

    def _indexar_buffer(self, buffer: list) -> int:
        """Indexa un buffer de documentos en Qdrant usando IDs determinísticos."""
        if not buffer:
            return 0

        textos = [item[1] for item in buffer]

        try:
            embeddings = embed_textos(textos)
        except Exception as e:
            print(f"Error generando embeddings: {e}")
            return 0

        # Agrupar por rama manteniendo el índice global para el embedding correcto
        por_rama = {}
        for i, (rama, texto, metadata, doc_id) in enumerate(buffer):
            if rama not in por_rama:
                por_rama[rama] = []
            por_rama[rama].append((i, texto, metadata, doc_id))

        total_indexados = 0
        for rama, items in por_rama.items():
            coleccion = self._nombre_coleccion(rama)
            crear_coleccion_si_no_existe(self.client, coleccion)

            points = [
                PointStruct(
                    id=doc_id,
                    vector=embeddings[i],
                    payload={**metadata, 'texto': texto[:2000]}
                )
                for i, texto, metadata, doc_id in items
            ]

            # upsert: si el doc ya existe (mismo ID), lo actualiza en lugar de duplicar
            self.client.upsert(collection_name=coleccion, points=points)
            total_indexados += len(points)

        return total_indexados

    def buscar_precedentes(self, query: str, rama: str = None,
                           n_results: int = 6, filtros: dict = None) -> list:
        """Busca precedentes similares en Qdrant"""
        try:
            query_vector = embed_query(query)
        except Exception as e:
            print(f"Error generando embedding de query: {e}")
            return []

        colecciones = []
        if rama:
            colecciones = [self._nombre_coleccion(rama)]
        else:
            # Buscar en todas las colecciones
            todas = [c.name for c in self.client.get_collections().collections
                     if c.name.startswith(COLECCION_BASE + "_")]
            colecciones = todas

        resultados = []
        for coleccion in colecciones:
            try:
                result = self.client.query_points(
                    collection_name=coleccion,
                    query=query_vector,
                    limit=n_results
                )
                for hit in result.points:
                    payload = hit.payload or {}
                    resultados.append({
                        'texto': payload.get('texto', ''),
                        'metadata': {k: v for k, v in payload.items() if k != 'texto'},
                        'distancia': 1.0 - hit.score,
                        'coleccion': coleccion,
                    })
            except Exception as e:
                print(f"  [buscar] Error en colección {coleccion}: {e}")

        # Ordenar por relevancia
        resultados.sort(key=lambda x: x['distancia'])
        return resultados[:n_results]

    def estadisticas(self) -> dict:
        """Devuelve estadísticas de las colecciones"""
        stats = {}
        try:
            colecciones = [c.name for c in self.client.get_collections().collections
                           if c.name.startswith(COLECCION_BASE + "_")]
            for col in colecciones:
                info = self.client.get_collection(col)
                stats[col] = info.points_count
        except Exception as e:
            stats['error'] = str(e)
        return stats
