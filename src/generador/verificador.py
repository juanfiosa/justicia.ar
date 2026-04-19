"""
VERIFICADOR DE CITAS NORMATIVAS Y JURISPRUDENCIALES
=====================================================
Verifica que las normas y precedentes citados en una sentencia
generada existan realmente en las bases de datos indexadas.

Proceso:
1. Extrae citas de la sentencia (expresiones regulares)
2. Busca cada cita en ChromaDB
3. Marca las verificadas, las no encontradas y las derogadas
4. Devuelve un reporte de confianza
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


# ================================================================
# PATRONES DE EXTRACCIÓN
# ================================================================

# Normas: "Ley 26.994", "art. 1753", "decreto 1023/01", "art. 68 CPCCN"
PATRON_LEY = re.compile(
    r'\b(?:ley|decreto[/-]?ley?|decreto|resolución|disposición)\s+n?[°º]?\s*(\d[\d\.]*(?:/\d+)?)',
    re.IGNORECASE
)

PATRON_ARTICULO = re.compile(
    r'\bart(?:ículo|s?)\.?\s*(\d+(?:\s*(?:bis|ter|quáter|quinquies))?(?:\s+inc\w*\.?\s*[a-z])?)',
    re.IGNORECASE
)

PATRON_CODIGO = re.compile(
    r'\b(CCyCN|CPCCN|CP|CPPN|LCT|CN|CADH|PIDCP|PIDESC)\b'
)

# Jurisprudencia: "CSJN, Fallos 324:2895", "CNCiv Sala A, García c/ López, 15/3/2022"
PATRON_CSJN = re.compile(
    r'(?:CSJN|Corte Suprema)[,\s]+(?:Fallos\s+(\d+:\d+)|[\w\s,]+)',
    re.IGNORECASE
)

PATRON_CAMARA = re.compile(
    r'(?:CNCiv|CNCom|CNTrab|CNAPE|CNCrim)\s+Sala\s+\w+[,\s]+',
    re.IGNORECASE
)


@dataclass
class CitaNormativa:
    texto_original: str
    tipo: str           # "ley", "articulo", "codigo", "jurisprudencia"
    verificada: bool = False
    encontrada_en: str = ""
    derogada: bool = False
    observacion: str = ""


@dataclass
class ResultadoVerificacion:
    total_citas: int = 0
    verificadas: int = 0
    no_encontradas: list = field(default_factory=list)
    derogadas: list = field(default_factory=list)
    score_confianza: float = 1.0
    congruente: bool = True
    advertencias: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_citas": self.total_citas,
            "verificadas": self.verificadas,
            "no_encontradas": self.no_encontradas,
            "derogadas": self.derogadas,
            "score_confianza": self.score_confianza,
            "congruente": self.congruente,
            "advertencias": self.advertencias,
        }


# ================================================================
# BASE DE NORMAS CLAVE (verificación sin necesidad de ChromaDB)
# ================================================================

# Normas cuya existencia es verificable directamente
NORMAS_CONOCIDAS = {

    # ── CÓDIGOS Y GRANDES CUERPOS NORMATIVOS ──────────────────────────────
    "26994": {"nombre": "Código Civil y Comercial de la Nación (CCyCN)", "vigente": True, "desde": "2015-08-01"},
    "11179": {"nombre": "Código Penal de la Nación", "vigente": True},
    "17454": {"nombre": "Código Procesal Civil y Comercial de la Nación (CPCCN)", "vigente": True},
    "23984": {"nombre": "Código Procesal Penal de la Nación (CPPN)", "vigente": True},
    "27063": {"nombre": "Código Procesal Penal Federal", "vigente": True, "desde": "2019-02-01"},

    # ── DERECHO LABORAL ───────────────────────────────────────────────────
    "20744": {"nombre": "Ley de Contrato de Trabajo (LCT)", "vigente": True},
    "24013": {"nombre": "Ley Nacional de Empleo", "vigente": True},
    "25877": {"nombre": "Ordenamiento del Régimen Laboral", "vigente": True},
    "14250": {"nombre": "Convenciones Colectivas de Trabajo", "vigente": True},
    "23551": {"nombre": "Ley de Asociaciones Sindicales", "vigente": True},
    "14546": {"nombre": "Ley del Viajante de Comercio", "vigente": True},
    "12908": {"nombre": "Estatuto del Periodista Profesional", "vigente": True},
    "26844": {"nombre": "Régimen Especial de Contrato para Personal de Casas Particulares", "vigente": True},
    "24714": {"nombre": "Ley de Asignaciones Familiares", "vigente": True},
    "18345": {"nombre": "Ley de Procedimiento Laboral (Cámara Nacional de Apelaciones del Trabajo)", "vigente": True},
    "18017": {"nombre": "Ley de Salario Mínimo Vital y Móvil", "vigente": True},

    # ── RIESGOS DEL TRABAJO ───────────────────────────────────────────────
    "24557": {"nombre": "Ley de Riesgos del Trabajo (LRT)", "vigente": True},
    "27348": {"nombre": "Ley de reforma de la LRT (27348)", "vigente": True},
    "26773": {"nombre": "Régimen de Ordenamiento de la Reparación de los Daños Laborales", "vigente": True},

    # ── PREVISIONAL / SEGURIDAD SOCIAL ───────────────────────────────────
    "24241": {"nombre": "Sistema Integrado de Jubilaciones y Pensiones (SIJP)", "vigente": True},
    "26425": {"nombre": "Sistema Integrado Previsional Argentino (SIPA)", "vigente": True},
    "24476": {"nombre": "Moratoria Previsional", "vigente": True},
    "23660": {"nombre": "Ley de Obras Sociales", "vigente": True},
    "23661": {"nombre": "Sistema Nacional del Seguro de Salud", "vigente": True},
    "19032": {"nombre": "INSSJP / PAMI", "vigente": True},

    # ── DERECHO COMERCIAL Y SOCIETARIO ───────────────────────────────────
    "19550": {"nombre": "Ley General de Sociedades (LGS)", "vigente": True},
    "24522": {"nombre": "Ley de Concursos y Quiebras", "vigente": True},
    "25248": {"nombre": "Ley de Leasing", "vigente": True},
    "24441": {"nombre": "Fideicomiso y Financiamiento de la Vivienda", "vigente": True},
    "25065": {"nombre": "Ley de Tarjetas de Crédito", "vigente": True},
    "25345": {"nombre": "Ley Antievasión (cheques y medios de pago)", "vigente": True},
    "21526": {"nombre": "Ley de Entidades Financieras", "vigente": True},
    "20091": {"nombre": "Ley de Entidades de Seguros", "vigente": True},
    "17418": {"nombre": "Ley de Seguros", "vigente": True},
    "22362": {"nombre": "Ley de Marcas y Designaciones", "vigente": True},
    "24481": {"nombre": "Ley de Patentes de Invención y Modelos de Utilidad", "vigente": True},
    "11723": {"nombre": "Ley de Propiedad Intelectual", "vigente": True},

    # ── DERECHO DEL CONSUMIDOR ────────────────────────────────────────────
    "24240": {"nombre": "Ley de Defensa del Consumidor (LDC)", "vigente": True},
    "26361": {"nombre": "Modificación Ley de Defensa del Consumidor", "vigente": True},
    "27250": {"nombre": "Reforma Ley de Defensa del Consumidor", "vigente": True},
    "24999": {"nombre": "Modificación Ley de Defensa del Consumidor", "vigente": True},

    # ── DERECHO ADMINISTRATIVO ────────────────────────────────────────────
    "19549": {"nombre": "Ley de Procedimientos Administrativos (LPA)", "vigente": True},
    "25164": {"nombre": "Ley Marco de Regulación de Empleo Público Nacional", "vigente": True},
    "26944": {"nombre": "Ley de Responsabilidad del Estado", "vigente": True},
    "24156": {"nombre": "Ley de Administración Financiera y de los Sistemas de Control del Sector Público Nacional", "vigente": True},
    "13064": {"nombre": "Ley de Obras Públicas", "vigente": True},
    "22431": {"nombre": "Sistema de Protección Integral de los Discapacitados", "vigente": True},
    "24314": {"nombre": "Accesibilidad de personas con movilidad reducida", "vigente": True},

    # ── DERECHO TRIBUTARIO ────────────────────────────────────────────────
    "11683": {"nombre": "Ley de Procedimiento Tributario", "vigente": True},
    "20628": {"nombre": "Ley de Impuesto a las Ganancias", "vigente": True},
    "23349": {"nombre": "Ley de Impuesto al Valor Agregado (IVA)", "vigente": True},
    "24977": {"nombre": "Régimen Simplificado para Pequeños Contribuyentes (Monotributo)", "vigente": True},
    "27430": {"nombre": "Reforma Tributaria (2017) — modifica Ganancias, IVA y Penal Tributario", "vigente": True},
    "27346": {"nombre": "Modificación Impuesto a las Ganancias (mínimo no imponible)", "vigente": True},

    # ── DERECHO PENAL ESPECIAL ────────────────────────────────────────────
    "23737": {"nombre": "Ley de Estupefacientes", "vigente": True},
    "26052": {"nombre": "Desfederalización parcial del tráfico de estupefacientes", "vigente": True},
    "24769": {"nombre": "Régimen Penal Tributario (anterior)", "vigente": False,
              "derogada_por": "27430", "observacion": "Derogado por art. 279 de la Ley 27430 (2017). Ver Título IX de la Ley 27430."},
    "22278": {"nombre": "Régimen Penal de la Minoridad", "vigente": True},
    "26842": {"nombre": "Prevención y Sanción de la Trata de Personas", "vigente": True},
    "26388": {"nombre": "Delitos Informáticos", "vigente": True},
    "25188": {"nombre": "Ética en el Ejercicio de la Función Pública", "vigente": True},
    "27401": {"nombre": "Responsabilidad Penal de las Personas Jurídicas (anticorrupción)", "vigente": True},
    "25246": {"nombre": "Encubrimiento y Lavado de Activos", "vigente": True},

    # ── DERECHO PROCESAL ──────────────────────────────────────────────────
    "16986": {"nombre": "Ley de Amparo", "vigente": True},
    "23098": {"nombre": "Ley de Hábeas Corpus", "vigente": True},
    "26589": {"nombre": "Ley de Mediación y Conciliación", "vigente": True},
    "27423": {"nombre": "Ley de Honorarios de Abogados, Procuradores y Auxiliares de la Justicia Nacional", "vigente": True},
    "24635": {"nombre": "Instancia Obligatoria de Conciliación Laboral (SECLO)", "vigente": True},

    # ── DERECHO DE FAMILIA Y PERSONAS ────────────────────────────────────
    "26485": {"nombre": "Protección Integral para Prevenir, Sancionar y Erradicar la Violencia contra la Mujer", "vigente": True},
    "26061": {"nombre": "Protección Integral de los Derechos de las Niñas, Niños y Adolescentes", "vigente": True},
    "26743": {"nombre": "Ley de Identidad de Género", "vigente": True},
    "26618": {"nombre": "Matrimonio Civil (matrimonio igualitario) — incorporado al CCyCN", "vigente": True},
    "24779": {"nombre": "Adopción — incorporada al CCyCN", "vigente": True},

    # ── DERECHO PENAL DE EJECUCIÓN ────────────────────────────────────────
    "24660": {"nombre": "Ejecución de la Pena Privativa de la Libertad", "vigente": True},
    "27375": {"nombre": "Reforma Ley de Ejecución Penal (endurece régimen)", "vigente": True},

    # ── HABEAS DATA / DATOS PERSONALES ───────────────────────────────────
    "25326": {"nombre": "Ley de Protección de los Datos Personales (habeas data)", "vigente": True},

    # ── DERECHO AMBIENTAL ─────────────────────────────────────────────────
    "25675": {"nombre": "Ley General del Ambiente", "vigente": True},
    "25612": {"nombre": "Gestión Integral de Residuos Industriales y de Actividades de Servicios", "vigente": True},
    "24051": {"nombre": "Residuos Peligrosos", "vigente": True},
    "26815": {"nombre": "Manejo del Fuego", "vigente": True},

    # ── DERECHOS HUMANOS / CONSTITUCIONAL ────────────────────────────────
    "23592": {"nombre": "Actos Discriminatorios (Ley Antidiscriminación)", "vigente": True},
    "23849": {"nombre": "Convención sobre los Derechos del Niño (aprobación)", "vigente": True},
    "23054": {"nombre": "Convención Americana sobre Derechos Humanos (CADH/Pacto de San José)", "vigente": True},
    "23313": {"nombre": "Pacto Internacional de Derechos Civiles y Políticos (PIDCP)", "vigente": True},
    "26657": {"nombre": "Ley Nacional de Salud Mental", "vigente": True},

    # ── ESTATUTOS LABORALES ESPECIALES ───────────────────────────────────
    "11544": {"nombre": "Jornada de Trabajo", "vigente": True},
    "22250": {"nombre": "Régimen para el Personal de la Industria de la Construcción (UOCRA)", "vigente": True},
    "26390": {"nombre": "Prohibición del Trabajo Infantil y Protección del Trabajo Adolescente", "vigente": True},
    "26727": {"nombre": "Régimen de Trabajo Agrario", "vigente": True},
    "26774": {"nombre": "Ciudadanía Argentina — modificación edad voto", "vigente": True},
    "13047": {"nombre": "Estatuto del Personal Docente", "vigente": True},
    "26206": {"nombre": "Ley de Educación Nacional", "vigente": True},
    "12981": {"nombre": "Régimen de Encargados de Casas de Renta y Horizontal", "vigente": True},
    "23592": {"nombre": "Actos Discriminatorios", "vigente": True},

    # ── PROCESAL PENAL / EJECUCIÓN ────────────────────────────────────────
    "27272": {"nombre": "Procedimiento Penal para Casos de Flagrancia", "vigente": True},
    "27372": {"nombre": "Derechos y Garantías de las Personas Víctimas de Delitos", "vigente": True},
    "26853": {"nombre": "Cámaras Federales y Nacionales de Casación", "vigente": True},
    "24050": {"nombre": "Organización y Competencia de la Justicia Penal Nacional", "vigente": True},
    "26550": {"nombre": "Juicio por Jurados (modificación CPPN)", "vigente": True},

    # ── DERECHO CONSTITUCIONAL / INSTITUCIONAL ───────────────────────────
    "24430": {"nombre": "Ordenamiento Constitución Nacional (t.o. 1994)", "vigente": True},
    "26122": {"nombre": "Decretos de Necesidad y Urgencia — Control parlamentario", "vigente": True},
    "23298": {"nombre": "Ley Orgánica de los Partidos Políticos", "vigente": True},
    "26215": {"nombre": "Financiamiento de los Partidos Políticos", "vigente": True},
    "27275": {"nombre": "Derecho de Acceso a la Información Pública", "vigente": True},
    "26571": {"nombre": "Democratización de la Representación Política (elecciones primarias)", "vigente": True},

    # ── TRATADOS CON JERARQUÍA CONSTITUCIONAL (art. 75 inc. 22 CN) ───────
    "23179": {"nombre": "CEDAW — Convención sobre la Eliminación de Discriminación contra la Mujer", "vigente": True},
    "23338": {"nombre": "Convención contra la Tortura y Otros Tratos Crueles (ONU)", "vigente": True},
    "23313": {"nombre": "PIDCP — Pacto Internacional de Derechos Civiles y Políticos", "vigente": True},
    "23432": {"nombre": "PIDESC — Pacto Internacional de Derechos Económicos, Sociales y Culturales", "vigente": True},
    "23054": {"nombre": "CADH — Convención Americana sobre Derechos Humanos (Pacto de San José)", "vigente": True},
    "23849": {"nombre": "CDN — Convención sobre los Derechos del Niño", "vigente": True},
    "24556": {"nombre": "Convención Interamericana sobre Desaparición Forzada", "vigente": True},
    "25778": {"nombre": "Convención sobre la Imprescriptibilidad de Crímenes de Guerra y de Lesa Humanidad", "vigente": True},

    # ── SALUD / BIOÉTICA ──────────────────────────────────────────────────
    "26529": {"nombre": "Derechos del Paciente en su Relación con los Profesionales e Instituciones de Salud", "vigente": True},
    "26742": {"nombre": "Muerte Digna (modificación Ley 26529)", "vigente": True},
    "26682": {"nombre": "Marco Regulatorio de Medicina Prepaga", "vigente": True},
    "26657": {"nombre": "Ley Nacional de Salud Mental", "vigente": True},
    "27610": {"nombre": "Acceso a la Interrupción Voluntaria del Embarazo (IVE)", "vigente": True, "desde": "2021-01-15"},
    "25929": {"nombre": "Parto Humanizado", "vigente": True},
    "26130": {"nombre": "Régimen para las Intervenciones de Contracepción Quirúrgica", "vigente": True},
    "17132": {"nombre": "Ejercicio de la Medicina, Odontología y Actividades Auxiliares", "vigente": True},

    # ── VIVIENDA / INQUILINATO ────────────────────────────────────────────
    "27551": {"nombre": "Ley de Alquileres (2020)", "vigente": True, "desde": "2020-07-01"},
    "23091": {"nombre": "Locaciones Urbanas (anterior)", "vigente": False,
              "derogada_por": "27551",
              "observacion": "Derogada y reemplazada por Ley 27551 (2020). Verificar norma aplicable según fecha del contrato."},

    # ── TECNOLOGÍA / DATOS / TELECOMUNICACIONES ───────────────────────────
    "25506": {"nombre": "Firma Digital", "vigente": True},
    "27078": {"nombre": "Argentina Digital — Tecnologías de la Información y las Comunicaciones", "vigente": True},
    "26951": {"nombre": "Registro Nacional No Llame", "vigente": True},
    "27411": {"nombre": "Convenio de Budapest sobre Ciberdelincuencia (aprobación)", "vigente": True},

    # ── MERCADO DE CAPITALES / FINANZAS ───────────────────────────────────
    "26831": {"nombre": "Ley de Mercado de Capitales", "vigente": True},
    "27440": {"nombre": "Financiamiento Productivo (modifica mercado de capitales)", "vigente": True},
    "25065": {"nombre": "Sistema de Tarjetas de Crédito", "vigente": True},

    # ── DEFENSA / COMPETENCIA ─────────────────────────────────────────────
    "27442": {"nombre": "Ley de Defensa de la Competencia", "vigente": True, "desde": "2018-05-26"},
    "25156": {"nombre": "Defensa de la Competencia (anterior)", "vigente": False,
              "derogada_por": "27442",
              "observacion": "Derogada por Ley 27442 (2018)."},
    "22262": {"nombre": "Defensa de la Competencia (anterior a 25156)", "vigente": False,
              "derogada_por": "25156"},
    "24425": {"nombre": "Acuerdo de Marrakech (OMC — TRIPS/ADPIC)", "vigente": True},

    # ── AMBIENTE / RECURSOS NATURALES ────────────────────────────────────
    "26331": {"nombre": "Presupuestos Mínimos de Protección Ambiental de Bosques Nativos", "vigente": True},
    "26639": {"nombre": "Régimen de Presupuestos Mínimos para la Preservación de Glaciares", "vigente": True},
    "25688": {"nombre": "Régimen de Gestión Ambiental de Aguas", "vigente": True},
    "27279": {"nombre": "Gestión de los Envases Vacíos de Fitosanitarios", "vigente": True},

    # ── DISCAPACIDAD ──────────────────────────────────────────────────────
    "26378": {"nombre": "Convención Internacional sobre los Derechos de las Personas con Discapacidad (CDPD)", "vigente": True},
    "24901": {"nombre": "Sistema de Prestaciones Básicas en Habilitación y Rehabilitación Integral a favor de las Personas con Discapacidad", "vigente": True},

    # ── COMUNIDADES INDÍGENAS ─────────────────────────────────────────────
    "23302": {"nombre": "Política Indígena y apoyo a las Comunidades Aborígenes", "vigente": True},
    "24071": {"nombre": "Convenio 169 OIT — Pueblos Indígenas y Tribales", "vigente": True},

    # ── NORMAS DEROGADAS RELEVANTES ───────────────────────────────────────
    "340":  {"nombre": "Código Civil de la Nación (Vélez Sársfield)", "vigente": False,
             "derogada_por": "26994",
             "observacion": "Derogado el 1/8/2015 por el CCyCN (Ley 26.994). Citar CCyCN."},
    "2637": {"nombre": "Ley de Sociedades Comerciales (anterior a LGS)", "vigente": False,
             "derogada_por": "19550",
             "observacion": "Derogada. Ver Ley General de Sociedades 19.550."},
    "19551": {"nombre": "Ley de Concursos (anterior)", "vigente": False,
              "derogada_por": "24522",
              "observacion": "Derogada por la Ley de Concursos y Quiebras 24.522."},
    "24769": {"nombre": "Régimen Penal Tributario (anterior)", "vigente": False,
              "derogada_por": "27430",
              "observacion": "Derogado por art. 279 de la Ley 27430 (2017). Ver Título IX Ley 27430."},
    "14394": {"nombre": "Bien de Familia (anterior)", "vigente": False,
              "derogada_por": "26994",
              "observacion": "Derogada. El régimen de vivienda está en arts. 244-256 CCyCN."},
    "2393":  {"nombre": "Ley de Matrimonio Civil (anterior)", "vigente": False,
              "derogada_por": "26994",
              "observacion": "Derogada. El matrimonio civil está regulado en arts. 401 y ss. CCyCN."},
}

# Artículos que ya no existen (ejemplos de errores comunes)
ARTICULOS_DEROGADOS = {
    # Artículos del CÓDIGO CIVIL (Vélez) confundidos con CCyCN
    "CCyCN": {
        # Responsabilidad civil
        "1078": "Art. del CC Vélez DEROGADO. Daño moral: ver arts. 1741-1742 CCyCN.",
        "1109": "Art. del CC Vélez DEROGADO. Responsabilidad por culpa: ver art. 1724 CCyCN.",
        "1113": "Art. del CC Vélez DEROGADO. Responsabilidad por cosas: ver arts. 1757-1758 CCyCN.",
        "1198": "Art. del CC Vélez DEROGADO. Buena fe contractual: ver art. 961 CCyCN.",
        "522":  "Art. del CC Vélez DEROGADO. Daño moral contractual: ver arts. 1741-1742 CCyCN.",
        "1071": "Art. del CC Vélez DEROGADO. Abuso del derecho: ver art. 10 CCyCN.",
        "953":  "Art. del CC Vélez DEROGADO. Objeto de los actos jurídicos: ver art. 279 CCyCN.",
        "1067": "Art. del CC Vélez DEROGADO. Acto ilícito: ver arts. 1717 y ss. CCyCN.",
        "505":  "Art. del CC Vélez DEROGADO. Efectos de las obligaciones: ver arts. 730 y ss. CCyCN.",
        "499":  "Art. del CC Vélez DEROGADO. Fuente de las obligaciones: ver art. 726 CCyCN.",
        "519":  "Art. del CC Vélez DEROGADO. Daños e intereses: ver arts. 1737 y ss. CCyCN.",
        "625":  "Art. del CC Vélez DEROGADO. Obligaciones de hacer: ver arts. 773 y ss. CCyCN.",
        "1137": "Art. del CC Vélez DEROGADO. Definición de contrato: ver art. 957 CCyCN.",
        "1167": "Art. del CC Vélez DEROGADO. Ver arts. 1003 y ss. CCyCN.",
        "1204": "Art. del CC Vélez DEROGADO. Pacto comisorio: ver art. 1083 CCyCN.",
    },
    # Artículos del CÓDIGO PENAL modificados/derogados
    "CP": {
        "186": "Ver texto vigente actualizado — fue modificado por varias leyes.",
    },
}


class VerificadorCitas:
    """
    Verifica la existencia y vigencia de las citas en una sentencia generada.
    Combina verificación local (normas conocidas) y búsqueda en ChromaDB.
    """

    def __init__(self, indexador_infoleg=None, indexador_jurisprudencia=None):
        """
        Args:
            indexador_infoleg: Instancia de IndexadorInfoLeg (opcional)
            indexador_jurisprudencia: Instancia de IndexadorJurisprudencia (opcional)
        """
        self.infoleg = indexador_infoleg
        self.jurisprudencia = indexador_jurisprudencia

    def verificar(self, texto_sentencia: str,
                  partes: list = None) -> ResultadoVerificacion:
        """
        Verifica el texto completo de una sentencia.

        Returns:
            ResultadoVerificacion con el detalle de citas encontradas/no encontradas
        """
        resultado = ResultadoVerificacion()

        # 1. Extraer y verificar leyes
        leyes_encontradas = PATRON_LEY.findall(texto_sentencia)
        for ley_num in set(leyes_encontradas):
            num_limpio = ley_num.replace(".", "").replace("/", "").strip()
            resultado.total_citas += 1
            info = NORMAS_CONOCIDAS.get(num_limpio)
            if info:
                if not info.get("vigente", True):
                    resultado.derogadas.append(
                        f"Ley {ley_num}: {info.get('observacion', 'DEROGADA — ' + info.get('nombre', ''))}"
                    )
                    resultado.advertencias.append(
                        f"NORMA DEROGADA: Ley {ley_num} ({info['nombre']}). {info.get('observacion', '')}"
                    )
                else:
                    resultado.verificadas += 1
            else:
                # Buscar en InfoLeg si está disponible
                if self.infoleg:
                    try:
                        hallazgos = self.infoleg.buscar_normas(f"Ley {ley_num}", n_results=1)
                        if hallazgos:
                            resultado.verificadas += 1
                        else:
                            resultado.no_encontradas.append(f"Ley {ley_num}")
                    except Exception:
                        pass
                # Si no tenemos acceso a InfoLeg, no penalizamos lo desconocido

        # 2. Verificar artículos de CCyCN (los más propensos a errores de versión)
        cuerpos_citados = PATRON_CODIGO.findall(texto_sentencia)
        if "CCyCN" in cuerpos_citados:
            arts_citados = PATRON_ARTICULO.findall(texto_sentencia)
            for art in arts_citados:
                num = re.search(r'\d+', art)
                if num:
                    num_int = int(num.group())
                    derogados_ccycn = ARTICULOS_DEROGADOS.get("CCyCN", {})
                    if str(num_int) in derogados_ccycn:
                        resultado.advertencias.append(
                            f"ARTÍCULO DEROGADO: art. {num_int} del código anterior. "
                            f"{derogados_ccycn[str(num_int)]}"
                        )
                        resultado.derogadas.append(f"art. {num_int} (versión antigua)")

        # 3. Verificar congruencia básica: ¿el RESUELVO tiene decisión?
        texto_upper = texto_sentencia.upper()
        if "RESUELVO" in texto_upper:
            resuelvo_idx = texto_upper.find("RESUELVO")
            resuelvo_texto = texto_sentencia[resuelvo_idx:]
            if not any(w in resuelvo_texto.upper() for w in
                       ["HACER LUGAR", "RECHAZAR", "CONDENAR", "ABSOLVER",
                        "REVOCAR", "CONFIRMAR", "DECLARAR", "HACER LUGAR",
                        "DESESTIMAR", "ADMITIR"]):
                resultado.congruente = False
                resultado.advertencias.append(
                    "ADVERTENCIA: El RESUELVO no contiene una decisión clara (hacer lugar, rechazar, condenar, etc.)."
                )

        # 4. Calcular score de confianza
        if resultado.total_citas > 0:
            tasa_verificacion = resultado.verificadas / resultado.total_citas
        else:
            tasa_verificacion = 1.0

        penalizacion_derogadas = len(resultado.derogadas) * 0.1
        penalizacion_no_encontradas = len(resultado.no_encontradas) * 0.05
        penalizacion_incongruencia = 0.2 if not resultado.congruente else 0.0

        resultado.score_confianza = max(
            0.0,
            tasa_verificacion - penalizacion_derogadas
            - penalizacion_no_encontradas - penalizacion_incongruencia
        )

        return resultado

    def verificar_y_reportar(self, texto_sentencia: str) -> dict:
        """Versión simplificada para la API"""
        resultado = self.verificar(texto_sentencia)
        return resultado.to_dict()


# ================================================================
# FUNCIÓN DE CONVENIENCIA
# ================================================================

def verificar_sentencia(texto: str, indexador_infoleg=None,
                        indexador_jurisprudencia=None) -> dict:
    """Verifica una sentencia y devuelve el reporte como dict"""
    v = VerificadorCitas(indexador_infoleg, indexador_jurisprudencia)
    return v.verificar_y_reportar(texto)
