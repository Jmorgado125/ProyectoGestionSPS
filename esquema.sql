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
CREATE TABLE IF NOT EXISTS pagos (
    id_pago INT NOT NULL PRIMARY KEY,          -- Identificador único del pago.
    id_inscripcion INT,                        -- Identificador de la inscripción asociada (relación con `inscripciones`).
    tipo_pago ENUM('contado', 'pagaré') NOT NULL, -- Tipo de pago.
    modalidad_pago ENUM('completo', 'diferido') NOT NULL, -- Modalidad del pago.
    num_documento VARCHAR(50),                -- Número del documento del pago (opcional).
    cuotas_totales INT,                       -- Número total de cuotas (opcional).
    valor DECIMAL(10,2) NOT NULL,             -- Monto del pago.
    estado TINYINT NOT NULL,                  -- Estado del pago (0 = pendiente, 1 = completado).
    cuotas_pagadas INT,                       -- Número de cuotas pagadas (opcional).
    FOREIGN KEY (id_inscripcion) REFERENCES inscripciones(id_inscripcion) -- Relación con la tabla `inscripciones`.
);

-- Tabla: PagosDetalle
-- Detalla las contribuciones específicas realizadas por los alumnos, empresas o SENCE.
CREATE TABLE IF NOT EXISTS pagosdetalle (
    id_pago INT NOT NULL,                       -- Identificador del pago (relación con `pagos`).
    tipo_contribuyente ENUM('alumno', 'empresa', 'sence') NOT NULL, -- Tipo de contribuyente.
    monto_contribuido DECIMAL(10,2) NOT NULL,  -- Monto aportado por el contribuyente.
    PRIMARY KEY (id_pago, tipo_contribuyente), -- Llave primaria compuesta por el pago y tipo de contribuyente.
    FOREIGN KEY (id_pago) REFERENCES pagos(id_pago) -- Relación con la tabla `pagos`.
);

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
