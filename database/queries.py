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
                ORDER BY i.fecha_inscripcion DESC, i.id_inscripcion DESC
            """)
            results = cursor.fetchall()
            print(f"Resultados obtenidos: {len(results)} inscripciones")
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
    """
    Obtiene los datos de una inscripción específica por su ID.
    Retorna una tupla con los datos o None si no se encuentra.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    i.id_inscripcion,
                    i.id_alumno,
                    i.id_curso,
                    i.fecha_inscripcion,
                    i.fecha_termino_condicional,
                    i.anio_inscripcion,
                    i.metodo_llegada,
                    i.id_empresa,
                    i.numero_acta,
                    i.ordenSence,
                    i.idfolio
                FROM inscripciones i 
                WHERE i.id_inscripcion = %s
            """, (id_inscripcion,))
            
            result = cursor.fetchone()
            
            if result:
                print(f"Inscripción encontrada: {result}")
                return result
            else:
                print(f"No se encontró inscripción con ID {id_inscripcion}")
                return None
                
        except Exception as e:
            print(f"Error al obtener inscripción: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    return None

def update_inscription(id_inscripcion,
                    id_alumno=None,
                    id_curso=None,
                    fecha_inscripcion=None,
                    fecha_termino_condicional=None,
                    anio_inscripcion=None,
                    metodo_llegada=None,
                    id_empresa=None,
                    numero_acta=None,
                    ordenSence=None,
                    idfolio=None):
    """
    Actualiza los datos de una inscripción existente.
    Solo modifica los campos que no vengan como None.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            # 1) Obtener la inscripción actual
            cursor.execute("SELECT * FROM Inscripciones WHERE id_inscripcion = %s", (id_inscripcion,))
            inscripcion = cursor.fetchone()
            if not inscripcion:
                print(f"No se encontró inscripcion con ID {id_inscripcion}")
                return False, "No se encontró la inscripción especificada."
            
            # Mapeo de columnas de la tabla Inscripciones:
            #  inscripcion[0] => id_inscripcion
            #  inscripcion[1] => id_alumno
            #  inscripcion[2] => id_curso
            #  inscripcion[3] => fecha_inscripcion
            #  inscripcion[4] => fecha_termino_condicional
            #  inscripcion[5] => anio_inscripcion
            #  inscripcion[6] => metodo_llegada
            #  inscripcion[7] => id_empresa
            #  inscripcion[8] => numero_acta
            #  inscripcion[9] => ordenSence
            #  inscripcion[10] => idfolio

            # 2) Obtener valores actuales
            current_values = {
                'id_alumno': inscripcion[1],
                'id_curso': inscripcion[2],
                'fecha_inscripcion': inscripcion[3],
                'fecha_termino_condicional': inscripcion[4],
                'anio_inscripcion': inscripcion[5],
                'metodo_llegada': inscripcion[6],
                'id_empresa': inscripcion[7],
                'numero_acta': inscripcion[8],
                'ordenSence': inscripcion[9],
                'idfolio': inscripcion[10]
            }

            # 3) Determinar nuevos valores
            new_values = {
                'id_alumno': id_alumno if id_alumno is not None else current_values['id_alumno'],
                'id_curso': id_curso if id_curso is not None else current_values['id_curso'],
                'fecha_inscripcion': fecha_inscripcion if fecha_inscripcion is not None else current_values['fecha_inscripcion'],
                'fecha_termino_condicional': fecha_termino_condicional if fecha_termino_condicional is not None else current_values['fecha_termino_condicional'],
                'anio_inscripcion': anio_inscripcion if anio_inscripcion is not None else current_values['anio_inscripcion'],
                'metodo_llegada': metodo_llegada if metodo_llegada is not None else current_values['metodo_llegada'],
                'id_empresa': id_empresa if id_empresa is not None else current_values['id_empresa'],
                'numero_acta': numero_acta if numero_acta is not None else current_values['numero_acta'],
                'ordenSence': ordenSence if ordenSence is not None else current_values['ordenSence'],
                'idfolio': idfolio if idfolio is not None else current_values['idfolio']
            }

            # 4) Ejecutar UPDATE
            update_query = """
                UPDATE Inscripciones
                SET id_alumno = %s,
                    id_curso = %s,
                    fecha_inscripcion = %s,
                    fecha_termino_condicional = %s,
                    anio_inscripcion = %s,
                    metodo_llegada = %s,
                    id_empresa = %s,
                    numero_acta = %s,
                    ordenSence = %s,
                    idfolio = %s
                WHERE id_inscripcion = %s
            """
            cursor.execute(update_query, (
                new_values['id_alumno'],
                new_values['id_curso'],
                new_values['fecha_inscripcion'],
                new_values['fecha_termino_condicional'],
                new_values['anio_inscripcion'],
                new_values['metodo_llegada'],
                new_values['id_empresa'],
                new_values['numero_acta'],
                new_values['ordenSence'],
                new_values['idfolio'],
                id_inscripcion
            ))
            conn.commit()
            return True, "Inscripción actualizada exitosamente."

        except Exception as e:
            print("Error al actualizar inscripción:", e)
            return False, f"Error al actualizar la inscripción: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    return False, "Error de conexión con la base de datos."

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

# =======================================
#             PAGOS
# =======================================

def fetch_payments():
    """
    Obtiene la lista de pagos con información detallada incluyendo inscripción y estado.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
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
                    CONCAT(a.nombre, ' ', a.apellido) as nombre_alumno,
                    c.nombre_curso
                FROM pagos p
                LEFT JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
                LEFT JOIN alumnos a ON i.id_alumno = a.rut
                LEFT JOIN cursos c ON i.id_curso = c.id_curso
                ORDER BY p.fecha_inscripcion DESC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        except Exception as e:
            print("Error al obtener pagos:", e)
            return []
        finally:
            cursor.close()
            conn.close()
    return []

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

def insert_payment(id_inscripcion, tipo_pago, modalidad_pago, valor_total, num_cuotas=1):
    """
    Inserta un nuevo pago y sus cuotas si es necesario
    """
    conn = connect_db()
    if not conn:
        return (None, None)

    try:
        with conn.cursor() as cursor:
            # Insertar el pago
            insert_pago_query = """
                INSERT INTO pagos 
                (id_inscripcion, tipo_pago, modalidad_pago, fecha_inscripcion, 
                num_cuotas, valor_total, estado)
                VALUES (%s, %s, %s, NOW(), %s, %s, 'pendiente')
            """
            cursor.execute(insert_pago_query, (
                id_inscripcion, tipo_pago, modalidad_pago,
                num_cuotas, valor_total
            ))
            
            id_pago = cursor.lastrowid
            id_pagare = None
            
            # Si es pagaré, generar cuotas
            if tipo_pago == 'pagare':
                valor_cuota = valor_total / num_cuotas
                for i in range(num_cuotas):
                    insert_cuota_query = """
                        INSERT INTO cuotas 
                        (id_pago, nro_cuota, valor_cuota, fecha_vencimiento, estado_cuota)
                        VALUES (%s, %s, %s, DATE_ADD(NOW(), INTERVAL %s MONTH), 'pendiente')
                    """
                    cursor.execute(insert_cuota_query, (
                        id_pago, i + 1, valor_cuota, i
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

def update_payment_status(id_pago, nuevo_estado):
    """
    Actualiza el estado de un pago.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = "UPDATE pagos SET estado = %s WHERE id_pago = %s"
            cursor.execute(query, (nuevo_estado, id_pago))
            conn.commit()
            return True
        except Exception as e:
            print("Error al actualizar estado del pago:", e)
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def register_quota_payment(id_cuota):
    """
    Registra el pago de una cuota y actualiza estado y fecha final si corresponde.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Actualizar estado de la cuota
            query_cuota = """
                UPDATE cuotas 
                SET estado_cuota = 'pagada', 
                    fecha_pago = NOW()
                WHERE id_cuota = %s
            """
            cursor.execute(query_cuota, (id_cuota,))

            # Verificar si todas las cuotas están pagadas
            query_check = """
                SELECT 
                    p.id_pago,
                    COUNT(c.id_cuota) as total_cuotas,
                    SUM(CASE WHEN c.estado_cuota = 'pagada' THEN 1 ELSE 0 END) as cuotas_pagadas
                FROM pagos p
                JOIN cuotas c ON p.id_pago = c.id_pago
                WHERE c.id_cuota = %s
                GROUP BY p.id_pago
            """
            cursor.execute(query_check, (id_cuota,))
            result = cursor.fetchone()
            
            # Si todas las cuotas están pagadas, actualizar estado del pago y fecha final
            if result and result[1] == result[2]:  # total_cuotas == cuotas_pagadas
                query_pago = """
                    UPDATE pagos 
                    SET estado = 'pagado',
                        fecha_final = NOW()
                    WHERE id_pago = %s
                """
                cursor.execute(query_pago, (result[0],))
                
                # Registrar en el log de pagos completados
                query_log = """
                    INSERT INTO log_pagos 
                    (id_pago, tipo_evento, fecha_evento, descripcion)
                    VALUES (%s, 'COMPLETADO', NOW(), 'Pago completado - todas las cuotas pagadas')
                """
                try:
                    cursor.execute(query_log, (result[0],))
                except:
                    # Si la tabla de log no existe, continuamos sin error
                    pass
            
            conn.commit()
            return True
        except Exception as e:
            print("Error al registrar pago de cuota:", e)
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    return False

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

def fetch_all_empresas(conn):
    """
    Obtiene todas las empresas registradas junto con su contacto principal.
    """
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                e.id_empresa,
                e.rut_empresa,
                e.direccion_empresa,
                ec.nombre_contacto,
                ec.correo_contacto,
                ec.telefono_contacto,
                ec.rol_contacto
            FROM empresa e
            LEFT JOIN empresa_contactos ec ON e.id_empresa = ec.id_empresa
            WHERE ec.id_contacto = (
                SELECT MIN(id_contacto)
                FROM empresa_contactos
                WHERE id_empresa = e.id_empresa
            )
            ORDER BY e.id_empresa
        """)
        empresas = cursor.fetchall()
        cursor.close()
        return empresas
    except Exception as e:
        print(f"Error al obtener empresas: {e}")
        return []

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

def insert_empresa(conn, empresa_data):
    """
    Inserta una nueva empresa.
    
    Args:
        empresa_data (dict): Diccionario con los datos de la empresa
            {
                'id_empresa': str,
                'rut_empresa': str,
                'direccion_empresa': str
            }
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO empresa (id_empresa, rut_empresa, direccion_empresa)
            VALUES (%s, %s, %s)
        """, (
            empresa_data['id_empresa'],
            empresa_data['rut_empresa'],
            empresa_data['direccion_empresa']
        ))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error al insertar empresa: {e}")
        conn.rollback()
        return False

def update_empresa(conn, empresa_data):
    """
    Actualiza los datos de una empresa existente.
    
    Args:
        empresa_data (dict): Diccionario con los datos actualizados
            {
                'id_empresa': str,
                'rut_empresa': str,
                'direccion_empresa': str
            }
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE empresa 
            SET rut_empresa = %s, direccion_empresa = %s
            WHERE id_empresa = %s
        """, (
            empresa_data['rut_empresa'],
            empresa_data['direccion_empresa'],
            empresa_data['id_empresa']
        ))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error al actualizar empresa: {e}")
        conn.rollback()
        return False

def insert_contacto_empresa(conn, contacto_data):
    """
    Inserta un nuevo contacto para una empresa.
    
    Args:
        contacto_data (dict): Diccionario con los datos del contacto
            {
                'id_empresa': str,
                'nombre_contacto': str,
                'rol_contacto': str,
                'correo_contacto': str,
                'telefono_contacto': int
            }
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO empresa_contactos 
            (id_empresa, nombre_contacto, rol_contacto, correo_contacto, telefono_contacto)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            contacto_data['id_empresa'],
            contacto_data['nombre_contacto'],
            contacto_data['rol_contacto'],
            contacto_data['correo_contacto'],
            contacto_data['telefono_contacto']
        ))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error al insertar contacto de empresa: {e}")
        conn.rollback()
        return False

def fetch_contactos_by_empresa(conn, id_empresa):
    """
    Obtiene todos los contactos de una empresa específica.
    """
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id_contacto, nombre_contacto, rol_contacto, 
                   correo_contacto, telefono_contacto
            FROM empresa_contactos 
            WHERE id_empresa = %s
            ORDER BY nombre_contacto
        """, (id_empresa,))
        contactos = cursor.fetchall()
        cursor.close()
        return contactos
    except Exception as e:
        print(f"Error al obtener contactos de empresa: {e}")
        return []

def update_contacto_empresa(conn, contacto_data):
    """
    Actualiza los datos de un contacto existente.
    
    Args:
        contacto_data (dict): Diccionario con los datos actualizados
            {
                'id_contacto': int,
                'nombre_contacto': str,
                'rol_contacto': str,
                'correo_contacto': str,
                'telefono_contacto': int
            }
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE empresa_contactos 
            SET nombre_contacto = %s,
                rol_contacto = %s,
                correo_contacto = %s,
                telefono_contacto = %s
            WHERE id_contacto = %s
        """, (
            contacto_data['nombre_contacto'],
            contacto_data['rol_contacto'],
            contacto_data['correo_contacto'],
            contacto_data['telefono_contacto'],
            contacto_data['id_contacto']
        ))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error al actualizar contacto de empresa: {e}")
        conn.rollback()
        return False

def delete_contacto_empresa(conn, id_contacto):
    """
    Elimina un contacto específico de empresa.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM empresa_contactos 
            WHERE id_contacto = %s
        """, (id_contacto,))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error al eliminar contacto de empresa: {e}")
        conn.rollback()
        return False

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


