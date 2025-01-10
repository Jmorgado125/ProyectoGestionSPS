-- Tabla: Usuarios
-- Contiene la información de los usuarios que tienen acceso al sistema.
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT NOT NULL PRIMARY KEY, -- Identificador único del usuario.
    username VARCHAR(50) NOT NULL,      -- Nombre de usuario único.
    password VARCHAR(100) NOT NULL,    -- Contraseña del usuario.
    nombre VARCHAR(100) NOT NULL,      -- Nombre del usuario.
    rol ENUM('admin', 'instructor', 'alumno') NOT NULL -- Rol del usuario.
);

-- Tabla: Alumnos
-- Contiene la información personal de los alumnos registrados.
CREATE TABLE IF NOT EXISTS alumnos (
    rut VARCHAR(10) NOT NULL PRIMARY KEY, -- Identificador único del alumno (formato de RUT).
    nombre VARCHAR(100) NOT NULL,          -- Nombre del alumno.
    apellido VARCHAR(100) NOT NULL,        -- Apellido del alumno.
    correo VARCHAR(100),                   -- Correo electrónico del alumno (opcional).
    telefono BIGINT,                       -- Número de teléfono del alumno (opcional).
    profesion VARCHAR(100),                -- Profesión del alumno (opcional).
    direccion VARCHAR(255),                -- Dirección residencial del alumno (opcional).
    comuna VARCHAR(100),                   -- Comuna de residencia del alumno (opcional).
    ciudad VARCHAR(100)                    -- Ciudad de residencia del alumno (opcional).
);

-- Tabla: Cursos
-- Define los cursos ofrecidos, incluyendo su descripción, modalidad y códigos asociados.
CREATE TABLE IF NOT EXISTS cursos (
    id_curso VARCHAR(20) NOT NULL PRIMARY KEY, -- Identificador único del curso.
    nombre_curso VARCHAR(255) NOT NULL,         -- Nombre del curso.
    modalidad ENUM('presencial', 'online', 'mixto') NOT NULL, -- Modalidad del curso.
    codigo_sence INT,                          -- Código SENCE del curso (opcional).
    codigo_elearning INT,                      -- Código de plataforma e-learning del curso (opcional).
    horas_cronologicas INT NOT NULL DEFAULT 0, -- Cantidad de horas cronológicas del curso.
    horas_pedagogicas FLOAT DEFAULT 0.0        -- Cantidad de horas pedagógicas del curso.
);

-- Tabla: Empresa
-- Contiene información sobre las empresas relacionadas.
CREATE TABLE IF NOT EXISTS empresa (
    id_empresa VARCHAR(255) NOT NULL PRIMARY KEY, -- Identificador único basado en el nombre de la empresa.
    rut_empresa VARCHAR(20) NOT NULL UNIQUE,     -- RUT único de la empresa.
    direccion_empresa VARCHAR(255)               -- Dirección de la empresa.
);

-- Tabla: Empresa Contactos
-- Permite almacenar múltiples contactos para una misma empresa.
CREATE TABLE IF NOT EXISTS empresa_contactos (
    id_contacto INT NOT NULL AUTO_INCREMENT PRIMARY KEY, -- Identificador único del contacto.
    id_empresa VARCHAR(255) NOT NULL,                   -- Relación con la tabla `empresa`.
    nombre_contacto VARCHAR(255) NOT NULL,              -- Nombre del contacto.
    rol_contacto VARCHAR(255),                          -- Rol del contacto (opcional).
    correo_contacto VARCHAR(255),                       -- Correo electrónico del contacto (opcional).
    telefono_contacto BIGINT,                           -- Número de contacto (opcional).
    FOREIGN KEY (id_empresa) REFERENCES empresa(id_empresa) -- Relación con `empresa`.
);

-- Tabla: Inscripciones
-- Contiene información sobre las inscripciones de alumnos a cursos.
CREATE TABLE IF NOT EXISTS inscripciones (
    id_inscripcion INT NOT NULL PRIMARY KEY,   -- Identificador único de la inscripción.
    id_alumno VARCHAR(10),                     -- Identificador del alumno inscrito (relación con `alumnos`).
    id_curso VARCHAR(20) NOT NULL,             -- Identificador del curso inscrito (relación con `cursos`).
    fecha_inscripcion DATE NOT NULL,           -- Fecha en que se realizó la inscripción.
    fecha_termino_condicional DATE,            -- Fecha condicional de término de inscripción (opcional).
    anio_inscripcion YEAR NOT NULL,            -- Año en que se realizó la inscripción.
    metodo_llegada ENUM('particular', 'empresa') NOT NULL, -- Método de llegada del alumno.
    id_empresa VARCHAR(255),                   -- Identificador de la empresa asociada (relación con `empresa`).
    ordenSence INT,                            -- Número de orden SENCE asociado.
    idfolio INT,                               -- Identificador de folio asociado.
    numero_acta VARCHAR(20) NOT NULL,          -- Número del acta de inscripción.
    FOREIGN KEY (id_alumno) REFERENCES alumnos(rut), -- Relación con la tabla `alumnos`.
    FOREIGN KEY (id_curso) REFERENCES cursos(id_curso), -- Relación con la tabla `cursos`.
    FOREIGN KEY (id_empresa) REFERENCES empresa(id_empresa) -- Relación con la tabla `empresa`.
);

-- Tabla: Pagos
-- Contiene la información de los pagos realizados por los alumnos o empresas.
-- Tabla PAGOS (cabecera)
CREATE TABLE IF NOT EXISTS pagos (
    id_pago           INT AUTO_INCREMENT PRIMARY KEY,
    id_inscripcion    INT NOT NULL,
    tipo_pago         ENUM('contado', 'pagare') NOT NULL,
    modalidad_pago    ENUM('completo', 'diferido') NOT NULL,
    fecha_inscripcion DATETIME NOT NULL,
    fecha_final       DATETIME NULL,
    num_cuotas        TINYINT NOT NULL DEFAULT 1,
    valor_total       DECIMAL(10,2) NOT NULL,
    estado            ENUM('pendiente', 'pagado', 'cancelado') NOT NULL DEFAULT 'pendiente',
    CONSTRAINT fk_pagos_inscripciones
        FOREIGN KEY (id_inscripcion) 
        REFERENCES inscripciones (id_inscripcion)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- Tabla CUOTAS (detalle de pagos)
CREATE TABLE IF NOT EXISTS cuotas (
    id_cuota         INT AUTO_INCREMENT PRIMARY KEY,
    id_pago          INT NOT NULL,
    nro_cuota        TINYINT NOT NULL,
    valor_cuota      DECIMAL(10,2) NOT NULL,
    fecha_vencimiento DATETIME NOT NULL,
    fecha_pago       DATETIME NULL,
    estado_cuota     ENUM('pendiente', 'pagada', 'vencida') NOT NULL DEFAULT 'pendiente',
    CONSTRAINT fk_cuotas_pagos
        FOREIGN KEY (id_pago) 
        REFERENCES pagos (id_pago)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Tabla CONTRIBUCIONES (distribución del pago entre diferentes entidades)
CREATE TABLE IF NOT EXISTS contribuciones (
    id_contribucion    INT AUTO_INCREMENT PRIMARY KEY,
    id_pago           INT NOT NULL,
    tipo_contribuyente ENUM('alumno', 'empresa', 'sence') NOT NULL,
    monto_contribuido DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_contribuciones_pagos
        FOREIGN KEY (id_pago) 
        REFERENCES pagos (id_pago)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uk_contribucion_tipo
        UNIQUE (id_pago, tipo_contribuyente)
);

-- Índices adicionales para optimizar consultas
CREATE INDEX idx_pagos_inscripcion ON pagos (id_inscripcion);
CREATE INDEX idx_cuotas_estado ON cuotas (estado_cuota);
CREATE INDEX idx_pagos_estado ON pagos (estado);

-- Tabla: Tramitaciones
-- Contiene la información sobre trámites específicos realizados por los alumnos.
CREATE TABLE IF NOT EXISTS tramaticiones (
    id_tramitacion INT NOT NULL PRIMARY KEY, -- Identificador único de la tramitación.
    id_alumno VARCHAR(10),                   -- Identificador del alumno (relación con `alumnos`).
    tipo_tramitacion ENUM('habilitación', 'tripulación') NOT NULL, -- Tipo de tramitación.
    fecha DATE NOT NULL,                     -- Fecha de la tramitación.
    n_carta_internalizacion VARCHAR(50),     -- Número de carta de internalización (opcional).
    n_recibo_directemar VARCHAR(50),         -- Número de recibo Directemar (opcional).
    estado TINYINT NOT NULL,                 -- Estado de la tramitación (0 = pendiente, 1 = completada).
    observacion TEXT,                        -- Observaciones adicionales sobre la tramitación (opcional).
    FOREIGN KEY (id_alumno) REFERENCES alumnos(rut) -- Relación con la tabla `alumnos`.
);

CREATE TABLE cotizacion (
    id_cotizacion INT AUTO_INCREMENT PRIMARY KEY,
    fecha_cotizacion DATE NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    origen VARCHAR(255) NOT NULL, -- Particular o nombre de la empresa
    nombre_contacto VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    modo_pago ENUM('Al Contado', 'Pagaré') NOT NULL,
	metodo_pago varchar(20), 
    num_cuotas INT DEFAULT NULL, -- Número de cuotas, aplicable solo para "Pagaré"
    detalle TEXT, -- Opcional, descripción del servicio
    total DECIMAL(10, 2) NOT NULL, -- Suma total de la cotización
);

CREATE TABLE detalle_cotizacion (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_cotizacion INT NOT NULL,
    id_curso varchar(20) NOT NULL,
    cantidad INT NOT NULL,
    valor_curso DECIMAL(10, 2) NOT NULL,
    valor_total DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (id_cotizacion) REFERENCES cotizacion(id_cotizacion) ON DELETE CASCADE,
    FOREIGN KEY (id_curso) REFERENCES cursos(id_curso)
);