import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime, timedelta
import traceback
from database.db_config import connect_db
from path_utils import resource_path

class LibrosManager:
    def __init__(self, root):
        """Inicializa el gestor de libros"""
        self.root = root
        self.current_carpeta = None
        self.current_libro = None
        self.widgets = {}  # Para almacenar referencias a widgets importantes
        self.setup_styles()
        self.setup_main_window()
        
    
    def setup_styles(self):
        style = ttk.Style()
        style.configure('Action.TButton',
                font=('Helvetica', 10, 'bold'),
                padding=(10, 5),
                background='#00239c',
                foreground='white',
                relief='raised',  # Cambiado a raised para dar el efecto 3D
                borderwidth=1)    # Añadido borde

        style.map('Action.TButton',
                    background=[('active', '#001970'),
                            ('pressed', '#00239c')],
                    foreground=[('active', 'white'),
                            ('pressed', 'white')],
                    relief=[('pressed', 'sunken')])  # Efecto presionado

        style.configure('delete.TButton',
                        font=('Helvetica', 10, 'bold'),
                        padding=(10, 5),
                        background='#b50707',
                        foreground='white',
                        relief='raised',  # Cambiado a raised para dar el efecto 3D
                        borderwidth=1)    # Añadido borde

        style.map('delete.TButton',
                    background=[('active', '#990606'),
                            ('pressed', '#b50707')],
                    foreground=[('active', 'white'),
                            ('pressed', 'white')],
                    relief=[('pressed', 'sunken')])  # Efecto presionado

    def setup_main_window(self):
        """Configura la ventana principal"""
        self.window = tk.Toplevel(self.root)
        self.window.title("Gestión de Libros de Clase")
        self.window.state("zoomed")
        try:
            self.window.iconbitmap(resource_path("assets/logo1.ico"))
        except:
            pass
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Estilo
        style = ttk.Style()
        style.configure("Header.TLabel", font=('Segoe UI', 12, 'bold'))
        
        # Frame principal
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Header
        self.setup_header()
        
        # Contenido
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

    def setup_header(self):
        """Configura el encabezado con título y navegación"""
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=5)
        
        self.title_label = ttk.Label(
            self.header_frame,
            text="",
            style="Header.TLabel"
        )
        self.title_label.pack(side=tk.LEFT, padx=5)
        
        self.back_button = ttk.Button(
            self.header_frame,
            text="← Volver",
            style="Action.TButton",
            command=self.go_back
        )

    def clear_content(self):
        """Limpia el contenido del frame principal"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.widgets.clear()

    def show_libros(self, carpeta_info):
        """Muestra los libros de una carpeta"""
        self.current_carpeta = carpeta_info
        self.current_libro = None
        
        # Actualizar título y mostrar botón volver
        self.title_label.config(text=f"Libros - Carpeta N° {carpeta_info[1]}")
        self.back_button.pack(side=tk.RIGHT, padx=5)
        
        # Limpiar contenido
        self.clear_content()
        
        # Información de la carpeta
        info_frame = ttk.LabelFrame(
            self.content_frame,
            text="Información",
            padding=10
        )
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            info_frame,
            text=f"N° Acta: {carpeta_info[1]}"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            info_frame,
            text=f"Curso: {carpeta_info[3]}"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            info_frame,
            text=f"Total Alumnos: {carpeta_info[7]}"
        ).pack(side=tk.LEFT, padx=5)
        
        # Botones
        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            button_frame,
            text="+ Crear Libro",
            command=lambda: self.crear_libro(carpeta_info[0]),
            style="Action.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        # Lista de libros
        tree_frame = ttk.Frame(self.content_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar Treeview
        self.setup_libros_tree(tree_frame)
        
        # Cargar datos
        self.cargar_libros(carpeta_info[0])

    def setup_libros_tree(self, parent_frame):
        """Configura el Treeview para la lista de libros"""
        columns = (
            "id", "asignatura", "instructor", "res_directemar",
            "horas_totales", "estado", "ultima_actualizacion"
        )
        
        headers = (
            "ID", "Asignatura", "Instructor", "N° Res. Directemar",
            "Horas Totales", "Estado", "Última Actualización"
        )
        
        # Scrollbars
        vsb = ttk.Scrollbar(parent_frame, orient="vertical")
        hsb = ttk.Scrollbar(parent_frame, orient="horizontal")
        
        # Treeview
        self.libros_tree = ttk.Treeview(
            parent_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=15
        )
        
        # Configurar scrollbars
        self.libros_tree.configure(
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        vsb.configure(command=self.libros_tree.yview)
        hsb.configure(command=self.libros_tree.xview)
        
        # Grid
        self.libros_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)
        
        # Configurar columnas
        widths = {
            "id": 60,
            "asignatura": 300,
            "instructor": 200,
            "res_directemar": 150,
            "horas_totales": 100,
            "estado": 100,
            "ultima_actualizacion": 150
        }
        
        for col, header in zip(columns, headers):
            self.libros_tree.heading(col, text=header, anchor=tk.CENTER)
            self.libros_tree.column(
                col,
                width=widths.get(col, 100),
                minwidth=50,
                anchor=tk.CENTER
            )
        
        # Configurar tags
        self.libros_tree.tag_configure('activo', background='#90EE90')
        self.libros_tree.tag_configure('finalizado', background='#FFB6C1')
        
        # Doble click
        self.libros_tree.bind("<Double-1>", self.on_libro_select)
        
        # Guardar referencia
        self.widgets['libros_tree'] = self.libros_tree

    def cargar_libros(self, id_carpeta):
        """Carga los libros de una carpeta"""
        try:
            # Limpiar árbol
            for item in self.libros_tree.get_children():
                self.libros_tree.delete(item)
                
            conn = connect_db()
            cursor = conn.cursor(buffered=True)
            
            cursor.execute("""
                SELECT 
                    l.id_libro,
                    l.asignatura,
                    l.instructor,
                    l.n_res_directemar,
                    l.horas_totales,
                    l.estado,
                    MAX(cd.fecha) as ultima_actualizacion
                FROM libros_clase l
                LEFT JOIN contenidos_semanales cs ON l.id_libro = cs.id_libro
                LEFT JOIN contenidos_diarios cd ON cs.id_contenido = cd.id_contenido
                WHERE l.id_carpeta = %s
                GROUP BY l.id_libro, l.asignatura, l.instructor, 
                        l.n_res_directemar, l.horas_totales, l.estado
                ORDER BY l.asignatura ASC
            """, (id_carpeta,))
            
            libros = cursor.fetchall()
            
            for libro in libros:
                ultima_act = libro[6]
                fecha_str = 'Sin registros'
                
                if ultima_act is not None:
                    try:
                        fecha_str = ultima_act.strftime('%Y-%m-%d')
                    except AttributeError:
                        fecha_str = 'Sin registros'
                
                values = [
                    libro[0],        # id_libro
                    libro[1],        # asignatura
                    libro[2] or '',  # instructor
                    libro[3] or '',  # n_res_directemar
                    libro[4] or '',  # horas_totales
                    libro[5].upper() if libro[5] else 'ACTIVO',  # estado
                    fecha_str        # ultima_actualizacion
                ]
                
                tag = 'activo' if libro[5] == 'activo' else 'finalizado'
                self.libros_tree.insert("", "end", values=values, tags=(tag,))
                    
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Error al cargar libros: {str(e)}"
            )
            traceback.print_exc()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()


    def crear_libro(self, id_carpeta):
        """Abre la ventana para crear un nuevo libro"""
        dialogo = tk.Toplevel(self.window)
        dialogo.title("Crear Nuevo Libro")
        dialogo.geometry("500x400")
        try:
            dialogo.iconbitmap(resource_path("assets/logo1.ico"))
        except:
            pass
        dialogo.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(dialogo, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Campos
        campos = [
            ("Asignatura:", "asignatura"),
            ("Instructor:", "instructor"),
            ("N° Res. Directemar:", "res_directemar"),
            ("Horas Totales:", "horas_totales")
        ]
        
        entries = {}
        for i, (label, campo) in enumerate(campos):
            ttk.Label(
                main_frame,
                text=label
            ).grid(row=i, column=0, pady=5, sticky="w")
            
            entry = ttk.Entry(main_frame, width=40)
            entry.grid(row=i, column=1, pady=5, padx=5)
            entries[campo] = entry
        
        def guardar():
            # Validar asignatura
            if not entries['asignatura'].get().strip():
                messagebox.showwarning(
                    "Error",
                    "La asignatura es obligatoria",
                    parent=dialogo
                )
                return
            
            try:
                conn = connect_db()
                cursor = conn.cursor(buffered=True)
                
                # Insertar libro
                cursor.execute("""
                    INSERT INTO libros_clase (
                        id_carpeta,
                        asignatura,
                        instructor,
                        n_res_directemar,
                        horas_totales,
                        estado
                    ) VALUES (%s, %s, %s, %s, %s, 'activo')
                """, (
                    id_carpeta,
                    entries['asignatura'].get().strip(),
                    entries['instructor'].get().strip() or None,
                    entries['res_directemar'].get().strip() or None,
                    entries['horas_totales'].get().strip() or None
                ))
                
                conn.commit()
                messagebox.showinfo(
                    "Éxito",
                    "Libro creado exitosamente",
                    parent=dialogo
                )
                dialogo.destroy()
                
                # Recargar lista
                self.cargar_libros(id_carpeta)
                
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Error al crear libro: {str(e)}",
                    parent=dialogo
                )
                traceback.print_exc()
            finally:
                cursor.close()
                conn.close()
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(campos), column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame,
            text="Guardar",
            command=guardar,
            style="Action.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancelar",
            command=dialogo.destroy,
            style="delete.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        # Focus inicial
        entries['asignatura'].focus()

    def on_libro_select(self, event=None):
        """Maneja la selección de un libro"""
        selected = self.libros_tree.selection()
        if not selected:
            return
        
        libro_info = self.libros_tree.item(selected[0])['values']
        self.show_libro_detail(libro_info)

    def show_libro_detail(self, libro_info):
        """Muestra los detalles del libro seleccionado"""
        self.current_libro = libro_info
        
        # Actualizar título
        self.title_label.config(text=f"Libro - {libro_info[1]}")
        
        # Limpiar contenido
        self.clear_content()
        
        # Frame de información básica
        info_frame = ttk.LabelFrame(self.content_frame, text="Información del Libro", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Mostrar información básica
        ttk.Label(info_frame, text=f"Asignatura: {libro_info[1]}").pack(side=tk.LEFT, padx=5)
        ttk.Label(info_frame, text=f"Instructor: {libro_info[2] or 'No asignado'}").pack(side=tk.LEFT, padx=5)
        ttk.Label(info_frame, text=f"Estado: {libro_info[5]}").pack(side=tk.LEFT, padx=5)
        
        # Frame para botones
        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Botones principales
        ttk.Button(
            button_frame,
            text="✏️ Editar Información",
            command=lambda: self.show_edit_info(libro_info),
            style="Action.TButton",
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="📋 Ver Registros",
            command=lambda: self.show_registros(libro_info),
            style="Action.TButton",
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="📝 Registro Diario",
            command=lambda: self.show_registro_diario(libro_info),
            style="Action.TButton",
            width=20
        ).pack(side=tk.LEFT, padx=5)

    def show_edit_info(self, libro_info):
        """Muestra la vista de edición de información básica"""
        self.clear_content()
        
        # Frame principal
        form_frame = ttk.LabelFrame(self.content_frame, text="Editar Información", padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Campos
        campos = [
            ("Asignatura:", libro_info[1], "asignatura"),
            ("Instructor:", libro_info[2], "instructor"),
            ("N° Res. Directemar:", libro_info[3], "res_directemar"),
            ("Horas Totales:", libro_info[4], "horas_totales")
        ]
        
        entries = {}
        for i, (label, valor, campo) in enumerate(campos):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, pady=5, sticky="e", padx=5)
            entry = ttk.Entry(form_frame, width=40)
            entry.insert(0, valor or '')
            entry.grid(row=i, column=1, pady=5, padx=5, sticky="w")
            entries[campo] = entry
        
        def guardar_cambios():
            try:
                if not entries['asignatura'].get().strip():
                    messagebox.showwarning("Error", "La asignatura es obligatoria")
                    return
                    
                conn = connect_db()
                cursor = conn.cursor(buffered=True)
                
                cursor.execute("""
                    UPDATE libros_clase
                    SET asignatura = %s,
                        instructor = %s,
                        n_res_directemar = %s,
                        horas_totales = %s
                    WHERE id_libro = %s
                """, (
                    entries['asignatura'].get().strip(),
                    entries['instructor'].get().strip() or None,
                    entries['res_directemar'].get().strip() or None,
                    entries['horas_totales'].get().strip() or None,
                    libro_info[0]
                ))
                
                conn.commit()
                messagebox.showinfo("Éxito", "Cambios guardados exitosamente")
                
                # Actualizar la información actual
                libro_info_actualizado = list(libro_info)
                libro_info_actualizado[1] = entries['asignatura'].get().strip()
                libro_info_actualizado[2] = entries['instructor'].get().strip()
                libro_info_actualizado[3] = entries['res_directemar'].get().strip()
                libro_info_actualizado[4] = entries['horas_totales'].get().strip()
                
                # Mostrar la vista actualizada
                self.show_libro_detail(libro_info_actualizado)
                
                # Recargar la lista de libros
                if self.current_carpeta:
                    self.cargar_libros(self.current_carpeta[0])
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar cambios: {str(e)}")
                traceback.print_exc()
            finally:
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
        
        # Frame para botones
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=len(campos), column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame,
            text="💾 Guardar Cambios",
            style="Action.TButton",
            command=guardar_cambios
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="↩️ Volver",
            style="delete.TButton",
            command=lambda: self.show_libro_detail(libro_info)
        ).pack(side=tk.LEFT, padx=5)

    def show_registros(self, libro_info):
        """Muestra el historial de registros del libro"""
        self.clear_content()
        
        # Frame principal
        registros_frame = ttk.LabelFrame(self.content_frame, text="Historial de Registros", padding=10)
        registros_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Crear Treeview para mostrar registros
        tree_frame = ttk.Frame(registros_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("fecha", "contenido", "horas", "asistencia")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        # Configurar columnas
        tree.heading("fecha", text="Fecha")
        tree.heading("contenido", text="Contenido")
        tree.heading("horas", text="Horas")
        tree.heading("asistencia", text="% Asistencia")
        
        # Configurar anchos y alineación
        tree.column("fecha", width=100, anchor=tk.CENTER)
        tree.column("contenido", width=400, anchor=tk.W)
        tree.column("horas", width=100, anchor=tk.CENTER)
        tree.column("asistencia", width=100, anchor=tk.CENTER)
        
        # Agregar scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Cargar datos
        self.cargar_historial_registros(tree, libro_info[0])
        
        # Botón volver
        ttk.Button(
            registros_frame,
            text="↩️ Volver",
            style="Action.TButton",
            command=lambda: self.show_libro_detail(libro_info)
        ).pack(pady=10)

    def cargar_historial_registros(self, tree, id_libro):
        """Carga el historial de registros del libro"""
        try:
            conn = connect_db()
            cursor = conn.cursor(buffered=True)
            
            cursor.execute("""
                SELECT 
                    cd.fecha,
                    cd.contenido_tratado,
                    cd.horas_realizadas,
                    COUNT(CASE WHEN aa.estado_asistencia = 'presente' THEN 1 END) * 100.0 / COUNT(*) as porcentaje_asistencia
                FROM contenidos_semanales cs
                JOIN contenidos_diarios cd ON cs.id_contenido = cd.id_contenido
                LEFT JOIN asistencia_alumnos aa ON cd.id_contenido_diario = aa.id_contenido_diario
                WHERE cs.id_libro = %s
                GROUP BY cd.fecha, cd.contenido_tratado, cd.horas_realizadas
                ORDER BY cd.fecha DESC
            """, (id_libro,))
            
            for registro in cursor.fetchall():
                fecha = registro[0].strftime('%Y-%m-%d')
                contenido = registro[1][:50] + '...' if registro[1] and len(registro[1]) > 50 else registro[1]
                tree.insert("", "end", values=(
                    fecha,
                    contenido,
                    registro[2],
                    f"{registro[3]:.1f}%" if registro[3] is not None else "0.0%"
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar registros: {str(e)}")
            traceback.print_exc()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def cargar_alumnos(self):
        """Carga la lista de alumnos del curso según número de acta, año de inscripción y el mismo id_curso."""
        try:
            conn = connect_db()
            cursor = conn.cursor(buffered=True)
            
            cursor.execute("""
                SELECT DISTINCT
                    a.rut,
                    a.nombre,
                    a.apellido,
                    CONCAT(a.nombre, ' ', a.apellido) AS nombre_completo
                FROM carpeta_libros cl
                JOIN inscripciones i 
                    ON cl.numero_acta = i.numero_acta
                    AND i.anio_inscripcion = YEAR(cl.fecha_inicio)
                    AND i.id_curso = cl.id_curso
                JOIN alumnos a ON i.id_alumno = a.rut
                WHERE cl.id_carpeta = %s
                ORDER BY a.nombre, a.apellido
            """, (self.current_carpeta[0],))
            
            # Limpiar el árbol de asistencia
            for item in self.asistencia_tree.get_children():
                self.asistencia_tree.delete(item)
            
            # Insertar alumnos en el Treeview
            for alumno in cursor.fetchall():
                self.asistencia_tree.insert(
                    "", "end",
                    values=(alumno[3], "PRESENTE")  # Se muestra nombre_completo y estado inicial
                )
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar alumnos: {str(e)}")
            traceback.print_exc()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def show_registro_diario(self, libro_info):
        """Muestra la vista de registro diario (contenidos y asistencia)"""
        self.clear_content()
        
        # Frame principal
        main_frame = ttk.LabelFrame(self.content_frame, text="Registro Diario", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Frame para fecha y horas
        fecha_frame = ttk.Frame(main_frame)
        fecha_frame.pack(fill=tk.X, pady=5)
        
        # Fecha
        fecha_label_frame = ttk.Frame(fecha_frame)
        fecha_label_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(fecha_label_frame, text="Fecha:").pack(side=tk.LEFT)
        
        self.fecha_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        fecha_entry = ttk.Entry(fecha_label_frame, textvariable=self.fecha_var, width=10)
        fecha_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            fecha_label_frame,
            text="📅",
            width=3,
            command=self.mostrar_calendario
        ).pack(side=tk.LEFT)
        
        # Horas
        horas_label_frame = ttk.Frame(fecha_frame)
        horas_label_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(horas_label_frame, text="Horas realizadas:").pack(side=tk.LEFT)
        
        self.horas_var = tk.StringVar(value="0")
        horas_entry = ttk.Entry(horas_label_frame, textvariable=self.horas_var, width=5)
        horas_entry.pack(side=tk.LEFT, padx=5)
        
        # Frame para contenido y asistencia
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Frame izquierdo - Contenidos
        left_frame = ttk.LabelFrame(content_frame, text="Contenidos", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.contenido_text = tk.Text(left_frame, height=10)
        self.contenido_text.pack(fill=tk.BOTH, expand=True)
        
        # Frame derecho - Asistencia
        right_frame = ttk.LabelFrame(content_frame, text="Asistencia", padding=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Configurar Treeview para asistencia
        self.setup_asistencia_tree(right_frame)
        
        # Cargar lista de alumnos inicial
        self.cargar_alumnos()
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame,
            text="💾 Guardar Registro",
            style="Action.TButton",
            command=self.guardar_semana
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="↩️ Volver",
            style="delete.TButton",
            command=lambda: self.show_libro_detail(libro_info)
        ).pack(side=tk.LEFT, padx=5)


    def setup_info_tab(self, notebook, libro_info):
        """Configura la pestaña de información general"""
        info_frame = ttk.Frame(notebook, padding=10)
        notebook.add(info_frame, text="Información General")
        
        # Campos
        campos = [
            ("Asignatura:", libro_info[1], "asignatura"),
            ("Instructor:", libro_info[2], "instructor"),
            ("N° Res. Directemar:", libro_info[3], "res_directemar"),
            ("Horas Totales:", libro_info[4], "horas_totales")
        ]
        
        entries = {}
        for i, (label, valor, campo) in enumerate(campos):
            ttk.Label(
                info_frame,
                text=label
            ).grid(row=i, column=0, pady=5, sticky="e")
            entry = ttk.Entry(info_frame, width=40)
            entry.insert(0, valor or '')
            entry.grid(row=i, column=1, pady=5, padx=5, sticky="w")
            entries[campo] = entry
        
        def guardar_cambios():
            try:
                conn = connect_db()
                cursor = conn.cursor(buffered=True)
                
                cursor.execute("""
                    UPDATE libros_clase
                    SET asignatura = %s,
                        instructor = %s,
                        n_res_directemar = %s,
                        horas_totales = %s
                    WHERE id_libro = %s
                """, (
                    entries['asignatura'].get().strip(),
                    entries['instructor'].get().strip() or None,
                    entries['res_directemar'].get().strip() or None,
                    entries['horas_totales'].get().strip() or None,
                    libro_info[0]
                ))
                
                conn.commit()
                messagebox.showinfo("Éxito", "Cambios guardados exitosamente")
                
                # Actualizar vista de libros
                self.show_libros(self.current_carpeta)
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar cambios: {str(e)}")
                traceback.print_exc()
            finally:
                cursor.close()
                conn.close()
        
        ttk.Button(
            info_frame,
            text="Guardar Cambios",
            style="Action.TButton",
            command=guardar_cambios
        ).grid(row=len(campos), column=0, columnspan=2, pady=20)

    def setup_contenidos_tab(self, notebook, libro_info):
        """Configura la pestaña de contenidos y asistencia"""
        contenidos_frame = ttk.Frame(notebook, padding=10)
        notebook.add(contenidos_frame, text="Contenidos y Asistencia")
        
        # Marco superior para fecha
        fecha_frame = ttk.LabelFrame(
            contenidos_frame,
            text="Registro Semanal",
            padding=10
        )
        fecha_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            fecha_frame,
            text="Fecha:"
        ).pack(side=tk.LEFT, padx=5)
        
        # Variable para la fecha
        self.fecha_var = tk.StringVar(
            value=datetime.now().strftime('%Y-%m-%d')
        )
        
        # Entry para la fecha
        self.fecha_entry = ttk.Entry(
            fecha_frame,
            textvariable=self.fecha_var,
            width=10
        )
        self.fecha_entry.pack(side=tk.LEFT, padx=5)
        
        # Botón calendario
        ttk.Button(
            fecha_frame,
            text="📅",
            width=3,
            command=self.mostrar_calendario
        ).pack(side=tk.LEFT)
        
        # Marco para contenidos y asistencia
        datos_frame = ttk.Frame(contenidos_frame)
        datos_frame.pack(fill=tk.BOTH, expand=True)
        
        # Columna izquierda: Contenidos
        izq_frame = ttk.LabelFrame(
            datos_frame,
            text="Contenidos",
            padding=10
        )
        izq_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.contenido_text = tk.Text(
            izq_frame,
            height=10,
            width=40
        )
        self.contenido_text.pack(fill=tk.BOTH, expand=True)
        
        # Columna derecha: Asistencia
        der_frame = ttk.LabelFrame(
            datos_frame,
            text="Asistencia",
            padding=10
        )
        der_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Configurar Treeview de asistencia
        self.setup_asistencia_tree(der_frame)
        
        # Botones
        button_frame = ttk.Frame(contenidos_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        
        ttk.Button(
            button_frame,
            text="Guardar Registro",
            style="Action.TButton", 
            command=self.guardar_semana
        ).pack(side=tk.LEFT, padx=5)
        

    def setup_asistencia_tree(self, parent_frame):
        """Configura el Treeview para la asistencia"""
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear Treeview
        self.asistencia_tree = ttk.Treeview(
            tree_frame,
            columns=("alumno", "estado"),
            show="headings",
            height=10
        )
        
        # Configurar columnas
        self.asistencia_tree.heading("alumno", text="Alumno")
        self.asistencia_tree.heading("estado", text="Estado")
        
        self.asistencia_tree.column("alumno", width=200, anchor=tk.W)
        self.asistencia_tree.column("estado", width=100, anchor=tk.CENTER)
        
        # Scrollbar
        vsb = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.asistencia_tree.yview
        )
        self.asistencia_tree.configure(yscrollcommand=vsb.set)
        
        # Grid
        self.asistencia_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Doble click para cambiar estado
        self.asistencia_tree.bind('<Double-1>', self.cambiar_estado_asistencia)
        
        # Guardar referencia
        self.widgets['asistencia_tree'] = self.asistencia_tree

    def mostrar_calendario(self):
        """Muestra el selector de fecha"""
        def set_fecha():
            self.fecha_var.set(cal.selection_get().strftime('%Y-%m-%d'))
            top.destroy()
            
        
        top = tk.Toplevel(self.window)
        top.title("Seleccionar Fecha")
        top.geometry('300x250')
        try:
            top.iconbitmap(resource_path("assets/logo1.ico"))
        except:
            pass
        
        cal = Calendar(
            top,
            selectmode='day',
            date_pattern='y-mm-dd'
        )
        cal.pack(pady=10)
        
        ttk.Button(
            top,
            text="Seleccionar",
            command=set_fecha
        ).pack()

    def cambiar_estado_asistencia(self, event):
        """Cambia el estado de asistencia al hacer doble click"""
        selected_item = self.asistencia_tree.selection()
        if not selected_item:
            return
        
        item = selected_item[0]
        current = self.asistencia_tree.item(item)['values'][1]
        estados = ['PRESENTE', 'AUSENTE']
        
        try:
            next_estado = estados[(estados.index(current) + 1) % len(estados)]
            self.asistencia_tree.set(item, 'estado', next_estado)
        except ValueError:
            self.asistencia_tree.set(item, 'estado', 'PRESENTE')


    def guardar_semana(self):
        """Guarda los datos del registro diario"""
        try:
            # Validar horas
            try:
                horas = float(self.horas_var.get())
                if horas < 0:
                    messagebox.showwarning("Error", "Las horas no pueden ser negativas")
                    return
            except ValueError:
                messagebox.showwarning("Error", "El valor de horas debe ser un número")
                return
            
            conn = connect_db()
            cursor = conn.cursor(buffered=True)
            
            # Iniciar transacción
            conn.start_transaction()
            
            try:
                fecha_seleccionada = datetime.strptime(self.fecha_var.get(), '%Y-%m-%d')
                semana_actual = fecha_seleccionada.isocalendar()[1]
                
                # Crear/obtener contenido semanal
                cursor.execute("""
                    INSERT INTO contenidos_semanales (
                        id_libro, semana, fecha_inicio, fecha_fin
                    ) VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        id_contenido = LAST_INSERT_ID(id_contenido)
                """, (
                    self.current_libro[0],
                    semana_actual,
                    fecha_seleccionada - timedelta(days=fecha_seleccionada.weekday()),
                    fecha_seleccionada + timedelta(days=6 - fecha_seleccionada.weekday())
                ))
                
                id_contenido = cursor.lastrowid
                
                # Crear/actualizar contenido diario
                cursor.execute("""
                    INSERT INTO contenidos_diarios (
                        id_contenido, fecha, contenido_tratado, horas_realizadas
                    ) VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        contenido_tratado = VALUES(contenido_tratado),
                        horas_realizadas = VALUES(horas_realizadas)
                """, (
                    id_contenido,
                    self.fecha_var.get(),
                    self.contenido_text.get('1.0', tk.END).strip(),
                    float(self.horas_var.get())
                ))
                
                # Obtener id del contenido diario
                cursor.execute("""
                    SELECT id_contenido_diario
                    FROM contenidos_diarios
                    WHERE id_contenido = %s AND fecha = %s
                """, (id_contenido, self.fecha_var.get()))
                
                id_contenido_diario = cursor.fetchone()[0]
                
                # Guardar asistencias
                for item in self.asistencia_tree.get_children():
                    alumno = self.asistencia_tree.item(item)['values']
                    estado = alumno[1].lower()
                    nombre_completo = alumno[0]
                    
                    cursor.execute("""
                        SELECT rut 
                        FROM alumnos 
                        WHERE CONCAT(nombre, ' ', apellido) = %s
                    """, (nombre_completo,))
                    
                    rut_alumno = cursor.fetchone()
                    if rut_alumno:
                        cursor.execute("""
                            INSERT INTO asistencia_alumnos (
                                id_contenido_diario, id_alumno, estado_asistencia
                            ) VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                estado_asistencia = VALUES(estado_asistencia)
                        """, (id_contenido_diario, rut_alumno[0], estado))
                
                conn.commit()
                messagebox.showinfo("Éxito", "Registro guardado exitosamente")
                
            except Exception as e:
                conn.rollback()
                raise e
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar registro: {str(e)}")
            traceback.print_exc()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def go_back(self):
        """Maneja la navegación hacia atrás"""
        if self.current_libro is not None:
            # Volver a la lista de libros
            self.show_libros(self.current_carpeta)
            self.current_libro = None
        elif self.current_carpeta is not None:
            # Cerrar la ventana
            self.close_window()

    def close_window(self):
        """Cierra la ventana y limpia las referencias"""
        try:
            if hasattr(self, 'window') and self.window.winfo_exists():
                self.window.destroy()
            
            # Limpiar referencias
            self.current_carpeta = None
            self.current_libro = None
            self.widgets.clear()
            
        except Exception as e:
            print(f"Error al cerrar ventana: {e}")
            traceback.print_exc()

def main():
    """Función principal para pruebas"""
    try:
        root = tk.Tk()
        root.withdraw()
        app = LibrosManager(root)
        root.mainloop()
    except Exception as e:
        print(f"Error en la aplicación: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()