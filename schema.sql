-- JUSTICIA.ar - Sistema de Resolución Asistida
-- Base de datos para casos civiles de menor cuantía

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    rol TEXT NOT NULL CHECK(rol IN ('ciudadano', 'funcionario', 'administrador')),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de casos
CREATE TABLE IF NOT EXISTS casos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_expediente TEXT UNIQUE NOT NULL,
    tipo_caso TEXT NOT NULL CHECK(tipo_caso IN ('daños_perjuicios', 'incumplimiento_contractual', 'cobro_suma_dinero')),
    actor_id INTEGER NOT NULL,
    demandado_nombre TEXT NOT NULL,
    monto_reclamado REAL NOT NULL,
    descripcion_hechos TEXT NOT NULL,
    pruebas TEXT,
    nivel_clasificacion INTEGER CHECK(nivel_clasificacion BETWEEN 1 AND 4),
    estado TEXT NOT NULL DEFAULT 'ingresado' CHECK(estado IN ('ingresado', 'clasificado', 'en_revision', 'resuelto', 'apelado')),
    fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_resolucion TIMESTAMP,
    FOREIGN KEY (actor_id) REFERENCES usuarios(id)
);

-- Tabla de decisiones
CREATE TABLE IF NOT EXISTS decisiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caso_id INTEGER NOT NULL,
    tipo_decision TEXT NOT NULL CHECK(tipo_decision IN ('automatica', 'asistida', 'humana', 'deliberativa')),
    resultado TEXT NOT NULL CHECK(resultado IN ('acoge', 'rechaza', 'acoge_parcial')),
    monto_otorgado REAL,
    fundamentacion TEXT NOT NULL,
    funcionario_id INTEGER,
    confianza_ia REAL, -- 0.0 a 1.0
    fecha_decision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (caso_id) REFERENCES casos(id),
    FOREIGN KEY (funcionario_id) REFERENCES usuarios(id)
);

-- Tabla de artículos legales
CREATE TABLE IF NOT EXISTS articulos_legales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    numero_articulo TEXT NOT NULL,
    texto TEXT NOT NULL,
    categoria TEXT NOT NULL
);

-- Tabla de casos precedentes (jurisprudencia)
CREATE TABLE IF NOT EXISTS casos_precedentes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    tribunal TEXT NOT NULL,
    fecha_sentencia DATE NOT NULL,
    hechos_resumidos TEXT NOT NULL,
    decision TEXT NOT NULL,
    monto_aproximado REAL,
    tipo_caso TEXT NOT NULL,
    principios_aplicados TEXT NOT NULL
);

-- Tabla de clasificación (criterios)
CREATE TABLE IF NOT EXISTS criterios_clasificacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factor TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    peso INTEGER NOT NULL,
    nivel_minimo INTEGER NOT NULL
);

-- Tabla de auditoría
CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caso_id INTEGER NOT NULL,
    decision_id INTEGER,
    tipo_evento TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    usuario_id INTEGER,
    fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (caso_id) REFERENCES casos(id),
    FOREIGN KEY (decision_id) REFERENCES decisiones(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de métricas
CREATE TABLE IF NOT EXISTS metricas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    periodo TEXT NOT NULL,
    casos_nivel_1 INTEGER DEFAULT 0,
    casos_nivel_2 INTEGER DEFAULT 0,
    casos_nivel_3 INTEGER DEFAULT 0,
    casos_nivel_4 INTEGER DEFAULT 0,
    precision_ia REAL,
    tiempo_promedio_resolucion REAL,
    satisfaccion_usuarios REAL,
    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
