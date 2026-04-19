"""
MÓDULO 2: GENERADOR DE SENTENCIAS
===================================
Motor de generación de sentencias judiciales usando Claude API.

Genera sentencias en formato:
    VISTOS: [encabezamiento procesal]
    CONSIDERANDO: [fundamentación jurídica numerada]
    RESUELVO: [parte dispositiva]

La estrategia de generación varía según el nivel de complejidad:
    Nivel 1-2: Subsunción clásica (norma + hechos → conclusión)
    Nivel 3: Interpretación + integración (vaguedad, lagunas, contradicciones)
    Nivel 4: Ponderación de principios constitucionales (derrotabilidad)
"""

import os
import sys
import json
import logging
import concurrent.futures
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum
from typing import Optional, Callable

# Timeout en segundos para cada llamada individual a un LLM
LLM_TIMEOUT = 120

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from generador.prompts import construir_system_prompt, construir_user_prompt
    PROMPTS_MEJORADOS = True
except ImportError:
    PROMPTS_MEJORADOS = False

try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_DISPONIBLE = True
except ImportError:
    genai = None
    genai_types = None
    GEMINI_DISPONIBLE = False

try:
    import anthropic
    ANTHROPIC_DISPONIBLE = True
except ImportError:
    anthropic = None
    ANTHROPIC_DISPONIBLE = False

if not GEMINI_DISPONIBLE and not ANTHROPIC_DISPONIBLE:
    print("ADVERTENCIA: Ni google-generativeai ni anthropic instalados. Modo demo activado.")


# ================================================================
# MODELOS DE DATOS
# ================================================================

class NivelComplejidad(Enum):
    RUTINARIO = 1
    DIFICIL = 2
    CONSTITUCIONAL = 3


@dataclass
class PosicionProcesal:
    """Posición jurídica de una parte procesal"""
    rol: str                        # "actor", "demandado", "querellante", "defensa"
    nombre: str
    letrado: str = ""
    pretension: str = ""
    fundamentos_juridicos: str = ""  # Normas invocadas
    argumentos: str = ""             # Desarrollo argumentativo
    jurisprudencia_citada: str = ""  # Precedentes invocados


@dataclass
class CasoInput:
    """Entrada del juez para generar una sentencia"""
    # Identificación
    caratula: str
    expediente: str = ""
    rama: str = "civil_comercial"
    subrama: str = ""
    tipo_proceso: str = "ordinario"
    tribunal: str = ""
    jurisdiccion: str = "Nacional"
    instancia: str = "primera"

    # Hechos (quaestio facti - fijados por el juez)
    hechos_probados: str = ""
    prueba_valorada: str = ""   # campo legacy
    valoracion_prueba: str = "" # lectura del juez sobre hechos controvertidos (solo primera instancia)

    # Partes
    partes: list = field(default_factory=list)

    # Cuestiones
    cuestiones_a_resolver: list = field(default_factory=list)
    hay_cuestion_constitucional: bool = False
    descripcion_cuestion_constitucional: str = ""

    # Clasificación
    nivel_complejidad: int = 1

    # Tipo de órgano (para diseño institucional específico)
    tipo_organo: str = ""

    # Segunda instancia / alzada
    sentencia_primera_instancia: str = ""
    agravios: str = ""

    # Casación / TSJ / CSJN
    tipo_recurso_casacion: str = ""
    causal_casacion: str = ""
    sentencia_recurrida: str = ""
    recurso_casacion_texto: str = ""
    contestacion_recurso: str = ""

    # CSJN — Recurso Extraordinario Federal
    tipo_cuestion_federal: str = ""
    cuestion_federal: str = ""
    es_queja: bool = False
    introduccion_oportuna: str = ""

    # Campos penales
    imputado: str = ""
    delito_imputado: str = ""
    pena_solicitada: str = ""
    atenuantes: str = ""
    agravantes: str = ""
    prision_preventiva: str = ""

    def to_dict(self):
        d = asdict(self)
        return d


@dataclass
class PrecedenteRecuperado:
    """Un precedente encontrado por el retrieval"""
    caratula: str
    tribunal: str
    fecha: str
    texto: str
    relevancia: float


@dataclass
class SentenciaGenerada:
    """Salida del generador"""
    vistos: str
    considerandos: str
    resuelvo: str
    texto_completo: str
    nivel_complejidad: int
    confianza: float
    advertencias: list = field(default_factory=list)
    notas_para_juez: str = ""
    precedentes_usados: list = field(default_factory=list)
    normas_citadas: list = field(default_factory=list)


# ================================================================
# PROMPTS POR NIVEL DE COMPLEJIDAD
# ================================================================

SYSTEM_PROMPT_BASE = """Eres un asistente judicial experto en derecho argentino. Tu función es generar
proyectos de sentencia judicial siguiendo estrictamente el formato y estilo de la
justicia argentina.

REGLAS FUNDAMENTALES:
1. Generás UNA sentencia que DECIDE el caso. No ofrecés opciones ni alternativas.
2. El formato es siempre: VISTOS... Y CONSIDERANDO... RESUELVO...
3. Cada norma que cites debe existir realmente en el derecho argentino vigente.
4. Cada precedente que cites debe ser real y verificable.
5. La sentencia debe ser CONGRUENTE: debe pronunciarse sobre todas las cuestiones
   planteadas por las partes, ni más ni menos.
6. Los hechos probados son los que fijó el juez. No los modificás ni cuestionás.
7. Tu trabajo es la QUAESTIO IURIS: aplicar el derecho a los hechos dados.

ESTILO:
- Lenguaje jurídico formal argentino
- Párrafos argumentativos desarrollados
- Citas normativas con número de ley y artículo
- Citas jurisprudenciales con tribunal, carátula y fecha
- Numeración romana para los considerandos
"""

PROMPT_NIVEL_1 = """ESTRATEGIA: SUBSUNCIÓN CLÁSICA (caso rutinario)

La norma aplicable es clara y la jurisprudencia es pacífica.
Aplicá el método subsuntivo clásico:

1. PREMISA MAYOR: Identificá la(s) norma(s) aplicable(s)
2. PREMISA MENOR: Subsumí los hechos probados en el supuesto normativo
3. CONCLUSIÓN: Derivá la consecuencia jurídica

Estructura de los CONSIDERANDO:
I. Antecedentes y cuestión a resolver
II. Marco normativo aplicable
III. Subsunción: aplicación de la norma a los hechos
IV. Cuantificación (si hay monto)
V. Costas
"""

PROMPT_NIVEL_2 = """ESTRATEGIA: CASO DIFÍCIL (problemas interpretativos)

Este caso presenta al menos uno de estos problemas:
- Indeterminación lingüística: vaguedad, ambigüedad semántica o sintáctica
- Problemas sistemáticos: laguna, antinomia, redundancia normativa
- Conflicto temporal, interpretación teleológica incierta, analogía vs. a contrario
- Eximentes, concurrencia de culpa, cuantificación con criterios divergentes

Tu enfoque:
1. IDENTIFICAR expresamente cuál es el problema interpretativo
2. EXPONER las interpretaciones posibles (al menos dos)
3. FUNDAMENTAR cuál se adopta y por qué (jurisprudencia, doctrina, principios)
4. APLICAR la interpretación elegida a los hechos concretos

Estructura de los CONSIDERANDO:
I. Antecedentes y cuestión a resolver
II. El problema interpretativo identificado
III. Las interpretaciones posibles
IV. Fundamentación de la interpretación adoptada
V. Aplicación al caso concreto
VI. Cuantificación (si hay monto)
VII. Costas
"""

PROMPT_NIVEL_3 = """ESTRATEGIA: PONDERACIÓN DE PRINCIPIOS (caso constitucional/de derrotabilidad)

Este es un caso de complejidad 4. Involucra una tensión entre principios
constitucionales o una situación de derrotabilidad donde la aplicación literal
de la norma produciría un resultado axiológicamente inaceptable.

Cuestión constitucional planteada: {cuestion_constitucional}

Tu enfoque (siguiendo la doctrina de la CSJN y la Corte IDH):
1. IDENTIFICAR los principios/derechos en tensión (P1 vs P2)
2. ANALIZAR el contenido esencial de cada derecho en juego
3. APLICAR el test de proporcionalidad (Alexy):
   a. IDONEIDAD: ¿La restricción de P2 es idónea para proteger P1?
   b. NECESIDAD: ¿Hay medida alternativa menos restrictiva?
   c. PROPORCIONALIDAD EN SENTIDO ESTRICTO: ¿El grado de satisfacción de P1
      justifica el grado de afectación de P2 en este caso concreto?
4. FUNDAMENTAR la prevalencia de un principio sin anular al otro
5. CITAR doctrina constitucional relevante (CSJN, Corte IDH)

Estructura de los CONSIDERANDO:
I. Antecedentes y cuestión a resolver
II. Los derechos/principios en tensión
III. Marco constitucional y convencional aplicable
IV. Test de proporcionalidad
V. Resolución del conflicto en el caso concreto
VI. Doctrina constitucional aplicable
VII. Aplicación a los hechos del caso
VIII. Costas
"""


# ================================================================
# GENERADOR
# ================================================================

class GeneradorSentencias:
    """Motor principal de generación de sentencias judiciales"""

    def __init__(self, api_key: str = None):
        """
        Inicializa el generador. Prioridad de backend:
          1. Gemini (GEMINI_API_KEY)
          2. Anthropic Claude (ANTHROPIC_API_KEY)
          3. Modo demo (sin IA)
        """
        self.gemini_key = os.environ.get('GEMINI_API_KEY', '')
        self.anthropic_key = api_key or os.environ.get('ANTHROPIC_API_KEY', '')
        self.client = None          # cliente Anthropic
        self.gemini_client = None   # cliente Gemini
        self.gemini_model = None    # nombre del modelo Gemini

        self.groq_key = os.environ.get('GROQ_API_KEY', '')

        if GEMINI_DISPONIBLE and self.gemini_key:
            self.gemini_client = genai.Client(api_key=self.gemini_key)
            # Cadena de modelos por cuota disponible en tier gratuito:
            # 1. gemini-2.0-flash-lite: 1500 RPD  <-- principal, la cuota más alta
            # 2. gemini-2.0-flash:       ~1500 RPD <-- fallback secundario
            # 3. gemini-2.5-flash-lite:   20 RPD   <-- solo si los anteriores están agotados
            # 4. gemini-2.5-flash:         20 RPD   <-- último recurso
            # Si todos fallan (ej. restricción regional en Render Oregon), se usa Groq.
            self.gemini_models_fallback = [
                'gemini-2.0-flash-lite',
                'gemini-2.0-flash',
                'gemini-2.5-flash-lite',
                'gemini-2.5-flash',
            ]
            self.gemini_model = self.gemini_models_fallback[0]
        elif ANTHROPIC_DISPONIBLE and self.anthropic_key:
            self.client = anthropic.Anthropic(api_key=self.anthropic_key)

    def generar_sentencia(self, caso: CasoInput,
                          precedentes: list[PrecedenteRecuperado] = None,
                          normas_contexto: list[str] = None) -> SentenciaGenerada:
        """
        Genera un proyecto de sentencia para el caso dado.

        Args:
            caso: Los datos del caso cargados por el juez
            precedentes: Precedentes recuperados por el módulo de retrieval
            normas_contexto: Textos de normas relevantes recuperados

        Returns:
            SentenciaGenerada con el proyecto de sentencia completo
        """
        # Construir el prompt
        system = SYSTEM_PROMPT_BASE
        user_prompt = self._construir_prompt(caso, precedentes, normas_contexto)

        # Generar con Claude o simular
        # System prompt mejorado o fallback
        if PROMPTS_MEJORADOS:
            from generador.prompts import (SYSTEM_TSJ, SYSTEM_CSJN, SYSTEM_SEGUNDA,
                                           SYSTEM_JUZGADO_CONTROL, SYSTEM_CAMARA_ACUSACION)
            tipo_organo = getattr(caso, 'tipo_organo', '')
            instancia = getattr(caso, 'instancia', '')
            if tipo_organo == 'juzgado_control':
                system = SYSTEM_JUZGADO_CONTROL
            elif tipo_organo == 'camara_acusacion':
                system = SYSTEM_CAMARA_ACUSACION
            elif instancia == 'extraordinaria':
                system = SYSTEM_CSJN
            elif instancia == 'casacion':
                system = SYSTEM_TSJ
            elif instancia == 'segunda':
                system = SYSTEM_SEGUNDA
            else:
                system = construir_system_prompt(caso.rama, caso.nivel_complejidad)
        if self.gemini_client and self.gemini_model:
            # Gemini primero; si falla regionalmente, _llamar_gemini hace fallback a Groq
            texto_sentencia = self._llamar_gemini(system, user_prompt)
        elif self.client:
            texto_sentencia = self._llamar_claude(system, user_prompt)
        elif self.groq_key:
            # Groq directo si no hay Gemini ni Claude configurados
            texto_sentencia = self._llamar_groq(system, user_prompt)
        else:
            texto_sentencia = self._generar_simulacion(caso)

        # Detectar errores LLM antes de parsear — evita sentencias vacías silenciosas
        if texto_sentencia and texto_sentencia.strip().startswith("ERROR"):
            logging.error(f"[LLM] El proveedor devolvió un error: {texto_sentencia[:200]}")
            # Devolver directamente un SentenciaGenerada con el mensaje de error visible
            return SentenciaGenerada(
                vistos="",
                considerandos="",
                resuelvo="",
                texto_completo=texto_sentencia,
                nivel_complejidad=caso.nivel_complejidad,
                confianza=0.0,
                advertencias=[
                    "⚠️ ERROR DEL PROVEEDOR IA: la sentencia no pudo generarse. "
                    "Revise los logs del servidor y vuelva a intentarlo en unos minutos."
                ],
                notas_para_juez=texto_sentencia,
            )

        # Parsear la sentencia
        sentencia = self._parsear_sentencia(texto_sentencia, caso)

        return sentencia

    def _construir_prompt(self, caso: CasoInput,
                          precedentes: list = None,
                          normas: list = None) -> str:
        """Construye el prompt completo para el LLM"""
        # Usar prompts mejorados si están disponibles
        if PROMPTS_MEJORADOS:
            caso_dict = caso.to_dict() if hasattr(caso, 'to_dict') else asdict(caso)
            return construir_user_prompt(caso_dict, precedentes, normas)

        # Fallback a prompts originales
        nivel = caso.nivel_complejidad
        if nivel == 1:
            estrategia = PROMPT_NIVEL_1
        elif nivel == 2:
            estrategia = PROMPT_NIVEL_2
        else:
            estrategia = PROMPT_NIVEL_3.format(
                cuestion_constitucional=caso.descripcion_cuestion_constitucional or "No especificada"
            )

        # Armar la sección de partes
        partes_texto = ""
        for p in caso.partes:
            if isinstance(p, dict):
                partes_texto += f"\n--- {p.get('rol', 'PARTE').upper()} ---\n"
                partes_texto += f"Nombre: {p.get('nombre', 'N/A')}\n"
                partes_texto += f"Letrado: {p.get('letrado', 'N/A')}\n"
                partes_texto += f"Pretensión: {p.get('pretension', 'N/A')}\n"
                partes_texto += f"Fundamentos jurídicos: {p.get('fundamentos_juridicos', 'N/A')}\n"
                partes_texto += f"Argumentos: {p.get('argumentos', 'N/A')}\n"
                partes_texto += f"Jurisprudencia citada: {p.get('jurisprudencia_citada', 'N/A')}\n"
            elif isinstance(p, PosicionProcesal):
                partes_texto += f"\n--- {p.rol.upper()} ---\n"
                partes_texto += f"Nombre: {p.nombre}\n"
                partes_texto += f"Letrado: {p.letrado}\n"
                partes_texto += f"Pretensión: {p.pretension}\n"
                partes_texto += f"Fundamentos jurídicos: {p.fundamentos_juridicos}\n"
                partes_texto += f"Argumentos: {p.argumentos}\n"
                partes_texto += f"Jurisprudencia citada: {p.jurisprudencia_citada}\n"

        # Sección de precedentes recuperados
        precedentes_texto = ""
        if precedentes:
            precedentes_texto = "\n\n=== PRECEDENTES RELEVANTES RECUPERADOS ===\n"
            for i, p in enumerate(precedentes, 1):
                if isinstance(p, dict):
                    precedentes_texto += f"\n[{i}] {p.get('caratula', 'N/A')} - {p.get('tribunal', 'N/A')} ({p.get('fecha', 'N/A')})\n"
                    precedentes_texto += f"    {p.get('texto', '')[:500]}\n"
                elif isinstance(p, PrecedenteRecuperado):
                    precedentes_texto += f"\n[{i}] {p.caratula} - {p.tribunal} ({p.fecha})\n"
                    precedentes_texto += f"    {p.texto[:500]}\n"

        # Sección de normas
        normas_texto = ""
        if normas:
            normas_texto = "\n\n=== NORMAS APLICABLES RECUPERADAS ===\n"
            for n in normas:
                normas_texto += f"\n{n}\n"

        # Prompt final
        prompt = f"""
{estrategia}

=== DATOS DEL CASO ===

CARÁTULA: {caso.caratula}
EXPEDIENTE: {caso.expediente}
TRIBUNAL: {caso.tribunal}
TIPO DE PROCESO: {caso.tipo_proceso}
RAMA: {caso.rama} / {caso.subrama}
INSTANCIA: {caso.instancia}

=== HECHOS PROBADOS (fijados por el juez) ===
{caso.hechos_probados}

=== PRUEBA VALORADA ===
{caso.prueba_valorada}

=== POSICIONES DE LAS PARTES ===
{partes_texto}

=== CUESTIONES A RESOLVER ===
{chr(10).join(f'- {c}' for c in caso.cuestiones_a_resolver) if caso.cuestiones_a_resolver else 'Las que surjan del planteo de las partes'}

{"=== CUESTIÓN CONSTITUCIONAL ===" + chr(10) + caso.descripcion_cuestion_constitucional if caso.hay_cuestion_constitucional else ""}

{precedentes_texto}
{normas_texto}

=== INSTRUCCIONES FINALES ===
Generá el proyecto de sentencia completo con el formato:

VISTOS:
[Encabezamiento con carátula, tipo de proceso, radicación, trámite procesal resumido]

Y CONSIDERANDO:
[Considerandos numerados con números romanos, desarrollados, con citas normativas y jurisprudenciales]

RESUELVO:
[Parte dispositiva numerada con los puntos de la decisión]

La sentencia debe DECIDIR el caso, no plantear alternativas.
"""
        return prompt

    # ------------------------------------------------------------------
    # Utilidad de timeout
    # ------------------------------------------------------------------

    def _ejecutar_con_timeout(self, fn: Callable, timeout: int = LLM_TIMEOUT):
        """Ejecuta fn() en un thread independiente con un timeout máximo.
        Lanza concurrent.futures.TimeoutError si se supera el límite."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fn)
            return future.result(timeout=timeout)

    def _llamar_gemini(self, system: str, user_prompt: str) -> str:
        """Llama a la API de Gemini para generar la sentencia.
        Si el modelo activo tiene la cuota agotada (429) o está restringido
        regionalmente (FAILED_PRECONDITION desde Render Oregon), prueba
        automáticamente el siguiente modelo; si todos fallan, usa Groq."""
        modelos = getattr(self, 'gemini_models_fallback', [self.gemini_model])
        ultimo_error = None
        for modelo in modelos:
            try:
                response = self._ejecutar_con_timeout(
                    lambda m=modelo: self.gemini_client.models.generate_content(
                        model=m,
                        contents=user_prompt,
                        config=genai_types.GenerateContentConfig(
                            system_instruction=system,
                            max_output_tokens=65536,
                            temperature=0.3,
                        )
                    )
                )
                # Si funcionó, actualizar el modelo activo para las próximas llamadas
                if modelo != self.gemini_model:
                    logging.warning(f"Gemini fallback: usando {modelo} (modelo anterior agotado)")
                    self.gemini_model = modelo
                return response.text
            except concurrent.futures.TimeoutError:
                ultimo_error = TimeoutError(f"Gemini ({modelo}) no respondió en {LLM_TIMEOUT}s")
                logging.warning(str(ultimo_error))
                continue  # probar siguiente modelo Gemini
            except Exception as e:
                ultimo_error = e
                # Hacer fallback si es cuota agotada, modelo no disponible, o restricción regional
                err_str = str(e)
                if ('429' in err_str or 'RESOURCE_EXHAUSTED' in err_str
                        or 'NOT_FOUND' in err_str or 'FAILED_PRECONDITION' in err_str
                        or 'location is not supported' in err_str.lower()):
                    continue  # probar siguiente modelo Gemini
                else:
                    # Error distinto (red, autenticación, etc.) — no tiene sentido reintentar
                    break

        # Todos los modelos Gemini fallaron → intentar con Groq
        logging.warning(f"Todos los modelos Gemini fallaron ({ultimo_error}). Intentando con Groq.")
        return self._llamar_groq(system, user_prompt)

    def _llamar_groq(self, system: str, user_prompt: str) -> str:
        """Fallback a Groq (LLaMA 3.3 70B) cuando Gemini no está disponible.
        Groq es un proveedor sin restricciones geográficas y con tier gratuito generoso."""
        groq_key = os.environ.get('GROQ_API_KEY', '')
        if not groq_key:
            return (
                "ERROR: Todos los modelos Gemini fallaron por restricción regional "
                "y GROQ_API_KEY no está configurada.\n\n"
                "[Para habilitar el fallback, configure GROQ_API_KEY en Render "
                "con una clave gratuita de console.groq.com]"
            )
        try:
            from groq import Groq
            client = Groq(api_key=groq_key, timeout=LLM_TIMEOUT)
            completion = self._ejecutar_con_timeout(
                lambda: client.chat.completions.create(
                    model='llama-3.3-70b-versatile',
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user",   "content": user_prompt},
                    ],
                    max_tokens=8000,
                    temperature=0.3,
                )
            )
            texto = completion.choices[0].message.content
            logging.info("Groq (LLaMA 3.3 70B) respondió correctamente como fallback.")
            return texto
        except concurrent.futures.TimeoutError:
            msg = f"ERROR: Groq no respondió en {LLM_TIMEOUT}s\n\n[Timeout — ningún proveedor IA disponible]"
            logging.error(msg)
            return msg
        except Exception as e:
            return f"ERROR en Groq fallback: {e}\n\n[Ningún proveedor IA disponible]"

    def _llamar_claude(self, system: str, user_prompt: str) -> str:
        """Llama a la API de Claude para generar la sentencia"""
        try:
            message = self._ejecutar_con_timeout(
                lambda: self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=8000,
                    system=system,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
            )
            return message.content[0].text
        except concurrent.futures.TimeoutError:
            msg = f"ERROR: Claude no respondió en {LLM_TIMEOUT}s\n\n[Se generará una sentencia de demostración]"
            logging.error(msg)
            return msg
        except Exception as e:
            return f"ERROR al llamar a Claude API: {e}\n\n[Se generará una sentencia de demostración]"

    def _generar_simulacion(self, caso: CasoInput) -> str:
        """
        Genera una sentencia de demostración cuando no hay API key.
        Útil para testing de la interfaz.
        """
        actor = "el actor"
        demandado = "el demandado"
        for p in caso.partes:
            if isinstance(p, dict):
                if p.get('rol') == 'actor':
                    actor = p.get('nombre', 'el actor')
                elif p.get('rol') == 'demandado':
                    demandado = p.get('nombre', 'el demandado')

        return f"""VISTOS:
Estos autos caratulados "{caso.caratula}" (Expte. {caso.expediente}), en trámite por ante este {caso.tribunal}, de los que

Y CONSIDERANDO:

I. Que llegan estos autos a conocimiento de este Tribunal a fin de resolver las cuestiones planteadas por las partes en el presente proceso {caso.tipo_proceso}.

II. Que {actor} promovió la presente acción contra {demandado}. De la relación de hechos que el suscripto tiene por probados surge que: {caso.hechos_probados[:500]}

III. Que en cuanto al marco normativo aplicable, corresponde señalar que la cuestión se rige por las disposiciones del derecho {caso.rama} argentino vigente.

IV. Que analizadas las constancias de autos, valorada la prueba producida conforme las reglas de la sana crítica ({caso.prueba_valorada[:300]}), y ponderados los argumentos de ambas partes, este Tribunal entiende que corresponde hacer lugar a la demanda.

V. Que las costas se imponen a la parte vencida en virtud del principio objetivo de la derrota (art. 68 CPCCN).

[NOTA: Esta es una sentencia de DEMOSTRACIÓN generada sin IA.
Para generar sentencias reales, configure la variable GEMINI_API_KEY.]

RESUELVO:

1) Hacer lugar a la demanda interpuesta por {actor} contra {demandado}.

2) Imponer las costas a la parte demandada vencida (art. 68 CPCCN).

3) Regular los honorarios de los profesionales intervinientes de conformidad con lo dispuesto por la Ley 27.423.

4) Notifíquese. Regístrese. Cúmplase."""

    def _parsear_sentencia(self, texto: str, caso: CasoInput) -> SentenciaGenerada:
        """Parsea el texto generado en las secciones de la sentencia"""
        vistos = ""
        considerandos = ""
        resuelvo = ""

        texto_upper = texto.upper()

        # Buscar secciones
        idx_vistos = texto_upper.find("VISTOS")
        idx_considerando = texto_upper.find("CONSIDERANDO")
        if idx_considerando == -1:
            idx_considerando = texto_upper.find("Y CONSIDERANDO")
        idx_resuelvo = texto_upper.find("RESUELVO")

        if idx_vistos >= 0 and idx_considerando > idx_vistos:
            vistos = texto[idx_vistos:idx_considerando].strip()
        if idx_considerando >= 0 and idx_resuelvo > idx_considerando:
            considerandos = texto[idx_considerando:idx_resuelvo].strip()
        if idx_resuelvo >= 0:
            resuelvo = texto[idx_resuelvo:].strip()

        # Determinar confianza según nivel
        confianza_base = {1: 0.95, 2: 0.75, 3: 0.55}
        confianza = confianza_base.get(caso.nivel_complejidad, 0.5)

        # Advertencias
        advertencias = []
        if caso.nivel_complejidad == 2:
            advertencias.append("Caso difícil: se recomienda revisión minuciosa de la fundamentación interpretativa.")
        if caso.nivel_complejidad == 3:
            advertencias.append("Caso constitucional: la ponderación de principios requiere especial atención del magistrado.")
        if caso.hay_cuestion_constitucional:
            advertencias.append("Se detectó cuestión constitucional: verificar doctrina de la CSJN citada.")
        if not self.gemini_client and not self.client and not self.groq_key:
            advertencias.append("MODO DEMOSTRACIÓN: sentencia generada sin IA. Configure GEMINI_API_KEY o GROQ_API_KEY para generación real.")

        return SentenciaGenerada(
            vistos=vistos,
            considerandos=considerandos,
            resuelvo=resuelvo,
            texto_completo=texto,
            nivel_complejidad=caso.nivel_complejidad,
            confianza=confianza,
            advertencias=advertencias,
            notas_para_juez="Proyecto de sentencia generado por el sistema JUSTICIA ARGENTINA. "
                           "Este documento es un BORRADOR para revisión del magistrado.",
        )


# ================================================================
# FUNCIÓN DE CONVENIENCIA
# ================================================================

def generar(caso_dict: dict, precedentes: list = None,
            normas: list = None, api_key: str = None) -> dict:
    """
    Función simple para generar una sentencia desde un diccionario.
    Útil para la API.
    """
    # Construir CasoInput
    partes = caso_dict.get('partes', [])
    caso = CasoInput(
        caratula=caso_dict.get('caratula', ''),
        expediente=caso_dict.get('expediente', ''),
        rama=caso_dict.get('rama', 'civil_comercial'),
        subrama=caso_dict.get('subrama', ''),
        tipo_proceso=caso_dict.get('tipo_proceso', 'ordinario'),
        tribunal=caso_dict.get('tribunal', ''),
        jurisdiccion=caso_dict.get('jurisdiccion', 'Nacional'),
        instancia=caso_dict.get('instancia', 'primera'),
        hechos_probados=caso_dict.get('hechos_probados', ''),
        prueba_valorada=caso_dict.get('prueba_valorada', ''),
        partes=partes,
        cuestiones_a_resolver=caso_dict.get('cuestiones_a_resolver', []),
        hay_cuestion_constitucional=caso_dict.get('hay_cuestion_constitucional', False),
        descripcion_cuestion_constitucional=caso_dict.get('descripcion_cuestion_constitucional', ''),
        nivel_complejidad=caso_dict.get('nivel_complejidad', 1),
        tipo_organo=caso_dict.get('tipo_organo', ''),
        sentencia_primera_instancia=caso_dict.get('sentencia_primera_instancia', ''),
        agravios=caso_dict.get('agravios', ''),
        valoracion_prueba=caso_dict.get('valoracion_prueba', ''),
        tipo_recurso_casacion=caso_dict.get('tipo_recurso_casacion', ''),
        causal_casacion=caso_dict.get('causal_casacion', ''),
        sentencia_recurrida=caso_dict.get('sentencia_recurrida', ''),
        recurso_casacion_texto=caso_dict.get('recurso_casacion_texto', ''),
        contestacion_recurso=caso_dict.get('contestacion_recurso', ''),
        tipo_cuestion_federal=caso_dict.get('tipo_cuestion_federal', ''),
        cuestion_federal=caso_dict.get('cuestion_federal', ''),
        es_queja=caso_dict.get('es_queja', False),
        introduccion_oportuna=caso_dict.get('introduccion_oportuna', ''),
        imputado=caso_dict.get('imputado', ''),
        delito_imputado=caso_dict.get('delito_imputado', ''),
        pena_solicitada=caso_dict.get('pena_solicitada', ''),
        atenuantes=caso_dict.get('atenuantes', ''),
        agravantes=caso_dict.get('agravantes', ''),
        prision_preventiva=caso_dict.get('prision_preventiva', ''),
    )

    generador = GeneradorSentencias(api_key=api_key)
    sentencia = generador.generar_sentencia(caso, precedentes, normas)

    return {
        'vistos': sentencia.vistos,
        'considerandos': sentencia.considerandos,
        'resuelvo': sentencia.resuelvo,
        'texto_completo': sentencia.texto_completo,
        'nivel_complejidad': sentencia.nivel_complejidad,
        'confianza': sentencia.confianza,
        'advertencias': sentencia.advertencias,
        'notas_para_juez': sentencia.notas_para_juez,
    }
