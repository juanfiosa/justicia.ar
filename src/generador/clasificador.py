"""
CLASIFICADOR AUTOMÁTICO DE COMPLEJIDAD
=======================================
Determina automáticamente el nivel de complejidad de un caso judicial (N1-N3)
usando Gemini para analizar los hechos y argumentos de las partes.

Niveles:
  N1 - Rutinario: norma clara, jurisprudencia pacífica, subsunción directa
  N2 - Difícil: problemas interpretativos (indeterminación lingüística,
       lagunas, antinomias, conflictos temporales, analogía, etc.)
  N3 - Constitucional/Derrotable: tensión entre principios, control de
       constitucionalidad/convencionalidad, derrotabilidad
"""

import os
import re
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_DISPONIBLE = True
except ImportError:
    GEMINI_DISPONIBLE = False

PROMPT_CLASIFICACION = """Sos un juez argentino experto en teoría del derecho. Tu tarea es clasificar la complejidad jurídica de un caso judicial en uno de TRES niveles.

NIVELES DE COMPLEJIDAD:

N1 - RUTINARIO (subsunción clásica):
- La norma aplicable es clara e inequívoca
- La jurisprudencia es pacífica y uniforme
- Solo hay que subsumir los hechos en la norma y derivar la consecuencia jurídica
- Ejemplos: cobro de deuda documentada clara, desalojo por vencimiento de plazo, accidente con culpa evidente sin eximentes serias

N2 - DIFÍCIL (problemas interpretativos):
Cualquier caso que presente al menos uno de estos problemas:
- Indeterminación lingüística: vaguedad (zona de penumbra), ambigüedad semántica o sintáctica
- Problemas sistemáticos: laguna (no hay norma directamente aplicable), antinomia (normas contradictorias), redundancia normativa
- Conflicto temporal: dudas sobre retroactividad o derecho transitorio
- Interpretación teleológica incierta: la finalidad de la norma no es clara para el caso
- Analogía vs. a contrario: duda sobre si extender o no la norma a un caso no previsto
- Eximentes, concurrencia de culpa, cuantificación compleja con criterios divergentes
- Jurisprudencia contradictoria o dividida
- Ejemplos: accidente con eximentes serias, contrato con cláusulas ambiguas, despido con justa causa discutida, situación no regulada expresamente

N3 - CONSTITUCIONAL / DERROTABLE (ponderación de principios):
- Hay tensión real entre derechos fundamentales o principios constitucionales
- La aplicación literal de la norma produciría un resultado axiológicamente inaceptable (derrotabilidad)
- Requiere control de constitucionalidad o convencionalidad
- Involucra principios de la CN, tratados de DDHH (CADH, PIDCP), o doctrina CSJN sobre proporcionalidad
- Ejemplos: libertad de expresión vs. privacidad, propiedad vs. función social, igualdad vs. autonomía, casos donde aplicar la ley produce injusticia manifiesta

CRITERIOS DE CLASIFICACIÓN:
- Mirá principalmente los argumentos jurídicos de LAS PARTES, no solo los hechos
- Si las partes discuten la interpretación de una norma o hay eximentes serias → N2
- Si se invoca la CN o tratados de DDHH con seriedad y hay tensión real entre principios → N3
- NO clasificar como N3 solo porque se menciona la CSJN o la Constitución (eso es común en cualquier caso)
- Usá el nivel MÁS BAJO que capture la complejidad real del caso

RESPONDÉ ÚNICAMENTE con un JSON con este formato exacto:
{
  "nivel": 2,
  "justificacion": "Una o dos oraciones explicando por qué este nivel",
  "indicadores": ["indicador 1", "indicador 2", "indicador 3"]
}
"""


def clasificar_caso(caso_dict: dict, api_key: str = None) -> dict:
    """
    Clasifica automáticamente el nivel de complejidad de un caso.

    Args:
        caso_dict: Datos del caso (carátula, hechos, argumentos de partes, etc.)
        api_key: API key de Gemini (opcional, usa env var si no se pasa)

    Returns:
        dict con nivel (1-3), justificacion, indicadores
    """
    gemini_key = api_key or os.environ.get('GEMINI_API_KEY', '')

    if not GEMINI_DISPONIBLE or not gemini_key:
        return _clasificar_heuristico(caso_dict)

    # Construir resumen del caso para clasificar
    resumen = _construir_resumen(caso_dict)

    try:
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=resumen,
            config=genai_types.GenerateContentConfig(
                system_instruction=PROMPT_CLASIFICACION,
                max_output_tokens=500,
                temperature=0.1,
            )
        )
        texto = response.text.strip()
        # Limpiar markdown si lo hay
        if '```json' in texto:
            texto = texto.split('```json')[1].split('```')[0].strip()
        elif '```' in texto:
            texto = texto.split('```')[1].split('```')[0].strip()

        # Extraer JSON si viene mezclado con texto
        json_match = re.search(r'\{[^{}]*"nivel"\s*:\s*\d[^{}]*\}', texto, re.DOTALL)
        if json_match:
            texto = json_match.group(0)

        resultado = json.loads(texto)
        # Asegurar que el nivel está en rango 1-3
        resultado['nivel'] = max(1, min(3, resultado.get('nivel', 1)))
        resultado['metodo'] = 'gemini'
        return resultado
    except Exception as e:
        # Fallback heurístico si falla la API
        resultado = _clasificar_heuristico(caso_dict)
        resultado['error'] = str(e)
        return resultado


def _construir_resumen(caso_dict: dict) -> str:
    """Construye un resumen del caso para enviarlo al clasificador"""
    partes = caso_dict.get('partes', [])
    actor = next((p for p in partes if isinstance(p, dict) and p.get('rol') == 'actor'), {})
    demandado = next((p for p in partes if isinstance(p, dict) and p.get('rol') == 'demandado'), {})

    # También soporta formato simplificado actor/demandado directo
    if not actor:
        actor = caso_dict.get('actor', {})
    if not demandado:
        demandado = caso_dict.get('demandado', {})

    lines = [
        f"CARÁTULA: {caso_dict.get('caratula', '')}",
        f"RAMA: {caso_dict.get('rama', '')}",
        f"TIPO DE PROCESO: {caso_dict.get('tipo_proceso', 'ordinario')}",
        "",
        "HECHOS PROBADOS:",
        caso_dict.get('hechos_probados', ''),
        "",
        "ARGUMENTOS DEL ACTOR:",
        f"  Pretensión: {actor.get('pretension', '')}",
        f"  Fundamentos jurídicos: {actor.get('fundamentos_juridicos', '')}",
        "",
        "ARGUMENTOS DEL DEMANDADO:",
        f"  Fundamentos jurídicos: {demandado.get('fundamentos_juridicos', '')}",
        "",
        "CUESTIONES A RESOLVER:",
        caso_dict.get('cuestiones_juridicas', ''),
    ]
    return '\n'.join(lines)


def _clasificar_heuristico(caso_dict: dict) -> dict:
    """
    Clasificación heurística basada en palabras clave cuando no hay API disponible.
    """
    texto = json.dumps(caso_dict, ensure_ascii=False).lower()

    # Indicadores N3 (constitucional/derrotabilidad) — solo indicadores fuertes
    indicadores_n3 = [
        'inconstitucional', 'convencionalidad', 'derechos humanos', 'tratado internacional',
        'libertad de expresion', 'derecho a la intimidad', 'dignidad humana',
        'discriminacion', 'proporcionalidad', 'ponderacion de principios',
        'derrotabilidad', 'control de constitucionalidad', 'tension entre derechos',
        'cadh', 'pidcp', 'corte idh'
    ]
    # Indicadores N2 (difícil)
    indicadores_n2 = [
        'culpa concurrente', 'eximente', 'caso fortuito', 'hecho de tercero',
        'cuantificacion', 'pericia', 'valuacion', 'discutido', 'impugna',
        'laguna', 'vaguedad', 'contradiccion', 'analogia', 'interpretacion',
        'ambiguedad', 'conflicto de normas', 'retroactividad', 'transitorio',
        'niega responsabilidad', 'subsidiariamente'
    ]

    score_n3 = sum(1 for k in indicadores_n3 if k in texto)
    score_n2 = sum(1 for k in indicadores_n2 if k in texto)

    if score_n3 >= 2:
        return {
            'nivel': 3,
            'justificacion': 'Se detectaron indicadores de tensión constitucional o convencional.',
            'indicadores': [k for k in indicadores_n3 if k in texto][:3],
            'metodo': 'heuristico'
        }
    elif score_n2 >= 1:
        return {
            'nivel': 2,
            'justificacion': 'Se detectaron problemas interpretativos: eximentes, cuantificación discutida o interpretación normativa.',
            'indicadores': [k for k in indicadores_n2 if k in texto][:3],
            'metodo': 'heuristico'
        }
    else:
        return {
            'nivel': 1,
            'justificacion': 'Caso rutinario: norma clara, jurisprudencia pacífica.',
            'indicadores': ['subsuncion directa'],
            'metodo': 'heuristico'
        }
