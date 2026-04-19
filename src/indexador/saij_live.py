"""
SAIJ LIVE — Indexador de sumarios vivos desde la API de SAIJ
=============================================================
Complementa el dump local (873k fallos históricos) con sumarios
actualizados descargados directamente de saij.gob.ar.

Los sumarios son más densos semánticamente que los fallos completos:
contienen el principio jurídico extraído, los descriptores del
tesauro jurídico y metadata normalizada.

Colecciones destino: jurisprudencia_{rama} (las mismas del dump local)
Checkpoint: datos/checkpoint_saij_live.json
  { "uuids_indexados": [...], "total_indexados": N, "offset": N }
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# saij_mcp: intentar importar desde site-packages estándar o user site-packages
import site
for _sp in site.getusersitepackages() if isinstance(site.getusersitepackages(), list) else [site.getusersitepackages()]:
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from saij_mcp.client import search as saij_search, SAIJError
from indexador.qdrant_store import (
    get_qdrant_client,
    embed_textos, embed_query,
    crear_coleccion_si_no_existe,
    QuotaExhaustedError,
)

try:
    from qdrant_client.models import PointStruct
except ImportError:
    pass

import uuid as uuid_lib

# ── Configuración ────────────────────────────────────────────────────────────

BATCH_SIZE       = 50
PAUSA_ENTRE_PAGS = 1.0   # segundos entre llamadas a la API SAIJ
SOLO_DESDE_ANIO  = 2024  # omitir sumarios anteriores a este año

# Mapa de descriptores → colección Qdrant (coincide con el dump local)
RAMA_POR_DESCRIPTOR = {
    "laboral":             "jurisprudencia_laboral",
    "trabajo":             "jurisprudencia_laboral",
    "despido":             "jurisprudencia_laboral",
    "penal":               "jurisprudencia_penal",
    "criminal":            "jurisprudencia_penal",
    "delito":              "jurisprudencia_penal",
    "procesal penal":      "jurisprudencia_penal",
    "civil":               "jurisprudencia_civil_comercial",
    "comercial":           "jurisprudencia_civil_comercial",
    "contratos":           "jurisprudencia_civil_comercial",
    "familia":             "jurisprudencia_familia",
    "divorcio":            "jurisprudencia_familia",
    "adopcion":            "jurisprudencia_familia",
    "alimentos":           "jurisprudencia_familia",
    "administrativo":      "jurisprudencia_contencioso_admin",
    "contencioso":         "jurisprudencia_contencioso_admin",
    "previsional":         "jurisprudencia_contencioso_admin",
    "constitucional":      "jurisprudencia_constitucional",
    "amparo":              "jurisprudencia_constitucional",
    "habeas corpus":       "jurisprudencia_constitucional",
}

COLECCION_DEFAULT = "jurisprudencia_civil_comercial"


def _clasificar_rama(descriptores: list[str]) -> str:
    """Mapea los descriptores del tesauro a una colección Qdrant."""
    text = " ".join(d.lower() for d in descriptores)
    for kw, col in RAMA_POR_DESCRIPTOR.items():
        if kw in text:
            return col
    return COLECCION_DEFAULT


def _anio(fecha_str: str) -> int:
    try:
        return int(fecha_str[:4])
    except Exception:
        return 0


# ── Indexador principal ──────────────────────────────────────────────────────

class IndexadorSAIJLive:
    """Descarga sumarios vivos de SAIJ y los indexa en Qdrant."""

    def __init__(self):
        self.client = get_qdrant_client()
        if self.client is None:
            raise RuntimeError("Faltan credenciales Qdrant")

    def indexar(self,
                terminos_busqueda: list[str] | None = None,
                solo_desde_anio: int = SOLO_DESDE_ANIO,
                checkpoint_path: str | None = None) -> int:
        """
        Descarga e indexa sumarios de SAIJ.

        Args:
            terminos_busqueda: lista de queries Lucene para cubrir distintas
                               áreas. Por defecto usa un set amplio.
            solo_desde_anio: omite sumarios anteriores a este año.
            checkpoint_path: JSON para guardar progreso entre sesiones.
        """
        if terminos_busqueda is None:
            terminos_busqueda = _TERMINOS_DEFAULT

        cp_path = Path(checkpoint_path) if checkpoint_path else None
        uuids_indexados: set[str] = set()
        total_indexados = 0

        if cp_path and cp_path.exists():
            with open(cp_path, encoding="utf-8") as f:
                cp = json.load(f)
            uuids_indexados = set(cp.get("uuids_indexados", []))
            total_indexados = cp.get("total_indexados", 0)
            print(f"Retomando SAIJ live ({total_indexados} ya indexados, "
                  f"{len(uuids_indexados)} UUIDs conocidos)")

        # Crear colecciones necesarias
        colecciones = set(RAMA_POR_DESCRIPTOR.values()) | {COLECCION_DEFAULT}
        for col in colecciones:
            crear_coleccion_si_no_existe(self.client, col)

        for termino in terminos_busqueda:
            print(f"\n[SAIJ live] Búsqueda: '{termino}'")
            offset = 0

            while True:
                try:
                    resp = saij_search(
                        termino,
                        doc_type="sumario",
                        field="titulo",
                        limit=25,
                        offset=offset,
                    )
                except SAIJError as e:
                    print(f"  [SAIJ ERROR] {e} — esperando 30s")
                    time.sleep(30)
                    break
                except Exception as e:
                    print(f"  [ERROR] {e}")
                    break

                docs = resp.get("results", [])
                if not docs:
                    break

                total_query = resp.get("total", 0)

                # Filtrar: ya indexados o muy antiguos
                nuevos = [
                    d for d in docs
                    if d.get("uuid") not in uuids_indexados
                    and _anio(d.get("fecha", "0000")) >= solo_desde_anio
                ]

                if nuevos:
                    try:
                        n = self._indexar_lote(nuevos)
                        total_indexados += n
                        for d in nuevos:
                            uuids_indexados.add(d.get("uuid", ""))
                        print(f"  offset={offset} | +{n} | total={total_indexados} "
                              f"/ query_total={total_query}")
                    except QuotaExhaustedError:
                        # Guardar checkpoint y propagar
                        self._guardar_checkpoint(
                            cp_path, uuids_indexados, total_indexados)
                        raise

                offset += 25
                if offset >= total_query:
                    break

                time.sleep(PAUSA_ENTRE_PAGS)

        self._guardar_checkpoint(cp_path, uuids_indexados, total_indexados)
        print(f"\nSAIJ live completado: {total_indexados} sumarios indexados.")
        return total_indexados

    def _indexar_lote(self, docs: list[dict]) -> int:
        """Embeda e inserta un lote de sumarios en Qdrant."""
        # Agrupar por colección
        por_coleccion: dict[str, list] = {}
        for doc in docs:
            texto = doc.get("texto", "").strip()
            if len(texto) < 30:
                continue
            col = _clasificar_rama(doc.get("descriptores", []))
            por_coleccion.setdefault(col, []).append(doc)

        total = 0
        for col, grupo in por_coleccion.items():
            textos = [d["texto"][:2000] for d in grupo]
            embeddings = embed_textos(textos)  # puede lanzar QuotaExhaustedError

            points = []
            for i, doc in enumerate(grupo):
                points.append(PointStruct(
                    id=str(uuid_lib.uuid4()),
                    vector=embeddings[i],
                    payload={
                        "texto":        doc["texto"][:2000],
                        "uuid_saij":    doc.get("uuid", ""),
                        "fecha":        doc.get("fecha", ""),
                        "jurisdiccion": doc.get("jurisdiccion", ""),
                        "tribunal":     doc.get("tribunal", ""),
                        "caratula":     doc.get("caratula", ""),
                        "descriptores": doc.get("descriptores", []),
                        "fuente":       "saij_live",
                    }
                ))

            self.client.upsert(collection_name=col, points=points)
            total += len(points)

        return total

    @staticmethod
    def _guardar_checkpoint(cp_path, uuids: set, total: int):
        if not cp_path:
            return
        with open(cp_path, "w", encoding="utf-8") as f:
            json.dump({
                "uuids_indexados": list(uuids),
                "total_indexados": total,
            }, f)


# ── Términos de búsqueda ────────────────────────────────────────────────────
# Un término amplio que cubre todo + términos específicos para maximizar recall.
# La API devuelve resultados por relevancia (no por fecha), así que paginamos
# completamente para capturar los sumarios recientes dispersos en el índice.

_TERMINOS_DEFAULT = [
    # Términos con alta probabilidad de retornar docs recientes primero
    # (eventos, fenómenos o derechos de aparición relativamente reciente)
    "violencia de genero",
    "perspectiva de genero",
    "teletrabajo",
    "emergencia sanitaria",
    "inteligencia artificial",
    "criptomonedas",
    "violencia familiar",
    "grooming",
    "femicidio",
    "acoso laboral",
    "derecho a la vivienda",
    "medio ambiente",
    "discapacidad inclusion",
    "migrantes extranjeros",
    "derechos digitales",
    # Términos procesales generales (alta cobertura)
    "medida cautelar innovativa",
    "recurso extraordinario federal",
    "accion de amparo",
    "habeas corpus",
    "recurso de casacion",
    # Materias con flujo constante de casos nuevos
    "concurso preventivo",
    "ejecucion hipotecaria",
    "alimentos provisorios",
    "responsabilidad medica",
    "daño punitivo",
]
