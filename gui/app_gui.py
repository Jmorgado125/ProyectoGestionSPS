import tkinter as tk
from tkinter import ttk, messagebox
import os
from PIL import Image, ImageTk

# Importar la función connect_db si la necesitas en el GUI (por ejemplo en load_course_data)
from database.db_config import connect_db

# IMPORTA tus funciones de la base de datos, incluyendo fetch_inscriptions:
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
    fetch_inscriptions
)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión SPS")
        self.root.state("zoomed")

        self.setup_styles()

        try:
            self.root.iconbitmap('assets/logo1.ico')
            self.root.call('wm', 'iconphoto', root._w, tk.PhotoImage(file='assets/logo2.ico'))
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
        style.configure("Main.TFrame", background="#f0f0f0")

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

    def show_login_frame(self):
        """
        Ventana de LOGIN.
        """
        login_frame = ttk.Frame(self.root, style="Login.TFrame")
        login_frame.pack(fill=tk.BOTH, expand=True)

        # Logo del login
        try:
            logo = Image.open('assets/logomarco.jpg')
            logo_tk = ImageTk.PhotoImage(logo)
            logo_label = tk.Label(login_frame, image=logo_tk, bg="#0f075e")
            logo_label.image = logo_tk
            logo_label.pack(pady=(50, 30))
        except Exception as e:
            print(f"Error al cargar logo: {e}")

        fields_frame = ttk.Frame(login_frame, style="Login.TFrame")
        fields_frame.pack(pady=20)

        ttk.Label(fields_frame, text="Usuario:", style="Login.TLabel").pack(pady=5)
        user_entry = ttk.Entry(fields_frame, width=30)
        user_entry.pack(pady=5)

        ttk.Label(fields_frame, text="Contraseña:", style="Login.TLabel").pack(pady=5)
        pass_entry = ttk.Entry(fields_frame, width=30, show="*")
        pass_entry.pack(pady=5)

        def validate_login():
            username = user_entry.get().strip()
            password = pass_entry.get().strip()

            if not username or not password:
                messagebox.showwarning("Error", "Complete todos los campos")
                return

            user = fetch_user_by_credentials(username, password)
            if user:
                messagebox.showinfo("Éxito", f"Bienvenido, {user['nombre']}")
                login_frame.destroy()
                self.setup_main_interface()
            else:
                messagebox.showerror("Error", "Credenciales inválidas")

        ttk.Button(
            fields_frame,
            text="Iniciar Sesión",
            style="Login.TButton",
            command=validate_login
        ).pack(pady=20)

    def setup_main_interface(self):
        """
        Ventana principal después de iniciar sesión.
        """
        self.main_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Logo principal
        try:
            big_logo = Image.open('assets/logo2.ico')
            big_logo = big_logo.resize((140, 90), Image.ANTIALIAS)
            big_logo_tk = ImageTk.PhotoImage(big_logo)
            logo_label = tk.Label(self.main_frame, image=big_logo_tk, bg="#F0F8FF")
            logo_label.image = big_logo_tk
            logo_label.pack(pady=10)
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
        alumnos_menu.add_command(label="Buscar Alumno", command=self.search_student_window)
        alumnos_menu.add_command(label="Eliminar Alumno", command=self.delete_student_window)
        alumnos_menu.add_command(label="Cursos por Alumno", command=self.show_courses_by_student)
        menubar.add_cascade(label="Alumnos", menu=alumnos_menu)

        # Menú Inscripciones
        inscripciones_menu = tk.Menu(menubar, tearoff=0)
        inscripciones_menu.add_command(label="Matricular Alumno", command=self.enroll_student_window)
        inscripciones_menu.add_command(label="Ver Inscripciones", command=self.show_inscriptions)
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
            # Lo insertamos antes del frame que contiene el tree, para que aparezca arriba
            self.title_label.pack(pady=(10,5), before=self.tree.master)
        else:
            # Solo cambiamos el texto
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
        data = fetch_inscriptions()
        columns = (
            "id_inscripcion", "id_alumno", "id_curso", "numero_acta",
            "fecha_inscripcion", "fecha_termino_condicional", "anio_inscripcion"
        )
        headers = (
            "ID", "Alumno (RUT)", "Curso", "N° Acta",
            "F. Inscripción", "F. Término", "Año"
        )
        self._update_title_label("Listado de Inscripciones")
        self._populate_tree(columns, headers, data)

    def enroll_student_window(self):
        enroll_window = tk.Toplevel(self.root)
        enroll_window.title("Matricular Alumno")
        enroll_window.geometry("480x420")
        enroll_window.configure(bg="#022e86")

        # Centrar ventana
        sw = enroll_window.winfo_screenwidth()
        sh = enroll_window.winfo_screenheight()
        x = (sw // 2) - (480 // 2)
        y = (sh // 2) - (420 // 2)
        enroll_window.geometry(f"480x420+{x}+{y}")

        # Crear campos
        def create_label_entry(parent, label_text):
            tk.Label(parent, text=label_text, bg="#022e86", fg="white").pack(pady=5)
            entry = tk.Entry(parent, width=40)
            entry.pack(pady=5)
            return entry

        acta_entry = create_label_entry(enroll_window, "N° Acta:")
        rut_entry = create_label_entry(enroll_window, "RUT Alumno:")
        id_curso_entry = create_label_entry(enroll_window, "ID Curso:")
        fecha_inscripcion_entry = create_label_entry(enroll_window, "Fecha Inscripción (YYYY-MM-DD):")
        fecha_termino_entry = create_label_entry(enroll_window, "Fecha Término Condicional (YYYY-MM-DD):")
        anio_entry = create_label_entry(enroll_window, "Año Inscripción (YYYY):")

        def save_enrollment():
            numero_acta = acta_entry.get().strip()
            rut = rut_entry.get().strip()
            id_curso = id_curso_entry.get().strip()
            fecha_insc = fecha_inscripcion_entry.get().strip()
            fecha_term = fecha_termino_entry.get().strip() or None
            anio_text = anio_entry.get().strip()

            # Validaciones
            if not numero_acta or not rut or not id_curso or not fecha_insc or not anio_text:
                messagebox.showwarning("Campos vacíos", "Complete todos los campos requeridos.")
                return

            try:
                anio_inscripcion = int(anio_text)
            except ValueError:
                messagebox.showerror("Error", "El año de inscripción debe ser un entero (YYYY).")
                return

            # Llamada a la función para inscribir al alumno
            success, db_error = enroll_student(rut, id_curso, numero_acta, fecha_insc, fecha_term, anio_inscripcion)
            if success:
                messagebox.showinfo("Éxito", "Alumno matriculado correctamente.")
                enroll_window.destroy()
                self.show_inscriptions()  # Refresca las inscripciones
            else:
                messagebox.showerror("Error al matricular", f"No se pudo matricular el alumno.\n\nDetalle:\n{db_error}")

        tk.Button(enroll_window, text="Guardar", bg="#ADD8E6", command=save_enrollment).pack(pady=20)


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
        window = tk.Toplevel(self.root)
        window.title("Añadir Curso")

        try:
            window.iconbitmap("assets/logo1.ico")
        except Exception as e:
            print(f"Error al cargar ícono de la ventana: {e}")

        width, height = 400, 600
        window.geometry(f"{width}x{height}")
        window.update_idletasks()

        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.configure(bg="#022e86")

        tk.Label(window, text="ID del Curso:", bg="#022e86", fg="white").pack(pady=5)
        id_entry = tk.Entry(window, width=40)
        id_entry.pack(pady=5)

        tk.Label(window, text="Nombre:", bg="#022e86", fg="white").pack(pady=5)
        nombre_entry = tk.Entry(window, width=40)
        nombre_entry.pack(pady=5)

        tk.Label(window, text="Modalidad:", bg="#022e86", fg="white").pack(pady=5)
        mod_entry = tk.Entry(window, width=40)
        mod_entry.pack(pady=5)

        tk.Label(window, text="Código SENCE:", bg="#022e86", fg="white").pack(pady=5)
        sence_entry = tk.Entry(window, width=40)
        sence_entry.pack(pady=5)

        tk.Label(window, text="Código eLearning:", bg="#022e86", fg="white").pack(pady=5)
        elearn_entry = tk.Entry(window, width=40)
        elearn_entry.pack(pady=5)

        tk.Label(window, text="Horas Cronológicas:", bg="#022e86", fg="white").pack(pady=5)
        horas_cron_entry = tk.Entry(window, width=40)
        horas_cron_entry.pack(pady=5)

        horas_pedag_label = tk.Label(window, text="Horas Pedagógicas: 0.0", bg="#022e86", fg="white")
        horas_pedag_label.pack(pady=5)

        tk.Label(window, text="Valor del Curso:", bg="#022e86", fg="white").pack(pady=5)
        valor_entry = tk.Entry(window, width=40)
        valor_entry.pack(pady=5)

        def calculate_horas_pedagogicas():
            try:
                horas_cron = float(horas_cron_entry.get().strip())
                horas_pedagogicas = round(horas_cron * 4 / 3, 1)
                horas_pedag_label.config(text=f"Horas Pedagógicas: {horas_pedagogicas}")
            except ValueError:
                horas_pedag_label.config(text="Horas Pedagógicas: Error")

        horas_cron_entry.bind("<KeyRelease>", lambda event: calculate_horas_pedagogicas())

        def save_course():
            id_curso = id_entry.get().strip()
            nombre_curso = nombre_entry.get().strip()
            modalidad = mod_entry.get().strip()
            sence_text = sence_entry.get().strip()
            elearn_text = elearn_entry.get().strip()
            horas_cron_text = horas_cron_entry.get().strip()
            valor_text = valor_entry.get().strip()

            if not id_curso or not nombre_curso or not modalidad:
                messagebox.showwarning("Campos requeridos",
                                       "El ID del Curso, el Nombre y la Modalidad son obligatorios.")
                return

            try:
                codigo_sence = int(sence_text) if sence_text else None
            except ValueError:
                messagebox.showerror("Error", f"El Código SENCE debe ser un número entero.\nValor: {sence_text}")
                return

            try:
                codigo_elearn = int(elearn_text) if elearn_text else None
            except ValueError:
                messagebox.showerror("Error", f"El Código eLearning debe ser un número entero.\nValor: {elearn_text}")
                return

            try:
                horas_cron = float(horas_cron_text)
            except ValueError:
                messagebox.showerror("Error", "Las horas cronológicas deben ser un número decimal.")
                return

            try:
                valor_curso = float(valor_text)
            except ValueError:
                messagebox.showerror("Error", "El valor del curso debe ser un número (puede ser decimal).")
                return

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
                messagebox.showinfo("Éxito", "Curso añadido correctamente.")
                self.show_courses()
                window.destroy()
            else:
                messagebox.showerror("Error", "No se pudo añadir el curso.")

        tk.Button(window, text="Guardar", bg="#E0F8FF", command=save_course).pack(pady=20)

    def edit_course_window(self):
        window = tk.Toplevel(self.root)
        window.title("Editar Curso")

        try:
            window.iconbitmap("assets/logo1.ico")
        except Exception as e:
            print(f"Error al cargar ícono de la ventana: {e}")

        width, height = 400, 650
        window.geometry(f"{width}x{height}")
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.configure(bg="#022e86")

        tk.Label(window, text="ID del Curso:", bg="#022e86", fg="white").pack(pady=5)
        id_curso_entry = tk.Entry(window, width=40)
        id_curso_entry.pack(pady=5)

        nombre_var = tk.StringVar()
        modalidad_var = tk.StringVar()
        sence_var = tk.StringVar()
        elearning_var = tk.StringVar()
        horas_cron_var = tk.StringVar()
        horas_pedag_var = tk.StringVar()
        valor_var = tk.StringVar()

        def load_course_data():
            id_curso = id_curso_entry.get().strip()
            if not id_curso:
                messagebox.showwarning("Error", "Debe ingresar un ID de curso.")
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

            if course:
                # Ajustar índices según tu tabla:
                # 0: id_curso
                # 1: nombre_curso
                # 2: modalidad
                # 3: codigo_sence
                # 4: codigo_elearning
                # 5: horas_cronologicas
                # 6: horas_pedagogicas
                # 7: valor
                nombre_var.set(course[1] or "")
                modalidad_var.set(course[2] or "")
                sence_var.set(course[3] if course[3] is not None else "")
                elearning_var.set(course[4] if course[4] is not None else "")
                horas_cron_var.set(course[5] if course[5] is not None else "")
                horas_pedag_var.set(course[6] if course[6] is not None else "")
                valor_var.set(course[7] if course[7] is not None else "")
            else:
                messagebox.showerror("Error", f"No se encontró el curso con ID: {id_curso}")

        def save_edited_course():
            id_curso = id_curso_entry.get().strip()
            nombre = nombre_var.get().strip()
            modalidad = modalidad_var.get().strip()
            codigo_sence = sence_var.get().strip()
            codigo_elearning = elearning_var.get().strip()
            horas_cronologicas = horas_cron_var.get().strip()
            horas_pedagogicas = horas_pedag_var.get().strip()
            valor_curso = valor_var.get().strip()

            if not id_curso or not nombre or not modalidad:
                messagebox.showwarning("Campos requeridos", "El ID, Nombre y Modalidad son obligatorios.")
                return

            try:
                codigo_sence = int(codigo_sence) if codigo_sence else None
            except ValueError:
                messagebox.showerror("Error", "El Código SENCE debe ser un número entero.")
                return

            try:
                codigo_elearning = int(codigo_elearning) if codigo_elearning else None
            except ValueError:
                messagebox.showerror("Error", "El Código eLearning debe ser un número entero.")
                return

            try:
                horas_cronologicas = float(horas_cronologicas) if horas_cronologicas else None
            except ValueError:
                messagebox.showerror("Error", "Las horas cronológicas deben ser un número.")
                return

            try:
                horas_pedagogicas = float(horas_pedagogicas) if horas_pedagogicas else None
            except ValueError:
                messagebox.showerror("Error", "Las horas pedagógicas deben ser un número.")
                return

            try:
                valor_curso = float(valor_curso) if valor_curso else None
            except ValueError:
                messagebox.showerror("Error", "El valor del curso debe ser un número (puede ser decimal).")
                return

            success = update_course(
                id_curso=id_curso,
                nombre_curso=nombre,
                modalidad=modalidad,
                codigo_sence=codigo_sence,
                codigo_elearning=codigo_elearning,
                horas_cronologicas=horas_cronologicas,
                horas_pedagogicas=horas_pedagogicas,
                valor=valor_curso
            )

            if success:
                messagebox.showinfo("Éxito", "Curso actualizado correctamente.")
                self.show_courses()
                window.destroy()
            else:
                messagebox.showerror("Error", "No se pudo actualizar el curso.")

        tk.Button(window, text="Cargar Datos", bg="#ADD8E6", command=load_course_data).pack(pady=10)

        tk.Label(window, text="Nombre:", bg="#022e86", fg="white").pack(pady=5)
        tk.Entry(window, textvariable=nombre_var, width=40).pack(pady=5)

        tk.Label(window, text="Modalidad:", bg="#022e86", fg="white").pack(pady=5)
        tk.Entry(window, textvariable=modalidad_var, width=40).pack(pady=5)

        tk.Label(window, text="Código SENCE:", bg="#022e86", fg="white").pack(pady=5)
        tk.Entry(window, textvariable=sence_var, width=40).pack(pady=5)

        tk.Label(window, text="Código eLearning:", bg="#022e86", fg="white").pack(pady=5)
        tk.Entry(window, textvariable=elearning_var, width=40).pack(pady=5)

        tk.Label(window, text="Horas Cronológicas:", bg="#022e86", fg="white").pack(pady=5)
        tk.Entry(window, textvariable=horas_cron_var, width=40).pack(pady=5)

        tk.Label(window, text="Horas Pedagógicas:", bg="#022e86", fg="white").pack(pady=5)
        tk.Entry(window, textvariable=horas_pedag_var, width=40).pack(pady=5)

        tk.Label(window, text="Valor del Curso:", bg="#022e86", fg="white").pack(pady=5)
        tk.Entry(window, textvariable=valor_var, width=40).pack(pady=5)

        tk.Button(window, text="Guardar Cambios", bg="#ADD8E6", command=save_edited_course).pack(pady=20)

    def delete_course_window(self):
        window = tk.Toplevel(self.root)
        window.title("Eliminar Curso")

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

        tk.Label(window, text="ID del Curso:", bg="#022e86", fg="white").pack(pady=10)
        id_entry = tk.Entry(window, width=30)
        id_entry.pack(pady=5)

        def delete_course():
            if messagebox.askyesno("Confirmar", "¿Seguro que desea eliminar este curso?"):
                course_id = id_entry.get().strip()
                if not course_id:
                    messagebox.showwarning("Error", "Ingrese un ID de curso válido.")
                    return
                success = delete_course_by_id(course_id)
                if success:
                    messagebox.showinfo("Éxito", "Curso eliminado con éxito.")
                    self.show_courses()
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el curso (o no existe).")
            window.destroy()

        tk.Button(window, text="Eliminar", bg="#FF6B6B", command=delete_course).pack(pady=20)

    # ---------------------------------------------------
    #                  ALUMNOS
    # ---------------------------------------------------
    def show_students(self):
        students = fetch_all_students()
        columns = ("rut", "nombre", "apellido", "correo", "telefono", "profesion", "direccion", "ciudad", "comuna")
        headers = ("RUT", "Nombre", "Apellido", "Correo", "Teléfono", "Profesión", "Dirección", "Ciudad", "Comuna")
        self._update_title_label("Listado de Alumnos")
        self._populate_tree(columns, headers, students)

    def add_student_window(self):
        self._generic_add_window(
            "Añadir Alumno",
            insert_student,
            [
                ("RUT:", None),
                ("Nombre:", None),
                ("Apellido:", None),
                ("Correo:", None),
                ("Teléfono:", None),
                ("Profesión:", None),
                ("Dirección:", None),
                ("Ciudad:", None),
                ("Comuna:", None)
            ]
        )

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
            for entry, value_type in entries:
                raw_val = entry.get().strip()
                try:
                    if value_type:  # int, float, etc.
                        raw_val = value_type(raw_val)
                except ValueError:
                    messagebox.showerror("Error", f"Valor inválido: {raw_val}")
                    window.destroy()
                    return
                values.append(raw_val)

            if insert_function(*values):
                messagebox.showinfo("Éxito", f"{title} añadido correctamente")
                if title.lower().startswith("añadir pago"):
                    self.show_payments()
                elif title.lower().startswith("añadir factura"):
                    self.show_invoices()
                elif title.lower().startswith("añadir alumno"):
                    self.show_students()
            else:
                messagebox.showerror("Error", "No se pudo añadir")

            window.destroy()

        tk.Button(window, text="Guardar", bg="#ADD8E6", command=save).pack(pady=20)

    def search_student_window(self):
        window = tk.Toplevel(self.root)
        window.title("Buscar Alumno")

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

        tk.Label(window, text="RUT:", bg="#022e86", fg="white").pack(pady=10)
        rut_entry = tk.Entry(window, width=30)
        rut_entry.pack(pady=5)

        def search():
            rut = rut_entry.get().strip()
            if not rut:
                messagebox.showwarning("Error", "Ingrese RUT")
                window.destroy()
                return

            student = fetch_student_by_rut(rut)
            if student:
                self._populate_tree(
                    ("rut", "nombre", "apellido", "correo", "telefono"),
                    ("RUT", "Nombre", "Apellido", "Correo", "Teléfono"),
                    [student]
                )
                self._update_title_label(f"Alumno encontrado: {rut}")
            else:
                messagebox.showerror("Error", "Alumno no encontrado.")
            window.destroy()

        tk.Button(window, text="Buscar", bg="#ADD8E6", command=search).pack(pady=20)

    def delete_student_window(self):
        window = tk.Toplevel(self.root)
        window.title("Eliminar Alumno")

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

        tk.Label(window, text="RUT:", bg="#022e86", fg="white").pack(pady=10)
        rut_entry = tk.Entry(window, width=30)
        rut_entry.pack(pady=5)

        def delete():
            if messagebox.askyesno("Confirmar", "¿Seguro que desea eliminar?"):
                rut = rut_entry.get().strip()
                if delete_student_by_rut(rut):
                    messagebox.showinfo("Éxito", "Alumno eliminado")
                    self.show_students()
                else:
                    messagebox.showerror("Error", "No se pudo eliminar")
            window.destroy()

        tk.Button(window, text="Eliminar", bg="#FF6B6B", command=delete).pack(pady=20)

    def show_courses_by_student(self):
        window = tk.Toplevel(self.root)
        window.title("Cursos por Alumno")

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

        tk.Label(window, text="RUT:", bg="#022e86", fg="white").pack(pady=10)
        rut_entry = tk.Entry(window, width=30)
        rut_entry.pack(pady=5)

        def search():
            rut = rut_entry.get().strip()
            if not rut:
                messagebox.showwarning("Error", "Ingrese RUT")
                window.destroy()
                return

            courses = fetch_courses_by_student_rut(rut)
            if courses:
                self._populate_tree(
                    ("nombre_curso", "fecha_inscripcion"),
                    ("Curso", "Fecha Inscripción"),
                    courses
                )
                self._update_title_label(f"Cursos de {rut}")
                messagebox.showinfo("Resultado", f"Se hallaron {len(courses)} cursos para el RUT {rut}.")
            else:
                messagebox.showinfo("Info", "No se encontraron cursos")

            window.destroy()

        tk.Button(window, text="Buscar", bg="#ADD8E6", command=search).pack(pady=20)

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
                ("Tipo de Pago:", None),
                ("Modalidad:", None),
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
