"""
INDEXADOR COMPLETO — SAIJ + InfoLeg + Legislación Provincial
=============================================================
Ejecuta en secuencia:
  1. SAIJ jurisprudencia         (desde checkpoint, sin límite)
  2. InfoLeg legislación nacional(desde checkpoint, sin límite)
  3. Legislación provincial      (metadata CSV + textos completos)

Ante QuotaExhaustedError (cuota diaria Gemini agotada) termina limpiamente
conservando los checkpoints; el Task Scheduler lo relanza a medianoche UTC.
"""

import sys
import os
from pathlib import Path

# Ruta absoluta al directorio del proyecto (funciona desde cualquier cwd)
_PROJ = Path(__file__).resolve().parent

sys.path.insert(0, str(_PROJ / 'src'))
# User site-packages (saij-mcp, google-genai instalados ahí)
sys.path.insert(0, "C:/Users/Juan/AppData/Roaming/Python/Python314/site-packages")

from dotenv import load_dotenv
load_dotenv(_PROJ / '.env', override=True)

from indexador.qdrant_store import QuotaExhaustedError

# ── Rutas de checkpoints ────────────────────────────────────────────────────
BASE = _PROJ
CP_SAIJ      = str(BASE / 'datos' / 'checkpoint_saij.json')
CP_SAIJ_LIVE = str(BASE / 'datos' / 'checkpoint_saij_live.json')
CP_INFOLEG   = str(BASE / 'datos' / 'checkpoint_infoleg.json')
CP_PROV_F1   = str(BASE / 'datos' / 'checkpoint_provincial_fase1.json')
CP_PROV_F2   = str(BASE / 'datos' / 'checkpoint_provincial_fase2.json')
CSV_INFOLEG  = str(BASE / 'datos' / 'base-infoleg-normativa-nacional.csv')
CSV_PROV     = str(BASE / 'datos' / 'saij_normativa_provincial.csv')
FUENTES_PROV = str(BASE / 'datos' / 'fuentes_textos_provinciales.json')
TEXTOS_DIR   = str(BASE / 'datos' / 'textos_provinciales')

# ═══════════════════════════════════════════════════════════════
# ORDEN DE PRIORIDAD:
#   1. InfoLeg nacional  (~1k normas, textos cortos = alta cobertura/token)
#   2. Legislación provincial (~80k normas, ídem)
#   3. SAIJ Live         (sumarios 2024-2026, textos medianos)
#   4. SAIJ dump         (873k fallos históricos, textos largos = más cuota)
#
# Así la legislación queda indexada antes de que se agote la cuota,
# y el dump histórico avanza incrementalmente en lo que sobre.
# ═══════════════════════════════════════════════════════════════

# ── 1. InfoLeg Legislación Nacional ────────────────────────────────────────
print("=" * 60)
print("PASO 1 — InfoLeg Legislacion Nacional (~1k normas)")
print("=" * 60)

try:
    from indexador.infoleg_qdrant import IndexadorInfoLegQdrant
    idx_infoleg = IndexadorInfoLegQdrant()
    n_infoleg = idx_infoleg.indexar(
        csv_path=CSV_INFOLEG,
        solo_prioritarios=False,
        max_registros=None,
        checkpoint_path=CP_INFOLEG
    )
    print(f"InfoLeg completado: {n_infoleg} normas indexadas.\n")

except QuotaExhaustedError as e:
    print(f"\n[CUOTA AGOTADA en InfoLeg] {e}")
    print("El scheduler lo retomara manana desde el checkpoint guardado.")
    sys.exit(0)

except Exception as e:
    print(f"\n[ERROR InfoLeg] {e}")

# ── 2. Legislación Provincial ───────────────────────────────────────────────
print("=" * 60)
print("PASO 2 — Legislacion Provincial (~80k normas)")
print("=" * 60)

try:
    from indexador.provincial_qdrant import IndexadorProvincialQdrant
    idx_prov = IndexadorProvincialQdrant()

    n_prov1 = idx_prov.indexar_csv(
        csv_path=CSV_PROV,
        solo_vigentes=True,
        checkpoint_path=CP_PROV_F1,
    )
    print(f"Provincial Fase 1: {n_prov1} normas indexadas.\n")

    n_prov2 = idx_prov.indexar_textos_completos(
        textos_dir=TEXTOS_DIR,
        checkpoint_path=CP_PROV_F2,
    )
    if n_prov2:
        print(f"Provincial Fase 2: {n_prov2} articulos indexados.\n")

except QuotaExhaustedError as e:
    print(f"\n[CUOTA AGOTADA en Provincial] {e}")
    print("El scheduler lo retomara manana desde el checkpoint guardado.")
    sys.exit(0)

except Exception as e:
    print(f"\n[ERROR Provincial] {e}")

# ── 3. SAIJ Live — sumarios actuales 2024-2026 ─────────────────────────────
print("=" * 60)
print("PASO 3 — SAIJ Live (sumarios recientes via API)")
print("=" * 60)

try:
    from indexador.saij_live import IndexadorSAIJLive
    idx_live = IndexadorSAIJLive()
    n_live = idx_live.indexar(
        solo_desde_anio=2024,
        checkpoint_path=CP_SAIJ_LIVE,
    )
    print(f"SAIJ Live completado: {n_live} sumarios indexados.\n")

except QuotaExhaustedError as e:
    print(f"\n[CUOTA AGOTADA en SAIJ Live] {e}")
    print("El scheduler lo retomara manana desde el checkpoint guardado.")
    sys.exit(0)

except Exception as e:
    print(f"\n[ERROR SAIJ Live] {e}")

# ── 4. SAIJ dump histórico (avanza incrementalmente) ───────────────────────
print("=" * 60)
print("PASO 4 — SAIJ Jurisprudencia historica (dump local)")
print("=" * 60)

try:
    from indexador.pipeline_qdrant import IndexadorJurisprudenciaQdrant
    idx_saij = IndexadorJurisprudenciaQdrant()
    n_saij = idx_saij.indexar_dataset(
        dataset_path=str(BASE / 'datos' / 'jurisprudencia_saij' / 'dataset.jsonl'),
        checkpoint_path=CP_SAIJ,
        max_registros=None,
    )
    print(f"SAIJ dump completado: {n_saij} documentos indexados.\n")

except QuotaExhaustedError as e:
    print(f"\n[CUOTA AGOTADA en SAIJ dump] {e}")
    print("El scheduler lo retomara manana desde el checkpoint guardado.")
    sys.exit(0)

except Exception as e:
    print(f"\n[ERROR SAIJ dump] {e}")

print("=" * 60)
print("Indexación completa.")
print("=" * 60)
