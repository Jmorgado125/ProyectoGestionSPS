import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Biblioteca para drag & drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    TkBase = TkinterDnD.Tk  # Usaremos la clase Tk de tkinterdnd2
except ImportError:
    # Si no está instalada, se usa Tk normal, pero NO habrá drag & drop
    TkBase = tk.Tk

from datetime import datetime
from PIL import Image
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from path_utils import resource_path

# Ajustar según tu estructura de proyecto
from database.db_config import connect_db


class LibroClasesFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # --- Variables de control ---
        self.selected_carpeta = tk.StringVar()
        self.selected_libro = tk.StringVar()
        self.firma_path = tk.StringVar()
        self.observaciones = tk.StringVar()

        # --- Inicializar UI ---
        self._init_ui()
        self._load_initial_data()

    def _init_ui(self):
        """
        Construye todos los componentes gráficos de la ventana.
        """
        self.parent.title("Generación de Libro de Clases")

        # Intentamos establecer el ícono
        try:
            self.parent.iconbitmap(resource_path("assets/logo1.ico"))
        except Exception:
            pass

        # --- FRAME PRINCIPAL ---
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Título
        title_label = ttk.Label(
            main_frame,
            text="Generación de Libro de Clases",
            font=('Helvetica', 14, 'bold')
        )
        title_label.pack(pady=(0, 15))

        # --- FRAME SELECCIÓN DE LIBRO ---
        selection_frame = ttk.LabelFrame(main_frame, text="Selección de Libro")
        selection_frame.pack(fill=tk.X, padx=5, pady=5)
        selection_frame.columnconfigure(1, weight=1)

        # Combobox de Carpeta
        lbl_carpeta = ttk.Label(selection_frame, text="Carpeta:")
        lbl_carpeta.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        self.carpeta_combo = ttk.Combobox(selection_frame, textvariable=self.selected_carpeta)
        self.carpeta_combo.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.carpeta_combo.bind('<<ComboboxSelected>>', self._on_carpeta_selected)

        # Combobox de Libro
        lbl_libro = ttk.Label(selection_frame, text="Libro:")
        lbl_libro.grid(row=1, column=0, padx=5, pady=5, sticky='w')

        self.libro_combo = ttk.Combobox(selection_frame, textvariable=self.selected_libro)
        self.libro_combo.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        self.libro_combo.bind('<<ComboboxSelected>>', self._on_libro_selected)

        obs_frame = ttk.LabelFrame(main_frame, text="Observaciones")
        obs_frame.pack(fill=tk.X, padx=5, pady=5)

        obs_entry = ttk.Entry(obs_frame, textvariable=self.observaciones, width=50)
        obs_entry.pack(fill=tk.X, padx=5, pady=5)

        # --- FRAME FIRMA ---
        firma_frame = ttk.LabelFrame(main_frame, text="Firma del Instructor")
        firma_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        self.firma_label = ttk.Label(firma_frame, text="No se ha seleccionado firma")
        self.firma_label.pack(side=tk.LEFT, padx=5, pady=5)

        btn_select_firma = ttk.Button(firma_frame, text="Seleccionar Firma", command=self._select_firma)
        btn_select_firma.pack(side=tk.RIGHT, padx=5, pady=5)

        # Habilitar drag & drop sobre el frame (solo si tkinterdnd2 está disponible)
        if hasattr(firma_frame, 'drop_target_register'):
            firma_frame.drop_target_register(DND_FILES)
            firma_frame.dnd_bind('<<Drop>>', self._on_drop_firma)

        # --- FRAME BOTONES ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)

        btn_generar = ttk.Button(button_frame, text="Generar Libro", command=self._generate_libro)
        btn_generar.pack(side=tk.RIGHT, padx=5)

        btn_limpiar = ttk.Button(button_frame, text="Limpiar", command=self._clear_form)
        btn_limpiar.pack(side=tk.RIGHT, padx=5)

    def _on_drop_firma(self, event):
        """
        Evento que se activa al arrastrar un archivo de imagen (firma) sobre el frame.
        """
        firma_arrastrada = event.data.strip('{}')  # Quitar llaves en Windows
        if os.path.isfile(firma_arrastrada):
            ext = os.path.splitext(firma_arrastrada)[1].lower()
            if ext in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
                self.firma_path.set(firma_arrastrada)
                self.firma_label.config(text=os.path.basename(firma_arrastrada))
            else:
                messagebox.showwarning("Archivo no válido", "Por favor arrastra una imagen con formato válido.")
        else:
            messagebox.showwarning("Archivo no válido", "No se detectó un archivo de imagen válido.")

    def _on_carpeta_selected(self, event=None):
        """
        Cuando se selecciona una carpeta, cargamos la lista de libros activos relacionados.
        """
        if not self.selected_carpeta.get():
            return
        try:
            carpeta_id = self.selected_carpeta.get().split(' - ')[0]
            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT l.id_libro, l.asignatura, l.instructor
                FROM libros_clase l
                WHERE l.id_carpeta = %s 
                  AND l.estado = 'activo'
                ORDER BY l.asignatura
            """, (carpeta_id,))
            libros = cursor.fetchall()

            self.libro_combo['values'] = [
                f"{id_} - {asig} ({inst if inst else 'Sin instructor'})"
                for (id_, asig, inst) in libros
            ]
            self.libro_combo.set('')

            cursor.close()
            conn.close()

        except Exception as err:
            messagebox.showerror("Error", f"Error al cargar libros: {err}")

    def _on_libro_selected(self, event=None):
        """
        Evento que se activa al seleccionar un libro. 
        (Opcional: Cargar información adicional si se desea.)
        """
        if not self.selected_libro.get():
            return
        try:
            libro_id = self.selected_libro.get().split(' - ')[0]
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT l.*, c.numero_acta, c.fecha_inicio, c.fecha_termino,
                       cur.nombre_curso, cur.codigo_sence
                FROM libros_clase l
                JOIN carpeta_libros c ON l.id_carpeta = c.id_carpeta
                JOIN cursos cur ON c.id_curso = cur.id_curso
                WHERE l.id_libro = %s
            """, (libro_id,))
            _ = cursor.fetchone()  # libro_info si necesitas usarlo

            cursor.close()
            conn.close()

        except Exception as err:
            messagebox.showerror("Error", f"Error al cargar información del libro: {err}")

    def _load_carpetas(self):
        """
        Carga todas las carpetas activas desde la base de datos (sin búsqueda).
        """
        try:
            conn = connect_db()
            cursor = conn.cursor()
            query = """
                SELECT cl.id_carpeta, cl.numero_acta, c.nombre_curso
                FROM carpeta_libros cl
                JOIN cursos c ON cl.id_curso = c.id_curso
                WHERE cl.estado = 'activo'
                ORDER BY cl.fecha_inicio DESC
            """
            cursor.execute(query)
            carpetas = cursor.fetchall()

            self.carpeta_combo['values'] = [
                f"{id_} - {acta} - {curso}"
                for (id_, acta, curso) in carpetas
            ]

            cursor.close()
            conn.close()

        except Exception as err:
            messagebox.showerror("Error", f"Error al cargar carpetas: {err}")

    def _load_initial_data(self):
        """ Carga los datos iniciales al iniciar la ventana """
        self._load_carpetas()

    def _select_firma(self):
        """
        Abre un diálogo para seleccionar la imagen de la firma de forma manual.
        """
        filetypes = [
            ('Imágenes', '*.png *.jpg *.jpeg *.bmp *.gif'),
            ('Todos los archivos', '*.*')
        ]
        firma_path = filedialog.askopenfilename(
            title="Seleccionar imagen de firma",
            filetypes=filetypes
        )
        if firma_path:
            self.firma_path.set(firma_path)
            self.firma_label.config(text=os.path.basename(firma_path))

    def _process_firma(self, template_doc):
        """
        Ajusta el tamaño de la firma y la inserta en el documento.
        Devuelve un objeto InlineImage listo para usarse en la plantilla.
        """
        if not self.firma_path.get():
            return None
        try:
            with Image.open(self.firma_path.get()) as img:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                max_width_mm = 80  # en milímetros
                max_height_mm = 40  # en milímetros

                width_px, height_px = img.size
                ratio = min(max_width_mm / width_px, max_height_mm / height_px)
                new_width = int(width_px * ratio)
                new_height = int(height_px * ratio)

                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                temp_path = os.path.join(os.path.dirname(__file__), 'temp_firma.png')
                img.save(temp_path, 'PNG')

                return InlineImage(template_doc, temp_path, width=Mm(max_width_mm))
        except Exception as e:
            messagebox.showerror("Error", f"Error procesando la firma: {str(e)}")
            return None

    def _get_template_data(self, libro_id):
        """
        Obtiene los datos necesarios para rellenar la plantilla del libro.
        Corrige la consulta de alumnos para evitar el error con DISTINCT y ORDER BY.
        """
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        try:
            # Info del libro y curso
            cursor.execute("""
                SELECT l.*, c.numero_acta, c.fecha_inicio, c.fecha_termino,
                       cur.nombre_curso
                FROM libros_clase l
                JOIN carpeta_libros c ON l.id_carpeta = c.id_carpeta
                JOIN cursos cur ON c.id_curso = cur.id_curso
                WHERE l.id_libro = %s
            """, (libro_id,))
            libro_info = cursor.fetchone()

            # Contenidos diarios
            cursor.execute("""
                SELECT cd.*, cs.semana
                FROM contenidos_diarios cd
                JOIN contenidos_semanales cs ON cd.id_contenido = cs.id_contenido
                WHERE cs.id_libro = %s
                ORDER BY cd.fecha, cd.id_contenido_diario
            """, (libro_id,))
            contenidos = cursor.fetchall()

            # Lista de alumnos y asistencia
            # NOTA: Se seleccionan a.nombre y a.apellido para que MySQL no falle en ORDER BY
            cursor.execute("""
                SELECT DISTINCT a.rut, a.nombre, a.apellido
                FROM alumnos a
                JOIN asistencia_alumnos aa ON a.rut = aa.id_alumno
                JOIN contenidos_diarios cd ON aa.id_contenido_diario = cd.id_contenido_diario
                JOIN contenidos_semanales cs ON cd.id_contenido = cs.id_contenido
                WHERE cs.id_libro = %s
                ORDER BY a.apellido, a.nombre
            """, (libro_id,))
            alumnos = cursor.fetchall()

            lista_asistencia = []
            for alumno in alumnos:
                # Construimos nombre completo en Python
                nombre_completo = f"{alumno['nombre']} {alumno['apellido']}".strip()

                cursor.execute("""
                    SELECT cd.fecha, aa.estado_asistencia
                    FROM asistencia_alumnos aa
                    JOIN contenidos_diarios cd ON aa.id_contenido_diario = cd.id_contenido_diario
                    JOIN contenidos_semanales cs ON cd.id_contenido = cs.id_contenido
                    WHERE cs.id_libro = %s AND aa.id_alumno = %s
                    ORDER BY cd.fecha
                """, (libro_id, alumno['rut']))
                asistencias = cursor.fetchall()

                # Tomamos máximo 14 días a mostrar, con '1' = presente, '0' = ausente
                dias_asistencia = {
                    f'd{i+1}': '1' if a_['estado_asistencia'] == 'presente' else '0'
                    for i, a_ in enumerate(asistencias[:14])
                }

                total_dias = len(asistencias)
                dias_presente = sum(1 for a_ in asistencias if a_['estado_asistencia'] == 'presente')
                porcentaje = round((dias_presente / total_dias * 100) if total_dias > 0 else 0, 2)

                alumno_data = {
                    'rut': alumno['rut'],
                    'nombre_alumno': nombre_completo,
                    'asisfinal': f"{porcentaje}%"
                }
                alumno_data.update(dias_asistencia)
                lista_asistencia.append(alumno_data)

            context = {
                'Num_acta':        libro_info['numero_acta'],
                'materia':         libro_info['asignatura'],
                'nombre_prof':     libro_info['instructor'],
                'n_res':           libro_info['n_res_directemar'],
                'cantidad_horas':  str(libro_info['horas_totales']),
                'firma':           '',  # Se inyectará luego con _process_firma
                'contenidos': [
                    {
                        'fecha':     c['fecha'].strftime('%d/%m/%Y'),
                        'horas':     str(c['horas_realizadas']),
                        'contenido': c['contenido_tratado']
                    }
                    for c in contenidos
                ],
                'lista_asistencia': lista_asistencia,
                'observaciones': ''
            }

            return context

        finally:
            cursor.close()
            conn.close()

    def _generate_libro(self):
        """
        Genera el documento Word del libro de clases a partir de la plantilla.
        """
        if not self.selected_libro.get():
            messagebox.showwarning("Advertencia", "Por favor seleccione un libro")
            return

        if not self.firma_path.get():
            messagebox.showwarning("Advertencia", "Por favor seleccione una imagen de firma (o arrástrela)")
            return

        try:
            libro_id = self.selected_libro.get().split(' - ')[0]

            # Cargar plantilla
            template_path = resource_path("formatos/libros_template.docx")
            doc = DocxTemplate(template_path)

            # Armar contexto
            context = self._get_template_data(libro_id)
            context['observaciones'] = self.observaciones.get()
            # Procesar firma
            firma_image = self._process_firma(doc)
            if firma_image:
                context['firma'] = firma_image

            # Renderizar documento en memoria
            doc.render(context)

            # Diálogo para que el usuario elija dónde guardar
            # Agregamos un nombre inicial que incluya fecha/hora
            nombre_predeterminado = f"libro_clases_{libro_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"

            save_path = filedialog.asksaveasfilename(
                title="Guardar libro de clases",
                initialfile=nombre_predeterminado,
                defaultextension=".docx",
                filetypes=[("Documento Word", "*.docx"), ("Todos los archivos", "*.*")]
            )

            if not save_path:
                # El usuario canceló el guardado
                return

            # Guardar documento en la ruta elegida
            doc.save(save_path)

            # Borrar la firma temporal, si existe
            temp_firma = os.path.join(os.path.dirname(__file__), 'temp_firma.png')
            if os.path.exists(temp_firma):
                os.remove(temp_firma)

            messagebox.showinfo("Éxito", f"Libro de clases generado exitosamente:\n{save_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar libro: {str(e)}")


    def _clear_form(self):
        """
        Limpia todos los campos del formulario.
        """
        self.selected_carpeta.set('')
        self.selected_libro.set('')
        self.firma_path.set('')
        self.firma_label.config(text="No se ha seleccionado firma")
        self._load_carpetas()


# --------------------------------------------------------------------
# Ejemplo de uso: si quieres usarlo en un script principal,
# puedes incluir algo como esto al final:

if __name__ == "__main__":
    root = TkBase()  # Para permitir drag & drop si está disponible
    root.title("Generación de Libro de Clases")

    try:
        root.iconbitmap(resource_path("assets/logo1.ico"))
    except:
        pass  # Si falla, simplemente no aplica el icono
    
    # (Opcional) Aplicar un estilo de tema
    style = ttk.Style(root)
    # style.theme_use('clam')

    app = LibroClasesFrame(root)
    app.pack(fill=tk.BOTH, expand=True)

    root.mainloop()
