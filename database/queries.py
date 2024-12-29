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

def insert_course(nombre_curso, descripcion, modalidad, codigo_sence, codigo_elearning):
    """Inserta un nuevo curso."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO Cursos 
                (nombre_curso, descripcion, modalidad, codigo_sence, codigo_elearning)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (nombre_curso, descripcion, modalidad, codigo_sence, codigo_elearning))
            conn.commit()
        except Exception as e:
            print("Error al insertar curso:", e)
            return False
        finally:
            cursor.close()
            conn.close()
        return True
    return False

# =======================================
#               ALUMNOS
# =======================================
def enroll_student(rut, id_curso, numero_acta,
                   fecha_inscripcion, fecha_termino_condicional, anio_inscripcion):
    """
    Inserta una fila en 'Inscripciones', usando la columna 'numero_acta'.
    """
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
                numero_acta,                  # <-- Nuevo
                fecha_inscripcion,
                fecha_termino_condicional,
                anio_inscripcion
            ))
            conn.commit()
        except Exception as e:
            print("Error al inscribir alumno:", e)
            return False
        finally:
            cursor.close()
            conn.close()
        return True
    return False



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

