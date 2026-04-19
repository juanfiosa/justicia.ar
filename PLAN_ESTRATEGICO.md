# JUSTICIA ARGENTINA - Plan Estrategico
## Plataforma de Asistencia Judicial con IA para el Dictado de Sentencias

### Vision
Ofrecer a los jueces argentinos una plataforma que les asista en el dictado de
sentencias, aplicando derecho a casos concretos con una tasa de correccion igual
o superior a la de los jueces humanos. La plataforma genera sentencias completas
en formato "Vistos... Considerando... Resuelvo..." incluso para casos dificiles
y constitucionales.

### Arquitectura Conceptual

```
JUEZ                    PARTES                   PLATAFORMA
  |                       |                          |
  |-- Hechos probados --> |                          |
  |                       |-- Argumentos juridicos ->|
  |                       |   (demandante/acusacion) |
  |                       |-- Argumentos juridicos ->|
  |                       |   (demandado/defensa)    |
  |                                                  |
  |                       BASE DE CONOCIMIENTO       |
  |                       |-- Legislacion vigente    |
  |                       |-- Jurisprudencia         |
  |                       |-- Doctrina               |
  |                                                  |
  |<------------- SENTENCIA BORRADOR ---------------|
  |   (Vistos/Considerando/Resuelvo)                |
  |                                                  |
  |-- Aprueba/Modifica/Rechaza                      |
```

### Division por Fueros (ramas del derecho)

Siguiendo la organizacion actual del Poder Judicial argentino:

1. **Civil y Comercial** (obligaciones, contratos, danos, familia, sucesiones)
2. **Penal** (delitos del Codigo Penal y leyes especiales)
3. **Laboral** (relaciones de trabajo, accidentes, despidos)
4. **Contencioso Administrativo** (actos administrativos, responsabilidad del Estado)
5. **Constitucional** (control de constitucionalidad, amparo, habeas corpus)
6. **Federal** (competencia federal por materia, persona o lugar)
7. **Previsional** (jubilaciones, pensiones)

Cada fuero tendria su propio modulo especializado con legislacion, jurisprudencia
y criterios de decision propios.
