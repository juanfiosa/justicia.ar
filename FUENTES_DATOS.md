# Fuentes de Datos Disponibles para JusticiaArgentina

## YA DESCARGADOS (en L:\JusticiaArgentina\datos\)

### 1. InfoLeg - Normativa Nacional
- **Archivo:** datos/infoleg/base-infoleg-normativa-nacional.csv
- **Registros:** 422,416 normas
- **Contenido:** Leyes, decretos, resoluciones, decisiones administrativas, disposiciones, acordadas
- **Periodo:** Desde mayo 1997 + normativa referenciada anterior
- **Campos:** id_norma, tipo_norma, numero_norma, clase_norma, organismo_origen, fecha_sancion,
  titulo_resumido, titulo_sumario, texto_resumido, texto_original (URL), texto_actualizado (URL),
  modificada_por, modifica_a
- **Fuente:** https://datos.jus.gob.ar/dataset/base-de-datos-legislativos-infoleg
- **Licencia:** Creative Commons Attribution 4.0
- **Actualizacion:** Mensual

### 2. SAIJ - Normativa Provincial
- **Archivo:** datos/saij_normativa_provincial.csv
- **Registros:** 80,985 normas provinciales
- **Contenido:** Constituciones provinciales, leyes, decretos, codigos provinciales
- **Campos:** provincia_nombre, tipo_norma, numero_norma, estado_vigencia, fecha,
  nombre_norma, titulo_resumido, titulo_sumario, texto_actualizado (URL SAIJ)
- **Fuente:** https://datos.jus.gob.ar/dataset/base-saij-de-normativa-provincial
- **Licencia:** Creative Commons Attribution 4.0

### 3. TSJ CABA - Sentencias del Tribunal Superior de Justicia de Buenos Aires
- **Archivos:** datos/sentencias_tsjcaba/sentencias-2023.csv a 2026.csv
- **Registros:** ~6,100 sentencias (2023-2026)
- **Campos:** tipo_resolucion, fecha, secretaria_tramite, objeto_procesal,
  juez_tramite, inicio_expediente, numero_registro, resolutivo, acumulado
- **Fuente:** https://datos.tsjbaires.gob.ar/dataset/sentencias
- **Nota:** Metadata de sentencias, NO texto completo

## DISPONIBLE PARA DESCARGAR

### 4. Jurisprudencia SAIJ en Hugging Face (CLAVE!)
- **URL:** https://huggingface.co/datasets/marianbasti/jurisprudencia-Argentina-SAIJ
- **Registros:** Entre 100,000 y 1,000,000 de sentencias
- **Contenido:** Sumarios y texto completo de sentencias de TODO el pais
- **Campos incluye:** caratula, sumario, TEXTO COMPLETO, tribunal, materia,
  magistrados, actor, demandado, descriptores, referencias-normativas, jurisdiccion
- **Tribunales:** CSJN, Camaras Nacionales, Juzgados Federales, tribunales provinciales
- **Licencia:** Apache 2.0
- **IMPORTANCIA:** Esta es la fuente mas valiosa. Contiene TEXTO COMPLETO de sentencias
  con metadata rica (materia, normas citadas, descriptores tematicos)

### 5. Tesauro SAIJ
- **URL:** https://datos.jus.gob.ar/dataset/tesauro-saij-de-derecho-argentino
- **Formato:** RDF
- **Contenido:** 6000+ voces juridicas organizadas jerarquicamente
- **Utilidad:** Clasificacion tematica, mapeo de conceptos juridicos

### 6. Sentencias TSJ CABA historicas (2016-2022)
- Disponibles en el mismo portal, mismos campos

## NO DISPONIBLE EN DATOS ABIERTOS (requiere scraping o acuerdo)

### 7. Texto completo de normas de InfoLeg
- El CSV solo tiene URLs (campo texto_original, texto_actualizado)
- El texto completo esta en servicios.infoleg.gob.ar, requiere acceder a cada URL
- Posible estrategia: scraping respetuoso de las ~30,000 leyes mas relevantes

### 8. Fallos completos de la CSJN
- cij.gov.ar tiene fallos de la Corte
- No hay dataset abierto; requiere scraping o API

### 9. Jurisprudencia de Camaras Nacionales
- pjn.gov.ar tiene buscador
- No hay dataset abierto

## ESTRATEGIA RECOMENDADA

**Paso 1 (inmediato):** Descargar el dataset de Hugging Face (jurisprudencia SAIJ)
**Paso 2:** Usar InfoLeg CSV como indice + scraping selectivo del texto de leyes clave
**Paso 3:** Combinar con normativa provincial SAIJ
**Paso 4:** Enriquecer con el Tesauro para clasificacion tematica
