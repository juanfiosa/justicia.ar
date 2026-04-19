"""
BENCHMARK DIRECTO - 3 CASOS CSJN
Corre el motor de sentencias directamente (sin HTTP server).
"""
import sys, os, json, re, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
os.environ.setdefault('GEMINI_API_KEY', 'AIzaSyDwQp6HcIiqamO0KFeiexL2T560-zvw0_w')

from generador.motor_sentencias import GeneradorSentencias, CasoInput
from generador.clasificador import clasificar_caso

OUT_DIR = os.path.dirname(__file__)

# ============================================================
# UTILIDADES
# ============================================================
def extraer_normas(texto):
    patrones = [
        r'[Aa]rt(?:\u00edculo|iculo)?\.?\s*\d+(?:\s*bis)?',
        r'[Ll]ey\s+\d{4,6}',
        r'[Dd]ecreto\s+\d{3,5}',
        r'L\.?C\.?T\.?',
        r'C\.?C\.?y\.?C\.?N\.?|CCyCN',
        r'PIDESC|Pacto\s+Internacional',
        r'CADH|Convenci\u00f3n\s+Americana',
        r'OIT|Convenio\s+\d+',
        r'Constituci\u00f3n\s+Nacional|C\.N\.',
    ]
    encontradas = set()
    for p in patrones:
        for m in re.finditer(p, texto, re.IGNORECASE):
            encontradas.add(m.group(0).strip().upper()[:30])
    return encontradas

def evaluar(sentencia, normas_ref, decision_ref):
    texto = sentencia.texto_completo or ''
    texto_upper = texto.upper()
    tiene_vistos = 'VISTOS' in texto_upper
    tiene_considerando = 'CONSIDERANDO' in texto_upper
    tiene_resuelvo = 'RESUELVO' in texto_upper
    estructura = (tiene_vistos + tiene_considerando + tiene_resuelvo) / 3

    normas_gen = extraer_normas(texto)
    normas_ref_set = set(n.upper() for n in normas_ref)
    if normas_ref_set and normas_gen:
        matches = sum(1 for n in normas_gen if any(r in n or n in r for r in normas_ref_set))
        precision = matches / len(normas_gen) if normas_gen else 0
        recall = matches / len(normas_ref_set)
        f1 = 2*precision*recall/(precision+recall) if (precision+recall) > 0 else 0
    else:
        precision = recall = f1 = 0.0

    decision_ok = decision_ref.lower() in texto.lower() if decision_ref else None
    extension = min(len(sentencia.considerandos or '') / 2000, 1.0)

    return {
        'estructura': estructura,
        'f1_normas': f1,
        'precision_normas': precision,
        'recall_normas': recall,
        'normas_generadas': sorted(normas_gen),
        'decision_correcta': decision_ok,
        'extension': extension,
    }

# ============================================================
# CASOS
# ============================================================
CASOS = [
    {
        'titulo': 'CASO 1 - Perez c/ Disco (N1 Rutinario)',
        'normas_ref': ['art. 14 bis', 'art. 103', 'LCT', 'PIDESC', 'OIT', 'Ley 20744'],
        'decision_ref': 'remuneratori',
        'data': {
            'caratula': 'Perez, Anibal Nestor c/ Disco S.A. s/ accion declarativa',
            'expediente': 'P.489.XLIV',
            'rama': 'laboral',
            'tipo_proceso': 'ordinario',
            'tribunal': 'Corte Suprema de Justicia de la Nacion',
            'hechos_probados': (
                'El actor percibia sumas dinerarias denominadas no remunerativas en virtud de acuerdos '
                'colectivos homologados por el Ministerio de Trabajo. Esas sumas fueron pactadas como '
                'asignaciones no remunerativas de caracter alimentario para eludir el pago de contribuciones '
                'patronales y su incidencia en la indemnizacion por despido. No estaban sujetas a descuento '
                'jubilatorio ni se incluian en el recibo como remuneracion.'
            ),
            'partes': [
                {
                    'nombre': 'Perez, Anibal Nestor',
                    'rol': 'actor',
                    'pretension': 'Que las sumas percibidas sean reconocidas como remuneracion y se recalculen contribuciones, aportes e indemnizaciones',
                    'fundamentos_juridicos': 'Art. 14 bis CN. Art. 103 LCT (todo lo que percibe el trabajador por su trabajo es remuneracion). PIDESC art. 7. Convenio 95 OIT.',
                    'jurisprudencia_citada': 'Nordensthol c/ Subte CSJN 1985',
                },
                {
                    'nombre': 'Disco S.A.',
                    'rol': 'demandado',
                    'pretension': 'Rechazo de la demanda',
                    'fundamentos_juridicos': 'Las sumas fueron pactadas en acuerdos colectivos homologados por autoridad estatal competente.',
                    'jurisprudencia_citada': 'Doctrina de la autonomia colectiva',
                },
            ],
            'cuestiones_a_resolver': [
                'Pueden los acuerdos colectivos homologados calificar como no remunerativa una suma pagada en razon del trabajo?',
                'Es constitucional esa calificacion frente al art. 14 bis CN y el PIDESC?',
            ],
        },
    },
    {
        'titulo': 'CASO 2 - Vizzoti c/ AMSA (N2 Dificil)',
        'normas_ref': ['art. 245', 'LCT', 'art. 14 bis', 'art. 28', 'art. 17', 'PIDESC', 'Ley 20744'],
        'decision_ref': 'inconstitucional',
        'data': {
            'caratula': 'Vizzoti, Carlos Alberto c/ AMSA S.A. s/ despido',
            'expediente': 'V.967.XXXVIII',
            'rama': 'laboral',
            'tipo_proceso': 'ordinario',
            'tribunal': 'Corte Suprema de Justicia de la Nacion',
            'hechos_probados': (
                'Vizzoti fue despedido sin causa por AMSA S.A. tras 26 anios de antiguedad. '
                'Su mejor remuneracion mensual normal y habitual era de $11.465. '
                'El promedio de las remuneraciones del convenio colectivo aplicable era de $1.000. '
                'Aplicando el tope del art. 245 LCT la base no podia superar $670, '
                'resultando la indemnizacion un 83% inferior a la que corresponderia sobre la remuneracion real.'
            ),
            'partes': [
                {
                    'nombre': 'Vizzoti, Carlos Alberto',
                    'rol': 'actor',
                    'pretension': 'Indemnizacion calculada sobre su remuneracion real de $11.465 sin aplicacion del tope del art. 245 LCT, o que el tope sea declarado inconstitucional cuando reduzca la base en mas del 33%',
                    'fundamentos_juridicos': 'Art. 14 bis CN (proteccion contra el despido arbitrario). Art. 17 CN (no confiscatoriedad). Art. 28 CN (razonabilidad). Arts. 7 y 8 PIDESC.',
                    'jurisprudencia_citada': 'Bercaitz CSJN Fallos 289:430; doctrina de razonabilidad',
                },
                {
                    'nombre': 'AMSA S.A.',
                    'rol': 'demandado',
                    'pretension': 'Rechazo. El tope del art. 245 LCT es valido',
                    'fundamentos_juridicos': 'El art. 245 LCT es norma valida sancionada por el Congreso. El tope busca equiparar indemnizaciones entre trabajadores.',
                    'jurisprudencia_citada': 'Fernandez Arias Fallos 247:646',
                },
            ],
            'cuestiones_a_resolver': [
                'Es constitucional el tope del art. 245 LCT cuando reduce la base indemnizatoria en mas del 33% respecto de la remuneracion real?',
                'Cual es el umbral de razonabilidad por debajo del cual la reglamentacion deviene inconstitucional?',
            ],
        },
    },
    {
        'titulo': 'CASO 3 - Halabi c/ PEN (N3 Constitucional)',
        'normas_ref': ['art. 18', 'art. 19', 'art. 43', 'Ley 25.873', 'CADH', 'PIDESC'],
        'decision_ref': 'inconstitucional',
        'data': {
            'caratula': 'Halabi, Ernesto c/ P.E.N. - Ley 25.873 - Dec. 1563/04 s/ amparo ley 16.986',
            'expediente': 'H.270.XLII',
            'rama': 'constitucional',
            'tipo_proceso': 'amparo',
            'tribunal': 'Corte Suprema de Justicia de la Nacion',
            'hay_cuestion_constitucional': True,
            'hechos_probados': (
                'La Ley 25.873 y el Decreto 1563/04 obligaron a las empresas de telecomunicaciones '
                'a capturar y almacenar por 10 anios el contenido de todas las comunicaciones '
                'telefonicas e informaticas de los usuarios, poniendolas a disposicion del PEN '
                'sin requerir orden judicial. Halabi, abogado, interpuso amparo invocando que '
                'la ley vulneraba sus comunicaciones profesionales con clientes.'
            ),
            'partes': [
                {
                    'nombre': 'Halabi, Ernesto',
                    'rol': 'actor',
                    'pretension': 'Inconstitucionalidad de la Ley 25.873 y Dec. 1563/04. Que se ordene al Estado abstenerse de interceptar comunicaciones con efectos erga omnes.',
                    'fundamentos_juridicos': 'Art. 18 CN (inviolabilidad correspondencia). Art. 19 CN (autonomia personal). Art. 43 CN (amparo). CADH art. 11 (vida privada).',
                    'jurisprudencia_citada': 'Urteaga CSJN Fallos 321:2767; Escher c/ Brasil Corte IDH',
                },
                {
                    'nombre': 'Poder Ejecutivo Nacional',
                    'rol': 'demandado',
                    'pretension': 'Rechazo del amparo. La ley persigue fines legitimos de seguridad publica.',
                    'fundamentos_juridicos': 'La ley persigue fines legitimos de seguridad y persecucion del delito.',
                    'jurisprudencia_citada': 'Doctrina de seguridad nacional',
                },
            ],
            'cuestiones_a_resolver': [
                'La Ley 25.873 vulnera el derecho a la privacidad (arts. 18 y 19 CN) al permitir interceptacion masiva sin orden judicial?',
                'Existe en el ordenamiento argentino la accion de clase para derechos de incidencia colectiva?',
                'Puede el amparo tener efectos erga omnes cuando hay un grupo de afectados en situacion analoga?',
            ],
        },
    },
]

# ============================================================
# EJECUTAR
# ============================================================
gen = GeneradorSentencias()
print(f'Modelo activo: {gen.gemini_model}')
print(f'Gemini disponible: {gen.gemini_client is not None}')
print()

campos_validos = set(CasoInput.__dataclass_fields__.keys())
resultados_benchmark = []

for i, caso_item in enumerate(CASOS):
    titulo = caso_item['titulo']
    data = caso_item['data'].copy()
    normas_ref = caso_item['normas_ref']
    decision_ref = caso_item['decision_ref']

    print('=' * 62)
    print(titulo)
    print('=' * 62)

    # Clasificar
    cl = clasificar_caso(data)
    nivel = cl['nivel']
    confianza = cl.get('confianza', 0.8)
    data['nivel_complejidad'] = nivel
    print(f'Nivel asignado: {nivel} | Confianza: {confianza*100:.0f}%')
    print('Generando sentencia...')

    # Generar
    caso_filtrado = {k: v for k, v in data.items() if k in campos_validos}
    caso_obj = CasoInput(**caso_filtrado)
    sentencia = gen.generar_sentencia(caso_obj)

    # Evaluar
    ev = evaluar(sentencia, normas_ref, decision_ref)

    print(f'Estructura formal: {ev["estructura"]*100:.0f}%')
    print(f'Decision correcta: {"SI" if ev["decision_correcta"] else "NO" if ev["decision_correcta"] is False else "N/A"}')
    print(f'F1 normativo:      {ev["f1_normas"]:.2f} (P={ev["precision_normas"]:.2f} R={ev["recall_normas"]:.2f})')
    print(f'Normas detectadas: {", ".join(ev["normas_generadas"][:8])}')
    print()
    print('--- CONSIDERANDOS (600 chars) ---')
    considerandos_texto = sentencia.considerandos or ''
    if not considerandos_texto and sentencia.texto_completo:
        # Extraer del texto completo
        tc = sentencia.texto_completo
        idx_c = tc.upper().find('CONSIDERANDO')
        idx_r = tc.upper().find('RESUELVO')
        if idx_c >= 0:
            considerandos_texto = tc[idx_c:idx_r].strip() if idx_r > idx_c else tc[idx_c:].strip()
    print(considerandos_texto[:600] if considerandos_texto else '[VACIO - ver texto_completo]')
    print()
    print('--- RESUELVO ---')
    resuelvo_texto = sentencia.resuelvo or ''
    if not resuelvo_texto and sentencia.texto_completo:
        tc = sentencia.texto_completo
        idx_r = tc.upper().find('RESUELVO')
        if idx_r >= 0:
            resuelvo_texto = tc[idx_r:].strip()
    print(resuelvo_texto[:400] if resuelvo_texto else '[VACIO - ver texto_completo]')
    print()

    rb = {
        'caso': titulo,
        'input': data,
        'output': {
            'texto_completo': sentencia.texto_completo,
            'considerandos': sentencia.considerandos,
            'resuelvo': sentencia.resuelvo,
            'nivel_complejidad': sentencia.nivel_complejidad,
            'confianza': sentencia.confianza,
        },
        'evaluacion': ev,
    }
    resultados_benchmark.append(rb)

    # Guardar caso individual
    fname = os.path.join(OUT_DIR, f'benchmark_caso{i+1}.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(rb, f, ensure_ascii=False, indent=2)

    if i < len(CASOS) - 1:
        print('Pausa 5s...')
        time.sleep(5)

# ============================================================
# RESUMEN
# ============================================================
print()
print('=' * 62)
print('RESUMEN BENCHMARK - 3 CASOS CSJN')
print('=' * 62)
for rb in resultados_benchmark:
    ev = rb['evaluacion']
    estado_dec = 'OK' if ev['decision_correcta'] else 'NO' if ev['decision_correcta'] is False else '??'
    print(f'{rb["caso"][:50]:50s} | Struct={ev["estructura"]*100:.0f}% | F1={ev["f1_normas"]:.2f} | Dec={estado_dec}')

# Promedios
structs = [rb['evaluacion']['estructura'] for rb in resultados_benchmark]
f1s = [rb['evaluacion']['f1_normas'] for rb in resultados_benchmark]
decs = [rb['evaluacion']['decision_correcta'] for rb in resultados_benchmark if rb['evaluacion']['decision_correcta'] is not None]
print(f'\nPROMEDIOS: Estructura={sum(structs)/len(structs)*100:.0f}% | F1={sum(f1s)/len(f1s):.2f} | Decision={sum(1 for d in decs if d)}/{len(decs)} correctas')

with open(os.path.join(OUT_DIR, 'resumen_benchmark.json'), 'w', encoding='utf-8') as f:
    json.dump(resultados_benchmark, f, ensure_ascii=False, indent=2)
print('\nGuardado en tests/resumen_benchmark.json')
