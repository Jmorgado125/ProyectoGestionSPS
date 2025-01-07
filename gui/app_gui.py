import tkinter as tk
from tkinter import ttk, messagebox
import os
from PIL import Image, ImageTk
from datetime import datetime
from database.db_config import connect_db
from itertools import cycle  # <<--- Para el validador avanzado de RUT
from .excel_export import ExcelExporter
from tkinterdnd2 import DND_FILES, TkinterDnD
import base64

# ============================
#   Validador avanzado de RUT
# ============================
def validar_rut(rut):
    """
    Valida RUT chileno de forma más completa,
    usando itertools.cycle y validando rango.
    """
    rut = rut.upper().replace("-", "").replace(".", "")
    # Cuerpo del RUT sin el dígito verificador
    rut_aux = rut[:-1]
    # Dígito verificador
    dv = rut[-1:]

    # Validar que sea un número en rango posible
    if not rut_aux.isdigit() or not (1_000_000 <= int(rut_aux) <= 90_000_000):
        return False

    revertido = map(int, reversed(rut_aux))
    factors = cycle(range(2, 8))  # 2,3,4,5,6,7,2,3,4,...

    suma = sum(d * f for d, f in zip(revertido, factors))
    residuo = suma % 11

    if dv == 'K':
        return residuo == 1
    if dv == '0':
        return residuo == 11
    # Cualquier otro dígito, comparamos con 11 - residuo
    return residuo == 11 - int(dv)


# --------------------------------------------------------------------
#   IMPORTAR FUNCIONES DE LA BASE DE DATOS (queries.py o similares)
# --------------------------------------------------------------------

from database.queries import (
    fetch_courses,insert_course,update_course,delete_course_by_id,                       #Cursos
    validate_curso_exists,get_course_duration,add_business_days,


    fetch_courses_by_student_rut,fetch_all_students,insert_student,fetch_student_by_rut, #Alumnos
    delete_student_by_rut,fetch_students_by_name_apellido,validate_alumno_exists,

    fetch_payments,insert_payment,fetch_payments_by_inscription,                         #Pagos

    insert_invoice,fetch_invoices,                                                       #Facturas
    
    fetch_user_by_credentials,enroll_student,fetch_inscriptions,                         #Inscripciones
    update_inscription,update_student,validate_duplicate_enrollment,
    format_inscription_data,delete_inscription,fetch_inscription_by_id,
    get_course_duration, add_business_days,

    get_empresa_by_name,get_or_create_empresa,register_new_empresa,fetch_all_empresas,   #Empresas
    update_empresa,insert_empresa,fetch_contactos_by_empresa,fetch_empresa_by_rut,
    insert_contacto_empresa,update_contacto_empresa,delete_contacto_empresa
                     
)



class App:
    def __init__(self, root=None):
        # Aseguramos usar TkinterDnD.Tk
        if root is None or not isinstance(root, TkinterDnD.Tk):
            self.root = TkinterDnD.Tk()
        else:
            self.root = root

        # 1. Ocultamos la ventana inmediatamente
        self.root.withdraw()
        
        self.root.title("Gestión SPS")

        # 2. Maximizamos la ventana (pero sigue oculta)
        self.root.state('zoomed')
        self.root.resizable(True, True)

        # Configuración de estilos, etc.
        self.setup_styles()

        # 3. Cargamos los íconos mientras sigue oculta
        try:
            # Usar solo iconbitmap con tu .ico
            self.root.iconbitmap('assets/logo2.ico')
            # Si tu .ico es suficiente, comenta la siguiente línea:
            # self.root.call('wm', 'iconphoto', self.root._w, tk.PhotoImage(file='assets/logo2.ico'))
        except Exception as e:
            print(f"Error al cargar íconos: {e}")

        # Instanciamos lo que necesitemos (ej. ExcelExporter)
        self.excel_exporter = ExcelExporter()

        self.main_frame = None
        self.title_label = None

        # 4. Ahora que la ventana está configurada, la mostramos.
        self.root.deiconify()

        # 5. Mostramos directamente el LoginFrame (o la interfaz principal)
        self.show_login_frame()


    def setup_styles(self):
        """
        Configuración de estilos para toda la aplicación.
        """
        style = ttk.Style()
        style.theme_use('clam')

        # ========== Estilos para LOGIN ==========        
        style.configure("Login.TFrame", background="#0f075e")
        style.configure("Login.TLabel",
                        background="#0f075e",
                        foreground="white",
                        font=("Helvetica", 12))
        style.configure("Login.TButton",
                        font=("Helvetica", 11),
                        padding=5)

        # ========== Estilos para la interfaz principal ==========
        style.configure("Main.TFrame", background="#0f075e")

        style.configure("Treeview",
                        background="#ffffff",
                        foreground="black",
                        rowheight=25,
                        fieldbackground="#ffffff",
                        borderwidth=1,
                        font=('Segoe UI', 10))

        style.configure("Treeview.Heading",
                        background="#e1e1e1",
                        foreground="black",
                        relief="flat",
                        font=('Segoe UI', 10, 'bold'))

        style.map('Treeview',
                  background=[('selected', '#0078D7')],
                  foreground=[('selected', 'white')])

        style.configure("TButton",
                        padding=6,
                        relief="flat",
                        background="#0078D7",
                        foreground="black",
                        font=('Segoe UI', 10))

        style.configure("TLabel",
                        font=('Segoe UI', 10),
                        background="#f0f0f0")

        style.configure("Title.TLabel",
                        font=('Segoe UI', 14, 'bold'),
                        background="#0f075e",
                        foreground="white")

        style.configure('Action.TButton',
                        font=('Segoe UI', 10),
                        padding=5,
                        background='#00239c',
                        foreground='white')

        style.configure('Secondary.TButton',
                        font=('Segoe UI', 10),
                        padding=5)

    def show_login_frame(self):
        """
        Muestra el frame de Login usando LoginFrame.
        
        """

        if hasattr(self, 'main_frame') and self.main_frame:
            self.main_frame.destroy()

        # Importa tu LoginFrame (el que usa escalado en grupo)
        try:
            from gui.gui import LoginFrame
        except ImportError:
            from gui import LoginFrame

        def login_callback(username, password):
            """Valida credenciales contra la DB."""
            if not username or not password:
                messagebox.showwarning("Error", "Complete todos los campos")
                return

            user = fetch_user_by_credentials(username, password)
            if user:
                # Si las credenciales son correctas
                self.login_frame.hide()
                self.setup_main_interface()
            else:
                messagebox.showerror("Error", "Credenciales inválidas revice la escritura.")

        self.login_frame = LoginFrame(self.root, login_callback)
        self.root.bind('<Return>', lambda e: self.login_frame.handle_login())
        self.login_frame.show()

    def setup_main_interface(self):
        """
        Configura la ventana principal después de iniciar sesión.
        """


        # Frame principal
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header con fondo y título
        self.header_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        self.header_frame.pack(fill=tk.X)

        title_container = ttk.Frame(self.header_frame, style="Main.TFrame")
        title_container.pack(fill=tk.X, padx=10, pady=5)

        title_container.grid_columnconfigure(1, weight=1)

        # Label de título
        self.title_label = ttk.Label(
            title_container,
            text="",
            style="Title.TLabel",
            anchor="center"
        )
        self.title_label.grid(row=0, column=1, sticky="ew")

        # Botón de exportación con ícono
        self.export_button = tk.Button(
            title_container,
            image=self.excel_exporter.get_excel_icon(),  # Se usa la instancia ya creada
            bg="#0f075e",
            activebackground="#1a237e",
            bd=0,
            cursor="hand2",
            command=self._export_data
        )
        self.export_button.grid(row=0, column=2, padx=(10, 5))

        self._setup_button_hover_effects()
        self._setup_menu()
        self._setup_tree()

        # Mostrar inscripciones al inicio
        self.show_inscriptions()

    def _setup_button_hover_effects(self):
        """Configura los efectos hover para el botón de exportación"""
        def on_enter(e):
            self.export_button['background'] = '#1a237e'
            
        def on_leave(e):
            self.export_button['background'] = '#0f075e'
        
        self.export_button.bind("<Enter>", on_enter)
        self.export_button.bind("<Leave>", on_leave)

    def _export_data(self):
        """Maneja la exportación de datos a Excel"""
        title = self.title_label.cget('text')
        self.excel_exporter.export_to_excel(self.tree, title)

    def _setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menú Cursos
        cursos_menu = tk.Menu(menubar, tearoff=0)
        cursos_menu.add_command(label="Ver Cursos", command=self.show_courses)
        cursos_menu.add_command(label="Añadir Curso", command=self.add_course_window)
        cursos_menu.add_command(label="Editar Curso", command=self.edit_course_window)
        cursos_menu.add_command(label="Eliminar Curso", command=self.delete_course_window)
        menubar.add_cascade(label="Cursos", menu=cursos_menu)

        # Menú Alumnos
        alumnos_menu = tk.Menu(menubar, tearoff=0)
        alumnos_menu.add_command(label="Ver Alumnos", command=self.show_students)
        alumnos_menu.add_command(label="Añadir Alumno", command=self.add_student_window)
        alumnos_menu.add_command(label="Editar Alumno", command=self.edit_student_window)
        alumnos_menu.add_command(label="Buscar Alumno", command=self.search_student_window)
        alumnos_menu.add_command(label="Eliminar Alumno", command=self.delete_student_window)
        alumnos_menu.add_command(label="Cursos por Alumno", command=self.show_courses_by_student)
        menubar.add_cascade(label="Alumnos", menu=alumnos_menu)

        # Menú Inscripciones
        inscripciones_menu = tk.Menu(menubar, tearoff=0)
        inscripciones_menu.add_command(label="Ver Inscripciones", command=self.show_inscriptions)
        inscripciones_menu.add_command(label="Matricular Alumno", command=self.enroll_student_window)
        inscripciones_menu.add_command(label="Editar Inscripción", command=self.update_inscription_window) # <<--- Añadir función
        inscripciones_menu.add_command(label="Eliminar Inscripción", command=self.delete_inscription_window)
        inscripciones_menu.add_command(label="Inscripcion Masiva", command=self.show_bulk_enrollment)
        menubar.add_cascade(label="Inscripciones", menu=inscripciones_menu)

        # Menú Pagos
        pagos_menu = tk.Menu(menubar, tearoff=0)
        pagos_menu.add_command(label="Ver Pagos", command=self.show_payments)
        pagos_menu.add_command(label="Añadir Pago", command=self.add_payment_window)
        pagos_menu.add_command(label="Pagos por Inscripción", command=self.show_payments_by_inscription)
        menubar.add_cascade(label="Pagos", menu=pagos_menu)

        # Menú Facturación
        facturas_menu = tk.Menu(menubar, tearoff=0)
        facturas_menu.add_command(label="Ver Facturas", command=self.show_invoices)
        facturas_menu.add_command(label="Añadir Factura", command=self.add_invoice_window)
        menubar.add_cascade(label="Facturación", menu=facturas_menu)

        # Menú Tramitaciones
        tramitaciones_menu = tk.Menu(menubar, tearoff=0)
        # Podrías añadir ítems aquí si lo requieres
        # menubar.add_cascade(label="Tramitaciones", menu=tramitaciones_menu)

        # Menú Cotizaciones
        cotizaciones_menu = tk.Menu(menubar, tearoff=0)
        # menubar.add_cascade(label="Cotizaciones", menu=cotizaciones_menu)

        # Menú empresas
        empresas_menu = tk.Menu(menubar, tearoff=0)
        empresas_menu.add_command(label="Ver Empresas", command=self.show_empresas)
        empresas_menu.add_command(label="Añadir y Editar Empresa", command=self.add_edit_empresa_window)
        empresas_menu.add_command(label="Gestionar Contactos", command=self.manage_contacts_window)
        menubar.add_cascade(label="Empresas", menu=empresas_menu)
        
    def _setup_tree(self):
        """
        Configura el treeview para mostrar los datos.
        """
        # Frame contenedor del tree (directamente bajo main_frame)
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configurar el Treeview
        self.tree = ttk.Treeview(tree_frame, show="headings", selectmode="browse")

        # Scrollbars
        vscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll.grid(row=1, column=0, sticky="ew")

        # Configurar pesos de grid
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # Configurar tags para filas alternadas
        self.tree.tag_configure('oddrow', background='#f5f5f5')
        self.tree.tag_configure('evenrow', background='#ffffff')

    def _update_title_label(self, text):
        """
        Actualiza el texto del título.
        
        Args:
            text (str): El texto a mostrar en el título
        """
        if self.title_label:
            self.title_label.config(text=text)

    def _copy_cell_to_clipboard(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            row_id = self.tree.identify_row(event.y)
            col_id = self.tree.identify_column(event.x)
            if row_id and col_id:
                item = self.tree.item(row_id)
                col_index = int(col_id.replace("#", "")) - 1
                cell_value = item["values"][col_index]
                self.root.clipboard_clear()
                self.root.clipboard_append(str(cell_value))
                messagebox.showinfo("Copiado", f"Copiado al portapapeles:\n{cell_value}")

    def _populate_tree(self, columns, headers, data):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = columns

        # Anchos automáticos con límite de 300
        for col, head in zip(columns, headers):
            max_width = len(str(head)) * 10
            for row in data:
                try:
                    width = len(str(row[columns.index(col)])) * 10
                    max_width = max(max_width, width)
                except IndexError:
                    pass
            self.tree.heading(col, text=head, anchor=tk.W)
            self.tree.column(
                col,
                anchor=tk.W,
                width=min(max_width, 300),
                minwidth=100
            )

        for i, row in enumerate(data):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.tree.insert("", "end", values=row, tags=(tag,))

    # =================================================================
    #  INSCRIPCIONES (se muestran al iniciar)
    # =================================================================
    def show_inscriptions(self):
        try:
            if not hasattr(self, 'tree'):
                print("Error: tree no está inicializado")
                return
                    
            # Actualizar el título primero
            self._update_title_label("Listado de Inscripciones")
                    
            # Definir las columnas y headers
            columns = (
                "ID", "N_Acta", "RUT", "Nombre_Completo",
                "ID_Curso", "F_Inscripcion", "F_Termino",
                "Año", "Metodo", "Empresa", "Codigo_Sence", "Folio"
            )
                
            headers = (
                "ID", "N° Acta", "RUT", "Nombre Completo",
                "ID Curso", "F. Inscripción", "F. Término",
                "Año", "Método", "Empresa", "Código SENCE", "Folio"
            )

            # Obtener datos y formatearlos
            data_raw = fetch_inscriptions()
            formatted_data = []
                
            if data_raw:
                for inscription in data_raw:
                    formatted = format_inscription_data(inscription)
                    if formatted:
                        row = [
                            formatted.get("ID", ""),
                            formatted.get("N_Acta", ""),
                            formatted.get("RUT", ""),
                            formatted.get("Nombre_Completo", ""),
                            formatted.get("ID_Curso", ""),
                            formatted.get("F_Inscripcion", ""),
                            formatted.get("F_Termino", ""),
                            formatted.get("Año", ""),
                            formatted.get("Metodo", ""),
                            formatted.get("Empresa", ""),
                            formatted.get("Codigo_Sence", ""),
                            formatted.get("Folio", "")
                        ]
                        formatted_data.append(row)
                
            # Limpiar y configurar el tree
            self.tree.delete(*self.tree.get_children())
            self.tree.config(columns=columns, show="headings")
                
            # Configurar encabezados y columnas
            for column, header in zip(columns, headers):
                self.tree.heading(column, text=header, anchor=tk.CENTER)
                # Ajustar anchos según el tipo de columna
                if column in ["Nombre_Completo", "Empresa"]:
                    width = 200
                elif column in ["ID", "Año"]:
                    width = 70
                elif column in ["N_Acta"]:
                    width = 80
                else:
                    width = 100
                self.tree.column(column, width=width, minwidth=50, anchor=tk.CENTER)
                
            # Insertar datos si existen
            for item in formatted_data:
                self.tree.insert("", "end", values=item)
                    
        except Exception as e:
            print(f"Error al mostrar inscripciones: {e}")
            import traceback
            traceback.print_exc()

    def enroll_student_window(self):
        enroll_window = tk.Toplevel(self.root)
        enroll_window.title("Matricular Alumno")
        enroll_window.configure(bg="#f0f5ff")
        enroll_window.grab_set()
        enroll_window.focus_force()

        # Configuración de la ventana
        width, height = 450, 600  # Aumentado el height para los nuevos campos
        sw = enroll_window.winfo_screenwidth()
        sh = enroll_window.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        enroll_window.geometry(f"{width}x{height}+{x}+{y}")

        try:
            enroll_window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")

        # Frame principal
        main_frame = tk.Frame(enroll_window, bg="#f0f5ff", padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text="Matricular Alumno",
            font=("Helvetica", 16, "bold"),
            bg="#f0f5ff",
            fg="#022e86"
        )
        title_label.pack(pady=(0, 20))

        def create_label_entry(parent, label_text, validate_cmd=None):
            frame = tk.Frame(parent, bg="#f0f5ff")
            frame.pack(fill='x', pady=5)
            
            label = tk.Label(
                frame,
                text=label_text,
                bg="#f0f5ff",
                fg="#022e86",
                font=("Helvetica", 10),
                width=25,
                anchor='w'
            )
            label.pack(side=tk.LEFT, padx=(0, 10))
            
            entry = tk.Entry(
                frame,
                font=("Helvetica", 10),
                relief="solid",
                bd=1,
                width=25
            )
            if validate_cmd:
                entry.config(validate='focusout', validatecommand=validate_cmd)
            entry.pack(side=tk.LEFT, fill='x', expand=True)
            return entry

        def create_label_display(parent, label_text, initial_value=""):
            frame = tk.Frame(parent, bg="#f0f5ff")
            frame.pack(fill='x', pady=5)
            
            label = tk.Label(
                frame,
                text=label_text,
                bg="#f0f5ff",
                fg="#022e86",
                font=("Helvetica", 10),
                width=25,
                anchor='w'
            )
            label.pack(side=tk.LEFT, padx=(0, 10))
            
            display_label = tk.Label(
                frame,
                text=initial_value,
                bg="white",
                font=("Helvetica", 10),
                relief="solid",
                bd=1,
                width=25,
                anchor='w'
            )
            display_label.pack(side=tk.LEFT, fill='x', expand=True)
            return display_label

        # Campos básicos con validación
        acta_entry = create_label_entry(main_frame, "N° Acta:")
        rut_entry = create_label_entry(main_frame, "RUT Alumno:")
        
        # Campo ID Curso
        id_curso_entry = create_label_entry(main_frame, "ID Curso:")

        # Fecha de inscripción (no editable)
        fecha_actual = datetime.now().strftime('%Y-%m-%d')
        fecha_inscripcion_label = create_label_display(main_frame, "Fecha Inscripción:", fecha_actual)

        # Label para nombre del curso
        nombre_curso_label = create_label_display(main_frame, "Nombre del Curso:")
        
        # Label para duración
        duracion_label = create_label_display(main_frame, "Duración (días):")

        # Label para fecha término
        fecha_termino_label = create_label_display(main_frame, "Fecha Término:")
        
        # Año de inscripción
        anio_entry = create_label_entry(main_frame, "Año Inscripción (YYYY):")
        anio_entry.insert(0, datetime.now().strftime('%Y'))

        def validate_rut_entry():
            rut = rut_entry.get().strip()
            if not validar_rut(rut):
                messagebox.showerror("Error", "RUT inválido", parent=enroll_window)
                rut_entry.focus()
                return False
            return True

        def update_course_info(event=None):
            curso_id = id_curso_entry.get().strip()
            # Limpiar campos si está vacío
            if not curso_id:
                nombre_curso_label.config(text="")
                fecha_termino_label.config(text="")
                duracion_label.config(text="")
                return

            conn = connect_db()
            if conn:
                try:
                    cursor = conn.cursor()
                    # Obtener información del curso
                    cursor.execute("""
                        SELECT nombre_curso, duracionDias 
                        FROM Cursos 
                        WHERE id_curso = %s
                    """, (curso_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        nombre_curso, duracion_dias = result
                        # Actualizar nombre del curso
                        nombre_curso_label.config(text=nombre_curso)
                        # Mostrar duración
                        duracion_label.config(text=str(duracion_dias))
                        
                        # Calcular fecha de término
                        fecha_inscripcion = datetime.strptime(fecha_actual, '%Y-%m-%d').date()
                        fecha_termino = add_business_days(fecha_inscripcion, duracion_dias)
                        fecha_termino_label.config(text=fecha_termino.strftime('%Y-%m-%d'))
                    else:
                        # Si no se encuentra el curso, limpiar campos
                        nombre_curso_label.config(text="")
                        fecha_termino_label.config(text="")
                        duracion_label.config(text="")
                finally:
                    conn.close()

        def validate_curso_entry():
            curso_id = id_curso_entry.get().strip()
            if not validate_curso_exists(curso_id):
                messagebox.showerror("Error", "El curso no existe", parent=enroll_window)
                id_curso_entry.focus()
                return False
            update_course_info()
            return True

        # Bindings para los campos
        rut_entry.bind('<FocusOut>', lambda e: validate_rut_entry())
        id_curso_entry.bind('<KeyRelease>', update_course_info)
        id_curso_entry.bind('<FocusOut>', lambda e: validate_curso_entry())

        # Frame para método de llegada
        metodo_frame = tk.LabelFrame(
            main_frame,
            text="Método de Llegada",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10)
        )
        metodo_frame.pack(fill='x', pady=10)

        # Variable para método de llegada
        metodo_var = tk.StringVar(value="PARTICULAR")

        # Frame para radiobuttons
        radio_frame = tk.Frame(metodo_frame, bg="#f0f5ff")
        radio_frame.pack(pady=5)

        tk.Radiobutton(
            radio_frame,
            text="Particular",
            variable=metodo_var,
            value="PARTICULAR",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10),
            command=lambda: toggle_empresa_fields(False)
        ).pack(side=tk.LEFT, padx=40)

        tk.Radiobutton(
            radio_frame,
            text="Empresa",
            variable=metodo_var,
            value="EMPRESA",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10),
            command=lambda: toggle_empresa_fields(True)
        ).pack(side=tk.LEFT, padx=40)

        # Frame para campos de empresa
        empresa_frame = tk.Frame(main_frame, bg="#f0f5ff")
        empresa_frame.pack(fill='x')

        nombre_empresa_entry = create_label_entry(empresa_frame, "Nombre de Empresa:")
        orden_sence_entry = create_label_entry(empresa_frame, "Orden SENCE:")
        id_folio_entry = create_label_entry(empresa_frame, "ID Folio:")
        empresa_frame.pack_forget()

        def toggle_empresa_fields(show):
            if show:
                empresa_frame.pack(fill='x', pady=5)
            else:
                empresa_frame.pack_forget()
                nombre_empresa_entry.delete(0, tk.END)
                orden_sence_entry.delete(0, tk.END)
                id_folio_entry.delete(0, tk.END)

        def validate_enrollment_data():
            # Validar campos requeridos
            if not all([
                acta_entry.get().strip(),
                rut_entry.get().strip(),
                id_curso_entry.get().strip(),
                anio_entry.get().strip()
            ]):
                messagebox.showwarning(
                    "Campos vacíos",
                    "Complete todos los campos requeridos.",
                    parent=enroll_window
                )
                return False

            # Validar RUT
            if not validate_rut_entry():
                return False

            # Validar curso
            if not validate_curso_exists(id_curso_entry.get().strip()):
                return False

            # Validar año
            try:
                anio = int(anio_entry.get().strip())
                if anio < 2000 or anio > 2100:  # Rango razonable
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Año de inscripción inválido",
                    parent=enroll_window
                )
                return False

            return True

        def save_enrollment():
            if not validate_enrollment_data():
                return

            # Obtener datos básicos
            numero_acta = acta_entry.get().strip()
            rut = rut_entry.get().strip()
            id_curso = id_curso_entry.get().strip()
            anio_inscripcion = int(anio_entry.get().strip())
            metodo_llegada = metodo_var.get()

            # Procesar datos de empresa
            nombre_empresa = None
            orden_sence = None
            id_folio = None

            if metodo_llegada == "EMPRESA":
                nombre_empresa = nombre_empresa_entry.get().strip()
                if nombre_empresa:
                    orden_sence = orden_sence_entry.get().strip() or None
                    id_folio = id_folio_entry.get().strip() or None

                    try:
                        if orden_sence:
                            orden_sence = int(orden_sence)
                        if id_folio:
                            id_folio = int(id_folio)
                    except ValueError:
                        messagebox.showerror(
                            "Error",
                            "Los campos numéricos de empresa deben ser números enteros",
                            parent=enroll_window
                        )
                        return

            # Validar inscripción duplicada
            if validate_duplicate_enrollment(rut, id_curso, anio_inscripcion):
                messagebox.showerror(
                    "Error",
                    "El alumno ya está inscrito en este curso para el año especificado",
                    parent=enroll_window
                )
                return

            try:
                fecha_inscripcion = datetime.strptime(fecha_actual, '%Y-%m-%d').date()
                
                success, message = enroll_student(
                    id_alumno=rut,
                    id_curso=id_curso,
                    numero_acta=numero_acta,
                    fecha_inscripcion=fecha_inscripcion,
                    anio_inscripcion=anio_inscripcion,
                    metodo_llegada=metodo_llegada,
                    nombre_empresa=nombre_empresa,
                    ordenSence=orden_sence,
                    idfolio=id_folio
                )

                if success:
                    messagebox.showinfo("Éxito", "Alumno matriculado correctamente", parent=enroll_window)
                    enroll_window.destroy()
                    self.show_inscriptions()
                else:
                    messagebox.showerror("Error al matricular", f"No se pudo matricular el alumno:\n{message}", parent=enroll_window)

            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Error al procesar la inscripción: {str(e)}",
                    parent=enroll_window
                )

        # Frame inferior para el botón
        button_frame = tk.Frame(enroll_window, bg="#f0f5ff", pady=20)
        button_frame.pack(side=tk.BOTTOM, fill='x')

        # Botón de guardar
        tk.Button(
            button_frame,
            text="Guardar",
            bg="#022e86",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=30,
            pady=10,
            cursor="hand2",
            width=15,
            command=save_enrollment
        ).pack()
 
    def delete_inscription_window(self):
        delete_window = tk.Toplevel(self.root)
        delete_window.title("Eliminar Inscripción")
        delete_window.configure(bg="#f0f5ff")
        delete_window.grab_set()
        delete_window.focus_force()

        # Configuración de la ventana
        width, height = 400, 200
        sw = delete_window.winfo_screenwidth()
        sh = delete_window.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        delete_window.geometry(f"{width}x{height}+{x}+{y}")

        try:
            delete_window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")

        # Frame principal
        main_frame = tk.Frame(delete_window, bg="#f0f5ff", padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text="Eliminar Inscripción",
            font=("Helvetica", 16, "bold"),
            bg="#f0f5ff",
            fg="#022e86"
        )
        title_label.pack(pady=(0, 20))

        # Frame para el campo de entrada
        input_frame = tk.Frame(main_frame, bg="#f0f5ff")
        input_frame.pack(fill='x', pady=10)

        # Label
        id_label = tk.Label(
            input_frame,
            text="ID Inscripción:",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10),
            width=15,
            anchor='w'
        )
        id_label.pack(side=tk.LEFT, padx=(0, 10))

        # Entry
        id_entry = tk.Entry(
            input_frame,
            font=("Helvetica", 10),
            relief="solid",
            bd=1,
            width=20
        )
        id_entry.pack(side=tk.LEFT, fill='x', expand=True)

        def confirm_delete():
            try:
                id_inscripcion = int(id_entry.get().strip())
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "El ID debe ser un número entero.",
                    parent=delete_window
                )
                return

            if messagebox.askyesno(
                "Confirmar Eliminación",
                "¿Está seguro de que desea eliminar esta inscripción?\nEsta acción no se puede deshacer.",
                parent=delete_window
            ):
                success, message = delete_inscription(id_inscripcion)
                if success:
                    messagebox.showinfo(
                        "Éxito",
                        message,
                        parent=delete_window
                    )
                    delete_window.destroy()
                    self.show_inscriptions()  # Actualizar la vista de inscripciones
                else:
                    messagebox.showerror(
                        "Error",
                        message,
                        parent=delete_window
                    )

        # Frame para botones
        button_frame = tk.Frame(main_frame, bg="#f0f5ff")
        button_frame.pack(pady=20)

        # Botón Eliminar
        tk.Button(
            button_frame,
            text="Eliminar",
            bg="#cc0000",  # Rojo para indicar acción peligrosa
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=confirm_delete
        ).pack(side=tk.LEFT, padx=5)

        # Botón Cancelar
        tk.Button(
            button_frame,
            text="Cancelar",
            bg="#666666",
            fg="white",
            font=("Helvetica", 10),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=delete_window.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def update_inscription_window(self):
        window = tk.Toplevel(self.root)
        window.title("Actualizar Inscripción")
        window.configure(bg="#f0f5ff")
        window.grab_set()
        window.focus_force()

        # Configuración de la ventana
        width, height = 800, 600
        scr_w = window.winfo_screenwidth()
        scr_h = window.winfo_screenheight()
        x = (scr_w // 2) - (width // 2)
        y = (scr_h // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

        try:
            window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar ícono: {e}")

        # Frame principal
        main_frame = tk.Frame(window, bg="#f0f5ff", padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text="Actualizar Inscripción",
            font=("Helvetica", 16, "bold"),
            bg="#f0f5ff",
            fg="#022e86"
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))

        # Variables
        id_alumno_var = tk.StringVar()
        id_curso_var = tk.StringVar()
        numero_acta_var = tk.StringVar()
        fecha_inscripcion_var = tk.StringVar()
        fecha_termino_var = tk.StringVar()
        anio_var = tk.StringVar()
        metodo_llegada_var = tk.StringVar()
        id_empresa_var = tk.StringVar()
        orden_sence_var = tk.StringVar()
        id_folio_var = tk.StringVar()

        def create_label_entry(parent, label_text, row, col, var=None):
            tk.Label(
                parent,
                text=label_text,
                bg="#f0f5ff",
                fg="#022e86",
                font=("Helvetica", 10),
                anchor='e'
            ).grid(row=row, column=col, padx=(10, 5), pady=10, sticky='e')
            
            entry = tk.Entry(
                parent,
                width=35,
                font=("Helvetica", 10),
                relief="solid",
                bd=1,
                textvariable=var
            )
            entry.grid(row=row, column=col+1, padx=(0, 20), pady=10, sticky='w')
            return entry

        # Frame para búsqueda de ID
        search_frame = tk.Frame(main_frame, bg="#f0f5ff")
        search_frame.grid(row=1, column=0, columnspan=4, pady=(0, 20))

        tk.Label(
            search_frame,
            text="ID Inscripción:",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10, "bold")
        ).pack(side='left', padx=5)

        id_inscripcion_entry = tk.Entry(
            search_frame,
            width=20,
            font=("Helvetica", 10),
            relief="solid",
            bd=1
        )
        id_inscripcion_entry.pack(side='left', padx=5)

        def load_inscription_data():
            id_inscripcion = id_inscripcion_entry.get().strip()
            if not id_inscripcion:
                messagebox.showwarning("Error", "Ingrese el ID de inscripción", parent=window)
                return
                
            # Aquí necesitarás crear una función que obtenga los datos de la inscripción
            inscription = fetch_inscription_by_id(id_inscripcion)  # Deberás crear esta función
            if not inscription:
                messagebox.showerror("Error", f"No se encontró inscripción con ID {id_inscripcion}", parent=window)
                return

            id_alumno_var.set(inscription[1] or "")
            id_curso_var.set(inscription[2] or "")
            numero_acta_var.set(inscription[8] or "")
            fecha_inscripcion_var.set(inscription[3] or "")
            fecha_termino_var.set(inscription[4] or "")
            anio_var.set(inscription[5] or "")
            metodo_llegada_var.set(inscription[6] or "")
            id_empresa_var.set(inscription[7] or "")
            orden_sence_var.set(inscription[9] or "")
            id_folio_var.set(inscription[10] or "")

        tk.Button(
            search_frame,
            text="Buscar",
            bg="#022e86",
            fg="white",
            font=("Helvetica", 10),
            relief="flat",
            padx=15,
            command=load_inscription_data
        ).pack(side='left', padx=5)

        # Configurar el grid
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(3, weight=1)

        # Campos - organizados en dos columnas
        create_label_entry(main_frame, "RUT Alumno:", 2, 0, id_alumno_var)
        create_label_entry(main_frame, "ID Curso:", 3, 0, id_curso_var)
        create_label_entry(main_frame, "Número Acta:", 4, 0, numero_acta_var)
        create_label_entry(main_frame, "Fecha Inscripción:", 5, 0, fecha_inscripcion_var)
        create_label_entry(main_frame, "Año:", 6, 0, anio_var)

        create_label_entry(main_frame, "Fecha Término:", 2, 2, fecha_termino_var)
        create_label_entry(main_frame, "ID Empresa:", 3, 2, id_empresa_var)
        create_label_entry(main_frame, "Orden SENCE:", 4, 2, orden_sence_var)
        create_label_entry(main_frame, "ID Folio:", 5, 2, id_folio_var)

        # Método de llegada (combobox)
        tk.Label(
            main_frame,
            text="Método de Llegada:",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10),
            anchor='e'
        ).grid(row=6, column=2, padx=(10, 5), pady=10, sticky='e')

        metodo_combo = ttk.Combobox(
            main_frame,
            values=["PARTICULAR", "EMPRESA"],
            state="readonly",
            width=33
        )
        metodo_combo.grid(row=6, column=3, padx=(0, 20), pady=10, sticky='w')

        def save_changes():
            id_inscripcion = id_inscripcion_entry.get().strip()
            if not id_inscripcion:
                messagebox.showwarning("Error", "Ingrese el ID de inscripción", parent=window)
                return

            # Procesar empresa si se proporciona
            id_empresa = id_empresa_var.get().strip()
            if id_empresa and metodo_combo.get() == "EMPRESA":
                print(f"Procesando empresa: {id_empresa}")
                id_empresa = get_or_create_empresa(id_empresa)
                if id_empresa is None:
                    messagebox.showerror(
                        "Error",
                        "No se pudo procesar la empresa. Verifique el nombre.",
                        parent=window
                    )
                    return

            success, message = update_inscription(
                id_inscripcion=id_inscripcion,
                id_alumno=id_alumno_var.get().strip() or None,
                id_curso=id_curso_var.get().strip() or None,
                numero_acta=numero_acta_var.get().strip() or None,
                fecha_inscripcion=fecha_inscripcion_var.get().strip() or None,
                fecha_termino_condicional=fecha_termino_var.get().strip() or None,
                anio_inscripcion=anio_var.get().strip() or None,
                metodo_llegada=metodo_combo.get() or None,
                id_empresa=id_empresa,  # Aquí usamos el id_empresa procesado
                ordenSence=orden_sence_var.get().strip() or None,
                idfolio=id_folio_var.get().strip() or None
            )

            if success:
                messagebox.showinfo("Éxito", message, parent=window)
                window.destroy()
                self.show_inscriptions()
            else:
                messagebox.showerror("Error", message, parent=window)

            if success:
                messagebox.showinfo("Éxito", message, parent=window)
                window.destroy()
                self.show_inscriptions()
            else:
                messagebox.showerror("Error", message, parent=window)

        # Botón de guardar
        button_frame = tk.Frame(main_frame, bg="#f0f5ff")
        button_frame.grid(row=7, column=0, columnspan=4, pady=30)

        tk.Button(
            button_frame,
            text="Guardar Cambios",
            bg="#022e86",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=30,
            pady=10,
            cursor="hand2",
            command=save_changes
        ).pack()

    def show_bulk_enrollment(self):
        from gui.bulk_enrollment import BulkEnrollment
        bulk_window = BulkEnrollment(self.root)
    # ---------------------------------------------------
    #                 CURSOS
    # ---------------------------------------------------
    def show_courses(self):
        courses = fetch_courses()
        columns = (
            "id_curso",
            "nombre_curso",
            "modalidad",
            "codigo_sence",
            "codigo_elearning",
            "horas_cronologicas",
            "horas_pedagogicas",
            "valor",
            "duracionDias"
        )
        headers = (
            "ID",
            "Nombre",
            "Modalidad",
            "Código SENCE",
            "Código eLearning",
            "Hrs. Cron.",
            "Hrs. Pedag.",
            "Valor",
            "Duración (días)"
        )
        self._update_title_label("Listado de Cursos")
        self._populate_tree(columns, headers, courses)

        # Ajustar anchos de columna específicamente para cursos si es necesario
        if hasattr(self, 'tree'):
            # Columnas que necesitan más espacio
            self.tree.column("nombre_curso", width=300)  # Nombre más ancho
            self.tree.column("modalidad", width=100)
            self.tree.column("id_curso", width=80)
            self.tree.column("codigo_sence", width=100)
            self.tree.column("codigo_elearning", width=100)
            self.tree.column("horas_cronologicas", width=80)
            self.tree.column("horas_pedagogicas", width=80)
            self.tree.column("valor", width=100)
            self.tree.column("duracionDias", width=100)

    def add_course_window(self):
        """
        Ventana modernizada para añadir un nuevo curso.
        Layout mejorado con diseño en dos columnas.
        """
        window = tk.Toplevel(self.root)
        window.title("Añadir Curso")
        window.configure(bg="#f0f5ff")
        window.grab_set()  # Hace la ventana modal
        window.focus_force()

        # Configuración de la ventana
        width, height = 800, 500  # Aumenté un poco el height para el nuevo campo
        scr_w = window.winfo_screenwidth()
        scr_h = window.winfo_screenheight()
        x = (scr_w // 2) - (width // 2)
        y = (scr_h // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

        try:
            window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar ícono: {e}")

        # Frame principal
        main_frame = tk.Frame(window, bg="#f0f5ff", padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text="Registrar Nuevo Curso",
            font=("Helvetica", 16, "bold"),
            bg="#f0f5ff",
            fg="#022e86"
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))

        # Variables
        id_var = tk.StringVar()
        nombre_var = tk.StringVar()
        modalidad_var = tk.StringVar()
        sence_var = tk.StringVar()
        elearn_var = tk.StringVar()
        horas_cron_var = tk.StringVar()
        horas_pedag_var = tk.StringVar()
        valor_var = tk.StringVar()
        duracion_dias_var = tk.StringVar()  # Nueva variable

        def create_label_entry(parent, label_text, row, col, var=None, width=35):
            label = tk.Label(
                parent,
                text=label_text,
                bg="#f0f5ff",
                fg="#022e86",
                font=("Helvetica", 10),
                anchor='e'
            )
            label.grid(row=row, column=col, padx=(10, 5), pady=10, sticky='e')
            
            entry = tk.Entry(
                parent,
                width=width,
                font=("Helvetica", 10),
                relief="solid",
                bd=1,
                textvariable=var
            )
            entry.grid(row=row, column=col+1, padx=(0, 20), pady=10, sticky='w')
            return entry

        # Configurar el grid
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(3, weight=1)

        # Primera columna de campos
        create_label_entry(main_frame, "ID del Curso:", 1, 0, id_var)
        create_label_entry(main_frame, "Nombre:", 2, 0, nombre_var)
        create_label_entry(main_frame, "Modalidad:", 3, 0, modalidad_var)
        create_label_entry(main_frame, "Código SENCE:", 4, 0, sence_var)
        create_label_entry(main_frame, "Duración (días):", 5, 0, duracion_dias_var)  # Nuevo campo

        # Segunda columna de campos
        create_label_entry(main_frame, "Código eLearning:", 1, 2, elearn_var)
        create_label_entry(main_frame, "Horas Cronológicas:", 2, 2, horas_cron_var)
        
        # Label para horas pedagógicas (calculado automáticamente)
        horas_pedag_label = tk.Label(
            main_frame,
            text="Horas Pedagógicas: 0.0",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10)
        )
        horas_pedag_label.grid(row=3, column=2, columnspan=2, padx=(0, 20), pady=10, sticky='w')

        create_label_entry(main_frame, "Valor del Curso:", 4, 2, valor_var)

        def calculate_horas_pedagogicas(*args):
            try:
                horas_cron = float(horas_cron_var.get().strip())
                horas_pedagogicas = round(horas_cron * 4 / 3, 1)
                horas_pedag_label.config(text=f"Horas Pedagógicas: {horas_pedagogicas}")
            except ValueError:
                horas_pedag_label.config(text="Horas Pedagógicas: Error")

        horas_cron_var.trace('w', calculate_horas_pedagogicas)

        def save_course():
            # Obtener y validar datos
            id_curso = id_var.get().strip()
            nombre_curso = nombre_var.get().strip()
            modalidad = modalidad_var.get().strip()
            sence_text = sence_var.get().strip()
            elearn_text = elearn_var.get().strip()
            horas_cron_text = horas_cron_var.get().strip()
            valor_text = valor_var.get().strip()
            duracion_dias_text = duracion_dias_var.get().strip()  # Nuevo campo

            # Validaciones
            if not id_curso or not nombre_curso or not modalidad:
                messagebox.showwarning(
                    "Campos requeridos",
                    "El ID del Curso, el Nombre y la Modalidad son obligatorios.",
                    parent=window
                )
                return

            # Convertir y validar campos numéricos
            try:
                codigo_sence = int(sence_text) if sence_text else None
                codigo_elearn = int(elearn_text) if elearn_text else None
                horas_cron = float(horas_cron_text) if horas_cron_text else None
                valor_curso = float(valor_text) if valor_text else None
                duracion_dias = int(duracion_dias_text) if duracion_dias_text else None  # Nuevo campo
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Por favor, verifique los campos numéricos:\n" +
                    "- Código SENCE: debe ser número entero\n" +
                    "- Código eLearning: debe ser número entero\n" +
                    "- Horas Cronológicas: debe ser número decimal\n" +
                    "- Valor: debe ser número decimal\n" +
                    "- Duración: debe ser número entero",  # Nueva validación
                    parent=window
                )
                return

            # Guardar curso
            success = insert_course(
                id_curso=id_curso,
                nombre_curso=nombre_curso,
                modalidad=modalidad,
                codigo_sence=codigo_sence,
                codigo_elearning=codigo_elearn,
                horas_cronologicas=horas_cron,
                valor=valor_curso,
                duracionDias=duracion_dias  # Nuevo campo
            )

            if success:
                messagebox.showinfo("Éxito", "Curso añadido correctamente.", parent=window)
                self.show_courses()  # Actualizar la vista de cursos
                window.destroy()
            else:
                messagebox.showerror("Error", "No se pudo añadir el curso.", parent=window)

        # Frame para botones
        button_frame = tk.Frame(main_frame, bg="#f0f5ff")
        button_frame.grid(row=6, column=0, columnspan=4, pady=30)  # Actualizado el row

        # Botón de guardar
        tk.Button(
            button_frame,
            text="Guardar Curso",
            bg="#022e86",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=30,
            pady=10,
            cursor="hand2",
            command=save_course
        ).pack()

    def edit_course_window(self):
        """
        Ventana modernizada para editar un curso existente.
        Layout mejorado con diseño en dos columnas.
        """
        window = tk.Toplevel(self.root)
        window.title("Editar Curso")
        window.configure(bg="#f0f5ff")
        window.grab_set()
        window.focus_force()

        # Configuración de la ventana
        width, height = 800, 500  # Aumentado height para nuevo campo
        scr_w = window.winfo_screenwidth()
        scr_h = window.winfo_screenheight()
        x = (scr_w // 2) - (width // 2)
        y = (scr_h // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

        try:
            window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar ícono: {e}")

        # Frame principal
        main_frame = tk.Frame(window, bg="#f0f5ff", padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text="Editar Curso",
            font=("Helvetica", 16, "bold"),
            bg="#f0f5ff",
            fg="#022e86"
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))

        # Variables
        nombre_var = tk.StringVar()
        modalidad_var = tk.StringVar()
        sence_var = tk.StringVar()
        elearning_var = tk.StringVar()
        horas_cron_var = tk.StringVar()
        horas_pedag_var = tk.StringVar()
        valor_var = tk.StringVar()
        duracion_dias_var = tk.StringVar()  # Nueva variable

        # Frame para búsqueda de ID
        search_frame = tk.Frame(main_frame, bg="#f0f5ff")
        search_frame.grid(row=1, column=0, columnspan=4, pady=(0, 20))

        tk.Label(
            search_frame,
            text="ID del Curso:",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10, "bold")
        ).pack(side='left', padx=5)

        id_entry = tk.Entry(
            search_frame,
            width=20,
            font=("Helvetica", 10),
            relief="solid",
            bd=1
        )
        id_entry.pack(side='left', padx=5)

        def create_label_entry(parent, label_text, row, col, var=None, width=35):
            label = tk.Label(
                parent,
                text=label_text,
                bg="#f0f5ff",
                fg="#022e86",
                font=("Helvetica", 10),
                anchor='e'
            )
            label.grid(row=row, column=col, padx=(10, 5), pady=10, sticky='e')
            
            entry = tk.Entry(
                parent,
                width=width,
                font=("Helvetica", 10),
                relief="solid",
                bd=1,
                textvariable=var
            )
            entry.grid(row=row, column=col+1, padx=(0, 20), pady=10, sticky='w')
            return entry

        def load_course_data():
            id_curso = id_entry.get().strip()
            if not id_curso:
                messagebox.showwarning("Error", "Debe ingresar un ID de curso.", parent=window)
                return

            course = None
            try:
                conn = connect_db()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM Cursos WHERE id_curso = %s", (id_curso,))
                    course = cursor.fetchone()
                    cursor.close()
                    conn.close()
            except Exception as e:
                print("Error al buscar el curso:", e)
                messagebox.showerror("Error", "Error al buscar el curso en la base de datos.", parent=window)
                return

            if course:
                nombre_var.set(course[1] or "")
                modalidad_var.set(course[2] or "")
                sence_var.set(str(course[3]) if course[3] is not None else "")
                elearning_var.set(str(course[4]) if course[4] is not None else "")
                horas_cron_var.set(str(course[5]) if course[5] is not None else "")
                horas_pedag_var.set(str(course[6]) if course[6] is not None else "")
                valor_var.set(str(course[7]) if course[7] is not None else "")
                duracion_dias_var.set(str(course[8]) if course[8] is not None else "")  # Nuevo campo
                
                # Actualizar campos
                calculate_horas_pedagogicas()
            else:
                messagebox.showerror("Error", f"No se encontró el curso con ID: {id_curso}", parent=window)

        # Botón de búsqueda con estilo mejorado
        tk.Button(
            search_frame,
            text="Buscar",
            bg="#022e86",
            fg="white",
            font=("Helvetica", 10),
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2",
            command=load_course_data
        ).pack(side='left', padx=5)

        # Configurar el grid
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(3, weight=1)

        # Primera columna de campos
        create_label_entry(main_frame, "Nombre:", 2, 0, nombre_var)
        create_label_entry(main_frame, "Modalidad:", 3, 0, modalidad_var)
        create_label_entry(main_frame, "Código SENCE:", 4, 0, sence_var)
        create_label_entry(main_frame, "Duración (días):", 5, 0, duracion_dias_var)  # Nuevo campo

        # Segunda columna de campos
        create_label_entry(main_frame, "Código eLearning:", 2, 2, elearning_var)
        create_label_entry(main_frame, "Horas Cronológicas:", 3, 2, horas_cron_var)
        
        # Label para horas pedagógicas
        horas_pedag_label = tk.Label(
            main_frame,
            text="Horas Pedagógicas: 0.0",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10)
        )
        horas_pedag_label.grid(row=4, column=2, columnspan=2, padx=(0, 20), pady=10, sticky='w')

        def calculate_horas_pedagogicas(*args):
            try:
                horas_cron = float(horas_cron_var.get().strip())
                horas_pedagogicas = round(horas_cron * 4 / 3, 1)
                horas_pedag_label.config(text=f"Horas Pedagógicas: {horas_pedagogicas}")
                horas_pedag_var.set(str(horas_pedagogicas))
            except ValueError:
                horas_pedag_label.config(text="Horas Pedagógicas: Error")
                horas_pedag_var.set("")

        horas_cron_var.trace('w', calculate_horas_pedagogicas)

        create_label_entry(main_frame, "Valor del Curso:", 5, 2, valor_var)

        def save_edited_course():
            id_curso = id_entry.get().strip()
            if not id_curso:
                messagebox.showwarning("Error", "Debe ingresar un ID de curso.", parent=window)
                return

            # Obtener y validar datos
            nombre = nombre_var.get().strip()
            modalidad = modalidad_var.get().strip()
            sence_text = sence_var.get().strip()
            elearn_text = elearning_var.get().strip()
            horas_cron_text = horas_cron_var.get().strip()
            valor_text = valor_var.get().strip()
            duracion_dias_text = duracion_dias_var.get().strip()  # Nuevo campo

            # Validaciones básicas
            if not nombre or not modalidad:
                messagebox.showwarning(
                    "Campos requeridos",
                    "El Nombre y la Modalidad son obligatorios.",
                    parent=window
                )
                return

            # Convertir y validar campos numéricos
            try:
                codigo_sence = int(sence_text) if sence_text else None
                codigo_elearn = int(elearn_text) if elearn_text else None
                horas_cron = float(horas_cron_text) if horas_cron_text else None
                horas_pedag = float(horas_pedag_var.get()) if horas_pedag_var.get() else None
                valor_curso = float(valor_text) if valor_text else None
                duracion_dias = int(duracion_dias_text) if duracion_dias_text else None  # Nuevo campo
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Por favor, verifique los campos numéricos:\n" +
                    "- Código SENCE: debe ser número entero\n" +
                    "- Código eLearning: debe ser número entero\n" +
                    "- Horas Cronológicas: debe ser número decimal\n" +
                    "- Valor: debe ser número decimal\n" +
                    "- Duración: debe ser número entero",  # Nueva validación
                    parent=window
                )
                return

            # Actualizar curso
            success = update_course(
                id_curso=id_curso,
                nombre_curso=nombre,
                modalidad=modalidad,
                codigo_sence=codigo_sence,
                codigo_elearning=codigo_elearn,
                horas_cronologicas=horas_cron,
                horas_pedagogicas=horas_pedag,
                valor=valor_curso,
                duracionDias=duracion_dias  # Nuevo campo
            )

            if success:
                messagebox.showinfo("Éxito", "Curso actualizado correctamente.", parent=window)
                self.show_courses()
                window.destroy()
            else:
                messagebox.showerror("Error", "No se pudo actualizar el curso.", parent=window)

        # Frame para botones
        button_frame = tk.Frame(main_frame, bg="#f0f5ff")
        button_frame.grid(row=7, column=0, columnspan=4, pady=30)  # Actualizado el row

        # Botón de guardar
        tk.Button(
            button_frame,
            text="Guardar Cambios",
            bg="#022e86",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=30,
            pady=10,
            cursor="hand2",
            command=save_edited_course
        ).pack()

    def delete_course_window(self):
        delete_window = tk.Toplevel(self.root)
        delete_window.title("Eliminar Curso") 
        delete_window.configure(bg="#f0f5ff")
        delete_window.grab_set()
        delete_window.focus_force()

        # Configuración de la ventana
        width, height = 400, 200
        sw = delete_window.winfo_screenwidth()
        sh = delete_window.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        delete_window.geometry(f"{width}x{height}+{x}+{y}")

        try:
            delete_window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")

        # Frame principal
        main_frame = tk.Frame(delete_window, bg="#f0f5ff", padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text="Eliminar Curso",
            font=("Helvetica", 16, "bold"),
            bg="#f0f5ff",
            fg="#022e86"
        )
        title_label.pack(pady=(0, 20))

        # Frame para el campo de entrada
        input_frame = tk.Frame(main_frame, bg="#f0f5ff")
        input_frame.pack(fill='x', pady=10)

        # Label
        id_label = tk.Label(
            input_frame,
            text="ID del Curso:",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10),
            width=15,
            anchor='w'
        )
        id_label.pack(side=tk.LEFT, padx=(0, 10))

        # Entry
        id_entry = tk.Entry(
            input_frame,
            font=("Helvetica", 10),
            relief="solid",
            bd=1,
            width=20
        )
        id_entry.pack(side=tk.LEFT, fill='x', expand=True)

        def confirm_delete():
            course_id = id_entry.get().strip()
            if not course_id:
                messagebox.showerror(
                    "Error", 
                    "Debe ingresar un ID de curso.",
                    parent=delete_window
                )
                return

            if messagebox.askyesno(
                "Confirmar Eliminación",
                "¿Está seguro de que desea eliminar este curso?\nEsta acción no se puede deshacer.",
                parent=delete_window
            ):
                success = delete_course_by_id(course_id)
                if success:
                    messagebox.showinfo(
                        "Éxito",
                        "Curso eliminado exitosamente.",
                        parent=delete_window
                    )
                    delete_window.destroy()
                    self.show_courses()  # Actualizar la vista de cursos
                else:
                    messagebox.showerror(
                        "Error",
                        "No se pudo eliminar el curso. Verifique el ID e intente nuevamente.",
                        parent=delete_window
                    )

        # Frame para botones
        button_frame = tk.Frame(main_frame, bg="#f0f5ff")
        button_frame.pack(pady=20)

        # Botón Eliminar
        tk.Button(
            button_frame,
            text="Eliminar",
            bg="#cc0000",  # Rojo para indicar acción peligrosa
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=confirm_delete
        ).pack(side=tk.LEFT, padx=5)

        # Botón Cancelar
        tk.Button(
            button_frame,
            text="Cancelar",
            bg="#666666",
            fg="white",
            font=("Helvetica", 10),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=delete_window.destroy
        ).pack(side=tk.LEFT, padx=5)

    # ---------------------------------------------------
    #                  ALUMNOS
    # ---------------------------------------------------
    def show_students(self):
        students = fetch_all_students()
        # Ajustar columnas si cambiaste la BD y eliminaste algunas
        columns = ("rut", "nombre", "apellido", "correo", "telefono",
                   "profesion", "direccion", "ciudad", "comuna")
        headers = ("RUT", "Nombre", "Apellido", "Correo", "Teléfono",
                   "Profesión", "Dirección", "Ciudad", "Comuna")
        self._update_title_label("Listado de Alumnos")
        self._populate_tree(columns, headers, students)

    def add_student_window(self):
            window = tk.Toplevel(self.root)
            window.title("Añadir Alumno")
            window.geometry("800x450")  # Más ancho, menos alto
            window.configure(bg="#f0f5ff")
            window.grab_set()
            window.focus_force()

            try:
                window.iconbitmap('assets/logo1.ico')
            except Exception as e:
                print(f"Error al cargar ícono de la ventana: {e}")

            # Centrar ventana
            sw = window.winfo_screenwidth()
            sh = window.winfo_screenheight()
            x = (sw // 2) - (800 // 2)
            y = (sh // 2) - (450 // 2)
            window.geometry(f"800x450+{x}+{y}")

            # Frame principal con dos columnas
            main_frame = tk.Frame(window, bg="#f0f5ff", padx=30, pady=20)
            main_frame.pack(fill='both', expand=True)

            # Título
            title_label = tk.Label(
                main_frame,
                text="Registro de Alumno",
                font=("Helvetica", 16, "bold"),
                bg="#f0f5ff",
                fg="#022e86"
            )
            title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))

            def create_label_entry(parent, label_text, row, col):
                tk.Label(
                    parent,
                    text=label_text,
                    bg="#f0f5ff",
                    fg="#022e86",
                    font=("Helvetica", 10),
                    anchor='e'
                ).grid(row=row, column=col, padx=(10, 5), pady=10, sticky='e')
                
                entry = tk.Entry(
                    parent,
                    width=35,
                    font=("Helvetica", 10),
                    relief="solid",
                    bd=1
                )
                entry.grid(row=row, column=col+1, padx=(0, 20), pady=10, sticky='w')
                return entry

            # Configurar el grid
            main_frame.grid_columnconfigure(1, weight=1)
            main_frame.grid_columnconfigure(3, weight=1)

            # Campos - organizados en dos columnas
            entries = []
            
            # Primera columna
            entries.append(create_label_entry(main_frame, "RUT:", 1, 0))
            entries.append(create_label_entry(main_frame, "Nombre:", 2, 0))
            entries.append(create_label_entry(main_frame, "Apellido:", 3, 0))
            entries.append(create_label_entry(main_frame, "Correo:", 4, 0))
            entries.append(create_label_entry(main_frame, "Teléfono:", 5, 0))
            
            # Segunda columna
            entries.append(create_label_entry(main_frame, "Profesión:", 1, 2))
            entries.append(create_label_entry(main_frame, "Dirección:", 2, 2))
            entries.append(create_label_entry(main_frame, "Ciudad:", 3, 2))
            entries.append(create_label_entry(main_frame, "Comuna:", 4, 2))

            def save():
                rut = entries[0].get().strip()
                nombre = entries[1].get().strip()
                apellido = entries[2].get().strip()
                correo = entries[3].get().strip() or None
                telefono = entries[4].get().strip() or None
                profesion = entries[5].get().strip() or None
                direccion = entries[6].get().strip() or None
                ciudad = entries[7].get().strip() or None
                comuna = entries[8].get().strip() or None

                if not validar_rut(rut):
                    messagebox.showerror("Error", "El RUT ingresado es inválido.", parent=window)
                    return

                success = insert_student(
                    rut,
                    nombre,
                    apellido,
                    correo,
                    telefono,
                    profesion,
                    direccion,
                    comuna,
                    ciudad
                )

                if success:
                    messagebox.showinfo("Éxito", "Alumno añadido correctamente", parent=window)
                    self.show_students()
                    window.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo añadir el alumno, ya existe.", parent=window)

            # Botón centrado en la parte inferior
            button_frame = tk.Frame(main_frame, bg="#f0f5ff")
            button_frame.grid(row=6, column=0, columnspan=4, pady=30)
            
            tk.Button(
                button_frame,
                text="Guardar",
                bg="#022e86",
                fg="white",
                font=("Helvetica", 10, "bold"),
                relief="flat",
                padx=30,
                pady=10,
                cursor="hand2",
                command=save
            ).pack()

    def search_student_window(self):
        window = tk.Toplevel(self.root)
        window.title("Buscar Alumno")
        window.configure(bg="#f0f5ff")
        window.grab_set()
        window.focus_force()

        # Configuración de la ventana
        width, height = 400, 300
        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

        try:
            window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar ícono: {e}")

        # Frame principal
        main_frame = tk.Frame(window, bg="#f0f5ff", padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text="Buscar Alumno",
            font=("Helvetica", 16, "bold"),
            bg="#f0f5ff",
            fg="#022e86"
        )
        title_label.pack(pady=(0, 20))

        # Frame para campos de búsqueda
        search_frame = tk.Frame(main_frame, bg="#f0f5ff")
        search_frame.pack(fill='x', pady=10)

        # Función para crear campos de entrada
        def create_entry_frame(parent, label_text):
            frame = tk.Frame(parent, bg="#f0f5ff")
            frame.pack(fill='x', pady=5)
            
            label = tk.Label(
                frame,
                text=label_text,
                bg="#f0f5ff",
                fg="#022e86",
                font=("Helvetica", 10),
                width=10,
                anchor='w'
            )
            label.pack(side=tk.LEFT, padx=(0, 10))
            
            entry = tk.Entry(
                frame,
                font=("Helvetica", 10),
                relief="solid",
                bd=1
            )
            entry.pack(side=tk.LEFT, fill='x', expand=True)
            return entry

        # Campos de búsqueda
        rut_entry = create_entry_frame(search_frame, "RUT:")
        nombre_entry = create_entry_frame(search_frame, "Nombre:")
        apellido_entry = create_entry_frame(search_frame, "Apellido:")

        def search():
            rut = rut_entry.get().strip()
            nombre = nombre_entry.get().strip()
            apellido = apellido_entry.get().strip()

            if not any([rut, nombre, apellido]):
                messagebox.showwarning(
                    "Error",
                    "Ingrese al menos un criterio de búsqueda",
                    parent=window
                )
                return

            students = []
            if rut:
                student = fetch_student_by_rut(rut)
                if student:
                    students = [student]
            elif nombre or apellido:
                students = fetch_students_by_name_apellido(nombre, apellido)

            if students:
                self._populate_tree(
                    ("rut", "nombre", "apellido", "correo", "telefono"),
                    ("RUT", "Nombre", "Apellido", "Correo", "Teléfono"),
                    students
                )
                self._update_title_label(f"Alumnos encontrados: {len(students)}")
                window.destroy()
            else:
                messagebox.showinfo(
                    "Información",
                    "No se encontraron alumnos con los criterios especificados.",
                    parent=window
                )

        # Frame para botones
        button_frame = tk.Frame(main_frame, bg="#f0f5ff")
        button_frame.pack(pady=20)

        # Botón Buscar
        tk.Button(
            button_frame,
            text="Buscar",
            bg="#022e86",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=search
        ).pack(side=tk.LEFT, padx=5)

        # Botón Cancelar
        tk.Button(
            button_frame,
            text="Cancelar",
            bg="#666666",
            fg="white",
            font=("Helvetica", 10),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=window.destroy
        ).pack(side=tk.LEFT, padx=5)

    def delete_student_window(self):
        delete_window = tk.Toplevel(self.root)
        delete_window.title("Eliminar Alumno")
        delete_window.configure(bg="#f0f5ff")
        delete_window.grab_set()
        delete_window.focus_force()

        # Configuración de la ventana
        width, height = 400, 200
        sw = delete_window.winfo_screenwidth()
        sh = delete_window.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        delete_window.geometry(f"{width}x{height}+{x}+{y}")

        try:
            delete_window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")

        # Frame principal
        main_frame = tk.Frame(delete_window, bg="#f0f5ff", padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text="Eliminar Alumno",
            font=("Helvetica", 16, "bold"),
            bg="#f0f5ff",
            fg="#022e86"
        )
        title_label.pack(pady=(0, 20))

        # Frame para el campo de entrada
        input_frame = tk.Frame(main_frame, bg="#f0f5ff")
        input_frame.pack(fill='x', pady=10)

        # Label
        rut_label = tk.Label(
            input_frame,
            text="RUT Alumno:",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10),
            width=15,
            anchor='w'
        )
        rut_label.pack(side=tk.LEFT, padx=(0, 10))

        # Entry
        rut_entry = tk.Entry(
            input_frame,
            font=("Helvetica", 10),
            relief="solid",
            bd=1,
            width=20
        )
        rut_entry.pack(side=tk.LEFT, fill='x', expand=True)

        def confirm_delete():
            rut = rut_entry.get().strip()
            if not rut:
                messagebox.showerror(
                    "Error",
                    "Debe ingresar un RUT.",
                    parent=delete_window
                )
                return

            if messagebox.askyesno(
                "Confirmar Eliminación",
                "¿Está seguro de que desea eliminar este alumno?\nEsta acción no se puede deshacer.",
                parent=delete_window
            ):
                if delete_student_by_rut(rut):
                    messagebox.showinfo(
                        "Éxito",
                        "Alumno eliminado exitosamente.",
                        parent=delete_window
                    )
                    delete_window.destroy()
                    self.show_students()  # Actualizar la vista de alumnos
                else:
                    messagebox.showerror(
                        "Error",
                        "No se pudo eliminar el alumno. Verifique el RUT e intente nuevamente.",
                        parent=delete_window
                    )

        # Frame para botones
        button_frame = tk.Frame(main_frame, bg="#f0f5ff")
        button_frame.pack(pady=20)

        # Botón Eliminar
        tk.Button(
            button_frame,
            text="Eliminar",
            bg="#cc0000",  # Rojo para indicar acción peligrosa
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=confirm_delete
        ).pack(side=tk.LEFT, padx=5)

        # Botón Cancelar
        tk.Button(
            button_frame,
            text="Cancelar",
            bg="#666666",
            fg="white",
            font=("Helvetica", 10),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=delete_window.destroy
        ).pack(side=tk.LEFT, padx=5)

    def show_courses_by_student(self):
        search_window = tk.Toplevel(self.root)
        search_window.title("Cursos por Alumno")
        search_window.configure(bg="#f0f5ff")
        search_window.grab_set()
        search_window.focus_force()

        # Configuración de la ventana
        width, height = 400, 200
        sw = search_window.winfo_screenwidth()
        sh = search_window.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        search_window.geometry(f"{width}x{height}+{x}+{y}")

        try:
            search_window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")

        # Frame principal
        main_frame = tk.Frame(search_window, bg="#f0f5ff", padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text="Buscar Cursos por Alumno",
            font=("Helvetica", 16, "bold"),
            bg="#f0f5ff",
            fg="#022e86"
        )
        title_label.pack(pady=(0, 20))

        # Frame para el campo de entrada
        input_frame = tk.Frame(main_frame, bg="#f0f5ff")
        input_frame.pack(fill='x', pady=10)

        # Label
        rut_label = tk.Label(
            input_frame,
            text="RUT Alumno:",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10),
            width=15,
            anchor='w'
        )
        rut_label.pack(side=tk.LEFT, padx=(0, 10))

        # Entry
        rut_entry = tk.Entry(
            input_frame,
            font=("Helvetica", 10),
            relief="solid",
            bd=1,
            width=20
        )
        rut_entry.pack(side=tk.LEFT, fill='x', expand=True)

        def search():
            rut = rut_entry.get().strip()
            if not rut:
                messagebox.showwarning(
                    "Error",
                    "Debe ingresar un RUT.",
                    parent=search_window
                )
                return

            courses = fetch_courses_by_student_rut(rut)
            if courses:
                self._populate_tree(
                    ("nombre_curso", "fecha_inscripcion"),
                    ("Curso", "Fecha Inscripción"),
                    courses
                )
                self._update_title_label(f"Cursos del Alumno: {rut}")
                messagebox.showinfo(
                    "Éxito",
                    f"Se encontraron {len(courses)} cursos para el RUT {rut}.",
                    parent=search_window
                )
                search_window.destroy()
            else:
                messagebox.showinfo(
                    "Información",
                    "No se encontraron cursos para el RUT indicado.",
                    parent=search_window
                )

        # Frame para botones
        button_frame = tk.Frame(main_frame, bg="#f0f5ff")
        button_frame.pack(pady=20)

        # Botón Buscar
        tk.Button(
            button_frame,
            text="Buscar",
            bg="#022e86",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=search
        ).pack(side=tk.LEFT, padx=5)

        # Botón Cancelar
        tk.Button(
            button_frame,
            text="Cancelar",
            bg="#666666",
            fg="white",
            font=("Helvetica", 10),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=search_window.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def edit_student_window(self):
            """
            Ventana para editar datos de un alumno existente.
            Diseño modernizado con layout horizontal.
            """
            window = tk.Toplevel(self.root)
            window.title("Editar Alumno")
            window.configure(bg="#f0f5ff")
            window.grab_set()
            window.focus_force()

            # Configuración de la ventana
            width, height = 800, 600
            scr_w = window.winfo_screenwidth()
            scr_h = window.winfo_screenheight()
            x = (scr_w // 2) - (width // 2)
            y = (scr_h // 2) - (height // 2)
            window.geometry(f"{width}x{height}+{x}+{y}")

            try:
                window.iconbitmap('assets/logo1.ico')
            except Exception as e:
                print(f"Error al cargar ícono: {e}")

            # Frame principal
            main_frame = tk.Frame(window, bg="#f0f5ff", padx=30, pady=20)
            main_frame.pack(fill='both', expand=True)

            # Título
            title_label = tk.Label(
                main_frame,
                text="Editar Datos del Alumno",
                font=("Helvetica", 16, "bold"),
                bg="#f0f5ff",
                fg="#022e86"
            )
            title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))

            # Variables
            nombre_var = tk.StringVar()
            apellido_var = tk.StringVar()
            correo_var = tk.StringVar()
            telefono_var = tk.StringVar()
            profesion_var = tk.StringVar()
            direccion_var = tk.StringVar()
            ciudad_var = tk.StringVar()
            comuna_var = tk.StringVar()

            def create_label_entry(parent, label_text, row, col, var=None):
                tk.Label(
                    parent,
                    text=label_text,
                    bg="#f0f5ff",
                    fg="#022e86",
                    font=("Helvetica", 10),
                    anchor='e'
                ).grid(row=row, column=col, padx=(10, 5), pady=10, sticky='e')
                
                entry = tk.Entry(
                    parent,
                    width=35,
                    font=("Helvetica", 10),
                    relief="solid",
                    bd=1,
                    textvariable=var
                )
                entry.grid(row=row, column=col+1, padx=(0, 20), pady=10, sticky='w')
                return entry

            # Frame para búsqueda de RUT
            search_frame = tk.Frame(main_frame, bg="#f0f5ff")
            search_frame.grid(row=1, column=0, columnspan=4, pady=(0, 20))

            tk.Label(
                search_frame,
                text="RUT del alumno:",
                bg="#f0f5ff",
                fg="#022e86",
                font=("Helvetica", 10, "bold")
            ).pack(side='left', padx=5)

            rut_entry = tk.Entry(
                search_frame,
                width=20,
                font=("Helvetica", 10),
                relief="solid",
                bd=1
            )
            rut_entry.pack(side='left', padx=5)

            def load_student_data():
                rut = rut_entry.get().strip()
                if not rut:
                    messagebox.showwarning("Error", "Ingrese el RUT", parent=window)
                    return
                st = fetch_student_by_rut(rut)
                if not st:
                    messagebox.showerror("Error", f"No se encontró alumno con RUT {rut}", parent=window)
                    return

                nombre_var.set(st[1] or "")
                apellido_var.set(st[2] or "")
                correo_var.set(st[3] or "")
                telefono_var.set(str(st[4]) if st[4] else "")
                profesion_var.set(st[5] or "")
                direccion_var.set(st[6] or "")
                comuna_var.set(st[7] or "")
                ciudad_var.set(st[8] or "")

            tk.Button(
                search_frame,
                text="Buscar",
                bg="#022e86",
                fg="white",
                font=("Helvetica", 10),
                relief="flat",
                padx=15,
                command=load_student_data
            ).pack(side='left', padx=5)

            # Configurar el grid
            main_frame.grid_columnconfigure(1, weight=1)
            main_frame.grid_columnconfigure(3, weight=1)

            # Campos - organizados en dos columnas
            create_label_entry(main_frame, "Nombre:", 2, 0, nombre_var)
            create_label_entry(main_frame, "Apellido:", 3, 0, apellido_var)
            create_label_entry(main_frame, "Correo:", 4, 0, correo_var)
            create_label_entry(main_frame, "Teléfono:", 5, 0, telefono_var)
            
            create_label_entry(main_frame, "Profesión:", 2, 2, profesion_var)
            create_label_entry(main_frame, "Dirección:", 3, 2, direccion_var)
            create_label_entry(main_frame, "Ciudad:", 4, 2, ciudad_var)
            create_label_entry(main_frame, "Comuna:", 5, 2, comuna_var)

            def save_edited_student():
                rut = rut_entry.get().strip()
                if not rut:
                    messagebox.showwarning("Error", "Ingrese el RUT para editar", parent=window)
                    return

                if not validar_rut(rut):
                    messagebox.showerror("Error", "El RUT ingresado es inválido.", parent=window)
                    return

                ok = update_student(
                    rut=rut,
                    nombre=nombre_var.get().strip(),
                    apellido=apellido_var.get().strip(),
                    correo=correo_var.get().strip() or None,
                    telefono=telefono_var.get().strip() or None,
                    profesion=profesion_var.get().strip() or None,
                    direccion=direccion_var.get().strip() or None,
                    comuna=comuna_var.get().strip() or None,
                    ciudad=ciudad_var.get().strip() or None
                )
                
                if ok:
                    messagebox.showinfo("Éxito", "Datos del alumno actualizados.", parent=window)
                    window.destroy()
                    self.show_students()
                else:
                    messagebox.showerror("Error", "No se pudo actualizar el alumno.", parent=window)

            # Botón de guardar
            button_frame = tk.Frame(main_frame, bg="#f0f5ff")
            button_frame.grid(row=6, column=0, columnspan=4, pady=30)

            tk.Button(
                button_frame,
                text="Guardar Cambios",
                bg="#022e86",
                fg="white",
                font=("Helvetica", 10, "bold"),
                relief="flat",
                padx=30,
                pady=10,
                cursor="hand2",
                command=save_edited_student
            ).pack()
    # ---------------------------------------------------
    #                  PAGOS
    # ---------------------------------------------------
    def show_payments(self):
        payments = fetch_payments()
        columns = (
            "id_pago", "id_inscripcion", "tipo_pago", "modalidad_pago",
            "num_documento", "cuotas_totales", "valor", "estado", "cuotas_pagadas"
        )
        headers = (
            "ID", "Inscripción", "Tipo", "Modalidad",
            "N° Documento", "Cuotas Totales", "Valor", "Estado", "Cuotas Pagadas"
        )
        self._update_title_label("Listado de Pagos")
        self._populate_tree(columns, headers, payments)

    def add_payment_window(self):
        self._generic_add_window(
            "Añadir Pago",
            insert_payment,
            [
                ("ID Inscripción:", int),
                ("Tipo de Pago(CONTADO/PAGARE):", None),
                ("Modalidad(COMPLETO/DIFERIDO):", None),
                ("N° Documento:", None),
                ("Cuotas Totales:", int),
                ("Valor:", float),
                ("Estado:", None),
                ("Cuotas Pagadas:", int)
            ]
        )

    def show_payments_by_inscription(self):
        window = tk.Toplevel(self.root)
        window.title("Pagos por Inscripción")

        try:
            window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar ícono: {e}")

        width, height = 300, 200
        window.geometry(f"{width}x{height}")
        window.update_idletasks()
        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.configure(bg="#022e86")

        try:
            logo = tk.PhotoImage(file='assets/logomarco.png')
            logo_label = tk.Label(window, image=logo, bg="#022e86")
            logo_label.image = logo
            logo_label.pack(pady=10)
        except Exception as e:
            print(f"Error al cargar logo: {e}")

        tk.Label(window, text="ID Inscripción:", bg="#022e86", fg="white").pack(pady=10)
        id_entry = tk.Entry(window, width=30)
        id_entry.pack(pady=5)

        def search():
            try:
                id_inscripcion = int(id_entry.get().strip())
                payments = fetch_payments_by_inscription(id_inscripcion)
                if payments:
                    columns = ("id_pago", "tipo_pago", "modalidad_pago", "valor", "estado")
                    headers = ("ID", "Tipo", "Modalidad", "Valor", "Estado")
                    self._populate_tree(columns, headers, payments)
                    self._update_title_label(f"Pagos de la Inscripción {id_inscripcion}")
                    messagebox.showinfo("Resultado", f"Se hallaron {len(payments)} pagos.")
                else:
                    messagebox.showinfo("Info", "No se encontraron pagos")
            except ValueError:
                messagebox.showerror("Error", "ID inválido")

            window.destroy()

        tk.Button(window, text="Buscar", bg="#ADD8E6", command=search).pack(pady=20)

    # ---------------------------------------------------
    #                  FACTURAS
    # ---------------------------------------------------
    def show_invoices(self):
        invoices = fetch_invoices()
        columns = ("id_factura", "id_inscripcion", "numero_factura", "monto_total", "estado")
        headers = ("ID", "Inscripción", "N° Factura", "Monto Total", "Estado")
        self._update_title_label("Listado de Facturas")
        self._populate_tree(columns, headers, invoices)

    def add_invoice_window(self):
        self._generic_add_window(
            "Añadir Factura",
            insert_invoice,
            [
                ("ID Inscripción:", int),
                ("N° Factura:", None),
                ("Monto Total:", float),
                ("Estado:", None)
            ]
        )

   #=======================================================
   #                EMPRESAS Y CONTACTOS
   #=======================================================
    def add_edit_empresa_window(self, empresa_data=None):
        """
        Ventana para agregar o editar una empresa.
        Si empresa_data es None, se usa para agregar. Si tiene datos, para editar.
        """
        window = tk.Toplevel(self.root)
        window.title("Editar Empresa" if empresa_data else "Agregar Empresa")
        window.configure(bg="#f0f5ff")
        window.grab_set()
        window.focus_force()

        # Configuración de la ventana
        width, height = 800, 500
        scr_w = window.winfo_screenwidth()
        scr_h = window.winfo_screenheight()
        x = (scr_w // 2) - (width // 2)
        y = (scr_h // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

        try:
            window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar ícono: {e}")

        # Frame principal
        main_frame = tk.Frame(window, bg="#f0f5ff", padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text="Editar Datos de Empresa" if empresa_data else "Agregar Nueva Empresa",
            font=("Helvetica", 16, "bold"),
            bg="#f0f5ff",
            fg="#022e86"
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))

        # Variables
        id_empresa_var = tk.StringVar(value=empresa_data['id_empresa'] if empresa_data else '')
        rut_empresa_var = tk.StringVar(value=empresa_data['rut_empresa'] if empresa_data else '')
        direccion_var = tk.StringVar(value=empresa_data['direccion_empresa'] if empresa_data else '')

        def create_label_entry(parent, label_text, row, col, var=None):
            tk.Label(
                parent,
                text=label_text,
                bg="#f0f5ff",
                fg="#022e86",
                font=("Helvetica", 10),
                anchor='e'
            ).grid(row=row, column=col, padx=(10, 5), pady=10, sticky='e')
            
            entry = tk.Entry(
                parent,
                width=35,
                font=("Helvetica", 10),
                relief="solid",
                bd=1,
                textvariable=var
            )
            entry.grid(row=row, column=col+1, padx=(0, 20), pady=10, sticky='w')
            return entry

        # Configurar el grid
        main_frame.grid_columnconfigure(1, weight=1)

        # Campos
        create_label_entry(main_frame, "ID Empresa:", 1, 0, id_empresa_var)
        create_label_entry(main_frame, "RUT Empresa:", 2, 0, rut_empresa_var)
        create_label_entry(main_frame, "Dirección:", 3, 0, direccion_var)

        def save_empresa():
            empresa_data = {
                'id_empresa': id_empresa_var.get().strip(),
                'rut_empresa': rut_empresa_var.get().strip(),
                'direccion_empresa': direccion_var.get().strip() or None
            }

            if not empresa_data['id_empresa'] or not empresa_data['rut_empresa']:
                messagebox.showwarning("Error", "ID y RUT de empresa son obligatorios", parent=window)
                return

            if not validar_rut(empresa_data['rut_empresa']):
                messagebox.showerror("Error", "El RUT ingresado es inválido.", parent=window)
                return

            if empresa_data:  # Editar
                ok = update_empresa(empresa_data)
            else:  # Agregar nuevo
                ok = insert_empresa(empresa_data)
            
            if ok:
                messagebox.showinfo("Éxito", 
                                "Empresa actualizada correctamente." if empresa_data else "Empresa agregada correctamente.", 
                                parent=window)
                window.destroy()
                self.show_empresas()  # Actualizar lista
            else:
                messagebox.showerror("Error", 
                                    "No se pudo actualizar la empresa." if empresa_data else "No se pudo agregar la empresa.", 
                                    parent=window)

        # Botón de guardar
        button_frame = tk.Frame(main_frame, bg="#f0f5ff")
        button_frame.grid(row=4, column=0, columnspan=2, pady=30)

        tk.Button(
            button_frame,
            text="Guardar Cambios" if empresa_data else "Agregar Empresa",
            bg="#022e86",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=30,
            pady=10,
            cursor="hand2",
            command=save_empresa
        ).pack()

    def show_empresas(self):
        try:
            if not hasattr(self, 'tree'):
                print("Error: tree no está inicializado")
                return
                
            # Actualizar el título
            self._update_title_label("Listado de Empresas")
                
            # Definir las columnas y headers
            columns = (
                "id_empresa", "rut_empresa", "direccion_empresa", 
                "nombre_contacto", "correo_contacto", "telefono_contacto", 
                "rol_contacto"
            )
                
            headers = (
                "Nombre Empresa", "RUT", "Dirección", 
                "Contacto", "Email", "Teléfono", 
                "Rol"
            )

            # Obtener datos
            data_raw = fetch_all_empresas(connect_db())
            formatted_data = []
                
            if data_raw:
                for empresa in data_raw:
                    row = [
                        empresa.get("id_empresa", ""),
                        empresa.get("rut_empresa", ""),
                        empresa.get("direccion_empresa", ""),
                        empresa.get("nombre_contacto", ""),
                        empresa.get("correo_contacto", ""),
                        empresa.get("telefono_contacto", ""),
                        empresa.get("rol_contacto", "")
                    ]
                    formatted_data.append(row)
                
            # Limpiar y configurar el tree
            self.tree.delete(*self.tree.get_children())
            self.tree.config(columns=columns, show="headings")
                
            # Configurar encabezados y columnas
            for column, header in zip(columns, headers):
                self.tree.heading(column, text=header, anchor=tk.CENTER)
                # Ajustar anchos según el tipo de columna
                if column in ["direccion_empresa", "correo_contacto"]:
                    width = 200
                elif column in ["id_empresa", "nombre_contacto"]:
                    width = 150
                elif column in ["rut_empresa"]:
                    width = 100
                else:
                    width = 120
                self.tree.column(column, width=width, minwidth=50, anchor=tk.CENTER)
                
            # Insertar datos si existen
            for item in formatted_data:
                self.tree.insert("", "end", values=item)
                    
        except Exception as e:
            print(f"Error al mostrar empresas: {e}")
            import traceback
            traceback.print_exc()

    def manage_contacts_window(self, id_empresa):
        """
        Ventana para gestionar los contactos de una empresa específica.
        """
        window = tk.Toplevel(self.root)
        window.title("Gestionar Contactos")
        window.configure(bg="#f0f5ff")
        window.grab_set()
        window.focus_force()

        # Configuración de la ventana
        width, height = 1000, 600
        scr_w = window.winfo_screenwidth()
        scr_h = window.winfo_screenheight()
        x = (scr_w // 2) - (width // 2)
        y = (scr_h // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

        # Frame principal
        main_frame = tk.Frame(window, bg="#f0f5ff", padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text=f"Contactos de Empresa",
            font=("Helvetica", 16, "bold"),
            bg="#f0f5ff",
            fg="#022e86"
        )
        title_label.pack(pady=(0, 20))

        # Frame para la tabla
        table_frame = tk.Frame(main_frame, bg="#f0f5ff")
        table_frame.pack(fill='both', expand=True, pady=10)

        # Crear Treeview
        columns = ("ID", "Nombre", "Rol", "Correo", "Teléfono")
        tree = ttk.Treeview(table_frame, columns=columns, show='headings')

        # Configurar columnas
        tree.heading("ID", text="ID")
        tree.heading("Nombre", text="Nombre")
        tree.heading("Rol", text="Rol")
        tree.heading("Correo", text="Correo")
        tree.heading("Teléfono", text="Teléfono")

        tree.column("ID", width=50)
        tree.column("Nombre", width=200)
        tree.column("Rol", width=150)
        tree.column("Correo", width=200)
        tree.column("Teléfono", width=150)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Empaquetar Treeview y scrollbar
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def load_contacts():
            for item in tree.get_children():
                tree.delete(item)
            contacts = fetch_contactos_by_empresa(id_empresa)
            for contact in contacts:
                tree.insert("", "end", values=(
                    contact['id_contacto'],
                    contact['nombre_contacto'],
                    contact['rol_contacto'],
                    contact['correo_contacto'],
                    contact['telefono_contacto']
                ))

        def add_contact_window():
            contact_window = tk.Toplevel(window)
            contact_window.title("Agregar Contacto")
            contact_window.configure(bg="#f0f5ff")
            contact_window.grab_set()

            # Variables
            nombre_var = tk.StringVar()
            rol_var = tk.StringVar()
            correo_var = tk.StringVar()
            telefono_var = tk.StringVar()

            # Frame para formulario
            form_frame = tk.Frame(contact_window, bg="#f0f5ff", padx=20, pady=20)
            form_frame.pack(fill='both', expand=True)

            # Campos
            fields = [
                ("Nombre:", nombre_var),
                ("Rol:", rol_var),
                ("Correo:", correo_var),
                ("Teléfono:", telefono_var)
            ]

            for i, (label_text, var) in enumerate(fields):
                tk.Label(
                    form_frame,
                    text=label_text,
                    bg="#f0f5ff",
                    fg="#022e86"
                ).grid(row=i, column=0, pady=5, padx=5)
                
                tk.Entry(
                    form_frame,
                    textvariable=var,
                    width=30
                ).grid(row=i, column=1, pady=5, padx=5)

            def save_contact():
                contact_data = {
                    'id_empresa': id_empresa,
                    'nombre_contacto': nombre_var.get().strip(),
                    'rol_contacto': rol_var.get().strip(),
                    'correo_contacto': correo_var.get().strip(),
                    'telefono_contacto': telefono_var.get().strip()
                }

                if not contact_data['nombre_contacto']:
                    messagebox.showwarning("Error", "El nombre es obligatorio", parent=contact_window)
                    return

                if insert_contacto_empresa(contact_data):
                    messagebox.showinfo("Éxito", "Contacto agregado correctamente", parent=contact_window)
                    contact_window.destroy()
                    load_contacts()
                else:
                    messagebox.showerror("Error", "No se pudo agregar el contacto", parent=contact_window)

            # Botón guardar
            tk.Button(
                form_frame,
                text="Guardar Contacto",
                bg="#022e86",
                fg="white",
                command=save_contact
            ).grid(row=len(fields), column=0, columnspan=2, pady=20)

        # Frame para botones
        button_frame = tk.Frame(main_frame, bg="#f0f5ff")
        button_frame.pack(pady=20)

        # Botones
        tk.Button(
            button_frame,
            text="Agregar Contacto",
            bg="#022e86",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=20,
            pady=5,
            cursor="hand2",
            command=add_contact_window
        ).pack(side='left', padx=5)

        def delete_contact():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Error", "Seleccione un contacto para eliminar", parent=window)
                return
            
            if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este contacto?", parent=window):
                contact_id = tree.item(selected[0])['values'][0]
                if delete_contacto_empresa(contact_id):
                    messagebox.showinfo("Éxito", "Contacto eliminado correctamente", parent=window)
                    load_contacts()
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el contacto", parent=window)

        tk.Button(
            button_frame,
            text="Eliminar Contacto",
            bg="#cc0000",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=20,
            pady=5,
            cursor="hand2",
            command=delete_contact
        ).pack(side='left', padx=5)

        # Cargar contactos iniciales
        load_contacts()

    # ---------------------------------------------------
    #  Función genérica para varias "ventanas de añadir"
    #  (En este ejemplo, la usamos para Pagos, Facturas, etc.)
    # ---------------------------------------------------
    def _generic_add_window(self, title, insert_function, fields):
        window = tk.Toplevel(self.root)
        window.title(title)

        try:
            window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar ícono de la ventana: {e}")

        width, height = 400, 600
        window.geometry(f"{width}x{height}")
        window.update_idletasks()
        scr_w = window.winfo_screenwidth()
        scr_h = window.winfo_screenheight()
        x = (scr_w // 2) - (width // 2)
        y = (scr_h // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.configure(bg="#022e86")

        try:
            logo = tk.PhotoImage(file='assets/logomarco.png')
            logo_label = tk.Label(window, image=logo, bg="#022e86")
            logo_label.image = logo
            logo_label.pack(pady=10)
        except Exception as e:
            print(f"Error al cargar logo: {e}")

        entries = []
        for label_text, value_type in fields:
            tk.Label(window, text=label_text, bg="#022e86", fg="white").pack(pady=5)
            entry = tk.Entry(window, width=40)
            entry.pack(pady=5)
            entries.append((entry, value_type))

        def save():
            values = []
            for entry, cast_type in entries:
                raw_val = entry.get().strip()
                if cast_type:  # int, float, etc.
                    try:
                        raw_val = cast_type(raw_val)
                    except ValueError:
                        messagebox.showerror("Error", f"Valor inválido: {raw_val}")
                        window.destroy()
                        return
                values.append(raw_val)

            # Insertar en BD
            if insert_function(*values):
                messagebox.showinfo("Éxito", f"{title} añadido correctamente")
                if "pago" in title.lower():
                    self.show_payments()
                elif "factura" in title.lower():
                    self.show_invoices()
                else:
                    pass
            else:
                messagebox.showerror("Error", "No se pudo añadir")

            window.destroy()

        tk.Button(window, text="Guardar", bg="#ADD8E6", command=save).pack(pady=20)


# ------------------------ MAIN ------------------------
if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.iconbitmap('assets/logo1.ico')
        small_icon_path = os.path.abspath(os.path.join('assets', 'logo2.ico'))
        root.call('wm', 'iconphoto', root._w, tk.PhotoImage(file=small_icon_path))
    except Exception as e:
        print(f"Error al cargar íconos: {e}")

    app = App(root)
    root.mainloop()
