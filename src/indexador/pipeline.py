"""
MÓDULO 1: INDEXADOR DE JURISPRUDENCIA
======================================
Pipeline para indexar los sumarios SAIJ en ChromaDB con embeddings.

Estrategia:
- Cada sumario SAIJ se convierte en un documento con embedding
- Se almacena en colecciones separadas por rama del derecho
- Los metadatos permiten filtrar por tribunal, jurisdicción, fecha, etc.
- Búsqueda semántica: dado un caso nuevo, encontrar precedentes similares

Uso:
    python -m src.indexador.pipeline --dataset L:/JusticiaArgentina/datos/jurisprudencia_saij/dataset.jsonl
"""

import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("ERROR: chromadb no instalado. Ejecutar: pip install chromadb")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable

from arquitectura.ramas_derecho import normalizar_materia_saij, RAMAS_DERECHO


# ================================================================
# CONFIGURACIÓN
# ================================================================

CHROMA_PERSIST_DIR = "L:/JusticiaArgentina/datos/chromadb"
DATASET_PATH = "L:/JusticiaArgentina/datos/jurisprudencia_saij/dataset.jsonl"
BATCH_SIZE = 500  # ChromaDB recomienda batches de ~500
MAX_TEXTO_LENGTH = 8000  # Límite de caracteres por documento


# ================================================================
# PREPROCESAMIENTO
# ================================================================

def limpiar_texto_saij(texto: str) -> str:
    """Limpia el markup interno de SAIJ ([[p]], [[r uuid:...]], etc.)"""
    if not texto:
        return ""
    import re
    # Remover tags SAIJ
    texto = re.sub(r'\[\[/?p\]\]', '', texto)
    texto = re.sub(r'\[\[r uuid:\w+\]\]', '', texto)
    texto = re.sub(r'\[\[/r uuid:\w+\]\]', '', texto)
    texto = re.sub(r'\[\[/?b\]\]', '', texto)
    texto = re.sub(r'\[\[/?i\]\]', '', texto)
    # Limpiar espacios múltiples
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def extraer_referencias_normativas(refs) -> list[str]:
    """Extrae lista de referencias normativas del campo del dataset"""
    if not refs:
        return []
    normas = []
    ref_list = refs.get('referencia-normativa', [])
    if isinstance(ref_list, dict):
        ref_list = [ref_list]
    for ref in ref_list:
        if isinstance(ref, dict) and ref.get('ref'):
            normas.append(ref['ref'])
    return normas


def preparar_documento(record: dict) -> Optional[dict]:
    """
    Transforma un registro SAIJ en un documento listo para ChromaDB.

    Returns:
        dict con 'id', 'text', 'metadata' o None si no es indexable
    """
    texto = limpiar_texto_saij(record.get('texto', ''))
    sumario = limpiar_texto_saij(record.get('sumario', ''))

    # Necesitamos al menos texto o sumario
    if not texto and not sumario:
        return None

    # El documento es la concatenación de sumario + texto
    contenido = ""
    if sumario:
        contenido += f"SUMARIO: {sumario}\n"
    if texto:
        contenido += f"DOCTRINA: {texto}"

    # Truncar si es muy largo
    if len(contenido) > MAX_TEXTO_LENGTH:
        contenido = contenido[:MAX_TEXTO_LENGTH]

    # Normalizar rama
    materia = record.get('materia', 'N/A')
    ramas = normalizar_materia_saij(materia)
    rama_principal = ramas[0] if ramas else 'sin_clasificar'

    # Extraer jurisdicción
    jurisdiccion = ''
    j = record.get('jurisdiccion', {})
    if isinstance(j, dict):
        jurisdiccion = j.get('descripcion', '')

    # Metadata
    metadata = {
        'rama': rama_principal,
        'materia_original': materia or '',
        'caratula': record.get('caratula', '') or '',
        'tribunal_tipo': record.get('tipo-tribunal', '') or '',
        'instancia': (record.get('instancia', '') or '')[:5],  # Truncar instancias duplicadas
        'jurisdiccion': jurisdiccion,
        'provincia': record.get('provincia', '') or '',
        'fecha': record.get('fecha', '') or '',
        'titulo': record.get('titulo', '') or '',
        'id_infojus': record.get('id-infojus', '') or '',
        'fuente': record.get('fuente', '') or '',
    }

    # ChromaDB no acepta None en metadata
    metadata = {k: v for k, v in metadata.items() if v is not None}

    doc_id = record.get('id-infojus', '') or record.get('guid', '') or record.get('numero-sumario', '')
    if not doc_id:
        return None

    return {
        'id': doc_id,
        'text': contenido,
        'metadata': metadata
    }


# ================================================================
# INDEXACIÓN EN CHROMADB
# ================================================================

class IndexadorJurisprudencia:
    """
    Indexa jurisprudencia SAIJ en ChromaDB con colecciones por rama del derecho.
    """

    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )

        # Colecciones por rama + una general
        self.colecciones = {}

    def _get_coleccion(self, rama: str) -> chromadb.Collection:
        """Obtiene o crea la colección para una rama del derecho"""
        if rama not in self.colecciones:
            nombre = f"jurisprudencia_{rama}"
            self.colecciones[rama] = self.client.get_or_create_collection(
                name=nombre,
                metadata={
                    "description": f"Jurisprudencia argentina - {RAMAS_DERECHO.get(rama, {}).get('nombre', rama)}",
                    "hnsw:space": "cosine"  # Distancia coseno para similitud semántica
                }
            )
        return self.colecciones[rama]

    def indexar_dataset(self, dataset_path: str = DATASET_PATH,
                        max_registros: int = 0,
                        solo_rama: str = None):
        """
        Indexa el dataset SAIJ completo o parcial.

        Args:
            dataset_path: Ruta al archivo JSONL
            max_registros: Límite de registros (0 = sin límite)
            solo_rama: Si se especifica, solo indexa esa rama
        """
        print(f"\n{'='*70}")
        print(f"INDEXADOR DE JURISPRUDENCIA SAIJ")
        print(f"{'='*70}")
        print(f"Dataset: {dataset_path}")
        print(f"ChromaDB: {self.persist_dir}")
        if max_registros:
            print(f"Límite: {max_registros} registros")
        if solo_rama:
            print(f"Solo rama: {solo_rama}")
        print(f"{'='*70}\n")

        # Buffers por rama para batch insert
        buffers = {}  # rama -> {'ids': [], 'documents': [], 'metadatas': []}

        stats = {
            'total_leidos': 0,
            'total_indexados': 0,
            'descartados_sin_texto': 0,
            'por_rama': {}
        }

        start_time = time.time()

        with open(dataset_path, 'r', encoding='utf-8') as f:
            for line in tqdm(f, desc="Procesando registros", unit=" docs"):
                stats['total_leidos'] += 1

                if max_registros and stats['total_leidos'] > max_registros:
                    break

                record = json.loads(line)
                doc = preparar_documento(record)

                if not doc:
                    stats['descartados_sin_texto'] += 1
                    continue

                rama = doc['metadata']['rama']

                # Filtrar por rama si se especificó
                if solo_rama and rama != solo_rama:
                    continue

                # Agregar al buffer de la rama
                if rama not in buffers:
                    buffers[rama] = {'ids': [], 'documents': [], 'metadatas': []}

                buffers[rama]['ids'].append(doc['id'])
                buffers[rama]['documents'].append(doc['text'])
                buffers[rama]['metadatas'].append(doc['metadata'])

                # Flush cuando el buffer alcanza BATCH_SIZE
                if len(buffers[rama]['ids']) >= BATCH_SIZE:
                    self._flush_buffer(rama, buffers[rama], stats)
                    buffers[rama] = {'ids': [], 'documents': [], 'metadatas': []}

        # Flush buffers restantes
        for rama, buffer in buffers.items():
            if buffer['ids']:
                self._flush_buffer(rama, buffer, stats)

        elapsed = time.time() - start_time

        # Reporte
        print(f"\n{'='*70}")
        print(f"INDEXACIÓN COMPLETADA en {elapsed:.1f}s")
        print(f"{'='*70}")
        print(f"  Registros leídos:    {stats['total_leidos']:>10,}")
        print(f"  Registros indexados: {stats['total_indexados']:>10,}")
        print(f"  Descartados:         {stats['descartados_sin_texto']:>10,}")
        print(f"\n  Por rama:")
        for rama, count in sorted(stats['por_rama'].items(), key=lambda x: -x[1]):
            nombre = RAMAS_DERECHO.get(rama, {}).get('nombre', rama)
            print(f"    {nombre:45s} {count:>8,}")
        print(f"{'='*70}")

        return stats

    def _flush_buffer(self, rama: str, buffer: dict, stats: dict):
        """Inserta un batch de documentos en la colección de la rama"""
        coleccion = self._get_coleccion(rama)
        try:
            coleccion.upsert(
                ids=buffer['ids'],
                documents=buffer['documents'],
                metadatas=buffer['metadatas']
            )
            count = len(buffer['ids'])
            stats['total_indexados'] += count
            stats['por_rama'][rama] = stats['por_rama'].get(rama, 0) + count
        except Exception as e:
            print(f"\n  ERROR indexando batch en '{rama}': {e}")

    def buscar_precedentes(self, query: str, rama: str = None,
                           n_results: int = 10,
                           filtros: dict = None) -> list[dict]:
        """
        Busca precedentes similares a una consulta.

        Args:
            query: Texto de búsqueda (hechos del caso, cuestión jurídica, etc.)
            rama: Rama del derecho (si None, busca en todas)
            n_results: Número de resultados
            filtros: Filtros adicionales de metadata (ej: {'jurisdiccion': 'Nacional'})

        Returns:
            Lista de precedentes con score de similitud
        """
        where = filtros or {}

        if rama:
            ramas_buscar = [rama]
        else:
            ramas_buscar = list(RAMAS_DERECHO.keys())

        resultados = []

        for r in ramas_buscar:
            try:
                coleccion = self._get_coleccion(r)
                if coleccion.count() == 0:
                    continue

                results = coleccion.query(
                    query_texts=[query],
                    n_results=min(n_results, coleccion.count()),
                    where=where if where else None
                )

                if results and results['documents'] and results['documents'][0]:
                    for i, doc in enumerate(results['documents'][0]):
                        resultados.append({
                            'rama': r,
                            'texto': doc,
                            'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                            'distancia': results['distances'][0][i] if results['distances'] else 1.0,
                            'id': results['ids'][0][i] if results['ids'] else '',
                        })
            except Exception as e:
                print(f"  Error buscando en '{r}': {e}")

        # Ordenar por distancia (menor = más similar)
        resultados.sort(key=lambda x: x['distancia'])
        return resultados[:n_results]

    def estadisticas(self) -> dict:
        """Devuelve estadísticas de las colecciones indexadas"""
        stats = {}
        for rama in list(RAMAS_DERECHO.keys()) + ['sin_clasificar']:
            try:
                col = self._get_coleccion(rama)
                count = col.count()
                if count > 0:
                    nombre = RAMAS_DERECHO.get(rama, {}).get('nombre', rama)
                    stats[nombre] = count
            except Exception:
                pass
        return stats


# ================================================================
# CLI
# ================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Indexar jurisprudencia SAIJ en ChromaDB')
    parser.add_argument('--dataset', default=DATASET_PATH, help='Ruta al dataset JSONL')
    parser.add_argument('--max', type=int, default=0, help='Máximo de registros (0=todos)')
    parser.add_argument('--rama', default=None, help='Solo indexar una rama específica')
    parser.add_argument('--buscar', default=None, help='Buscar precedentes (modo consulta)')
    parser.add_argument('--stats', action='store_true', help='Mostrar estadísticas')

    args = parser.parse_args()

    indexador = IndexadorJurisprudencia()

    if args.stats:
        stats = indexador.estadisticas()
        print("\n=== ESTADÍSTICAS DE COLECCIONES ===")
        total = 0
        for nombre, count in sorted(stats.items(), key=lambda x: -x[1]):
            print(f"  {nombre:45s} {count:>8,}")
            total += count
        print(f"  {'TOTAL':45s} {total:>8,}")

    elif args.buscar:
        print(f"\nBuscando: '{args.buscar}'")
        print(f"Rama: {args.rama or 'todas'}\n")
        resultados = indexador.buscar_precedentes(args.buscar, rama=args.rama)
        for i, r in enumerate(resultados, 1):
            meta = r['metadata']
            print(f"\n--- Resultado {i} (distancia: {r['distancia']:.4f}) ---")
            print(f"  Carátula: {meta.get('caratula', 'N/A')}")
            print(f"  Tribunal: {meta.get('tribunal_tipo', 'N/A')} | Fecha: {meta.get('fecha', 'N/A')}")
            print(f"  Rama: {meta.get('rama', 'N/A')} | Jurisdicción: {meta.get('jurisdiccion', 'N/A')}")
            print(f"  Texto: {r['texto'][:300]}...")

    else:
        indexador.indexar_dataset(
            dataset_path=args.dataset,
            max_registros=args.max,
            solo_rama=args.rama
        )
