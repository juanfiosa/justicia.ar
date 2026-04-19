"""
BENCHMARK 3 CASOS REALES CSJN
Evalua la calidad de las sentencias generadas vs. los fallos reales.
"""
import urllib.request, json, time, re
from pathlib import Path

BASE_URL = "http://localhost:8000"
OUT_DIR = Path(__file__).parent

def generar(caso):
    data = json.dumps(caso, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(f'{BASE_URL}/api/generar', data=data,
        headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())

def extraer_normas(texto):
    patrones = [
        r'[Aa]rt(?:ículo|iculo)?\.?\s*(\d+(?:\s*bis)?)',
        r'[Ll]ey\s+(\d{4,6})',
        r'[Dd]ecreto\s+(\d{3,5})',
        r'C\.?C\.?y\.?C\.?N\.?|CCyCN|C[oó]digo\s+Civil',
        r'L\.?C\.?T\.?|[Ll]ey\s+20\.?744',
        r'C\.?N\.?|[Cc]onstituci[oó]n\s+[Nn]acional',
        r'PIDESC|Pacto\s+Internacional',
        r'CADH|Convenci[oó]n\s+Americana',
        r'OIT|Convenio\s+\d+',
    ]
    encontradas = set()
    for p in patrones:
        for m in re.finditer(p, texto):
            encontradas.add(m.group(0).strip().upper()[:30])
    return encontradas

def evaluar(resultado, normas_reales_ref, decision_real):
    texto = resultado.get('texto_completo', '')
    resuelvo = resultado.get('resuelvo', '')
    considerandos = resultado.get('considerandos', '')

    # 1. Estructura formal
    tiene_vistos = 'VISTOS' in texto.upper()
    tiene_considerando = 'CONSIDERANDO' in texto.upper()
    tiene_resuelvo = 'RESUELVO' in texto.upper()
    estructura = (tiene_vistos + tiene_considerando + tiene_resuelvo) / 3

    # 2. Normas generadas vs. referencia
    normas_gen = extraer_normas(texto)
    normas_ref = set(n.upper() for n in normas_reales_ref)
    if normas_ref:
        precision = len(normas_gen & normas_ref) / len(normas_gen) if normas_gen else 0
        recall = len(normas_gen & normas_ref) / len(normas_ref)
        f1 = 2*precision*recall/(precision+recall) if (precision+recall) > 0 else 0
    else:
        precision = recall = f1 = None

    # 3. Congruencia con la decision real
    decision_correcta = decision_real.lower() in resuelvo.lower() if decision_real else None

    # 4. Extension considerandos
    extension = min(len(considerandos) / 2000, 1.0)

    return {
        'estructura': estructura,
        'f1_normas': f1,
        'precision_normas': precision,
        'recall_normas': recall,
        'normas_generadas': list(normas_gen),
        'decision_correcta': decision_correcta,
        'extension': extension,
        'nivel': resultado.get('nivel_complejidad'),
        'confianza': resultado.get('confianza'),
    }

# ================================================================
# CASO 1: PEREZ c/ DISCO (N1 - Rutinario - Laboral)
# CSJN 01/09/2009 - Fallos 332:2043
# Decision real: las sumas no remunerativas SON remuneracion
# ================================================================
caso1 = {
    'caratula': 'Perez, Anibal Nestor c/ Disco S.A. s/ accion declarativa',
    'expediente': 'P.489.XLIV',
    'rama': 'laboral',
    'tipo_proceso': 'ordinario',
    'tribunal': 'Corte Suprema de Justicia de la Nacion',
    'hechos_probados': 'El actor percibia sumas dinerarias denominadas no remunerativas en virtud de acuerdos colectivos homologados por el Ministerio de Trabajo. Esas sumas fueron pactadas como asignaciones no remunerativas de caracter alimentario para eludir el pago de contribuciones patronales y su incidencia en la indemnizacion por despido. No estaban sujetas a descuento jubilatorio ni se incluian en el recibo como remuneracion.',
    'partes': [
        {'nombre':'Perez, Anibal Nestor','rol':'actor',
         'pretension':'Que las sumas percibidas sean reconocidas como remuneracion y que se recalculen contribuciones, aportes e indemnizaciones',
         'fundamentos_juridicos':'Art. 14 bis CN. Art. 103 LCT (todo lo que percibe el trabajador por su trabajo es remuneracion). PIDESC art. 7. Convenio 95 OIT.',
         'jurisprudencia_citada':'Nordensthol c/ Subte CSJN 1985'},
        {'nombre':'Disco S.A.','rol':'demandado',
         'pretension':'Rechazo de la demanda',
         'fundamentos_juridicos':'Las sumas fueron pactadas en acuerdos colectivos homologados por autoridad estatal competente. El acto administrativo de homologacion otorga validez a la calificacion adoptada.',
         'jurisprudencia_citada':'Doctrina de la autonomia colectiva'}
    ],
    'cuestiones_a_resolver': [
        'Pueden los acuerdos colectivos homologados calificar como no remunerativa una suma pagada en razon del trabajo?',
        'Es constitucional esa calificacion frente al art. 14 bis CN y el PIDESC?'
    ]
}
NORMAS_REF_1 = ['art. 14 bis', 'art. 103', 'LCT', 'PIDESC', 'OIT', 'Ley 20744']
DECISION_REF_1 = 'remuneratori'  # palabra clave en el resuelvo real

# ================================================================
# CASO 2: VIZZOTI c/ AMSA (N2 - Dificil - Laboral)
# CSJN 14/09/2004 - Fallos 327:3677
# Decision real: inconstitucional la reduccion de mas del 33%
# ================================================================
caso2 = {
    'caratula': 'Vizzoti, Carlos Alberto c/ AMSA S.A. s/ despido',
    'expediente': 'V.967.XXXVIII',
    'rama': 'laboral',
    'tipo_proceso': 'ordinario',
    'tribunal': 'Corte Suprema de Justicia de la Nacion',
    'hechos_probados': 'Vizzoti fue despedido sin causa por AMSA S.A. tras 26 anios de antiguedad. Su mejor remuneracion mensual normal y habitual era de $11.465. El promedio de las remuneraciones del convenio colectivo aplicable era de $1.000. Aplicando el tope del art. 245 LCT (la base no puede superar el 67% del promedio del convenio, es decir $670), la indemnizacion calculada resultaba un 83% inferior a la que corresponderia si se usara la remuneracion real como base.',
    'partes': [
        {'nombre':'Vizzoti, Carlos Alberto','rol':'actor',
         'pretension':'Indemnizacion calculada sobre su remuneracion real de $11.465 sin aplicacion del tope del art. 245 LCT, o subsidiariamente que el tope sea declarado inconstitucional cuando reduzca la base en mas del 33%',
         'fundamentos_juridicos':'Art. 14 bis CN (proteccion contra el despido arbitrario). Art. 17 CN (no confiscatoriedad). Art. 28 CN (razonabilidad). Arts. 7 y 8 PIDESC.',
         'jurisprudencia_citada':'Bercaitz CSJN Fallos 289:430; doctrina de razonabilidad'},
        {'nombre':'AMSA S.A.','rol':'demandado',
         'pretension':'Rechazo. El tope del art. 245 LCT es valido',
         'fundamentos_juridicos':'El art. 245 LCT es norma valida sancionada por el Congreso. El tope busca equiparar indemnizaciones entre trabajadores. El legislador puede reglamentar derechos del art. 14 bis mientras no los suprima.',
         'jurisprudencia_citada':'Fernandez Arias Fallos 247:646; doctrina de deferencia legislativa'}
    ],
    'cuestiones_a_resolver': [
        'Es constitucional el tope del art. 245 LCT cuando reduce la base indemnizatoria en mas del 33% respecto de la remuneracion real?',
        'Cual es el umbral de razonabilidad por debajo del cual la reglamentacion del derecho a la proteccion contra el despido arbitrario deviene inconstitucional?'
    ]
}
NORMAS_REF_2 = ['art. 245', 'LCT', 'art. 14 bis', 'art. 28', 'art. 17', 'PIDESC', 'Ley 20744']
DECISION_REF_2 = 'inconstitucional'

# ================================================================
# CASO 3: HALABI c/ PEN (N3 - Constitucional)
# CSJN 24/02/2009 - Fallos 332:111
# Decision real: inconstitucional Ley 25.873; accion de clase reconocida
# ================================================================
caso3 = {
    'caratula': 'Halabi, Ernesto c/ P.E.N. - Ley 25.873 - Dec. 1563/04 s/ amparo ley 16.986',
    'expediente': 'H.270.XLII',
    'rama': 'constitucional',
    'tipo_proceso': 'amparo',
    'tribunal': 'Corte Suprema de Justicia de la Nacion',
    'hay_cuestion_constitucional': True,
    'hechos_probados': 'La Ley 25.873 y el Decreto 1563/04 obligaron a las empresas de telecomunicaciones a capturar y almacenar por 10 anios el contenido de todas las comunicaciones telefonicas e informaticas de los usuarios, poniendolas a disposicion del PEN sin requerir orden judicial. Halabi, abogado, interpuso amparo invocando que la ley vulneraba sus comunicaciones profesionales con clientes. La Camara hizo lugar al amparo con efectos erga omnes.',
    'partes': [
        {'nombre':'Halabi, Ernesto','rol':'actor',
         'pretension':'Inconstitucionalidad de la Ley 25.873 y Dec. 1563/04. Que se ordene al Estado abstenerse de interceptar sus comunicaciones y las de todos los usuarios en igual situacion',
         'fundamentos_juridicos':'Art. 18 CN (inviolabilidad correspondencia). Art. 19 CN (autonomia personal). Art. 43 CN (amparo). Ley 25.326 (habeas data). CADH art. 11 (vida privada). La interceptacion masiva sin control judicial viola el nucleo esencial del derecho a la privacidad.',
         'jurisprudencia_citada':'Urteaga CSJN Fallos 321:2767; Escher c/ Brasil Corte IDH'},
        {'nombre':'Poder Ejecutivo Nacional','rol':'demandado',
         'pretension':'Rechazo del amparo. La ley persigue fines legitimos de seguridad publica',
         'fundamentos_juridicos':'La ley persigue fines legitimos de seguridad y persecucion del delito. El Estado tiene deber de investigar crimen organizado. La restriccion a la privacidad es minima frente a la gravedad de los delitos que se buscan prevenir.',
         'jurisprudencia_citada':'Doctrina de seguridad nacional'}
    ],
    'cuestiones_a_resolver': [
        'La Ley 25.873 vulnera el derecho a la privacidad (arts. 18 y 19 CN) al permitir interceptacion masiva sin orden judicial?',
        'Existe en el ordenamiento argentino la accion de clase para derechos de incidencia colectiva referentes a derechos individuales homogeneos?',
        'Puede el amparo tener efectos erga omnes cuando hay un grupo de afectados en situacion analoga?'
    ]
}
NORMAS_REF_3 = ['art. 18', 'art. 19', 'art. 43', 'Ley 25.873', 'Ley 25.326', 'CADH', 'PIDESC']
DECISION_REF_3 = 'inconstitucional'

# ================================================================
# EJECUTAR
# ================================================================
casos = [
    ('CASO 1 — Perez c/ Disco (N1 Rutinario)', caso1, NORMAS_REF_1, DECISION_REF_1),
    ('CASO 2 — Vizzoti c/ AMSA (N2 Dificil)', caso2, NORMAS_REF_2, DECISION_REF_2),
    ('CASO 3 — Halabi c/ PEN (N3 Constitucional)', caso3, NORMAS_REF_3, DECISION_REF_3),
]

resultados_benchmark = []
for titulo, caso, normas_ref, decision_ref in casos:
    print(f'\n{"="*60}')
    print(f'{titulo}')
    print('='*60)
    print('Generando sentencia...')
    r = generar(caso)

    ev = evaluar(r, normas_ref, decision_ref)
    resultados_benchmark.append({'caso': titulo, 'evaluacion': ev})

    print(f'Nivel asignado:    {ev["nivel"]} | Confianza: {ev["confianza"]*100:.0f}%')
    print(f'Estructura formal: {ev["estructura"]*100:.0f}%')
    print(f'Decision correcta: {"SI" if ev["decision_correcta"] else "NO" if ev["decision_correcta"] is False else "N/A"}')
    if ev['f1_normas'] is not None:
        print(f'F1 normativo:      {ev["f1_normas"]:.2f} (P={ev["precision_normas"]:.2f} R={ev["recall_normas"]:.2f})')
    print(f'Normas generadas:  {", ".join(sorted(ev["normas_generadas"])[:8])}')
    print()
    print('--- CONSIDERANDOS (extracto) ---')
    print(r['considerandos'][:1200])
    print()
    print('--- RESUELVO ---')
    print(r['resuelvo'])

    # Guardar sentencia completa
    fname = OUT_DIR / f'benchmark_{titulo.split("—")[0].strip().replace(" ","_").lower()}.json'
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump({'caso': titulo, 'input': caso, 'output': r, 'evaluacion': ev}, f, ensure_ascii=False, indent=2)

    if titulo != casos[-1][0]:
        print('\nEsperando 10s entre casos...')
        time.sleep(10)

# Resumen final
print('\n' + '='*60)
print('RESUMEN BENCHMARK')
print('='*60)
for rb in resultados_benchmark:
    ev = rb['evaluacion']
    print(f'{rb["caso"][:50]:50s} | Struct={ev["estructura"]*100:.0f}% | Decision={"OK" if ev["decision_correcta"] else "NO" if ev["decision_correcta"] is False else "??"}')

with open(OUT_DIR / 'resumen_benchmark.json', 'w', encoding='utf-8') as f:
    json.dump(resultados_benchmark, f, ensure_ascii=False, indent=2)
print('\nGuardado en tests/resumen_benchmark.json')
