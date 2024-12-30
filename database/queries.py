from database.db_config import connect_db

# =======================================
#                CURSOS
# =======================================
def fetch_courses():
    """Obtiene la lista de cursos."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Cursos")
            results = cursor.fetchall()
        except Exception as e:
            print("Error al obtener cursos:", e)
            results = []
        finally:
            cursor.close()
            conn.close()
        return results
    return []

def insert_course(
    id_curso, 
    nombre_curso, 
    modalidad, 
    codigo_sence, 
    codigo_elearning, 
    horas_cronologicas, 
    valor
):
    """
    Inserta un nuevo curso con cálculo de horas pedagógicas y valor del curso.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            horas_pedagogicas = round((horas_cronologicas * 4 / 3), 1)
            query = """
                INSERT INTO Cursos
                (id_curso, nombre_curso, modalidad,
                 codigo_sence, codigo_elearning,
                 horas_cronologicas, horas_pedagogicas, valor)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                id_curso,
                nombre_curso,
                modalidad,
                codigo_sence,
                codigo_elearning,
                horas_cronologicas,
                horas_pedagogicas,
                valor
            ))
            conn.commit()
        except Exception as e:
            print("Error al insertar curso:", e)
            return False
        finally:
            cursor.close()
            conn.close()
        return True
    return False


def update_course(
    id_curso,
    nombre_curso=None,
    modalidad=None,
    codigo_sence=None,
    codigo_elearning=None,
    horas_cronologicas=None,
    horas_pedagogicas=None,
    valor=None
):
    """
    Actualiza los datos de un curso existente, incluido el 'valor'.
    Si 'horas_cronologicas' se cambia, recalcula 'horas_pedagogicas' 
    a menos que se haya pasado manualmente.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # 1) Obtener el curso actual
            cursor.execute("SELECT * FROM Cursos WHERE id_curso = %s", (id_curso,))
            course = cursor.fetchone()
            if not course:
                print(f"Curso con ID {id_curso} no encontrado.")
                return False

            # Asumiendo orden de columnas:
            #  course[0] => id_curso
            #  course[1] => nombre_curso
            #  course[2] => modalidad
            #  course[3] => codigo_sence
            #  course[4] => codigo_elearning
            #  course[5] => horas_cronologicas
            #  course[6] => horas_pedagogicas
            #  course[7] => valor

            current_nombre   = course[1]
            current_mod      = course[2]
            current_sence    = course[3]
            current_elearn   = course[4]
            current_h_cron   = course[5]
            current_h_pedag  = course[6]
            current_valor    = course[7]

            # 2) Determinar horas_cronologicas
            new_horas_cron = horas_cronologicas if horas_cronologicas is not None else current_h_cron

            # 3) Determinar horas_pedagogicas
            if horas_pedagogicas is not None:
                # Si nos pasan un valor manual, lo usamos tal cual
                new_horas_pedag = horas_pedagogicas
            else:
                # Si no pasó horas_pedagogicas, la calculamos
                new_horas_pedag = round((new_horas_cron * 4 / 3), 1)

            # 4) Determinar valor
            new_valor = valor if valor is not None else current_valor

            # 5) Armamos la query de UPDATE
            query = """
                UPDATE Cursos
                SET nombre_curso = %s,
                    modalidad = %s,
                    codigo_sence = %s,
                    codigo_elearning = %s,
                    horas_cronologicas = %s,
                    horas_pedagogicas = %s,
                    valor = %s
                WHERE id_curso = %s
            """

            # 6) Ejecutar el update
            cursor.execute(query, (
                nombre_curso or current_nombre,
                modalidad or current_mod,
                codigo_sence if codigo_sence is not None else current_sence,
                codigo_elearning if codigo_elearning is not None else current_elearn,
                new_horas_cron,
                new_horas_pedag,
                new_valor,
                id_curso
            ))
            conn.commit()

        except Exception as e:
            print("Error al actualizar curso:", e)
            return False
        finally:
            cursor.close()
            conn.close()
        return True
    return False

def delete_course_by_id(id_curso):
    """
    Elimina un curso de la tabla 'Cursos' usando su id_curso como criterio.
    Retorna True si se eliminó correctamente, False en caso contrario.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = "DELETE FROM Cursos WHERE id_curso = %s"
            cursor.execute(query, (id_curso,))
            conn.commit()
            if cursor.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar curso:", e)
            return False
        finally:
            cursor.close()
            conn.close()
    return False

# =======================================
#               ALUMNOS y Matricula 
# =======================================
def validate_alumno_exists(rut):
    """Valida si un alumno existe en la base de datos."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT COUNT(*) FROM Alumnos WHERE rut = %s"
            cursor.execute(query, (rut,))
            result = cursor.fetchone()
            return result[0] > 0
        except Exception as e:
            print("Error al validar alumno:", e)
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def validate_curso_exists(id_curso):
    """Valida si un curso existe en la base de datos."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT COUNT(*) FROM Cursos WHERE id_curso = %s"
            cursor.execute(query, (id_curso,))
            result = cursor.fetchone()
            return result[0] > 0
        except Exception as e:
            print("Error al validar curso:", e)
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def enroll_student(rut, id_curso, numero_acta, fecha_inscripcion, fecha_termino_condicional, anio_inscripcion):
    """
    Inserta una fila en 'Inscripciones', usando la columna 'numero_acta'.
    Retorna (True, None) si OK, o (False, str_error) si ocurre un error.
    """
    if not validate_alumno_exists(rut):
        return (False, "El alumno no existe.")
    if not validate_curso_exists(id_curso):
        return (False, "El curso no existe.")

    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO Inscripciones
                (id_alumno, id_curso, numero_acta,
                 fecha_inscripcion, fecha_termino_condicional, anio_inscripcion)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                rut,
                id_curso,
                numero_acta,
                fecha_inscripcion,
                fecha_termino_condicional,
                anio_inscripcion
            ))
            conn.commit()
        except Exception as e:
            print("Error al inscribir alumno:", e)
            return (False, str(e))
        finally:
            cursor.close()
            conn.close()
        return (True, None)
    return (False, "No hay conexión con la base de datos")


def fetch_inscriptions():
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
              SELECT id_inscripcion, id_alumno, id_curso, numero_acta,
                     fecha_inscripcion, fecha_termino_condicional, anio_inscripcion
              FROM Inscripciones
            """)
            results = cursor.fetchall()
        except Exception as e:
            print("Error al obtener inscripciones:", e)
            results = []
        finally:
            cursor.close()
            conn.close()
        return results
    return []



def insert_student(rut, nombre, apellido, correo, telefono, profesion, direccion, ciudad, comuna, id_empresa=None):
    """Inserta un nuevo alumno."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO Alumnos 
                (rut, nombre, apellido, correo, telefono, profesion, direccion, ciudad, comuna, id_empresa)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (rut, nombre, apellido, correo, telefono, profesion, direccion, ciudad, comuna, id_empresa))
            conn.commit()
        except Exception as e:
            print("Error al insertar alumno:", e)
            return False
        finally:
            cursor.close()
            conn.close()
        return True
    return False

def fetch_all_students():
    """Retorna todos los alumnos."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM Alumnos"
            cursor.execute(query)
            results = cursor.fetchall()
        except Exception as e:
            print("Error al obtener alumnos:", e)
            results = []
        finally:
            cursor.close()
            conn.close()
        return results
    return []

def fetch_student_by_rut(rut):
    """Retorna un alumno que coincida con el RUT dado."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM Alumnos WHERE rut = %s"
            cursor.execute(query, (rut,))
            result = cursor.fetchone()
        except Exception as e:
            print("Error al buscar alumno por RUT:", e)
            result = None
        finally:
            cursor.close()
            conn.close()
        return result
    return None

def delete_student_by_rut(rut):
    """Elimina un alumno por su RUT."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = "DELETE FROM Alumnos WHERE rut = %s"
            cursor.execute(query, (rut,))
            conn.commit()
            if cursor.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            print("Error al eliminar alumno:", e)
            return False
        finally:
            cursor.close()
            conn.close()

def fetch_courses_by_student_rut(rut):
    """Obtiene los cursos realizados por un alumno y las fechas de inscripción."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                SELECT c.nombre_curso, i.fecha_inscripcion
                FROM Inscripciones i
                INNER JOIN Cursos c ON i.id_curso = c.id_curso
                WHERE i.id_alumno = %s
            """
            cursor.execute(query, (rut,))
            results = cursor.fetchall()
        except Exception as e:
            print("Error al obtener cursos del alumno:", e)
            results = []
        finally:
            cursor.close()
            conn.close()
        return results
    return []

# =======================================
#             PAGOS
# =======================================
def fetch_payments():
    """Obtiene la lista de pagos."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Pagos")
            results = cursor.fetchall()
        except Exception as e:
            print("Error al obtener pagos:", e)
            results = []
        finally:
            cursor.close()
            conn.close()
        return results
    return []

def insert_payment(id_inscripcion, tipo_pago, modalidad_pago, num_documento, cuotas_totales, valor, estado, cuotas_pagadas):
    """Inserta un nuevo pago."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO Pagos 
                (id_inscripcion, tipo_pago, modalidad_pago, num_documento, cuotas_totales, valor, estado, cuotas_pagadas)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (id_inscripcion, tipo_pago, modalidad_pago, num_documento, cuotas_totales, valor, estado, cuotas_pagadas))
            conn.commit()
        except Exception as e:
            print("Error al insertar pago:", e)
            return False
        finally:
            cursor.close()
            conn.close()
        return True
    return False

def fetch_payments_by_inscription(id_inscripcion):
    """Obtiene los pagos asociados a una inscripción específica."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM Pagos WHERE id_inscripcion = %s"
            cursor.execute(query, (id_inscripcion,))
            results = cursor.fetchall()
        except Exception as e:
            print("Error al obtener pagos por inscripción:", e)
            results = []
        finally:
            cursor.close()
            conn.close()
        return results
    return []

# =======================================
#             FACTURACIÓN
# =======================================
def insert_invoice(id_inscripcion, numero_factura, monto_total, estado):
    """Inserta una nueva factura en la tabla 'Facturacion'."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO Facturacion 
                (id_inscripcion, numero_factura, monto_total, estado)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (id_inscripcion, numero_factura, monto_total, estado))
            conn.commit()
        except Exception as e:
            print("Error al insertar factura:", e)
            return False
        finally:
            cursor.close()
            conn.close()
        return True
    return False

def fetch_invoices():
    """Obtiene la lista de facturas."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Facturacion")
            results = cursor.fetchall()
        except Exception as e:
            print("Error al obtener facturas:", e)
            results = []
        finally:
            cursor.close()
            conn.close()
        return results
    return []

# =======================================
#           AUTENTICACION 
# =======================================

def fetch_user_by_credentials(username, password):
    """Obtiene un usuario por sus credenciales."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM Usuarios WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()
            return user
        except Exception as e:
            print("Error al validar usuario:", e)
            return None
        finally:
            cursor.close()
            conn.close()
    return None

