import tkinter as tk
from tkinter import ttk, messagebox,filedialog
import os
from PIL import Image, ImageTk
from datetime import datetime
from database.db_config import connect_db
from itertools import cycle  # <<--- Para el validador avanzado de RUT
from .excel_export import ExcelExporter
from tkinterdnd2 import DND_FILES, TkinterDnD
import base64
import math
from functools import wraps
from tkcalendar import DateEntry
from .cotizacion_window import CotizacionWindow
from helpers.doc_generator import generate_pagare_docx
from helpers.num_a_let import numero_a_letras


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

def requiere_rol_gui(rol_permitido):
    """
    Decorador para verificar si el usuario tiene el rol permitido.
    Muestra un mensaje de error en la GUI si no tiene permisos.
    """
    def decorador(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Verificar el rol del usuario desde la instancia de la clase
            if getattr(self, 'rol', None) != rol_permitido:
                # Mostrar un mensaje de error en la GUI
                messagebox.showerror(
                    "Permiso Denegado",
                    f"No tiene permiso para acceder a esta funcionalidad. Rol requerido: {rol_permitido}."
                )
                return  # No ejecuta la función si no tiene permisos
            return func(self, *args, **kwargs)  # Ejecuta la función si tiene permisos
        return wrapper
    return decorador

# --------------------------------------------------------------------
#   IMPORTAR FUNCIONES DE LA BASE DE DATOS (queries.py o similares)
# --------------------------------------------------------------------

from database.queries import (
    fetch_courses,insert_course,update_course,delete_course_by_id,                                  #Cursos
    validate_curso_exists,get_course_duration,add_business_days,


    fetch_courses_by_student_rut,fetch_all_students,insert_student,fetch_student_by_rut,            #Alumnos
    delete_student_by_rut,fetch_students_by_name_apellido,validate_alumno_exists,

    fetch_payments,insert_payment,fetch_payments_by_inscription,insert_payment_contribution,        #Pagos
    update_payment_status,fetch_alumno_curso_inscripcion,

    insert_invoice,fetch_invoices,                                                                  #Facturas
    
    fetch_user_by_credentials,enroll_student,fetch_inscriptions,                                    #Inscripciones
    update_inscription,update_student,validate_duplicate_enrollment,
    format_inscription_data,delete_inscription,fetch_inscription_by_id,
    get_course_duration, add_business_days,fetch_inscription_details,

    get_empresa_by_name,get_or_create_empresa,register_new_empresa,fetch_all_empresas,              #Empresas
    update_empresa,insert_empresa,fetch_contactos_by_empresa,fetch_empresa_by_rut,
    insert_contacto_empresa,update_contacto_empresa,delete_contacto_empresa,

    fetch_cotizaciones          
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
                # Si las credenciales son correctas, almacenamos los datos del usuario
                self.username = user.get("username")
                self.rol = user.get("rol")  # Guardamos el rol del usuario
                print(f"Usuario autenticado: {self.username}, Rol: {self.rol}")

                # Ocultamos el login y mostramos la interfaz principal
                self.login_frame.hide()
                self.setup_main_interface()
            else:
                messagebox.showerror("Error", "Credenciales inválidas. Revise la escritura.")

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
        pagos_menu.add_command(label="Actualizar Estado", command=self.update_payment_status_window)
        #pagos_menu.add_command(label="Actualizar Cuotas", command=self.update_payment_contribution_window)
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
        cotizaciones_menu.add_command(label="Ver Cotizaciones", command=self.show_cotizaciones)
        cotizaciones_menu.add_command(label="Generar Cotizacion", command=self.show_cotizacion_window)
        menubar.add_cascade(label="Cotizaciones", menu=cotizaciones_menu)

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

        # Crear menú contextual
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copiar celda", command=self._copy_selected_cell)
        self.context_menu.add_command(label="Copiar fila", command=self._copy_selected_row)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Cancelar", command=self.context_menu.unpost)

        # Vincular eventos
        self.tree.bind("<Button-3>", self._show_context_menu)  # Clic derecho
        self.tree.bind("<Control-c>", lambda e: self._copy_selected_cell())  # Ctrl+C
        self.tree.bind("<Control-r>", lambda e: self._copy_selected_row())   # Ctrl+R

    def _update_title_label(self, text):
        """
        Actualiza el texto del título.
        
        Args:
            text (str): El texto a mostrar en el título
        """
        if self.title_label:
            self.title_label.config(text=text)

    def _show_context_menu(self, event):
        """Muestra el menú contextual en la posición del clic"""
        try:
            self.tree.selection_set(self.tree.identify_row(event.y))
            self.context_menu.post(event.x_root, event.y_root)
            return "break"
        except:
            pass

    def _copy_selected_cell(self):
        """Copia el contenido de la celda seleccionada"""
        try:
            selection = self.tree.selection()
            if not selection:
                return

            # Obtener la columna seleccionada o usar la primera
            column = self.tree.identify_column(self.tree.winfo_pointerx() - self.tree.winfo_rootx())
            if not column:
                column = '#1'

            col_id = int(str(column).replace('#', '')) - 1
            cell_value = self.tree.item(selection[0])['values'][col_id]

            # Copiar al portapapeles
            self.root.clipboard_clear()
            self.root.clipboard_append(str(cell_value))

            # Mostrar mensaje de éxito
            messagebox.showinfo("Copiado", f"Valor copiado al portapapeles:\n{cell_value}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo copiar el valor: {str(e)}")

    def _copy_selected_row(self):
        """Copia toda la fila seleccionada"""
        try:
            selection = self.tree.selection()
            if not selection:
                return

            # Obtener valores de la fila
            row_values = self.tree.item(selection[0])['values']
            
            # Convertir a texto con tabulaciones
            row_text = '\t'.join(str(value) for value in row_values)
            
            # Copiar al portapapeles
            self.root.clipboard_clear()
            self.root.clipboard_append(row_text)
            
            # Mostrar mensaje de éxito
            messagebox.showinfo("Copiado", "Fila completa copiada al portapapeles")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo copiar la fila: {str(e)}")

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
                    
            # Actualizar el título
            self._update_title_label("Listado de Inscripciones")
                    
            # Definir las columnas y headers
            columns = (
                "ID", "N_Acta", "RUT", "Nombre_Completo",
                "ID_Curso", "F_Inscripcion", "F_Termino",
                "Año", "Empresa", "Codigo_Sence", "Folio", "Estado_Pago"
            )
                
            headers = (
                "ID", "N° Acta", "RUT", "Nombre Completo",
                "Curso", "F. Inscripción", "F. Término",
                "Año", "Empresa", "Código SENCE", "Folio", "Estado"
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
                            formatted.get("Empresa", ""),
                            formatted.get("Codigo_Sence", ""),
                            formatted.get("Folio", ""),
                            formatted.get("Estado_Pago", "SIN PROCESAR")
                        ]
                        formatted_data.append(row)
                
            # Limpiar y configurar el tree
            self.tree.delete(*self.tree.get_children())
            self.tree.config(columns=columns, show="headings")
                
            # Configurar encabezados y columnas con anchos optimizados
            column_widths = {
                "ID": 50,                  # IDs suelen ser cortos
                "N_Acta": 60,             # Números de acta suelen ser cortos
                "RUT": 90,                # RUT chileno tiene largo fijo
                "Nombre_Completo": 200,    # Nombres necesitan espacio razonable
                "ID_Curso": 90,           # Códigos de curso suelen ser cortos
                "F_Inscripcion": 90,      # Fechas tienen largo fijo
                "F_Termino": 90,          # Fechas tienen largo fijo
                "Año": 50,                # Año es muy corto
                "Empresa": 150,           # Nombres de empresa pueden variar
                "Codigo_Sence": 100,      # Códigos SENCE son números
                "Folio": 60,              # Folios suelen ser cortos
                "Estado_Pago": 90         # Estados son palabras cortas
            }

            # Aplicar configuración de columnas
            for column, header in zip(columns, headers):
                self.tree.heading(column, text=header, anchor=tk.CENTER)
                width = column_widths.get(column, 100)
                self.tree.column(column, width=width, minwidth=50, anchor=tk.CENTER)
                
            # Insertar datos y aplicar colores según el estado
            for item in formatted_data:
                estado = item[-1]  # El estado es la última columna
                tag = self._get_estado_tag(estado)
                item_id = self.tree.insert("", "end", values=item, tags=(tag,))
                
            # Configurar colores para los diferentes estados
            self.tree.tag_configure('pendiente', background='#FFF3CD')    # Amarillo claro
            self.tree.tag_configure('pagado', background='#D4EDDA')       # Verde claro
            self.tree.tag_configure('cancelado', background='#F8D7DA')    # Rojo claro
            self.tree.tag_configure('sin_procesar', background='#E2E3E5') # Gris claro
                    
        except Exception as e:
            print(f"Error al mostrar inscripciones: {e}")
            import traceback
            traceback.print_exc()

    def _get_estado_tag(self, estado):
        """
        Determina el tag de color según el estado del pago
        """
        estado = estado.lower()
        if estado == 'pendiente':
            return 'pendiente'
        elif estado == 'pagado':
            return 'pagado'
        elif estado == 'cancelado':
            return 'cancelado'
        else:  # 'SIN PROCESAR'
            return 'sin_procesar'

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
 
    @requiere_rol_gui("admin")
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
    
    @requiere_rol_gui("admin")
    def update_inscription_window(self):
        window = tk.Toplevel(self.root)
        window.title("Actualizar Inscripción")
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
            "duracionDias",
            "tipo_curso",
            "resolucion",
            "fecha_resolucion",
            "fecha_vigencia",
            "valor_alumno_sence"
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
            "Duración (días)",
            "Tipo de Curso",
            "Resolución",
            "Fecha Resolución",
            "Fecha Vigencia",
            "Valor Alumno SENCE"
        )

        self._update_title_label("Listado de Cursos")
        self._populate_tree(columns, headers, courses)

        # Ajustar anchos de columna dinámicamente
        if hasattr(self, 'tree'):
            self.tree.column("id_curso", width=80, stretch=False)
            self.tree.column("nombre_curso", width=250, stretch=True)
            self.tree.column("modalidad", width=100, stretch=False)
            self.tree.column("codigo_sence", width=120, stretch=False)
            self.tree.column("codigo_elearning", width=120, stretch=False)
            self.tree.column("horas_cronologicas", width=100, stretch=False)
            self.tree.column("horas_pedagogicas", width=100, stretch=False)
            self.tree.column("valor", width=120, stretch=False)
            self.tree.column("duracionDias", width=120, stretch=False)
            self.tree.column("tipo_curso", width=150, stretch=False)
            self.tree.column("resolucion", width=150, stretch=False)
            self.tree.column("fecha_resolucion", width=120, stretch=False)
            self.tree.column("fecha_vigencia", width=120, stretch=False)
            self.tree.column("valor_alumno_sence", width=150, stretch=False)

        # Configurar scroll horizontal si es necesario
        if hasattr(self, 'tree_scroll_horizontal'):
            self.tree_scroll_horizontal.pack(side=tk.BOTTOM, fill=tk.X)
            self.tree.configure(xscrollcommand=self.tree_scroll_horizontal.set)
    
    @requiere_rol_gui("admin")
    def add_course_window(self):
        """
        Ventana para añadir un nuevo curso, ajustada con el campo 'Valor' y sin fondo blanco.
        """
        window = tk.Toplevel(self.root)
        window.title("Añadir Curso")
        window.configure(bg="#f0f5ff")
        
        # Ocultar la ventana inicialmente
        window.withdraw()
        
        # Posicionar la ventana en el centro de la pantalla
        width, height = 1000, 500  # Ajuste de tamaño
        scr_w = window.winfo_screenwidth()
        scr_h = window.winfo_screenheight()
        x = (scr_w // 2) - (width // 2)
        y = (scr_h // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Agregar el icono
        try:
            window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar ícono: {e}")

        # Frame principal
        main_frame = tk.Frame(window, bg="#f0f5ff", padx=30, pady=20)
        main_frame.pack(fill="both", expand=True)

        # Variables
        id_var = tk.StringVar()
        nombre_var = tk.StringVar()
        modalidad_var = tk.StringVar(value="Presencial")  # Valor por defecto
        tipo_curso_var = tk.StringVar(value="FORMACION")  # Valor por defecto
        sence_var = tk.StringVar()
        elearn_var = tk.StringVar()
        horas_cron_var = tk.StringVar()
        valor_var = tk.StringVar()  # Nueva variable para 'Valor'
        duracion_dias_var = tk.StringVar()
        resolucion_var = tk.StringVar()
        valor_alumno_sence_var = tk.StringVar()

        # Opciones ENUM
        modalidades = ["Presencial", "Online", "Híbrido"]
        tipos_curso = ["FORMACION", "COMPETENCIA"]

        # Función para crear etiquetas y entradas
        def create_label_entry(parent, label_text, row, col, var=None, width=40, is_date=False, is_option=False, options=None):
            label = tk.Label(parent, text=label_text, bg="#f0f5ff", fg="#022e86", font=("Helvetica", 10), anchor="e")
            label.grid(row=row, column=col, padx=(10, 5), pady=10, sticky="e")

            if is_date:
                # Usa DateEntry para seleccionar fechas
                entry = DateEntry(
                    parent,
                    width=width // 2,
                    font=("Helvetica", 10),
                    relief="solid",
                    bd=1,
                    date_pattern="yyyy-mm-dd",  # Formato de fecha
                    background="darkblue",
                    foreground="white",
                    borderwidth=2
                )
                entry.grid(row=row, column=col + 1, padx=(0, 20), pady=10, sticky="w")
                return entry
            elif is_option:
                entry = ttk.Combobox(parent, values=options, textvariable=var, state="readonly", width=30, font=("Helvetica", 10))
                entry.grid(row=row, column=col + 1, padx=(0, 20), pady=10, sticky="w")
                return entry
            else:
                entry = tk.Entry(parent, width=width, font=("Helvetica", 10), relief="solid", bd=1, textvariable=var)
                entry.grid(row=row, column=col + 1, padx=(0, 20), pady=10, sticky="w")
                return entry

        # Configurar campos
        create_label_entry(main_frame, "ID del Curso:", 1, 0, id_var)
        create_label_entry(main_frame, "Nombre:", 2, 0, nombre_var)
        create_label_entry(main_frame, "Modalidad:", 3, 0, modalidad_var, is_option=True, options=modalidades)
        create_label_entry(main_frame, "Código SENCE:", 4, 0, sence_var)
        create_label_entry(main_frame, "Duración (días):", 5, 0, duracion_dias_var)
        create_label_entry(main_frame, "Tipo de Curso:", 6, 0, tipo_curso_var, is_option=True, options=tipos_curso)
        create_label_entry(main_frame, "Valor del Curso:", 7, 0, valor_var)  # Campo para Valor

        create_label_entry(main_frame, "Código eLearning:", 1, 2, elearn_var)
        create_label_entry(main_frame, "Horas Cronológicas:", 2, 2, horas_cron_var)
        create_label_entry(main_frame, "Resolución:", 3, 2, resolucion_var)
        fecha_resolucion_entry = create_label_entry(main_frame, "Fecha Resolución:", 4, 2, is_date=True)
        fecha_vigencia_entry = create_label_entry(main_frame, "Fecha Vigencia:", 5, 2, is_date=True)
        create_label_entry(main_frame, "Valor por Alumno SENCE:", 6, 2, valor_alumno_sence_var)

        # Label para horas pedagógicas (calculado automáticamente)
        horas_pedag_label = tk.Label(
            main_frame,
            text="Horas Pedagógicas: 0.0",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10)
        )
        horas_pedag_label.grid(row=8, column=0, columnspan=4, pady=10)

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
            tipo_curso = tipo_curso_var.get().strip()
            sence_text = sence_var.get().strip()
            elearn_text = elearn_var.get().strip()
            horas_cron_text = horas_cron_var.get().strip()
            valor_text = valor_var.get().strip()
            duracion_dias_text = duracion_dias_var.get().strip()
            resolucion = resolucion_var.get().strip()
            fecha_resolucion = fecha_resolucion_entry.get()
            fecha_vigencia = fecha_vigencia_entry.get()
            valor_alumno_sence_text = valor_alumno_sence_var.get().strip()

            # Validaciones
            if not id_curso or not nombre_curso or not modalidad or not tipo_curso:
                messagebox.showwarning(
                    "Campos requeridos",
                    "Los campos ID del Curso, Nombre, Modalidad y Tipo de Curso son obligatorios.",
                    parent=window
                )
                return

            # Convertir y validar campos numéricos
            try:
                codigo_sence = int(sence_text) if sence_text else None
                codigo_elearn = int(elearn_text) if elearn_text else None
                horas_cron = float(horas_cron_text) if horas_cron_text else None
                valor_curso = int(valor_text) if valor_text else None  # Cambiado a int para 'valor'
                duracion_dias = int(duracion_dias_text) if duracion_dias_text else None
                valor_alumno_sence = int(valor_alumno_sence_text) if valor_alumno_sence_text else None  # Cambiado a int para 'valor_alumno_sence'
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Por favor, verifica los campos numéricos.",
                    parent=window
                )
                return

            # Función para convertir fechas al formato YYYY-MM-DD
            def convert_date(date_str):
                if date_str and date_str != "":
                    try:
                        fecha = datetime.strptime(date_str, '%Y-%m-%d')
                        return fecha.strftime('%Y-%m-%d')
                    except ValueError:
                        return None
                return None

            fecha_resolucion_converted = convert_date(fecha_resolucion)
            fecha_vigencia_converted = convert_date(fecha_vigencia)

            # Verificar fechas válidas
            if (fecha_resolucion and not fecha_resolucion_converted) or (fecha_vigencia and not fecha_vigencia_converted):
                messagebox.showerror(
                    "Error",
                    "Formato de fecha inválido. Use YYYY-MM-DD.",
                    parent=window
                )
                return

            # Guardar curso (llama a tu función insert_course)
            success = insert_course(
                id_curso, nombre_curso, modalidad, codigo_sence, codigo_elearn,
                horas_cron, valor_curso, duracion_dias, tipo_curso, resolucion,
                fecha_resolucion_converted, fecha_vigencia_converted, valor_alumno_sence
            )

            if success:
                messagebox.showinfo("Éxito", "Curso añadido correctamente.", parent=window)
                self.show_courses()  # Actualiza la vista
                window.destroy()
            else:
                messagebox.showerror("Error", "No se pudo añadir el curso.", parent=window)

        # Botón para guardar
        save_button = tk.Button(
            main_frame,
            text="Guardar Curso",
            bg="#022e86",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=30,
            pady=10,
            cursor="hand2",
            command=save_course
        )
        save_button.grid(row=9, column=0, columnspan=4, pady=30)

        # Forzar la actualización de la interfaz para renderizar todos los widgets
        window.update_idletasks()

        # Mostrar la ventana después de que todo esté construido
        window.deiconify()

    @requiere_rol_gui("admin")
    def edit_course_window(self):
        window = tk.Toplevel(self.root)
        window.title("Editar Curso")
        window.geometry("900x500")
        scr_w = window.winfo_screenwidth()
        scr_h = window.winfo_screenheight()
        x = (scr_w // 2) - (900 // 2)
        y = (scr_h // 2) - (500 // 2)
        window.geometry(f"{900}x{500}+{x}+{y}")
        window.configure(bg="#f0f5ff")
        window.grab_set()
        window.focus_force()

        try:
            window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar ícono: {e}")

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

        # Variables con nombres corregidos
        nombre_var = tk.StringVar()
        modalidad_var = tk.StringVar()
        codigo_sence_var = tk.StringVar()
        codigo_elearning_var = tk.StringVar()
        horas_cronologicas_var = tk.StringVar()
        horas_pedagogicas_var = tk.StringVar()
        duracion_dias_var = tk.StringVar()
        tipo_curso_var = tk.StringVar()
        resolucion_var = tk.StringVar()
        fecha_resolucion_var = tk.StringVar()
        fecha_vigencia_var = tk.StringVar()
        valor_var = tk.StringVar()
        valor_alumno_sence_var = tk.StringVar()

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

        def load_course_data():
            id_curso = id_entry.get().strip()
            if not id_curso:
                messagebox.showwarning("Error", "Debe ingresar un ID de curso.", parent=window)
                return

            try:
                conn = connect_db()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT nombre_curso, modalidad, codigo_sence, codigo_elearning,
                            horas_cronologicas, horas_pedagogicas, duracionDias, tipo_curso,
                            resolucion, fecha_resolucion, fecha_vigencia, valor, valor_alumno_sence
                        FROM cursos WHERE id_curso = %s
                    """, (id_curso,))
                    course = cursor.fetchone()
                    cursor.close()
                    conn.close()

                    if course:
                        nombre_var.set(course[0] or "")
                        modalidad_var.set(course[1] or "")
                        codigo_sence_var.set(str(course[2]) if course[2] is not None else "")
                        codigo_elearning_var.set(str(course[3]) if course[3] is not None else "")
                        horas_cronologicas_var.set(str(course[4]) if course[4] is not None else "")
                        horas_pedagogicas_var.set(str(course[5]) if course[5] is not None else "")
                        duracion_dias_var.set(str(course[6]) if course[6] is not None else "")
                        tipo_curso_var.set(course[7] or "")
                        resolucion_var.set(course[8] or "")
                        
                        # Convertir fechas al formato dd/mm/aaaa
                        def format_date(date_str):
                            if date_str:
                                try:
                                    fecha = datetime.strptime(str(date_str), '%Y-%m-%d')
                                    return fecha.strftime('%d/%m/%Y')
                                except:
                                    return "dd/mm/aaaa"
                            return "dd/mm/aaaa"

                        fecha_resolucion_var.set(format_date(course[9]))
                        fecha_vigencia_var.set(format_date(course[10]))
                        valor_var.set(str(course[11]) if course[11] is not None else "")
                        valor_alumno_sence_var.set(str(course[12]) if course[12] is not None else "")
                    else:
                        messagebox.showerror("Error", f"No se encontró el curso con ID: {id_curso}", parent=window)

            except Exception as e:
                print("Error al buscar el curso:", e)
                messagebox.showerror("Error", "Error al buscar el curso en la base de datos.", parent=window)

        # Botón de búsqueda
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

        # Crear campos del formulario
        def create_label_entry(parent, label_text, row, col, var):
            tk.Label(
                parent,
                text=label_text,
                bg="#f0f5ff",
                fg="#022e86",
                font=("Helvetica", 10),
                anchor='e'
            ).grid(row=row, column=col, padx=(10, 5), pady=10, sticky='e')
            
            if label_text == "Modalidad:":
                widget = ttk.Combobox(
                    parent,
                    values=["Presencial", "Online", "Híbrido"],
                    width=33,
                    font=("Helvetica", 10),
                    state="readonly",
                    textvariable=var
                )
            elif label_text == "Tipo Curso:":
                widget = ttk.Combobox(
                    parent,
                    values=["FORMACION", "COMPETENCIA"],
                    width=33,
                    font=("Helvetica", 10),
                    state="readonly",
                    textvariable=var
                )
            else:
                widget = tk.Entry(
                    parent,
                    width=35,
                    font=("Helvetica", 10),
                    relief="solid",
                    bd=1,
                    textvariable=var
                )
                if "Fecha" in label_text:
                    widget.insert(0, "dd/mm/aaaa")
                    widget.bind('<FocusIn>', lambda e: clear_placeholder(e, widget))
                    widget.bind('<FocusOut>', lambda e: restore_placeholder(e, widget))

            widget.grid(row=row, column=col+1, padx=(0, 20), pady=10, sticky='w')
            return widget

        # Organizar campos en dos columnas
        # Primera columna
        create_label_entry(main_frame, "Nombre:", 2, 0, nombre_var)
        create_label_entry(main_frame, "Modalidad:", 3, 0, modalidad_var)
        create_label_entry(main_frame, "Código SENCE:", 4, 0, codigo_sence_var)
        create_label_entry(main_frame, "Código eLearning:", 5, 0, codigo_elearning_var)
        create_label_entry(main_frame, "Horas Cronológicas:", 6, 0, horas_cronologicas_var)
        create_label_entry(main_frame, "Horas Pedagógicas:", 7, 0, horas_pedagogicas_var)

        # Segunda columna
        create_label_entry(main_frame, "Duración en Días:", 2, 2, duracion_dias_var)
        create_label_entry(main_frame, "Tipo Curso:", 3, 2, tipo_curso_var)
        create_label_entry(main_frame, "Resolución:", 4, 2, resolucion_var)
        create_label_entry(main_frame, "Fecha Resolución:", 5, 2, fecha_resolucion_var)
        create_label_entry(main_frame, "Fecha Vigencia:", 6, 2, fecha_vigencia_var)
        create_label_entry(main_frame, "Valor:", 7, 2, valor_var)
        create_label_entry(main_frame, "Valor Alumno SENCE:", 8, 2, valor_alumno_sence_var)

        def clear_placeholder(event, widget):
            if widget.get() == "dd/mm/aaaa":
                widget.delete(0, tk.END)

        def restore_placeholder(event, widget):
            if widget.get() == "":
                widget.insert(0, "dd/mm/aaaa")

        def validate_date(date_str):
            if date_str == "dd/mm/aaaa" or not date_str:
                return True
            try:
                day, month, year = map(int, date_str.split('/'))
                if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                    return True
                return False
            except:
                return False

        def save_edited_course():
            id_curso = id_entry.get().strip()
            if not id_curso:
                messagebox.showwarning("Error", "Debe ingresar un ID de curso.", parent=window)
                return

            # Validar campos obligatorios
            if not all([nombre_var.get().strip(), modalidad_var.get().strip()]):
                messagebox.showwarning(
                    "Campos requeridos",
                    "Los campos Nombre y Modalidad son obligatorios.",
                    parent=window
                )
                return

            # Validar fechas
            for fecha in [fecha_resolucion_var.get(), fecha_vigencia_var.get()]:
                if fecha != "dd/mm/aaaa" and fecha and not validate_date(fecha):
                    messagebox.showerror("Error", "El formato de fecha debe ser dd/mm/aaaa", parent=window)
                    return

            def convert_date(date_str):
                if date_str and date_str != "dd/mm/aaaa":
                    day, month, year = date_str.split('/')
                    return f"{year}-{month}-{day}"
                return None

            # Convertir valores numéricos
            try:
                curso_data = {
                    'id_curso': id_curso,  # Eliminada la conversión a int
                    'nombre_curso': nombre_var.get().strip(),
                    'modalidad': modalidad_var.get().strip(),
                    'codigo_sence': int(codigo_sence_var.get()) if codigo_sence_var.get().strip() else None,
                    'codigo_elearning': int(codigo_elearning_var.get()) if codigo_elearning_var.get().strip() else None,
                    'horas_cronologicas': int(horas_cronologicas_var.get()) if horas_cronologicas_var.get().strip() else None,  # Cambiado a int si es necesario
                    'horas_pedagogicas': float(horas_pedagogicas_var.get()) if horas_pedagogicas_var.get().strip() else None,
                    'duracionDias': int(duracion_dias_var.get()) if duracion_dias_var.get().strip() else None,
                    'tipo_curso': tipo_curso_var.get().strip() or None,
                    'resolucion': resolucion_var.get().strip() or None,
                    'fecha_resolucion': convert_date(fecha_resolucion_var.get()),
                    'fecha_vigencia': convert_date(fecha_vigencia_var.get()),
                    'valor': int(valor_var.get()) if valor_var.get().strip() else None,  # Cambiado a int si es necesario
                    'valor_alumno_sence': int(valor_alumno_sence_var.get()) if valor_alumno_sence_var.get().strip() else None  # Cambiado a int para decimal(10,0)
                }
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Por favor, verifique que los campos numéricos contengan valores válidos.",
                    parent=window
                )
                return

            success = update_course(**curso_data)

            if success:
                messagebox.showinfo("Éxito", "Curso actualizado correctamente.", parent=window)
                window.destroy()
                self.show_courses()  # Actualizar la lista de cursos
            else:
                messagebox.showerror("Error", "No se pudo actualizar el curso. Verifique los datos.", parent=window)

        # Botón guardar
        button_frame = tk.Frame(main_frame, bg="#f0f5ff")
        button_frame.grid(row=9, column=0, columnspan=4, pady=30)

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

    @requiere_rol_gui("admin")
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

    @requiere_rol_gui("admin")
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
    
    @requiere_rol_gui("admin")
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
        try:
            if not hasattr(self, 'tree'):
                print("Error: tree no está inicializado")
                return
                    
            # Actualizar el título
            self._update_title_label("Listado de Pagos")
                    
            # Definir las columnas y headers
            columns = (
                "ID", "Inscripcion", "Alumno", "Curso", "N_Acta",
                "Tipo_Pago", "Modalidad_Pago", "Cuotas", "Valor_Total",
                "Estado", "F_Inscripcion", "F_Final"
            )
                
            headers = (
                "ID", "Inscripción", "Alumno", "Curso", "N° Acta",
                "Tipo", "Modalidad", "Cuotas", "Valor Total",
                "Estado", "F. Inscripción", "F. Final"
            )

            # Obtener datos
            data_raw = fetch_payments()
            formatted_data = []
                
            if data_raw:
                for payment in data_raw:
                    # Formatear fechas y valores monetarios
                    fecha_inscripcion = payment[4].strftime('%Y-%m-%d') if payment[4] else ''
                    fecha_final = payment[5].strftime('%Y-%m-%d') if payment[5] else ''
                    valor_total = f"${payment[7]:,.0f}" if payment[7] else ''

                    row = [
                        payment[0],                    # ID
                        payment[1],                    # ID Inscripción
                        payment[10],                   # Nombre Alumno
                        payment[11],                   # Nombre Curso
                        payment[9],                    # N° Acta
                        payment[2].capitalize(),       # Tipo Pago
                        payment[3].capitalize(),       # Modalidad Pago
                        f"{payment[6]}/{payment[6]}",  # Cuotas (total/total)
                        valor_total,                   # Valor Total
                        payment[8].upper(),            # Estado
                        fecha_inscripcion,            # Fecha Inscripción
                        fecha_final                    # Fecha Final
                    ]
                    formatted_data.append(row)
                
            # Limpiar y configurar el tree
            self.tree.delete(*self.tree.get_children())
            self.tree.config(columns=columns, show="headings")
                
            # Configurar encabezados y columnas con anchos optimizados
            column_widths = {
                "ID": 60,
                "Inscripcion": 80,
                "Alumno": 200,
                "Curso": 200,
                "N_Acta": 80,
                "Tipo_Pago": 80,
                "Modalidad_Pago": 90,
                "Cuotas": 70,
                "Valor_Total": 100,
                "Estado": 90,
                "F_Inscripcion": 100,
                "F_Final": 100
            }

            # Aplicar configuración de columnas
            for column, header in zip(columns, headers):
                self.tree.heading(column, text=header, anchor=tk.CENTER)
                width = column_widths.get(column, 100)
                self.tree.column(column, width=width, minwidth=50, anchor=tk.CENTER)
                
            # Insertar datos y aplicar colores según el estado
            for item in formatted_data:
                estado = item[9]  # Estado es la columna 9
                tag = self._get_estado_pago_tag(estado)
                self.tree.insert("", "end", values=item, tags=(tag,))
                
            # Configurar colores para los diferentes estados
            self.tree.tag_configure('PENDIENTE', background='#FFF3CD')  # Amarillo claro
            self.tree.tag_configure('PAGADO', background='#D4EDDA')     # Verde claro
            self.tree.tag_configure('CANCELADO', background='#F8D7DA')  # Rojo claro

        except Exception as e:
            print(f"Error al mostrar pagos: {e}")
            import traceback
            traceback.print_exc()

    def _get_estado_pago_tag(self, estado):
        """
        Determina el tag de color según el estado del pago
        """
        estado = estado.upper()
        if estado in ['PENDIENTE', 'PAGADO', 'CANCELADO']:
            return estado
        return 'PENDIENTE'  # Estado por defecto

    def add_payment_window(self):
        window = tk.Toplevel(self.root)
        window.title("Añadir Pago")
        window.geometry("900x550")
        window.configure(bg="#f0f5ff")
        window.grab_set()
        window.focus_force()

        # Intentar ícono (opcional)
        try:
            window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar ícono de la ventana: {e}")

        # Centrar ventana
        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight()
        x = (sw // 2) - (900 // 2)
        y = (sh // 2) - (550 // 2)
        window.geometry(f"900x550+{x}+{y}")

        main_frame = ttk.Frame(window, padding="20")
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = ttk.Label(
            main_frame,
            text="Registro de Pago",
            font=("Helvetica", 16, "bold"),
            foreground="#022e86"
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))

        # --- Frame: Información de inscripción ---
        inscription_frame = ttk.LabelFrame(main_frame, text="Información de Inscripción", padding="10")
        inscription_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 10))

        ttk.Label(inscription_frame, text="ID Inscripción:").grid(row=0, column=0, padx=5)
        inscription_entry = ttk.Entry(inscription_frame, width=10)
        inscription_entry.grid(row=0, column=1, padx=5)

        student_label = ttk.Label(inscription_frame, text="Alumno: ")
        student_label.grid(row=0, column=3, padx=20)
        course_label = ttk.Label(inscription_frame, text="Curso: ")
        course_label.grid(row=0, column=4, padx=20)
        acta_label = ttk.Label(inscription_frame, text="N° Acta: ")
        acta_label.grid(row=0, column=5, padx=20)

        # Diccionario donde guardaremos la info recuperada:
        fetched_data = {
            "id_inscripcion": None,
            "numero_acta": None,
            "fecha_inscripcion": None,
            "anio_inscripcion": None,
            "rut_alumno": None,
            "direccion_alumno": None,
            "nombre_alumno": None,
            "nombre_curso": None,
            "valor_curso": 0.0,
        }

        def fetch_inscription_info():
            """Busca la inscripción, alumno y curso, y llena la interfaz."""
            try:
                inscripcion_id = int(inscription_entry.get())
            except ValueError:
                messagebox.showerror("Error", "ID de inscripción inválido", parent=window)
                return

            info = fetch_alumno_curso_inscripcion(inscripcion_id)
            if not info:
                messagebox.showerror("Error", "Inscripción no encontrada", parent=window)
                return

            # Llenamos fetched_data
            fetched_data["id_inscripcion"] = info["id_inscripcion"]
            fetched_data["numero_acta"] = info["numero_acta"]
            fetched_data["fecha_inscripcion"] = info["fecha_inscripcion"]
            fetched_data["anio_inscripcion"] = info["anio_inscripcion"]
            fetched_data["rut_alumno"] = info["rut_alumno"]
            fetched_data["direccion_alumno"] = info["direccion_alumno"]
            fetched_data["nombre_alumno"] = info["nombre_alumno"]
            fetched_data["nombre_curso"] = info["nombre_curso"]
            fetched_data["valor_curso"] = info["valor_curso"] or 0.0

            # Mostramos en los labels
            student_label.config(text=f"Alumno: {fetched_data['nombre_alumno']}")
            course_label.config(text=f"Curso: {fetched_data['nombre_curso']}")
            acta_label.config(text=f"N° Acta: {fetched_data['numero_acta']}")
            
            # Actualizar el campo de valor con el valor del curso
            valor_entry.delete(0, tk.END)
            valor_entry.insert(0, str(fetched_data["valor_curso"]))

        ttk.Button(inscription_frame, text="Buscar", command=fetch_inscription_info).grid(row=0, column=2, padx=5)

        # --- Frame: Detalles del pago ---
        payment_frame = ttk.LabelFrame(main_frame, text="Detalles del Pago", padding="10")
        payment_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=10)

        tipo_pago_var = tk.StringVar()
        modalidad_pago_var = tk.StringVar()
        num_cuotas_var = tk.StringVar(value="1")

        ttk.Label(payment_frame, text="Tipo de Pago:").grid(row=0, column=0, padx=5, pady=5)
        tipo_pago_combo = ttk.Combobox(payment_frame, textvariable=tipo_pago_var,
                                       values=["contado", "pagare"],
                                       state="readonly", width=15)
        tipo_pago_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(payment_frame, text="Modalidad:").grid(row=0, column=2, padx=5, pady=5)
        modalidad_combo = ttk.Combobox(payment_frame, textvariable=modalidad_pago_var,
                                       values=["completo", "diferido"],
                                       state="readonly", width=15)
        modalidad_combo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(payment_frame, text="Valor Total:").grid(row=0, column=4, padx=5, pady=5)
        valor_entry = ttk.Entry(payment_frame, width=15)
        valor_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(payment_frame, text="N° Cuotas:").grid(row=1, column=0, padx=5, pady=5)
        cuotas_entry = ttk.Entry(payment_frame, textvariable=num_cuotas_var, width=15)
        cuotas_entry.grid(row=1, column=1, padx=5, pady=5)

        # Mes de Inicio
        ttk.Label(payment_frame, text="Mes de Inicio:").grid(row=1, column=2, padx=5, pady=5)
        mes_inicio_var = tk.StringVar()
        mes_inicio_entry = ttk.Entry(payment_frame, textvariable=mes_inicio_var, width=15)
        mes_inicio_entry.grid(row=1, column=3, padx=5, pady=5)

        def on_tipo_pago_change(*args):
            """
            Muestra u oculta el botón 'Generar Contrato Pagaré'
            según sea 'pagare' o 'contado'.
            """
            if tipo_pago_var.get() == "pagare":
                cuotas_entry.config(state="normal")
                generate_button.grid(row=5, column=0, columnspan=4, pady=10)
            else:
                num_cuotas_var.set("1")
                cuotas_entry.config(state="disabled")
                generate_button.grid_remove()

        def on_modalidad_change(*args):
            """Muestra/oculta frame de contribuciones si es 'diferido'."""
            if modalidad_pago_var.get() == "diferido":
                contribuciones_frame.grid()
            else:
                contribuciones_frame.grid_remove()

        tipo_pago_var.trace("w", on_tipo_pago_change)
        modalidad_pago_var.trace("w", on_modalidad_change)

        # --- Frame: Distribución (diferido) ---
        contribuciones_frame = ttk.LabelFrame(main_frame, text="Distribución del Pago", padding="10")
        contribuciones_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=10)
        contribuciones_frame.grid_remove()  # Oculto por defecto

        ttk.Label(contribuciones_frame, text="Alumno:").grid(row=0, column=0, padx=5, pady=5)
        alumno_entry = ttk.Entry(contribuciones_frame, width=15)
        alumno_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(contribuciones_frame, text="Empresa:").grid(row=0, column=2, padx=5, pady=5)
        empresa_entry = ttk.Entry(contribuciones_frame, width=15)
        empresa_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(contribuciones_frame, text="SENCE:").grid(row=0, column=4, padx=5, pady=5)
        sence_entry = ttk.Entry(contribuciones_frame, width=15)
        sence_entry.grid(row=0, column=5, padx=5, pady=5)

        # Variables para guardar (id_pago, id_pagare)
        created_id_pago = [None]
        created_id_pagare = [None]

        def validate_and_save():
            """Inserta el pago en BD y, si es 'diferido', registra contribuciones."""
            if not inscription_entry.get():
                messagebox.showerror("Error", "Debe especificar una inscripción", parent=window)
                return

            if not valor_entry.get():
                messagebox.showerror("Error", "Debe especificar un valor total", parent=window)
                return

            # Parsear
            try:
                id_insc = int(inscription_entry.get())
                valor_total = float(valor_entry.get())
                n_cuotas = int(num_cuotas_var.get())
            except ValueError:
                messagebox.showerror("Error", "Valores numéricos inválidos", parent=window)
                return

            tipo_pago_sel = tipo_pago_var.get()
            modalidad_sel = modalidad_pago_var.get()

            # Validar contribuciones si 'diferido'
            if modalidad_sel == "diferido":
                try:
                    monto_alumno = float(alumno_entry.get() or 0)
                    monto_empresa = float(empresa_entry.get() or 0)
                    monto_sence = float(sence_entry.get() or 0)
                    total_contrib = monto_alumno + monto_empresa + monto_sence
                    if not math.isclose(total_contrib, valor_total, rel_tol=1e-9):
                        messagebox.showerror("Error",
                                             "La suma de contribuciones debe ser igual al valor total",
                                             parent=window)
                        return
                except ValueError:
                    messagebox.showerror("Error", "Valores de contribución inválidos", parent=window)
                    return
            else:
                monto_alumno = 0
                monto_empresa = 0
                monto_sence = 0

            # Insertar pago
            (id_pago, id_pagare) = insert_payment(
                id_inscripcion=id_insc,
                tipo_pago=tipo_pago_sel,
                modalidad_pago=modalidad_sel,
                valor_total=valor_total,
                num_cuotas=n_cuotas
            )
            if not id_pago:
                messagebox.showerror("Error", "No se pudo registrar el pago", parent=window)
                return

            created_id_pago[0] = id_pago
            created_id_pagare[0] = id_pagare

            # Si es diferido, insertamos contribuciones
            if modalidad_sel == "diferido":
                if monto_alumno > 0:
                    insert_payment_contribution(id_pago, "alumno", monto_alumno)
                if monto_empresa > 0:
                    insert_payment_contribution(id_pago, "empresa", monto_empresa)
                if monto_sence > 0:
                    insert_payment_contribution(id_pago, "sence", monto_sence)

            messagebox.showinfo("Éxito", "Pago registrado correctamente", parent=window)
            self.show_payments()

        def generar_contrato_pagare():
            """
            Genera el doc .docx (usando docxtpl) en la ubicación que el usuario
            escoja con 'Guardar como...'.
            """
            if not created_id_pagare[0]:
                messagebox.showerror("Error", "No hay ID de pagaré. Guarde primero con tipo 'pagare'.", parent=window)
                return

            # Construir el contexto
            contexto = {
                "id_pagare":      created_id_pagare[0],
                "nombre_alumno":  fetched_data["nombre_alumno"] or "",
                "id_alumno":      fetched_data["rut_alumno"] or "",
                "direccion":      fetched_data["direccion_alumno"] or "",
                "valor":          valor_entry.get() or "0",
                "num_cuotas":     num_cuotas_var.get(),
                "valorEscrito":   numero_a_letras(float(valor_entry.get())),
                "valor_cuota":    f"{float(valor_entry.get()) / float(num_cuotas_var.get()):.2f}",
                "cuotaEscrito":   numero_a_letras(float(valor_entry.get()) / float(num_cuotas_var.get())),
                "mes_inicio":     mes_inicio_var.get(),
                "year":           fetched_data["anio_inscripcion"] or "",
                "fecha_inscripcion": str(fetched_data["fecha_inscripcion"]) 
                                      if fetched_data["fecha_inscripcion"] else "",
            }

            template_path = "formatos/PAGARE.docx"
            # Diálogo de "guardar como"
            initial_filename = f"Pagare_{created_id_pagare[0]}.docx"
            file_path = filedialog.asksaveasfilename(
                parent=window,
                title="Guardar Contrato Pagaré",
                initialdir=os.path.expanduser("~"),
                initialfile=initial_filename,
                defaultextension=".docx",
                filetypes=[("Documentos Word", "*.docx")]
            )
            if not file_path:
                return  # Usuario canceló

            generate_pagare_docx(template_path, file_path, contexto)
            messagebox.showinfo("Éxito", f"Documento pagare generado:\n{file_path}", parent=window)

        # Botón para guardar
        save_button = ttk.Button(
            main_frame,
            text="Guardar Pago",
            command=validate_and_save,
            style="Accent.TButton"
        )
        save_button.grid(row=4, column=0, columnspan=4, pady=10)

        # Botón para generar contrato (se mostrará solo cuando 'tipo_pago' sea 'pagare')
        generate_button = ttk.Button(
            main_frame,
            text="Generar Contrato Pagaré",
            command=generar_contrato_pagare
        )
        generate_button.grid_remove()  # Oculto por defecto

        # Ajustar pesos de columnas
        for i in range(4):
            main_frame.grid_columnconfigure(i, weight=1)

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

    def update_payment_status_window(self):
        """
        Ventana para actualizar el estado de pago con múltiples opciones de búsqueda
        """
        update_window = tk.Toplevel(self.root)
        update_window.title("Actualizar Estado de Pago")
        update_window.grab_set()
        try:
            update_window.iconbitmap('assets/logo1.ico')
        except Exception as e:
            print(f"Error al cargar ícono de la ventana: {e}")

        # Configurar tamaño y posición
        window_width = 900
        window_height = 600
        x = (update_window.winfo_screenwidth() - window_width) // 2
        y = (update_window.winfo_screenheight() - window_height) // 2
        update_window.geometry(f'{window_width}x{window_height}+{x}+{y}')

        # Frame principal
        main_frame = ttk.Frame(update_window, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Frame de búsqueda
        search_frame = ttk.LabelFrame(main_frame, text="Opciones de Búsqueda", padding="5")
        search_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Variables para criterios de búsqueda
        search_type = tk.StringVar(value="rut")
        
        # Radio buttons para tipo de búsqueda
        ttk.Radiobutton(search_frame, text="RUT", variable=search_type, 
                    value="rut", command=lambda: toggle_search_fields("rut")).grid(row=0, column=0, padx=5)
        ttk.Radiobutton(search_frame, text="ID Inscripción", variable=search_type, 
                    value="id", command=lambda: toggle_search_fields("id")).grid(row=0, column=1, padx=5)
        ttk.Radiobutton(search_frame, text="Nombre y Apellido", variable=search_type, 
                    value="nombre", command=lambda: toggle_search_fields("nombre")).grid(row=0, column=2, padx=5)

        # Frame para campos de búsqueda
        fields_frame = ttk.Frame(search_frame)
        fields_frame.grid(row=1, column=0, columnspan=4, pady=5)

        # Campos de búsqueda
        # RUT
        rut_frame = ttk.Frame(fields_frame)
        ttk.Label(rut_frame, text="RUT:").pack(side="left", padx=5)
        rut_entry = ttk.Entry(rut_frame, width=15)
        rut_entry.pack(side="left", padx=5)

        # ID Inscripción
        id_frame = ttk.Frame(fields_frame)
        ttk.Label(id_frame, text="ID Inscripción:").pack(side="left", padx=5)
        id_entry = ttk.Entry(id_frame, width=10)
        id_entry.pack(side="left", padx=5)

        # Nombre y Apellido
        nombre_frame = ttk.Frame(fields_frame)
        ttk.Label(nombre_frame, text="Nombre:").pack(side="left", padx=5)
        nombre_entry = ttk.Entry(nombre_frame, width=15)
        nombre_entry.pack(side="left", padx=5)
        ttk.Label(nombre_frame, text="Apellido:").pack(side="left", padx=5)
        apellido_entry = ttk.Entry(nombre_frame, width=15)
        apellido_entry.pack(side="left", padx=5)

        def toggle_search_fields(search_mode):
            """Muestra/oculta campos según el tipo de búsqueda seleccionado"""
            rut_frame.pack_forget()
            id_frame.pack_forget()
            nombre_frame.pack_forget()

            if search_mode == "rut":
                rut_frame.pack(side="left")
            elif search_mode == "id":
                id_frame.pack(side="left")
            else:
                nombre_frame.pack(side="left")

        # Mostrar inicialmente el campo de RUT
        toggle_search_fields("rut")

        # Tabla de resultados
        table_frame = ttk.Frame(main_frame)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        columns = ("ID Pago", "N° Acta", "RUT", "Alumno", "Curso", "Valor", "Estado Actual", "F. Inscripción")
        payment_table = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)

        # Configurar columnas
        widths = {
            "ID Pago": 80, "N° Acta": 100, "RUT": 100, "Alumno": 200,
            "Curso": 200, "Valor": 100, "Estado Actual": 100, "F. Inscripción": 100
        }
        for col in columns:
            payment_table.heading(col, text=col)
            payment_table.column(col, width=widths[col])

        # Scrollbars
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=payment_table.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=payment_table.xview)
        payment_table.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        payment_table.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        # Frame para actualización
        update_frame = ttk.LabelFrame(main_frame, text="Actualizar Estado", padding="5")
        update_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        ttk.Label(update_frame, text="Nuevo Estado:").grid(row=0, column=0, padx=5, pady=5)
        estado_combo = ttk.Combobox(update_frame, values=["pendiente", "pagado", "cancelado"], 
                                state="readonly", width=15)
        estado_combo.grid(row=0, column=1, padx=5, pady=5)

        def search_payments():
            """Busca pagos según el criterio seleccionado"""
            # Limpiar tabla
            for item in payment_table.get_children():
                payment_table.delete(item)

            conn = connect_db()
            if not conn:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos")
                return

            try:
                cursor = conn.cursor()
                search_criteria = search_type.get()
                
                base_query = """
                    SELECT p.id_pago, i.numero_acta, a.rut,
                        CONCAT(a.nombre, ' ', a.apellido) as alumno,
                        c.nombre_curso, p.valor_total, p.estado,
                        p.fecha_inscripcion
                    FROM pagos p
                    JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
                    JOIN alumnos a ON i.id_alumno = a.rut
                    JOIN cursos c ON i.id_curso = c.id_curso
                    WHERE {}
                    ORDER BY p.fecha_inscripcion DESC
                """

                if search_criteria == "rut":
                    rut = rut_entry.get().strip()
                    if not validar_rut(rut):
                        messagebox.showerror("Error", "RUT inválido")
                        return
                    query = base_query.format("a.rut = %s")
                    cursor.execute(query, (rut,))

                elif search_criteria == "id":
                    inscription_id = id_entry.get().strip()
                    if not inscription_id.isdigit():
                        messagebox.showerror("Error", "ID de inscripción inválido")
                        return
                    query = base_query.format("i.id_inscripcion = %s")
                    cursor.execute(query, (inscription_id,))

                else:  # búsqueda por nombre y apellido
                    nombre = nombre_entry.get().strip()
                    apellido = apellido_entry.get().strip()
                    if not nombre and not apellido:
                        messagebox.showwarning("Advertencia", "Ingrese al menos un nombre o apellido")
                        return
                    conditions = []
                    params = []
                    if nombre:
                        conditions.append("a.nombre LIKE %s")
                        params.append(f"%{nombre}%")
                    if apellido:
                        conditions.append("a.apellido LIKE %s")
                        params.append(f"%{apellido}%")
                    query = base_query.format(" AND ".join(conditions))
                    cursor.execute(query, tuple(params))

                results = cursor.fetchall()

                if not results:
                    messagebox.showinfo("Información", "No se encontraron pagos")
                    return

                # Insertar resultados en la tabla
                for row in results:
                    formatted_row = [
                        row[0],  # ID Pago
                        row[1],  # N° Acta
                        row[2],  # RUT
                        row[3],  # Alumno
                        row[4],  # Curso
                        f"${row[5]:,.0f}",  # Valor Total
                        row[6].upper(),  # Estado
                        row[7].strftime('%Y-%m-%d')  # Fecha Inscripción
                    ]
                    payment_table.insert('', 'end', values=formatted_row)

            except Exception as e:
                messagebox.showerror("Error", f"Error al buscar pagos: {str(e)}")
            finally:
                cursor.close()
                conn.close()

        def update_selected_payment():
            """Actualiza el estado del pago seleccionado"""
            selection = payment_table.selection()
            if not selection:
                messagebox.showwarning("Advertencia", "Por favor seleccione un pago")
                return

            nuevo_estado = estado_combo.get()
            if not nuevo_estado:
                messagebox.showwarning("Advertencia", "Por favor seleccione el nuevo estado")
                return

            payment_id = payment_table.item(selection[0])['values'][0]
            current_status = payment_table.item(selection[0])['values'][6].lower()

            # Validar cambio de estado
            if current_status == nuevo_estado:
                messagebox.showinfo("Información", "El pago ya tiene ese estado")
                return

            # Confirmar acción
            if not messagebox.askyesno("Confirmar", 
                f"¿Está seguro de cambiar el estado del pago a {nuevo_estado.upper()}?"):
                return

            # Actualizar estado
            if update_payment_status(payment_id, nuevo_estado):
                messagebox.showinfo("Éxito", "Estado actualizado correctamente")
                self.show_payments()  # Actualizar la tabla
                search_payments()  # Actualizar la tabla
            else:
                messagebox.showerror("Error", "No se pudo actualizar el estado")

        # Botones
        ttk.Button(search_frame, text="Buscar", command=search_payments).grid(
            row=1, column=3, padx=5, pady=5)
        ttk.Button(update_frame, text="Actualizar Estado", command=update_selected_payment).grid(
            row=0, column=2, padx=5)
        ttk.Button(main_frame, text="Cerrar", command=update_window.destroy).grid(
            row=3, column=0, sticky="e", padx=5, pady=10)

        # Binds para tecla Enter
        rut_entry.bind('<Return>', lambda e: search_payments())
        id_entry.bind('<Return>', lambda e: search_payments())
        nombre_entry.bind('<Return>', lambda e: search_payments())
        apellido_entry.bind('<Return>', lambda e: search_payments())

        # Configuración de grid weights
        update_window.grid_columnconfigure(0, weight=1)
        update_window.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
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

    #========================================================
    #                    COTIZACIONES
    #========================================================

    def show_cotizaciones(self):
        """
        Muestra la lista de cotizaciones en el treeview
        """
        cotizaciones = fetch_cotizaciones()
        
        # Definir columnas y encabezados
        columns = (
            "id_cotizacion",
            "nombre_contacto",
            "origen",
            "fecha_cotizacion",
            "fecha_vencimiento",
            "email",
            "modo_pago",
            "cantidad_total_cursos"
        )
        
        headers = (
            "ID",
            "Nombre Contacto",
            "Origen",
            "Fecha Cotización",
            "Fecha Vencimiento",
            "Email",
            "Modo de Pago",
            "Cantidad Cursos"
        )

        self._update_title_label("Listado de Cotizaciones")
        self._populate_tree(columns, headers, cotizaciones)

        # Ajustar el ancho de las columnas específicas
        if hasattr(self, 'tree'):
            self.tree.column("id_cotizacion", width=80)
            self.tree.column("nombre_contacto", width=150)
            self.tree.column("origen", width=150)
            self.tree.column("fecha_cotizacion", width=120)
            self.tree.column("fecha_vencimiento", width=120)
            self.tree.column("email", width=200)
            self.tree.column("modo_pago", width=100)
            self.tree.column("cantidad_total_cursos", width=100)
  
    def show_cotizacion_window(self):
        window = tk.Toplevel(self.root)
        window.title("Nueva Cotización")
        CotizacionWindow(window)
    # ---------------------------------------------------
    #  Función genérica "ventanas de añadir"
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
