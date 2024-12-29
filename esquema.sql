CREATE TABLE IF NOT EXISTS Alumnos (
    rut VARCHAR(10) PRIMARY KEY, -- Rut en formato xxxxxxxx-x
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(100),
    telefono BIGINT, -- Teléfono numérico de 9 cifras
    profesion VARCHAR(100),
    direccion VARCHAR(255),
    comuna VARCHAR(100),
    ciudad VARCHAR(100),
    metodo_llegada ENUM('Particular', 'Empresa') NOT NULL,
    id_empresa INT,
    FOREIGN KEY (id_empresa) REFERENCES Empresa(id_empresa)
);

-- Tabla: Empresa
CREATE TABLE IF NOT EXISTS Empresa (
    id_empresa INT AUTO_INCREMENT PRIMARY KEY,
    nombre_empresa VARCHAR(255) NOT NULL,
    ordenSence INT, -- Orden SENCE como número entero
    idfolio INT -- Id de folio como número entero
);

-- Tabla: Cursos
CREATE TABLE IF NOT EXISTS Cursos (
    id_curso INT AUTO_INCREMENT PRIMARY KEY,
    nombre_curso VARCHAR(255) NOT NULL,
    descripcion TEXT,
    modalidad ENUM('Presencial', 'Online') NOT NULL,
    codigo_sence INT, -- Código SENCE como número entero
    codigo_elearning INT -- Código e-learning como número entero
);

-- Tabla: Inscripciones
CREATE TABLE IF NOT EXISTS Inscripciones (
    id_inscripcion INT AUTO_INCREMENT PRIMARY KEY,
    id_alumno VARCHAR(10), -- Relación con Alumnos
    id_curso INT, -- Relación con Cursos
    fecha_inscripcion DATE NOT NULL,
    fecha_termino_condicional DATE,
    anio_inscripcion YEAR NOT NULL,
    FOREIGN KEY (id_alumno) REFERENCES Alumnos(rut),
    FOREIGN KEY (id_curso) REFERENCES Cursos(id_curso)
);

-- Tabla: Pagos
CREATE TABLE IF NOT EXISTS Pagos (
    id_pago INT AUTO_INCREMENT PRIMARY KEY,
    id_inscripcion INT, -- Relación con Inscripciones
    tipo_pago ENUM('Contado', 'Pagaré') NOT NULL,
    modalidad_pago ENUM('Completo', 'Diferido') NOT NULL,
    num_documento VARCHAR(50),
    cuotas_totales INT,
    valor DECIMAL(10, 2) NOT NULL,
    estado BOOLEAN NOT NULL,
    cuotas_pagadas INT,
    FOREIGN KEY (id_inscripcion) REFERENCES Inscripciones(id_inscripcion)
);

-- Tabla: PagosDetalle
CREATE TABLE IF NOT EXISTS PagosDetalle (
    id_pago INT, -- Relación con Pagos
    tipo_contribuyente ENUM('Alumno', 'Empresa', 'SENCE') NOT NULL,
    monto_contribuido DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (id_pago, tipo_contribuyente),
    FOREIGN KEY (id_pago) REFERENCES Pagos(id_pago)
);

-- Tabla: Tramitaciones
CREATE TABLE IF NOT EXISTS Tramitaciones (
    id_tramitacion INT AUTO_INCREMENT PRIMARY KEY,
    id_alumno VARCHAR(10), -- Relación con Alumnos
    tipo_tramitacion ENUM('Habilitación', 'Tripulación') NOT NULL,
    fecha DATE NOT NULL,
    n_carta_internalizacion VARCHAR(50),
    n_recibo_directemar VARCHAR(50),
    estado BOOLEAN NOT NULL,
    observacion TEXT,
    FOREIGN KEY (id_alumno) REFERENCES Alumnos(rut)
);
CREATE TABLE IF NOT EXISTS Usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    rol ENUM('admin', 'usuario') DEFAULT 'usuario'
);
