import tkinter as tk
from tkinter import ttk, messagebox
import os
from PIL import Image, ImageTk

from database.queries import (
    fetch_courses, insert_course, fetch_courses_by_student_rut,
    fetch_all_students, insert_student, fetch_student_by_rut, delete_student_by_rut,
    fetch_payments, insert_payment, fetch_payments_by_inscription,
    insert_invoice, fetch_invoices, fetch_user_by_credentials,
    enroll_student
)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión SPS")
        self.root.state("zoomed")

        # Iconos
        try:
            self.root.iconbitmap('assets/logo1.ico')
            self.root.call('wm', 'iconphoto', root._w, tk.PhotoImage(file='assets/logo2.ico'))
        except Exception as e:
            print(f"Error al cargar íconos: {e}")

        self.main_frame = None
        self.show_login_frame()

    def show_login_frame(self):
        login_frame = ttk.Frame(self.root, style="Login.TFrame")
        login_frame.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.configure("Login.TFrame", background="#0f075e")
        style.configure("Login.TLabel", background="#0f075e", foreground="white", font=("Helvetica", 12))
        style.configure("Login.TButton", font=("Helvetica", 11), padding=5)

        # Logo login
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
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Main.TFrame", background="#0f075e")
        style.configure("Treeview", font=('Helvetica', 10), rowheight=25)
        style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))

        self.main_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Logo principal
        try:
            big_logo = Image.open('assets/logo.jpg')
            big_logo = big_logo.resize((140, 90), Image.ANTIALIAS)
            big_logo_tk = ImageTk.PhotoImage(big_logo)
            logo_label = tk.Label(self.main_frame, image=big_logo_tk, bg="#F0F8FF")
            logo_label.image = big_logo_tk
            logo_label.pack(pady=10)
        except Exception as e:
            print(f"Error al cargar logo: {e}")

        self._setup_menu()
        self._setup_tree()

    def _setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menú Cursos
        cursos_menu = tk.Menu(menubar, tearoff=0)
        cursos_menu.add_command(label="Ver Cursos", command=self.show_courses)
        cursos_menu.add_command(label="Añadir Curso", command=self.add_course_window)
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

        self.tree = ttk.Treeview(tree_frame, show="headings")

        # Scrollbars
        vscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

        # Layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

    def _populate_tree(self, columns, headers, data):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = columns

        for col, head in zip(columns, headers):
            self.tree.heading(col, text=head)
            self.tree.column(col, anchor=tk.W, width=150)

        for row in data:
            self.tree.insert("", "end", values=row)

    def _generic_add_window(self, title, insert_function, fields):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("400x600")
        window.configure(bg="#F0F8FF")

        try:
            window.iconbitmap('assets/logo1.ico')
            logo = tk.PhotoImage(file='assets/logomarco.png')
            logo_label = tk.Label(window, image=logo, bg="#F0F8FF")
            logo_label.image = logo
            logo_label.pack(pady=10)
        except Exception as e:
            print(f"Error al cargar logo: {e}")

        entries = []
        for label_text, value_type in fields:
            tk.Label(window, text=label_text, bg="#F0F8FF").pack(pady=5)
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
                    return
                values.append(raw_val)

            if insert_function(*values):
                messagebox.showinfo("Éxito", f"{title} añadido correctamente")
                window.destroy()
            else:
                messagebox.showerror("Error", "No se pudo añadir")

        tk.Button(window, text="Guardar", bg="#ADD8E6", command=save).pack(pady=20)

    # ---------------------------------------------------
    #            MÉTODOS RELACIONADOS A INSCRIPCIONES
    # ---------------------------------------------------
    def enroll_student_window(self):
        enroll_window = tk.Toplevel(self.root)
        enroll_window.title("Matricular Alumno")

        # 1) Fijar tamaño deseado
        width, height = 400, 320
        enroll_window.geometry(f"{width}x{height}")

        # 2) Centrar la ventana en la pantalla
        enroll_window.update_idletasks()
        screen_width = enroll_window.winfo_screenwidth()
        screen_height = enroll_window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        enroll_window.geometry(f"{width}x{height}+{x}+{y}")

        enroll_window.configure(bg="#E6F1FA")  # Fondo clarito

        # Campos
        tk.Label(enroll_window, text="N° Acta:", bg="#E6F1FA").pack(pady=5)
        acta_entry = tk.Entry(enroll_window)
        acta_entry.pack(pady=5)

        tk.Label(enroll_window, text="RUT Alumno:", bg="#E6F1FA").pack(pady=5)
        rut_entry = tk.Entry(enroll_window)
        rut_entry.pack(pady=5)

        tk.Label(enroll_window, text="ID Curso:", bg="#E6F1FA").pack(pady=5)
        id_curso_entry = tk.Entry(enroll_window)
        id_curso_entry.pack(pady=5)

        tk.Label(enroll_window, text="Fecha Inscripción (YYYY-MM-DD):", bg="#E6F1FA").pack(pady=5)
        fecha_inscripcion_entry = tk.Entry(enroll_window)
        fecha_inscripcion_entry.pack(pady=5)

        tk.Label(enroll_window, text="Fecha Término Condicional (YYYY-MM-DD):", bg="#E6F1FA").pack(pady=5)
        fecha_termino_entry = tk.Entry(enroll_window)
        fecha_termino_entry.pack(pady=5)

        tk.Label(enroll_window, text="Año Inscripción (YYYY):", bg="#E6F1FA").pack(pady=5)
        anio_entry = tk.Entry(enroll_window)
        anio_entry.pack(pady=5)

        # Botón Guardar
        def save_enrollment():
            numero_acta = acta_entry.get().strip()
            rut = rut_entry.get().strip()
            id_curso_text = id_curso_entry.get().strip()
            fecha_insc = fecha_inscripcion_entry.get().strip()
            fecha_term = fecha_termino_entry.get().strip() or None
            anio_text = anio_entry.get().strip()

            if not numero_acta or not rut or not id_curso_text or not fecha_insc or not anio_text:
                messagebox.showwarning("Campos vacíos",
                                       "Complete todos los campos requeridos (incluyendo N° Acta).")
                return

            # ID Curso
            try:
                id_curso = int(id_curso_text)
            except ValueError:
                messagebox.showerror("Error", "El ID del curso debe ser un número entero.")
                return

            # Año de inscripción
            try:
                anio_inscripcion = int(anio_text)
            except ValueError:
                messagebox.showerror("Error", "El año de inscripción debe ser un entero (YYYY).")
                return

            # Llamar a la función enroll_student con numero_acta
            if enroll_student(rut, id_curso, numero_acta, fecha_insc, fecha_term, anio_inscripcion):
                messagebox.showinfo("Éxito", "Alumno matriculado correctamente.")
                enroll_window.destroy()
            else:
                messagebox.showerror("Error", "No se pudo matricular el alumno.")

        tk.Button(enroll_window, text="Guardar", bg="#ADD8E6", command=save_enrollment).pack(pady=10)

    # ---------------------------------------------------
    #       MÉTODOS RELACIONADOS A CURSOS / ALUMNOS
    # ---------------------------------------------------
    def show_courses(self):
        courses = fetch_courses()
        columns = ("id_curso", "nombre_curso", "descripcion", "modalidad", "codigo_sence", "codigo_elearning")
        headers = ("ID", "Nombre", "Descripción", "Modalidad", "Código SENCE", "Código eLearning")
        self._populate_tree(columns, headers, courses)

    def add_course_window(self):
        self._generic_add_window(
            "Añadir Curso",
            insert_course,
            [
                ("Nombre:", None),
                ("Descripción:", None),
                ("Modalidad:", None),
                ("Código SENCE:", int),
                ("Código eLearning:", int)
            ]
        )

    def show_students(self):
        students = fetch_all_students()
        columns = ("rut", "nombre", "apellido", "correo", "telefono", "profesion", "direccion", "ciudad", "comuna")
        headers = ("RUT", "Nombre", "Apellido", "Correo", "Teléfono", "Profesión", "Dirección", "Ciudad", "Comuna")
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

    def search_student_window(self):
        window = tk.Toplevel(self.root)
        window.title("Buscar Alumno")
        window.geometry("300x200")
        window.configure(bg="#F0F8FF")

        tk.Label(window, text="RUT:", bg="#F0F8FF").pack(pady=10)
        rut_entry = tk.Entry(window, width=30)
        rut_entry.pack(pady=5)

        def search():
            rut = rut_entry.get().strip()
            if not rut:
                messagebox.showwarning("Error", "Ingrese RUT")
                return

            student = fetch_student_by_rut(rut)
            if student:
                self._populate_tree(
                    ("rut", "nombre", "apellido", "correo", "telefono"),
                    ("RUT", "Nombre", "Apellido", "Correo", "Teléfono"),
                    [student]
                )
                window.destroy()
            else:
                messagebox.showerror("Error", "Alumno no encontrado")

        tk.Button(window, text="Buscar", bg="#ADD8E6", command=search).pack(pady=20)

    def delete_student_window(self):
        window = tk.Toplevel(self.root)
        window.title("Eliminar Alumno")
        window.geometry("300x200")
        window.configure(bg="#F0F8FF")

        tk.Label(window, text="RUT:", bg="#F0F8FF").pack(pady=10)
        rut_entry = tk.Entry(window, width=30)
        rut_entry.pack(pady=5)

        def delete():
            if messagebox.askyesno("Confirmar", "¿Seguro que desea eliminar?"):
                rut = rut_entry.get().strip()
                if delete_student_by_rut(rut):
                    messagebox.showinfo("Éxito", "Alumno eliminado")
                    window.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo eliminar")

        tk.Button(window, text="Eliminar", bg="#FF6B6B", command=delete).pack(pady=20)

    def show_courses_by_student(self):
        window = tk.Toplevel(self.root)
        window.title("Cursos por Alumno")
        window.geometry("300x200")
        window.configure(bg="#F0F8FF")

        tk.Label(window, text="RUT:", bg="#F0F8FF").pack(pady=10)
        rut_entry = tk.Entry(window, width=30)
        rut_entry.pack(pady=5)

        def search():
            rut = rut_entry.get().strip()
            courses = fetch_courses_by_student_rut(rut)
            if courses:
                self._populate_tree(
                    ("nombre_curso", "fecha_inscripcion"),
                    ("Curso", "Fecha Inscripción"),
                    courses
                )
                window.destroy()
            else:
                messagebox.showinfo("Info", "No se encontraron cursos")

        tk.Button(window, text="Buscar", bg="#ADD8E6", command=search).pack(pady=20)

    # ---------------------------------------------------
    #       MÉTODOS RELACIONADOS A PAGOS
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
        window.geometry("300x200")
        window.configure(bg="#F0F8FF")

        try:
            window.iconbitmap('assets/logo1.ico')
            logo = tk.PhotoImage(file='assets/logomarco.png')
            logo_label = tk.Label(window, image=logo, bg="#F0F8FF")
            logo_label.image = logo
            logo_label.pack(pady=10)
        except Exception as e:
            print(f"Error al cargar logo: {e}")

        tk.Label(window, text="ID Inscripción:", bg="#F0F8FF").pack(pady=10)
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
                    window.destroy()
                else:
                    messagebox.showinfo("Info", "No se encontraron pagos")
            except ValueError:
                messagebox.showerror("Error", "ID inválido")

        tk.Button(window, text="Buscar", bg="#ADD8E6", command=search).pack(pady=20)

    # ---------------------------------------------------
    #       MÉTODOS RELACIONADOS A FACTURAS
    # ---------------------------------------------------
    def show_invoices(self):
        invoices = fetch_invoices()
        columns = ("id_factura", "id_inscripcion", "numero_factura", "monto_total", "estado")
        headers = ("ID", "Inscripción", "N° Factura", "Monto Total", "Estado")
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
