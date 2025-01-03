-- Tabla: Alumnos
-- Contiene la información personal de los alumnos registrados.
CREATE TABLE IF NOT EXISTS alumnos (
    rut VARCHAR NOT NULL PRIMARY KEY, -- Identificador único del alumno (formato de RUT).
    nombre VARCHAR NOT NULL,          -- Nombre del alumno.
    apellido VARCHAR NOT NULL,        -- Apellido del alumno.
    correo VARCHAR,                   -- Correo electrónico del alumno (opcional).
    telefono BIGINT,                  -- Número de teléfono del alumno (opcional).
    profesion VARCHAR,                -- Profesión del alumno (opcional).
    direccion VARCHAR,                -- Dirección residencial del alumno (opcional).
    comuna VARCHAR,                   -- Comuna de residencia del alumno (opcional).
    ciudad VARCHAR                    -- Ciudad de residencia del alumno (opcional).
);

-- Tabla: Cursos
-- Define los cursos ofrecidos, incluyendo su descripción, modalidad y códigos asociados.
CREATE TABLE IF NOT EXISTS cursos (
    id_curso VARCHAR NOT NULL PRIMARY KEY, -- Identificador único del curso.
    nombre_curso VARCHAR NOT NULL,         -- Nombre del curso.
    modalidad ENUM NOT NULL,               -- Modalidad del curso (Presencial u Online).
    codigo_sence INT,                      -- Código SENCE del curso (opcional).
    codigo_elearning INT,                  -- Código de plataforma e-learning del curso (opcional).
    horas_cronologicas INT NOT NULL DEFAULT 0, -- Cantidad de horas cronológicas del curso.
    horas_pedagogicas FLOAT DEFAULT 0.0    -- Cantidad de horas pedagógicas del curso.
);

-- Tabla: Empresa
-- Contiene los datos de las empresas asociadas a los alumnos o cursos.
CREATE TABLE IF NOT EXISTS empresa (
    id_empresa INT NOT NULL PRIMARY KEY, -- Identificador único de la empresa.
    nombre_empresa VARCHAR NOT NULL,     -- Nombre de la empresa.
    ordenSence INT,                      -- Número de orden SENCE asociado (opcional).
    idfolio INT                          -- Identificador de folio de la empresa (opcional).
);

-- Tabla: Inscripciones
-- Relaciona alumnos con cursos, registrando la inscripción de un alumno en un curso.
CREATE TABLE IF NOT EXISTS inscripciones (
    id_inscripcion INT NOT NULL PRIMARY KEY, -- Identificador único de la inscripción.
    id_alumno VARCHAR,                       -- Identificador del alumno inscrito (relación con `alumnos`).
    id_curso VARCHAR NOT NULL,               -- Identificador del curso inscrito (relación con `cursos`).
    fecha_inscripcion DATE NOT NULL,         -- Fecha en que se realizó la inscripción.
    fecha_termino_condicional DATE,          -- Fecha condicional de término de inscripción (opcional).
    anio_inscripcion YEAR NOT NULL,          -- Año en que se realizó la inscripción.
    metodo_llegada ENUM NOT NULL,            -- Método de llegada del alumno (Particular o Empresa).
    id_empresa INT,                          -- Identificador de la empresa asociada (relación con `empresa`).
    numero_acta VARCHAR NOT NULL,            -- Número del acta de inscripción.
    FOREIGN KEY (id_alumno) REFERENCES alumnos(rut), -- Relación con la tabla `alumnos`.
    FOREIGN KEY (id_curso) REFERENCES cursos(id_curso), -- Relación con la tabla `cursos`.
    FOREIGN KEY (id_empresa) REFERENCES empresa(id_empresa) -- Relación con la tabla `empresa`.
);

-- Tabla: Pagos
-- Contiene la información de los pagos realizados por los alumnos o empresas.
CREATE TABLE IF NOT EXISTS pagos (
    id_pago INT NOT NULL PRIMARY KEY,        -- Identificador único del pago.
    id_inscripcion INT,                      -- Identificador de la inscripción asociada (relación con `inscripciones`).
    tipo_pago ENUM NOT NULL,                 -- Tipo de pago (Contado o Pagaré).
    modalidad_pago ENUM NOT NULL,            -- Modalidad del pago (Completo o Diferido).
    num_documento VARCHAR,                   -- Número del documento del pago (opcional).
    cuotas_totales INT,                      -- Número total de cuotas (opcional).
    valor DECIMAL NOT NULL,                  -- Monto del pago.
    estado TINYINT NOT NULL,                 -- Estado del pago (0 = pendiente, 1 = completado).
    cuotas_pagadas INT,                      -- Número de cuotas pagadas (opcional).
    FOREIGN KEY (id_inscripcion) REFERENCES inscripciones(id_inscripcion) -- Relación con la tabla `inscripciones`.
);

-- Tabla: PagosDetalle
-- Detalla las contribuciones específicas realizadas por los alumnos, empresas o SENCE.
CREATE TABLE IF NOT EXISTS pagosdetalle (
    id_pago INT NOT NULL,                       -- Identificador del pago (relación con `pagos`).
    tipo_contribuyente ENUM NOT NULL,           -- Tipo de contribuyente (Alumno, Empresa o SENCE).
    monto_contribuido DECIMAL NOT NULL,         -- Monto aportado por el contribuyente.
    PRIMARY KEY (id_pago, tipo_contribuyente),  -- Llave primaria compuesta por el pago y tipo de contribuyente.
    FOREIGN KEY (id_pago) REFERENCES pagos(id_pago) -- Relación con la tabla `pagos`.
);

-- Tabla: Tramitaciones
-- Contiene la información sobre trámites específicos realizados por los alumnos.
CREATE TABLE IF NOT EXISTS tramitaciones (
    id_tramitacion INT NOT NULL PRIMARY KEY, -- Identificador único de la tramitación.
    id_alumno VARCHAR,                       -- Identificador del alumno (relación con `alumnos`).
    tipo_tramitacion ENUM NOT NULL,          -- Tipo de tramitación (Habilitación o Tripulación).
    fecha DATE NOT NULL,                     -- Fecha de la tramitación.
    n_carta_internalizacion VARCHAR,         -- Número de carta de internalización (opcional).
    n_recibo_directemar VARCHAR,             -- Número de recibo Directemar (opcional).
    estado TINYINT NOT NULL,                 -- Estado de la tramitación (0 = pendiente, 1 = completada).
    observacion TEXT,                        -- Observaciones adicionales sobre la tramitación (opcional).
    FOREIGN KEY (id_alumno) REFERENCES alumnos(rut) -- Relación con la tabla `alumnos`.
);

-- Tabla: Usuarios
-- Contiene la información de los usuarios que tienen acceso al sistema.
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT NOT NULL PRIMARY KEY, -- Identificador único del usuario.
    username VARCHAR NOT NULL,          -- Nombre de usuario único.
    password VARCHAR NOT NULL,          -- Contraseña del usuario.
    nombre VARCHAR NOT NULL,            -- Nombre del usuario.
    rol ENUM('admin', 'usuario') DEFAULT 'usuario' -- Rol del usuario (admin o usuario estándar).
);
