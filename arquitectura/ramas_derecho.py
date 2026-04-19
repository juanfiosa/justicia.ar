"""
JUSTICIA ARGENTINA - Taxonomía de Ramas del Derecho
====================================================
Mapa de ramas del derecho argentino alineado con la organización
de los fueros judiciales existentes (nacionales y federales).

Cada rama tiene:
- id: identificador único
- nombre: nombre formal
- fuero_judicial: fuero(s) correspondiente(s) en la organización judicial
- materias_saij: etiquetas del dataset SAIJ que mapean a esta rama
- normativa_principal: cuerpos normativos centrales
- subramas: especializaciones dentro de la rama
"""

RAMAS_DERECHO = {

    # ================================================================
    # 1. DERECHO CIVIL Y COMERCIAL
    # ================================================================
    "civil_comercial": {
        "id": "civil_comercial",
        "nombre": "Derecho Civil y Comercial",
        "fuero_judicial": [
            "Nacional en lo Civil",
            "Nacional en lo Comercial",
            "Nacional en lo Civil y Comercial Federal",
            "Juzgados Civiles y Comerciales (provinciales)"
        ],
        "materias_saij": [
            "CIVIL", "COMERCIAL", "CIVIL - COMERCIAL", "CIVIL-COMERCIAL",
            "COMERCIAL-CIVIL", "CIVIL - COMERCIAL - PROCESAL",
            "CIVIL-COMERCIAL-PROCESAL", "COMERCIAL-CIVIL-PROCESAL",
            "BANCARIO", "NAVEGACION", "AERONAUTICO",
            "INTERNACIONAL PRIVADO"
        ],
        "normativa_principal": [
            "Código Civil y Comercial de la Nación (Ley 26.994)",
            "Ley General de Sociedades (Ley 19.550)",
            "Ley de Concursos y Quiebras (Ley 24.522)",
            "Ley de Defensa del Consumidor (Ley 24.240)",
            "Código de Comercio (normas subsistentes)",
            "Ley de Navegación (Ley 20.094)",
            "Código Aeronáutico (Ley 17.285)",
        ],
        "subramas": {
            "obligaciones_contratos": {
                "nombre": "Obligaciones y Contratos",
                "descripcion": "Responsabilidad civil, contratos, daños y perjuicios",
                "descriptores_clave": ["daños y perjuicios", "incumplimiento contractual",
                                       "responsabilidad civil", "indemnización"]
            },
            "reales": {
                "nombre": "Derechos Reales",
                "descripcion": "Dominio, posesión, usucapión, hipoteca, propiedad horizontal",
                "descriptores_clave": ["dominio", "posesión", "usucapión", "hipoteca",
                                       "propiedad horizontal", "servidumbre"]
            },
            "familia": {
                "nombre": "Derecho de Familia",
                "descripcion": "Matrimonio, divorcio, alimentos, filiación, adopción, violencia familiar",
                "descriptores_clave": ["divorcio", "alimentos", "tenencia", "régimen de visitas",
                                       "filiación", "adopción", "violencia familiar"]
            },
            "sucesiones": {
                "nombre": "Sucesiones",
                "descripcion": "Sucesión testamentaria e intestada, legítima, colación",
                "descriptores_clave": ["sucesión", "testamento", "legítima", "heredero"]
            },
            "societario": {
                "nombre": "Derecho Societario",
                "descripcion": "Sociedades, asambleas, responsabilidad de directores",
                "descriptores_clave": ["sociedad", "asamblea", "directores", "accionistas"]
            },
            "concursal": {
                "nombre": "Concursos y Quiebras",
                "descripcion": "Concurso preventivo, quiebra, verificación de créditos",
                "descriptores_clave": ["concurso preventivo", "quiebra", "verificación",
                                       "síndico", "acuerdo preventivo"]
            },
            "consumidor": {
                "nombre": "Derecho del Consumidor",
                "descripcion": "Relación de consumo, daño punitivo, prácticas abusivas",
                "descriptores_clave": ["consumidor", "relación de consumo", "daño punitivo",
                                       "cláusula abusiva"]
            },
            "navegacion_aeronautico": {
                "nombre": "Navegación y Aeronáutico",
                "descripcion": "Derecho marítimo, transporte aéreo, abordaje",
                "descriptores_clave": ["navegación", "abordaje", "transporte aéreo", "buque"]
            }
        }
    },

    # ================================================================
    # 2. DERECHO PENAL
    # ================================================================
    "penal": {
        "id": "penal",
        "nombre": "Derecho Penal",
        "fuero_judicial": [
            "Nacional en lo Criminal y Correccional",
            "Nacional en lo Criminal y Correccional Federal",
            "Nacional en lo Penal Económico",
            "Tribunal Oral en lo Criminal",
            "Tribunal Oral en lo Criminal Federal",
            "Cámara Federal de Casación Penal",
            "Juzgados Penales (provinciales)"
        ],
        "materias_saij": [
            "PENAL", "PENAL-PROCESAL", "PROCESAL-PENAL", "PROCESAL PENAL",
            "PROCESAL - PENAL", "PENAL - PROCESAL", "CONTRAVENCIONAL",
            "CONTRAVENCIONAL-PROCESAL", "CONTRAVENCIONAL-CONSTITUCIONAL",
            "PENAL-TRIBUTARIO", "PENAL-ADUANERO"
        ],
        "normativa_principal": [
            "Código Penal de la Nación (Ley 11.179 y modificatorias)",
            "Código Procesal Penal de la Nación (Ley 23.984 / Ley 27.063)",
            "Ley de Estupefacientes (Ley 23.737)",
            "Ley Penal Tributaria (Ley 27.430, Título IX)",
            "Código Aduanero (Ley 22.415) - delitos aduaneros",
            "Ley de Ejecución Penal (Ley 24.660)",
            "Régimen Penal de la Minoridad (Ley 22.278)",
            "Ley de Violencia de Género (Ley 26.485)",
        ],
        "subramas": {
            "comun": {
                "nombre": "Penal Común",
                "descripcion": "Delitos contra las personas, la propiedad, la integridad sexual, etc.",
                "descriptores_clave": ["homicidio", "robo", "hurto", "estafa", "lesiones",
                                       "abuso sexual", "amenazas", "privación de libertad"]
            },
            "economico": {
                "nombre": "Penal Económico",
                "descripcion": "Delitos económicos, tributarios, aduaneros, cambiarios",
                "descriptores_clave": ["evasión", "contrabando", "lavado de activos",
                                       "administración fraudulenta", "balance falso"]
            },
            "federal": {
                "nombre": "Penal Federal",
                "descripcion": "Narcotráfico, trata de personas, terrorismo, delitos federales",
                "descriptores_clave": ["estupefacientes", "trata de personas",
                                       "contrabando", "narcotráfico"]
            },
            "ejecucion": {
                "nombre": "Ejecución Penal",
                "descripcion": "Libertad condicional, salidas transitorias, cómputo de pena",
                "descriptores_clave": ["libertad condicional", "cómputo de pena",
                                       "salida transitoria", "prisión domiciliaria"]
            },
            "contravencional": {
                "nombre": "Contravencional",
                "descripcion": "Contravenciones (CABA y provinciales)",
                "descriptores_clave": ["contravención", "hostigamiento", "ruidos molestos"]
            }
        }
    },

    # ================================================================
    # 3. DERECHO LABORAL
    # ================================================================
    "laboral": {
        "id": "laboral",
        "nombre": "Derecho del Trabajo y la Seguridad Social",
        "fuero_judicial": [
            "Nacional del Trabajo",
            "Federal de la Seguridad Social",
            "Tribunales del Trabajo (provinciales)"
        ],
        "materias_saij": [
            "LABORAL", "LABORAL-PROCESAL", "PROCESAL-LABORAL",
            "PROCESAL LABORAL", "PROCESAL - LABORAL", "LABORAL - PROCESAL",
            "SEGURIDAD SOCIAL", "SEGURIDAD SOCIAL-PROCESAL",
            "PROCESAL-SEGURIDAD SOCIAL", "SEGURIDAD SOCIAL - PROCESAL",
            "LABORAL-CIVIL", "LABORAL-COMERCIAL", "LABORAL-ADMINISTRATIVO",
            "LABORAL-SEGURIDAD SOCIAL", "SEGURIDAD SOCIAL-LABORAL",
            "SEGURIDAD SOCIAL-CONSTITUCIONAL", "SEGURIDAD SOCIAL-ADMINISTRATIVO",
            "SEGURIDAD SOCIAL - ADMINISTRATIVO", "SEGURIDAD SOCIAL - CONSTITUCIONAL"
        ],
        "normativa_principal": [
            "Ley de Contrato de Trabajo (Ley 20.744)",
            "Ley de Riesgos del Trabajo (Ley 24.557 y Ley 27.348)",
            "Ley de Asociaciones Sindicales (Ley 23.551)",
            "Ley de Convenciones Colectivas (Ley 14.250)",
            "Ley de Empleo (Ley 24.013)",
            "Ley de Jornada de Trabajo (Ley 11.544)",
            "Régimen de Jubilaciones y Pensiones (Ley 24.241)",
            "Ley de Procedimiento Laboral (Ley 18.345)",
        ],
        "subramas": {
            "individual": {
                "nombre": "Derecho Individual del Trabajo",
                "descripcion": "Contrato de trabajo, despido, indemnización, accidentes",
                "descriptores_clave": ["despido", "indemnización", "contrato de trabajo",
                                       "accidente de trabajo", "enfermedad profesional"]
            },
            "colectivo": {
                "nombre": "Derecho Colectivo del Trabajo",
                "descripcion": "Sindicatos, negociación colectiva, huelga",
                "descriptores_clave": ["sindicato", "convenio colectivo", "huelga",
                                       "tutela sindical", "práctica desleal"]
            },
            "seguridad_social": {
                "nombre": "Seguridad Social",
                "descripcion": "Jubilaciones, pensiones, obras sociales",
                "descriptores_clave": ["jubilación", "pensión", "movilidad",
                                       "reajuste", "obra social", "ANSES"]
            }
        }
    },

    # ================================================================
    # 4. DERECHO ADMINISTRATIVO
    # ================================================================
    "administrativo": {
        "id": "administrativo",
        "nombre": "Derecho Administrativo",
        "fuero_judicial": [
            "Contencioso Administrativo Federal",
            "Contencioso Administrativo (provinciales)",
            "Contencioso Administrativo y Tributario (CABA)"
        ],
        "materias_saij": [
            "ADMINISTRATIVO", "ADMINISTRATIVO-PROCESAL",
            "PROCESAL-ADMINISTRATIVO", "PROCESAL - ADMINISTRATIVO",
            "ADMINISTRATIVO - PROCESAL", "ADMINISTRATIVO-TRIBUTARIO",
            "ADMINISTRATIVO - TRIBUTARIO", "ADMINISTRATIVO-CIVIL",
            "ADMINISTRATIVO - CIVIL", "ADMINISTRATIVO-COMERCIAL",
            "ADMINISTRATIVO - COMERCIAL", "ADMINISTRATIVO-LABORAL",
            "ADMINISTRATIVO - LABORAL", "ADMINISTRATIVO-PENAL",
            "ADMINISTRATIVO - PENAL", "ADMINISTRATIVO-CONSTITUCIONAL",
            "ADMINISTRATIVO - CONSTITUCIONAL"
        ],
        "normativa_principal": [
            "Ley de Procedimientos Administrativos (Ley 19.549)",
            "Decreto Reglamentario 1759/72",
            "Ley de Expropiaciones (Ley 21.499)",
            "Ley de Obra Pública (Ley 13.064)",
            "Ley de Responsabilidad del Estado (Ley 26.944)",
            "Ley de Empleo Público (Ley 25.164)",
            "Ley de Contrataciones del Estado (Decreto 1023/01)",
        ],
        "subramas": {
            "acto_administrativo": {
                "nombre": "Acto Administrativo",
                "descripcion": "Nulidad, revocación, recursos administrativos",
                "descriptores_clave": ["acto administrativo", "nulidad", "revocación",
                                       "recurso jerárquico", "agotamiento vía administrativa"]
            },
            "empleo_publico": {
                "nombre": "Empleo Público",
                "descripcion": "Estabilidad, cesantía, exoneración, concursos",
                "descriptores_clave": ["empleo público", "estabilidad", "cesantía",
                                       "sumario administrativo"]
            },
            "responsabilidad_estado": {
                "nombre": "Responsabilidad del Estado",
                "descripcion": "Daños por actividad estatal lícita e ilícita",
                "descriptores_clave": ["responsabilidad del Estado", "falta de servicio",
                                       "daño por actividad estatal"]
            },
            "regulatorio": {
                "nombre": "Derecho Regulatorio",
                "descripcion": "Servicios públicos, entes reguladores, tarifas",
                "descriptores_clave": ["servicio público", "ente regulador", "tarifa",
                                       "concesión"]
            }
        }
    },

    # ================================================================
    # 5. DERECHO TRIBUTARIO
    # ================================================================
    "tributario": {
        "id": "tributario",
        "nombre": "Derecho Tributario",
        "fuero_judicial": [
            "Contencioso Administrativo Federal (competencia tributaria)",
            "Tribunal Fiscal de la Nación",
            "Contencioso Administrativo y Tributario (CABA)"
        ],
        "materias_saij": [
            "TRIBUTARIO", "TRIBUTARIO-PROCESAL", "PROCESAL-TRIBUTARIO",
            "TRIBUTARIO-CONSTITUCIONAL", "CONSTITUCIONAL-TRIBUTARIO",
            "ADUANERO", "PROCESAL - TRIBUTARIO",
            "CONSTITUCIONAL - TRIBUTARIO", "ECONOMIA"
        ],
        "normativa_principal": [
            "Ley de Procedimiento Tributario (Ley 11.683)",
            "Código Aduanero (Ley 22.415)",
            "Ley de Impuesto a las Ganancias (Ley 20.628)",
            "Ley de IVA (Ley 23.349)",
            "Ley de Coparticipación Federal (Ley 23.548)",
            "Convenio Multilateral",
        ],
        "subramas": {
            "impositivo": {
                "nombre": "Derecho Impositivo",
                "descripcion": "Determinación de oficio, repetición, ejecución fiscal",
                "descriptores_clave": ["determinación de oficio", "repetición",
                                       "ejecución fiscal", "hecho imponible"]
            },
            "aduanero": {
                "nombre": "Derecho Aduanero",
                "descripcion": "Clasificación arancelaria, infracciones, derechos de importación/exportación",
                "descriptores_clave": ["clasificación arancelaria", "derechos de importación",
                                       "infracción aduanera", "zona franca"]
            }
        }
    },

    # ================================================================
    # 6. DERECHO CONSTITUCIONAL Y DERECHOS HUMANOS
    # ================================================================
    "constitucional": {
        "id": "constitucional",
        "nombre": "Derecho Constitucional y Derechos Humanos",
        "fuero_judicial": [
            "Todos los fueros (competencia transversal)",
            "Corte Suprema de Justicia de la Nación (competencia originaria)",
            "Corte Interamericana de Derechos Humanos (jurisdicción internacional)"
        ],
        "materias_saij": [
            "CONSTITUCIONAL", "CONSTITUCIONAL-PROCESAL",
            "CONSTITUCIONAL - PROCESAL", "PROCESAL-CONSTITUCIONAL",
            "PROCESAL - CONSTITUCIONAL", "PROCESAL CONSTITUCIONAL",
            "DERECHOS HUMANOS", "CONSTITUCIONAL-DERECHOS HUMANOS",
            "DERECHOS HUMANOS-PROCESAL", "DERECHOS HUMANOS-PENAL",
            "DERECHOS HUMANOS-CIVIL", "CONSTITUCIONAL-MEDIO AMBIENTE",
            "MEDIO AMBIENTE", "MEDIO AMBIENTE-PROCESAL",
            "CONSTITUCIONAL-EDUCACION", "CONSTITUCIONAL-ELECTORAL",
            "ELECTORAL", "POLITICO - ELECTORAL",
            "INTERNACIONAL PUBLICO", "CONSTITUCIONAL-INTERNACIONAL PUBLICO"
        ],
        "normativa_principal": [
            "Constitución Nacional Argentina",
            "Tratados internacionales con jerarquía constitucional (art. 75 inc. 22 CN)",
            "Convención Americana sobre Derechos Humanos (Pacto de San José)",
            "Pacto Internacional de Derechos Civiles y Políticos",
            "Pacto Internacional de Derechos Económicos, Sociales y Culturales",
            "Convención sobre los Derechos del Niño",
            "CEDAW",
            "Ley de Amparo (Ley 16.986)",
            "Ley de Hábeas Corpus (Ley 23.098)",
            "Ley de Hábeas Data (Ley 25.326)",
            "Ley de Acceso a la Información Pública (Ley 27.275)",
            "Ley General del Ambiente (Ley 25.675)",
        ],
        "subramas": {
            "garantias": {
                "nombre": "Garantías Constitucionales",
                "descripcion": "Amparo, hábeas corpus, hábeas data, medidas cautelares",
                "descriptores_clave": ["amparo", "hábeas corpus", "hábeas data",
                                       "acción declarativa de inconstitucionalidad",
                                       "medida cautelar", "per saltum"]
            },
            "derechos_fundamentales": {
                "nombre": "Derechos Fundamentales",
                "descripcion": "Libertad de expresión, igualdad, debido proceso, propiedad",
                "descriptores_clave": ["libertad de expresión", "igualdad",
                                       "debido proceso", "derecho de propiedad",
                                       "derecho a la salud", "derecho a la vivienda"]
            },
            "control_constitucionalidad": {
                "nombre": "Control de Constitucionalidad",
                "descripcion": "Declaración de inconstitucionalidad, control difuso y concentrado",
                "descriptores_clave": ["inconstitucionalidad", "control de constitucionalidad",
                                       "cuestión federal", "recurso extraordinario"]
            },
            "ddhh": {
                "nombre": "Derechos Humanos",
                "descripcion": "Derecho internacional de los DDHH, control de convencionalidad",
                "descriptores_clave": ["control de convencionalidad", "lesa humanidad",
                                       "desaparición forzada", "Corte IDH"]
            },
            "ambiental": {
                "nombre": "Derecho Ambiental",
                "descripcion": "Daño ambiental, principio precautorio, EIA",
                "descriptores_clave": ["daño ambiental", "principio precautorio",
                                       "evaluación de impacto ambiental", "recomposición"]
            },
            "electoral": {
                "nombre": "Derecho Electoral",
                "descripcion": "Procesos electorales, partidos políticos, financiamiento",
                "descriptores_clave": ["elecciones", "partido político", "boleta",
                                       "financiamiento de campaña"]
            }
        }
    },

    # ================================================================
    # 7. DERECHO PROCESAL (transversal)
    # ================================================================
    "procesal": {
        "id": "procesal",
        "nombre": "Derecho Procesal (transversal)",
        "fuero_judicial": [
            "Transversal a todos los fueros"
        ],
        "materias_saij": [
            "PROCESAL", "PROCESAL CIVIL", "PROCESAL PENAL",
            "PROCESAL LABORAL", "PROCESAL COMERCIAL",
            "PROCESAL CONSTITUCIONAL", "PROCESAL CIVIL - COMERCIAL"
        ],
        "normativa_principal": [
            "Código Procesal Civil y Comercial de la Nación (Ley 17.454)",
            "Código Procesal Penal de la Nación (Ley 23.984 / Ley 27.063)",
            "Ley de Procedimiento Laboral (Ley 18.345)",
            "Ley de Amparo (Ley 16.986)",
            "Ley de Mediación (Ley 26.589)",
        ],
        "subramas": {
            "civil_comercial": {
                "nombre": "Procesal Civil y Comercial",
                "descripcion": "Proceso ordinario, sumarísimo, ejecutivo, medidas cautelares",
                "descriptores_clave": ["demanda", "contestación", "prueba", "sentencia",
                                       "recurso de apelación", "medida cautelar",
                                       "ejecución de sentencia"]
            },
            "penal": {
                "nombre": "Procesal Penal",
                "descripcion": "Instrucción, juicio oral, recursos, ejecución penal",
                "descriptores_clave": ["instrucción", "juicio oral", "casación",
                                       "prisión preventiva", "excarcelación"]
            },
            "constitucional": {
                "nombre": "Procesal Constitucional",
                "descripcion": "Recurso extraordinario federal, amparo, hábeas corpus",
                "descriptores_clave": ["recurso extraordinario", "cuestión federal",
                                       "sentencia arbitraria", "gravedad institucional"]
            }
        }
    },
}


def normalizar_materia_saij(materia_saij: str) -> list[str]:
    """
    Dada una etiqueta de materia del dataset SAIJ (que puede ser compuesta,
    ej: "CONSTITUCIONAL-CIVIL-PROCESAL"), devuelve la(s) rama(s) principales
    a las que pertenece.
    """
    if not materia_saij or materia_saij == "N/A":
        return ["sin_clasificar"]

    materia_upper = materia_saij.upper().strip()

    # Mapa de tokens a ramas
    TOKEN_RAMA = {
        "CIVIL": "civil_comercial",
        "COMERCIAL": "civil_comercial",
        "BANCARIO": "civil_comercial",
        "NAVEGACION": "civil_comercial",
        "AERONAUTICO": "civil_comercial",
        "INTERNACIONAL PRIVADO": "civil_comercial",
        "PENAL": "penal",
        "CONTRAVENCIONAL": "penal",
        "LABORAL": "laboral",
        "SEGURIDAD SOCIAL": "laboral",
        "ADMINISTRATIVO": "administrativo",
        "TRIBUTARIO": "tributario",
        "ADUANERO": "tributario",
        "ECONOMIA": "tributario",
        "CONSTITUCIONAL": "constitucional",
        "DERECHOS HUMANOS": "constitucional",
        "MEDIO AMBIENTE": "constitucional",
        "ELECTORAL": "constitucional",
        "POLITICO": "constitucional",
        "EDUCACION": "constitucional",
        "INTERNACIONAL PUBLICO": "constitucional",
        "PROCESAL": "procesal",
    }

    ramas = set()

    # Primero buscar tokens multi-palabra (ej: "SEGURIDAD SOCIAL", "DERECHOS HUMANOS")
    for token, rama in sorted(TOKEN_RAMA.items(), key=lambda x: -len(x[0])):
        if token in materia_upper:
            ramas.add(rama)
            materia_upper = materia_upper.replace(token, "")

    # Si no se encontró nada, clasificar como sin_clasificar
    if not ramas:
        return ["sin_clasificar"]

    # Remover "procesal" si hay ramas sustantivas (procesal es transversal)
    if len(ramas) > 1 and "procesal" in ramas:
        ramas.discard("procesal")

    return sorted(ramas)


# ================================================================
# Estadísticas de distribución
# ================================================================
if __name__ == "__main__":
    import json
    from collections import Counter

    print("Normalizando materias del dataset SAIJ...")
    rama_count = Counter()
    sin_clasificar = Counter()

    with open(r"L:\JusticiaArgentina\datos\jurisprudencia_saij\dataset.jsonl",
              "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            materia = data.get("materia", "N/A")
            ramas = normalizar_materia_saij(materia)
            for r in ramas:
                rama_count[r] += 1
            if "sin_clasificar" in ramas and materia != "N/A":
                sin_clasificar[materia] += 1

    print("\n=== DISTRIBUCIÓN POR RAMA NORMALIZADA ===")
    total = sum(rama_count.values())
    for rama, count in rama_count.most_common():
        pct = count / total * 100
        nombre = RAMAS_DERECHO.get(rama, {}).get("nombre", rama)
        print(f"  {nombre:45s} {count:>8,}  ({pct:5.1f}%)")

    if sin_clasificar:
        print(f"\n=== MATERIAS NO CLASIFICADAS (top 20) ===")
        for m, c in sin_clasificar.most_common(20):
            print(f"  {m}: {c}")
