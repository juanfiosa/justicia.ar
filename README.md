# JUSTICIA.ar - Sistema de Resolución Asistida

Sistema experimental de adjudicación asistida por IA para casos civiles de menor cuantía en Córdoba, Argentina.

## 🎯 Características

- **Clasificación automática** de casos en 4 niveles de complejidad
- **Motor de decisión** que genera resoluciones basadas en legislación y precedentes
- **Interfaz web** intuitiva para gestión de casos
- **Base de conocimiento** con Código Civil y Comercial argentino
- **Auditoría completa** de todas las decisiones

## 🏗️ Arquitectura

### Modelo de 4 Niveles

1. **Nivel 1 - Rutinario**: Resolución automática por IA
2. **Nivel 2 - Complejo**: IA sugiere, humano revisa rápido
3. **Nivel 3 - Difícil**: Deliberación humana con asistencia IA
4. **Nivel 4 - Constitucional**: Deliberación ampliada

### Stack Tecnológico

- **Backend**: Python + Flask
- **Base de Datos**: SQLite
- **Frontend**: HTML5 + JavaScript vanilla
- **IA**: Algoritmos de clasificación y razonamiento basado en casos

## 📦 Instalación

### Requisitos

- Python 3.8+
- pip

### Pasos

1. **Instalar dependencias de Python**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Inicializar base de datos**:
```bash
cd backend
python init_db.py
```

Esto creará la base de datos `justicia.db` con:
- 9 artículos del Código Civil y Comercial
- 5 casos precedentes de ejemplo
- 5 usuarios de prueba
- Criterios de clasificación

3. **Iniciar servidor backend**:
```bash
cd backend
python app.py
```

El servidor estará disponible en `http://localhost:5000`

4. **Abrir frontend**:
Simplemente abre el archivo `frontend/index.html` en un navegador web moderno.

## 🚀 Uso del Sistema

### Ingresar un Nuevo Caso

1. Ve a la pestaña "Nuevo Caso"
2. Completa el formulario:
   - Tipo de caso (Daños, Incumplimiento, Cobro)
   - Nombre del demandado
   - Monto reclamado
   - Descripción de hechos
   - Pruebas disponibles
3. Envía el formulario
4. El sistema clasificará automáticamente el caso
5. Puedes generar la decisión haciendo clic en "Generar Decisión"

### Ver Lista de Casos

1. Ve a la pestaña "Lista de Casos"
2. Filtra por nivel si lo deseas
3. Visualiza todos los casos ingresados con su estado

### Estadísticas

Ve a la pestaña "Estadísticas" para ver:
- Total de casos por nivel
- Casos resueltos vs pendientes
- Distribución de casos

## 🧪 Ejemplos de Casos

### Caso Nivel 1 (Rutinario)
```
Tipo: Cobro de Suma de Dinero
Monto: $200,000
Descripción: Préstamo documentado en pagaré vencido hace 6 meses
Pruebas: Pagaré firmado y certificado notarialmente
```

### Caso Nivel 2 (Complejo)
```
Tipo: Daños y Perjuicios
Monto: $450,000
Descripción: Accidente de tránsito con versiones contradictorias sobre quién tenía prioridad
Pruebas: Testigos con versiones encontradas, necesita pericial
```

### Caso Nivel 3 (Difícil)
```
Tipo: Incumplimiento Contractual
Monto: $600,000
Descripción: Contrato de obra con cláusulas ambiguas. Disputas sobre interpretación contractual compleja
Pruebas: Contrato con cláusulas controvertidas, pericias técnicas contradictorias
```

## 📁 Estructura del Proyecto

```
justicia-ar/
├── backend/
│   ├── app.py                 # API Flask principal
│   ├── clasificador.py        # Motor de clasificación
│   ├── motor_decision.py      # Motor de decisión
│   ├── init_db.py            # Inicializador de BD
│   ├── requirements.txt       # Dependencias Python
│   └── justicia.db           # Base de datos (se crea)
├── database/
│   ├── schema.sql            # Esquema de BD
│   └── seed_data.sql         # Datos iniciales
├── frontend/
│   └── index.html            # Interfaz web
├── docs/
└── README.md
```

## 🔌 API Endpoints

### Casos
- `POST /api/casos` - Crear nuevo caso
- `GET /api/casos` - Listar casos
- `GET /api/casos/<id>` - Obtener caso específico
- `POST /api/casos/<id>/decidir` - Generar decisión

### Decisiones
- `POST /api/decisiones/<id>/aprobar` - Aprobar decisión (Nivel 2)

### Utilidades
- `GET /api/estadisticas` - Estadísticas del sistema
- `GET /api/articulos` - Artículos legales
- `GET /api/precedentes` - Casos precedentes
- `GET /api/health` - Health check

## 📊 Base de Conocimiento

### Legislación Incluida

- **Art. 1716 CCyC**: Deber de reparar
- **Art. 1737 CCyC**: Concepto de daño
- **Art. 1740 CCyC**: Reparación plena
- **Art. 1757 CCyC**: Responsabilidad objetiva
- **Art. 730 CCyC**: Efectos del incumplimiento
- **Art. 1083 CCyC**: Resolución por incumplimiento
- Y más...

### Casos Precedentes

El sistema incluye 5 casos precedentes simulados pero realistas de:
- Accidentes de tránsito
- Incumplimientos contractuales
- Cobros de sumas de dinero
- Daños a la propiedad

## ⚠️ Advertencias

- **Este es un prototipo experimental** con fines académicos y de investigación
- **NO tiene valor legal vinculante**
- **NO sustituye el asesoramiento legal profesional**
- Los datos son ficticios y con fines demostrativos

## 🔬 Lógica de Clasificación

El clasificador asigna puntos según:

**Factores que bajan el nivel (rutinario)**:
- Monto bajo (< $300,000): +2 puntos
- Prueba documental clara: +3 puntos
- Sin contestación: +3 puntos
- Cobro ejecutivo con título: +3 puntos

**Factores que suben el nivel (complejo)**:
- Necesidad de pericial: -2 puntos
- Hechos controvertidos: -2 puntos
- Cuestión jurídica novedosa: -3 puntos
- Cuestión constitucional: -4 puntos (Nivel 4 forzado)

**Resultado**:
- 6+ puntos → Nivel 1
- 2-5 puntos → Nivel 2
- -2 a 1 puntos → Nivel 3
- < -2 puntos → Nivel 4

## 🎓 Contexto Académico

Este prototipo fue desarrollado como demostración del paper "A favor del gobierno de las máquinas" 
que explora el futuro de la adjudicación asistida por IA en sistemas jurídicos.

## 📝 Licencia

Este proyecto es de código abierto con fines educativos y de investigación.

## 👥 Contacto

Para consultas sobre el proyecto, contactar a Juan Iosa (CIJS/IDEJUS-CONICET-UNC).

---

**Versión**: 0.1.0
**Última actualización**: Febrero 2025
