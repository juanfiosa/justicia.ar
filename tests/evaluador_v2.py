"""
EVALUADOR v2 - JUSTICIA ARGENTINA
===================================
Mejoras sobre v1:
  - Solo casos post-2015 (CCyCN vigente → no hay mismatch temporal)
  - Evaluación de ESTRUCTURA (VISTOS/CONSIDERANDO/RESUELVO)
  - Evaluación de CONGRUENCIA (el RESUELVO responde las cuestiones)
  - Evaluación de DENSIDAD NORMATIVA (cantidad de normas por sección)
  - Score compuesto automático (sin necesidad de jueces)
"""

import json, re, time, urllib.request
from pathlib import Path
from datetime import datetime

API_URL        = "http://localhost:8000"
SAIJ_PATH      = Path("L:/JusticiaArgentina/datos/jurisprudencia_saij/dataset.jsonl")
SKIP_REGISTROS = 20_000
N_CASOS        = 100
PAUSA          = 5   # 12 req/min < 20 RPM free tier limit
SALIDA         = Path("L:/JusticiaArgentina/tests/resultados_v2.jsonl")
RESUMEN        = Path("L:/JusticiaArgentina/tests/resumen_v2.json")

MATERIA_A_RAMA = {
    "CIVIL": "civil_comercial", "COMERCIAL": "civil_comercial",
    "PENAL": "penal", "LABORAL": "laboral",
    "ADMINISTRATIVO": "administrativo", "TRIBUTARIO": "tributario",
    "CONSTITUCIONAL": "constitucional", "PROCESAL": "procesal",
}

def materia_a_rama(m):
    m = m.upper()
    for k, v in MATERIA_A_RAMA.items():
        if k in m: return v
    return "civil_comercial"

def limpiar(t):
    if not t: return ""
    t = re.sub(r'\[\[p\]\]', '\n', t)
    t = re.sub(r'\[\[r [^\]]+\]\]', '', t)
    t = re.sub(r'\[\[.*?\]\]', '', t)
    return t.strip()

def extraer_fecha(reg):
    f = reg.get('fecha', '') or ''
    m = re.search(r'(\d{4})', f)
    return int(m.group(1)) if m else 0

def extraer_normas(texto):
    normas = set()
    for m in re.finditer(r'[Ll]ey\s+(\d[\d\.]{3,})', texto):
        normas.add(f"Ley{m.group(1).replace('.','')}")
    for m in re.finditer(r'art[íi]culo[s]?\s*\.?\s*(\d+)', texto, re.I):
        normas.add(f"art{m.group(1)}")
    if re.search(r'CCyCN|C[óo]digo Civil.*Comercial|CCCN', texto): normas.add("CCyCN")
    if re.search(r'C[óo]digo Penal|C\.P\.\b', texto): normas.add("CP")
    if re.search(r'\bLCT\b|20\.744', texto): normas.add("LCT")
    if re.search(r'CPCCN|C[óo]digo Procesal', texto): normas.add("CPCCN")
    return normas

# ── Evaluación de estructura ──────────────────────────────────────────────────

def evaluar_estructura(resultado_api: dict) -> dict:
    """
    Puntúa la sentencia generada en 5 dimensiones automáticamente.
    Cada dimensión vale 0-1. Score final = promedio.
    """
    texto = resultado_api.get('texto_completo', '')
    tu = texto.upper()

    # 1. ESTRUCTURA FORMAL: tiene las 3 secciones
    tiene_vistos       = bool(re.search(r'\bVISTOS\b', tu))
    tiene_considerando = bool(re.search(r'\bCONSIDERANDO\b', tu))
    tiene_resuelvo     = bool(re.search(r'\bRESUELVO\b', tu))
    estructura = (tiene_vistos + tiene_considerando + tiene_resuelvo) / 3

    # 2. DENSIDAD NORMATIVA: número de normas citadas (>3 = bueno)
    normas_gen = extraer_normas(texto)
    densidad = min(len(normas_gen) / 5, 1.0)  # 5 normas = 100%

    # 3. CONGRUENCIA: el RESUELVO menciona a las partes
    resuelvo = resultado_api.get('resuelvo', '')
    partes_en_resuelvo = bool(re.search(
        r'[Hh]acer lugar|[Rr]echazar|[Cc]ondenar|[Aa]bsolver|[Dd]eclarar',
        resuelvo
    ))
    congruencia = 1.0 if partes_en_resuelvo else 0.0

    # 4. EXTENSIÓN DE CONSIDERANDOS: razonamiento desarrollado (>500 chars = bien)
    considerandos = resultado_api.get('considerandos', '')
    extension = min(len(considerandos) / 1500, 1.0)

    # 5. SECCIONES NUMERADAS: ¿los considerandos están ordenados?
    secciones = len(re.findall(r'\b[IVX]+\.\s|\b\d+\.\s', considerandos))
    orden = min(secciones / 4, 1.0)  # 4 secciones = 100%

    score = (estructura + densidad + congruencia + extension + orden) / 5

    return {
        "estructura_formal": round(estructura, 2),
        "densidad_normativa": round(densidad, 2),
        "congruencia_resuelvo": round(congruencia, 2),
        "extension_considerandos": round(extension, 2),
        "secciones_ordenadas": round(orden, 2),
        "score_estructural": round(score, 3),
        "normas_citadas": list(normas_gen),
    }

def metricas_normativas(normas_reales, normas_gen):
    if not normas_reales:
        return None
    inter = normas_reales & normas_gen
    p = len(inter) / len(normas_gen) if normas_gen else 0
    r = len(inter) / len(normas_reales)
    f1 = 2*p*r/(p+r) if (p+r) > 0 else 0
    return {"precision": round(p,3), "recall": round(r,3), "f1": round(f1,3),
            "reales": list(normas_reales), "generadas": list(normas_gen)}

def construir_caso(reg):
    texto = limpiar(reg.get('texto','') or '')
    if len(texto) < 300: return None
    caratula = reg.get('caratula','') or reg.get('titulo','') or 'Sin carátula'
    materia  = reg.get('materia','') or ''
    return {
        "caratula": caratula[:200],
        "expediente": (reg.get('id','') or '')[:50],
        "rama": materia_a_rama(materia),
        "tipo_proceso": "ordinario",
        "tribunal": (reg.get('tribunal','') or '')[:100],
        "hechos_probados": ' '.join(texto.split()[:150]),
        "nivel_complejidad": None,
        "hay_cuestion_constitucional": False,
        "cuestiones_a_resolver": [f"Resolver la cuestión jurídica en materia {materia}"],
        "partes": [
            {"nombre":"Actor","rol":"actor","pretension":"Tutela judicial efectiva.",
             "fundamentos_juridicos":"Normativa vigente argentina.","jurisprudencia_citada":""},
            {"nombre":"Demandado","rol":"demandado","pretension":"Rechazo de la pretensión.",
             "fundamentos_juridicos":"Carece de fundamento suficiente.","jurisprudencia_citada":""}
        ]
    }

def llamar_api(caso):
    data = json.dumps(caso).encode('utf-8')
    req  = urllib.request.Request(f"{API_URL}/api/generar", data=data,
                                   headers={"Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def main():
    print(f"[{datetime.now():%H:%M:%S}] EVALUADOR v2 — solo post-2015 + evaluación estructural")

    casos_candidatos = []
    print(f"Cargando registros desde posición {SKIP_REGISTROS:,}...")
    with open(SAIJ_PATH,'r',encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i < SKIP_REGISTROS: continue
            if len(casos_candidatos) >= N_CASOS * 5: break
            try:
                reg = json.loads(line.strip())
                if extraer_fecha(reg) < 2015: continue   # ← FILTRO CLAVE
                caso = construir_caso(reg)
                if caso: casos_candidatos.append((reg, caso))
            except: continue

    print(f"  Candidatos post-2015: {len(casos_candidatos)}")
    seleccionados = casos_candidatos[:N_CASOS]
    print(f"  Seleccionados:        {len(seleccionados)}\n")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    resultados, scores, f1s, errores, demos = [], [], [], 0, 0

    for i, (reg_real, caso) in enumerate(seleccionados):
        print(f"[{datetime.now():%H:%M:%S}] {i+1:3}/{len(seleccionados)}  {caso['caratula'][:55]}...", end=' ')
        r = llamar_api(caso)
        if "error" in r:
            print(f"ERROR: {r['error'][:50]}"); errores += 1; continue
        if any("DEMOSTRACIÓN" in a for a in r.get('advertencias',[])):
            print("DEMO"); demos += 1; continue
        texto_c = r.get('texto_completo', '')
        if texto_c.startswith('ERROR') or 'RESOURCE_EXHAUSTED' in texto_c or len(texto_c) < 100:
            print(f"GEMINI_ERROR: {texto_c[:80]}"); errores += 1; continue

        struct  = evaluar_estructura(r)
        normas_reales = extraer_normas(limpiar(reg_real.get('texto','') or ''))
        normas_gen    = set(extraer_normas(r.get('texto_completo','')))
        mn = metricas_normativas(normas_reales, normas_gen)

        scores.append(struct['score_estructural'])
        if mn: f1s.append(mn['f1'])

        resultado = {
            "id": i+1, "caratula": caso['caratula'],
            "rama": caso['rama'], "año": extraer_fecha(reg_real),
            "nivel_auto": r.get('nivel_complejidad'),
            "confianza": r.get('confianza'),
            "estructura": struct,
            "normas": mn,
        }
        resultados.append(resultado)
        with open(SALIDA,'a',encoding='utf-8') as out:
            out.write(json.dumps(resultado, ensure_ascii=False)+'\n')

        f1_str = f"F1={mn['f1']:.2f}" if mn else "sin_normas"
        print(f"OK  score={struct['score_estructural']:.2f}  {f1_str}")
        time.sleep(PAUSA)

    # Resumen
    n = len(resultados)
    resumen = {
        "fecha": datetime.now().isoformat(),
        "total": n, "errores": errores, "demo": demos,
        "score_estructural_promedio": round(sum(scores)/len(scores),3) if scores else 0,
        "f1_normativo_promedio":      round(sum(f1s)/len(f1s),3) if f1s else 0,
        "f1_casos_con_normas":        len(f1s),
        "confianza_promedio":         round(sum(r['confianza'] for r in resultados)/n,3) if n else 0,
        "distribucion_niveles": {str(lv): sum(1 for r in resultados if str(r['nivel_auto'])==str(lv))
                                  for lv in [1,2,3]},
        "dimensiones_promedio": {
            dim: round(sum(r['estructura'][dim] for r in resultados)/n, 3)
            for dim in ['estructura_formal','densidad_normativa','congruencia_resuelvo',
                        'extension_considerandos','secciones_ordenadas']
        } if n else {}
    }
    with open(RESUMEN,'w',encoding='utf-8') as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print("RESUMEN v2")
    print(f"{'='*60}")
    print(f"  Casos evaluados:          {n}")
    print(f"  Score estructural prom:   {resumen['score_estructural_promedio']:.3f}")
    print(f"  F1 normativo prom:        {resumen['f1_normativo_promedio']:.3f}  ({len(f1s)} casos con normas)")
    print(f"  Distribución niveles:     {resumen['distribucion_niveles']}")
    print(f"  Dimensiones:")
    for k,v in resumen['dimensiones_promedio'].items():
        print(f"    {k:35s}: {v:.3f}")
    print(f"\n  Guardado en: {RESUMEN}")

if __name__=="__main__":
    main()
