"""
INDEXADOR LEGISLACIÓN PROVINCIAL
=================================
Fase 1: indexa metadata de los ~80k registros del CSV SAIJ provincial.
Fase 2: descarga textos completos (Wayback Machine / URLs oficiales)
        y los indexa artículo por artículo.

Uso:
  python indexar_provincial.py             # ambas fases
  python indexar_provincial.py --fase 1    # solo metadata CSV
  python indexar_provincial.py --fase 2    # solo textos completos
  python indexar_provincial.py --scraping  # solo descarga (sin indexar)
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')

from indexador.qdrant_store import QuotaExhaustedError

BASE = Path(__file__).parent
CP_FASE1   = str(BASE / 'datos' / 'checkpoint_provincial_fase1.json')
CP_FASE2   = str(BASE / 'datos' / 'checkpoint_provincial_fase2.json')
CSV_PROV   = str(BASE / 'datos' / 'saij_normativa_provincial.csv')
FUENTES    = str(BASE / 'datos' / 'fuentes_textos_provinciales.json')
TEXTOS_DIR = str(BASE / 'datos' / 'textos_provinciales')


def run_fase1():
    print("=" * 60)
    print("FASE 1 — Metadata CSV SAIJ provincial (80k normas)")
    print("=" * 60)
    try:
        from indexador.provincial_qdrant import IndexadorProvincialQdrant
        idx = IndexadorProvincialQdrant()
        n = idx.indexar_csv(
            csv_path=CSV_PROV,
            solo_vigentes=True,
            solo_prioritarios=False,
            checkpoint_path=CP_FASE1,
        )
        print(f"Fase 1 completada: {n} normas indexadas.")
        return True
    except QuotaExhaustedError as e:
        print(f"\n[CUOTA AGOTADA en Fase 1] {e}")
        print("Reanudar mañana — checkpoint guardado.")
        return False
    except Exception as e:
        print(f"\n[ERROR Fase 1] {e}")
        import traceback; traceback.print_exc()
        return False


def run_scraping(tipos=None):
    """Descarga los textos completos de fuentes oficiales / Wayback Machine."""
    print("=" * 60)
    print("SCRAPING — Constituciones y códigos procesales")
    print("=" * 60)
    try:
        from indexador.scraper_provincial import descargar_todas_las_fuentes
        stats = descargar_todas_las_fuentes(
            fuentes_json=FUENTES,
            salida_dir=TEXTOS_DIR,
            tipos_filtro=tipos,
            forzar=False,
        )
        print(f"Scraping: {stats}")
        return True
    except Exception as e:
        print(f"\n[ERROR scraping] {e}")
        import traceback; traceback.print_exc()
        return False


def run_fase2():
    print("=" * 60)
    print("FASE 2 — Textos completos por artículo")
    print("=" * 60)
    # Primero descargar lo que falte
    run_scraping()

    try:
        from indexador.provincial_qdrant import IndexadorProvincialQdrant
        idx = IndexadorProvincialQdrant()
        n = idx.indexar_textos_completos(
            textos_dir=TEXTOS_DIR,
            checkpoint_path=CP_FASE2,
        )
        print(f"Fase 2 completada: {n} artículos indexados.")
        return True
    except QuotaExhaustedError as e:
        print(f"\n[CUOTA AGOTADA en Fase 2] {e}")
        print("Reanudar mañana — checkpoint guardado.")
        return False
    except Exception as e:
        print(f"\n[ERROR Fase 2] {e}")
        import traceback; traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='Indexador legislación provincial')
    parser.add_argument('--fase', type=int, choices=[1, 2],
                        help='1=solo metadata, 2=solo textos completos')
    parser.add_argument('--scraping', action='store_true',
                        help='Solo descarga textos (sin indexar)')
    args = parser.parse_args()

    if args.scraping:
        run_scraping()
        return

    if args.fase == 1:
        run_fase1()
        return

    if args.fase == 2:
        run_fase2()
        return

    # Sin argumentos: ambas fases
    ok1 = run_fase1()
    if not ok1:
        sys.exit(0)  # cuota agotada, el scheduler lo retoma
    run_fase2()


if __name__ == '__main__':
    main()
