CREATE TABLE `alumnos` (
  `rut` varchar(10) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) NOT NULL,
  `correo` varchar(100) DEFAULT NULL,
  `telefono` bigint DEFAULT NULL,
  `profesion` varchar(100) DEFAULT NULL,
  `direccion` varchar(255) DEFAULT NULL,
  `comuna` varchar(100) DEFAULT NULL,
  `ciudad` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`rut`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `asignaturas` (
  `id_asignatura` int NOT NULL AUTO_INCREMENT,
  `nombre_asignatura` varchar(100) NOT NULL,
  `id_curso` varchar(20) NOT NULL,
  PRIMARY KEY (`id_asignatura`),
  KEY `id_curso` (`id_curso`),
  CONSTRAINT `asignaturas_ibfk_1` FOREIGN KEY (`id_curso`) REFERENCES `cursos` (`id_curso`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `asistencia_alumnos` (
  `id_asistencia` int NOT NULL AUTO_INCREMENT,
  `id_contenido_diario` int NOT NULL,
  `id_alumno` varchar(10) NOT NULL,
  `estado_asistencia` enum('presente','ausente','justificado') NOT NULL,
  `observacion` text,
  PRIMARY KEY (`id_asistencia`),
  KEY `fk_asistencia_alumno` (`id_alumno`),
  KEY `fk_asistencia_contenido` (`id_contenido_diario`),
  CONSTRAINT `fk_asistencia_alumno` FOREIGN KEY (`id_alumno`) REFERENCES `alumnos` (`rut`),
  CONSTRAINT `fk_asistencia_contenido` FOREIGN KEY (`id_contenido_diario`) REFERENCES `contenidos_diarios` (`id_contenido_diario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `carpeta_libros` (
  `id_carpeta` int NOT NULL AUTO_INCREMENT,
  `numero_acta` varchar(20) NOT NULL,
  `id_curso` varchar(20) NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_termino` date DEFAULT NULL,
  `estado` enum('activo','finalizado') DEFAULT 'activo',
  PRIMARY KEY (`id_carpeta`),
  UNIQUE KEY `uk_acta_curso` (`numero_acta`,`id_curso`),
  KEY `fk_carpeta_curso` (`id_curso`),
  CONSTRAINT `fk_carpeta_curso` FOREIGN KEY (`id_curso`) REFERENCES `cursos` (`id_curso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `contenidos_diarios` (
  `id_contenido_diario` int NOT NULL AUTO_INCREMENT,
  `id_contenido` int NOT NULL,
  `fecha` date NOT NULL,
  `contenido_tratado` text NOT NULL,
  `horas_realizadas` int NOT NULL,
  `observaciones` text,
  PRIMARY KEY (`id_contenido_diario`),
  KEY `fk_contenido_semanal` (`id_contenido`),
  CONSTRAINT `fk_contenido_semanal` FOREIGN KEY (`id_contenido`) REFERENCES `contenidos_semanales` (`id_contenido`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `contenidos_semanales` (
  `id_contenido` int NOT NULL AUTO_INCREMENT,
  `id_libro` int NOT NULL,
  `semana` int NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date NOT NULL,
  PRIMARY KEY (`id_contenido`),
  KEY `fk_contenido_libro` (`id_libro`),
  CONSTRAINT `fk_contenido_libro` FOREIGN KEY (`id_libro`) REFERENCES `libros_clase` (`id_libro`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `contribuciones` (
  `id_contribucion` int NOT NULL AUTO_INCREMENT,
  `id_pago` int NOT NULL,
  `tipo_contribuyente` enum('alumno','empresa','sence') NOT NULL,
  `monto_contribuido` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id_contribucion`),
  UNIQUE KEY `uk_contribucion_tipo` (`id_pago`,`tipo_contribuyente`),
  CONSTRAINT `fk_contribuciones_pagos` FOREIGN KEY (`id_pago`) REFERENCES `pagos` (`id_pago`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `cotizacion` (
  `id_cotizacion` int NOT NULL AUTO_INCREMENT,
  `fecha_cotizacion` date NOT NULL,
  `fecha_vencimiento` date NOT NULL,
  `origen` varchar(255) NOT NULL,
  `nombre_contacto` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `modo_pago` enum('Al Contado','Pagaré') NOT NULL,
  `num_cuotas` int DEFAULT NULL,
  `detalle` text,
  `total` decimal(10,2) NOT NULL,
  `metodo_pago` varchar(20) DEFAULT NULL,
  `encargado` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id_cotizacion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `cuotas` (
  `id_cuota` int NOT NULL AUTO_INCREMENT,
  `id_pago` int NOT NULL,
  `nro_cuota` tinyint NOT NULL,
  `valor_cuota` decimal(10,2) NOT NULL,
  `fecha_vencimiento` datetime NOT NULL,
  `fecha_pago` datetime DEFAULT NULL,
  `estado_cuota` enum('pendiente','pagada','vencida') NOT NULL DEFAULT 'pendiente',
  `numero_ingreso` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id_cuota`),
  UNIQUE KEY `numero_ingreso` (`numero_ingreso`),
  KEY `fk_cuotas_pagos` (`id_pago`),
  KEY `idx_cuotas_estado` (`estado_cuota`),
  KEY `idx_cuotas_numero_ingreso` (`numero_ingreso`),
  CONSTRAINT `fk_cuotas_pagos` FOREIGN KEY (`id_pago`) REFERENCES `pagos` (`id_pago`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `current_alumnos` (
  `id_seguimiento` int NOT NULL AUTO_INCREMENT,
  `id_inscripcion` int NOT NULL,
  `fecha_actualizacion` timestamp NULL DEFAULT NULL,
  `asistencia_current` decimal(5,2) DEFAULT '0.00',
  `metodo_contacto` enum('llamada','mensaje','correo') DEFAULT NULL,
  `observacion` text,
  PRIMARY KEY (`id_seguimiento`),
  KEY `id_inscripcion` (`id_inscripcion`),
  KEY `idx_fecha_act` (`fecha_actualizacion`),
  CONSTRAINT `current_alumnos_ibfk_1` FOREIGN KEY (`id_inscripcion`) REFERENCES `inscripciones` (`id_inscripcion`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `current_alumnos_history` (
  `id_history` int NOT NULL AUTO_INCREMENT,
  `id_inscripcion` int NOT NULL,
  `fecha_actualizacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `asistencia_current` decimal(5,2) NOT NULL,
  `metodo_contacto` enum('llamada','mensaje','correo') DEFAULT NULL,
  `observacion` text,
  PRIMARY KEY (`id_history`),
  KEY `idx_fecha_inscripcion` (`id_inscripcion`,`fecha_actualizacion`),
  CONSTRAINT `current_alumnos_history_ibfk_1` FOREIGN KEY (`id_inscripcion`) REFERENCES `inscripciones` (`id_inscripcion`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `cursos` (
  `id_curso` varchar(20) NOT NULL,
  `nombre_curso` varchar(255) NOT NULL,
  `modalidad` enum('Presencial','Online','Híbrido') NOT NULL,
  `codigo_sence` int DEFAULT NULL,
  `codigo_elearning` int DEFAULT NULL,
  `horas_cronologicas` int NOT NULL DEFAULT '0',
  `horas_pedagogicas` float DEFAULT '0',
  `valor` int NOT NULL,
  `duracionDias` int DEFAULT NULL,
  `tipo_curso` enum('FORMACION','COMPETENCIA') NOT NULL,
  `resolucion` varchar(50) DEFAULT NULL,
  `fecha_resolucion` date DEFAULT NULL,
  `fecha_vigencia` date DEFAULT NULL,
  `valor_alumno_sence` decimal(10,0) DEFAULT NULL,
  PRIMARY KEY (`id_curso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `detalle_cotizacion` (
  `id_detalle` int NOT NULL AUTO_INCREMENT,
  `id_cotizacion` int NOT NULL,
  `id_curso` varchar(20) NOT NULL,
  `cantidad` int NOT NULL,
  `valor_curso` decimal(10,2) NOT NULL,
  `valor_total` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id_detalle`),
  KEY `id_cotizacion` (`id_cotizacion`),
  KEY `id_curso` (`id_curso`),
  CONSTRAINT `detalle_cotizacion_ibfk_1` FOREIGN KEY (`id_cotizacion`) REFERENCES `cotizacion` (`id_cotizacion`) ON DELETE CASCADE,
  CONSTRAINT `detalle_cotizacion_ibfk_2` FOREIGN KEY (`id_curso`) REFERENCES `cursos` (`id_curso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `doc_sequences` (
  `doc_type` varchar(50) NOT NULL,
  `last_number` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`doc_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `empresa` (
  `id_empresa` varchar(255) NOT NULL,
  `rut_empresa` varchar(20) NOT NULL,
  `direccion_empresa` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_empresa`),
  UNIQUE KEY `rut_empresa` (`rut_empresa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `empresa_contactos` (
  `id_contacto` int NOT NULL AUTO_INCREMENT,
  `id_empresa` varchar(255) NOT NULL,
  `nombre_contacto` varchar(255) NOT NULL,
  `rol_contacto` varchar(255) DEFAULT NULL,
  `correo_contacto` varchar(255) DEFAULT NULL,
  `telefono_contacto` bigint DEFAULT NULL,
  PRIMARY KEY (`id_contacto`),
  KEY `id_empresa` (`id_empresa`),
  CONSTRAINT `empresa_contactos_ibfk_1` FOREIGN KEY (`id_empresa`) REFERENCES `empresa` (`id_empresa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `facturas` (
  `id_factura` int NOT NULL AUTO_INCREMENT,
  `id_inscripcion` int NOT NULL,
  `numero_factura` varchar(20) NOT NULL,
  `monto_total` decimal(10,2) NOT NULL,
  `fecha_emision` datetime DEFAULT NULL,
  `estado` enum('pendiente','facturada') NOT NULL DEFAULT 'pendiente',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_factura`),
  UNIQUE KEY `numero_factura` (`numero_factura`),
  KEY `idx_facturas_inscripcion` (`id_inscripcion`),
  KEY `idx_facturas_estado` (`estado`),
  KEY `idx_facturas_numero` (`numero_factura`),
  CONSTRAINT `fk_facturas_inscripciones` FOREIGN KEY (`id_inscripcion`) REFERENCES `inscripciones` (`id_inscripcion`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `historial_pagos` (
  `id_historial` int NOT NULL AUTO_INCREMENT,
  `fecha_registro` datetime DEFAULT CURRENT_TIMESTAMP,
  `tipo_pago` enum('contado','pagare') NOT NULL,
  `id_inscripcion` int NOT NULL,
  `id_pago` int DEFAULT NULL,
  `id_cuota` int DEFAULT NULL,
  `rut_alumno` varchar(10) NOT NULL,
  `nombre_alumno` varchar(200) NOT NULL,
  `monto` decimal(10,2) NOT NULL,
  `numero_ingreso` varchar(20) DEFAULT NULL,
  `detalle` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_historial`),
  KEY `id_inscripcion` (`id_inscripcion`),
  KEY `id_pago` (`id_pago`),
  KEY `id_cuota` (`id_cuota`),
  KEY `rut_alumno` (`rut_alumno`),
  CONSTRAINT `historial_pagos_ibfk_1` FOREIGN KEY (`id_inscripcion`) REFERENCES `inscripciones` (`id_inscripcion`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `historial_pagos_ibfk_2` FOREIGN KEY (`id_pago`) REFERENCES `pagos` (`id_pago`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `historial_pagos_ibfk_3` FOREIGN KEY (`id_cuota`) REFERENCES `cuotas` (`id_cuota`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `historial_pagos_ibfk_4` FOREIGN KEY (`rut_alumno`) REFERENCES `alumnos` (`rut`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `inscripciones` (
  `id_inscripcion` int NOT NULL AUTO_INCREMENT,
  `id_alumno` varchar(10) DEFAULT NULL,
  `id_curso` varchar(20) DEFAULT NULL,
  `fecha_inscripcion` date DEFAULT NULL,
  `fecha_termino_condicional` date DEFAULT NULL,
  `anio_inscripcion` year DEFAULT NULL,
  `metodo_llegada` enum('particular','empresa') DEFAULT NULL,
  `numero_acta` varchar(20) DEFAULT NULL,
  `ordenSence` int DEFAULT NULL,
  `idfolio` int DEFAULT NULL,
  `id_empresa` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_inscripcion`),
  KEY `idx_inscripciones_alumno` (`id_alumno`),
  KEY `idx_inscripciones_curso` (`id_curso`),
  KEY `idx_inscripciones_empresa` (`id_empresa`),
  CONSTRAINT `fk_empresa_inscripciones` FOREIGN KEY (`id_empresa`) REFERENCES `empresa` (`id_empresa`),
  CONSTRAINT `fk_inscripciones_alumnos` FOREIGN KEY (`id_alumno`) REFERENCES `alumnos` (`rut`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_inscripciones_cursos` FOREIGN KEY (`id_curso`) REFERENCES `cursos` (`id_curso`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_inscripciones_empresa` FOREIGN KEY (`id_empresa`) REFERENCES `empresa` (`id_empresa`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `inscripciones_ibfk_1` FOREIGN KEY (`id_alumno`) REFERENCES `alumnos` (`rut`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `libros_clase` (
  `id_libro` int NOT NULL AUTO_INCREMENT,
  `id_carpeta` int NOT NULL,
  `asignatura` varchar(100) NOT NULL,
  `instructor` varchar(255) DEFAULT NULL,
  `n_res_directemar` varchar(50) DEFAULT NULL,
  `horas_totales` int DEFAULT NULL,
  `estado` enum('activo','finalizado') DEFAULT 'activo',
  PRIMARY KEY (`id_libro`),
  KEY `fk_libro_carpeta` (`id_carpeta`),
  CONSTRAINT `fk_libro_carpeta` FOREIGN KEY (`id_carpeta`) REFERENCES `carpeta_libros` (`id_carpeta`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `pagares` (
  `id_pagare` int NOT NULL AUTO_INCREMENT,
  `id_pago` int NOT NULL,
  `fecha_creacion` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_pagare`),
  KEY `fk_pagares_pagos` (`id_pago`),
  CONSTRAINT `fk_pagares_pagos` FOREIGN KEY (`id_pago`) REFERENCES `pagos` (`id_pago`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `pagos` (
  `id_pago` int NOT NULL AUTO_INCREMENT,
  `numero_orden` varchar(20) DEFAULT NULL,
  `id_inscripcion` int NOT NULL,
  `tipo_pago` enum('contado','pagare') NOT NULL,
  `modalidad_pago` enum('completo','diferido') NOT NULL,
  `fecha_inscripcion` datetime NOT NULL,
  `fecha_pago` datetime DEFAULT NULL,
  `fecha_final` datetime DEFAULT NULL,
  `num_cuotas` tinyint NOT NULL DEFAULT '1',
  `valor_total` decimal(10,2) NOT NULL,
  `estado` enum('pendiente','pagado','cancelado') NOT NULL DEFAULT 'pendiente',
  `estado_orden` enum('SIN EMITIR','EMITIDO') DEFAULT 'SIN EMITIR',
  `encargado` varchar(100) DEFAULT NULL,
  `detalle` varchar(255) DEFAULT NULL,
  `metodo_pago` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_pago`),
  UNIQUE KEY `numero_orden` (`numero_orden`),
  KEY `idx_pagos_inscripcion` (`id_inscripcion`),
  KEY `idx_pagos_estado` (`estado`),
  CONSTRAINT `fk_pagos_inscripciones` FOREIGN KEY (`id_inscripcion`) REFERENCES `inscripciones` (`id_inscripcion`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `tipos_tramite` (
  `id_tipo_tramite` int NOT NULL AUTO_INCREMENT,
  `id_tramitacion` int NOT NULL,
  `doc_num` int DEFAULT NULL,
  `nombre_tramite` varchar(100) NOT NULL,
  `fecha_emision` date DEFAULT NULL,
  `estado` enum('pendiente','completado') DEFAULT 'pendiente',
  PRIMARY KEY (`id_tipo_tramite`),
  KEY `tipos_tramite_ibfk_1` (`id_tramitacion`),
  CONSTRAINT `tipos_tramite_ibfk_1` FOREIGN KEY (`id_tramitacion`) REFERENCES `tramitaciones` (`id_tramitacion`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `tramitaciones` (
  `id_tramitacion` int NOT NULL AUTO_INCREMENT,
  `id_inscripcion` int NOT NULL,
  `estado_general` enum('pendiente','en_proceso','completado') DEFAULT 'pendiente',
  `fecha_final` date DEFAULT NULL,
  `fecha_ultimo_cambio` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `observacion` text,
  PRIMARY KEY (`id_tramitacion`),
  KEY `tramitaciones_ibfk_1` (`id_inscripcion`),
  CONSTRAINT `tramitaciones_ibfk_1` FOREIGN KEY (`id_inscripcion`) REFERENCES `inscripciones` (`id_inscripcion`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `usuarios` (
  `id_usuario` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(100) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `rol` enum('admin','usuario') DEFAULT 'usuario',
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
