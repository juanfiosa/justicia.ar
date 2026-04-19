"""
INDEXADOR DE LEGISLACIÓN InfoLeg
==================================
Indexa la base de legislación nacional argentina (InfoLeg) en ChromaDB.
Cada norma queda disponible para el retrieval del generador de sentencias.

Uso:
    python -m src.indexador.infoleg
"""

import csv
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.config import Settings

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(it, **kw): return it

from arquitectura.ramas_derecho import RAMAS_DERECHO

# ================================================================
# CONFIGURACIÓN
# ================================================================

CHROMA_PERSIST_DIR = "L:/JusticiaArgentina/datos/chromadb"
INFOLEG_CSV = "L:/JusticiaArgentina/datos/infoleg/base-infoleg-normativa-nacional.csv"
BATCH_SIZE = 500

# Tipos de normas prioritarios para el sistema judicial
TIPOS_PRIORITARIOS = {"Ley", "Decreto/Ley", "Decreto"}

# Mapa de palabras clave en titulo/sumario → rama
PALABRAS_CLAVE_RAMA = {
    "civil_comercial": [
        "CIVIL", "COMERCIAL", "SOCIETAD", "CONCURSO", "QUIEBRA", "CONTRATO",
        "CONSUMIDOR", "SEGUROS", "NAVEGACION", "AERONAUTICO", "SUCESION",
        "FAMILIA", "ADOPCION", "DIVORCIO", "FILIACION", "ALIMENTOS",
        "PROPIEDAD HORIZONTAL", "HIPOTECA"
    ],
    "penal": [
        "PENAL", "DELITO", "PENA", "CARCEL", "PRISION", "EJECUCION PENAL",
        "ESTUPEFACIENTE", "NARCOTRÁFICO", "TRATA DE PERSONAS", "TERRORISMO",
        "LAVADO DE ACTIVOS", "CONTRAVENCI"
    ],
    "laboral": [
        "TRABAJO", "LABORAL", "EMPLEO", "SINDICATO", "CONVENIO COLECTIVO",
        "JUBILACION", "PENSION", "SEGURIDAD SOCIAL", "ACCIDENTE DE TRABAJO",
        "RIESGO DEL TRABAJO", "ANSES", "OBRA SOCIAL"
    ],
    "administrativo": [
        "ADMINISTRACION", "ADMINISTRATIVO", "EMPLEO PUBLICO", "LICITACION",
        "OBRA PUBLICA", "CONTRATACION PUBLICA", "EXPROPIACION",
        "RESPONSABILIDAD DEL ESTADO", "PROCEDIMIENTO ADMINISTRATIVO"
    ],
    "tributario": [
        "IMPUESTO", "TRIBUTARIO", "FISCAL", "ADUANA", "IVA", "GANANCIAS",
        "COPARTICIPACION", "AFIP", "DGI", "RECAUDACION", "EXENCION"
    ],
    "constitucional": [
        "CONSTITUCIONAL", "DERECHOS HUMANOS", "GARANTIA", "AMPARO",
        "HABEAS CORPUS", "HABEAS DATA", "LIBERTAD DE EXPRESION",
        "DERECHO A LA SALUD", "DERECHO A LA VIVIENDA", "MEDIO AMBIENTE",
        "ELECTORAL", "PARTIDO POLITICO", "INTERNACIONAL"
    ],
}


def clasificar_norma_rama(tipo: str, titulo: str, sumario: str) -> str:
    """Clasifica una norma en una rama del derecho según su título y sumario"""
    texto = f"{titulo} {sumario}".upper()

    scores = {rama: 0 for rama in PALABRAS_CLAVE_RAMA}
    for rama, palabras in PALABRAS_CLAVE_RAMA.items():
        for palabra in palabras:
            if palabra in texto:
                scores[rama] += 1

    mejor = max(scores, key=scores.get)
    return mejor if scores[mejor] > 0 else "sin_clasificar"


def preparar_norma(row: dict) -> dict | None:
    """Convierte una fila CSV de InfoLeg en documento indexable"""
    tipo = row.get("tipo_norma", "").strip()
    numero = row.get("numero_norma", "").strip()
    titulo = row.get("titulo_resumido", "").strip()
    sumario = row.get("titulo_sumario", "").strip()
    texto = row.get("texto_resumido", "").strip()
    fecha = row.get("fecha_sancion", "").strip()
    id_norma = row.get("id_norma", "").strip()

    if not texto or not id_norma:
        return None

    # Descripción compacta de la norma
    identificacion = f"{tipo} {numero}".strip()
    contenido = f"NORMA: {identificacion}\nTITULO: {titulo}\nMATERIA: {sumario}\nTEXTO: {texto}"

    if len(contenido) > 6000:
        contenido = contenido[:6000]

    rama = clasificar_norma_rama(tipo, titulo, sumario)

    return {
        "id": f"infoleg_{id_norma}",
        "text": contenido,
        "metadata": {
            "tipo": tipo,
            "numero": numero,
            "titulo": titulo[:200],
            "sumario": sumario[:200],
            "fecha_sancion": fecha,
            "rama": rama,
            "fuente": "infoleg",
            "id_norma": id_norma,
        }
    }


class IndexadorInfoLeg:
    """Indexa la legislación nacional InfoLeg en ChromaDB"""

    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self._col_legislacion = None

    def _get_coleccion(self) -> chromadb.Collection:
        if self._col_legislacion is None:
            self._col_legislacion = self.client.get_or_create_collection(
                name="legislacion_nacional",
                metadata={
                    "description": "Legislación nacional argentina (InfoLeg)",
                    "hnsw:space": "cosine"
                }
            )
        return self._col_legislacion

    def indexar(self, csv_path: str = INFOLEG_CSV,
                solo_prioritarios: bool = True,
                max_registros: int = 0):
        """
        Indexa las normas de InfoLeg.

        Args:
            solo_prioritarios: Si True, solo Leyes y Decretos (más relevantes para sentencias)
            max_registros: 0 = todos
        """
        print(f"\n{'='*70}")
        print(f"INDEXADOR InfoLeg - Legislación Nacional")
        print(f"{'='*70}")
        print(f"CSV: {csv_path}")
        print(f"Solo prioritarios: {solo_prioritarios} {TIPOS_PRIORITARIOS if solo_prioritarios else ''}")
        print(f"{'='*70}\n")

        coleccion = self._get_coleccion()
        buffer = {"ids": [], "documents": [], "metadatas": []}
        stats = {"leidos": 0, "indexados": 0, "descartados": 0, "por_rama": {}}
        start = time.time()

        with open(csv_path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in tqdm(reader, desc="Indexando normas", unit=" normas"):
                stats["leidos"] += 1
                if max_registros and stats["leidos"] > max_registros:
                    break

                tipo = row.get("tipo_norma", "").strip()
                if solo_prioritarios and tipo not in TIPOS_PRIORITARIOS:
                    continue

                doc = preparar_norma(row)
                if not doc:
                    stats["descartados"] += 1
                    continue

                buffer["ids"].append(doc["id"])
                buffer["documents"].append(doc["text"])
                buffer["metadatas"].append(doc["metadata"])

                if len(buffer["ids"]) >= BATCH_SIZE:
                    self._flush(coleccion, buffer, stats)
                    buffer = {"ids": [], "documents": [], "metadatas": []}

        if buffer["ids"]:
            self._flush(coleccion, buffer, stats)

        elapsed = time.time() - start
        print(f"\n{'='*70}")
        print(f"INDEXACIÓN COMPLETADA en {elapsed:.1f}s")
        print(f"  Leídas:    {stats['leidos']:>10,}")
        print(f"  Indexadas: {stats['indexados']:>10,}")
        print(f"  Por rama:")
        for rama, c in sorted(stats["por_rama"].items(), key=lambda x: -x[1]):
            print(f"    {rama:40s} {c:>8,}")
        print(f"{'='*70}")
        return stats

    def _flush(self, coleccion, buffer, stats):
        try:
            coleccion.upsert(
                ids=buffer["ids"],
                documents=buffer["documents"],
                metadatas=buffer["metadatas"]
            )
            for meta in buffer["metadatas"]:
                r = meta.get("rama", "sin_clasificar")
                stats["por_rama"][r] = stats["por_rama"].get(r, 0) + 1
            stats["indexados"] += len(buffer["ids"])
        except Exception as e:
            print(f"\nERROR flush: {e}")

    def buscar_normas(self, query: str, rama: str = None,
                      n_results: int = 5) -> list[dict]:
        """Busca normas relevantes para una consulta"""
        coleccion = self._get_coleccion()
        if coleccion.count() == 0:
            return []

        where = {"rama": rama} if rama else None
        try:
            results = coleccion.query(
                query_texts=[query],
                n_results=min(n_results, coleccion.count()),
                where=where
            )
            out = []
            for i, doc in enumerate(results["documents"][0]):
                out.append({
                    "texto": doc,
                    "metadata": results["metadatas"][0][i],
                    "distancia": results["distances"][0][i],
                })
            return out
        except Exception as e:
            print(f"Error búsqueda: {e}")
            return []


if __name__ == "__main__":
    idx = IndexadorInfoLeg()
    idx.indexar(solo_prioritarios=True)
