# JUSTICIA ARGENTINA - Arquitectura RAG

## Flujo del sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        ENTRADA DEL JUEZ                         │
│                                                                 │
│  1. Hechos probados (quaestio facti - fijados por el juez)     │
│  2. Valoración de la prueba (síntesis)                         │
│  3. Cuestiones a resolver                                      │
│                                                                 │
│  + PARTES PROCESALES (actor y demandado / acusación y defensa) │
│    - Pretensión                                                │
│    - Fundamentos jurídicos (normas invocadas)                  │
│    - Argumentos                                                │
│    - Jurisprudencia citada                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   1. CLASIFICACIÓN Y ANÁLISIS                   │
│                                                                 │
│  - Rama del derecho (civil, penal, laboral, etc.)              │
│  - Subrama (obligaciones, familia, penal económico, etc.)      │
│  - Nivel de complejidad (1-4)                                  │
│  - Detección de problemas:                                     │
│    □ Vaguedad normativa                                        │
│    □ Laguna                                                    │
│    □ Contradicción normativa                                   │
│    □ Derrotabilidad (caso no previsto)                         │
│  - Cuestiones jurídicas a resolver                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              2. RETRIEVAL (Recuperación multi-etapa)            │
│                                                                 │
│  Capa 1: Normas del cuerpo legal principal de la rama          │
│          (CCyCN para civil, CP para penal, LCT para laboral)   │
│                ↓                                                │
│  Capa 2: Búsqueda semántica de precedentes similares           │
│          (por hechos + cuestiones jurídicas)                   │
│                ↓                                                │
│  Capa 3: Verificación de normas citadas por las partes         │
│          (ampliar con normas conexas)                          │
│                ↓                                                │
│  Capa 4: [Si Nivel 3-4] Doctrina constitucional               │
│          (CSJN + Corte IDH + tratados DDHH)                   │
│                ↓                                                │
│  Capa 5: Cross-reference                                       │
│          (normas citadas en precedentes encontrados)           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Vector Store │  │ Vector Store │  │ Vector Store         │  │
│  │ LEGISLACIÓN  │  │JURISPRUDENCIA│  │ DOCTRINA CONST.      │  │
│  │ (por rama)   │  │ (por rama)   │  │ (CSJN + Corte IDH)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    3. GENERACIÓN (LLM)                          │
│                                                                 │
│  Prompt contextualizado por:                                   │
│  - Rama del derecho → estilo argumentativo específico          │
│  - Nivel de complejidad → estrategia de razonamiento           │
│  - Tipo de proceso → formato y requisitos procesales           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Nivel 1-2: Subsunción clásica                           │   │
│  │   Norma (premisa mayor) + Hechos (premisa menor)        │   │
│  │   → Conclusión jurídica                                 │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Nivel 3: Interpretación + Integración                   │   │
│  │   Interpretaciones posibles → Elección fundamentada     │   │
│  │   Laguna → Analogía / Principios generales              │   │
│  │   Contradicción → Jerarquía / Especialidad / Temporalidad│  │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Nivel 4: Ponderación de principios                      │   │
│  │   Principios en tensión → Test de proporcionalidad      │   │
│  │   (Alexy): idoneidad, necesidad, proporcionalidad e.e.  │   │
│  │   → Prevalencia justificada en el caso concreto         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  SALIDA: Sentencia en formato                                  │
│          VISTOS... CONSIDERANDO... RESUELVO...                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     4. VERIFICACIÓN                             │
│                                                                 │
│  ✓ Normas citadas existen y están vigentes                     │
│  ✓ Precedentes citados existen en la base                      │
│  ✓ Citas textuales coinciden con texto oficial                 │
│  ✓ Congruencia: se resolvió todo lo pedido                     │
│  ✓ Coherencia interna de la argumentación                      │
│  ✓ Consistencia de montos/condenas con fundamentos             │
│                                                                 │
│  Si hay errores → Ciclo de corrección automática               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  5. PRESENTACIÓN AL JUEZ                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              PROYECTO DE SENTENCIA                       │   │
│  │                                                         │   │
│  │  VISTOS: [carátula, trámite procesal]                   │   │
│  │                                                         │   │
│  │  CONSIDERANDO:                                          │   │
│  │  I. La cuestión a resolver                              │   │
│  │  II. Marco normativo aplicable                          │   │
│  │  III. Hechos relevantes                                 │   │
│  │  IV-V. Análisis de pretensiones                         │   │
│  │  VI. Aplicación del derecho                             │   │
│  │  VII. [Ponderación constitucional si aplica]            │   │
│  │  VIII. Costas                                           │   │
│  │                                                         │   │
│  │  RESUELVO:                                              │   │
│  │  1) Hacer lugar / rechazar la demanda...                │   │
│  │  2) Costas...                                           │   │
│  │  3) Regular honorarios...                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  + Panel lateral:                                              │
│    - Nivel de confianza del sistema                            │
│    - Advertencias y notas para el juez                         │
│    - Fuentes normativas y jurisprudenciales (verificadas)      │
│    - [Nivel 3-4] Alternativas descartadas y por qué           │
│    - Botón: "Editar sentencia" / "Aprobar" / "Rechazar"       │
└─────────────────────────────────────────────────────────────────┘
```

## Ramas del derecho → Fueros judiciales

```
RAMA                              FUEROS JUDICIALES ARGENTINOS          VOLUMEN SAIJ
─────────────────────────────────────────────────────────────────────────────────────
Civil y Comercial                 Civil / Comercial / CyC Federal       165,458 (18%)
Penal                             Criminal / Penal Económico / TOC       92,049 (10%)
Laboral y Seg. Social             Trabajo / Seg. Social Federal          69,510  (8%)
Constitucional y DDHH             Transversal / CSJN originaria          68,898  (8%)
Procesal (transversal)            Todos los fueros                       65,183  (7%)
Administrativo                    Cont. Admin. Federal / Provincial      49,087  (5%)
Tributario                        Tribunal Fiscal / CAF                   9,550  (1%)
Sin clasificar                    —                                     391,351 (43%)
```

## Bases de datos necesarias

| Base | Fuente | Estado | Uso |
|------|--------|--------|-----|
| Jurisprudencia (sumarios) | SAIJ / HuggingFace | ✅ 873,656 registros | Precedentes, doctrina |
| Jurisprudencia (completa) | SAIJ API / CIJ | ⏳ Por conseguir | Sentencias íntegras |
| Legislación vigente | InfoLeg | ⏳ Juan la está consiguiendo | Normas aplicables |
| Doctrina CSJN | CSJN / CIJ | ⏳ Por conseguir | Casos Nivel 3-4 |
| Tratados DDHH | ONU / OEA | ⏳ Por indexar | Casos Nivel 4 |

## Stack tecnológico propuesto

- **LLM**: Claude (Anthropic) - generación de sentencias y análisis
- **Embeddings**: text-embedding-3-large (o modelo local)
- **Vector Store**: ChromaDB (local/prototipo) → Pinecone/Weaviate (producción)
- **Base relacional**: PostgreSQL (metadata, usuarios, auditoría)
- **Backend**: Python + FastAPI
- **Frontend**: React/Next.js
- **Indexación**: Pipeline de ingesta con chunking por artículo/sumario
