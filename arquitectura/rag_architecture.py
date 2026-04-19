"""
JUSTICIA ARGENTINA - Arquitectura RAG (Retrieval-Augmented Generation)
======================================================================

Sistema de generación de sentencias asistido por recuperación de información.

Flujo general:
    1. INGESTA: El juez carga hechos probados + pretensiones + argumentos jurídicos
    2. CLASIFICACIÓN: Se identifica rama del derecho, tipo de proceso, complejidad
    3. RECUPERACIÓN (Retrieval): Se buscan normas y precedentes relevantes
    4. GENERACIÓN: El LLM produce el proyecto de sentencia
    5. VERIFICACIÓN: Se validan citas normativas y jurisprudenciales
    6. PRESENTACIÓN: Formato Vistos / Considerando / Resuelvo

Principios de diseño:
    - Quaestio facti la fija el juez; la plataforma resuelve la quaestio iuris
    - El sistema es un copiloto: propone, el juez decide
    - Transparencia: toda fuente normativa y jurisprudencial debe ser verificable
    - Congruencia procesal: la sentencia debe pronunciarse sobre lo pedido
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ================================================================
# MODELOS DE DATOS - ENTRADA DEL JUEZ
# ================================================================

class RamaDerecho(Enum):
    CIVIL_COMERCIAL = "civil_comercial"
    PENAL = "penal"
    LABORAL = "laboral"
    ADMINISTRATIVO = "administrativo"
    TRIBUTARIO = "tributario"
    CONSTITUCIONAL = "constitucional"


class TipoProceso(Enum):
    # Civil/Comercial
    ORDINARIO = "ordinario"
    SUMARISIMO = "sumarísimo"
    EJECUTIVO = "ejecutivo"
    AMPARO = "amparo"
    SUCESORIO = "sucesorio"
    CONCURSAL = "concursal"
    # Penal
    JUICIO_ORAL = "juicio_oral"
    ABREVIADO = "abreviado"
    INSTRUCCION = "instrucción"
    # Laboral
    LABORAL_ORDINARIO = "laboral_ordinario"
    # Administrativo
    CONTENCIOSO_ADMIN = "contencioso_administrativo"
    # Otros
    HABEAS_CORPUS = "hábeas_corpus"
    HABEAS_DATA = "hábeas_data"
    ACCION_DECLARATIVA = "acción_declarativa"


class NivelComplejidad(Enum):
    """
    Nivel 1 - Caso rutinario: norma clara, hechos típicos, jurisprudencia pacífica
    Nivel 2 - Caso con matices: requiere interpretación, jurisprudencia no unánime
    Nivel 3 - Caso complejo: colisión de normas, vaguedad significativa, lagunas
    Nivel 4 - Caso constitucional/de derrotabilidad: tensión entre principios,
              caso no previsto, requiere ponderación o argumentación axiológica
    """
    RUTINARIO = 1
    CON_MATICES = 2
    COMPLEJO = 3
    CONSTITUCIONAL = 4


@dataclass
class PosicionProcesal:
    """Posición jurídica de una parte (actor/demandado, acusación/defensa)"""
    parte: str                          # "actor", "demandado", "querellante", "defensa"
    nombre: str                         # Nombre de la parte
    letrado: str                        # Nombre del abogado
    pretension: str                     # Qué pide (ej: "condena al pago de $X por daños")
    fundamentos_juridicos: list[str]    # Normas y doctrina invocadas
    argumentos: str                     # Desarrollo argumentativo libre
    jurisprudencia_citada: list[str]    # Precedentes invocados por la parte


@dataclass
class CasoJudicial:
    """
    Entrada principal del sistema: el caso tal como lo carga el juez.
    El juez fija los HECHOS (quaestio facti).
    Las PARTES aportan su visión del derecho aplicable.
    El SISTEMA resuelve la quaestio iuris.
    """
    # Identificación
    caratula: str                                # "García, Juan c/ Pérez, María s/ daños"
    expediente: str                              # "CNciv 12345/2024"
    rama: RamaDerecho
    subrama: str                                 # ej: "obligaciones_contratos"
    tipo_proceso: TipoProceso
    tribunal: str                                # "Juzgado Nacional Civil Nro. 42"
    jurisdiccion: str                            # "Nacional", "Federal", provincia
    instancia: str                               # "primera", "segunda" (apelación), "casación"

    # Hechos (fijados por el juez - quaestio facti)
    hechos_probados: str                         # Relación detallada de hechos que el juez tiene por acreditados
    prueba_valorada: str                         # Síntesis de la valoración probatoria

    # Posiciones de las partes
    partes: list[PosicionProcesal]               # Mínimo 2: actor y demandado (o equivalentes)

    # Contexto procesal
    cuestiones_a_resolver: list[str]             # Las cuestiones que el juez debe decidir
    hay_reconvencion: bool = False
    hay_cuestion_constitucional: bool = False
    descripcion_cuestion_constitucional: str = ""

    # Metadatos
    nivel_complejidad: Optional[NivelComplejidad] = None  # Se puede fijar o dejar que el sistema clasifique


# ================================================================
# MÓDULO 1: CLASIFICACIÓN Y ANÁLISIS
# ================================================================

@dataclass
class AnalisisCaso:
    """Resultado del análisis automático del caso"""
    rama_detectada: RamaDerecho
    subramas_involucradas: list[str]
    nivel_complejidad: NivelComplejidad
    cuestiones_juridicas: list[str]          # Problemas jurídicos identificados
    normas_potencialmente_aplicables: list[str]
    hay_vaguedad: bool                       # Hay normas vagas que requieren interpretación
    hay_laguna: bool                         # No hay norma directamente aplicable
    hay_contradiccion: bool                  # Normas contradictorias aplicables
    hay_derrotabilidad: bool                 # Caso con propiedad axiológica no prevista
    justificacion_complejidad: str


# ================================================================
# MÓDULO 2: RETRIEVAL - Recuperación de información jurídica
# ================================================================

@dataclass
class FuenteNormativa:
    """Una norma aplicable al caso"""
    tipo: str                                # "ley", "decreto", "resolución", "constitución", "tratado"
    identificacion: str                      # "Ley 26.994, art. 1753"
    texto: str                               # Texto completo del artículo
    vigencia: str                            # "vigente", "derogada", "modificada"
    relevancia_score: float                  # 0.0 a 1.0
    motivo_relevancia: str                   # Por qué es relevante al caso


@dataclass
class Precedente:
    """Un caso precedente relevante"""
    tribunal: str                            # "CSJN", "CNCiv Sala A"
    caratula: str                            # "Rodríguez c/ Google"
    fecha: str
    sumario: str
    doctrina_relevante: str                  # Qué establece que es aplicable al caso actual
    similitud_score: float                   # 0.0 a 1.0
    es_obligatorio: bool                     # True si es de un tribunal superior en la cadena
    fuente_id: str                           # Referencia al registro en la base


@dataclass
class ResultadoRetrieval:
    """Todo lo recuperado para fundamentar la sentencia"""
    normas: list[FuenteNormativa]
    precedentes: list[Precedente]
    doctrina_constitucional: list[str]       # Para casos Nivel 4: doctrina de ponderación
    normas_internacionales: list[str]        # Tratados DDHH si aplica


# ================================================================
# MÓDULO 3: GENERACIÓN DE SENTENCIA
# ================================================================

@dataclass
class SeccionVistos:
    """Sección VISTOS de la sentencia"""
    texto: str
    # Contiene: carátula, tipo de proceso, radicación, trámite procesal


@dataclass
class Considerando:
    """Un considerando individual"""
    numero: int
    titulo: str                              # "La cuestión a resolver", "El marco normativo", etc.
    texto: str
    normas_citadas: list[str]
    precedentes_citados: list[str]


@dataclass
class SeccionConsiderando:
    """Sección CONSIDERANDO de la sentencia"""
    considerandos: list[Considerando]
    # Estructura típica:
    # I. La cuestión a resolver
    # II. El marco normativo aplicable
    # III. Los hechos relevantes (según los fijó el juez)
    # IV. Análisis de las pretensiones del actor
    # V. Análisis de la defensa del demandado
    # VI. Aplicación del derecho a los hechos
    # VII. [Si Nivel 4: Ponderación de principios constitucionales]
    # VIII. Costas
    # IX. Regulación de honorarios


@dataclass
class PuntoResolutivo:
    """Un punto del resuelvo"""
    numero: int
    texto: str                               # "Hacer lugar a la demanda..."


@dataclass
class SeccionResuelvo:
    """Sección RESUELVO de la sentencia"""
    puntos: list[PuntoResolutivo]


@dataclass
class ProyectoSentencia:
    """La sentencia completa generada por el sistema"""
    caso_id: str
    vistos: SeccionVistos
    considerandos: SeccionConsiderando
    resuelvo: SeccionResuelvo
    confianza_global: float                  # 0.0 a 1.0
    advertencias: list[str]                  # Alertas para el juez
    fuentes_verificadas: bool
    requiere_revision_humana: bool           # True para Nivel 3 y 4
    notas_para_juez: str                     # Explicación de decisiones del sistema


# ================================================================
# MÓDULO 4: VERIFICACIÓN
# ================================================================

@dataclass
class ResultadoVerificacion:
    """Resultado de la verificación post-generación"""
    normas_verificadas: int                  # Cuántas normas citadas existen y están vigentes
    normas_no_encontradas: list[str]         # Citas que no se pudieron verificar
    normas_derogadas: list[str]              # Normas citadas que están derogadas
    precedentes_verificados: int
    precedentes_no_encontrados: list[str]
    coherencia_argumentativa: float          # 0.0 a 1.0
    congruencia_con_pretensiones: bool       # ¿Se pronunció sobre todo lo pedido?
    alertas: list[str]


# ================================================================
# PIPELINE PRINCIPAL
# ================================================================

class PipelineJudicialRAG:
    """
    Pipeline completo: Caso → Análisis → Retrieval → Generación → Verificación → Sentencia
    """

    def __init__(self, config: dict):
        """
        config debe incluir:
        - vector_store: conexión al store de embeddings (normas + jurisprudencia)
        - llm_provider: proveedor del LLM (Claude API)
        - db_legislacion: base de datos de legislación vigente
        - db_jurisprudencia: base de datos de jurisprudencia indexada
        """
        self.config = config
        # Los componentes se inicializarán cuando tengamos la infraestructura

    def procesar_caso(self, caso: CasoJudicial) -> ProyectoSentencia:
        """Pipeline principal"""

        # Paso 1: Analizar y clasificar
        analisis = self._analizar_caso(caso)

        # Paso 2: Recuperar normas y precedentes relevantes
        retrieval = self._recuperar_fuentes(caso, analisis)

        # Paso 3: Generar proyecto de sentencia
        sentencia = self._generar_sentencia(caso, analisis, retrieval)

        # Paso 4: Verificar citas y coherencia
        verificacion = self._verificar_sentencia(sentencia, retrieval)

        # Paso 5: Ajustar si hay problemas
        if verificacion.normas_derogadas or verificacion.normas_no_encontradas:
            sentencia = self._corregir_sentencia(sentencia, verificacion)

        # Paso 6: Marcar nivel de revisión requerido
        sentencia.requiere_revision_humana = (
            analisis.nivel_complejidad.value >= 3
            or verificacion.coherencia_argumentativa < 0.8
            or not verificacion.congruencia_con_pretensiones
        )

        return sentencia

    def _analizar_caso(self, caso: CasoJudicial) -> AnalisisCaso:
        """
        Paso 1: Analiza el caso para determinar complejidad y cuestiones jurídicas.

        Para detectar los problemas de indeterminación (vaguedad, lagunas,
        contradicciones, derrotabilidad) usa una combinación de:
        - Análisis semántico del texto de hechos y pretensiones
        - Búsqueda de normas potencialmente aplicables y detección de conflictos
        - Comparación con casos precedentes similares que hayan planteado
          estas cuestiones
        """
        raise NotImplementedError("Implementar con LLM + búsqueda semántica")

    def _recuperar_fuentes(self, caso: CasoJudicial,
                           analisis: AnalisisCaso) -> ResultadoRetrieval:
        """
        Paso 2: Retrieval multi-etapa.

        Estrategia de búsqueda por capas:
        1. Búsqueda por rama/subrama → normas del cuerpo legal principal
        2. Búsqueda semántica por hechos → precedentes similares
        3. Búsqueda por normas citadas por las partes → verificar y ampliar
        4. Si hay cuestión constitucional → buscar doctrina CSJN + Corte IDH
        5. Cross-reference: normas citadas en los precedentes encontrados

        El retrieval es CONTEXTUAL a la rama:
        - Civil: busca en CCyCN, leyes especiales, doctrina de cámaras civiles
        - Penal: busca en CP, CPP, doctrina de casación penal
        - Laboral: busca en LCT, LRT, doctrina de cámaras laborales
        - etc.
        """
        raise NotImplementedError("Implementar con vector store + filtros por rama")

    def _generar_sentencia(self, caso: CasoJudicial,
                           analisis: AnalisisCaso,
                           retrieval: ResultadoRetrieval) -> ProyectoSentencia:
        """
        Paso 3: Genera la sentencia con el LLM.

        El prompt se construye dinámicamente según:
        - La rama del derecho (cada rama tiene su estilo argumentativo)
        - El nivel de complejidad
        - El tipo de proceso

        Para Nivel 1-2: aplicación subsuntiva clásica
            premisa mayor (norma) + premisa menor (hechos) → conclusión

        Para Nivel 3: interpretación + integración
            Se explicitan las interpretaciones posibles, se fundamenta la elegida

        Para Nivel 4: ponderación + argumentación de principios
            Se identifican los principios en tensión, se aplica test de
            proporcionalidad (Alexy), se fundamenta por qué uno prevalece
            en el caso concreto sin anular al otro.

        CLAVE: El sistema debe generar UNA sentencia (no opciones).
        Para Niveles 3-4, explicita su razonamiento y las alternativas
        descartadas en las notas_para_juez, pero la sentencia misma
        decide en un sentido.
        """
        raise NotImplementedError("Implementar con Claude API + prompt engineering por rama")

    def _verificar_sentencia(self, sentencia: ProyectoSentencia,
                             retrieval: ResultadoRetrieval) -> ResultadoVerificacion:
        """
        Paso 4: Verifica que la sentencia generada sea correcta.

        Verificaciones:
        1. Toda norma citada existe en la base de legislación y está vigente
        2. Todo precedente citado existe en la base de jurisprudencia
        3. Las citas textuales de normas coinciden con el texto oficial
        4. Se pronunció sobre todas las cuestiones planteadas (congruencia)
        5. No hay contradicciones internas en la argumentación
        6. Los montos/condenas son consistentes con los fundamentos
        """
        raise NotImplementedError("Implementar con búsqueda exacta + LLM checker")

    def _corregir_sentencia(self, sentencia: ProyectoSentencia,
                            verificacion: ResultadoVerificacion) -> ProyectoSentencia:
        """
        Paso 5: Corrige problemas detectados en la verificación.
        Reemplaza normas derogadas, corrige citas, ajusta argumentación.
        """
        raise NotImplementedError("Implementar con LLM + resultados de verificación")


# ================================================================
# ESTRATEGIA DE EMBEDDINGS POR RAMA
# ================================================================

VECTOR_STORES_CONFIG = {
    "legislacion": {
        "descripcion": "Base de legislación vigente (InfoLeg)",
        "modelo_embedding": "text-embedding-3-large",  # o modelo local
        "chunk_strategy": "por_artículo",               # Cada artículo es un chunk
        "metadata": ["ley", "articulo", "vigencia", "rama", "fecha_sancion"],
        "indices_por_rama": True,                        # Un índice por rama para búsqueda eficiente
    },
    "jurisprudencia": {
        "descripcion": "Base de jurisprudencia (SAIJ + sentencias completas)",
        "modelo_embedding": "text-embedding-3-large",
        "chunk_strategy": "por_sumario_y_doctrina",      # El sumario como unidad semántica
        "metadata": ["tribunal", "materia", "rama_normalizada", "fecha",
                     "caratula", "instancia", "jurisdiccion"],
        "indices_por_rama": True,
    },
    "doctrina_constitucional": {
        "descripcion": "Doctrina CSJN + Corte IDH para casos Nivel 4",
        "modelo_embedding": "text-embedding-3-large",
        "chunk_strategy": "por_considerando_clave",
        "metadata": ["tribunal", "principio", "test_aplicado", "fecha"],
        "indices_por_rama": False,                       # Un solo índice (transversal)
    }
}


# ================================================================
# ESTRATEGIA PARA CASOS DE DERROTABILIDAD (Nivel 4)
# ================================================================

class EstrategiaDerrotabilidad:
    """
    Enfoque para casos donde la norma aplicable es "derrotada" por una
    propiedad axiológica relevante del caso concreto.

    El sistema NO pretende tener "intuición moral" ni "comprensión" en
    sentido fuerte (la crítica de Dupoux es válida en ese punto).

    Lo que SÍ puede hacer:

    1. RECONOCER el caso como derrotable:
       - Detectar que la aplicación literal de la norma produce un resultado
         que contradice principios constitucionales o de DDHH
       - Detectar que el caso tiene propiedades fácticas no contempladas
         por la norma (novedad tecnológica, situación no prevista)

    2. RECUPERAR doctrina de ponderación:
       - Buscar cómo la CSJN y la Corte IDH resolvieron tensiones similares
       - Identificar los tests aplicados (proporcionalidad, razonabilidad)

    3. APLICAR un framework de ponderación estructurado:
       - Identificar principios en tensión (P1 vs P2)
       - Evaluar la idoneidad de la restricción de cada principio
       - Evaluar la necesidad (¿hay alternativa menos restrictiva?)
       - Evaluar la proporcionalidad en sentido estricto
       - Fundamentar la prevalencia de un principio en el caso concreto

    4. TRANSPARENTAR las limitaciones:
       - Explicitar que se trata de un caso sin precedente claro
       - Mostrar al juez las alternativas descartadas y por qué
       - Marcar alta necesidad de revisión humana

    La honestidad epistemológica es clave: el sistema dice "este es mi
    mejor análisis basado en la doctrina existente, pero este caso
    requiere especialmente su criterio judicial".
    """
    pass
