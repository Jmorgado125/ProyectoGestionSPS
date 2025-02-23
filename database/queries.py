from database.db_config import connect_db
import re
from datetime import datetime , timedelta
from helpers.utils import requiere_rol
import mysql.connector
from mysql.connector import Error

# =======================================
#          UTILIDAD: VALIDAR RUT
# =======================================

def is_valid_chilean_rut(rut_str):
    """
    Valida formato y dígito verificador de un RUT chileno de forma básica.
    Formato esperado: XX.XXX.XXX-X o sin puntos, e.g. 12345678-9
    Esta función es simplificada. Para casos reales, 
    usar una librería o algoritmo más completo.
    """
    # Quitar puntos y convertir a mayúscula
    rut_str = rut_str.replace(".", "").upper().strip()

    # Verificar patrón básico: números, guión y dígito verificador (0-9 o K)
    if not re.match(r'^\d{1,8}-[\dK]$', rut_str):
        return False

    # Separar cuerpo y dígito verificador
    cuerpo, dv = rut_str.split("-")

    # Calcular dígito verificador
    suma = 0
    factor = 2
    for c in reversed(cuerpo):
        suma += int(c) * factor
        factor = 9 if factor == 7 else factor + 1
    # Resto
    resto = 11 - (suma % 11)
    dv_calc = 'K' if resto == 10 else '0' if resto == 11 else str(resto)

    return dv == dv_calc

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
    valor,
    duracionDias,
    tipo_curso,
    resolucion,
    fecha_resolucion,
    fecha_vigencia,
    valor_alumno_sence
):
    """
    Inserta un nuevo curso con cálculo de horas pedagógicas, valor del curso y duración en días.
    Incluye nuevos campos como tipo_curso, resolución, fechas y valor por alumno SENCE.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            horas_pedagogicas = round((horas_cronologicas * 4 / 3), 1)
            query = """
                INSERT INTO cursos
                (id_curso, nombre_curso, modalidad, codigo_sence, codigo_elearning,
                 horas_cronologicas, horas_pedagogicas, valor, duracionDias,
                 tipo_curso, resolucion, fecha_resolucion, fecha_vigencia, valor_alumno_sence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                id_curso,
                nombre_curso,
                modalidad,
                codigo_sence,
                codigo_elearning,
                horas_cronologicas,
                horas_pedagogicas,
                valor,
                duracionDias,
                tipo_curso,
                resolucion,
                fecha_resolucion,
                fecha_vigencia,
                valor_alumno_sence
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
    valor=None,
    duracionDias=None,
    tipo_curso=None,
    resolucion=None,
    fecha_resolucion=None,
    fecha_vigencia=None,
    valor_alumno_sence=None
):
    """
    Actualiza los datos de un curso existente con los nombres de columnas corregidos.
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

            # Nombres de columnas corregidos
            current_nombre = course[1]
            current_mod = course[2]
            current_sence = course[3]
            current_elearning = course[4]
            current_h_cron = course[5]
            current_h_pedag = course[6]
            current_valor = course[7]
            current_dias = course[8]
            current_tipo = course[9]
            current_resolucion = course[10]
            current_fecha_resolucion = course[11]
            current_fecha_vigencia = course[12]
            current_valor_alumno_sence = course[13]

            # 2) Determinar horas_cronologicas
            new_horas_cron = horas_cronologicas if horas_cronologicas is not None else current_h_cron

            # 3) Determinar horas_pedagogicas
            if horas_pedagogicas is not None:
                new_horas_pedag = horas_pedagogicas
            else:
                new_horas_pedag = round((new_horas_cron * 4 / 3), 1)

            # 4) Query actualizada con los nombres correctos de las columnas
            query = """
                UPDATE Cursos
                SET nombre_curso = %s,
                    modalidad = %s,
                    codigo_sence = %s,
                    codigo_elearning = %s,
                    horas_cronologicas = %s,
                    horas_pedagogicas = %s,
                    valor = %s,
                    duracionDias = %s,
                    tipo_curso = %s,
                    resolucion = %s,
                    fecha_resolucion = %s,
                    fecha_vigencia = %s,
                    valor_alumno_sence = %s
                WHERE id_curso = %s
            """

            # 5) Ejecutar el update con todos los campos
            cursor.execute(query, (
                nombre_curso or current_nombre,
                modalidad or current_mod,
                codigo_sence if codigo_sence is not None else current_sence,
                codigo_elearning if codigo_elearning is not None else current_elearning,
                new_horas_cron,
                new_horas_pedag,
                valor if valor is not None else current_valor,
                duracionDias if duracionDias is not None else current_dias,
                tipo_curso if tipo_curso is not None else current_tipo,
                resolucion if resolucion is not None else current_resolucion,
                fecha_resolucion if fecha_resolucion is not None else current_fecha_resolucion,
                fecha_vigencia if fecha_vigencia is not None else current_fecha_vigencia,
                valor_alumno_sence if valor_alumno_sence is not None else current_valor_alumno_sence,
                id_curso
            ))
            conn.commit()
            return True

        except Exception as e:
            print("Error al actualizar curso:", e)
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
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
#               ALUMNOS
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

def insert_student(rut, nombre, apellido, correo=None, telefono=None, 
                   profesion=None, direccion=None, comuna=None, ciudad=None):


    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO Alumnos 
                (rut, nombre, apellido, correo, telefono, profesion, direccion, comuna, ciudad)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                rut, nombre, apellido, correo, telefono, 
                profesion, direccion, comuna, ciudad
            ))
            conn.commit()
        except Exception as e:
            print("Error al insertar alumno:", e)
            return False
        finally:
            cursor.close()
            conn.close()
        return True
    return False

def update_student(rut, nombre=None, apellido=None, correo=None, 
                   telefono=None, profesion=None, direccion=None, 
                   comuna=None, ciudad=None):
    """
    Edita (actualiza) los datos de un alumno existente.
    Rut es la clave primaria y no se modifica.
    Retorna True si se actualiza correctamente, False en caso de error.
    """
    if not validate_alumno_exists(rut):
        print(f"No se encontró alumno con RUT {rut}")
        return False

    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            # 1) Obtener datos actuales
            cursor.execute("SELECT * FROM Alumnos WHERE rut = %s", (rut,))
            alumno = cursor.fetchone()
            if not alumno:
                print(f"Alumno con RUT {rut} no encontrado.")
                return False
            
            # Asumiendo el orden de columnas en la tabla Alumnos:
            #  alumno[0] => rut
            #  alumno[1] => nombre
            #  alumno[2] => apellido
            #  alumno[3] => correo
            #  alumno[4] => telefono
            #  alumno[5] => profesion
            #  alumno[6] => direccion
            #  alumno[7] => comuna
            #  alumno[8] => ciudad

            current_nombre    = alumno[1]
            current_apellido  = alumno[2]
            current_correo    = alumno[3]
            current_telefono  = alumno[4]
            current_profesion = alumno[5]
            current_direccion = alumno[6]
            current_comuna    = alumno[7]
            current_ciudad    = alumno[8]

            # 2) Determinar nuevos valores (si no llega ninguno, se deja el actual)
            new_nombre    = nombre if nombre is not None else current_nombre
            new_apellido  = apellido if apellido is not None else current_apellido
            new_correo    = correo if correo is not None else current_correo
            new_telefono  = telefono if telefono is not None else current_telefono
            new_profesion = profesion if profesion is not None else current_profesion
            new_direccion = direccion if direccion is not None else current_direccion
            new_comuna    = comuna if comuna is not None else current_comuna
            new_ciudad    = ciudad if ciudad is not None else current_ciudad

            # 3) Ejecutar UPDATE
            update_query = """
                UPDATE Alumnos
                SET nombre = %s,
                    apellido = %s,
                    correo = %s,
                    telefono = %s,
                    profesion = %s,
                    direccion = %s,
                    comuna = %s,
                    ciudad = %s
                WHERE rut = %s
            """
            cursor.execute(update_query, (
                new_nombre, new_apellido, new_correo, new_telefono,
                new_profesion, new_direccion, new_comuna, new_ciudad, rut
            ))
            conn.commit()

        except Exception as e:
            print("Error al actualizar datos del alumno:", e)
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

def fetch_students_by_name_apellido(nombre, apellido):
    """
    Retorna lista de alumnos que coincidan con (nombre, apellido).
    Búsqueda insensible a mayúsculas/minúsculas.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                SELECT * FROM Alumnos
                WHERE LOWER(nombre) LIKE LOWER(%s)
                  AND LOWER(apellido) LIKE LOWER(%s)
            """
            # Convertir los parámetros a minúsculas y agregar % para coincidencia parcial
            nombre_param = f"%{nombre}%" if nombre else "%"
            apellido_param = f"%{apellido}%" if apellido else "%"
            
            cursor.execute(query, (nombre_param, apellido_param))
            results = cursor.fetchall()
        except Exception as e:
            print("Error al buscar alumno por nombre y apellido:", e)
            results = []
        finally:
            cursor.close()
            conn.close()
        return results
    return []

def fetch_student_by_rut(rut):
    """
    Retorna un alumno que coincida con el RUT dado.
    Búsqueda insensible a mayúsculas/minúsculas.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM Alumnos WHERE LOWER(rut) = LOWER(%s)"
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
    return False

# =======================================
#         INSCRIPCIONES
# =======================================

    def process_enrollments(self):
            """
            Procesa las matrículas e inscripciones masivas en la base de datos
            """
            try:
                if not self.tree.get_children():
                    messagebox.showwarning("Advertencia", "No hay datos para procesar")
                    return
                
                # Recolectar datos del Treeview
                data_to_process = []
                for item in self.tree.get_children():
                    values = self.tree.item(item)["values"]
                    data_to_process.append(values)
                
                # Convertir a DataFrame para validación
                df = pd.DataFrame(data_to_process, columns=self.tree["columns"])
                
                # Validar datos
                errors = self.validate_data(df)
                if errors:
                    error_msg = "\n".join(errors)
                    messagebox.showerror("Errores en los datos", error_msg)
                    return
                
                # Contador para el registro de éxitos y errores
                success_count = 0
                error_count = 0
                error_messages = []
                
                # Procesar cada fila
                for idx, row in df.iterrows():
                    try:
                        # 1. Verificar si existe el alumno
                        student = fetch_student_by_rut(row['RUT'])
                        
                        # 2. Crear o actualizar alumno
                        student_data = {
                            'rut': row['RUT'],
                            'nombre': row['Nombre'],
                            'apellido': row['Apellido'],
                            'email': row['Email'],
                            'telefono': row['Teléfono'],
                            'profesion': row['Profesión'],
                            'direccion': row['Dirección'],
                            'ciudad': row['Ciudad'],
                            'comuna': row['Comuna']
                        }
                        
                        if student:
                            update_student(student_data)
                        else:
                            insert_student(student_data)
                        
                        # 3. Crear inscripción
                        inscription_data = {
                            'rut_alumno': row['RUT'],
                            'id_curso': row['ID Curso'],
                            'num_acta': row['N° Acta'],
                            'fecha_inscripcion': row['Fecha Inscripción'],
                            'fecha_termino': row['Fecha Término'] if pd.notna(row['Fecha Término']) else None,
                            'anio': int(row['Año']),
                            'metodo': row['Método'],
                            'empresa': row['Empresa'] if pd.notna(row['Empresa']) else None,
                            'cod_sence': row['Código SENCE'] if pd.notna(row['Código SENCE']) else None,
                            'folio': row['Folio'] if pd.notna(row['Folio']) else None
                        }
                        
                        # Usar la función de inscripción existente
                        enroll_student(inscription_data)
                        
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f"Error en fila {idx + 1} (RUT: {row['RUT']}): {str(e)}")
                
                # Mostrar resumen
                message = f"Proceso completado:\n\n"
                message += f"Registros exitosos: {success_count}\n"
                if error_count > 0:
                    message += f"Registros con error: {error_count}\n\n"
                    message += "Detalle de errores:\n" + "\n".join(error_messages)
                
                if error_count > 0:
                    messagebox.showwarning("Proceso Completado con Advertencias", message)
                else:
                    messagebox.showinfo("Proceso Completado", message)
                
                if success_count > 0:
                    self.window.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al procesar datos: {str(e)}")

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

def fetch_inscriptions():
    """
    Obtiene todas las inscripciones con información detallada incluyendo el estado del pago.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    i.id_inscripcion as ID,
                    i.numero_acta as N_Acta,
                    a.rut as RUT,
                    CASE 
                        WHEN a.nombre IS NOT NULL AND a.apellido IS NOT NULL 
                        THEN CONCAT(a.nombre, ' ', a.apellido)
                        ELSE a.nombre 
                    END as Nombre_Completo,
                    i.id_curso as ID_Curso,
                    i.fecha_inscripcion as F_Inscripcion,
                    i.fecha_termino_condicional as F_Termino,
                    i.anio_inscripcion as Año,
                    CASE 
                        WHEN i.id_empresa IS NOT NULL THEN e.id_empresa 
                        ELSE 'Particular'
                    END as Empresa,
                    i.ordenSence as Codigo_Sence,
                    i.idfolio as Folio,
                    COALESCE(
                        CASE 
                            WHEN p.estado IS NULL THEN 'SIN PROCESAR'
                            ELSE UPPER(p.estado)
                        END,
                        'SIN PROCESAR'
                    ) as Estado_Pago
                FROM inscripciones i
                LEFT JOIN alumnos a ON i.id_alumno = a.rut
                LEFT JOIN empresa e ON i.id_empresa = e.id_empresa
                LEFT JOIN (
                    SELECT id_inscripcion, estado
                    FROM pagos
                    WHERE id_pago = (
                        SELECT id_pago
                        FROM pagos p2
                        WHERE p2.id_inscripcion = pagos.id_inscripcion
                        ORDER BY fecha_inscripcion DESC
                        LIMIT 1
                    )
                ) p ON i.id_inscripcion = p.id_inscripcion
                ORDER BY i.id_inscripcion DESC, i.fecha_inscripcion DESC
            """)
            results = cursor.fetchall()
            return results
        except Exception as e:
            print("Error al obtener inscripciones:", e)
            return []
        finally:
            cursor.close()
            conn.close()
    return []

def format_inscription_data(inscription):
    """
    Formatea los datos de inscripción para su visualización.
    La función espera que inscription sea una tupla con los datos en el orden de la query fetch_inscriptions
    """
    try:
        # Formatear fechas si existen
        fecha_inscripcion = inscription[5].strftime('%Y-%m-%d') if inscription[5] else ''
        fecha_termino = inscription[6].strftime('%Y-%m-%d') if inscription[6] else ''
        
        return {
            "ID": inscription[0],                    # id_inscripcion
            "N_Acta": inscription[1],               # numero_acta
            "RUT": inscription[2],                  # rut
            "Nombre_Completo": inscription[3],      # nombre_completo
            "ID_Curso": inscription[4],             # id_curso
            "F_Inscripcion": fecha_inscripcion,     # fecha_inscripcion formateada
            "F_Termino": fecha_termino,             # fecha_termino formateada
            "Año": inscription[7],                  # anio_inscripcion
            "Empresa": inscription[8],              # empresa
            "Codigo_Sence": inscription[9],         # ordenSence
            "Folio": inscription[10],               # idfolio
            "Estado_Pago": inscription[11] if inscription[11] else 'SIN PROCESAR'  # estado_pago
        }
    except Exception as e:
        print(f"Error formateando datos de inscripción: {e}")
        return None

def fetch_inscription_by_id(id_inscripcion):
    """Obtiene una inscripción por su ID"""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    id_inscripcion,
                    id_alumno,
                    id_curso,
                    fecha_inscripcion,
                    fecha_termino_condicional,
                    anio_inscripcion,
                    metodo_llegada,
                    id_empresa,
                    numero_acta,
                    ordenSence,
                    idfolio
                FROM inscripciones 
                WHERE id_inscripcion = %s
            """
            cursor.execute(query, (id_inscripcion,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'id_inscripcion': result[0],
                    'id_alumno': result[1],
                    'id_curso': result[2],
                    'fecha_inscripcion': result[3],
                    'fecha_termino_condicional': result[4],
                    'anio_inscripcion': result[5],
                    'metodo_llegada': result[6],
                    'id_empresa': result[7],
                    'numero_acta': result[8],
                    'ordenSence': result[9],
                    'idfolio': result[10]
                }
            return None
            
        except Exception as e:
            print(f"Error al obtener inscripción: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    return None

def update_inscription(id_inscripcion, **kwargs):
    """Actualiza una inscripción"""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Filtramos los campos que no son None
            fields_to_update = {k: v for k, v in kwargs.items() if v is not None}
            
            if not fields_to_update:
                return False, "No hay campos para actualizar"
            
            # Construimos la query dinámicamente
            query = "UPDATE inscripciones SET "
            query += ", ".join(f"{field} = %s" for field in fields_to_update.keys())
            query += " WHERE id_inscripcion = %s"
            
            # Preparamos los valores
            values = list(fields_to_update.values())
            values.append(id_inscripcion)
            
            cursor.execute(query, tuple(values))
            conn.commit()
            
            if cursor.rowcount == 0:
                return False, "No se encontró la inscripción para actualizar"
            
            return True, "Inscripción actualizada exitosamente"
            
        except Exception as e:
            print(f"Error en update_inscription: {str(e)}")
            return False, f"Error al actualizar: {str(e)}"
            
        finally:
            cursor.close()
            conn.close()
    
    return False, "Error de conexión con la base de datos"

def verify_and_create_empresa(empresa_id):
    """
    Verifica si una empresa existe y la crea si no existe.
    El ID y nombre de la empresa serán el mismo valor en mayúsculas.
    """
    try:
        # Convertir a mayúsculas
        empresa_id = empresa_id.strip().upper()
        
        # Consultar si la empresa existe
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id_empresa FROM empresa WHERE id_empresa = %s", (empresa_id,))
        exists = cursor.fetchone()
        
        if not exists:
            # Si no existe, crear la empresa
            cursor.execute("""
                INSERT INTO empresa (id_empresa, rut_empresa)
                VALUES (%s, %s)
            """, (empresa_id, ''))
            
            conn.commit()
        
        cursor.close()
        conn.close()
        return True, empresa_id
        
    except Exception as e:
        print(f"Error al verificar/crear empresa: {e}")
        return False, str(e)    

def validate_alumno_exists(rut):
    """Verifica si existe un alumno con el RUT especificado."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT rut FROM Alumnos WHERE rut = %s", (rut,))
            return cursor.fetchone() is not None
        except Exception as e:
            print("Error al validar alumno:", e)
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def validate_curso_exists(id_curso):
    """Verifica si existe un curso con el ID especificado."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id_curso FROM Cursos WHERE id_curso = %s", (id_curso,))
            return cursor.fetchone() is not None
        except Exception as e:
            print("Error al validar curso:", e)
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def delete_inscription(id_inscripcion):
    """
    Elimina una inscripción por su ID.
    
    Args:
        id_inscripcion: El ID de la inscripción a eliminar
        
    Returns:
        tuple: (bool, str) - (éxito, mensaje)
    """
    conn = connect_db()
    if not conn:
        return False, "Error de conexión con la base de datos."
    
    try:
        cursor = conn.cursor()
        
        # Primero verificamos si la inscripción existe
        cursor.execute("SELECT id_inscripcion FROM inscripciones WHERE id_inscripcion = %s", (id_inscripcion,))
        if not cursor.fetchone():
            return False, "La inscripción especificada no existe."
            
        # Si existe, procedemos a eliminarla
        cursor.execute("DELETE FROM inscripciones WHERE id_inscripcion = %s", (id_inscripcion,))
        conn.commit()
        
        return True, "Inscripción eliminada correctamente."
        
    except Exception as e:
        conn.rollback()
        return False, f"Error al eliminar la inscripción: {str(e)}"
    finally:
        cursor.close()
        conn.close()

def validate_duplicate_enrollment(id_alumno, id_curso, anio_inscripcion):
    """
    Verifica si ya existe una inscripción activa para el mismo alumno en el mismo curso y año.
    Retorna True si ya existe una inscripción, False si no existe.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_inscripcion 
                FROM Inscripciones 
                WHERE id_alumno = %s 
                AND id_curso = %s 
                AND anio_inscripcion = %s
                AND (fecha_termino_condicional IS NULL 
                     OR fecha_termino_condicional >= CURRENT_DATE)
            """, (id_alumno, id_curso, anio_inscripcion))
            
            return cursor.fetchone() is not None
        except Exception as e:
            print("Error al validar duplicados:", e)
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def get_course_duration(id_curso, conn):
    """
    Obtiene la duración en días del curso.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT duracionDias FROM Cursos WHERE id_curso = %s", (id_curso,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Error al obtener duración del curso: {e}")
        return None

def add_business_days(start_date, days):
    """
    Añade un número específico de días hábiles a una fecha.
    No cuenta sábados ni domingos.
    """
    business_days_to_add = days
    current_date = start_date
    while business_days_to_add > 0:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:  # 0-4 representa Lunes a Viernes
            business_days_to_add -= 1
    return current_date

def enroll_student(id_alumno, id_curso, numero_acta, fecha_inscripcion,
                  anio_inscripcion, metodo_llegada,
                  nombre_empresa=None, ordenSence=None, idfolio=None):
    """
    Registra una nueva inscripción en la base de datos.
    Calcula automáticamente la fecha de término basada en días hábiles.
    """
    # Validaciones básicas
    if not validate_alumno_exists(id_alumno):
        return False, "El alumno no existe en el sistema."
    
    if not validate_curso_exists(id_curso):
        return False, "El curso especificado no existe."
        
    if validate_duplicate_enrollment(id_alumno, id_curso, anio_inscripcion):
        return False, "El alumno ya está inscrito en este curso para el año especificado."

    # Procesar empresa
    id_empresa = None
    if nombre_empresa and metodo_llegada == "EMPRESA":
        print(f"Procesando empresa: {nombre_empresa}")
        id_empresa = get_or_create_empresa(nombre_empresa)
        if id_empresa is None:
            return False, "Error al procesar la empresa."
    
    conn = connect_db()
    if not conn:
        return False, "Error de conexión con la base de datos."
    
    try:
        # Obtener la duración del curso
        duracion_dias = get_course_duration(id_curso, conn)
        if duracion_dias is None:
            return False, "No se pudo obtener la duración del curso."

        # Convertir fecha_inscripcion a objeto date si es string
        if isinstance(fecha_inscripcion, str):
            fecha_inscripcion = datetime.strptime(fecha_inscripcion, '%Y-%m-%d').date()

        # Calcular fecha de término
        fecha_termino = add_business_days(fecha_inscripcion, duracion_dias)

        cursor = conn.cursor()
        query = """
            INSERT INTO inscripciones (
                id_alumno, id_curso, numero_acta,
                fecha_inscripcion, fecha_termino_condicional,
                anio_inscripcion, metodo_llegada, id_empresa,
                ordenSence, idfolio
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        values = (
            id_alumno, id_curso, numero_acta,
            fecha_inscripcion, fecha_termino,
            anio_inscripcion, metodo_llegada, id_empresa,
            ordenSence, idfolio
        )
        
        cursor.execute(query, values)
        conn.commit()
        return True, "Inscripción realizada exitosamente."
        
    except Exception as e:
        conn.rollback()
        return False, f"Error al realizar la inscripción: {str(e)}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        conn.close()

def fetch_inscriptions_filtered(rut=None, act_number=None, nombre=None, fecha_inicio=None, fecha_fin=None):
    """
    Obtiene las inscripciones con información detallada (mismas columnas que fetch_inscriptions)
    filtrando por:
      - RUT del alumno (a.rut)
      - Nº Acta (i.numero_acta)
      - Nombre (a.nombre y/o a.apellido, búsqueda parcial)
      - Fecha de inscripción o rango de fechas (i.fecha_inscripcion)
    """
    conn = connect_db()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                i.id_inscripcion as ID,
                i.numero_acta as N_Acta,
                a.rut as RUT,
                CASE 
                    WHEN a.nombre IS NOT NULL AND a.apellido IS NOT NULL 
                    THEN CONCAT(a.nombre, ' ', a.apellido)
                    ELSE a.nombre 
                END as Nombre_Completo,
                i.id_curso as ID_Curso,
                i.fecha_inscripcion as F_Inscripcion,
                i.fecha_termino_condicional as F_Termino,
                i.anio_inscripcion as Año,
                CASE 
                    WHEN i.id_empresa IS NOT NULL THEN e.id_empresa 
                    ELSE 'Particular'
                END as Empresa,
                i.ordenSence as Codigo_Sence,
                i.idfolio as Folio,
                COALESCE(
                    CASE 
                        WHEN p.estado IS NULL THEN 'SIN PROCESAR'
                        ELSE UPPER(p.estado)
                    END,
                    'SIN PROCESAR'
                ) as Estado_Pago
            FROM inscripciones i
            LEFT JOIN alumnos a ON i.id_alumno = a.rut
            LEFT JOIN empresa e ON i.id_empresa = e.id_empresa
            LEFT JOIN (
                SELECT id_inscripcion, estado
                FROM pagos
                WHERE id_pago = (
                    SELECT id_pago
                    FROM pagos p2
                    WHERE p2.id_inscripcion = pagos.id_inscripcion
                    ORDER BY fecha_inscripcion DESC
                    LIMIT 1
                )
            ) p ON i.id_inscripcion = p.id_inscripcion
            WHERE 1=1
        """
        params = []

        # Filtro por RUT
        if rut:
            query += " AND a.rut = %s"
            params.append(rut)

        # Filtro por Nº Acta
        if act_number:
            query += " AND i.numero_acta = %s"
            params.append(act_number)

        # Filtro por Nombre (en a.nombre o a.apellido, búsqueda parcial)
        if nombre:
            query += " AND (a.nombre ILIKE %s OR a.apellido ILIKE %s)"
            like_param = f"%{nombre}%"
            params.extend([like_param, like_param])

        # Filtro por fecha (única o rango) en i.fecha_inscripcion
        if fecha_inicio and fecha_fin:
            query += " AND i.fecha_inscripcion BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
        elif fecha_inicio:
            query += " AND i.fecha_inscripcion = %s"
            params.append(fecha_inicio)

        query += " ORDER BY i.fecha_inscripcion DESC, i.id_inscripcion DESC"

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print("Error al obtener inscripciones filtradas:", e)
        return []
    finally:
        cursor.close()
        conn.close()

def fetch_inscription_details(id_inscripcion):
    """
    Obtiene los detalles completos de una inscripción, incluyendo información
    del alumno, curso y estado de pagos.
    
    Returns:
        dict: Diccionario con toda la información de la inscripción o None si no se encuentra
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    i.id_inscripcion,
                    i.numero_acta,
                    CONCAT(a.nombre, ' ', a.apellido) as nombre_alumno,
                    c.nombre_curso,
                    c.valor as valor_curso,
                    i.fecha_inscripcion,
                    i.fecha_termino_condicional,
                    i.anio_inscripcion,
                    i.metodo_llegada,
                    COALESCE(e.id_empresa, 'Particular') as empresa,
                    i.ordenSence,
                    i.idfolio,
                    -- Información de pagos
                    p.id_pago,
                    p.tipo_pago,
                    p.modalidad_pago,
                    p.fecha_inscripcion as fecha_pago,
                    p.fecha_final as fecha_pago_final,
                    p.num_cuotas,
                    p.valor_total,
                    p.estado as estado_pago,
                    -- Contadores y sumas
                    COUNT(DISTINCT p.id_pago) as total_pagos,
                    SUM(CASE WHEN p.estado = 'pendiente' THEN p.valor_total ELSE 0 END) as monto_pendiente,
                    SUM(CASE WHEN p.estado = 'pagado' THEN p.valor_total ELSE 0 END) as monto_pagado,
                    -- Información de cuotas
                    COUNT(DISTINCT cu.id_cuota) as total_cuotas,
                    SUM(CASE WHEN cu.estado_cuota = 'pendiente' THEN 1 ELSE 0 END) as cuotas_pendientes,
                    SUM(CASE WHEN cu.estado_cuota = 'pagada' THEN 1 ELSE 0 END) as cuotas_pagadas,
                    SUM(CASE WHEN cu.estado_cuota = 'vencida' THEN 1 ELSE 0 END) as cuotas_vencidas,
                    -- Información de contribuciones
                    SUM(CASE WHEN co.tipo_contribuyente = 'alumno' THEN co.monto_contribuido ELSE 0 END) as monto_alumno,
                    SUM(CASE WHEN co.tipo_contribuyente = 'empresa' THEN co.monto_contribuido ELSE 0 END) as monto_empresa,
                    SUM(CASE WHEN co.tipo_contribuyente = 'sence' THEN co.monto_contribuido ELSE 0 END) as monto_sence
                FROM inscripciones i 
                LEFT JOIN alumnos a ON i.id_alumno = a.rut
                LEFT JOIN cursos c ON i.id_curso = c.id_curso
                LEFT JOIN empresa e ON i.id_empresa = e.id_empresa
                LEFT JOIN pagos p ON i.id_inscripcion = p.id_inscripcion
                LEFT JOIN cuotas cu ON p.id_pago = cu.id_pago
                LEFT JOIN contribuciones co ON p.id_pago = co.id_pago
                WHERE i.id_inscripcion = %s
                GROUP BY 
                    i.id_inscripcion, i.numero_acta, a.nombre, a.apellido,
                    c.nombre_curso, c.valor, i.fecha_inscripcion, 
                    i.fecha_termino_condicional, i.anio_inscripcion,
                    i.metodo_llegada, e.id_empresa, i.ordenSence, i.idfolio,
                    p.id_pago, p.tipo_pago, p.modalidad_pago, p.fecha_inscripcion,
                    p.fecha_final, p.num_cuotas, p.valor_total, p.estado
            """, (id_inscripcion,))
            
            result = cursor.fetchone()
            
            if result:
                # Calcular estado general de pago
                estado_general = 'SIN PROCESAR'
                if result[20] > 0:  # Si hay pagos registrados
                    if result[22] == result[18]:  # Si monto_pagado == valor_total
                        estado_general = 'PAGADO'
                    elif result[21] > 0:  # Si hay monto_pendiente
                        estado_general = 'PENDIENTE'
                    if result[26] > 0:  # Si hay cuotas vencidas
                        estado_general = 'ATRASADO'

                return {
                    # Información básica
                    'id_inscripcion': result[0],
                    'numero_acta': result[1],
                    'nombre_alumno': result[2],
                    'nombre_curso': result[3],
                    'valor_curso': result[4],
                    'fecha_inscripcion': result[5],
                    'fecha_termino': result[6],
                    'anio': result[7],
                    'metodo_llegada': result[8],
                    'empresa': result[9],
                    'orden_sence': result[10],
                    'folio': result[11],
                    
                    # Información del último pago
                    'ultimo_pago': {
                        'id_pago': result[12],
                        'tipo_pago': result[13],
                        'modalidad_pago': result[14],
                        'fecha_pago': result[15],
                        'fecha_final': result[16],
                        'num_cuotas': result[17],
                        'valor_total': result[18],
                        'estado': result[19]
                    },
                    
                    # Resumen de pagos
                    'resumen_pagos': {
                        'total_pagos': result[20],
                        'monto_pendiente': result[21],
                        'monto_pagado': result[22],
                        'estado_general': estado_general
                    },
                    
                    # Resumen de cuotas
                    'resumen_cuotas': {
                        'total_cuotas': result[23],
                        'cuotas_pendientes': result[24],
                        'cuotas_pagadas': result[25],
                        'cuotas_vencidas': result[26]
                    },
                    
                    # Resumen de contribuciones
                    'contribuciones': {
                        'monto_alumno': result[27],
                        'monto_empresa': result[28],
                        'monto_sence': result[29]
                    }
                }
            else:
                print(f"No se encontró inscripción con ID {id_inscripcion}")
                return None
                
        except Exception as e:
            print(f"Error al obtener detalles de inscripción: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    return None

def fetch_active_students():
    """
    Retorna todos los alumnos que están actualmente cursando.
    Incluye número de acta, nombre completo, RUT y ID del curso.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                SELECT DISTINCT 
                    i.numero_acta,
                    CONCAT(a.nombre, ' ', a.apellido) as nombre_completo,
                    a.rut,
                    i.id_curso
                FROM inscripciones i
                INNER JOIN alumnos a ON i.id_alumno = a.rut
                WHERE i.fecha_termino_condicional >= CURDATE() 
                OR i.fecha_termino_condicional IS NULL
                ORDER BY nombre_completo
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"Error al obtener alumnos activos: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    return []

def fetch_payments_by_criteria(id_inscripcion=None, rut=None, nombre_completo=None):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        query = """
            SELECT DISTINCT p.* 
            FROM pagos p
            INNER JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
            INNER JOIN alumnos a ON i.id_alumno = a.rut
            WHERE 1=1
        """
        params = []

        if id_inscripcion:
            query += " AND p.id_inscripcion = %s"
            params.append(id_inscripcion)
        if rut:
            query += " AND a.rut = %s"
            params.append(rut)
        if nombre_completo:
            query += " AND CONCAT(a.nombre, ' ', a.apellido) LIKE %s"
            params.append(f"%{nombre_completo}%")

        cursor.execute(query, params)
        payments = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        columns = [desc[0] for desc in cursor.description]
        result = []
        for row in payments:
            result.append(dict(zip(columns, row)))

        cursor.close()
        conn.close()
        return result

    except Exception as e:
        print(f"Error en fetch_payments_by_criteria: {e}")
        raise

def update_current_students_table():
    """Actualiza la tabla current_alumnos basado en las fechas de inscripción"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Obtenemos las inscripciones inactivas una sola vez para mejorar rendimiento
        cursor.execute("""
            WITH inscripciones_inactivas AS (
                SELECT i.id_inscripcion 
                FROM inscripciones i 
                WHERE i.fecha_termino_condicional < CURDATE()
            )
            DELETE ca, cah
            FROM current_alumnos ca
            LEFT JOIN current_alumnos_history cah ON ca.id_inscripcion = cah.id_inscripcion
            WHERE ca.id_inscripcion IN (SELECT id_inscripcion FROM inscripciones_inactivas)
        """)
        
        # Insertar nuevos alumnos activos usando una subconsulta más eficiente
        cursor.execute("""
            INSERT INTO current_alumnos 
                (id_inscripcion, asistencia_current, metodo_contacto, fecha_actualizacion)
            SELECT 
                i.id_inscripcion, 
                0,
                NULL,
                NULL
            FROM inscripciones i
            LEFT JOIN current_alumnos ca ON i.id_inscripcion = ca.id_inscripcion
            WHERE i.fecha_inscripcion <= CURDATE() 
            AND i.fecha_termino_condicional >= CURDATE()
            AND ca.id_inscripcion IS NULL
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error actualizando tabla current_alumnos: {e}")
        return False

def update_student_contact(id_inscripcion, asistencia, metodo, observacion):
    """Actualiza el contacto de un alumno y registra en el historial"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Verificar primero que la inscripción existe y está activa
        cursor.execute("""
            SELECT 1 FROM inscripciones 
            WHERE id_inscripcion = %s 
            AND fecha_termino_condicional >= CURDATE()
            AND fecha_inscripcion <= CURDATE()
        """, (id_inscripcion,))
        
        if not cursor.fetchone():
            raise ValueError("La inscripción no existe o no está activa")
            
        # Transacción para asegurar la integridad de los datos
        cursor.execute("START TRANSACTION")
        try:
            # Registrar en el historial
            cursor.execute("""
                INSERT INTO current_alumnos_history 
                    (id_inscripcion, asistencia_current, metodo_contacto, observacion)
                VALUES (%s, %s, %s, %s)
            """, (id_inscripcion, asistencia, metodo, observacion))
            
            # Actualizar la tabla current_alumnos
            cursor.execute("""
                UPDATE current_alumnos
                SET asistencia_current = %s,
                    metodo_contacto = %s,
                    observacion = %s,
                    fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE id_inscripcion = %s
            """, (asistencia, metodo, observacion, id_inscripcion))
            
            cursor.execute("COMMIT")
        except:
            cursor.execute("ROLLBACK")
            raise
            
        conn.close()
    except Exception as e:
        print(f"Error actualizando contacto: {e}")
        raise

def fetch_active_students():
    """Obtiene la lista de alumnos activos con su información"""
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            WITH alumnos_activos AS (
                SELECT i.id_inscripcion
                FROM inscripciones i
                WHERE i.fecha_termino_condicional >= CURDATE()
                AND i.fecha_inscripcion <= CURDATE()
            )
            SELECT 
                i.id_inscripcion,
                a.rut,
                CONCAT(a.nombre, ' ', a.apellido) as nombre_completo,
                c.nombre_curso,
                i.fecha_inscripcion,
                i.fecha_termino_condicional,
                COALESCE(ca.asistencia_current, 0) as asistencia_current,
                ca.fecha_actualizacion,
                ca.metodo_contacto,
                ca.observacion,
                DATEDIFF(CURDATE(), ca.fecha_actualizacion) as dias_ultimo_contacto
            FROM alumnos_activos aa
            INNER JOIN inscripciones i ON aa.id_inscripcion = i.id_inscripcion
            INNER JOIN alumnos a ON i.id_alumno = a.rut
            INNER JOIN cursos c ON i.id_curso = c.id_curso
            LEFT JOIN current_alumnos ca ON i.id_inscripcion = ca.id_inscripcion
            ORDER BY 
                CASE 
                    WHEN ca.fecha_actualizacion IS NULL THEN 1 
                    ELSE 0 
                END,
                ca.fecha_actualizacion DESC
        """
        
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error obteniendo alumnos activos: {e}")
        raise
# =======================================
#             PAGOS
# =======================================

def fetch_payments():
    conn = connect_db()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                p.id_pago,                    -- 0
                p.id_inscripcion,             -- 1
                p.tipo_pago,                  -- 2
                p.modalidad_pago,             -- 3
                p.fecha_inscripcion,          -- 4
                p.fecha_final,                -- 5
                p.num_cuotas,                 -- 6
                p.valor_total,                -- 7
                p.estado,                     -- 8
                i.numero_acta,                -- 9
                CONCAT(a.nombre, ' ', a.apellido) AS nombre_alumno,  -- 10
                c.nombre_curso,               -- 11
                COALESCE(SUM(CASE 
                    WHEN cuo.estado_cuota = 'pagada' 
                    THEN 1 
                    ELSE 0 
                END), 0) AS cuotas_pagadas,  -- 12
                p.estado_orden,               -- 13
                p.numero_orden,               -- 14
                a.rut                         -- 15
            FROM pagos p
            LEFT JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
            LEFT JOIN alumnos a ON i.id_alumno = a.rut
            LEFT JOIN cursos c ON i.id_curso = c.id_curso
            LEFT JOIN cuotas cuo ON p.id_pago = cuo.id_pago
            GROUP BY 
                p.id_pago, 
                p.id_inscripcion,
                p.tipo_pago,
                p.modalidad_pago,
                p.fecha_inscripcion,
                p.fecha_final,
                p.num_cuotas,
                p.valor_total,
                p.estado,
                i.numero_acta,
                nombre_alumno,
                c.nombre_curso,
                p.estado_orden,
                p.numero_orden,
                a.rut
            ORDER BY p.fecha_inscripcion DESC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except Exception as e:
        print("Error al obtener pagos:", e)
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def fetch_pending_payments():
    conn = connect_db()
    if not conn:
        return [], {'total': 0, 'pagare_pendiente': 0}

    try:
        cursor = conn.cursor()
        
        # First, get the summary counts
        summary_query = """
            SELECT 
                COUNT(*) as total_pendientes,
                SUM(CASE WHEN tipo_pago = 'pagare' THEN 1 ELSE 0 END) as total_pagare_pendiente
            FROM pagos 
            WHERE estado = 'pendiente'
        """
        cursor.execute(summary_query)
        summary_result = cursor.fetchone()
        summary = {
            'total': summary_result[0],
            'pagare_pendiente': summary_result[1]
        }

        # Then, get the detailed payment information
        detail_query = """
            SELECT 
                p.id_pago,
                p.id_inscripcion,
                p.tipo_pago,
                p.modalidad_pago,
                p.fecha_inscripcion,
                p.fecha_final,
                p.num_cuotas,
                p.valor_total,
                p.estado,
                i.numero_acta,
                CONCAT(a.nombre, ' ', a.apellido) AS nombre_alumno,
                c.nombre_curso,
                COALESCE(SUM(CASE WHEN cuo.estado_cuota = 'pagada' THEN 1 ELSE 0 END), 0) AS cuotas_pagadas
            FROM pagos p
            LEFT JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
            LEFT JOIN alumnos a ON i.id_alumno = a.rut
            LEFT JOIN cursos c ON i.id_curso = c.id_curso
            LEFT JOIN cuotas cuo ON p.id_pago = cuo.id_pago
            WHERE p.estado = 'pendiente'
            GROUP BY p.id_pago
            ORDER BY p.fecha_inscripcion DESC
        """
        cursor.execute(detail_query)
        results = cursor.fetchall()
        return results, summary
    except Exception as e:
        print("Error al obtener pagos pendientes:", e)
        return [], {'total': 0, 'pagare_pendiente': 0}
    finally:
        cursor.close()
        conn.close()

def fetch_alumno_curso_inscripcion(id_inscripcion):
    """
    Retorna la info esencial de la inscripción, alumno y curso
    """
    conn = connect_db()
    if not conn:
        return None

    try:
        with conn.cursor(dictionary=True) as cursor:
            query = """
                SELECT 
                    i.id_inscripcion,
                    i.numero_acta,
                    i.fecha_inscripcion,
                    i.anio_inscripcion,
                    a.rut AS rut_alumno,
                    a.direccion AS direccion_alumno,
                    CONCAT(a.nombre, ' ', a.apellido) AS nombre_alumno,
                    c.nombre_curso,
                    c.valor AS valor_curso
                FROM inscripciones i
                INNER JOIN alumnos a ON i.id_alumno = a.rut
                INNER JOIN cursos c ON i.id_curso = c.id_curso
                WHERE i.id_inscripcion = %s
            """
            cursor.execute(query, (id_inscripcion,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "id_inscripcion": result["id_inscripcion"],
                    "numero_acta": result["numero_acta"],
                    "fecha_inscripcion": result["fecha_inscripcion"],
                    "anio_inscripcion": result["anio_inscripcion"],
                    "rut_alumno": result["rut_alumno"],
                    "direccion_alumno": result["direccion_alumno"],
                    "nombre_alumno": result["nombre_alumno"],
                    "nombre_curso": result["nombre_curso"],
                    "valor_curso": float(result["valor_curso"]) if result["valor_curso"] else 0.0
                }
            return None
            
    except Exception as e:
        print(f"Error en fetch_alumno_curso_inscripcion: {e}")
        return None
    finally:
        conn.close()

def insert_payment(id_inscripcion, tipo_pago, modalidad_pago, valor_total, num_cuotas=1, fecha_pago=None):
    """
    Inserta un nuevo pago (1 a 1 por id_inscripcion) y, si es "pagare",
    crea las cuotas en estado 'pendiente', con vencimientos calculados desde `fecha_pago`.
    """
    conn = connect_db()
    if not conn:
        return (None, None)

    try:
        with conn.cursor() as cursor:
            # Verificar que no exista un pago previo para esta inscripción
            check_query = """
                SELECT id_pago 
                FROM pagos
                WHERE id_inscripcion = %s
                LIMIT 1
            """
            cursor.execute(check_query, (id_inscripcion,))
            existing = cursor.fetchone()
            if existing:
                raise Exception("Ya existe un pago registrado para esta inscripción (solo se permite 1 a 1).")

            # Si no se proporciona `fecha_pago`, usar la fecha actual
            if not fecha_pago:
                fecha_pago = datetime.now()

            # Insertar el pago principal
            insert_pago_query = """
                INSERT INTO pagos 
                (id_inscripcion, tipo_pago, modalidad_pago, fecha_inscripcion, fecha_pago,
                 num_cuotas, valor_total, estado)
                VALUES (%s, %s, %s, NOW(), %s, %s, %s, 'pendiente')
            """
            cursor.execute(insert_pago_query, (
                id_inscripcion,
                tipo_pago,
                modalidad_pago,
                fecha_pago,
                num_cuotas,
                valor_total
            ))
            
            id_pago = cursor.lastrowid
            id_pagare = None
            
            # Si es pagaré, generar las cuotas
            if tipo_pago == 'pagare':
                valor_cuota = valor_total / num_cuotas
                for i in range(num_cuotas):
                    # Calcular la fecha de vencimiento de cada cuota
                    fecha_vencimiento = fecha_pago + timedelta(days=(30 * (i + 1)))

                    insert_cuota_query = """
                        INSERT INTO cuotas 
                        (id_pago, nro_cuota, valor_cuota, fecha_vencimiento, estado_cuota)
                        VALUES (%s, %s, %s, %s, 'pendiente')
                    """
                    cursor.execute(insert_cuota_query, (
                        id_pago,
                        i + 1,
                        valor_cuota,
                        fecha_vencimiento
                    ))
                
                # Insertar en tabla pagares
                insert_pagare_query = """
                    INSERT INTO pagares (id_pago) 
                    VALUES (%s)
                """
                cursor.execute(insert_pagare_query, (id_pago,))
                id_pagare = cursor.lastrowid

            conn.commit()
            return (id_pago, id_pagare)

    except Exception as e:
        print(f"Error en insert_payment: {e}")
        conn.rollback()
        return (None, None)
    finally:
        conn.close()

def insert_payment_contribution(id_pago, tipo_contribuyente, monto):
    """
    Registra una contribución al pago (SENCE, empresa o alumno).
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO contribuciones 
                (id_pago, tipo_contribuyente, monto_contribuido)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (id_pago, tipo_contribuyente, monto))
            conn.commit()
            return True
        except Exception as e:
            print("Error al insertar contribución:", e)
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def update_cuota(id_cuota, valor_cuota=None, fecha_vencimiento=None):
    """
    Actualiza campos de la cuota y registra en el historial si se marca como pagada.
    Retorna una tupla (éxito, numero_ingreso).
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Obtenemos información completa de la cuota
            cursor.execute("""
                SELECT c.estado_cuota, c.numero_ingreso, c.valor_cuota,
                       c.id_pago, p.id_inscripcion, a.rut,
                       CONCAT(a.nombre, ' ', a.apellido) as nombre_completo,
                       c.nro_cuota
                FROM cuotas c
                JOIN pagos p ON c.id_pago = p.id_pago
                JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
                JOIN alumnos a ON i.id_alumno = a.rut
                WHERE c.id_cuota = %s
            """, (id_cuota,))
            
            result = cursor.fetchone()
            if not result:
                return False, None
            
            (estado_actual, num_ingreso_actual, valor_actual, 
             id_pago, id_inscripcion, rut, nombre_alumno, nro_cuota) = result
            
            # Construimos campos a actualizar
            fields = []
            params = []
            
            if valor_cuota is not None:
                fields.append("valor_cuota = %s")
                params.append(valor_cuota)
                valor_a_usar = valor_cuota
            else:
                valor_a_usar = valor_actual

            if fecha_vencimiento is not None:
                fields.append("fecha_vencimiento = %s")
                params.append(fecha_vencimiento)
            
            # Si la cuota se está marcando como pagada y no tiene número de ingreso
            if estado_actual != 'pagada' and num_ingreso_actual is None:
                # Obtenemos el último número de ingreso
                cursor.execute("""
                    SELECT MAX(CAST(SUBSTRING(numero_ingreso, 4) AS UNSIGNED))
                    FROM cuotas 
                    WHERE numero_ingreso IS NOT NULL
                """)
                last_num = cursor.fetchone()[0] or 0
                new_num = last_num + 1
                new_num_ingreso = f"IN-{new_num:06d}"
                
                fields.append("numero_ingreso = %s")
                params.append(new_num_ingreso)
                fields.append("estado_cuota = 'pagada'")
                fields.append("fecha_pago = CURRENT_TIMESTAMP")
                
                # Registrar en historial
                cursor.execute("""
                    INSERT INTO historial_pagos (
                        tipo_pago, id_pago, id_cuota, id_inscripcion,
                        rut_alumno, nombre_alumno, monto, 
                        numero_ingreso, detalle
                    ) VALUES (
                        'pagare', %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    id_pago, id_cuota, id_inscripcion, rut, 
                    nombre_alumno, valor_a_usar, new_num_ingreso,
                    f'Pago de cuota {nro_cuota}'
                ))
            else:
                new_num_ingreso = num_ingreso_actual
            
            # Si no hay campos a actualizar
            if not fields:
                cursor.close()
                conn.close()
                return True, new_num_ingreso
            
            set_clause = ", ".join(fields)
            query = f"UPDATE cuotas SET {set_clause} WHERE id_cuota = %s"
            params.append(id_cuota)
            
            cursor.execute(query, params)
            conn.commit()
            cursor.close()
            conn.close()
            return True, new_num_ingreso
            
        except Exception as e:
            print("Error en update_cuota:", e)
            if conn:
                conn.rollback()
                conn.close()
            return False, None
    return False, None

def fetch_cuotas_by_pago(id_pago):
    """
    Obtiene todas las cuotas asociadas a un pago, incluyendo el número de ingreso.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_cuota, id_pago, nro_cuota, valor_cuota, 
                       fecha_vencimiento, fecha_pago, estado_cuota, numero_ingreso
                FROM cuotas 
                WHERE id_pago = %s 
                ORDER BY nro_cuota
            """, (id_pago,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print("Error en fetch_cuotas_by_pago:", e)
            conn.close()
            return None
    return None

def register_quota_payment(id_cuota):
    """
    Registra el pago de una cuota y genera su número de ingreso.
    Retorna una tupla (éxito, numero_ingreso).
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Obtenemos información completa de la cuota
            cursor.execute("""
                SELECT c.estado_cuota, c.numero_ingreso, c.valor_cuota,
                       c.id_pago, p.id_inscripcion, i.id_alumno as rut,
                       CONCAT(a.nombre, ' ', a.apellido) as nombre_completo,
                       c.nro_cuota
                FROM cuotas c
                JOIN pagos p ON c.id_pago = p.id_pago
                JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
                JOIN alumnos a ON i.id_alumno = a.rut
                WHERE c.id_cuota = %s
            """, (id_cuota,))
            
            result = cursor.fetchone()
            if not result:
                return False, None
            
            estado_actual, num_ingreso_actual, valor_cuota, id_pago, id_inscripcion, rut, nombre_alumno, nro_cuota = result
            
            if estado_actual == 'pagada' and num_ingreso_actual:
                return True, num_ingreso_actual
            
            # Generamos nuevo número de ingreso
            cursor.execute("""
                SELECT MAX(CAST(SUBSTRING(numero_ingreso, 4) AS UNSIGNED))
                FROM cuotas 
                WHERE numero_ingreso IS NOT NULL
            """)
            last_num = cursor.fetchone()[0] or 0
            new_num = last_num + 1
            new_num_ingreso = f"IN-{new_num:06d}"
            
            # Actualizamos la cuota
            cursor.execute("""
                UPDATE cuotas 
                SET estado_cuota = 'pagada',
                    fecha_pago = CURRENT_TIMESTAMP,
                    numero_ingreso = %s
                WHERE id_cuota = %s
            """, (new_num_ingreso, id_cuota))
            
            # Registramos en el historial de pagos
            cursor.execute("""
                INSERT INTO historial_pagos (
                    fecha_registro,
                    tipo_pago,
                    id_inscripcion,
                    id_pago,
                    id_cuota,
                    rut_alumno,
                    nombre_alumno,
                    monto,
                    numero_ingreso,
                    detalle
                ) VALUES (
                    CURRENT_TIMESTAMP,
                    'pagare',
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                id_inscripcion,
                id_pago,
                id_cuota,
                rut,
                nombre_alumno,
                valor_cuota,
                new_num_ingreso,
                f'Pago de cuota {nro_cuota}'
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True, new_num_ingreso
            
        except Exception as e:
            print("Error en register_quota_payment:", e)
            if conn:
                conn.rollback()
                conn.close()
            return False, None
    return False, None

def get_payment_completion_info(id_pago):
    """
    Obtiene información sobre el estado de completitud del pago.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    p.id_pago,
                    p.valor_total,
                    p.fecha_inscripcion,
                    p.fecha_final,
                    p.estado,
                    COUNT(c.id_cuota) as total_cuotas,
                    SUM(CASE WHEN c.estado_cuota = 'pagada' THEN 1 ELSE 0 END) as cuotas_pagadas,
                    MIN(CASE WHEN c.estado_cuota = 'pendiente' 
                        THEN c.fecha_vencimiento END) as proxima_cuota
                FROM pagos p
                LEFT JOIN cuotas c ON p.id_pago = c.id_pago
                WHERE p.id_pago = %s
                GROUP BY p.id_pago, p.valor_total, p.fecha_inscripcion, 
                         p.fecha_final, p.estado
            """
            cursor.execute(query, (id_pago,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'id_pago': result[0],
                    'valor_total': result[1],
                    'fecha_inscripcion': result[2],
                    'fecha_final': result[3],
                    'estado': result[4],
                    'total_cuotas': result[5],
                    'cuotas_pagadas': result[6],
                    'proxima_cuota': result[7]
                }
            return None
        except Exception as e:
            print("Error al obtener información de completitud:", e)
            return None
        finally:
            cursor.close()
            conn.close()
    return None

def get_payment_details(id_pago):
    """
    Obtiene los detalles completos de un pago incluyendo cuotas y contribuciones.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Obtener información del pago
            query_pago = """
                SELECT p.*, i.numero_acta, 
                       CONCAT(a.nombre, ' ', a.apellido) as nombre_alumno,
                       c.nombre_curso
                FROM pagos p
                LEFT JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
                LEFT JOIN alumnos a ON i.id_alumno = a.rut
                LEFT JOIN cursos c ON i.id_curso = c.id_curso
                WHERE p.id_pago = %s
            """
            cursor.execute(query_pago, (id_pago,))
            pago = cursor.fetchone()
            
            # Obtener cuotas
            query_cuotas = """
                SELECT *
                FROM cuotas
                WHERE id_pago = %s
                ORDER BY nro_cuota
            """
            cursor.execute(query_cuotas, (id_pago,))
            cuotas = cursor.fetchall()
            
            # Obtener contribuciones
            query_contribuciones = """
                SELECT *
                FROM contribuciones
                WHERE id_pago = %s
            """
            cursor.execute(query_contribuciones, (id_pago,))
            contribuciones = cursor.fetchall()
            
            return {
                'pago': pago,
                'cuotas': cuotas,
                'contribuciones': contribuciones
            }
        except Exception as e:
            print("Error al obtener detalles del pago:", e)
            return None
        finally:
            cursor.close()
            conn.close()
    return None

def cancel_payment(id_pago):
    """
    Cancela un pago y sus cuotas asociadas.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Actualizar estado del pago
            query_pago = """
                UPDATE pagos 
                SET estado = 'cancelado',
                    fecha_final = NOW()
                WHERE id_pago = %s
            """
            cursor.execute(query_pago, (id_pago,))
            
            # Actualizar estado de las cuotas
            query_cuotas = """
                UPDATE cuotas 
                SET estado_cuota = 'cancelado'
                WHERE id_pago = %s
                AND estado_cuota = 'pendiente'
            """
            cursor.execute(query_cuotas, (id_pago,))
            
            conn.commit()
            return True
        except Exception as e:
            print("Error al cancelar pago:", e)
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def get_pending_quotas():
    """
    Obtiene todas las cuotas pendientes ordenadas por fecha de vencimiento.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                SELECT c.*, p.id_inscripcion, 
                       CONCAT(a.nombre, ' ', a.apellido) as nombre_alumno,
                       i.numero_acta
                FROM cuotas c
                JOIN pagos p ON c.id_pago = p.id_pago
                JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
                JOIN alumnos a ON i.id_alumno = a.rut
                WHERE c.estado_cuota = 'pendiente'
                ORDER BY c.fecha_vencimiento
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print("Error al obtener cuotas pendientes:", e)
            return []
        finally:
            cursor.close()
            conn.close()
    return []

def get_payment_summary_by_dates(fecha_inicio, fecha_fin):
    """
    Obtiene un resumen de pagos entre fechas específicas.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    COUNT(*) as total_pagos,
                    SUM(valor_total) as monto_total,
                    SUM(CASE WHEN estado = 'pagado' THEN valor_total ELSE 0 END) as monto_pagado,
                    SUM(CASE WHEN estado = 'pendiente' THEN valor_total ELSE 0 END) as monto_pendiente,
                    COUNT(CASE WHEN tipo_pago = 'contado' THEN 1 END) as pagos_contado,
                    COUNT(CASE WHEN tipo_pago = 'pagare' THEN 1 END) as pagos_pagare
                FROM pagos
                WHERE fecha_inscripcion BETWEEN %s AND %s
            """
            cursor.execute(query, (fecha_inicio, fecha_fin))
            return cursor.fetchone()
        except Exception as e:
            print("Error al obtener resumen de pagos:", e)
            return None
        finally:
            cursor.close()
            conn.close()
    return None

def register_contado_payment(payment_id):
    """
    Registra un pago al contado y lo añade al historial
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Obtenemos la información necesaria del pago incluyendo el id_inscripcion
            cursor.execute("""
                SELECT p.valor_total, p.id_inscripcion, a.rut, CONCAT(a.nombre, ' ', a.apellido) as nombre_completo
                FROM pagos p
                JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
                JOIN alumnos a ON i.id_alumno = a.rut
                WHERE p.id_pago = %s 
                AND p.tipo_pago = 'contado' 
                AND p.estado = 'pendiente'
            """, (payment_id,))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            monto, id_inscripcion, rut, nombre = result
            
            # Actualizar el pago
            cursor.execute("""
                UPDATE pagos 
                SET estado = 'pagado',
                    fecha_pago = CURRENT_TIMESTAMP
                WHERE id_pago = %s
            """, (payment_id,))
            
            if cursor.rowcount == 0:
                raise Exception("No se pudo actualizar el pago")
            
            # Registrar en historial incluyendo id_inscripcion
            cursor.execute("""
                INSERT INTO historial_pagos (
                    tipo_pago, id_pago, id_inscripcion, 
                    rut_alumno, nombre_alumno, monto, detalle
                ) VALUES (
                    'contado', %s, %s, %s, %s, %s, 'Pago al contado registrado'
                )
            """, (payment_id, id_inscripcion, rut, nombre, monto))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error en register_contado_payment: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    return False

def get_payment_history():
    """
    Obtiene el historial completo de pagos ordenado por fecha
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    fecha_registro,
                    tipo_pago,
                    rut_alumno,
                    nombre_alumno,
                    monto,
                    CASE 
                        WHEN tipo_pago = 'pagare' THEN numero_ingreso
                        ELSE ''
                    END as numero_ingreso,
                    detalle
                FROM historial_pagos
                ORDER BY fecha_registro DESC
            """)
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error obteniendo historial: {e}")
            if conn:
                conn.close()
            return None
    return None

def search_pagare_payments(search_type, value):
    """
    search_type: 'inscripcion', 'rut', 'pago'
    value: valor buscado
    Devuelve los pagos que sean tipo 'pagare', sin filtrar por estado,
    para que aparezcan aunque se hayan pagado cuotas parcial o totalmente.
    """
    conn = connect_db()
    results = []
    if conn:
        try:
            cursor = conn.cursor()
            base_query = """
                SELECT 
                    p.id_pago,
                    p.id_inscripcion,
                    CONCAT(a.nombre, ' ', a.apellido) AS nombre_alumno,
                    i.numero_acta,
                    p.valor_total,
                    p.estado
                FROM pagos p
                JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
                JOIN alumnos a ON i.id_alumno = a.rut
                WHERE p.tipo_pago = 'pagare'
                  AND {}
            """
            # Construimos la cláusula según el tipo de búsqueda
            if search_type == 'inscripcion':
                clause = "i.id_inscripcion = %s"
            elif search_type == 'rut':
                clause = "a.rut = %s"
            elif search_type == 'pago':
                clause = "p.id_pago = %s"
            else:
                clause = "1=2"  # nada

            final_query = base_query.format(clause)
            cursor.execute(final_query, (value,))
            results = cursor.fetchall()
        except Exception as e:
            print("Error al buscar pagos tipo 'pagare':", e)
        finally:
            cursor.close()
            conn.close()
    return results

def fetch_inscription_details(id_inscripcion):
    """
    Obtiene los detalles de una inscripción específica para la ventana de añadir pago.
    
    Args:
        id_inscripcion: ID de la inscripción a buscar
        
    Returns:
        dict: Diccionario con la información de la inscripción o None si no se encuentra
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    i.id_inscripcion,
                    i.numero_acta,
                    CONCAT(a.nombre, ' ', a.apellido) as nombre_alumno,
                    c.nombre_curso,
                    i.id_empresa,
                    c.valor as valor_curso
                FROM inscripciones i 
                LEFT JOIN alumnos a ON i.id_alumno = a.rut
                LEFT JOIN cursos c ON i.id_curso = c.id_curso
                WHERE i.id_inscripcion = %s
            """, (id_inscripcion,))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    'id_inscripcion': result[0],
                    'numero_acta': result[1],
                    'nombre_alumno': result[2],
                    'nombre_curso': result[3],
                    'id_empresa': result[4],
                    'valor_curso': result[5]
                }
            else:
                print(f"No se encontró inscripción con ID {id_inscripcion}")
                return None
                
        except Exception as e:
            print(f"Error al obtener detalles de inscripción: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    return None

def fetch_payments_by_inscription(id_inscripcion):
    """
    Obtiene todos los pagos asociados a una inscripción específica.
    
    Args:
        id_inscripcion (int): ID de la inscripción a consultar
        
    Returns:
        list: Lista de tuplas con la información de los pagos o lista vacía si no hay pagos
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.id_pago,
                    p.tipo_pago,
                    p.modalidad_pago,
                    p.fecha_inscripcion,
                    p.fecha_final,
                    p.num_cuotas,
                    p.valor_total,
                    p.estado,
                    -- Información de cuotas
                    COUNT(c.id_cuota) as total_cuotas,
                    SUM(CASE WHEN c.estado_cuota = 'pagada' THEN 1 ELSE 0 END) as cuotas_pagadas,
                    -- Información de contribuciones
                    GROUP_CONCAT(DISTINCT 
                        CONCAT(co.tipo_contribuyente, ': $', co.monto_contribuido)
                        SEPARATOR ' | '
                    ) as detalle_contribuciones
                FROM pagos p
                LEFT JOIN cuotas c ON p.id_pago = c.id_pago
                LEFT JOIN contribuciones co ON p.id_pago = co.id_pago
                WHERE p.id_inscripcion = %s
                GROUP BY 
                    p.id_pago, p.tipo_pago, p.modalidad_pago,
                    p.fecha_inscripcion, p.fecha_final,
                    p.num_cuotas, p.valor_total, p.estado
                ORDER BY p.fecha_inscripcion DESC
            """, (id_inscripcion,))
            
            results = cursor.fetchall()
            
            if results:
                print(f"Se encontraron {len(results)} pagos para la inscripción {id_inscripcion}")
                # Formatear los resultados para la visualización
                formatted_results = []
                for row in results:
                    # Formatear fechas y valores monetarios
                    fecha_inscripcion = row[3].strftime('%Y-%m-%d') if row[3] else ''
                    fecha_final = row[4].strftime('%Y-%m-%d') if row[4] else ''
                    valor_total = f"${row[6]:,.0f}" if row[6] else '$0'
                    
                    formatted_row = [
                        row[0],                    # ID Pago
                        row[1].upper(),           # Tipo Pago
                        row[2].upper(),           # Modalidad Pago
                        valor_total,              # Valor Total
                        row[7].upper(),           # Estado
                        f"{row[9]}/{row[8]}",     # Cuotas Pagadas/Total
                        fecha_inscripcion,        # Fecha Inscripción
                        fecha_final,              # Fecha Final
                        row[10] if row[10] else 'Sin contribuciones'  # Detalle contribuciones
                    ]
                    formatted_results.append(formatted_row)
                return formatted_results
            else:
                print(f"No se encontraron pagos para la inscripción {id_inscripcion}")
                return []
                
        except Exception as e:
            print(f"Error al obtener pagos por inscripción: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    return []
# =======================================
#             FACTURACIÓN
# =======================================
def fetch_inscripcion_info(id_inscripcion):
    """Obtiene la información de una inscripción específica."""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                i.id_inscripcion,
                CONCAT(a.nombre, ' ', a.apellido) as nombre_alumno,
                c.nombre_curso,
                c.valor as monto
            FROM inscripciones i
            JOIN alumnos a ON i.id_alumno = a.rut
            JOIN cursos c ON i.id_curso = c.id_curso
            WHERE i.id_inscripcion = %s
        """
        
        cursor.execute(query, (id_inscripcion,))
        result = cursor.fetchone()
        
        if result:
            return {
                'id_inscripcion': result[0],
                'nombre': result[1],
                'curso': result[2],
                'monto': result[3]
            }
        return None
        
    except Exception as e:
        print(f"Error al obtener información de inscripción: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def insert_invoice(id_inscripcion, numero_factura):
    """Inserta una nueva factura."""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Obtener el monto del curso
        cursor.execute(
            """
            SELECT c.valor 
            FROM inscripciones i
            JOIN cursos c ON i.id_curso = c.id_curso
            WHERE i.id_inscripcion = %s
            """, 
            (id_inscripcion,)
        )
        
        result = cursor.fetchone()
        monto_total = result[0] if result else 0
        
        # Insertar la factura
        cursor.execute(
            """
            INSERT INTO facturas 
            (id_inscripcion, numero_factura, monto_total, estado, fecha_emision) 
            VALUES (%s, %s, %s, 'pendiente', NOW())
            """,
            (id_inscripcion, numero_factura, monto_total)
        )
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error al insertar factura: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
def update_invoice_status(id_factura, nuevo_estado):
    """
    Actualiza el estado de una factura.
    
    Args:
        id_factura (int): ID de la factura a actualizar
        nuevo_estado (str): Nuevo estado ('pendiente' o 'facturada')
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                UPDATE facturas
                SET estado = %s
                WHERE id_factura = %s
            """
            cursor.execute(query, (nuevo_estado, id_factura))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar estado de factura: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False

# =======================================
#           EMPRESAS 
# =======================================

def get_empresa_by_name(nombre_empresa):
    """
    Busca una empresa por nombre (usando el id como nombre)
    y retorna su ID.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Convertir a mayúsculas para la búsqueda
            nombre_empresa = nombre_empresa.upper().strip()
            cursor.execute(
                "SELECT id_empresa FROM empresa WHERE id_empresa = %s", 
                (nombre_empresa,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error al buscar empresa: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    return None

def register_new_empresa(nombre_empresa):
    """
    Registra una nueva empresa usando el nombre como id_empresa.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Convertir a mayúsculas para el registro
            id_empresa = nombre_empresa.upper().strip()
            
            # La tabla empresa requiere rut_empresa según el esquema
            # Generamos un RUT temporal único basado en el ID
            rut_temporal = f"0-{id_empresa[:8]}"  # Podemos ajustar esto según necesites
            
            cursor.execute("""
                INSERT INTO empresa (
                    id_empresa,
                    rut_empresa,
                    direccion_empresa
                ) VALUES (%s, %s, NULL)
            """, (id_empresa, rut_temporal))
            
            conn.commit()
            print(f"Empresa registrada exitosamente con ID: {id_empresa}")
            return id_empresa
        except Exception as e:
            print(f"Error al registrar empresa: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()
    return None

def get_or_create_empresa(nombre_empresa):
    """
    Busca una empresa por nombre (id), si no existe la crea.
    Retorna el ID de la empresa.
    """
    if not nombre_empresa or not nombre_empresa.strip():
        return None
        
    # Primero intentamos encontrar la empresa
    id_empresa = get_empresa_by_name(nombre_empresa)
    
    # Si no existe, la creamos
    if id_empresa is None:
        print(f"Empresa {nombre_empresa} no encontrada, creando nueva...")
        id_empresa = register_new_empresa(nombre_empresa)
        if id_empresa is not None:
            print(f"Nueva empresa creada con ID: {id_empresa}")
        else:
            print("Error al crear nueva empresa")
            
    return id_empresa

def fetch_all_empresas():
    """
    Obtiene todas las empresas registradas junto con su contacto principal.
    Retorna una lista de diccionarios con la información.
    """
    conn = connect_db()
    if not conn:
        print("Error: No se pudo conectar a la base de datos")
        return []

    try:
        with conn.cursor(dictionary=True) as cursor:
            query = """
                SELECT 
                    e.id_empresa,
                    e.rut_empresa,
                    e.direccion_empresa,
                    ec.nombre_contacto,
                    ec.correo_contacto,
                    ec.telefono_contacto,
                    ec.rol_contacto
                FROM empresa e
                LEFT JOIN (
                    SELECT ec1.*
                    FROM empresa_contactos ec1
                    INNER JOIN (
                        SELECT id_empresa, MIN(id_contacto) as min_id
                        FROM empresa_contactos
                        GROUP BY id_empresa
                    ) ec2 ON ec1.id_empresa = ec2.id_empresa 
                    AND ec1.id_contacto = ec2.min_id
                ) ec ON e.id_empresa = ec.id_empresa
                ORDER BY e.id_empresa
            """
            cursor.execute(query)
            empresas = cursor.fetchall()
            return empresas

    except Exception as e:
        print(f"Error al obtener empresas: {e}")
        return []
    finally:
        conn.close()

def format_empresa_data(empresa):
    """
    Formatea los datos de una empresa para su visualización
    """
    return [
        str(empresa.get("id_empresa", "")),
        str(empresa.get("rut_empresa", "")),
        str(empresa.get("direccion_empresa", "")),
        str(empresa.get("nombre_contacto", "")),
        str(empresa.get("correo_contacto", "")),
        str(empresa.get("telefono_contacto", "")),
        str(empresa.get("rol_contacto", ""))
    ]

def fetch_empresa_by_rut(conn, rut_empresa):
    """
    Busca una empresa específica por su RUT.
    """
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id_empresa, rut_empresa, direccion_empresa 
            FROM empresa 
            WHERE rut_empresa = %s
        """, (rut_empresa,))
        empresa = cursor.fetchone()
        cursor.close()
        return empresa
    except Exception as e:
        print(f"Error al buscar empresa por RUT: {e}")
        return None

def save_empresa(empresa_data, is_update=False):
    """
    Guarda o actualiza una empresa en la base de datos.
    
    Args:
        empresa_data (dict): Datos de la empresa
        is_update (bool): True si es actualización, False si es inserción
    
    Returns:
        bool: True si la operación fue exitosa
    """
    conn = connect_db()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            if is_update:
                query = """
                    UPDATE empresa 
                    SET rut_empresa = %s, direccion_empresa = %s
                    WHERE id_empresa = %s
                """
                params = (
                    empresa_data['rut_empresa'],
                    empresa_data['direccion_empresa'],
                    empresa_data['id_empresa']
                )
            else:
                query = """
                    INSERT INTO empresa (id_empresa, rut_empresa, direccion_empresa)
                    VALUES (%s, %s, %s)
                """
                params = (
                    empresa_data['id_empresa'],
                    empresa_data['rut_empresa'],
                    empresa_data['direccion_empresa']
                )
            
            cursor.execute(query, params)
            conn.commit()
            return True
            
    except Exception as e:
        print(f"Error al {'actualizar' if is_update else 'insertar'} empresa: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def fetch_empresa_by_id(id_empresa):
    """
    Obtiene los datos de una empresa por su ID.
    """
    conn = connect_db()
    if not conn:
        return None

    try:
        with conn.cursor(dictionary=True) as cursor:
            query = """
                SELECT id_empresa, rut_empresa, direccion_empresa
                FROM empresa
                WHERE id_empresa = %s
            """
            cursor.execute(query, (id_empresa,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Error al obtener empresa: {e}")
        return None
    finally:
        conn.close()

def fetch_all_empresas_for_combo():
    """
    Obtiene todas las empresas para mostrar en un combobox
    """
    conn = connect_db()
    if not conn:
        return []
        
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT id_empresa, rut_empresa
                FROM empresa
                ORDER BY id_empresa
            """)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error al obtener lista de empresas: {e}")
        return []
    finally:
        conn.close()

def fetch_contactos_by_empresa(id_empresa):
    """
    Obtiene todos los contactos de una empresa específica.
    """
    conn = connect_db()
    if not conn:
        return []
        
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT id_contacto, nombre_contacto, rol_contacto, 
                       correo_contacto, telefono_contacto
                FROM empresa_contactos 
                WHERE id_empresa = %s
                ORDER BY nombre_contacto
            """, (id_empresa,))
            return cursor.fetchall()
    except Exception as e:
        print(f"Error al obtener contactos: {e}")
        return []
    finally:
        conn.close()

def save_contacto_empresa(contacto_data, is_update=False):
    """
    Guarda o actualiza un contacto de empresa
    """
    conn = connect_db()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            if is_update:
                query = """
                    UPDATE empresa_contactos 
                    SET nombre_contacto = %s,
                        rol_contacto = %s,
                        correo_contacto = %s,
                        telefono_contacto = %s
                    WHERE id_contacto = %s
                """
                params = (
                    contacto_data['nombre_contacto'],
                    contacto_data['rol_contacto'],
                    contacto_data['correo_contacto'],
                    contacto_data['telefono_contacto'],
                    contacto_data['id_contacto']
                )
            else:
                query = """
                    INSERT INTO empresa_contactos 
                    (id_empresa, nombre_contacto, rol_contacto, correo_contacto, telefono_contacto)
                    VALUES (%s, %s, %s, %s, %s)
                """
                params = (
                    contacto_data['id_empresa'],
                    contacto_data['nombre_contacto'],
                    contacto_data['rol_contacto'],
                    contacto_data['correo_contacto'],
                    contacto_data['telefono_contacto']
                )
            
            cursor.execute(query, params)
            conn.commit()
            return True
    except Exception as e:
        print(f"Error al guardar contacto: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_contacto_empresa(id_contacto):
    """Elimina un contacto de empresa"""
    conn = connect_db()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM empresa_contactos WHERE id_contacto = %s", (id_contacto,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error al eliminar contacto: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# =======================================
#           COTIZACIONES 
# =======================================

def fetch_cotizaciones():
    """
    Obtiene todas las cotizaciones con su información básica y cantidad total de cursos
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    c.id_cotizacion,
                    c.nombre_contacto,
                    c.origen,
                    c.fecha_cotizacion,
                    c.fecha_vencimiento,
                    c.email,
                    c.modo_pago,
                    c.encargado,
                    COALESCE(SUM(dc.cantidad), 0) as cantidad_total_cursos
                FROM cotizacion c
                LEFT JOIN detalle_cotizacion dc ON c.id_cotizacion = dc.id_cotizacion
                GROUP BY 
                    c.id_cotizacion,
                    c.nombre_contacto,
                    c.origen,
                    c.fecha_cotizacion,
                    c.fecha_vencimiento,
                    c.email,
                    c.modo_pago,
                    c.encargado
                ORDER BY c.id_cotizacion DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener cotizaciones: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    return []

def insertar_cotizacion(fecha_cotizacion, fecha_vencimiento, origen, nombre_contacto, 
                       email, modo_pago, metodo_pago, num_cuotas, detalle, total, 
                       detalles_cursos, encargado):
    """
    Inserta una nueva cotización en la tabla cotizacion y sus detalles en detalle_cotizacion.
    """
    conn = connect_db()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Insertar en la tabla cotizacion
        query_cotizacion = """
        INSERT INTO cotizacion (
            fecha_cotizacion, fecha_vencimiento, origen, nombre_contacto, email,
            modo_pago, metodo_pago, num_cuotas, detalle, total, encargado
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query_cotizacion, (
            fecha_cotizacion, fecha_vencimiento, origen, nombre_contacto, email,
            modo_pago, metodo_pago, num_cuotas, detalle, total, encargado
        ))
        id_cotizacion = cursor.lastrowid

        # Insertar en la tabla detalle_cotizacion
        query_detalle = """
        INSERT INTO detalle_cotizacion (
            id_cotizacion, id_curso, cantidad, valor_curso, valor_total
        ) VALUES (%s, %s, %s, %s, %s)
        """
        for detalle in detalles_cursos:
            cursor.execute(query_detalle, (
                id_cotizacion, detalle["id_curso"], detalle["cantidad"],
                detalle["valor_curso"], detalle["valor_total"]
            ))

        conn.commit()
        return id_cotizacion

    except mysql.connector.Error as e:
        print(f"Error al insertar cotización: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_cotizacion_details(id_cotizacion):
    """
    Obtiene los detalles completos de una cotización, incluyendo sus items.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Obtener la cotización con encargado
            query_cotizacion = """
                SELECT 
                    id_cotizacion, fecha_cotizacion, fecha_vencimiento, 
                    origen, nombre_contacto, email, modo_pago, metodo_pago, 
                    num_cuotas, detalle, total, encargado
                FROM cotizacion 
                WHERE id_cotizacion = %s
            """
            cursor.execute(query_cotizacion, (id_cotizacion,))
            cotizacion = cursor.fetchone()
            
            # Obtener los detalles
            query_detalles = """
                SELECT d.*, c.nombre_curso 
                FROM detalle_cotizacion d
                JOIN cursos c ON d.id_curso = c.id_curso
                WHERE d.id_cotizacion = %s
            """
            cursor.execute(query_detalles, (id_cotizacion,))
            detalles = cursor.fetchall()
            
            return {
                'cotizacion': cotizacion,
                'detalles': detalles
            }
        except Exception as e:
            print(f"Error al obtener detalles de cotización: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    return None


# =======================================
#           AUTENTICACION 
# =======================================

# queries.py
def fetch_user_by_credentials(username, password):
    """
    Consulta las credenciales del usuario en la base de datos.
    """
    conn = connect_db()
    try:
        cursor = conn.cursor()
        query = "SELECT username, rol FROM Usuarios WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
        if result:
            return {"username": result[0], "rol": result[1]}  # Devuelve un diccionario con username y rol
        return None
    except Exception as e:
        print("Error al consultar credenciales:", e)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


#=======================================================================
#                   QUERIES FOR REPORTS
#=======================================================================
def fetch_inscription(student_rut):
    """
    Obtiene las inscripciones y datos de cursos para un alumno específico
    """
    conn = connect_db()
    if not conn:
        return []
        
    try:
        cursor = conn.cursor()  # Usamos cursor normal, no dictionary
        
        query = """
            SELECT 
                c.id_curso,
                c.nombre_curso,
                i.numero_acta
            FROM inscripciones i
            INNER JOIN cursos c ON i.id_curso = c.id_curso
            WHERE i.id_alumno = %s
            ORDER BY i.fecha_inscripcion DESC
        """
        
        cursor.execute(query, (student_rut,))
        results = cursor.fetchall()
        
        # Convertimos los resultados a lista de diccionarios
        formatted_results = []
        for row in results:
            formatted_results.append({
                'ID_Curso': row[0],
                'nombre_curso': row[1],
                'N_Acta': row[2]
            })
            
        return formatted_results
        
    except Exception as e:
        print(f"Error en fetch_inscription: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def fetch_omi_courses(rut):
    """
    Obtiene los datos del alumno y sus cursos de competencia para certificación OMI.
    Retorna una tupla (datos_alumno, cursos)
    """
    conn = connect_db()
    if not conn:
        return None, []

    try:
        cursor = conn.cursor()
        
        # 1. Obtener datos del alumno
        cursor.execute("""
            SELECT rut, nombre, apellido 
            FROM alumnos 
            WHERE rut = %s
        """, (rut,))
        
        alumno = cursor.fetchone()
        
        if not alumno:
            return None, []
            
        # 2. Obtener cursos de competencia incluyendo id_inscripcion
        cursor.execute("""
            SELECT 
                i.id_inscripcion,  -- Agregamos id_inscripcion
                c.id_curso,
                c.nombre_curso,
                i.numero_acta
            FROM inscripciones i
            INNER JOIN cursos c ON i.id_curso = c.id_curso
            WHERE i.id_alumno = %s
            AND c.tipo_curso = 'COMPETENCIA'  -- Solo cursos presenciales
            ORDER BY i.fecha_inscripcion DESC
        """, (rut,))
        
        cursos = cursor.fetchall()
        
        return alumno, cursos
        
    except Exception as e:
        print(f"Error en fetch_omi_courses: {e}")
        return None, []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_or_create_tramitacion(id_inscripcion):
    """
    Obtiene o crea una tramitación para una inscripción
    """
    conn = connect_db()
    if not conn:
        raise Exception("No se pudo conectar a la base de datos")
        
    try:
        cursor = conn.cursor()
        
        # Primero intentamos obtener una tramitación existente
        cursor.execute("""
            SELECT id_tramitacion 
            FROM tramitaciones 
            WHERE id_inscripcion = %s
        """, (id_inscripcion,))
        
        result = cursor.fetchone()
        
        if result:
            return result[0]
            
        # Si no existe, creamos una nueva
        cursor.execute("""
            INSERT INTO tramitaciones (id_inscripcion, estado_general) 
            VALUES (%s, 'pendiente')
        """, (id_inscripcion,))
        
        conn.commit()
        return cursor.lastrowid
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def get_apendice4_data(numero_acta, anio):
    """
    Devuelve las filas de 'inscripciones' + 'cursos' + 'alumnos' para un número de acta dado y año.
    """
    sql = """
        SELECT
            i.numero_acta,
            c.nombre_curso,
            c.modalidad,
            i.fecha_inscripcion        AS fecha_inicio,
            i.fecha_termino_condicional AS fecha_termino,
            c.horas_cronologicas,
            c.horas_pedagogicas,
            a.rut        AS rut_alumno,
            a.nombre     AS nombre_alumno,
            a.apellido   AS apellido_alumno,
            a.profesion  AS profesion_alumno
        FROM inscripciones i
        JOIN cursos c   ON i.id_curso = c.id_curso
        JOIN alumnos a  ON i.id_alumno = a.rut
        WHERE i.numero_acta = %s AND YEAR(i.fecha_inscripcion) = %s
        ORDER BY a.apellido, a.nombre
    """
    conn = connect_db()
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, (numero_acta, anio))
            rows = cursor.fetchall()
        return rows
    except Exception as e:
        print("Error en get_apendice4_data:", e)
        return []
    finally:
        conn.close()
        
def get_next_doc_number(conn, doc_type):
    """
    Aumenta la secuencia en doc_sequences para doc_type.
    Cada doc_type lleva su numeración independiente.
    """
    sql_select = "SELECT last_number FROM doc_sequences WHERE doc_type=%s FOR UPDATE"
    sql_insert = "INSERT INTO doc_sequences(doc_type, last_number) VALUES(%s, %s)"
    sql_update = "UPDATE doc_sequences SET last_number=%s WHERE doc_type=%s"

    with conn.cursor() as cursor:
        cursor.execute(sql_select, (doc_type,))
        row = cursor.fetchone()
        if row is None:
            # No existe => arrancamos en 1
            new_number = 1
            cursor.execute(sql_insert, (doc_type, new_number))
        else:
            last_number = row[0]
            new_number = last_number + 1
            cursor.execute(sql_update, (new_number, doc_type))
    conn.commit()
    return new_number

def get_or_create_tramitacion(conn, id_inscripcion):
    """
    Obtiene o crea una tramitación para una inscripción.
    
    Args:
        conn: Conexión a la base de datos
        id_inscripcion: ID de la inscripción
    
    Returns:
        int: ID de la tramitación
    """
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Primero intentamos obtener una tramitación existente
        cursor.execute("""
            SELECT id_tramitacion 
            FROM tramitaciones 
            WHERE id_inscripcion = %s
        """, (id_inscripcion,))
        
        result = cursor.fetchone()
        
        if result:
            return result['id_tramitacion']
        
        # Si no existe, creamos una nueva
        cursor.execute("""
            INSERT INTO tramitaciones (id_inscripcion)
            VALUES (%s)
        """, (id_inscripcion,))
        
        conn.commit()
        return cursor.lastrowid
        
    except Exception as e:
        conn.rollback()
        raise Exception(f"Error al gestionar tramitación: {str(e)}")
    finally:
        cursor.close()

def create_document_for_tramitacion(conn, id_tramitacion, doc_type_name):
    """
    Crea una nueva fila en 'tipos_tramite', asociada a la MISMA tramitacion.
    - doc_num se obtiene de doc_sequences (doc_type_name).
    - fecha_emision = hoy (puedes cambiarlo).
    - estado = 'pendiente'.

    Retorna (id_tipo_tramite, doc_num).
    """
    from datetime import date

    doc_num = get_next_doc_number(conn, doc_type_name)
    today = date.today()

    sql_insert = """
        INSERT INTO tipos_tramite (id_tramitacion, doc_num, nombre_tramite, fecha_emision, estado)
        VALUES (%s, %s, %s, %s, %s)
    """
    with conn.cursor() as cursor:
        cursor.execute(sql_insert, (id_tramitacion, doc_num, doc_type_name, today, 'completado'))
        new_id_tipo_tramite = cursor.lastrowid

    conn.commit()
    return new_id_tipo_tramite, doc_num

#=======================================================================
#       Tramitaciones
#=======================================================================
def get_apendice6_data(numero_acta, anio):
    """
    Obtiene los datos necesarios para generar el Apéndice 6 basado en el número de acta y el año.
    """
    query = """
    SELECT 
        i.id_inscripcion,  -- Se agrega el id_inscripcion
        i.numero_acta,
        c.id_curso,
        c.nombre_curso,
        c.horas_cronologicas,
        c.horas_pedagogicas,
        i.fecha_inscripcion as fecha_inicio,
        i.fecha_termino_condicional as fecha_termino,
        a.rut,
        a.nombre,
        a.apellido,
        a.profesion,
        '' as mmn  -- Campo placeholder para MMN si se necesita agregar después
    FROM inscripciones i
    JOIN cursos c ON i.id_curso = c.id_curso
    JOIN alumnos a ON i.id_alumno = a.rut
    WHERE i.numero_acta = %s AND YEAR(i.fecha_inscripcion) = %s
    ORDER BY a.apellido, a.nombre
    """
    
    try:
        conn = connect_db()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, (numero_acta, anio))
            results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Error en get_apendice6_data: {e}")
        return None
    
def fetch_tramitaciones():
    """
    Obtiene todas las tramitaciones con información relacionada
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
            SELECT  
                i.id_inscripcion,
                a.rut,
                CONCAT(a.nombre, ' ', a.apellido) as nombre_completo,
                t.estado_general,
                t.fecha_ultimo_cambio,
                t.observacion,
                COUNT(tt.estado) as total_documentos,
                t.id_tramitacion
            FROM tramitaciones t
            JOIN inscripciones i ON t.id_inscripcion = i.id_inscripcion
            JOIN alumnos a ON i.id_alumno = a.rut
            LEFT JOIN tipos_tramite tt ON t.id_tramitacion = tt.id_tramitacion
            GROUP BY i.id_inscripcion, a.rut, nombre_completo, 
                     t.estado_general, t.fecha_ultimo_cambio, t.observacion, t.id_tramitacion
            ORDER BY t.fecha_ultimo_cambio DESC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        except Exception as e:
            print("Error al obtener tramitaciones:", e)
            return []
        finally:
            cursor.close()
            conn.close()
    return []

def fetch_tramitaciones_by_rut(rut):
    """
    Obtiene todas las tramitaciones de un alumno específico
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
            SELECT  
                i.id_inscripcion,
                a.rut,
                CONCAT(a.nombre, ' ', a.apellido) as nombre_completo,
                t.estado_general,
                t.fecha_ultimo_cambio,
                t.observacion,
                COUNT(tt.estado) as total_documentos,
                t.id_tramitacion
            FROM tramitaciones t
            JOIN inscripciones i ON t.id_inscripcion = i.id_inscripcion
            JOIN alumnos a ON i.id_alumno = a.rut
            LEFT JOIN tipos_tramite tt ON t.id_tramitacion = tt.id_tramitacion
            WHERE a.rut = %s
            GROUP BY i.id_inscripcion, a.rut, nombre_completo,
                     t.estado_general, t.fecha_ultimo_cambio, t.observacion, t.id_tramitacion
            ORDER BY t.fecha_ultimo_cambio DESC
            """
            cursor.execute(query, (rut,))
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"Error al obtener tramitaciones para RUT {rut}:", e)
            return []
        finally:
            cursor.close()
            conn.close()
    return []

def fetch_tramitaciones_activas():
    """
    Obtiene todas las tramitaciones que no están en estado completado
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
            SELECT  
                i.id_inscripcion,
                a.rut,
                CONCAT(a.nombre, ' ', a.apellido) as nombre_completo,
                t.estado_general,
                t.fecha_ultimo_cambio,
                t.observacion,
                COUNT(tt.estado) as total_documentos,
                t.id_tramitacion
            FROM tramitaciones t
            JOIN inscripciones i ON t.id_inscripcion = i.id_inscripcion
            JOIN alumnos a ON i.id_alumno = a.rut
            LEFT JOIN tipos_tramite tt ON t.id_tramitacion = tt.id_tramitacion
            WHERE t.estado_general != 'completado'
            GROUP BY i.id_inscripcion, a.rut, nombre_completo,
                     t.estado_general, t.fecha_ultimo_cambio, t.observacion, t.id_tramitacion
            ORDER BY t.fecha_ultimo_cambio DESC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        except Exception as e:
            print("Error al obtener tramitaciones activas:", e)
            return []
        finally:
            cursor.close()
            conn.close()
    return []

def fetch_tipos_tramite(id_tramitacion):
    """
    Obtiene todos los documentos asociados a una tramitación
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
            SELECT 
                doc_num,
                nombre_tramite,
                fecha_emision,
                estado
            FROM tipos_tramite
            WHERE id_tramitacion = %s
            ORDER BY fecha_emision DESC
            """
            cursor.execute(query, (id_tramitacion,))
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"Error al obtener documentos para tramitación {id_tramitacion}:", e)
            return []
        finally:
            cursor.close()
            conn.close()
    return []


# =======================================
#   Libro de clases
#========================================

def check_carpeta_exists(cursor, numero_acta, id_curso):
    """Verifica si existe una carpeta de libros para esta acta y curso"""
    query = """
        SELECT id_carpeta 
        FROM carpeta_libros 
        WHERE numero_acta = %s AND id_curso = %s
    """
    cursor.execute(query, (numero_acta, id_curso))
    return cursor.fetchone()

def create_carpeta_libros(numero_acta, id_curso, fecha_inicio):
    """Crea una nueva carpeta de libros si no existe"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Verificar si el curso es de formación
        cursor.execute("""
            SELECT tipo_curso 
            FROM cursos 
            WHERE id_curso = %s 
            AND tipo_curso = 'FORMACION'
        """, (id_curso,))
        
        if not cursor.fetchone():
            return False, "El curso debe ser de tipo FORMACION"
        
        # Verificar si ya existe la carpeta
        carpeta = check_carpeta_exists(cursor, numero_acta, id_curso)
        if carpeta:
            return True, carpeta[0]  # Retorna el id_carpeta existente
            
        # Crear nueva carpeta
        cursor.execute("""
            INSERT INTO carpeta_libros (
                numero_acta,
                id_curso,
                fecha_inicio,
                estado
            ) VALUES (%s, %s, %s, 'activo')
        """, (numero_acta, id_curso, fecha_inicio))
        
        id_carpeta = cursor.lastrowid
        conn.commit()
        return True, id_carpeta
        
    except Exception as e:
        return False, f"Error al crear carpeta: {str(e)}"
    finally:
        cursor.close()
        conn.close()

def fetch_carpetas_formacion(active_only=True):
    """Obtiene las carpetas de libros de clase, filtrando por estado si es necesario."""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        query = """
            SELECT 
                cl.id_carpeta,
                cl.numero_acta,
                cl.id_curso,
                c.nombre_curso,
                cl.fecha_inicio,
                cl.fecha_termino,
                cl.estado,
                COUNT(DISTINCT a.rut) AS total_alumnos,
                COUNT(DISTINCT l.id_libro) AS total_libros
            FROM carpeta_libros cl
            JOIN cursos c ON cl.id_curso = c.id_curso
            LEFT JOIN inscripciones i 
                ON cl.id_curso = i.id_curso 
                AND cl.numero_acta = i.numero_acta 
                AND i.anio_inscripcion = YEAR(cl.fecha_inicio)
            LEFT JOIN alumnos a ON i.id_alumno = a.rut
            LEFT JOIN libros_clase l ON cl.id_carpeta = l.id_carpeta
            {}
            GROUP BY 
                cl.id_carpeta, 
                cl.numero_acta, 
                cl.id_curso, 
                c.nombre_curso, 
                cl.fecha_inicio, 
                cl.fecha_termino, 
                cl.estado
            ORDER BY cl.numero_acta ASC
        """
        if active_only:
            query = query.format("WHERE cl.estado = 'activo'")
        else:
            query = query.format("")
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error al obtener carpetas: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        cursor.close()
        conn.close()


# =======================================
#           Deudores
# =======================================
def is_student_debtor(rut_alumno):
    """
    Retorna True si el alumno (identificado por su RUT) está en la lista de deudores con estado 'activo'.
    """
    conn = connect_db()  # Asegúrate de tener definida esta función para conectar a tu BD
    try:
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM deudores WHERE rut_alumno = %s AND estado = 'activo'"
        cursor.execute(query, (rut_alumno,))
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        print(f"Error en is_student_debtor: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def fetch_deudores(search_term=None):
    """
    Obtiene los deudores de la tabla. Si se proporciona un término de búsqueda,
    se filtra por el ID de inscripción o por el RUT del alumno.
    """
    conn = connect_db()
    cursor = conn.cursor()
    if search_term:
        query = """
            SELECT id_deudor, id_inscripcion, rut_alumno, fecha_registro, motivo, 
                   numero_cuotas_vencidas, monto_total, estado 
            FROM deudores 
            WHERE id_inscripcion LIKE %s OR rut_alumno LIKE %s
        """
        like_term = "%" + search_term + "%"
        cursor.execute(query, (like_term, like_term))
    else:
        query = """
            SELECT id_deudor, id_inscripcion, rut_alumno, fecha_registro, motivo, 
                   numero_cuotas_vencidas, monto_total, estado 
            FROM deudores
        """
        cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# -----------------------------------------------------------------------------
# Query: Insert deudor
# -----------------------------------------------------------------------------
def insert_deudor(id_inscripcion, rut_alumno, motivo, cuotas_vencidas, monto_total, estado="activo"):
    """
    Inserta un nuevo registro en la tabla de deudores.
    """
    conn = connect_db()
    cursor = conn.cursor()
    query = """
        INSERT INTO deudores (id_inscripcion, rut_alumno, motivo, numero_cuotas_vencidas, monto_total, estado)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (id_inscripcion, rut_alumno, motivo, cuotas_vencidas, monto_total, estado))
    conn.commit()
    last_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return last_id

# -----------------------------------------------------------------------------
# Query: Delete deudor
# -----------------------------------------------------------------------------
def delete_deudor_db(deudor_id):
    """
    Elimina un registro de deudor a partir de su ID.
    """
    conn = connect_db()
    cursor = conn.cursor()
    query = "DELETE FROM deudores WHERE id_deudor = %s"
    cursor.execute(query, (deudor_id,))
    conn.commit()
    cursor.close()
    conn.close()

# -----------------------------------------------------------------------------
# Función: Verificar y agregar deudores por cuotas vencidas
# -----------------------------------------------------------------------------
def check_overdue_debtors():
    """
    Verifica los alumnos que tienen 2 o más cuotas vencidas y los agrega a la tabla
    de deudores con motivo 'CuotasVencidas', siempre y cuando no exista ya un registro
    activo para esa inscripción y alumno.
    """
    conn = connect_db()
    # Utilizamos dictionary=True para trabajar con diccionarios en lugar de tuplas.
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT p.id_inscripcion, a.rut AS rut_alumno, COUNT(*) AS cuotas_vencidas, 
               SUM(c.valor_cuota) AS monto_total
        FROM cuotas c
        JOIN pagos p ON c.id_pago = p.id_pago
        JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
        JOIN alumnos a ON i.id_alumno = a.rut
        WHERE c.estado_cuota = 'vencida'
        GROUP BY p.id_inscripcion, a.rut
        HAVING COUNT(*) >= 2
    """
    cursor.execute(query)
    results = cursor.fetchall()
    
    for row in results:
        # Verificar si ya existe un registro activo en deudores para este alumno e inscripción
        check_query = """
            SELECT COUNT(*) AS count 
            FROM deudores 
            WHERE id_inscripcion = %s AND rut_alumno = %s 
              AND motivo = 'CuotasVencidas' AND estado = 'activo'
        """
        cursor.execute(check_query, (row['id_inscripcion'], row['rut_alumno']))
        result_check = cursor.fetchone()
        
        if result_check['count'] == 0:
            # Insertar en deudores
            insert_query = """
                INSERT INTO deudores (id_inscripcion, rut_alumno, motivo, numero_cuotas_vencidas, monto_total, estado)
                VALUES (%s, %s, 'CuotasVencidas', %s, %s, 'activo')
            """
            cursor.execute(insert_query, (row['id_inscripcion'], row['rut_alumno'],
                                            row['cuotas_vencidas'], row['monto_total']))
            conn.commit()
    
    cursor.close()
    conn.close()