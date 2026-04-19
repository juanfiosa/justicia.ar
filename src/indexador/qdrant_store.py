"""
MÓDULO: QDRANT STORE
=====================
Cliente centralizado para Qdrant Cloud.
Embeddings: Google Gemini gemini-embedding-001 (3072 dims, via API).
Throttling proactivo para respetar el rate limit del free tier (100 req/min).
"""

import os
import re
import time
from typing import Optional

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_DISPONIBLE = True
except ImportError:
    QDRANT_DISPONIBLE = False

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 3072

# Máximo de reintentos consecutivos por cuota diaria agotada
MAX_RETRIES_CUOTA = 5


class QuotaExhaustedError(Exception):
    """La cuota diaria de Gemini está agotada. Reintentar mañana."""
    pass

# Estado de throttling compartido entre llamadas
_rate_state = {"requests_this_window": 0, "window_start": 0.0}
_MAX_RPM = 90  # margen de seguridad bajo el límite real de 100


def _get_client():
    from google import genai
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY no configurada")
    return genai.Client(api_key=api_key)


def _throttle(n_requests: int):
    """Duerme proactivamente para no superar _MAX_RPM requests/minuto."""
    state = _rate_state
    now = time.time()

    # Reiniciar ventana si pasó más de 60 segundos
    if now - state["window_start"] >= 60:
        state["window_start"] = now
        state["requests_this_window"] = 0

    # Si este batch superaría el límite, esperar hasta el próximo minuto
    if state["requests_this_window"] + n_requests > _MAX_RPM:
        elapsed = now - state["window_start"]
        wait = max(0.0, 61.0 - elapsed)
        if wait > 0:
            print(f"  [throttle] {state['requests_this_window']} req usados — esperando {wait:.1f}s")
            time.sleep(wait)
        state["window_start"] = time.time()
        state["requests_this_window"] = 0

    state["requests_this_window"] += n_requests


def embed_textos(textos: list[str], batch_size: int = 50) -> list[list[float]]:
    """Genera embeddings en batch con throttling proactivo y retry ante 429.

    La API actual acepta una lista de textos en un solo call.
    Cada texto en la lista cuenta como 1 request para el rate limit.
    """
    client = _get_client()
    resultados = []

    for inicio in range(0, len(textos), batch_size):
        lote = textos[inicio:inicio + batch_size]
        n = len(lote)

        # Throttling proactivo ANTES de hacer la llamada
        _throttle(n)

        intentos = 0
        while True:
            try:
                res = client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=lote
                )
                for emb in res.embeddings:
                    resultados.append(list(emb.values))
                break
            except Exception as e:
                msg = str(e)
                if '429' in msg or 'RESOURCE_EXHAUSTED' in msg:
                    match = re.search(r'retryDelay["\s:]+(\d+)s', msg)
                    if not match:
                        match = re.search(r'retry.*?(\d{1,3})s', msg, re.IGNORECASE)
                    espera = min(int(match.group(1)) + 5, 120) if match else 65
                    intentos += 1
                    print(f"  [429] Rate limit, esperando {espera}s (intento {intentos}/{MAX_RETRIES_CUOTA})")
                    if intentos >= MAX_RETRIES_CUOTA:
                        raise QuotaExhaustedError(
                            f"Cuota diaria Gemini agotada tras {intentos} reintentos. "
                            "Reintentar mañana (medianoche UTC)."
                        )
                    time.sleep(espera)
                    _rate_state["window_start"] = time.time()
                    _rate_state["requests_this_window"] = 0
                else:
                    raise

    return resultados


def embed_query(texto: str) -> list[float]:
    """Genera embedding para una query de búsqueda."""
    _throttle(1)
    client = _get_client()
    res = client.models.embed_content(model=EMBEDDING_MODEL, contents=texto)
    return list(res.embeddings[0].values)


def get_qdrant_client() -> Optional[object]:
    if not QDRANT_DISPONIBLE:
        return None
    url = os.environ.get('QDRANT_URL', '')
    api_key = os.environ.get('QDRANT_API_KEY', '')
    if not url or not api_key:
        return None
    return QdrantClient(url=url, api_key=api_key)


def crear_coleccion_si_no_existe(client: object, nombre: str):
    colecciones = [c.name for c in client.get_collections().collections]
    if nombre not in colecciones:
        client.create_collection(
            collection_name=nombre,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )
        print(f"Colección creada: {nombre}")
    return nombre
