CREATE TABLE `alumnos` (
  `rut` VARCHAR(10) NOT NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `apellido` VARCHAR(100) NOT NULL,
  `correo` VARCHAR(100) DEFAULT NULL,
  `telefono` BIGINT DEFAULT NULL,
  `profesion` VARCHAR(100) DEFAULT NULL,
  `direccion` VARCHAR(255) DEFAULT NULL,
  `comuna` VARCHAR(100) DEFAULT NULL,
  `ciudad` VARCHAR(100) DEFAULT NULL,
  PRIMARY KEY (`rut`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `cursos` (
  `id_curso` VARCHAR(20) NOT NULL,
  `nombre_curso` VARCHAR(255) NOT NULL,
  `modalidad` ENUM('Presencial','Online','Híbrido') NOT NULL,
  `codigo_sence` INT DEFAULT NULL,
  `codigo_elearning` INT DEFAULT NULL,
  `horas_cronologicas` INT NOT NULL DEFAULT '0',
  `horas_pedagogicas` FLOAT DEFAULT '0',
  `valor` INT NOT NULL,
  `duracionDias` INT DEFAULT NULL,
  `tipo_curso` ENUM('FORMACION','COMPETENCIA') NOT NULL,
  `resolucion` VARCHAR(50) DEFAULT NULL,
  `fecha_resolucion` DATE DEFAULT NULL,
  `fecha_vigencia` DATE DEFAULT NULL,
  `valor_alumno_sence` DECIMAL(10,0) DEFAULT NULL,
  PRIMARY KEY (`id_curso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `empresa` (
  `id_empresa` VARCHAR(255) NOT NULL,
  `rut_empresa` VARCHAR(20) NOT NULL,
  `direccion_empresa` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id_empresa`),
  UNIQUE KEY `rut_empresa` (`rut_empresa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `carpeta_libros` (
  `id_carpeta` INT NOT NULL AUTO_INCREMENT,
  `numero_acta` VARCHAR(20) NOT NULL,
  `id_curso` VARCHAR(20) NOT NULL,
  `fecha_inicio` DATE NOT NULL,
  `fecha_termino` DATE DEFAULT NULL,
  `estado` ENUM('activo','finalizado') DEFAULT 'activo',
  PRIMARY KEY (`id_carpeta`),
  UNIQUE KEY `uk_acta_curso` (`numero_acta`,`id_curso`),
  KEY `fk_carpeta_curso` (`id_curso`),
  CONSTRAINT `fk_carpeta_curso` FOREIGN KEY (`id_curso`) REFERENCES `cursos` (`id_curso`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `libros_clase` (
  `id_libro` INT NOT NULL AUTO_INCREMENT,
  `id_carpeta` INT NOT NULL,
  `asignatura` VARCHAR(100) NOT NULL,
  `instructor` VARCHAR(255) DEFAULT NULL,
  `n_res_directemar` VARCHAR(50) DEFAULT NULL,
  `horas_totales` INT DEFAULT NULL,
  `estado` ENUM('activo','finalizado') DEFAULT 'activo',
  PRIMARY KEY (`id_libro`),
  KEY `fk_libro_carpeta` (`id_carpeta`),
  CONSTRAINT `fk_libro_carpeta` FOREIGN KEY (`id_carpeta`) REFERENCES `carpeta_libros` (`id_carpeta`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `contenidos_semanales` (
  `id_contenido` INT NOT NULL AUTO_INCREMENT,
  `id_libro` INT NOT NULL,
  `semana` INT NOT NULL,
  `fecha_inicio` DATE NOT NULL,
  `fecha_fin` DATE NOT NULL,
  PRIMARY KEY (`id_contenido`),
  KEY `fk_contenido_libro` (`id_libro`),
  CONSTRAINT `fk_contenido_libro` FOREIGN KEY (`id_libro`) REFERENCES `libros_clase` (`id_libro`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `contenidos_diarios` (
  `id_contenido_diario` INT NOT NULL AUTO_INCREMENT,
  `id_contenido` INT NOT NULL,
  `fecha` DATE NOT NULL,
  `contenido_tratado` TEXT NOT NULL,
  `horas_realizadas` INT NOT NULL,
  `observaciones` TEXT,
  PRIMARY KEY (`id_contenido_diario`),
  KEY `fk_contenido_semanal` (`id_contenido`),
  CONSTRAINT `fk_contenido_semanal` FOREIGN KEY (`id_contenido`) REFERENCES `contenidos_semanales` (`id_contenido`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `asignaturas` (
  `id_asignatura` INT NOT NULL AUTO_INCREMENT,
  `nombre_asignatura` VARCHAR(100) NOT NULL,
  `id_curso` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`id_asignatura`),
  KEY `id_curso` (`id_curso`),
  CONSTRAINT `asignaturas_ibfk_1` FOREIGN KEY (`id_curso`) REFERENCES `cursos` (`id_curso`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `inscripciones` (
  `id_inscripcion` INT NOT NULL AUTO_INCREMENT,
  `id_alumno` VARCHAR(10) DEFAULT NULL,
  `id_curso` VARCHAR(20) DEFAULT NULL,
  `fecha_inscripcion` DATE DEFAULT NULL,
  `fecha_termino_condicional` DATE DEFAULT NULL,
  `anio_inscripcion` YEAR DEFAULT NULL,
  `metodo_llegada` ENUM('particular','empresa') DEFAULT NULL,
  `numero_acta` VARCHAR(20) DEFAULT NULL,
  `ordenSence` INT DEFAULT NULL,
  `idfolio` INT DEFAULT NULL,
  `id_empresa` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id_inscripcion`),
  KEY `idx_inscripciones_alumno` (`id_alumno`),
  KEY `idx_inscripciones_curso` (`id_curso`),
  KEY `idx_inscripciones_empresa` (`id_empresa`),
  CONSTRAINT `fk_empresa_inscripciones` FOREIGN KEY (`id_empresa`) REFERENCES `empresa` (`id_empresa`),
  CONSTRAINT `fk_inscripciones_alumnos` FOREIGN KEY (`id_alumno`) REFERENCES `alumnos` (`rut`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_inscripciones_cursos` FOREIGN KEY (`id_curso`) REFERENCES `cursos` (`id_curso`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `pagos` (
  `id_pago` INT NOT NULL AUTO_INCREMENT,
  `id_inscripcion` INT NOT NULL,
  `tipo_pago` ENUM('contado','pagare') NOT NULL,
  `modalidad_pago` ENUM('completo','diferido') NOT NULL,
  `fecha_inscripcion` DATETIME NOT NULL,
  `fecha_pago` DATETIME DEFAULT NULL,
  `fecha_final` DATETIME DEFAULT NULL,
  `num_cuotas` TINYINT NOT NULL DEFAULT '1',
  `valor_total` DECIMAL(10,2) NOT NULL,
  `estado` ENUM('pendiente','pagado','cancelado') NOT NULL DEFAULT 'pendiente',
  PRIMARY KEY (`id_pago`),
  KEY `idx_pagos_inscripcion` (`id_inscripcion`),
  KEY `idx_pagos_estado` (`estado`),
  CONSTRAINT `fk_pagos_inscripciones` FOREIGN KEY (`id_inscripcion`) REFERENCES `inscripciones` (`id_inscripcion`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `detalle_cotizacion` (
  `id_detalle` INT NOT NULL AUTO_INCREMENT,
  `id_cotizacion` INT NOT NULL,
  `id_curso` VARCHAR(20) NOT NULL,
  `cantidad` INT NOT NULL,
  `valor_curso` DECIMAL(10,2) NOT NULL,
  `valor_total` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`id_detalle`),
  KEY `id_cotizacion` (`id_cotizacion`),
  KEY `id_curso` (`id_curso`),
  CONSTRAINT `detalle_cotizacion_ibfk_1` FOREIGN KEY (`id_cotizacion`) REFERENCES `cotizacion` (`id_cotizacion`) ON DELETE CASCADE,
  CONSTRAINT `detalle_cotizacion_ibfk_2` FOREIGN KEY (`id_curso`) REFERENCES `cursos` (`id_curso`)
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `cotizacion` (
  `id_cotizacion` INT NOT NULL AUTO_INCREMENT,
  `fecha_cotizacion` DATE NOT NULL,
  `fecha_vencimiento` DATE NOT NULL,
  `origen` VARCHAR(255) NOT NULL,
  `nombre_contacto` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `modo_pago` ENUM('Al Contado','Pagaré') NOT NULL,
  `num_cuotas` INT DEFAULT NULL,
  `detalle` TEXT,
  `total` DECIMAL(10,2) NOT NULL,
  `metodo_pago` VARCHAR(20) DEFAULT NULL,
  `encargado` VARCHAR(20) DEFAULT NULL,
  PRIMARY KEY (`id_cotizacion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `pagares` (
  `id_pagare` INT NOT NULL AUTO_INCREMENT,
  `id_pago` INT NOT NULL,
  `fecha_creacion` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_pagare`),
  KEY `fk_pagares_pagos` (`id_pago`),
  CONSTRAINT `fk_pagares_pagos` FOREIGN KEY (`id_pago`) REFERENCES `pagos` (`id_pago`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `contribuciones` (
  `id_contribucion` INT NOT NULL AUTO_INCREMENT,
  `id_pago` INT NOT NULL,
  `tipo_contribuyente` ENUM('alumno','empresa','sence') NOT NULL,
  `monto_contribuido` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`id_contribucion`),
  UNIQUE KEY `uk_contribucion_tipo` (`id_pago`,`tipo_contribuyente`),
  CONSTRAINT `fk_contribuciones_pagos` FOREIGN KEY (`id_pago`) REFERENCES `pagos` (`id_pago`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `cuotas` (
  `id_cuota` INT NOT NULL AUTO_INCREMENT,
  `id_pago` INT NOT NULL,
  `nro_cuota` TINYINT NOT NULL,
  `valor_cuota` DECIMAL(10,2) NOT NULL,
  `fecha_vencimiento` DATETIME NOT NULL,
  `fecha_pago` DATETIME DEFAULT NULL,
  `estado_cuota` ENUM('pendiente','pagada','vencida') NOT NULL DEFAULT 'pendiente',
  `numero_ingreso` VARCHAR(20) DEFAULT NULL,
  PRIMARY KEY (`id_cuota`),
  UNIQUE KEY `numero_ingreso` (`numero_ingreso`),
  KEY `fk_cuotas_pagos` (`id_pago`),
  KEY `idx_cuotas_estado` (`estado_cuota`),
  KEY `idx_cuotas_numero_ingreso` (`numero_ingreso`),
  CONSTRAINT `fk_cuotas_pagos` FOREIGN KEY (`id_pago`) REFERENCES `pagos` (`id_pago`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `asistencia_alumnos` (
  `id_asistencia` INT NOT NULL AUTO_INCREMENT,
  `id_contenido_diario` INT NOT NULL,
  `id_alumno` VARCHAR(10) NOT NULL,
  `estado_asistencia` ENUM('presente','ausente','justificado') NOT NULL,
  `observacion` TEXT,
  PRIMARY KEY (`id_asistencia`),
  KEY `fk_asistencia_contenido` (`id_contenido_diario`),
  KEY `fk_asistencia_alumno` (`id_alumno`),
  CONSTRAINT `fk_asistencia_alumno` FOREIGN KEY (`id_alumno`) REFERENCES `alumnos` (`rut`),
  CONSTRAINT `fk_asistencia_contenido` FOREIGN KEY (`id_contenido_diario`) REFERENCES `contenidos_diarios` (`id_contenido_diario`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `historial_pagos` (
  `id_historial` INT NOT NULL AUTO_INCREMENT,
  `fecha_registro` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `tipo_pago` ENUM('contado','pagare') NOT NULL,
  `id_inscripcion` INT NOT NULL,
  `id_pago` INT DEFAULT NULL,
  `id_cuota` INT DEFAULT NULL,
  `rut_alumno` VARCHAR(10) NOT NULL,
  `nombre_alumno` VARCHAR(200) NOT NULL,
  `monto` DECIMAL(10,2) NOT NULL,
  `numero_ingreso` VARCHAR(20) DEFAULT NULL,
  `detalle` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id_historial`),
  KEY `id_inscripcion` (`id_inscripcion`),
  KEY `id_pago` (`id_pago`),
  KEY `id_cuota` (`id_cuota`),
  KEY `rut_alumno` (`rut_alumno`),
  CONSTRAINT `historial_pagos_ibfk_1` FOREIGN KEY (`id_inscripcion`) REFERENCES `inscripciones` (`id_inscripcion`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `historial_pagos_ibfk_2` FOREIGN KEY (`id_pago`) REFERENCES `pagos` (`id_pago`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `historial_pagos_ibfk_3` FOREIGN KEY (`id_cuota`) REFERENCES `cuotas` (`id_cuota`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `historial_pagos_ibfk_4` FOREIGN KEY (`rut_alumno`) REFERENCES `alumnos` (`rut`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `empresa_contactos` (
  `id_contacto` INT NOT NULL AUTO_INCREMENT,
  `id_empresa` VARCHAR(255) NOT NULL,
  `nombre_contacto` VARCHAR(255) NOT NULL,
  `rol_contacto` VARCHAR(255) DEFAULT NULL,
  `correo_contacto` VARCHAR(255) DEFAULT NULL,
  `telefono_contacto` BIGINT DEFAULT NULL,
  PRIMARY KEY (`id_contacto`),
  KEY `id_empresa` (`id_empresa`),
  CONSTRAINT `empresa_contactos_ibfk_1` FOREIGN KEY (`id_empresa`) REFERENCES `empresa` (`id_empresa`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `facturas` (
  `id_factura` INT NOT NULL AUTO_INCREMENT,
  `id_inscripcion` INT NOT NULL,
  `numero_factura` VARCHAR(20) NOT NULL,
  `monto_total` DECIMAL(10,2) NOT NULL,
  `fecha_emision` DATETIME DEFAULT NULL,
  `estado` ENUM('pendiente','facturada') NOT NULL DEFAULT 'pendiente',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_factura`),
  UNIQUE KEY `numero_factura` (`numero_factura`),
  KEY `idx_facturas_inscripcion` (`id_inscripcion`),
  KEY `idx_facturas_estado` (`estado`),
  KEY `idx_facturas_numero` (`numero_factura`),
  CONSTRAINT `fk_facturas_inscripciones` FOREIGN KEY (`id_inscripcion`) REFERENCES `inscripciones` (`id_inscripcion`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `tramitaciones` (
  `id_tramitacion` INT NOT NULL AUTO_INCREMENT,
  `id_inscripcion` INT NOT NULL,
  `estado_general` ENUM('pendiente','en_proceso','completado') DEFAULT 'pendiente',
  `fecha_final` DATE DEFAULT NULL,
  `fecha_ultimo_cambio` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `observacion` TEXT,
  PRIMARY KEY (`id_tramitacion`),
  KEY `tramitaciones_ibfk_1` (`id_inscripcion`),
  CONSTRAINT `tramitaciones_ibfk_1` FOREIGN KEY (`id_inscripcion`) REFERENCES `inscripciones` (`id_inscripcion`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `tipos_tramite` (
  `id_tipo_tramite` INT NOT NULL AUTO_INCREMENT,
  `id_tramitacion` INT NOT NULL,
  `doc_num` INT DEFAULT NULL,
  `nombre_tramite` VARCHAR(100) NOT NULL,
  `fecha_emision` DATE DEFAULT NULL,
  `estado` ENUM('pendiente','completado') DEFAULT 'pendiente',
  PRIMARY KEY (`id_tipo_tramite`),
  KEY `tipos_tramite_ibfk_1` (`id_tramitacion`),
  CONSTRAINT `tipos_tramite_ibfk_1` FOREIGN KEY (`id_tramitacion`) REFERENCES `tramitaciones` (`id_tramitacion`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `usuarios` (
  `id_usuario` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL,
  `password` VARCHAR(100) NOT NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `rol` ENUM('admin','usuario') DEFAULT 'usuario',
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `doc_sequences` (
  `doc_type` VARCHAR(50) NOT NULL,
  `last_number` INT NOT NULL DEFAULT '0',
  PRIMARY KEY (`doc_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
