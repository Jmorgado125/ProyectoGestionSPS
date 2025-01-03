import tkinter as tk
from tkinter import ttk, messagebox
import os
from PIL import Image, ImageTk
from datetime import datetime
from database.db_config import connect_db
from itertools import cycle  # <<--- Para el validador avanzado de RUT

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
    if not rut_aux.isdigit() or not (1_000_000 <= int(rut_aux) <= 25_000_000):
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
# from database.db_config import connect_db  # Si lo requieres para algunas funciones directas

from database.queries import (
    fetch_courses,
    insert_course,
    update_course,
    delete_course_by_id,
    fetch_courses_by_student_rut,
    fetch_all_students,
    insert_student,
    fetch_student_by_rut,
    delete_student_by_rut,
    fetch_payments,
    insert_payment,
    fetch_payments_by_inscription,
    insert_invoice,
    fetch_invoices,
    fetch_user_by_credentials,
    enroll_student,
    fetch_inscriptions,
    update_inscription,
    update_student,
    get_or_create_empresa,
    validate_alumno_exists,
    validate_curso_exists,
    get_empresa_by_name,
    register_new_empresa,
    get_or_create_empresa,
    validate_duplicate_enrollment,
    fetch_students_by_name_apellido,
    format_inscription_data,
    delete_inscription,
    fetch_inscription_by_id
)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión SPS")
        self.root.state("zoomed")

        self.setup_styles()

        try:
            self.root.iconbitmap('assets/logo1.ico')
            self.root.call('wm', 'iconphoto', root._w, tk.PhotoImage(file='assets/logo1.ico'))
        except Exception as e:
            print(f"Error al cargar íconos: {e}")

        self.main_frame = None
        
        # Label único para el título de la tabla
        self.title_label = None

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

        # Estilo para la tabla (Treeview) y sus encabezados
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

        # Estilo para las filas seleccionadas
        style.map('Treeview',
                  background=[('selected', '#0078D7')],
                  foreground=[('selected', 'white')])

        # Estilo para botones genéricos
        style.configure("TButton",
                        padding=6,
                        relief="flat",
                        background="#0078D7",
                        foreground="black",
                        font=('Segoe UI', 10))

        # Estilo para etiquetas (Labels) genéricas
        style.configure("TLabel",
                        font=('Segoe UI', 10),
                        background="#f0f0f0")
        
        # En setup_styles, agregar:
        style.configure("Title.TLabel",
                font=('Segoe UI', 14, 'bold'),
                background="#0f075e",  # Mantener consistente con el tema
                foreground="white")    # Texto blanco para contraste

    def show_login_frame(self):
            """
            Ventana de LOGIN con animaciones optimizadas.
            """
            # Frame principal
            login_frame = ttk.Frame(self.root, style="Login.TFrame")
            login_frame.pack(fill=tk.BOTH, expand=True)

            # Contenedor principal
            main_container = tk.Frame(login_frame, bg="#0f075e", width=400, height=500)
            main_container.pack(expand=True)
            main_container.pack_propagate(False)

            # Solo fade-in inicial
            def fade_in(widget, current_alpha=0):
                if current_alpha < 1:
                    current_alpha += 0.05
                    widget.attributes('-alpha', current_alpha)
                    self.root.after(30, lambda: fade_in(widget, current_alpha))

            self.root.attributes('-alpha', 0)
            fade_in(self.root)

            # Logo con animación suave
            try:
                from PIL import Image, ImageTk
                logo = Image.open('assets/logomarco.jpg')
                logo_tk = ImageTk.PhotoImage(logo)
                logo_label = tk.Label(main_container, image=logo_tk, bg="#0f075e")
                logo_label.image = logo_tk
                
                # Animación del logo
                logo_label.place(relx=0.5, rely=-0.5, anchor="center")
                def animate_logo(pos=0):
                    if pos < 0.2:
                        pos += 0.02
                        logo_label.place(relx=0.5, rely=pos, anchor="center")
                        self.root.after(30, lambda: animate_logo(pos))
                animate_logo()
                
            except Exception as e:
                print(f"Error al cargar logo: {e}")

            # Frame para campos
            fields_frame = tk.Frame(main_container, bg="#0f075e", width=300)
            fields_frame.pack(pady=(220, 20))

            # Campos de entrada mejorados con efectos
            def create_entry(parent, placeholder, show=None):
                frame = tk.Frame(parent, bg="#0f075e")
                frame.pack(pady=15, padx=20, fill='x')
                
                label = tk.Label(
                    frame,
                    text=placeholder,
                    bg="#0f075e",
                    fg="white",
                    font=('Helvetica', 12)
                )
                label.pack(anchor='w')
                
                entry = tk.Entry(
                    frame,
                    font=('Helvetica', 12),
                    bg="#1a237e",
                    fg="white",
                    insertbackground='white',
                    relief='flat',
                    show=show
                )
                entry.pack(fill='x', pady=(5, 0))
                
                # Línea decorativa con efecto
                line = tk.Frame(frame, height=2, bg='white')
                line.pack(fill='x', pady=(2, 0))
                
                # Efectos al focus
                def on_focus_in(event):
                    line.configure(height=3)
                    entry.configure(bg="#283593")
                    
                def on_focus_out(event):
                    line.configure(height=2)
                    entry.configure(bg="#1a237e")
                    
                entry.bind("<FocusIn>", on_focus_in)
                entry.bind("<FocusOut>", on_focus_out)
                
                return entry

            # Crear campos
            user_entry = create_entry(fields_frame, "Usuario")
            pass_entry = create_entry(fields_frame, "Contraseña", show="*")

            def validate_login():
                username = user_entry.get().strip()
                password = pass_entry.get().strip()

                if not username or not password:
                    messagebox.showwarning("Error", "Complete todos los campos")
                    return

                user = fetch_user_by_credentials(username, password)
                if user:
                    login_frame.destroy()
                    self.setup_main_interface()
                else:
                    messagebox.showerror("Error", "Credenciales inválidas")

            # Botón de login mejorado
            button_frame = tk.Frame(main_container, bg="#0f075e")
            button_frame.pack(pady=20)

            login_button = tk.Button(
                button_frame,
                text="Iniciar Sesión",
                font=('Helvetica', 12, 'bold'),
                bg="#1a237e",
                fg="white",
                activebackground="#283593",
                activeforeground="white",
                relief='flat',
                cursor='hand2',
                width=20,
                command=validate_login
            )
            
            def on_enter(e):
                e.widget['background'] = '#283593'
                
            def on_leave(e):
                e.widget['background'] = '#1a237e'
                
            login_button.bind("<Enter>", on_enter)
            login_button.bind("<Leave>", on_leave)
            login_button.pack(pady=10)
            
            # Bind Enter key para login
            def on_return(event):
                validate_login()
                
            self.root.bind('<Return>', on_return)

    def setup_main_interface(self):
        """
        Ventana principal después de iniciar sesión.
        """
        self.main_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Inicializar title_label como None
        self.title_label = None

        # Para el error del logo ANTIALIAS
        try:
            img = Image.open("assets/logomarco.jpg")
            # Usar LANCZOS en lugar de ANTIALIAS
            resized_image = img.resize((140, 90), Image.LANCZOS)
        except Exception as e:
            print(f"Error al cargar logo: {e}")

        self._setup_menu()
        self._setup_tree()

        # Al iniciar, mostrar inscripciones directamente
        self.show_inscriptions()

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

    def _setup_tree(self):
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(tree_frame, show="headings", selectmode="browse")

        # Scrollbars
        vscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # Fila alternada
        self.tree.tag_configure('oddrow', background='#f5f5f5')
        self.tree.tag_configure('evenrow', background='#ffffff')

        # Copiar contenido con doble clic
        self.tree.bind("<Double-1>", self._copy_cell_to_clipboard)

    def _update_title_label(self, text):
        """
        Actualiza (o crea) un único Label para el título, evitando que se dupliquen.
        """
        if self.title_label is None:
            self.title_label = ttk.Label(
                self.main_frame,
                text=text,
                font=('Segoe UI', 14, 'bold'),
                background="#f0f0f0"
            )
            self.title_label.pack(pady=(10,5), before=self.tree.master)
        else:
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
            width, height = 450, 520
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

            def validate_rut_entry():
                rut = rut_entry.get().strip()
                if not validar_rut(rut):
                    messagebox.showerror("Error", "RUT inválido", parent=enroll_window)
                    rut_entry.focus()
                    return False
                return True

            def validate_curso_entry():
                curso_id = id_curso_entry.get().strip()
                if not validate_curso_exists(curso_id):
                    messagebox.showerror("Error", "El curso no existe", parent=enroll_window)
                    id_curso_entry.focus()
                    return False
                return True

            def validate_fecha(fecha_str):
                try:
                    if fecha_str:
                        datetime.strptime(fecha_str, '%Y-%m-%d')
                    return True
                except ValueError:
                    return False

            # Campos básicos con validación
            acta_entry = create_label_entry(main_frame, "N° Acta:")
            rut_entry = create_label_entry(main_frame, "RUT Alumno:")
            rut_entry.bind('<FocusOut>', lambda e: validate_rut_entry())
            
            id_curso_entry = create_label_entry(main_frame, "ID Curso:")
            id_curso_entry.bind('<FocusOut>', lambda e: validate_curso_entry())
            
            # Fecha de inscripción automática
            fecha_frame = tk.Frame(main_frame, bg="#f0f5ff")
            fecha_frame.pack(fill='x', pady=5)
            
            fecha_label = tk.Label(
                fecha_frame,
                text="Fecha Inscripción (YYYY-MM-DD):",
                bg="#f0f5ff",
                fg="#022e86",
                font=("Helvetica", 10),
                width=25,
                anchor='w'
            )
            fecha_label.pack(side=tk.LEFT, padx=(0, 10))
            
            fecha_actual = datetime.now().strftime('%Y-%m-%d')
            fecha_value = tk.Label(
                fecha_frame,
                text=fecha_actual,
                bg="white",
                font=("Helvetica", 10),
                relief="solid",
                bd=1,
                width=25,
                anchor='w'
            )
            fecha_value.pack(side=tk.LEFT, fill='x', expand=True)
            
            fecha_termino_entry = create_label_entry(main_frame, "Fecha Término (YYYY-MM-DD):")
            fecha_termino_entry.bind('<FocusOut>', lambda e: validate_fecha_termino())
            
            anio_entry = create_label_entry(main_frame, "Año Inscripción (YYYY):")
            anio_entry.insert(0, datetime.now().strftime('%Y'))

            def validate_fecha_termino():
                fecha_term = fecha_termino_entry.get().strip()
                if fecha_term and not validate_fecha(fecha_term):
                    messagebox.showerror(
                        "Error",
                        "Formato de fecha inválido. Use YYYY-MM-DD",
                        parent=enroll_window
                    )
                    fecha_termino_entry.focus()
                    return False
                
                if fecha_term:
                    fecha_term_date = datetime.strptime(fecha_term, '%Y-%m-%d').date()
                    fecha_insc_date = datetime.strptime(fecha_actual, '%Y-%m-%d').date()
                    
                    if fecha_term_date < fecha_insc_date:
                        messagebox.showerror(
                            "Error",
                            "La fecha de término no puede ser anterior a la fecha de inscripción",
                            parent=enroll_window
                        )
                        fecha_termino_entry.focus()
                        return False
                return True

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

                # Validar fecha término
                if not validate_fecha_termino():
                    return False

                return True

            # Frame inferior para el botón
            button_frame = tk.Frame(enroll_window, bg="#f0f5ff", pady=20)
            button_frame.pack(side=tk.BOTTOM, fill='x')

            def save_enrollment():
                if not validate_enrollment_data():
                    return

                # Obtener datos básicos
                numero_acta = acta_entry.get().strip()
                rut = rut_entry.get().strip()
                id_curso = id_curso_entry.get().strip()
                fecha_term = fecha_termino_entry.get().strip() or None
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

                # Intentar guardar la inscripción
                # Convertir fechas al formato correcto
                try:
                    fecha_inscripcion = datetime.strptime(fecha_actual, '%Y-%m-%d').date()
                    fecha_termino = None
                    if fecha_term:
                        fecha_termino = datetime.strptime(fecha_term, '%Y-%m-%d').date()
                    
                    success, message = enroll_student(
                        id_alumno=rut,
                        id_curso=id_curso,
                        numero_acta=numero_acta,
                        fecha_inscripcion=fecha_inscripcion,
                        fecha_termino_condicional=fecha_termino,
                        anio_inscripcion=anio_inscripcion,
                        metodo_llegada=metodo_llegada,
                        nombre_empresa=nombre_empresa,
                        ordenSence=orden_sence,
                        idfolio=id_folio
                    )
                except ValueError as e:
                    messagebox.showerror(
                        "Error",
                        f"Error en el formato de las fechas: {str(e)}",
                        parent=enroll_window
                    )
                    return

                if success:
                    messagebox.showinfo(
                        "Éxito",
                        "Alumno matriculado correctamente",
                        parent=enroll_window
                    )
                    enroll_window.destroy()
                    self.show_inscriptions()  # Actualizar vista
                else:
                    messagebox.showerror(
                        "Error al matricular",
                        f"No se pudo matricular el alumno:\n{message}",
                        parent=enroll_window
                    )

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
            "valor"
        )
        headers = (
            "ID",
            "Nombre",
            "Modalidad",
            "Código SENCE",
            "Código eLearning",
            "Hrs. Cron.",
            "Hrs. Pedag.",
            "Valor"
        )
        self._update_title_label("Listado de Cursos")
        self._populate_tree(columns, headers, courses)

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
        width, height = 800, 450
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
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Por favor, verifique los campos numéricos:\n" +
                    "- Código SENCE: debe ser número entero\n" +
                    "- Código eLearning: debe ser número entero\n" +
                    "- Horas Cronológicas: debe ser número decimal\n" +
                    "- Valor: debe ser número decimal",
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
                valor=valor_curso
            )

            if success:
                messagebox.showinfo("Éxito", "Curso añadido correctamente.", parent=window)
                self.show_courses()  # Actualizar la vista de cursos
                window.destroy()
            else:
                messagebox.showerror("Error", "No se pudo añadir el curso.", parent=window)

        # Frame para botones
        button_frame = tk.Frame(main_frame, bg="#f0f5ff")
        button_frame.grid(row=5, column=0, columnspan=4, pady=30)

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
        width, height = 800, 450
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
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Por favor, verifique los campos numéricos:\n" +
                    "- Código SENCE: debe ser número entero\n" +
                    "- Código eLearning: debe ser número entero\n" +
                    "- Horas Cronológicas: debe ser número decimal\n" +
                    "- Valor: debe ser número decimal",
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
                valor=valor_curso
            )

            if success:
                messagebox.showinfo("Éxito", "Curso actualizado correctamente.", parent=window)
                self.show_courses()
                window.destroy()
            else:
                messagebox.showerror("Error", "No se pudo actualizar el curso.", parent=window)

        # Frame para botones
        button_frame = tk.Frame(main_frame, bg="#f0f5ff")
        button_frame.grid(row=6, column=0, columnspan=4, pady=30)

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
