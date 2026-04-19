"""
INDEXADOR LEGISLACIÓN PROVINCIAL — QDRANT
==========================================
Indexa legislación provincial argentina en Qdrant Cloud.

FASE 1: metadata del CSV SAIJ (80k normas, sin cuota extra de Gemini)
FASE 2: texto completo por artículo (requiere scraping previo)

Colección: legislacion_provincial
"""

import os
import csv
import json
import re
import uuid
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / '.env')

from indexador.qdrant_store import (
    get_qdrant_client,
    embed_textos, embed_query,
    crear_coleccion_si_no_existe,
    QuotaExhaustedError,
)

try:
    from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
except ImportError:
    pass

COLECCION = "legislacion_provincial"
BATCH_SIZE = 50

# Tipos de norma prioritarios para Fase 2 (texto completo)
TIPOS_PRIORITARIOS = {
    'Constitución Nacional',   # constituciones provinciales
    'Constitución Provincial',
    'Código',
    'Código Procesal',
}

# Palabras clave que identifican códigos procesales en el nombre
KEYWORDS_CODIGO = [
    'código procesal civil', 'código procesal penal',
    'código procesal laboral', 'código procesal contencioso',
    'código de procedimiento civil', 'código de procedimiento penal',
    'código procesal minero', 'código procesal de familia',
    'código contencioso administrativo',
]


def es_vigente(estado: str) -> bool:
    """Filtra normas derogadas, con alcance individual o sin eficacia."""
    if not estado:
        return True
    e = estado.lower()
    if 'derogad' in e:
        return False
    if 'sin eficacia' in e or 'individual' in e:
        return False
    return True


def clasificar_tipo(tipo: str, nombre: str) -> str:
    """Normaliza el tipo de norma para metadata."""
    t = (tipo or '').lower()
    n = (nombre or '').lower()
    if 'constituc' in t or 'constituc' in n:
        return 'constitucion'
    for kw in KEYWORDS_CODIGO:
        if kw in n:
            return 'codigo_procesal'
    if 'código' in n or 'codigo' in n:
        return 'codigo'
    return tipo or 'ley'


class IndexadorProvincialQdrant:
    """Indexa y busca legislación provincial en Qdrant Cloud."""

    def __init__(self):
        self.client = get_qdrant_client()
        if self.client is None:
            raise RuntimeError("Faltan credenciales Qdrant")

    # ── FASE 1: metadata del CSV ────────────────────────────────────────────

    def indexar_csv(self, csv_path: str = None,
                    solo_vigentes: bool = True,
                    solo_prioritarios: bool = False,
                    checkpoint_path: str = None) -> int:
        """
        Fase 1: indexa metadata de los ~80k registros del CSV SAIJ provincial.

        Parámetros:
            solo_vigentes: omite derogadas e individuales (recomendado)
            solo_prioritarios: solo constituciones y códigos (~138 registros)
            checkpoint_path: JSON para reanudar si se corta
        """
        if csv_path is None:
            csv_path = str(Path(__file__).parent.parent.parent /
                           'datos' / 'saij_normativa_provincial.csv')
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV no encontrado: {csv_path}")

        # Checkpoint
        cp_path = Path(checkpoint_path) if checkpoint_path else None
        fila_inicio, indexados = 0, 0
        if cp_path and cp_path.exists():
            with open(cp_path, encoding='utf-8') as f:
                cp = json.load(f)
            fila_inicio = cp.get('fila', 0)
            indexados   = cp.get('indexados', 0)
            print(f"Retomando provincia CSV desde fila {fila_inicio} "
                  f"({indexados} ya indexados)")
        else:
            print("Indexando legislación provincial (CSV metadata)...")

        crear_coleccion_si_no_existe(self.client, COLECCION)

        total, buffer = 0, []

        with open(path, encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for num_fila, row in enumerate(reader):
                if num_fila < fila_inicio:
                    continue

                tipo    = row.get('tipo_norma', '').strip()
                estado  = row.get('estado_vigencia', '').strip()
                nombre  = row.get('nombre_norma', '').strip()
                titulo  = (row.get('titulo_resumido') or '').strip()
                sumario = (row.get('titulo_sumario') or '').strip()

                if solo_vigentes and not es_vigente(estado):
                    continue
                if solo_prioritarios and tipo not in TIPOS_PRIORITARIOS:
                    nombre_lower = nombre.lower()
                    if not any(kw in nombre_lower for kw in KEYWORDS_CODIGO):
                        continue

                if not nombre and not titulo:
                    continue

                # Construir texto para embedding
                contenido = f"{tipo}: {nombre}"
                if titulo and titulo.lower() != nombre.lower():
                    contenido += f"\n{titulo}"
                if sumario:
                    contenido += f"\n{sumario[:500]}"

                tipo_norm = clasificar_tipo(tipo, nombre)
                metadata = {
                    'provincia':    row.get('provincia_nombre', '').strip(),
                    'provincia_id': row.get('provincia_id', '').strip(),
                    'tipo':         tipo_norm,
                    'tipo_original':tipo,
                    'numero':       row.get('numero_norma', '').strip(),
                    'nombre':       nombre[:200],
                    'titulo':       titulo[:200],
                    'estado':       estado[:80],
                    'fecha':        row.get('fecha', '')[:10],
                    'saij_url':     row.get('texto_actualizado', '').strip(),
                    'tiene_texto_completo': False,
                }

                total += 1
                buffer.append((contenido, metadata))

                if len(buffer) >= BATCH_SIZE:
                    indexados += self._indexar_buffer(buffer)
                    buffer = []
                    print(f"  Fila: {num_fila} | Indexados: {indexados}")
                    if cp_path:
                        with open(cp_path, 'w', encoding='utf-8') as fc:
                            json.dump({'fila': num_fila + 1,
                                       'indexados': indexados}, fc)

        if buffer:
            indexados += self._indexar_buffer(buffer)
            if cp_path:
                with open(cp_path, 'w', encoding='utf-8') as fc:
                    json.dump({'fila': total, 'indexados': indexados,
                               'completo': True}, fc)

        print(f"CSV provincial completado: {total} leídos, "
              f"{indexados} indexados.")
        return indexados

    # ── FASE 2: texto completo por artículo ─────────────────────────────────

    def indexar_textos_completos(self, textos_dir: str = None,
                                  checkpoint_path: str = None) -> int:
        """
        Fase 2: indexa los textos completos descargados por el scraper,
        chunkeados artículo por artículo.

        El scraper guarda JSONs en textos_dir/ con formato:
          { "provincia", "tipo", "nombre", "numero", "articulos": [
              {"numero": "1", "texto": "..."},
              ...
          ]}
        """
        if textos_dir is None:
            textos_dir = str(Path(__file__).parent.parent.parent /
                             'datos' / 'textos_provinciales')
        td = Path(textos_dir)
        if not td.exists():
            print(f"Directorio de textos no encontrado: {textos_dir}")
            return 0

        cp_path = Path(checkpoint_path) if checkpoint_path else None
        procesados_ids = set()
        indexados = 0
        if cp_path and cp_path.exists():
            with open(cp_path, encoding='utf-8') as f:
                cp = json.load(f)
            procesados_ids = set(cp.get('procesados', []))
            indexados = cp.get('indexados', 0)
            print(f"Retomando textos completos ({indexados} ya indexados)")

        crear_coleccion_si_no_existe(self.client, COLECCION)

        archivos = sorted(td.glob('*.json'))
        print(f"Textos completos disponibles: {len(archivos)} archivos")

        for archivo in archivos:
            if archivo.stem in procesados_ids:
                continue

            try:
                with open(archivo, encoding='utf-8') as f:
                    doc = json.load(f)
            except Exception as e:
                print(f"  [ERROR] No se pudo leer {archivo.name}: {e}")
                continue

            articulos = doc.get('articulos', [])
            if not articulos:
                continue

            provincia = doc.get('provincia', '')
            tipo      = doc.get('tipo', '')
            nombre    = doc.get('nombre', '')
            numero    = doc.get('numero', '')

            buffer = []
            for art in articulos:
                num_art = art.get('numero', '')
                texto_art = art.get('texto', '').strip()
                if len(texto_art) < 20:
                    continue

                contenido = (f"{nombre}\n"
                             f"Artículo {num_art}.- {texto_art[:2000]}")

                meta = {
                    'provincia':    provincia,
                    'tipo':         tipo,
                    'nombre':       nombre[:200],
                    'numero_ley':   numero,
                    'articulo':     num_art,
                    'tiene_texto_completo': True,
                }
                buffer.append((contenido, meta))

                if len(buffer) >= BATCH_SIZE:
                    indexados += self._indexar_buffer(buffer)
                    buffer = []

            if buffer:
                indexados += self._indexar_buffer(buffer)

            procesados_ids.add(archivo.stem)
            print(f"  {archivo.stem}: {len(articulos)} artículos indexados")

            if cp_path:
                with open(cp_path, 'w', encoding='utf-8') as fc:
                    json.dump({'procesados': list(procesados_ids),
                               'indexados': indexados}, fc)

        print(f"Textos completos: {indexados} artículos indexados.")
        return indexados

    # ── Buffer interno ───────────────────────────────────────────────────────

    def _indexar_buffer(self, buffer: list) -> int:
        textos = [item[0] for item in buffer]
        try:
            embeddings = embed_textos(textos)
        except QuotaExhaustedError:
            raise
        except Exception as e:
            print(f"  [ERROR embeddings provincial]: {e}")
            return 0

        points = []
        for i, (texto, metadata) in enumerate(buffer):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=embeddings[i],
                payload={**metadata, 'texto': texto[:2000]}
            ))

        self.client.upsert(collection_name=COLECCION, points=points)
        return len(points)

    # ── Búsqueda ─────────────────────────────────────────────────────────────

    def buscar(self, query: str, provincia: str = None,
               tipo: str = None, n_results: int = 5) -> list:
        """
        Busca normas provinciales.

        Args:
            query: texto de búsqueda semántica
            provincia: filtrar por provincia (ej. 'Córdoba')
            tipo: filtrar por tipo ('constitucion', 'codigo_procesal', etc.)
            n_results: cantidad de resultados
        """
        try:
            query_vector = embed_query(query)
        except Exception as e:
            print(f"Error embedding query provincial: {e}")
            return []

        # Construir filtro Qdrant si aplica
        query_filter = None
        conditions = []
        if provincia:
            conditions.append(
                FieldCondition(key='provincia',
                               match=MatchValue(value=provincia))
            )
        if tipo:
            conditions.append(
                FieldCondition(key='tipo',
                               match=MatchValue(value=tipo))
            )
        if conditions:
            from qdrant_client.models import Filter, Must
            query_filter = Filter(must=conditions)

        try:
            kwargs = dict(
                collection_name=COLECCION,
                query=query_vector,
                limit=n_results,
            )
            if query_filter:
                kwargs['query_filter'] = query_filter

            result = self.client.query_points(**kwargs)
            resultados = []
            for hit in result.points:
                payload = hit.payload or {}
                resultados.append({
                    'texto':    payload.get('texto', ''),
                    'metadata': {k: v for k, v in payload.items()
                                 if k != 'texto'},
                    'score':    hit.score,
                })
            return resultados
        except Exception as e:
            print(f"Error buscando normas provinciales: {e}")
            return []
