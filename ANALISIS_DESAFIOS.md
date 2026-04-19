# Analisis de Desafios para la Plataforma JusticiaArgentina

## 1. Sobre el paper de Dupoux, LeCun y Malik

El argumento central de Dupoux et al. (2026) es que los sistemas de IA actuales
"una vez desplegados, no aprenden esencialmente nada" (p. 2). Su critica apunta
al problema del **domain mismatch**: los sistemas entrenados sobre datos fijos
de internet, al enfrentarse a datos nuevos que divergen significativamente de
esa distribucion, producen consecuencias impredecibles. Y esto "no puede
arreglarse meramente aumentando el tamano del set de entrenamiento, porque los
datos de la vida real siempre contienen casos nuevos, no vistos (heavy tailed)
y siguen cambiando en el tiempo (non-stationarity)".

### Conexion con la derrotabilidad juridica

El usuario conecta esto con el problema de la **derrotabilidad** (defeasibility)
en el ambito juridico-moral. La conexion es pertinente pero requiere matices:

**El argumento de Dupoux trasladado al derecho seria:** un sistema de IA
entrenado sobre legislacion y jurisprudencia existente no podria manejar
adecuadamente los casos genuinamente nuevos - aquellos donde una propiedad
axiologica relevante no fue prevista por el legislador ni por jueces anteriores.
Asi como un nino aprende adaptativamente y un LLM no, un juez humano puede
"ver" que una norma no deberia aplicarse a un caso que satisface sus condiciones
de aplicacion pero tiene una propiedad moralmente relevante no prevista, mientras
que un sistema de IA aplicaria mecanicamente la norma.

### Mi evaluacion honesta

**Dupoux tiene razon en un punto fundamental:** los LLMs actuales (yo incluido)
no tenemos aprendizaje autonomo post-deployment. No puedo "aprender" del caso
que acabo de resolver para mejorar en el siguiente. Cada interaccion parte de
mis parametros congelados.

**Sin embargo, hay que distinguir dos problemas:**

1. **Casos nuevos pero decidibles con principios existentes.** La mayoria de los
   casos de "derrotabilidad" juridica no requieren inventar principios morales
   nuevos, sino aplicar principios constitucionales de nivel superior (dignidad
   humana, razonabilidad, proporcionalidad) a situaciones no previstas. Para esto,
   un LLM con acceso a la estructura completa del ordenamiento juridico puede
   ser razonablemente competente. Ejemplo: aplicar el derecho a la intimidad
   (ya existente) a tecnologias de reconocimiento facial (nuevas).

2. **Casos genuinamente revolucionarios** donde ni siquiera los principios
   existentes ofrecen orientacion clara. Estos son los que Dupoux correctamente
   senala como problematicos. Son tambien los que dividen a la Corte Suprema
   en votaciones 3-2 o 4-3. Aqui la IA seria menos confiable, pero tambien
   lo son los jueces humanos - de ahi que haya votos disidentes.

**La clave pragmatica:** no se trata de que la IA reemplace el juicio moral
del juez, sino de que lo asista. En los casos de derrotabilidad genuina, la
plataforma deberia:
- Identificar explicitamente que el caso tiene propiedades no previstas
- Presentar los argumentos de ambas partes
- Ofrecer una decision *con su fundamentacion*, pero marcada como de alta
  incertidumbre
- Dejar la decision final siempre al juez humano

## 2. Sobre la base de datos de legislacion y jurisprudencia

**Si, es absolutamente necesaria.** Aunque yo (Claude) tengo conocimiento
general del derecho argentino por mi entrenamiento, este conocimiento es:

- **Incompleto:** no conozco todas las leyes ni todas las sentencias
- **Desactualizado:** mi corte de conocimiento es mayo 2025; las leyes cambian
- **No verificable:** no puedo citar con precision numeros de articulo, fechas
  exactas de sentencias, o textos legales palabra por palabra
- **No autoritativo:** para una sentencia judicial, se necesita citar la fuente
  exacta, no una parafrasis

### Lo que necesitariamos:

1. **Legislacion nacional:**
   - Constitucion Nacional (texto actualizado)
   - Codigos: Civil y Comercial, Penal, Procesal Civil, Procesal Penal, Laboral
   - Leyes especiales vigentes (InfoLeg como fuente)
   - Decretos reglamentarios relevantes

2. **Legislacion provincial** (al menos para las jurisdicciones objetivo)

3. **Jurisprudencia:**
   - Fallos de la CSJN (base completa, idealmente con texto completo)
   - Camaras Nacionales y Federales
   - Tribunales Superiores provinciales
   - Con metadata: fecha, tribunal, materia, voces, resultado

4. **Doctrina** (opcional pero util para fundamentacion)

### Fuentes posibles:
- **InfoLeg** (infoleg.gob.ar): legislacion nacional
- **SAIJ** (saij.gob.ar): Sistema Argentino de Informacion Juridica
- **CIJ** (cij.gov.ar): Centro de Informacion Judicial
- **Bases de datos privadas:** La Ley, El Derecho, Abeledo Perrot

## 3. Sobre la distincion quaestio facti / quaestio iuris

La distincion es excelente y hace el problema mucho mas manejable:

**Quaestio facti (que NO hace la plataforma):**
- Valorar pruebas testimoniales, documentales, periciales
- Determinar la credibilidad de los testigos
- Establecer los hechos probados
- Todo lo relativo a la inmediacion (ver y oir a las partes)

**Quaestio iuris (que SI hace la plataforma):**
- Dado un conjunto de hechos probados que el juez carga...
- ...y dados los argumentos juridicos de las partes...
- ...determinar que normas son aplicables
- ...interpretar esas normas
- ...resolver conflictos normativos
- ...aplicar el derecho a los hechos y generar la sentencia

### Ventaja de este enfoque:
La valoracion de la prueba es el aspecto mas "humano" y menos formalizable de
la actividad jurisdiccional. Al excluirla, nos concentramos en donde la IA
puede realmente aportar: el procesamiento sistematico de un ordenamiento
juridico enorme y complejo.

### Flujo propuesto:

```
1. El JUEZ carga: hechos probados (narrativa + lista estructurada)
2. El DEMANDANTE carga: su vision del derecho aplicable (normas, jurisprudencia,
   doctrina que invoca, como se aplican al caso)
3. El DEMANDADO carga: su vision del derecho aplicable (idem)
4. La PLATAFORMA:
   a. Identifica las normas potencialmente aplicables
   b. Analiza los argumentos de ambas partes
   c. Busca jurisprudencia relevante (precedentes)
   d. Identifica problemas interpretativos (vaguedad, ambiguedad, lagunas,
      contradicciones, derrotabilidad)
   e. Genera la sentencia en formato Vistos/Considerando/Resuelvo
   f. Marca el nivel de confianza y los puntos de mayor incertidumbre
5. El JUEZ revisa, modifica si corresponde, y firma
```

## 4. Los desafios de la concepcion mecanicista de la jurisdiccion

### 4.1 Indeterminaciones linguisticas

**Vaguedad:** "plazo razonable", "buen padre de familia", "orden publico",
"graves injurias". El derecho esta plagado de conceptos vagos.

*Estrategia de la plataforma:*
- Construir un repositorio de como los tribunales han interpretado cada concepto
  vago en casos concretos
- Para cada concepto vago, ofrecer el rango de interpretaciones jurisprudenciales
- Identificar en que punto del espectro cae el caso concreto
- Hacer explicito cuando se esta en la "zona de penumbra" hartiana

**Ambiguedad:** cuando una norma admite dos o mas significados (ambiguedad
semantica, sintactica o pragmatica).

*Estrategia:*
- Aplicar canones de interpretacion (literal, sistematico, teleologico, historico)
- Mostrar que resultado arroja cada canon
- Si los canones convergen: alta confianza
- Si divergen: exponer la divergencia y fundamentar la eleccion

### 4.2 Problemas sistemicos

**Lagunas normativas:** casos no regulados por ninguna norma del sistema.

*Estrategia:*
- Aplicar los mecanismos que el propio ordenamiento preve: analogia (art. 2 CCCN),
  principios generales del derecho, principios de los derechos humanos
- Buscar como se han resuelto casos analogos
- Hacer explicito que se esta integrando una laguna

**Contradicciones (antinomias):** dos normas que regulan el mismo caso de modo
incompatible.

*Estrategia:*
- Aplicar los criterios clasicos de resolucion: jerarquico (lex superior),
  cronologico (lex posterior), de especialidad (lex specialis)
- Cuando estos criterios no resuelven la antinomia, aplicar ponderacion
  (principio de proporcionalidad)
- Hacer explicito el conflicto y el criterio de resolucion elegido

### 4.3 Derrotabilidad

Este es el desafio mas profundo. Un caso de derrotabilidad puro: la norma N
regula el caso C; C tiene todas las propiedades previstas por N; pero C tiene
ademas una propiedad P no prevista por el legislador que hace que aplicar N
a C produzca un resultado axiologicamente inaceptable.

*Ejemplo clasico:* "Riggs v. Palmer" (1889) - el heredero que asesina al
testador para heredar. La ley de sucesiones no preveia esta situacion.

*Ejemplo moderno:* algoritmos de reconocimiento facial usados como prueba en
un proceso penal - la normativa procesal habla de "pericias" pero no contempla
este tipo de tecnologia con sus sesgos raciales documentados.

*Estrategia de la plataforma:*

1. **Deteccion:** El sistema deberia poder detectar indicios de derrotabilidad:
   - El resultado literal de aplicar la norma entra en tension con principios
     constitucionales
   - Las partes invocan principios en tension con la regla aplicable
   - No hay precedentes para el caso especifico
   - El caso involucra tecnologias o situaciones sociales nuevas

2. **Senalizacion:** Marcar explicitamente: "Este caso presenta indicios de
   derrotabilidad. El resultado de la aplicacion literal de [norma] es [X],
   pero esto podria entrar en tension con [principio constitucional/valor]
   porque [razon]."

3. **Argumentacion:** Presentar ambos caminos:
   - Camino A: aplicar la norma tal cual (con fundamentacion)
   - Camino B: exceptuar la norma invocando el principio superior (con
     fundamentacion)

4. **Recomendacion con incertidumbre:** Ofrecer una decision, pero con un
   indicador explicito de que la confianza del sistema es baja y que el caso
   requiere especial atencion judicial.

**Mi opinion sobre la critica de Dupoux aplicada a esto:**

Dupoux tiene razon en que un sistema entrenado sobre datos fijos no puede
"ver" lo que nunca vio. Pero la derrotabilidad juridica tiene una ventaja
sobre la derrotabilidad moral pura: **el derecho tiene una estructura
jerarquica explicita** (Constitucion > leyes > decretos) y **principios
de nivel superior expresamente formulados** (dignidad humana, razonabilidad,
igualdad, proporcionalidad). Cuando una regla produce un resultado
inaceptable, generalmente es porque viola un principio de nivel superior
*que ya esta en el sistema*. No se trata de inventar valores morales nuevos
(que es donde la IA falla segun Dupoux), sino de aplicar principios
preexistentes a situaciones nuevas.

Dicho esto, habra casos limite - los verdaderamente revolucionarios - donde
la plataforma debera ser honesta sobre sus limitaciones y ceder
explicitamente la decision al juez humano.

## 5. Otros desafios que identifico

### 5.1 Problema de la fundamentacion y la transparencia
Una sentencia judicial no solo debe ser correcta sino que debe estar
**fundamentada**. La IA debe poder explicar *por que* llega a cada conclusion.
No alcanza con un resultado; el "Considerando" es tan importante como el
"Resuelvo". Esto requiere razonamiento explicable (no caja negra).

### 5.2 Problema de los sesgos
Los datos de entrenamiento (jurisprudencia historica) contienen sesgos
historicos. Si los tribunales históricamente discriminaron (ej: genero,
raza, clase social), la IA podria replicar esos sesgos. Se necesitan
mecanismos de deteccion y correccion de sesgos.

### 5.3 Problema del cambio jurisprudencial
El derecho vivo cambia: la Corte Suprema puede cambiar un criterio
jurisprudencial. La plataforma necesita actualizacion continua y la
capacidad de distinguir jurisprudencia vigente de jurisprudencia superada.

### 5.4 Problema de la legitimidad democratica
Un juez que firma una sentencia generada por IA: es realmente "su"
sentencia? Hay un problema filosofico-politico sobre la legitimidad de la
decision judicial delegada (parcialmente) a un algoritmo. La plataforma
debe posicionarse claramente como **herramienta de asistencia**, no como
decisor autonomo.

### 5.5 Problema de la motivacion en lenguaje judicial
Las sentencias argentinas tienen un estilo discursivo particular, con
formulas rituales, citas doctrinarias, y un modo argumentativo especifico.
La plataforma debe generar texto que sea indistinguible del que escribiria
un juez experimentado.

### 5.6 Problema de la cuantificacion del dano
En casos civiles (danos y perjuicios), determinar el monto de la
indemnizacion es uno de los problemas mas dificiles. Requiere analisis
de precedentes, tablas de incapacidad, criterios jurisprudenciales,
y un juicio de razonabilidad. Aqui la IA podria ser especialmente util
si tiene acceso a una base de datos de montos otorgados en casos similares.

### 5.7 Problema del secreto y la privacidad
Los datos de casos judiciales contienen informacion sensible. La plataforma
debe cumplir con la Ley de Proteccion de Datos Personales (25.326) y
garantizar que los datos no se filtren ni se usen para entrenar modelos.

## 6. Pasos concretos propuestos

### Fase 1: Prototipo acotado (3-6 meses)
- Elegir UN fuero y UN tipo de caso (ej: civil, danos y perjuicios menores)
- Construir la base de datos: legislacion relevante + 500 sentencias modelo
- Desarrollar el motor de razonamiento juridico para ese tipo de caso
- Generar sentencias y compararlas con las reales
- Medir tasa de correccion contra panel de jueces

### Fase 2: Expansion del prototipo (6-12 meses)
- Ampliar a mas tipos de casos dentro del fuero elegido
- Incorporar los argumentos de las partes como input
- Mejorar la deteccion de problemas interpretativos
- Agregar la base de jurisprudencia completa

### Fase 3: Multifuero (12-24 meses)
- Expandir a otros fueros (laboral, penal, administrativo)
- Desarrollar modulos especializados por materia
- Incorporar control de constitucionalidad

### Fase 4: Casos constitucionales y dificiles (24+ meses)
- Abordar los casos de nivel 4 (tension constitucional)
- Desarrollar el modulo de deteccion de derrotabilidad
- Implementar razonamiento por principios
- Validacion con tribunales superiores
