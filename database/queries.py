from database.db_config import connect_db
import re
from datetime import datetime , timedelta

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
    duracionDias
):
    """
    Inserta un nuevo curso con cálculo de horas pedagógicas, valor del curso y duración en días.
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
                 horas_cronologicas, horas_pedagogicas, valor, duracionDias)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                duracionDias
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
    duracionDias=None
):
    """
    Actualiza los datos de un curso existente, incluido el 'valor' y 'duracionDias'.
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

            # Asumiendo orden de columnas en la tabla Cursos:
            #  course[0] => id_curso
            #  course[1] => nombre_curso
            #  course[2] => modalidad
            #  course[3] => codigo_sence
            #  course[4] => codigo_elearning
            #  course[5] => horas_cronologicas
            #  course[6] => horas_pedagogicas
            #  course[7] => valor
            #  course[8] => duracionDias

            current_nombre   = course[1]
            current_mod      = course[2]
            current_sence    = course[3]
            current_elearn   = course[4]
            current_h_cron   = course[5]
            current_h_pedag  = course[6]
            current_valor    = course[7]
            current_dias     = course[8]

            # 2) Determinar horas_cronologicas
            new_horas_cron = horas_cronologicas if horas_cronologicas is not None else current_h_cron

            # 3) Determinar horas_pedagogicas
            if horas_pedagogicas is not None:
                # Si nos pasan un valor manual, lo usamos tal cual
                new_horas_pedag = horas_pedagogicas
            else:
                # Si no pasó horas_pedagogicas, la calculamos
                new_horas_pedag = round((new_horas_cron * 4 / 3), 1)

            # 4) Determinar valor y duración
            new_valor = valor if valor is not None else current_valor
            new_dias = duracionDias if duracionDias is not None else current_dias

            # 5) Armamos la query de UPDATE
            query = """
                UPDATE Cursos
                SET nombre_curso = %s,
                    modalidad = %s,
                    codigo_sence = %s,
                    codigo_elearning = %s,
                    horas_cronologicas = %s,
                    horas_pedagogicas = %s,
                    valor = %s,
                    duracionDias = %s
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
                new_dias,
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
    Obtiene todas las inscripciones con información detallada.
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
                    i.metodo_llegada as Metodo,
                    CASE 
                        WHEN i.id_empresa IS NOT NULL THEN e.id_empresa 
                        ELSE 'Particular'
                    END as Empresa,
                    i.ordenSence as Codigo_Sence,
                    i.idfolio as Folio
                FROM inscripciones i
                LEFT JOIN alumnos a ON i.id_alumno = a.rut
                LEFT JOIN empresa e ON i.id_empresa = e.id_empresa
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
    Da formato a los datos de inscripción para mostrarlos en la tabla.
    """
    try:
        fecha_inscripcion = inscription[5] if isinstance(inscription[5], str) else inscription[5].strftime('%Y-%m-%d') if inscription[5] else ''
        fecha_termino = inscription[6] if isinstance(inscription[6], str) else inscription[6].strftime('%Y-%m-%d') if inscription[6] else ''
        
        return {
            "ID": inscription[0],
            "N_Acta": inscription[1],
            "RUT": inscription[2],
            "Nombre_Completo": inscription[3],
            "ID_Curso": inscription[4],
            "F_Inscripcion": fecha_inscripcion,
            "F_Termino": fecha_termino,
            "Año": inscription[7],
            "Metodo": inscription[8],
            "Empresa": inscription[9],
            "Codigo_Sence": inscription[10],
            "Folio": inscription[11]
        }
    except Exception as e:
        print(f"Error al formatear inscripción: {e}")
        print(f"Datos recibidos: {inscription}")
        return {}

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

def insert_payment(id_inscripcion, tipo_pago, modalidad_pago, num_documento, 
                   cuotas_totales, valor, estado, cuotas_pagadas):
    """Inserta un nuevo pago."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO Pagos 
                (id_inscripcion, tipo_pago, modalidad_pago, num_documento,
                 cuotas_totales, valor, estado, cuotas_pagadas)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                id_inscripcion, tipo_pago, modalidad_pago, num_documento, 
                cuotas_totales, valor, estado, cuotas_pagadas
            ))
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
#           AUTENTICACION 
# =======================================

# queries.py
def fetch_user_by_credentials(username, password):
    """Obtiene un usuario por sus credenciales."""
    conn = connect_db()
    if conn:
        try:
            # dictionary=True para obtener columnas como dict
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM usuarios WHERE username = %s AND password = %s"
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

