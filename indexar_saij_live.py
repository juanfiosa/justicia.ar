"""
INDEXADOR SAIJ LIVE
====================
Descarga sumarios recientes (2024+) desde la API de SAIJ y los indexa
en Qdrant. Complementa el dump histórico local con contenido actualizado.

Uso:
  python indexar_saij_live.py              # indexa desde 2024
  python indexar_saij_live.py --desde 2025 # solo desde 2025
  python indexar_saij_live.py --test       # prueba sin indexar
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, "C:/Users/Juan/AppData/Roaming/Python/Python314/site-packages")

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')

BASE = Path(__file__).parent
CP = str(BASE / 'datos' / 'checkpoint_saij_live.json')


def test_api():
    """Verifica que la API de SAIJ esté accesible y muestra una muestra."""
    from saij_mcp.client import search
    print("Probando API SAIJ...")
    r = search("despido", doc_type="sumario", limit=3)
    print(f"  Total sumarios 'despido': {r['total']}")
    facets_fecha = r.get("facets", {}).get("Fecha", {})
    if facets_fecha:
        anios = sorted(facets_fecha.items(), reverse=True)[:5]
        print(f"  Años disponibles: {anios}")
    for doc in r["results"][:2]:
        print(f"  - {doc.get('fecha','')} | {doc.get('jurisdiccion','')} | "
              f"{str(doc.get('texto',''))[:80]}...")
    print("API OK.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--desde', type=int, default=2024,
                        help='Año mínimo a indexar (default: 2024)')
    parser.add_argument('--test', action='store_true',
                        help='Solo prueba la API, sin indexar')
    args = parser.parse_args()

    if args.test:
        test_api()
        return

    from indexador.qdrant_store import QuotaExhaustedError
    from indexador.saij_live import IndexadorSAIJLive

    print(f"Indexando sumarios SAIJ desde {args.desde}...")
    try:
        idx = IndexadorSAIJLive()
        n = idx.indexar(solo_desde_anio=args.desde, checkpoint_path=CP)
        print(f"\nCompletado: {n} sumarios indexados.")
    except QuotaExhaustedError as e:
        print(f"\n[CUOTA AGOTADA] {e}")
        print("Reanudar mañana — checkpoint guardado.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
