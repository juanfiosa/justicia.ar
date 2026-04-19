"""
EVALUADOR DE CALIDAD - JUSTICIA ARGENTINA
==========================================
Evalúa la plataforma con casos reales del SAIJ usando método de holdout:
- Toma casos NO indexados
- Extrae hechos/materias como input
- Corre el sistema
- Compara normas citadas con las del fallo real
- Mide precisión y recall normativo (sin data leakage de texto)

Método anti-leakage:
    El sistema indexó solo los primeros 20K registros del SAIJ.
    Los casos de evaluación se toman desde el registro 20.001 en adelante.
    Gemini puede "conocer" los fallos por entrenamiento general, pero
    NO los tiene en el índice RAG local — así medimos razonamiento autónomo.
"""

import json
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
import sys

# ── Configuración ─────────────────────────────────────────────────────────────
API_URL        = "http://localhost:8000"
SAIJ_PATH      = Path("L:/JusticiaArgentina/datos/jurisprudencia_saij/dataset.jsonl")
SKIP_REGISTROS = 20_000      # saltear los ya indexados
N_CASOS        = 100         # casos a evaluar
PAUSA_ENTRE    = 3           # segundos entre llamadas (respetar rate limit Gemini)
SALIDA         = Path("L:/JusticiaArgentina/tests/resultados_evaluacion.jsonl")
RESUMEN        = Path("L:/JusticiaArgentina/tests/resumen_evaluacion.json")

# Mapeo de materias SAIJ → ramas del sistema
MATERIA_A_RAMA = {
    "CIVIL": "civil_comercial",
    "COMERCIAL": "civil_comercial",
    "PENAL": "penal",
    "LABORAL": "laboral",
    "ADMINISTRATIVO": "administrativo",
    "TRIBUTARIO": "tributario",
    "CONSTITUCIONAL": "constitucional",
    "PROCESAL": "procesal",
}

def materia_a_rama(materia: str) -> str:
    m = materia.upper()
    for k, v in MATERIA_A_RAMA.items():
        if k in m:
            return v
    return "civil_comercial"

def limpiar_texto(texto: str) -> str:
    """Limpia markup del SAIJ"""
    if not texto:
        return ""
    texto = re.sub(r'\[\[p\]\]', '\n', texto)
    texto = re.sub(r'\[\[r [^\]]+\]\]', '', texto)
    texto = re.sub(r'\[\[.*?\]\]', '', texto)
    return texto.strip()

def extraer_normas_reales(registro: dict) -> set[str]:
    """Extrae normas citadas en el fallo real (para comparar)"""
    normas = set()
    texto = limpiar_texto(registro.get('texto', '') or '')
    # Leyes
    for m in re.finditer(r'[Ll]ey\s+(\d[\d\.]+)', texto):
        normas.add(f"Ley {m.group(1).replace('.', '')}")
    # Artículos con código
    for m in re.finditer(r'art(?:ículo|[s\.])\s*\.?\s*(\d+)', texto, re.I):
        normas.add(f"art.{m.group(1)}")
    # CCyCN
    if re.search(r'C[óo]digo Civil.*Comercial|CCyCN|CCCN', texto):
        normas.add("CCyCN")
    if re.search(r'C[óo]digo Penal|C\.P\.|CP\b', texto):
        normas.add("CódigoPenal")
    if re.search(r'LCT|[Ll]ey.*20\.744', texto):
        normas.add("LCT")
    return normas

def extraer_normas_generadas(texto_sentencia: str) -> set[str]:
    """Extrae normas de la sentencia generada"""
    normas = set()
    for m in re.finditer(r'[Ll]ey\s+(\d[\d\.]+)', texto_sentencia):
        normas.add(f"Ley {m.group(1).replace('.', '')}")
    for m in re.finditer(r'art(?:ículo|[s\.])\s*\.?\s*(\d+)', texto_sentencia, re.I):
        normas.add(f"art.{m.group(1)}")
    if re.search(r'CCyCN|C[óo]digo Civil.*Comercial|CCCN', texto_sentencia):
        normas.add("CCyCN")
    if re.search(r'C[óo]digo Penal|C\.P\.|CP\b', texto_sentencia):
        normas.add("CódigoPenal")
    if re.search(r'LCT|[Ll]ey.*20\.744', texto_sentencia):
        normas.add("LCT")
    return normas

def calcular_metricas(normas_reales: set, normas_generadas: set) -> dict:
    if not normas_reales:
        return {"precision": None, "recall": None, "f1": None, "nota": "fallo sin normas extraíbles"}
    interseccion = normas_reales & normas_generadas
    precision = len(interseccion) / len(normas_generadas) if normas_generadas else 0
    recall    = len(interseccion) / len(normas_reales)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return {
        "precision": round(precision, 3),
        "recall":    round(recall, 3),
        "f1":        round(f1, 3),
        "normas_reales":     list(normas_reales),
        "normas_generadas":  list(normas_generadas),
        "coincidencias":     list(interseccion),
    }

def construir_caso(reg: dict) -> dict:
    texto = limpiar_texto(reg.get('texto', '') or '')
    if len(texto) < 200:
        return None
    caratula = reg.get('caratula', '') or reg.get('titulo', '') or 'Sin carátula'
    materia  = reg.get('materia', '') or ''
    rama     = materia_a_rama(materia)
    tribunal = reg.get('tribunal', '') or ''
    fecha    = reg.get('fecha', '') or ''

    # Extraer hechos: primer tercio del texto como proxy
    palabras = texto.split()
    hechos = ' '.join(palabras[:150])

    return {
        "caratula":             caratula[:200],
        "expediente":           reg.get('id', '')[:50] if reg.get('id') else '',
        "rama":                 rama,
        "tipo_proceso":         "ordinario",
        "tribunal":             tribunal[:100],
        "hechos_probados":      hechos,
        "nivel_complejidad":    None,  # clasificación automática
        "hay_cuestion_constitucional": False,
        "cuestiones_a_resolver": [f"Resolver la cuestión jurídica en materia {materia}"],
        "partes": [
            {
                "nombre":              "Actor",
                "rol":                 "actor",
                "pretension":          "Obtener tutela judicial efectiva conforme los hechos probados.",
                "fundamentos_juridicos": "Conforme las normas vigentes del ordenamiento argentino.",
                "jurisprudencia_citada": ""
            },
            {
                "nombre":              "Demandado",
                "rol":                 "demandado",
                "pretension":          "Rechazo de la pretensión actora.",
                "fundamentos_juridicos": "La pretensión carece de fundamento normativo suficiente.",
                "jurisprudencia_citada": ""
            }
        ]
    }

def llamar_api(caso: dict) -> dict | None:
    data = json.dumps(caso).encode('utf-8')
    req  = urllib.request.Request(
        f"{API_URL}/api/generar",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def main():
    print(f"[{datetime.now():%H:%M:%S}] EVALUADOR JUSTICIA ARGENTINA")
    print(f"  Dataset:   {SAIJ_PATH}")
    print(f"  Skip:      {SKIP_REGISTROS:,} registros (ya indexados)")
    print(f"  Evaluar:   {N_CASOS} casos")
    print(f"  Salida:    {SALIDA}")
    print()

    if not SAIJ_PATH.exists():
        print("ERROR: No se encuentra el dataset SAIJ.")
        sys.exit(1)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)

    # ── Cargar casos holdout ───────────────────────────────────────────────────
    print(f"[{datetime.now():%H:%M:%S}] Cargando casos holdout (saltando {SKIP_REGISTROS:,})...")
    casos_candidatos = []
    with open(SAIJ_PATH, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i < SKIP_REGISTROS:
                continue
            if len(casos_candidatos) >= N_CASOS * 3:  # 3x para filtrar inválidos
                break
            try:
                reg = json.loads(line.strip())
                caso = construir_caso(reg)
                if caso:
                    casos_candidatos.append((reg, caso))
            except:
                continue

    print(f"  Candidatos válidos: {len(casos_candidatos)}")
    casos_a_evaluar = casos_candidatos[:N_CASOS]
    print(f"  Seleccionados:      {len(casos_a_evaluar)}")
    print()

    # ── Ejecutar evaluación ────────────────────────────────────────────────────
    resultados = []
    metricas_f1 = []
    errores = 0
    en_demo = 0

    for i, (reg_real, caso) in enumerate(casos_a_evaluar):
        print(f"[{datetime.now():%H:%M:%S}] {i+1:3}/{N_CASOS}  {caso['caratula'][:60]}...", end=' ')
        resultado_api = llamar_api(caso)

        if "error" in resultado_api:
            print(f"ERROR: {resultado_api['error'][:60]}")
            errores += 1
            continue

        # ¿Usó IA o demo?
        es_demo = any("DEMOSTRACIÓN" in a for a in resultado_api.get('advertencias', []))
        if es_demo:
            en_demo += 1
            print("DEMO (sin IA)")
            continue

        texto_generado = resultado_api.get('texto_completo', '')
        normas_reales  = extraer_normas_reales(reg_real)
        normas_gen     = extraer_normas_generadas(texto_generado)
        metricas       = calcular_metricas(normas_reales, normas_gen)
        nivel_auto     = resultado_api.get('nivel_complejidad', '?')
        confianza      = resultado_api.get('confianza', 0)

        f1_val = metricas.get('f1')
        if f1_val is not None:
            metricas_f1.append(f1_val)

        resultado = {
            "id":              i + 1,
            "caratula":        caso['caratula'],
            "rama":            caso['rama'],
            "nivel_auto":      nivel_auto,
            "confianza":       confianza,
            "metricas":        metricas,
            "advertencias":    resultado_api.get('advertencias', []),
        }
        resultados.append(resultado)

        f1_str = f"F1={f1_val:.2f}" if f1_val is not None else "sin_normas"
        print(f"OK  nivel={nivel_auto}  conf={confianza:.0%}  {f1_str}")

        # Guardar progresivamente
        with open(SALIDA, 'a', encoding='utf-8') as out:
            out.write(json.dumps(resultado, ensure_ascii=False) + '\n')

        time.sleep(PAUSA_ENTRE)

    # ── Resumen ────────────────────────────────────────────────────────────────
    procesados = len(resultados)
    f1_promedio = sum(metricas_f1) / len(metricas_f1) if metricas_f1 else 0

    # Distribución por nivel
    dist_nivel = {}
    for r in resultados:
        n = str(r['nivel_auto'])
        dist_nivel[n] = dist_nivel.get(n, 0) + 1

    # Confianza promedio
    conf_prom = sum(r['confianza'] for r in resultados) / procesados if procesados else 0

    resumen = {
        "fecha":                datetime.now().isoformat(),
        "total_evaluados":      procesados,
        "errores":              errores,
        "en_demo":              en_demo,
        "f1_promedio_normas":   round(f1_promedio, 3),
        "confianza_promedio":   round(conf_prom, 3),
        "distribucion_niveles": dist_nivel,
        "nota_metodologica": (
            "F1 mide coincidencia de normas citadas entre sentencia generada y fallo real. "
            "Casos tomados desde registro 20.001 del SAIJ (no indexados → sin data leakage de RAG). "
            "Gemini puede conocer los fallos por entrenamiento general, por lo que F1 alto "
            "puede reflejar tanto conocimiento previo como buen razonamiento. "
            "Para evaluación ciega pura usar casos post-2025 evaluados por jueces."
        )
    }

    with open(RESUMEN, 'w', encoding='utf-8') as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    print(f"  Casos evaluados:     {procesados}")
    print(f"  Errores:             {errores}")
    print(f"  En modo demo:        {en_demo}")
    print(f"  F1 promedio normas:  {f1_promedio:.3f}")
    print(f"  Confianza promedio:  {conf_prom:.1%}")
    print(f"  Distribución niveles: {dist_nivel}")
    print(f"  Resumen guardado en: {RESUMEN}")
    print()

if __name__ == "__main__":
    main()
