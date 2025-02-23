import tkinter as tk
from tkinter import ttk, messagebox,filedialog
import os
from PIL import Image, ImageTk
from datetime import datetime , timedelta
from database.db_config import connect_db
from itertools import cycle  # <<--- Para el validador avanzado de RUT
from .excel_export import ExcelExporter
from tkinterdnd2 import DND_FILES, TkinterDnD
import base64
import math
import traceback
import mysql
from functools import wraps
from tkcalendar import DateEntry, Calendar
from .cotizacion_window import CotizacionWindow
from helpers.doc_generator import generate_pagare_docx
from helpers.num_a_let import numero_a_letras
from gui.tramitaciones.tramitacion import IntegratedTramitacionesFrame
from gui.tramitaciones.ordenpago import OrdenCompraWindow
from gui.Libros import LibrosManager
from path_utils import resource_path
from docxtpl import DocxTemplate
from docx.shared import Cm

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
    validate_curso_exists,add_business_days,


    fetch_all_students,insert_student,fetch_student_by_rut,            #Alumnos
    delete_student_by_rut,fetch_students_by_name_apellido,fetch_active_students,update_current_students_table,
    update_student_contact,

    fetch_payments,insert_payment,fetch_payments_by_criteria,insert_payment_contribution,        #Pagos
    fetch_alumno_curso_inscripcion,fetch_cuotas_by_pago,register_quota_payment,
    update_cuota,search_pagare_payments,fetch_pending_payments,register_contado_payment,

    insert_invoice,fetch_inscripcion_info,update_invoice_status,                                                                  #Facturas
    
    fetch_user_by_credentials,enroll_student,fetch_inscriptions,                                    #Inscripciones
    update_inscription,update_student,validate_duplicate_enrollment,
    format_inscription_data,delete_inscription,fetch_inscription_by_id,
    add_business_days,fetch_inscriptions_filtered,verify_and_create_empresa,

    fetch_all_empresas,                                                       #Empresas
    fetch_contactos_by_empresa,fetch_all_empresas_for_combo
    ,delete_contacto_empresa,format_empresa_data,
    fetch_empresa_by_id,save_empresa,save_contacto_empresa,

    fetch_cotizaciones,                                                 #Cotizaciones   

    fetch_tramitaciones_by_rut,fetch_tramitaciones_activas,fetch_tramitaciones,fetch_tipos_tramite,  #Tramitaciones     

    fetch_carpetas_formacion,create_carpeta_libros,                                            #Libros de Clase

                                                            #Alertas
    
    check_overdue_debtors, delete_deudor_db ,insert_deudor,fetch_deudores,is_student_debtor #Deudores
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
        self.alerts_shown = set()  # Conjunto para guardar las alertas mostradas
        # Configuración de estilos, etc.
        self.setup_styles()

        # 3. Cargamos los íconos mientras sigue oculta
        try:
            # Usar solo iconbitmap con tu .ico
            self.root.iconbitmap(resource_path('assets/logo2.ico'))
        except Exception as e:
            print(f"Error al cargar íconos: {e}")

        # Instanciamos lo que necesitemos (ej. ExcelExporter)
        self.excel_exporter = ExcelExporter()

        self.main_frame = None
        self.title_label = None

        # 4. Ahora que la ventana está configurada, la mostramos.
        self.root.deiconify()

        # 5. Mostramos directamente el LoginFrame (o la interfaz principal)
        #self.show_login_frame()
        self.setup_main_interface()

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
                        rowheight=30,
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

        style.configure('TButton',
                        font=('Segoe UI', 10),
                        padding=5,
                        background='#00239c',
                        foreground='white')

        style.configure("TLabel",
                        font=('Segoe UI', 10),
                        background="#f0f0f0")

        style.configure("Title.TLabel",
                        font=('Segoe UI', 14, 'bold'),
                        background="#0f075e",
                        foreground="white")

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

        style.configure('Secondary.TButton',
                        font=('Segoe UI', 10),
                        padding=5)
        # Agregar estilo específico para tramitaciones
        style.configure("Tramitaciones.TFrame", 
                    background="#FFFFFF",
                    relief="flat",
                    borderwidth=0)
            # Estilo para el botón de alerta
        style.configure("Custom.TButton",
                    padding=6,
                    relief="flat",
                    background="#0078D7",
                    foreground="white",
                    font=('Segoe UI', 10))
        
        style.configure('Red.TButton',
                background='#dc3545',
                foreground='white',
                bordercolor='#dc3545',
                lightcolor='#dc3545',
                darkcolor='#dc3545',
                focuscolor='#dc3545',
                relief='flat',
                padding=6)

        # Configurar el hover del botón
        style.map('Red.TButton',
                background=[('active', '#c82333'),  # Un rojo más oscuro para el hover
                            ('pressed', '#bd2130')],  # Un rojo aún más oscuro para cuando se presiona
                foreground=[('active', 'white'),
                            ('pressed', 'white')])

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

        # Agregar comandos directos en el menubar (sin submenús)
        menubar.add_command(label="Cursos", command=self.show_courses)
        menubar.add_command(label="Alumnos", command=self.show_students)
        menubar.add_command(label="Inscripciones", command=self.show_inscriptions)
        menubar.add_command(label="Pagos", command=self.show_payments)
        menubar.add_command(label="Historial", command=self.show_payment_history)
        menubar.add_command(label="Facturación", command=self.show_invoices)
        menubar.add_command(label="Cotizaciones", command=self.show_cotizaciones)
        menubar.add_command(label="Empresas", command=self.show_empresas)
        menubar.add_command(label="Alumnos Activos", command=self.show_current_students) 
        menubar.add_command(label="Tramitaciones", command=self.show_tramitaciones)
        menubar.add_command(label='Libros de Clase', command=self.show_carpetas)
        menubar.add_command(label='Tramitar', command=self.show_tramitar)
        menubar.add_command(label='Deudores', command=self.show_deudores)
              
    def _clear_main_content(self):
        """Limpia solo el contenido principal preservando el header"""
        try:
            # Preservar el header_frame y eliminar solo el contenido debajo
            for widget in self.main_frame.winfo_children():
                if widget != self.header_frame:
                    widget.destroy()
        except Exception as e:
            print(f"Error al limpiar contenido principal: {e}")
        
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
        
        # Inicializar variables para tracking de posición
        self.last_click_x = 0
        self.last_click_y = 0
        
        # Vincular eventos
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Button-1>", self._save_click_position)
        self.tree.bind("<Button-3>", self._save_click_position)

    def _update_title_label(self, text):
        """
        Actualiza el texto del título.
        
        Args:
            text (str): El texto a mostrar en el título
        """
        if self.title_label:
            self.title_label.config(text=text)

    def _save_click_position(self, event):
        """Guarda la posición del último click"""
        self.last_click_x = event.x_root
        self.last_click_y = event.y_root

    def _show_context_menu(self, event):
        """Muestra el menú contextual en la posición del clic"""
        try:
            # Identificar y seleccionar la fila
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
                self._save_click_position(event)
                self.context_menu.post(event.x_root, event.y_root)
            return "break"  # Prevenir el menú contextual por defecto
        except Exception as e:
            print(f"Error al mostrar menú contextual: {e}")

    def _copy_selected_cell(self):
        """Copia el contenido de la celda seleccionada"""
        try:
            selection = self.tree.selection()
            if not selection:
                return

            # Obtener la columna seleccionada
            column = self.tree.identify_column(self.last_click_x - self.tree.winfo_rootx())
            if not column:
                column = '#1'

            # Obtener el índice de la columna
            col_id = int(column.replace('#', '')) - 1
            
            # Obtener el valor de la celda
            cell_value = self.tree.item(selection[0])['values'][col_id]

            # Copiar al portapapeles
            self.root.clipboard_clear()
            self.root.clipboard_append(str(cell_value))
            
        except Exception as e:
            print(f"Error al copiar celda: {e}")

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
            
        except Exception as e:
            print(f"Error al copiar fila: {e}")

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
    #                       Alertas
    # =================================================================

    def payment_alert(self):
        """
        Muestra alerta de pagos que vencen hoy
        """
        current_date = datetime.now().strftime('%Y-%m-%d')
        alert_key = f"payment_alert_{current_date}"
        
        if alert_key in self.alerts_shown:
            return

        try:
            # Query para obtener pagos vencidos
            query = """
            SELECT DISTINCT
                a.nombre,
                a.apellido,
                a.rut,
                p.tipo_pago,
                p.id_pago,
                c.nro_cuota,
                c.valor_cuota,
                c.fecha_vencimiento
            FROM pagos p
            INNER JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
            INNER JOIN alumnos a ON i.id_alumno = a.rut
            LEFT JOIN cuotas c ON p.id_pago = c.id_pago
            WHERE 
                (c.fecha_vencimiento = CURDATE() AND c.estado_cuota = 'pendiente')
                OR
                (p.fecha_final = CURDATE() AND p.estado = 'pendiente')
            ORDER BY a.apellido, a.nombre;
            """

            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute(query)
            due_payments = cursor.fetchall()
            cursor.close()
            conn.close()

            if not due_payments:
                return

            # Crear y configurar la ventana
            alert_window = tk.Toplevel(self.root)
            alert_window.withdraw()
            alert_window.title("¡Alerta de Pagos!")
            alert_window.configure(bg='white')
            alert_window.resizable(False, False)

            # Configurar el estilo para el frame principal
            style = ttk.Style()
            style.configure('White.TFrame', background='white')
            
            # Configurar el estilo del botón
            style.configure('Red.TButton',
                        background='#dc3545',
                        foreground='white',
                        bordercolor='#dc3545',
                        lightcolor='#dc3545',
                        darkcolor='#dc3545',
                        focuscolor='#dc3545',
                        relief='flat',
                        padding=6)

            style.map('Red.TButton',
                    background=[('active', '#c82333'),
                            ('pressed', '#bd2130')],
                    foreground=[('active', 'white'),
                            ('pressed', 'white')])

            try:
                alert_window.iconbitmap(resource_path('assets/logo1.ico'))
            except Exception as e:
                print(f"Error al cargar ícono: {e}")

            # Frame principal con fondo blanco
            main_frame = tk.Frame(alert_window, bg='white')
            main_frame.pack(fill='both', expand=True)

            # Contenedor del mensaje con padding
            msg_container = tk.Frame(main_frame, bg='white')
            msg_container.pack(fill='both', expand=True, padx=20, pady=10)

            # Título con ícono de advertencia
            title_frame = tk.Frame(msg_container, bg='white')
            title_frame.pack(pady=(0, 15))
            
            # Ícono de advertencia
            warning_label = tk.Label(title_frame,
                                text="⚠️",
                                font=('Segoe UI', 16),
                                bg='white')
            warning_label.pack(side='left', padx=(0, 10))
            
            # Texto del título
            title_label = tk.Label(title_frame,
                                text=f"¡Hoy vencen {len(due_payments)} pagos!",
                                font=('Segoe UI', 12, 'bold'),
                                fg='#dc3545',
                                bg='white')
            title_label.pack(side='left')

            # Subtítulo
            subtitle_label = tk.Label(msg_container,
                                    text="Revisar pagos de:",
                                    font=('Segoe UI', 11, 'bold'),
                                    bg='white')
            subtitle_label.pack(pady=(0, 10))

            # Frame para la lista con scroll
            list_frame = tk.Frame(msg_container, bg='white')
            list_frame.pack(fill='both', expand=True, pady=(0, 10))

            # Canvas para el scroll con fondo blanco
            canvas = tk.Canvas(list_frame, bg='white', highlightthickness=0)
            scroll_frame = tk.Frame(canvas, bg='white')

            # Configurar el scroll
            def on_configure(event):
                canvas.configure(scrollregion=canvas.bbox('all'))
            scroll_frame.bind('<Configure>', on_configure)

            # Crear ventana en el canvas
            canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor='nw')

            # Ajustar el ancho del canvas al frame
            def on_canvas_configure(event):
                canvas.itemconfig(canvas_window, width=event.width)
            canvas.bind('<Configure>', on_canvas_configure)

            # Función para manejar el scroll con la rueda del mouse
            def on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")

            # Binding del mousewheel
            canvas.bind_all("<MouseWheel>", on_mousewheel)
            
            # Lista de pagos
            for payment in due_payments:
                nombre_completo = payment[0].lower() + " " + payment[1].lower()
                
                # Frame para cada pago con fondo blanco
                payment_frame = tk.Frame(scroll_frame, bg='white')
                payment_frame.pack(fill='x', pady=2)
                
                # Nombre del alumno
                tk.Label(payment_frame,
                        text=f"• {nombre_completo}",
                        font=('Segoe UI', 10),
                        bg='white',
                        anchor='w').pack(fill='x')
                
                # RUT
                tk.Label(payment_frame,
                        text=f"RUT: {payment[2]}",
                        font=('Segoe UI', 10),
                        bg='white',
                        fg='#666666',
                        anchor='w',
                        padx=20).pack(fill='x')
                
                # Información de la cuota
                monto = f"${payment[6]:,.0f}" if payment[6] else "Pendiente"
                tk.Label(payment_frame,
                        text=f"Cuota - {monto}",
                        font=('Segoe UI', 10),
                        bg='white',
                        fg='#dc3545',
                        anchor='w',
                        padx=20).pack(fill='x')

            # Empaquetar solo el canvas
            canvas.pack(side='left', fill='both', expand=True)

            # Frame para el botón con fondo blanco
            button_frame = tk.Frame(main_frame, bg='white')
            button_frame.pack(pady=(0, 10))

            def dismiss_alert():
                """Función para cerrar la alerta y recordar que fue vista"""
                self.alerts_shown.add(alert_key)
                alert_window.destroy()

            # Botón de aceptar
            accept_button = ttk.Button(button_frame,
                                    text="Aceptar",
                                    command=dismiss_alert,
                                    style='Red.TButton')
            accept_button.pack(ipadx=20, ipady=5)

            # Calcular las dimensiones basadas en el contenido
            alert_window.update_idletasks()
            width = max(400, main_frame.winfo_reqwidth() + 40)
            height = min(600, main_frame.winfo_reqheight() + 40)

            # Centrar la ventana
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2

            # Configurar geometría final
            alert_window.geometry(f'{width}x{height}+{x}+{y}')

            # Mostrar la ventana
            alert_window.grab_set()
            alert_window.deiconify()
            alert_window.focus_force()

        except Exception as e:
            print(f"Error en payment_alert: {e}")

    def tramite_alert(self):
        """
        Muestra alerta de trámites pendientes con más de 5 días hábiles
        """
        current_date = datetime.now().strftime('%Y-%m-%d')
        alert_key = f"tramite_alert_{current_date}"
        
        
        if alert_key in self.alerts_shown:
            return

        try:
            # Query para obtener trámites pendientes
            query = """
            SELECT DISTINCT
                a.nombre,
                a.apellido,
                a.rut,
                t.estado_general,
                t.fecha_ultimo_cambio,
                DATEDIFF(CURDATE(), t.fecha_ultimo_cambio) as dias_totales
            FROM tramitaciones t
            INNER JOIN inscripciones i ON t.id_inscripcion = i.id_inscripcion
            INNER JOIN alumnos a ON i.id_alumno = a.rut
            WHERE t.estado_general != 'completado'
            HAVING dias_totales >= 5;
            """




            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute(query)
            pending_tramites = cursor.fetchall()
            cursor.close()
            conn.close()

            

            if not pending_tramites:
                return

            # Crear y configurar la ventana
            alert_window = tk.Toplevel(self.root)
            alert_window.withdraw()
            alert_window.title("¡Alerta de Trámites!")
            alert_window.configure(bg='white')
            alert_window.resizable(False, False)

            # Configurar el estilo para el frame principal
            style = ttk.Style()
            style.configure('White.TFrame', background='white')
            
            # Configurar el estilo del botón
            style.configure('Red.TButton',
                        background='#dc3545',
                        foreground='white',
                        bordercolor='#dc3545',
                        lightcolor='#dc3545',
                        darkcolor='#dc3545',
                        focuscolor='#dc3545',
                        relief='flat',
                        padding=6)

            style.map('Red.TButton',
                    background=[('active', '#c82333'),
                            ('pressed', '#bd2130')],
                    foreground=[('active', 'white'),
                            ('pressed', 'white')])

            try:
                alert_window.iconbitmap(resource_path('assets/logo1.ico'))
            except Exception as e:
                print(f"Error al cargar ícono: {e}")

            # Frame principal con fondo blanco
            main_frame = tk.Frame(alert_window, bg='white')
            main_frame.pack(fill='both', expand=True)

            # Contenedor del mensaje con padding
            msg_container = tk.Frame(main_frame, bg='white')
            msg_container.pack(fill='both', expand=True, padx=20, pady=10)

            # Título con ícono de advertencia
            title_frame = tk.Frame(msg_container, bg='white')
            title_frame.pack(pady=(0, 15))
            
            warning_label = tk.Label(title_frame,
                                text="⚠️",
                                font=('Segoe UI', 16),
                                bg='white')
            warning_label.pack(side='left', padx=(0, 10))
            
            title_label = tk.Label(title_frame,
                                text=f"¡{len(pending_tramites)} trámites pendientes!",
                                font=('Segoe UI', 12, 'bold'),
                                fg='#dc3545',
                                bg='white')
            title_label.pack(side='left')

            subtitle_label = tk.Label(msg_container,
                                    text="Trámites sin actualizar por más de 5 días :",
                                    font=('Segoe UI', 11, 'bold'),
                                    bg='white')
            subtitle_label.pack(pady=(0, 10))

            # Frame para la lista con scroll
            list_frame = tk.Frame(msg_container, bg='white')
            list_frame.pack(fill='both', expand=True, pady=(0, 10))

            # Canvas para el scroll con fondo blanco
            canvas = tk.Canvas(list_frame, bg='white', highlightthickness=0)
            scroll_frame = tk.Frame(canvas, bg='white')

            def on_configure(event):
                canvas.configure(scrollregion=canvas.bbox('all'))
            scroll_frame.bind('<Configure>', on_configure)

            canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor='nw')

            def on_canvas_configure(event):
                canvas.itemconfig(canvas_window, width=event.width)
            canvas.bind('<Configure>', on_canvas_configure)

            def on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")

            canvas.bind_all("<MouseWheel>", on_mousewheel)
            
            # Lista de trámites
            for tramite in pending_tramites:
                nombre_completo = tramite[0].lower() + " " + tramite[1].lower()
                dias = tramite[5]
                
                tramite_frame = tk.Frame(scroll_frame, bg='white')
                tramite_frame.pack(fill='x', pady=2)
                
                tk.Label(tramite_frame,
                        text=f"• {nombre_completo}",
                        font=('Segoe UI', 10),
                        bg='white',
                        anchor='w').pack(fill='x')
                
                tk.Label(tramite_frame,
                        text=f"RUT: {tramite[2]}",
                        font=('Segoe UI', 10),
                        bg='white',
                        fg='#666666',
                        anchor='w',
                        padx=20).pack(fill='x')
                
                tk.Label(tramite_frame,
                        text=f"Estado: {tramite[3]} - {dias} días sin actualizar",
                        font=('Segoe UI', 10),
                        bg='white',
                        fg='#dc3545',
                        anchor='w',
                        padx=20).pack(fill='x')

            canvas.pack(side='left', fill='both', expand=True)

            # Frame para el botón con fondo blanco
            button_frame = tk.Frame(main_frame, bg='white')
            button_frame.pack(pady=(0, 10))

            def dismiss_alert():
                """Función para cerrar la alerta y recordar que fue vista"""
                self.alerts_shown.add(alert_key)
                alert_window.destroy()

            accept_button = ttk.Button(button_frame,
                                    text="Aceptar",
                                    command=dismiss_alert,
                                    style='Red.TButton')
            accept_button.pack(ipadx=20, ipady=5)

            # Calcular las dimensiones basadas en el contenido
            alert_window.update_idletasks()
            width = max(400, main_frame.winfo_reqwidth() + 40)
            height = min(600, main_frame.winfo_reqheight() + 40)

            # Centrar la ventana
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2

            alert_window.geometry(f'{width}x{height}+{x}+{y}')

            # Mostrar la ventana
            alert_window.grab_set()
            alert_window.deiconify()
            alert_window.focus_force()

        except Exception as e:
            print(f"Error en tramite_alert: {e}")

    # =================================================================
    #  INSCRIPCIONES (se muestran al iniciar)
    # =================================================================
    def show_inscriptions(self):
        try:
            # Limpiar el contenido principal
            self._clear_main_content()
            
            # Actualizar el título
            self._update_title_label("Listado de Inscripciones")
            
            # Crear frame principal
            content_frame = ttk.Frame(self.main_frame)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Frame para los botones
            button_frame = ttk.Frame(content_frame)
            button_frame.pack(fill=tk.X, pady=(0, 5))
            
            # Botones de acción
            ttk.Button(
                button_frame,
                text="Nueva Inscripción",
                command=self.enroll_student_window,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=2)

            ttk.Button(
                button_frame,
                text="Buscar Inscripciones",
                command=self.show_inscriptions_search,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=2)

            ttk.Button(
                button_frame,
                text="Modificar Inscripción",
                command=self.update_inscription_window,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=2)

            ttk.Button(
                button_frame,
                text="Eliminar Inscripción",
                command=self.delete_inscription_window,
                style='delete.TButton'
            ).pack(side=tk.LEFT, padx=2)

            ttk.Button(
                button_frame,
                text="Inscripción Masiva",
                command=self.show_bulk_enrollment,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=2)

            # Frame para el treeview y scrollbars
            tree_frame = ttk.Frame(content_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            # Configurar estilo del Treeview
            style = ttk.Style()
            style.configure("Treeview",
                background="#ffffff",
                foreground="black",
                rowheight=25,
                fieldbackground="#ffffff"
            )
            style.configure("Treeview.Heading",
                background="#e1e1e1",
                foreground="black",
                relief="flat"
            )
            style.map('Treeview',
                background=[('selected', '#0078D7')],
                foreground=[('selected', 'white')]
            )

            # Scrollbars
            vscroll = ttk.Scrollbar(tree_frame, orient="vertical")
            hscroll = ttk.Scrollbar(tree_frame, orient="horizontal")

            # Crear Treeview
            self.tree = ttk.Treeview(
                tree_frame,
                selectmode="extended",
                yscrollcommand=vscroll.set,
                xscrollcommand=hscroll.set
            )

            # Ubicar tree y scrollbars
            self.tree.grid(row=0, column=0, sticky="nsew")
            vscroll.grid(row=0, column=1, sticky="ns")
            hscroll.grid(row=1, column=0, sticky="ew")

            # Configurar scrollbars
            vscroll.configure(command=self.tree.yview)
            hscroll.configure(command=self.tree.xview)

            # Menú contextual
            self.context_menu = tk.Menu(tree_frame, tearoff=0)
            self.context_menu.add_command(label="Copiar celda", command=self._copy_selected_cell)
            self.context_menu.add_command(label="Copiar fila", command=self._copy_selected_row)

            # Track de posición del click
            self.last_click_x = 0
            self.last_click_y = 0

            # Bindings para el menú contextual
            self.tree.bind("<Button-3>", self._show_context_menu)
            self.tree.bind("<Button-1>", self._save_click_position)
            self.tree.bind("<ButtonRelease-3>", self._save_click_position)

            # Configurar tags para estados
            self.tree.tag_configure('pendiente', background='#FFF3CD')  # Amarillo claro
            self.tree.tag_configure('pagado', background='#D4EDDA')    # Verde claro
            self.tree.tag_configure('cancelado', background='#F8D7DA') # Rojo claro
            self.tree.tag_configure('sin_procesar', background='#E2E3E5') # Gris claro
            self.tree.tag_configure('oddrow', background='#f5f5f5')
            self.tree.tag_configure('evenrow', background='#ffffff')

            # Definir columnas
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

            # Obtener datos
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

            # Configurar Treeview
            self.tree.config(columns=columns, show="headings")
            
            # Definir anchos de columnas
            column_widths = {
                "ID": 50,
                "N_Acta": 60,
                "RUT": 90,
                "Nombre_Completo": 200,
                "ID_Curso": 90,
                "F_Inscripcion": 90,
                "F_Termino": 90,
                "Año": 50,
                "Empresa": 150,
                "Codigo_Sence": 100,
                "Folio": 60,
                "Estado_Pago": 90
            }

            # Aplicar configuraciones de columnas
            for column, header in zip(columns, headers):
                self.tree.heading(column, text=header, anchor=tk.CENTER)
                width = column_widths.get(column, 100)
                self.tree.column(column, width=width, minwidth=50, anchor=tk.CENTER)

            # Insertar datos en el Treeview
            for i, item in enumerate(formatted_data):
                estado = item[-1].lower() if item[-1] else 'sin_procesar'
                
                # Determinar el tag del estado
                if estado == 'pendiente':
                    estado_tag = 'pendiente'
                elif estado == 'pagado':
                    estado_tag = 'pagado'
                elif estado == 'cancelado':
                    estado_tag = 'cancelado'
                else:
                    estado_tag = 'sin_procesar'
                
                # Aplicar tags
                row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.tree.insert("", "end", values=item, tags=(estado_tag, row_tag))

            # Forzar actualización del Treeview
            self.tree.update_idletasks()

        except Exception as e:
            print(f"Error al mostrar inscripciones: {e}")
            import traceback
            traceback.print_exc()

    def show_inscriptions_search(self):
        # Ventana renombrada a "Buscar inscripciones"
        search_window = tk.Toplevel(self.root)
        search_window.title("Buscar inscripciones")
        search_window.configure(bg="#f0f5ff")
        search_window.grab_set()
        search_window.focus_force()

        # Centrar ventana
        width, height = 500, 350
        sw = search_window.winfo_screenwidth()
        sh = search_window.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        search_window.geometry(f"{width}x{height}+{x}+{y}")

        try:
            search_window.iconbitmap(resource_path('assets/logo1.ico'))
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")

        # Frame principal
        main_frame = tk.Frame(search_window, bg="#f0f5ff", padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text="Buscar inscripciones",
            font=("Helvetica", 16, "bold"),
            bg="#f0f5ff",
            fg="#022e86"
        )
        title_label.pack(pady=(0, 20))

        # Campo: RUT Alumno
        frame_rut = tk.Frame(main_frame, bg="#f0f5ff")
        frame_rut.pack(fill='x', pady=5)
        tk.Label(
            frame_rut,
            text="RUT Alumno:",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10),
            width=15,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        rut_entry = tk.Entry(frame_rut, font=("Helvetica", 10), relief="solid", bd=1, width=25)
        rut_entry.pack(side=tk.LEFT, fill='x', expand=True)

        # Campo: Nº Acta
        frame_acta = tk.Frame(main_frame, bg="#f0f5ff")
        frame_acta.pack(fill='x', pady=5)
        tk.Label(
            frame_acta,
            text="Nº Acta:",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10),
            width=15,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        acta_entry = tk.Entry(frame_acta, font=("Helvetica", 10), relief="solid", bd=1, width=25)
        acta_entry.pack(side=tk.LEFT, fill='x', expand=True)

        # Campo: Nombre Alumno
        frame_nombre = tk.Frame(main_frame, bg="#f0f5ff")
        frame_nombre.pack(fill='x', pady=5)
        tk.Label(
            frame_nombre,
            text="Nombre Alumno:",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10),
            width=15,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        nombre_entry = tk.Entry(frame_nombre, font=("Helvetica", 10), relief="solid", bd=1, width=25)
        nombre_entry.pack(side=tk.LEFT, fill='x', expand=True)

        # Campo: Fecha o Rango de Fecha (para F_Inscripcion)
        frame_fecha = tk.Frame(main_frame, bg="#f0f5ff")
        frame_fecha.pack(fill='x', pady=5)
        tk.Label(
            frame_fecha,
            text="Fecha (YYYY-MM-DD):",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10),
            width=15,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        fecha_inicio_entry = tk.Entry(frame_fecha, font=("Helvetica", 10), relief="solid", bd=1, width=10)
        fecha_inicio_entry.pack(side=tk.LEFT)
        tk.Label(
            frame_fecha,
            text="a",
            bg="#f0f5ff",
            fg="#022e86",
            font=("Helvetica", 10)
        ).pack(side=tk.LEFT, padx=5)
        fecha_fin_entry = tk.Entry(frame_fecha, font=("Helvetica", 10), relief="solid", bd=1, width=10)
        fecha_fin_entry.pack(side=tk.LEFT)

        # Función de búsqueda
        def search():
            rut = rut_entry.get().strip()
            act_number = acta_entry.get().strip()
            nombre = nombre_entry.get().strip()
            fecha_inicio = fecha_inicio_entry.get().strip()
            fecha_fin = fecha_fin_entry.get().strip()

            # Se requiere al menos un criterio de búsqueda
            if not (rut or act_number or nombre or fecha_inicio):
                messagebox.showwarning(
                    "Error",
                    "Ingrese al menos un criterio de búsqueda (RUT, Nº Acta, Nombre o Fecha).",
                    parent=search_window
                )
                return

            # Llamamos a la consulta con los parámetros no vacíos
            inscripciones = fetch_inscriptions_filtered(
                rut=rut if rut else None,
                act_number=act_number if act_number else None,
                nombre=nombre if nombre else None,
                fecha_inicio=fecha_inicio if fecha_inicio else None,
                fecha_fin=fecha_fin if fecha_fin else None
            )

            # Se actualiza el treeview principal con TODA la información de la inscripción
            if inscripciones:
                # Se espera que _populate_tree reciba:
                # - Una tupla de claves (o índices) correspondientes a las columnas de la consulta.
                # - Una tupla de títulos para las columnas.
                # - Los datos (lista de tuplas).
                self._populate_tree(
                    (
                        "ID",
                        "N_Acta",
                        "RUT",
                        "Nombre_Completo",
                        "ID_Curso",
                        "F_Inscripcion",
                        "F_Termino",
                        "Año",
                        "Empresa",
                        "Codigo_Sence",
                        "Folio",
                        "Estado_Pago"
                    ),
                    (
                        "ID",
                        "N° Acta",
                        "RUT",
                        "Alumno",
                        "ID Curso",
                        "F. Inscripción",
                        "F. Término",
                        "Año",
                        "Empresa",
                        "Código Sence",
                        "Folio",
                        "Estado Pago"
                    ),
                    inscripciones
                )
                self._update_title_label("Inscripciones filtradas")
                search_window.destroy()
            else:
                messagebox.showinfo(
                    "Información",
                    "No se encontraron inscripciones con los criterios ingresados.",
                    parent=search_window
                )

        # Frame para botones
        button_frame = tk.Frame(main_frame, bg="#f0f5ff")
        button_frame.pack(pady=20)
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
            enroll_window.iconbitmap(resource_path('assets/logo1.ico'))
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
            # Verificar si el alumno está en la lista de deudores
            if is_student_debtor(rut):
                messagebox.showerror(
                    "Error",
                    "El alumno está en la lista de deudores y no puede matricularse.",
                    parent=enroll_window
                )
                return
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
                
                # Si es curso de formación, verificar/crear carpeta de libros
                conn = connect_db()
                cursor = conn.cursor()
                
                cursor.execute("SELECT tipo_curso FROM cursos WHERE id_curso = %s", (id_curso,))
                tipo_curso = cursor.fetchone()
                
                if tipo_curso and tipo_curso[0] == 'FORMACION':
                    success, result = create_carpeta_libros(
                        numero_acta=numero_acta,
                        id_curso=id_curso,
                        fecha_inicio=fecha_inscripcion
                    )
                    if not success:
                        messagebox.showerror(
                            "Error",
                            f"No se pudo crear la carpeta de libros:\n{result}",
                            parent=enroll_window
                        )
                        cursor.close()
                        conn.close()
                        return
                
                cursor.close()
                conn.close()

                # Ahora, proceder a inscribir al alumno
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
            delete_window.iconbitmap(resource_path('assets/logo1.ico'))
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
        window.configure(bg="#f0f0f0")
        window.grab_set()
        window.focus_force()

        # Intentar cargar el ícono
        try:
            if os.path.exists('assets/logo1.ico'):
                window.iconbitmap(resource_path('assets/logo1.ico'))
            else:
                print("Logo no encontrado en assets/logo1.ico")
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")

        # Tamaño inicial
        width, height = 600, 400
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

        # Frame principal
        main_frame = ttk.Frame(window, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Frame de búsqueda
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(
            search_frame,
            text="ID Inscripción:",
            font=('Helvetica', 9)
        ).pack(side='left', padx=5)

        id_inscripcion_entry = ttk.Entry(search_frame, width=15)
        id_inscripcion_entry.pack(side='left', padx=5)

        # Frame para campos
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill='both', expand=True, pady=5)

        # Configurar grid
        fields_frame.grid_columnconfigure(1, weight=1)
        fields_frame.grid_columnconfigure(3, weight=1)

        def create_field(label, row, column, to_upper=True):
            ttk.Label(
                fields_frame,
                text=label,
                font=('Helvetica', 9)
            ).grid(row=row, column=column*2, sticky='e', padx=5, pady=3)
            
            entry = ttk.Entry(fields_frame, width=25)
            
            if to_upper:
                def to_uppercase(*args):
                    value = entry.get()
                    uppercase_value = value.upper()
                    if value != uppercase_value:
                        entry.delete(0, tk.END)
                        entry.insert(0, uppercase_value)
                
                entry.bind('<KeyRelease>', to_uppercase)
            
            entry.grid(row=row, column=column*2 + 1, sticky='w', padx=5, pady=3)
            return entry

        # Crear campos
        entries = {
            'rut': create_field("RUT Alumno:", 0, 0),
            'fecha_term': create_field("Fecha Término (YYYY-MM-DD):", 0, 1, to_upper=False),
            'curso': create_field("ID Curso:", 1, 0),
            'empresa': create_field("ID Empresa:", 1, 1),
            'acta': create_field("Número Acta:", 2, 0),
            'sence': create_field("Orden SENCE:", 2, 1),
            'fecha_insc': create_field("Fecha Inscripción (YYYY-MM-DD):", 3, 0, to_upper=False),
            'folio': create_field("ID Folio:", 3, 1),
            'anio': create_field("Año:", 4, 0, to_upper=False)
        }

        # Método de llegada
        ttk.Label(
            fields_frame,
            text="Método de Llegada:",
            font=('Helvetica', 9)
        ).grid(row=4, column=2, sticky='e', padx=5, pady=3)

        metodo_combo = ttk.Combobox(
            fields_frame,
            values=["PARTICULAR", "EMPRESA"],
            state="readonly",
            width=22
        )
        metodo_combo.grid(row=4, column=3, sticky='w', padx=5, pady=3)
        metodo_combo.set("PARTICULAR")

        def validate_date(date_str):
            if not date_str:
                return True
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                return True
            except ValueError:
                return False

        def load_inscription_data():
            id_inscripcion = id_inscripcion_entry.get().strip()
            if not id_inscripcion:
                messagebox.showwarning("Error", "Ingrese el ID de inscripción", parent=window)
                return

            try:
                inscription = fetch_inscription_by_id(id_inscripcion)
                if not inscription:
                    messagebox.showerror("Error", f"No se encontró inscripción con ID {id_inscripcion}", parent=window)
                    return

                # Limpiar y llenar campos
                for entry in entries.values():
                    entry.delete(0, tk.END)

                entries['rut'].insert(0, inscription['id_alumno'] or '')
                entries['curso'].insert(0, inscription['id_curso'] or '')
                entries['acta'].insert(0, inscription['numero_acta'] or '')
                if inscription['fecha_inscripcion']:
                    entries['fecha_insc'].insert(0, inscription['fecha_inscripcion'].strftime('%Y-%m-%d'))
                if inscription['fecha_termino_condicional']:
                    entries['fecha_term'].insert(0, inscription['fecha_termino_condicional'].strftime('%Y-%m-%d'))
                entries['anio'].insert(0, str(inscription['anio_inscripcion']) if inscription['anio_inscripcion'] else '')
                entries['empresa'].insert(0, inscription['id_empresa'] or '')
                entries['sence'].insert(0, str(inscription['ordenSence']) if inscription['ordenSence'] else '')
                entries['folio'].insert(0, str(inscription['idfolio']) if inscription['idfolio'] else '')
                
                metodo = inscription['metodo_llegada']
                metodo_combo.set(metodo.upper() if metodo else "PARTICULAR")
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar datos: {str(e)}", parent=window)

        def save_changes():
            id_inscripcion = id_inscripcion_entry.get().strip()
            if not id_inscripcion:
                messagebox.showwarning("Error", "Ingrese el ID de inscripción", parent=window)
                return

            # Validar fechas
            for field_name in ['fecha_insc', 'fecha_term']:
                date_value = entries[field_name].get().strip()
                if date_value and not validate_date(date_value):
                    messagebox.showerror("Error", f"Formato de fecha inválido. Use YYYY-MM-DD", parent=window)
                    return

            # Si hay empresa, verificar/crear primero
            empresa_id = entries['empresa'].get().strip()
            if empresa_id:
                success, result = verify_and_create_empresa(empresa_id)
                if not success:
                    messagebox.showerror("Error", f"Error al procesar empresa: {result}", parent=window)
                    return
                empresa_id = result

            update_data = {
                'id_alumno': entries['rut'].get().strip() or None,
                'id_curso': entries['curso'].get().strip() or None,
                'numero_acta': entries['acta'].get().strip() or None,
                'fecha_inscripcion': entries['fecha_insc'].get().strip() or None,
                'fecha_termino_condicional': entries['fecha_term'].get().strip() or None,
                'anio_inscripcion': entries['anio'].get().strip() or None,
                'metodo_llegada': metodo_combo.get().lower() if metodo_combo.get() else None,
                'id_empresa': empresa_id or None,
                'ordenSence': entries['sence'].get().strip() or None,
                'idfolio': entries['folio'].get().strip() or None
            }

            try:
                success, message = update_inscription(id_inscripcion, **update_data)
                if success:
                    messagebox.showinfo("Éxito", message, parent=window)
                    window.destroy()
                    self.show_inscriptions()
                else:
                    messagebox.showerror("Error", message, parent=window)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {str(e)}", parent=window)

        # Botones
        ttk.Button(
            search_frame,
            text="Buscar",
            command=load_inscription_data,
            style='Action.TButton'
        ).pack(side='left', padx=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(
            button_frame,
            text="Cancelar",
            command=window.destroy,
            style='Secondary.TButton'
        ).pack(side='right', padx=5)

        ttk.Button(
            button_frame,
            text="Guardar Cambios",
            command=save_changes,
            style='Action.TButton'
        ).pack(side='right', padx=5)

        # Ajustar tamaño de la ventana al contenido
        window.update_idletasks()
        window.geometry("")
        
        # Hacer la ventana no redimensionable
        window.resizable(False, False)
        
    def show_bulk_enrollment(self):
        from gui.bulk_enrollment import BulkEnrollment
        bulk_window = BulkEnrollment(self.root)
    # ---------------------------------------------------
    #                 CURSOS
    # ---------------------------------------------------

    def show_courses(self):
        try:
            # Limpiar solo el contenido principal
            self._clear_main_content()
            
            # Actualizar el título
            self._update_title_label("Listado de Cursos")
            
            # Crear frame para el contenido principal
            content_frame = ttk.Frame(self.main_frame)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Frame para botones
            button_frame = ttk.Frame(content_frame)
            button_frame.pack(fill=tk.X, pady=(0, 5))
            
            # Botones de acción
            ttk.Button(
                button_frame,
                text="Nuevo Curso",
                command=self.add_course_window,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=2)

            ttk.Button(
                button_frame,
                text="Modificar Curso",
                command=self.edit_course_window,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=2)

            ttk.Button(
                button_frame,
                text="Eliminar Curso",
                command=self.delete_course_window,
                style='delete.TButton'
            ).pack(side=tk.LEFT, padx=2)
            
            # Frame para el treeview y scrollbars
            tree_frame = ttk.Frame(content_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            # Configurar estilo para aumentar la altura de las filas
            style = ttk.Style()
            # Puedes cambiar "Custom.Course.Treeview" a cualquier nombre que desees
            style.configure("Custom.Course.Treeview",
                            rowheight=30,  # Ajusta este valor según tus necesidades
                            font=('Helvetica', 9))  # Opcional: Ajusta el tamaño de la fuente
            
            # Scrollbars
            vscroll = ttk.Scrollbar(tree_frame, orient="vertical")
            hscroll = ttk.Scrollbar(tree_frame, orient="horizontal")

            # Crear Treeview con el estilo personalizado
            self.tree = ttk.Treeview(
                tree_frame,
                style="Custom.Course.Treeview",  # Aplica el estilo personalizado
                selectmode="extended",
                yscrollcommand=vscroll.set,
                xscrollcommand=hscroll.set
            )

            # Configurar grid
            self.tree.grid(row=0, column=0, sticky="nsew")
            vscroll.grid(row=0, column=1, sticky="ns")
            hscroll.grid(row=1, column=0, sticky="ew")

            # Configurar scrollbars
            vscroll.configure(command=self.tree.yview)
            hscroll.configure(command=self.tree.xview)

            # Configurar menú contextual
            self.context_menu = tk.Menu(tree_frame, tearoff=0)
            self.context_menu.add_command(label="Copiar celda", command=self._copy_selected_cell)
            self.context_menu.add_command(label="Copiar fila", command=self._copy_selected_row)

            # Variables para tracking
            self.last_click_x = 0
            self.last_click_y = 0

            # Bindings para el menú contextual
            self.tree.bind("<Button-3>", self._show_context_menu)
            self.tree.bind("<Button-1>", self._save_click_position)
            self.tree.bind("<ButtonRelease-3>", self._save_click_position)

            # Configurar tags
            self.tree.tag_configure('oddrow', background='#f5f5f5')
            self.tree.tag_configure('evenrow', background='#ffffff')
            
            # Definir columnas y headers
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

            # Obtener datos
            courses = fetch_courses()
            
            # Configurar el tree
            self.tree.config(columns=columns, show="headings")
            
            # Configurar columnas con sus anchos
            column_widths = {
                "id_curso": (80, False),
                "nombre_curso": (250, True),
                "modalidad": (100, False),
                "codigo_sence": (120, False),
                "codigo_elearning": (120, False),
                "horas_cronologicas": (100, False),
                "horas_pedagogicas": (100, False),
                "valor": (120, False),
                "duracionDias": (120, False),
                "tipo_curso": (150, False),
                "resolucion": (150, False),
                "fecha_resolucion": (120, False),
                "fecha_vigencia": (120, False),
                "valor_alumno_sence": (150, False)
            }

            # Aplicar configuración de columnas
            for column, header in zip(columns, headers):
                self.tree.heading(column, text=header, anchor=tk.CENTER)
                width, stretch = column_widths.get(column, (100, False))
                self.tree.column(column, width=width, stretch=stretch, anchor=tk.CENTER)
                
            # Insertar datos con colores alternados
            for i, course in enumerate(courses):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.tree.insert("", "end", values=course, tags=(tag,))

        except Exception as e:
            print(f"Error al mostrar cursos: {e}")
            traceback.print_exc()
    
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
            window.iconbitmap(resource_path('assets/logo1.ico'))
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
            window.iconbitmap(resource_path('assets/logo1.ico'))
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
            delete_window.iconbitmap(resource_path('assets/logo1.ico'))
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
        try:
            # Limpiar solo el contenido principal
            self._clear_main_content()
            
            # Actualizar el título
            self._update_title_label("Listado de Alumnos")
            
            # Crear frame para el contenido principal
            content_frame = ttk.Frame(self.main_frame)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Frame para botones
            button_frame = ttk.Frame(content_frame)
            button_frame.pack(fill=tk.X, pady=(0, 5))
            
            # Botones de acción
            ttk.Button(
                button_frame,
                text="Nuevo Alumno",
                command=self.add_student_window,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=2)

            ttk.Button(
                button_frame,
                text="Modificar Alumno",
                command=self.edit_student_window,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=2)

            ttk.Button(
                button_frame,
                text="Buscar Alumno",
                command=self.search_student_window,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=2)

            ttk.Button(
                button_frame,
                text="Eliminar Alumno",
                command=self.delete_student_window,
                style='delete.TButton'
            ).pack(side=tk.LEFT, padx=2)
            
            # Frame para el treeview y scrollbars
            tree_frame = ttk.Frame(content_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            # Scrollbars
            vscroll = ttk.Scrollbar(tree_frame, orient="vertical")
            hscroll = ttk.Scrollbar(tree_frame, orient="horizontal")

            # Crear Treeview
            self.tree = ttk.Treeview(
                tree_frame,
                selectmode="extended",
                yscrollcommand=vscroll.set,
                xscrollcommand=hscroll.set
            )

            # Configurar grid
            self.tree.grid(row=0, column=0, sticky="nsew")
            vscroll.grid(row=0, column=1, sticky="ns")
            hscroll.grid(row=1, column=0, sticky="ew")

            # Configurar scrollbars
            vscroll.configure(command=self.tree.yview)
            hscroll.configure(command=self.tree.xview)

            # Configurar menú contextual
            self.context_menu = tk.Menu(tree_frame, tearoff=0)
            self.context_menu.add_command(label="Copiar celda", command=self._copy_selected_cell)
            self.context_menu.add_command(label="Copiar fila", command=self._copy_selected_row)

            # Variables para tracking
            self.last_click_x = 0
            self.last_click_y = 0

            # Bindings para el menú contextual
            self.tree.bind("<Button-3>", self._show_context_menu)
            self.tree.bind("<Button-1>", self._save_click_position)
            self.tree.bind("<ButtonRelease-3>", self._save_click_position)

            # Configurar tags
            self.tree.tag_configure('oddrow', background='#f5f5f5')
            self.tree.tag_configure('evenrow', background='#ffffff')
            
            # Definir columnas y headers
            columns = (
                "rut", 
                "nombre", 
                "apellido", 
                "correo", 
                "telefono",
                "profesion", 
                "direccion", 
                "ciudad", 
                "comuna"
            )
            
            headers = (
                "RUT", 
                "Nombre", 
                "Apellido", 
                "Correo", 
                "Teléfono",
                "Profesión", 
                "Dirección", 
                "Ciudad", 
                "Comuna"
            )

            # Obtener datos
            students = fetch_all_students()
            
            # Configurar el tree
            self.tree.config(columns=columns, show="headings")
            
            # Configurar columnas con sus anchos optimizados
            column_widths = {
                "rut": (100, False),
                "nombre": (150, True),
                "apellido": (150, True),
                "correo": (200, True),
                "telefono": (100, False),
                "profesion": (150, True),
                "direccion": (200, True),
                "ciudad": (120, False),
                "comuna": (120, False)
            }

            # Aplicar configuración de columnas
            for column, header in zip(columns, headers):
                self.tree.heading(column, text=header, anchor=tk.CENTER)
                width, stretch = column_widths.get(column, (100, False))
                self.tree.column(column, width=width, stretch=stretch, anchor=tk.CENTER)
                
            # Insertar datos con colores alternados
            for i, student in enumerate(students):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.tree.insert("", "end", values=student, tags=(tag,))

        except Exception as e:
            print(f"Error al mostrar alumnos: {e}")
            import traceback
            traceback.print_exc()  

    def add_student_window(self):
            window = tk.Toplevel(self.root)
            window.title("Añadir Alumno")
            window.geometry("800x450")  # Más ancho, menos alto
            window.configure(bg="#f0f5ff")
            window.grab_set()
            window.focus_force()

            try:
                window.iconbitmap(resource_path('assets/logo1.ico'))
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
            window.iconbitmap(resource_path('assets/logo1.ico'))
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
            delete_window.iconbitmap(resource_path('assets/logo1.ico'))
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
                window.iconbitmap(resource_path('assets/logo1.ico'))
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
    #                  PAGOS e Historial 
    # ---------------------------------------------------
    def _get_estado_pago_tag(self, estado):
        """
        Determina el tag del Treeview para colorear según el estado del pago.
        """
        estado = estado.upper()
        if estado == 'PENDIENTE':
            return 'pendiente'
        elif estado == 'PAGADO':
            return 'pagado'
        elif estado == 'CANCELADO':
            return 'cancelado'
        else:
            return 'sin_procesar'

    def show_payments(self):
            try:
                # Limpiar solo el contenido principal
                self._clear_main_content()
                # Mostrar alerta de pagos vencidos
                self.payment_alert()
                
                # Actualizar el título
                self._update_title_label("Listado de Pagos")
                
                # Crear frame para el contenido principal
                content_frame = ttk.Frame(self.main_frame)
                content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

                # Frame para botones
                button_frame = ttk.Frame(content_frame)
                button_frame.pack(fill=tk.X, pady=(0, 5))
                
                # Botones de acción
                ttk.Button(
                    button_frame,
                    text="Nuevo Pago",
                    command=self.add_payment_window,
                    style='Action.TButton'
                ).pack(side=tk.LEFT, padx=5)

                ttk.Button(
                    button_frame,
                    text="Pagos Pendientes",
                    command=self.show_pending_payments,
                    style='Action.TButton'
                ).pack(side=tk.LEFT, padx=5)

                ttk.Button(
                    button_frame,
                    text="Buscar por Inscripción",
                    command=self.show_payments_by_inscription,
                    style='Action.TButton'
                ).pack(side=tk.LEFT, padx=5)

                ttk.Button(
                    button_frame,
                    text="Pago Contado",
                    command=self.update_payment_status_window,
                    style='Action.TButton'
                ).pack(side=tk.LEFT, padx=5)

                ttk.Button(
                    button_frame,
                    text="Pago Cuotas",
                    command=self.manage_cuotas_pagare_window,
                    style='Action.TButton'
                ).pack(side=tk.LEFT, padx=5)

                # Nuevo botón de Orden de Compra
                ttk.Button(
                    button_frame,
                    text="Generar Orden",
                    command=self.open_orden_compra_window,
                    style='Action.TButton'
                ).pack(side=tk.LEFT, padx=5)
                
                # Frame para el treeview y scrollbars
                tree_frame = ttk.Frame(content_frame)
                tree_frame.pack(fill=tk.BOTH, expand=True)
                tree_frame.grid_rowconfigure(0, weight=1)
                tree_frame.grid_columnconfigure(0, weight=1)

                # Configurar estilo del Treeview
                style = ttk.Style()
                style.configure("Treeview",
                    background="#ffffff",
                    foreground="black",
                    rowheight=35,
                    fieldbackground="#ffffff"
                )
                
                style.configure("Treeview.Heading",
                    background="#e1e1e1",
                    foreground="black",
                    relief="flat"
                )
                style.map('Treeview',
                    background=[('selected', '#0078D7')],
                    foreground=[('selected', 'white')]
                )

                # Scrollbars
                vscroll = ttk.Scrollbar(tree_frame, orient="vertical")
                hscroll = ttk.Scrollbar(tree_frame, orient="horizontal")

                # Crear Treeview
                self.tree = ttk.Treeview(
                    tree_frame,
                    selectmode="extended",
                    yscrollcommand=vscroll.set,
                    xscrollcommand=hscroll.set
                )

                # Configurar grid
                self.tree.grid(row=0, column=0, sticky="nsew")
                vscroll.grid(row=0, column=1, sticky="ns")
                hscroll.grid(row=1, column=0, sticky="ew")

                # Configurar scrollbars
                vscroll.configure(command=self.tree.yview)
                hscroll.configure(command=self.tree.xview)

                # Configurar menú contextual
                self.context_menu = tk.Menu(tree_frame, tearoff=0)
                self.context_menu.add_command(label="Copiar celda", command=self._copy_selected_cell)
                self.context_menu.add_command(label="Copiar fila", command=self._copy_selected_row)

                # Variables para tracking
                self.last_click_x = 0
                self.last_click_y = 0

                # Bindings para el menú contextual
                self.tree.bind("<Button-3>", self._show_context_menu)
                self.tree.bind("<Button-1>", self._save_click_position)
                self.tree.bind("<ButtonRelease-3>", self._save_click_position)

                # Configurar tags para estados
                self.tree.tag_configure('pendiente', background='#FFF3CD')  # Amarillo claro
                self.tree.tag_configure('pagado', background='#D4EDDA')    # Verde claro
                self.tree.tag_configure('cancelado', background='#F8D7DA') # Rojo claro
                self.tree.tag_configure('sin_procesar', background='#E2E3E5') # Gris claro
                self.tree.tag_configure('oddrow', background='#f5f5f5')
                self.tree.tag_configure('evenrow', background='#ffffff')
                                    
                # Definir las columnas y headers
                columns = (
                    "ID", "Inscripcion", "Alumno", "Curso", "N_Acta",
                    "Tipo_Pago", "Modalidad_Pago", "Cuotas", "Valor_Total",
                    "Estado", "Estado_Orden", "N_Orden", "F_Inscripcion", "F_Final"
                )
                        
                headers = (
                    "ID", "Inscripción", "Alumno", "Curso", "N° Acta",
                    "Tipo", "Modalidad", "Cuotas", "Valor Total",
                    "Estado", "Estado Orden", "N° Orden", "F. Inscripción", "F. Final"
                )

                # Obtener datos y formatear
                data_raw = fetch_payments()
                formatted_data = []
                        
                if data_raw:
                    for payment in data_raw:
                        fecha_inscripcion = payment[4].strftime('%Y-%m-%d') if payment[4] else ''
                        fecha_final = payment[5].strftime('%Y-%m-%d') if payment[5] else ''
                        valor_total = f"${payment[7]:,.0f}" if payment[7] else ''

                        row = [
                            payment[0],                    # ID
                            payment[1],                    # Inscripción
                            payment[10],                   # Alumno
                            payment[11],                   # Curso
                            payment[9],                    # N° Acta
                            payment[2].capitalize(),       # Tipo
                            payment[3].capitalize(),       # Modalidad
                            f"{payment[12]}/{payment[6]}", # Cuotas pagadas / total
                            valor_total,                   # Valor
                            payment[8].upper(),            # Estado
                            payment[13] if payment[13] else 'SIN EMITIR',  # Estado Orden
                            payment[14] if payment[14] else '',            # N° Orden
                            fecha_inscripcion,             # Fecha Inscripción
                            fecha_final                    # Fecha Final
                        ]
                        formatted_data.append(row)
                
                # Configurar el tree
                self.tree.config(columns=columns, show="headings")
                    
                # Configurar columnas con anchos
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
                    "Estado_Orden": 90,
                    "N_Orden": 90,
                    "F_Inscripcion": 100,
                    "F_Final": 100
                }

                # Aplicar configuración de columnas
                for column, header in zip(columns, headers):
                    self.tree.heading(column, text=header, anchor=tk.CENTER)
                    width = column_widths.get(column, 100)
                    self.tree.column(column, width=width, minwidth=50, anchor=tk.CENTER)
                    
                # Insertar datos con colores de estado
                for i, item in enumerate(formatted_data):
                    estado = item[9].upper()  # Estado es la columna 9
                    estado_tag = self._get_estado_pago_tag(estado)
                    row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                    self.tree.insert("", "end", values=item, tags=(estado_tag, row_tag))

                # Forzar actualización del Treeview
                self.tree.update_idletasks()

            except Exception as e:
                print(f"Error al mostrar pagos: {e}")
                import traceback
                traceback.print_exc()

 
    def open_orden_compra_window(self):
        """Abre la ventana de generación de órdenes de compra"""
        try:
            # Crear ventana top level
            top = tk.Toplevel(self.root)
            
            # Hacer la ventana modal
            top.transient(self.root)
            top.grab_set()
            
            # Configurar el título
            top.title("Generación de Orden de Compra")
            
            # Obtener dimensiones de la pantalla
            screen_width = top.winfo_screenwidth()
            screen_height = top.winfo_screenheight()
            
            # Definir un tamaño fijo para la ventana
            window_width = 1024  # Ancho fijo
            window_height = 700  # Alto fijo
            
            # Calcular posición para centrar la ventana
            x_pos = (screen_width - window_width) // 2
            y_pos = (screen_height - window_height) // 2
            
            # Configurar geometría con tamaño fijo
            top.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos-30}")
            
            # Deshabilitar la maximización
            top.resizable(True, True)
            
            # Establecer conexión
            conn = connect_db()
            
            # Crear la ventana de orden de compra
            orden_window = OrdenCompraWindow(
                parent=top,
                connection=conn
            )
            
            # Vincular el evento de cierre
            top.protocol("WM_DELETE_WINDOW", lambda: self._close_orden_window(top, conn))
            
            # Esperar hasta que se cierre la ventana
            self.root.wait_window(top)
            
            # Refrescar la vista de pagos
            self.show_payments()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir ventana de órdenes: {str(e)}")
            print(f"Error en open_orden_compra_window: {e}")
            import traceback
            traceback.print_exc()

    def _close_orden_window(self, window, conn=None):
        """Maneja el cierre de la ventana de órdenes"""
        try:
            if conn:
                conn.close()
            window.grab_release()
            window.destroy()
        except Exception as e:
            print(f"Error al cerrar ventana de órdenes: {e}")
            window.destroy()
 
    def generar_recibo_ingreso(self):
        """Genera un recibo de ingreso basado en la selección actual del historial usando docxtpl."""
        # Obtener el primer elemento seleccionado del Treeview
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "Debe seleccionar un pago para generar el recibo.")
            return

        item = self.tree.item(selected_items[0])
        values = item['values']

        # Extraer los valores necesarios
        tipo_pago = values[2]
        if tipo_pago.upper() != "PAGARE":
            messagebox.showwarning("Advertencia", "Solo se pueden generar recibos para pagos de tipo 'PAGARE'.")
            return

        num_ingreso = values[6]       # Número de ingreso
        nombre_alumno = values[4]       # Nombre del alumno

        # Permitir al usuario elegir dónde guardar el archivo
        save_path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Documentos Word", "*.docx")],
            initialfile=f"Recibo_{num_ingreso}.docx",
            title="Guardar Recibo de Ingreso"
        )

        if not save_path:
            return  # El usuario canceló la selección

        # Ruta de la plantilla (asegúrate de que exista y tenga los placeholders correctos)
        template_path = "formatos/recibo_template.docx"

        try:
            # Cargar la plantilla usando DocxTemplate
            doc = DocxTemplate(template_path)


            # Define el contexto para reemplazar los placeholders.
            # Asegúrate de que los nombres de las claves coincidan con los marcadores en el template.
            context = {
                'num_ing': num_ingreso,
                'nombre_completo': nombre_alumno,
            }

            # Renderiza la plantilla con el contexto
            doc.render(context)

            # Guarda el documento en la ubicación seleccionada
            doc.save(save_path)

            messagebox.showinfo("Éxito", f"Recibo guardado en: {save_path}")
            os.startfile(save_path)  # Abre el archivo generado

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el recibo: {e}")
            traceback.print_exc()

    def show_payment_history(self):
        """Muestra el historial de pagos en el frame principal con scrollbars correctamente configuradas."""
        try:
            # Limpiar el contenido principal (método propio)
            self._clear_main_content()

            # Actualizar el título del frame
            self._update_title_label("Historial de Pagos")

            # Crear frame para el contenido principal
            content_frame = ttk.Frame(self.main_frame)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Frame de filtros en la parte superior
            filter_frame = ttk.LabelFrame(content_frame, text="Filtros de Búsqueda", padding="5")
            filter_frame.pack(fill=tk.X, padx=10, pady=5)

            # Variables para filtros
            mes_var = tk.StringVar()
            fecha_var = tk.StringVar()
            rut_var = tk.StringVar()

            # Frame para los campos de filtro
            fields_frame = ttk.Frame(filter_frame)
            fields_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)

            # Campos de búsqueda
            ttk.Label(fields_frame, text="Mes (MM/YYYY):").grid(row=0, column=0, padx=(0,10), pady=5, sticky='e')
            ttk.Entry(fields_frame, textvariable=mes_var, width=15).grid(row=0, column=1, padx=5, pady=5, sticky='w')

            ttk.Label(fields_frame, text="Fecha (DD/MM/YYYY):").grid(row=0, column=2, padx=(20,10), pady=5, sticky='e')
            ttk.Entry(fields_frame, textvariable=fecha_var, width=15).grid(row=0, column=3, padx=5, pady=5, sticky='w')

            ttk.Label(fields_frame, text="RUT:").grid(row=0, column=4, padx=(20,10), pady=5, sticky='e')
            ttk.Entry(fields_frame, textvariable=rut_var, width=15).grid(row=0, column=5, padx=5, pady=5, sticky='w')

            ttk.Button(fields_frame, text="Buscar", 
                    command=lambda: self.load_history_data(mes_var, fecha_var, rut_var),
                    style='Action.TButton').grid(row=0, column=6, padx=20, pady=5)

            # Botón para generar recibo: se corrige el command para llamar a generar_recibo_ingreso
            ttk.Button(fields_frame, text="Generar Recibo",
                    command=self.generar_recibo_ingreso,
                    style='Action.TButton').grid(row=0, column=7, padx=20, pady=5)

            # Crear frame para el Treeview y las scrollbars
            tree_frame = ttk.Frame(content_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)

            # Configurar columnas para el historial de pagos
            columns = ('id_historial', 'fecha', 'tipo_pago', 'rut', 'alumno', 'monto', 'num_ingreso', 'detalle')
            self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

            # Configurar encabezados
            self.tree.heading('id_historial', text='ID')
            self.tree.heading('fecha', text='Fecha')
            self.tree.heading('tipo_pago', text='Tipo Pago')
            self.tree.heading('rut', text='RUT')
            self.tree.heading('alumno', text='Alumno')
            self.tree.heading('monto', text='Valor')
            self.tree.heading('num_ingreso', text='N° Ingreso')
            self.tree.heading('detalle', text='Detalle')

            # Configurar anchos de columna
            self.tree.column('id_historial', width=50, anchor='center')
            self.tree.column('fecha', width=150, anchor='center')
            self.tree.column('tipo_pago', width=100, anchor='center')
            self.tree.column('rut', width=120, anchor='center')
            self.tree.column('alumno', width=200, anchor='w')
            self.tree.column('monto', width=120, anchor='e')
            self.tree.column('num_ingreso', width=120, anchor='center')
            self.tree.column('detalle', width=250, anchor='w')

            # Crear scrollbars vertical y horizontal
            vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
            hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
            self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

            # Colocar el Treeview y las scrollbars en el grid
            self.tree.grid(row=0, column=0, sticky='nsew')
            vsb.grid(row=0, column=1, sticky='ns')
            hsb.grid(row=1, column=0, sticky='ew')

            # Configurar el grid para que el Treeview se expanda correctamente
            tree_frame.rowconfigure(0, weight=1)
            tree_frame.columnconfigure(0, weight=1)

            # Configurar colores para los diferentes tipos de pago
            self.tree.tag_configure('PAGARE', background='#E8F4FF')  # Azul muy claro
            self.tree.tag_configure('CONTADO', background='#F0FFF0')  # Verde muy claro

            # Función para cargar datos del historial
            def load_history_data(mes_var, fecha_var, rut_var):
                """Carga el historial según los filtros"""
                try:
                    # Limpiar datos actuales
                    for item in self.tree.get_children():
                        self.tree.delete(item)

                    query = """
                        SELECT 
                            id_historial,
                            fecha_registro,
                            tipo_pago,
                            rut_alumno,
                            nombre_alumno,
                            monto,
                            numero_ingreso,
                            detalle
                        FROM historial_pagos 
                        WHERE 1=1
                    """
                    params = []

                    if mes_var.get().strip():
                        try:
                            month, year = mes_var.get().strip().split('/')
                            month = int(month)
                            year = int(year)
                            if not (1 <= month <= 12):
                                raise ValueError
                            query += " AND MONTH(fecha_registro) = %s AND YEAR(fecha_registro) = %s"
                            params.extend([month, year])
                        except ValueError:
                            messagebox.showwarning("Advertencia", "Formato de mes inválido. Use MM/YYYY")
                            return

                    if fecha_var.get().strip():
                        try:
                            day, month, year = fecha_var.get().strip().split('/')
                            # Validar fecha
                            import datetime
                            datetime.datetime(int(year), int(month), int(day))
                            fecha = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                            query += " AND DATE(fecha_registro) = %s"
                            params.append(fecha)
                        except (ValueError, OverflowError):
                            messagebox.showwarning("Advertencia", "Formato de fecha inválido. Use DD/MM/YYYY")
                            return

                    if rut_var.get().strip():
                        if not self.validar_rut(rut_var.get().strip()):
                            messagebox.showwarning("Advertencia", "RUT inválido")
                            return
                        query += " AND rut_alumno = %s"
                        params.append(rut_var.get().strip())

                    query += " ORDER BY fecha_registro DESC"

                    conn = connect_db()
                    if not conn:
                        messagebox.showerror("Error", "No se pudo conectar a la base de datos")
                        return

                    try:
                        cursor = conn.cursor()
                        cursor.execute(query, tuple(params))
                        results = cursor.fetchall()

                        for row in results:
                            formatted_row = [
                                row[0],                                            # id_historial
                                row[1].strftime('%d/%m/%Y %H:%M') if row[1] else '',  # fecha_registro
                                row[2].upper() if row[2] else '',                     # tipo_pago
                                row[3] if row[3] else '',                            # rut_alumno
                                row[4] if row[4] else '',                            # nombre_alumno
                                f"${int(row[5]):,}" if row[5] else '$0',            # monto
                                row[6] if row[6] else '',                            # numero_ingreso
                                row[7] if row[7] else ''                             # detalle
                            ]
                            
                            # Aplicar tag según el tipo de pago
                            tag = 'PAGARE' if row[2].lower() == 'pagare' else 'CONTADO'
                            self.tree.insert("", "end", values=formatted_row, tags=(tag,))

                    except Exception as e:
                        print(f"Error específico: {e}")
                        messagebox.showerror("Error", f"Error al cargar datos: {str(e)}")
                    finally:
                        if cursor:
                            cursor.close()
                        if conn:
                            conn.close()

                except Exception as e:
                    print(f"Error en load_history_data: {e}")
                    import traceback
                    traceback.print_exc()

            # Bind the load_history_data to the button
            # Esto ya está hecho en el botón "Buscar" anteriormente

            # Cargar datos iniciales
            load_history_data(mes_var, fecha_var, rut_var)

        except Exception as e:
            print(f"Error al mostrar historial de pagos: {e}")
            import traceback
            traceback.print_exc()

    def show_pending_payments(self):
        try:
            # Actualizar el título sin recrear el label
            self._update_title_label("Pagos Pendientes")
            
            # Limpiar solo el contenido del tree existente
            if hasattr(self, 'tree'):
                self.tree.delete(*self.tree.get_children())
            
            # Obtener datos y resumen
            data_raw, summary = fetch_pending_payments()
            
            # Verificar si ya existe el frame de resumen
            summary_exists = False
            for widget in self.main_frame.winfo_children():
                if isinstance(widget, ttk.Frame) and hasattr(widget, 'is_summary_frame'):
                    summary_exists = True
                    break
            
            # Crear el frame de resumen solo si no existe
            if not summary_exists:
                # Frame de resumen con el estilo consistente
                summary_frame = ttk.Frame(self.main_frame)
                summary_frame.is_summary_frame = True  # Marcamos el frame para identificarlo
                summary_frame.pack(fill=tk.X, padx=10, pady=5)
                
                # Box de resumen con estilo consistente
                summary_box = ttk.LabelFrame(summary_frame, text="Resumen de Pagos Pendientes")
                summary_box.pack(fill=tk.X, padx=5, pady=5)
                
                # Labels de resumen con estilo consistente de la aplicación
                total_label = ttk.Label(
                    summary_box, 
                    text=f"Total Pagos Pendientes: {summary['total']}",
                    style="TLabel"
                )
                total_label.pack(side=tk.LEFT, padx=20)
                
                pagare_label = ttk.Label(
                    summary_box,
                    text=f"Pagarés Pendientes: {summary['pagare_pendiente']}",
                    style="TLabel"
                )
                pagare_label.pack(side=tk.LEFT, padx=20)
            
            # Definir columnas y headers
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

            # Formatear datos
            formatted_data = []
            if data_raw:
                for payment in data_raw:
                    fecha_inscripcion = payment[4].strftime('%Y-%m-%d') if payment[4] else ''
                    fecha_final = payment[5].strftime('%Y-%m-%d') if payment[5] else ''
                    valor_total = f"${payment[7]:,.0f}" if payment[7] else ''

                    row = [
                        payment[0],                    # ID
                        payment[1],                    # Inscripción
                        payment[10],                   # Alumno
                        payment[11],                   # Curso
                        payment[9],                    # N° Acta
                        payment[2].capitalize(),       # Tipo
                        payment[3].capitalize(),       # Modalidad
                        f"{payment[12]}/{payment[6]}", # Cuotas pagadas / total
                        valor_total,                   # Valor
                        payment[8].upper(),            # Estado
                        fecha_inscripcion,
                        fecha_final
                    ]
                    formatted_data.append(row)

            # Configurar columnas del tree
            self.tree.config(columns=columns, show="headings")
            
            # Configurar columnas con anchos consistentes
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
                
            # Insertar datos
            for item in formatted_data:
                self.tree.insert("", "end", values=item, tags=('PENDIENTE',))
                
            # Configurar color para pendientes manteniendo consistencia
            self.tree.tag_configure('PENDIENTE', background='#FFF3CD')  # Amarillo claro

        except Exception as e:
            print(f"Error al mostrar pagos pendientes: {e}")
            import traceback
            traceback.print_exc()

    def add_payment_window(self):
        window = tk.Toplevel(self.root)
        window.title("Añadir Pago")
        window.geometry("900x550")
        window.configure(bg="#f0f5ff")
        window.grab_set()
        window.focus_force()

        # Intentar ícono (opcional)
        try:
            window.iconbitmap(resource_path('assets/logo1.ico'))
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

        # Botón "Buscar"
        ttk.Button(inscription_frame, text="Buscar",
            style='Action.TButton',command=fetch_inscription_info).grid(row=0, column=2, padx=5)

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

        # Nuevo: Fecha de Pago
        ttk.Label(payment_frame, text="Fecha de Pago:").grid(row=1, column=2, padx=5, pady=5)
        fecha_pago_var = tk.StringVar()
        fecha_pago_entry = DateEntry(payment_frame, textvariable=fecha_pago_var, width=17, date_pattern="yyyy-mm-dd")
        fecha_pago_entry.grid(row=1, column=3, padx=5, pady=5)

        # Mes de Inicio (si lo necesitas aparte)
        ttk.Label(payment_frame, text="Mes de Inicio:").grid(row=1, column=4, padx=5, pady=5)
        mes_inicio_var = tk.StringVar()
        mes_inicio_entry = ttk.Entry(payment_frame, textvariable=mes_inicio_var, width=10)
        mes_inicio_entry.grid(row=1, column=5, padx=5, pady=5)

        # Manejo del cambio de tipo de pago / modalidad
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

            # Obtener y validar fecha_pago ingresada
            try:
                fecha_pago_str = fecha_pago_var.get()
                if not fecha_pago_str:
                    raise ValueError
                fecha_pago_dt = datetime.strptime(fecha_pago_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Fecha de pago inválida", parent=window)
                return

            # Validar contribuciones si 'diferido'
            if modalidad_sel == "diferido":
                try:
                    monto_alumno = float(alumno_entry.get() or 0)
                    monto_empresa = float(empresa_entry.get() or 0)
                    monto_sence = float(sence_entry.get() or 0)
                    total_contrib = monto_alumno + monto_empresa + monto_sence
                    if not math.isclose(total_contrib, valor_total, rel_tol=1e-9):
                        messagebox.showerror(
                            "Error",
                            "La suma de contribuciones debe ser igual al valor total",
                            parent=window
                        )
                        return
                except ValueError:
                    messagebox.showerror("Error", "Valores de contribución inválidos", parent=window)
                    return
            else:
                monto_alumno = 0
                monto_empresa = 0
                monto_sence = 0

            # Insertar pago
            id_pago, id_pagare = insert_payment(
                id_inscripcion=id_insc,
                tipo_pago=tipo_pago_sel,
                modalidad_pago=modalidad_sel,
                valor_total=valor_total,
                num_cuotas=n_cuotas,
                fecha_pago=fecha_pago_dt
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

            template_path = resource_path("formatos/PAGARE.docx")
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
            style='Action.TButton',
            command=validate_and_save,
        )
        save_button.grid(row=4, column=0, columnspan=4, pady=10)

        # Botón para generar contrato (se mostrará solo cuando 'tipo_pago' sea 'pagare')
        generate_button = ttk.Button(
            main_frame,
            text="Generar Contrato Pagaré",
            style='Action.TButton',
            command=generar_contrato_pagare,
        )
        generate_button.grid_remove()  # Oculto por defecto

        # Ajustar pesos de columnas
        for i in range(4):
            main_frame.grid_columnconfigure(i, weight=1)

    def show_payments_by_inscription(self):
        window = tk.Toplevel(self.root)
        window.withdraw()  # Ocultar la ventana mientras se configura
        window.title("Búsqueda de Pagos")
        window.configure(bg="white")
        window.grab_set()

        try:
            if os.path.exists('assets/logo1.ico'):
                window.iconbitmap(resource_path('assets/logo1.ico'))
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")

        # Frame principal
        main_frame = ttk.Frame(window, padding="10", style='White.TFrame')
        main_frame.pack(fill='both', expand=True)

        # Frame para el logo
        logo_frame = ttk.Frame(main_frame, style='White.TFrame')
        logo_frame.pack(fill='x', pady=5)

        try:
            logo = tk.PhotoImage(file=resource_path('assets/logomarco.png'))
            logo_label = ttk.Label(logo_frame, image=logo, style='White.TLabel')
            logo_label.image = logo
            logo_label.pack()
        except Exception as e:
            print(f"Error al cargar logo: {e}")

        # Frame para campos de búsqueda
        search_frame = ttk.Frame(main_frame, style='White.TFrame')
        search_frame.pack(fill='x', pady=10)

        def create_search_field(label, row):
            ttk.Label(
                search_frame,
                text=label,
                style='White.TLabel'
            ).grid(row=row, column=0, sticky='e', padx=5, pady=3)
            
            entry = ttk.Entry(search_frame, width=30)
            entry.grid(row=row, column=1, sticky='w', padx=5, pady=3)
            return entry

        # Crear campos de búsqueda
        id_inscripcion_entry = create_search_field("ID Inscripción:", 0)
        rut_entry = create_search_field("RUT:", 1)
        nombre_completo_entry = create_search_field("Nombre Completo:", 2)

        def search():
            id_inscripcion = id_inscripcion_entry.get().strip()
            rut = rut_entry.get().strip()
            nombre_completo = nombre_completo_entry.get().strip()

            # Verificar que al menos un campo tenga datos
            if not any([id_inscripcion, rut, nombre_completo]):
                messagebox.showwarning("Advertencia", "Ingrese al menos un criterio de búsqueda", parent=window)
                return

            try:
                # Convertir ID a número si está presente
                id_inscripcion = int(id_inscripcion) if id_inscripcion else None
                
                # Llamar a la función de búsqueda
                payments = fetch_payments_by_criteria(
                    id_inscripcion=id_inscripcion,
                    rut=rut if rut else None,
                    nombre_completo=nombre_completo if nombre_completo else None
                )

                if payments:
                    columns = ("id_pago", "id_inscripcion", "tipo_pago", "modalidad_pago", "valor", "estado")
                    headers = ("ID Pago", "ID Inscripción", "Tipo", "Modalidad", "Valor", "Estado")
                    self._populate_tree(columns, headers, payments)
                    self._update_title_label(f"Pagos Encontrados: {len(payments)}")
                    messagebox.showinfo("Éxito", f"Se encontraron {len(payments)} pagos", parent=window)
                    window.destroy()
                else:
                    messagebox.showinfo("Info", "No se encontraron pagos", parent=window)

            except ValueError:
                messagebox.showerror("Error", "ID de inscripción inválido", parent=window)
            except Exception as e:
                messagebox.showerror("Error", f"Error al buscar pagos: {str(e)}", parent=window)

        # Frame para botones
        button_frame = ttk.Frame(main_frame, style='White.TFrame')
        button_frame.pack(fill='x', pady=10)

        ttk.Button(
            button_frame,
            text="Cancelar",
            command=window.destroy,
            style='Secondary.TButton'
        ).pack(side='right', padx=5)

        ttk.Button(
            button_frame,
            text="Buscar",
            command=search,
            style='Action.TButton'
        ).pack(side='right', padx=5)

        # Ajustar el tamaño de la ventana al contenido
        window.update_idletasks()
        window.geometry("")  # Esto hace que la ventana se ajuste al contenido exacto
        
        # Centrar la ventana
        window_width = window.winfo_width()
        window_height = window.winfo_height()
        position_x = (window.winfo_screenwidth() // 2) - (window_width // 2)
        position_y = (window.winfo_screenheight() // 2) - (window_height // 2)
        window.geometry(f"+{position_x}+{position_y}")
        
        # Hacer la ventana no redimensionable
        window.resizable(False, False)
        
        # Mostrar la ventana
        window.deiconify()
        window.focus_force()

    def update_payment_status_window(self):
        """
        Ventana para registrar pagos al contado
        """
        update_window = tk.Toplevel(self.root)
        update_window.title("Registrar Pago al Contado")
        update_window.grab_set()
        try:
            update_window.iconbitmap(resource_path('assets/logo1.ico'))
        except Exception as e:
            print(f"Error al cargar ícono: {e}")

        # Configurar tamaño y posición
        window_width = 910
        window_height = 630
        x = (update_window.winfo_screenwidth() - window_width) // 2
        y = (update_window.winfo_screenheight() - window_height) // 2
        update_window.geometry(f'{window_width}x{window_height}+{x}+{y-30}')


        # Frame principal
        main_frame = ttk.Frame(update_window, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Título
        title_label = ttk.Label(
            main_frame,
            text="Registrar Pago al Contado",
            font=("Segoe UI", 16, "bold"),
            foreground="#022e86"
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))

        # Frame de búsqueda
        search_frame = ttk.LabelFrame(main_frame, text="Buscar Pagos Pendientes", padding="5")
        search_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # Variables para criterios de búsqueda
        search_type = tk.StringVar(value="rut")
        
        # Radio buttons
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
        rut_frame = ttk.Frame(fields_frame)
        ttk.Label(rut_frame, text="RUT:").pack(side="left", padx=5)
        rut_entry = ttk.Entry(rut_frame, width=15)
        rut_entry.pack(side="left", padx=5)

        id_frame = ttk.Frame(fields_frame)
        ttk.Label(id_frame, text="ID Inscripción:").pack(side="left", padx=5)
        id_entry = ttk.Entry(id_frame, width=10)
        id_entry.pack(side="left", padx=5)

        nombre_frame = ttk.Frame(fields_frame)
        ttk.Label(nombre_frame, text="Nombre:").pack(side="left", padx=5)
        nombre_entry = ttk.Entry(nombre_frame, width=15)
        nombre_entry.pack(side="left", padx=5)
        ttk.Label(nombre_frame, text="Apellido:").pack(side="left", padx=5)
        apellido_entry = ttk.Entry(nombre_frame, width=15)
        apellido_entry.pack(side="left", padx=5)

        ttk.Button(search_frame, text="Buscar", command=lambda: search_payments(), 
                  style='Action.TButton').grid(row=1, column=3, padx=5, pady=5)

        # Tabla de resultados
        table_frame = ttk.Frame(main_frame)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        columns = ("ID Pago", "N° Acta", "RUT", "Alumno", "Curso", "Valor", "F. Inscripción")
        payment_table = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)

        widths = {
            "ID Pago": 80, "N° Acta": 100, "RUT": 100, "Alumno": 200,
            "Curso": 200, "Valor": 100, "F. Inscripción": 100
        }
        for col in columns:
            payment_table.heading(col, text=col)
            payment_table.column(col, width=widths[col])

        payment_table.grid(row=0, column=0, sticky="nsew")
        ttk.Scrollbar(table_frame, orient="vertical", 
                     command=payment_table.yview).grid(row=0, column=1, sticky="ns")
        ttk.Scrollbar(table_frame, orient="horizontal",
                     command=payment_table.xview).grid(row=1, column=0, sticky="ew")

        # Frame para botón de registro
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=10)

        ttk.Button(button_frame, text="Registrar Pago",
                  command=lambda: register_selected_payment(),
                  style='Action.TButton').pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Cerrar",
                  command=update_window.destroy,
                  style='Action.TButton').pack(side='right', padx=5)

        def toggle_search_fields(search_mode):
            """Muestra/oculta campos según el tipo de búsqueda"""
            rut_frame.pack_forget()
            id_frame.pack_forget()
            nombre_frame.pack_forget()

            if search_mode == "rut":
                rut_frame.pack(side="left")
            elif search_mode == "id":
                id_frame.pack(side="left")
            else:
                nombre_frame.pack(side="left")

        def search_payments():
            """Busca pagos pendientes al contado"""
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
                    SELECT 
                        p.id_pago, i.numero_acta, a.rut,
                        CONCAT(a.nombre, ' ', a.apellido) as alumno,
                        c.nombre_curso, p.valor_total,
                        p.fecha_inscripcion
                    FROM pagos p
                    JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
                    JOIN alumnos a ON i.id_alumno = a.rut
                    JOIN cursos c ON i.id_curso = c.id_curso
                    WHERE p.tipo_pago = 'contado' 
                    AND p.estado = 'pendiente'
                    AND {}
                    ORDER BY p.fecha_inscripcion DESC
                """

                if search_criteria == "rut":
                    rut = rut_entry.get().strip()
                    if not validar_rut(rut):
                        messagebox.showerror("Error", "RUT inválido", parent=update_window)
                        return
                    query = base_query.format("a.rut = %s")
                    cursor.execute(query, (rut,))

                elif search_criteria == "id":
                    inscription_id = id_entry.get().strip()
                    if not inscription_id.isdigit():
                        messagebox.showerror("Error", "ID de inscripción inválido", parent=update_window)
                        return
                    query = base_query.format("i.id_inscripcion = %s")
                    cursor.execute(query, (inscription_id,))

                else:
                    nombre = nombre_entry.get().strip()
                    apellido = apellido_entry.get().strip()
                    if not nombre and not apellido:
                        messagebox.showwarning("Advertencia", 
                                             "Ingrese al menos un nombre o apellido",
                                             parent=update_window)
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
                    messagebox.showinfo("Información", "No se encontraron pagos pendientes",
                                      parent=update_window)
                    return

                for row in results:
                    formatted_row = [
                        row[0],  # ID Pago
                        row[1],  # N° Acta
                        row[2],  # RUT
                        row[3],  # Alumno
                        row[4],  # Curso
                        f"${row[5]:,.0f}",  # Valor Total
                        row[6].strftime('%Y-%m-%d')  # Fecha Inscripción
                    ]
                    payment_table.insert('', 'end', values=formatted_row)

            except Exception as e:
                messagebox.showerror("Error", f"Error al buscar pagos: {str(e)}", parent=update_window)
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

        def show_success_message(alumno, valor):
            """
            Muestra ventana emergente con detalles del pago al contado registrado
            """
            success_window = tk.Toplevel()
            success_window.title("¡Pago Registrado!")
            
            # Configurar ícono
            try:
                success_window.iconbitmap(resource_path('assets/logo1.ico'))
            except Exception as e:
                print(f"Error al cargar ícono: {e}")
            
            # Configurar ventana
            success_window.configure(bg='white')
            width = 350
            height = 200
            
            # Obtener dimensiones de la pantalla
            screen_width = success_window.winfo_screenwidth()
            screen_height = success_window.winfo_screenheight()
            
            # Calcular posición para centrar
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            
            success_window.geometry(f'{width}x{height}+{x}+{y}')
            success_window.resizable(False, False)
            success_window.grab_set()

            # Frame principal con fondo blanco
            frame = tk.Frame(success_window, bg='white', padx=20, pady=20)
            frame.pack(fill='both', expand=True)

            # Mensajes
            tk.Label(frame,
                    text="¡Pago al Contado Registrado!",
                    font=('Segoe UI', 12, 'bold'),
                    fg='#0056b3',
                    bg='white').pack(pady=(0, 15))
            
            tk.Label(frame,
                    text=f"Valor Total: ${valor:,.0f}",
                    font=('Segoe UI', 11),
                    bg='white').pack(pady=2)
                    
            tk.Label(frame,
                    text=f"por el alumno {alumno}",
                    font=('Segoe UI', 11),
                    bg='white').pack(pady=2)

            # Botón Aceptar
            ttk.Button(frame,
                    text="Aceptar",
                    command=success_window.destroy,
                    style='Action.TButton').pack(pady=(15, 0))

        def register_selected_payment():
            """Registra el pago al contado seleccionado"""
            selection = payment_table.selection()
            if not selection:
                messagebox.showwarning("Advertencia", "Seleccione un pago para registrar",
                                    parent=update_window)
                return

            payment_id = payment_table.item(selection[0])['values'][0]
            
            # Confirmar
            if not messagebox.askyesno("Confirmar", 
                                    "¿Desea registrar este pago como pagado?",
                                    parent=update_window):
                return

            # Registrar pago
            success = register_contado_payment(payment_id)
            
            if success:
                # Obtener datos para mensaje
                datos = payment_table.item(selection[0])['values']
                alumno = datos[3]  # Nombre del alumno
                valor = float(datos[5].replace('$', '').replace(',', ''))
                
                # Mostrar mensaje de éxito con formato de pago al contado
                show_success_message(alumno, valor)
                
                # Actualizar interfaces
                self.show_payments()
            else:
                messagebox.showerror("Error", "No se pudo registrar el pago",
                                parent=update_window)

        # Mostrar campo RUT inicial y dar foco
        toggle_search_fields("rut")
        rut_entry.focus()

        # Binds para tecla Enter
        rut_entry.bind('<Return>', lambda e: search_payments())
        id_entry.bind('<Return>', lambda e: search_payments())
        nombre_entry.bind('<Return>', lambda e: search_payments())
        apellido_entry.bind('<Return>', lambda e: search_payments())

    def manage_cuotas_pagare_window(self):
        """
        Ventana para gestionar cuotas de pagaré con interfaz mejorada
        """
        window = tk.Toplevel(self.root)
        window.title("Administrar Cuotas - Pagaré")
        window.configure(bg="#f0f5ff")
        window.state("zoomed")
        window.grab_set()
        window.focus_force()

        try:
            window.iconbitmap(resource_path('assets/logo1.ico'))
        except Exception as e:
            print(f"Error al cargar ícono: {e}")

        # --- ESTILO MEJORADO ---
        style = ttk.Style(window)
        style.theme_use('clam')
        
        style.configure('Custom.Treeview',
                       background='white',
                       fieldbackground='white',
                       rowheight=30)
        style.map('Custom.Treeview',
                 background=[('selected', '#0056b3')],
                 foreground=[('selected', 'white')])

        # --- FRAME PRINCIPAL ---
        main_frame = ttk.Frame(window, padding="20")
        main_frame.pack(fill='both', expand=True)

        # --- FRAME DE BÚSQUEDA ---
        search_frame = ttk.LabelFrame(main_frame, text="Buscar Pagos (Tipo: Pagaré)", padding="15")
        search_frame.pack(fill='x', padx=5, pady=(0, 10))

        search_type = tk.StringVar(value="rut")
        for text, val in [("Por RUT Alumno", "rut"), 
                         ("Por ID Inscripción", "inscripcion"),
                         ("Por ID Pago", "pago")]:
            ttk.Radiobutton(search_frame, text=text, variable=search_type, 
                           value=val).pack(side='left', padx=10)

        search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=search_var, width=20,
                 font=('Segoe UI', 10)).pack(side='left', padx=15)
        ttk.Button(search_frame, text="Buscar", command=lambda: do_search(),
                  style='Action.TButton').pack(side='left')

        # --- FRAME DE PAGOS ---
        pagos_frame = ttk.LabelFrame(main_frame, text="Pagos Encontrados", padding="15")
        pagos_frame.pack(fill='x', padx=5, pady=(0, 10))

        pagos_columns = ("ID Pago", "ID Insc", "Alumno", "N° Acta", "Valor", "Estado")
        pagos_tree = ttk.Treeview(pagos_frame, columns=pagos_columns, 
                                 show="headings", height=3, style='Action.Treeview')

        for col in pagos_columns:
            pagos_tree.heading(col, text=col)
            pagos_tree.column(col, width=110, anchor=tk.CENTER)

        pagos_tree.pack(side='left', fill='x', expand=True)
        ttk.Scrollbar(pagos_frame, orient="vertical",
                     command=pagos_tree.yview).pack(side='right', fill='y')

        # --- FRAME DE CUOTAS Y ACCIONES ---
        cuotas_main_frame = ttk.Frame(main_frame)
        cuotas_main_frame.pack(fill='both', expand=True, pady=(0, 5))

        # Frame izquierdo (cuotas)
        cuotas_frame = ttk.LabelFrame(cuotas_main_frame, text="Cuotas del Pago", padding="15")
        cuotas_frame.pack(side='left', fill='both', expand=True, padx=(5, 10))

        cuotas_columns = ("N° Cuota", "Valor Cuota", "Vence", "F. Pago", 
                         "Estado Cuota", "N° Ingreso")
        cuotas_tree = ttk.Treeview(cuotas_frame, columns=cuotas_columns,
                                  show='headings', selectmode='extended',
                                  style='Action.Treeview')

        col_widths = {
            "N° Cuota": 80,
            "Valor Cuota": 120,
            "Vence": 120,
            "F. Pago": 120,
            "Estado Cuota": 120,
            "N° Ingreso": 120
        }
        
        for col in cuotas_columns:
            cuotas_tree.heading(col, text=col)
            cuotas_tree.column(col, width=col_widths[col], anchor=tk.CENTER)

        cuotas_tree.pack(side='left', fill='both', expand=True)
        ttk.Scrollbar(cuotas_frame, orient='vertical',
                     command=cuotas_tree.yview).pack(side='right', fill='y')

        # Frame derecho (acciones)
        action_frame = ttk.LabelFrame(cuotas_main_frame, text="Acciones", padding="15")
        action_frame.pack(side='right', fill='y', padx=(0, 5))

        # Variables
        selected_cuota_id = tk.IntVar(value=0)
        nro_cuota_var = tk.StringVar()
        valor_cuota_var = tk.StringVar()
        fecha_venc_var = tk.StringVar()
        cuotas_info_label_var = tk.StringVar(value="Cuotas Pagadas: 0 / 0")

        # Campos de edición
        fields = [
            ("ID Cuota:", selected_cuota_id, 6, 'readonly'),
            ("N° Cuota:", nro_cuota_var, 6, 'readonly'),
            ("Valor:", valor_cuota_var, 12, 'normal'),
            ("Vence:", fecha_venc_var, 12, 'normal')
        ]

        for row, (label, var, width, state) in enumerate(fields):
            ttk.Label(action_frame, text=label).grid(row=row, column=0, 
                                                   padx=5, pady=8, sticky='e')
            ttk.Entry(action_frame, textvariable=var, width=width,
                     state=state).grid(row=row, column=1, padx=5, sticky='w')

        # Botones de acción
        ttk.Button(action_frame, text="Pagar Seleccionadas",
                  command=lambda: pay_selected_cuotas(),
                  style='Action.TButton').grid(row=5, column=0, columnspan=2,
                                             pady=10, sticky='ew')

        ttk.Button(action_frame, text="Actualizar Cuota",
                  command=lambda: update_selected_cuota(),
                  style='Action.TButton').grid(row=6, column=0, columnspan=2,
                                             pady=5, sticky='ew')

        ttk.Label(action_frame, textvariable=cuotas_info_label_var,
                 font=('Segoe UI', 10, 'bold')).grid(row=7, column=0,
                                                    columnspan=2, pady=15)

        def show_success_message(nro_cuota, valor, alumno, num_ingreso):
            """Muestra mensaje de éxito con detalles de la cuota"""
            success_window = tk.Toplevel(window)
            success_window.title("¡Cuota Pagada!")
            
            # Configurar ícono
            try:
                success_window.iconbitmap(resource_path('assets/logo1.ico'))
            except Exception as e:
                print(f"Error al cargar ícono: {e}")
            
            # Configurar ventana
            success_window.configure(bg='white')  # Fondo blanco
            width = 350
            height = 250
            
            # Obtener dimensiones de la pantalla
            screen_width = success_window.winfo_screenwidth()
            screen_height = success_window.winfo_screenheight()
            
            # Calcular posición para centrar
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            
            success_window.geometry(f'{width}x{height}+{x}+{y}')
            success_window.resizable(False, False)
            success_window.grab_set()

            # Frame principal con fondo blanco
            frame = ttk.Frame(success_window)
            frame.pack(fill='both', expand=True)
            
            # Contenedor del mensaje con fondo blanco
            msg_container = tk.Frame(frame, bg='white', padx=20, pady=20)
            msg_container.pack(fill='both', expand=True)

            # Mensajes con fondo blanco y fuente personalizada
            tk.Label(msg_container,
                    text="¡Cuota Pagada Con Éxito!",
                    font=('Segoe UI', 12, 'bold'),
                    fg='#0056b3',
                    bg='white').pack(pady=(0, 15))
            
            tk.Label(msg_container,
                    text=f"Cuota {nro_cuota} de ${valor:,.0f}",
                    font=('Segoe UI', 11),
                    bg='white').pack(pady=2)
                    
            tk.Label(msg_container,
                    text=f"por el alumno {alumno}",
                    font=('Segoe UI', 11),
                    bg='white').pack(pady=2)
                    
            tk.Label(msg_container,
                    text=f"[N° Ingreso {num_ingreso}]",
                    font=('Segoe UI', 11),
                    bg='white').pack(pady=2)

            # Frame para el botón con fondo blanco
            button_frame = tk.Frame(msg_container, bg='white')
            button_frame.pack(pady=(15, 0))

            # Botón personalizado
            ttk.Button(button_frame,
                    text="Aceptar",
                    command=success_window.destroy,
                    style='Action.TButton').pack()
        def do_search():
            """Busca pagos según criterio seleccionado"""
            # Limpiar árboles
            for tree in [pagos_tree, cuotas_tree]:
                for item in tree.get_children():
                    tree.delete(item)

            val = search_var.get().strip()
            if not val:
                messagebox.showwarning("Atención", 
                                     "Ingrese un valor de búsqueda.",
                                     parent=window)
                return

            results = search_pagare_payments(search_type.get(), val)
            if not results:
                messagebox.showinfo("Información",
                                  "No se encontraron pagos con ese criterio.",
                                  parent=window)
                return

            for row in results:
                pagos_tree.insert("", "end", values=row)

        def load_cuotas_for_payment():
            """Carga las cuotas del pago seleccionado"""
            # Limpiar árbol de cuotas
            for item in cuotas_tree.get_children():
                cuotas_tree.delete(item)

            selection = pagos_tree.selection()
            if not selection:
                return
            
            row_values = pagos_tree.item(selection[0], 'values')
            id_pago = row_values[0]

            cuota_list = fetch_cuotas_by_pago(id_pago)
            if not cuota_list:
                cuotas_info_label_var.set("Cuotas Pagadas: 0 / 0")
                return

            total_cuotas = len(cuota_list)
            cuotas_pagadas = sum(1 for c in cuota_list if c[6] == 'pagada')

            for c in cuota_list:
                # c: (id_cuota, id_pago, nro_cuota, valor_cuota, fecha_venc, 
                #     fecha_pago, estado_cuota, numero_ingreso)
                nro = c[2]
                val = f"{c[3]:,.0f}"
                fven = c[4].strftime("%Y-%m-%d") if c[4] else ""
                fpag = c[5].strftime("%Y-%m-%d") if c[5] else ""
                est = c[6]
                n_ing = c[7] if c[7] else ""

                cuotas_tree.insert("", "end", 
                                 values=(nro, val, fven, fpag, est, n_ing),
                                 tags=(str(c[0]),))

            cuotas_info_label_var.set(f"Cuotas Pagadas: {cuotas_pagadas} / {total_cuotas}")

            # Limpiar campos
            selected_cuota_id.set(0)
            nro_cuota_var.set("")
            valor_cuota_var.set("")
            fecha_venc_var.set("")

        def on_select_cuota(event):
            """Maneja la selección de cuotas"""
            selected_items = cuotas_tree.selection()
            if not selected_items:
                return

            first_item = selected_items[0]
            vals = cuotas_tree.item(first_item, 'values')
            tags_ = cuotas_tree.item(first_item, 'tags')

            if tags_:
                selected_cuota_id.set(int(tags_[0]))

            nro_cuota_var.set(vals[0])
            valor_cuota_var.set(vals[1].replace(',', ''))
            fecha_venc_var.set(vals[2])

        def pay_selected_cuotas():
            """Procesa el pago de las cuotas seleccionadas"""
            selected_items = cuotas_tree.selection()
            if not selected_items:
                messagebox.showwarning("Atención",
                                     "Seleccione al menos una cuota.",
                                     parent=window)
                return
            
            # Obtener datos del pago seleccionado
            pago_selection = pagos_tree.selection()
            if not pago_selection:
                return
            pago_data = pagos_tree.item(pago_selection[0], 'values')
            alumno_nombre = pago_data[2]  # Índice del nombre del alumno
            
            error_count = 0
            for it in selected_items:
                tags_ = cuotas_tree.item(it, 'tags')
                valores = cuotas_tree.item(it, 'values')
                if tags_:
                    id_cuota = int(tags_[0])
                    nro_cuota = valores[0]
                    valor = float(valores[1].replace(',', ''))
                    
                    success, num_ingreso = register_quota_payment(id_cuota)
                    if success:
                        show_success_message(nro_cuota, valor, alumno_nombre, num_ingreso)
                    else:
                        error_count += 1

            if error_count > 0:
                messagebox.showerror("Error",
                                   f"Ocurrió un problema pagando {error_count} cuota(s).",
                                   parent=window)

            load_cuotas_for_payment()
            self.show_payments()

        def update_selected_cuota():
            """Actualiza los datos de la cuota seleccionada"""
            _id = selected_cuota_id.get()
            if _id == 0:
                messagebox.showwarning("Atención",
                                     "Seleccione una cuota primero.",
                                     parent=window)
                return

            new_val = valor_cuota_var.get().strip().replace(',', '')
            new_date = fecha_venc_var.get().strip()
            try:
                val_float = float(new_val) if new_val else None
            except ValueError:
                messagebox.showerror("Error",
                                   "El valor debe ser numérico.",
                                   parent=window)
                return

            if new_date:
                try:
                    datetime.strptime(new_date, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Error",
                                       "La fecha debe tener formato YYYY-MM-DD.",
                                       parent=window)
                    return

            # Obtener información del alumno para el mensaje de éxito
            pago_selection = pagos_tree.selection()
            if not pago_selection:
                return
            pago_data = pagos_tree.item(pago_selection[0], 'values')
            alumno_nombre = pago_data[2]  # Índice del nombre del alumno

            # Obtener número de cuota actual
            cuota_selection = cuotas_tree.selection()
            if not cuota_selection:
                return
            cuota_data = cuotas_tree.item(cuota_selection[0], 'values')
            nro_cuota = cuota_data[0]

            success, num_ingreso = update_cuota(
                _id, 
                valor_cuota=val_float,
                fecha_vencimiento=new_date or None
            )

            if success:
                show_success_message(
                    nro_cuota=nro_cuota,
                    valor=val_float,
                    alumno=alumno_nombre,
                    num_ingreso=num_ingreso
                )
                load_cuotas_for_payment()
                self.show_payments()
            else:
                messagebox.showerror("Error",
                                   "No se pudo actualizar la cuota.",
                                   parent=window)

        def on_pago_selected(event):
            """Carga automáticamente las cuotas al seleccionar un pago"""
            selection = pagos_tree.selection()
            if selection:
                load_cuotas_for_payment()

        # Eventos
        pagos_tree.bind('<<TreeviewSelect>>', on_pago_selected)
        cuotas_tree.bind('<<TreeviewSelect>>', on_select_cuota)
        
    # ---------------------------------------------------
    #                  FACTURAS
    # ---------------------------------------------------
   
    def show_invoices(self):
        """Muestra la lista de facturas en el TreeView."""
        try:
            self._clear_main_content()
            self._update_title_label("Listado de Facturas")
            
            content_frame = ttk.Frame(self.main_frame)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Frame para botones
            button_frame = ttk.Frame(content_frame)
            button_frame.pack(fill=tk.X, pady=(0, 5))
            
            ttk.Button(
                button_frame,
                text="Registrar N° Factura",
                command=self.add_invoice_window,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                button_frame,
                text="Cambiar Estado",
                command=self.change_invoice_status,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=5)
            
            # Frame para el treeview
            tree_frame = ttk.Frame(content_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            # Scrollbars
            vscroll = ttk.Scrollbar(tree_frame, orient="vertical")
            hscroll = ttk.Scrollbar(tree_frame, orient="horizontal")

            # Treeview
            self.tree = ttk.Treeview(
                tree_frame,
                selectmode="browse",
                yscrollcommand=vscroll.set,
                xscrollcommand=hscroll.set
            )

            # Configurar grid
            self.tree.grid(row=0, column=0, sticky="nsew")
            vscroll.grid(row=0, column=1, sticky="ns")
            hscroll.grid(row=1, column=0, sticky="ew")
            vscroll.configure(command=self.tree.yview)
            hscroll.configure(command=self.tree.xview)

            # Definir columnas
            columns = (
                "id_factura",
                "id_inscripcion",
                "numero_orden",
                "alumno",
                "curso",
                "numero_factura",
                "monto_total",
                "estado",
                "fecha_emision"
            )
            
            headers = (
                "ID",
                "ID Inscripción",
                "N° Orden",
                "Alumno",
                "Curso",
                "N° Factura",
                "Monto Total",
                "Estado",
                "Fecha Emisión"
            )

            # Configurar el tree
            self.tree.config(columns=columns, show="headings")
            
            # Configurar anchos de columnas
            column_widths = {
                "id_factura": 80,
                "id_inscripcion": 100,
                "numero_orden": 100,
                "alumno": 250,
                "curso": 250,
                "numero_factura": 120,
                "monto_total": 120,
                "estado": 100,
                "fecha_emision": 150
            }

            for column, header in zip(columns, headers):
                self.tree.heading(column, text=header, anchor=tk.CENTER)
                width = column_widths.get(column, 100)
                self.tree.column(column, width=width, minwidth=50, anchor=tk.CENTER)
            
            # Configurar tags de estado
            self.tree.tag_configure('PENDIENTE', background='#FFF3CD')
            self.tree.tag_configure('FACTURADA', background='#D4EDDA')
            
            # Cargar y mostrar datos
            try:
                conn = connect_db()
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        f.id_factura,
                        f.id_inscripcion,
                        p.numero_orden,
                        CONCAT(a.nombre, ' ', a.apellido) as alumno,
                        c.nombre_curso,
                        f.numero_factura,
                        f.monto_total,
                        f.estado,
                        f.fecha_emision
                    FROM facturas f
                    JOIN inscripciones i ON f.id_inscripcion = i.id_inscripcion
                    JOIN alumnos a ON i.id_alumno = a.rut
                    JOIN cursos c ON i.id_curso = c.id_curso
                    LEFT JOIN pagos p ON i.id_inscripcion = p.id_inscripcion
                    WHERE p.estado_orden = 'EMITIDO'
                    ORDER BY f.id_factura DESC
                """
                
                cursor.execute(query)
                facturas = cursor.fetchall()
                
                for factura in facturas:
                    # Formatear fecha
                    fecha_emision = factura[8].strftime('%Y-%m-%d %H:%M') if factura[8] else ''
                    # Formatear monto
                    monto_total = f"${factura[6]:,.0f}" if factura[6] is not None else '$0'
                    
                    # Obtener número de orden o mostrar "Sin N° Orden"
                    numero_orden = factura[2] if factura[2] else 'Sin N° Orden'
                    
                    values = (
                        factura[0],                # id_factura
                        factura[1],                # id_inscripcion
                        numero_orden,              # numero_orden directamente de pagos
                        factura[3],                # alumno
                        factura[4],                # curso
                        factura[5] or 'Sin N° Factura', # numero_factura
                        monto_total,               # monto_total formateado
                        factura[7].upper() if factura[7] else 'PENDIENTE',  # estado
                        fecha_emision              # fecha_emision formateada
                    )
                    
                    # Determinar el tag según el estado
                    estado = factura[7].upper() if factura[7] else 'PENDIENTE'
                    tag = 'PENDIENTE' if estado == 'PENDIENTE' else 'FACTURADA'
                    
                    self.tree.insert("", "end", values=values, tags=(tag,))
                    
            except Exception as e:
                print(f"Error al cargar datos de facturas: {e}")
                traceback.print_exc()
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

        except Exception as e:
            print(f"Error al mostrar facturas: {e}")
            traceback.print_exc()

    def _get_estado_factura_tag(self, estado):
        """
        Determina el tag de color según el estado de la factura
        """
        estado = estado.upper()
        if estado in ['PENDIENTE', 'FACTURADA']:
            return estado
        return 'PENDIENTE'  # Estado por defecto

    def add_invoice_window(self):
                """Ventana simplificada para registrar número de factura."""
                window = tk.Toplevel(self.root)
                window.title("Registrar N° Factura")
                window.geometry("500x350")  # Ajustado el tamaño
                window.configure(bg="white")  # Color de fondo gris claro
                window.resizable(False, False)  # No permitir redimensionar
                window.grab_set()
                window.focus_force()

                try:
                    window.iconbitmap(resource_path('assets/logo1.ico'))
                except Exception as e:
                    print(f"Error al cargar ícono: {e}")

                # Centrar ventana
                window.geometry(f"500x350+{(window.winfo_screenwidth() - 500)//2}+{(window.winfo_screenheight() - 350)//2}")

                # Frame principal - usando pack con expand=False para control preciso
                main_frame = ttk.Frame(window)
                main_frame.pack(fill='both', expand=False, padx=20, pady=20)

                # Título
                ttk.Label(
                    main_frame,
                    text="Registrar Número de Factura",
                    font=("Helvetica", 12, "bold"),
                    foreground="#00008B"  # Azul oscuro
                ).pack(pady=(0, 20))

                # Frame de información
                info_frame = ttk.LabelFrame(main_frame, text="Información", padding="10")
                info_frame.pack(fill="x", padx=5, pady=5)

                # Variables
                id_inscripcion_var = tk.StringVar()
                numero_factura_var = tk.StringVar()

                # Grid para campos con alineación precisa
                ttk.Label(info_frame, text="ID Inscripción:", anchor="e").grid(row=0, column=0, padx=(5, 10), pady=10, sticky="e")
                id_inscripcion_entry = ttk.Entry(info_frame, textvariable=id_inscripcion_var, width=20)
                id_inscripcion_entry.grid(row=0, column=1, padx=5, pady=10, sticky="w")

                ttk.Label(info_frame, text="N° Factura:", anchor="e").grid(row=1, column=0, padx=(5, 10), pady=10, sticky="e")
                ttk.Entry(info_frame, textvariable=numero_factura_var, width=20).grid(row=1, column=1, padx=5, pady=10, sticky="w")

                # Info del alumno
                info_alumno_label = ttk.Label(info_frame, text="", font=("Helvetica", 10))
                info_alumno_label.grid(row=2, column=0, columnspan=2, pady=10)

                def validate_inscripcion(*args):
                    try:
                        id_inscripcion = id_inscripcion_var.get()
                        if id_inscripcion:
                            info = fetch_inscripcion_info(id_inscripcion)
                            if info:
                                info_text = f"Alumno: {info['nombre']}\nCurso: {info['curso']}"
                                info_alumno_label.config(text=info_text)
                            else:
                                info_alumno_label.config(text="No se encontró la inscripción")
                    except Exception as e:
                        print(f"Error al validar inscripción: {e}")

                id_inscripcion_var.trace('w', validate_inscripcion)

                def save_invoice():
                    try:
                        id_inscripcion = int(id_inscripcion_var.get())
                        numero_factura = numero_factura_var.get().strip()

                        if not numero_factura:
                            messagebox.showerror("Error", "El número de factura es requerido", parent=window)
                            return

                        if insert_invoice(id_inscripcion, numero_factura):
                            messagebox.showinfo("Éxito", "Factura registrada correctamente", parent=window)
                            window.destroy()
                            self.show_invoices()
                        else:
                            messagebox.showerror("Error", "No se pudo registrar la factura", parent=window)
                    except ValueError:
                        messagebox.showerror("Error", "ID de inscripción inválido", parent=window)
                    except Exception as e:
                        messagebox.showerror("Error", f"Error al guardar: {str(e)}", parent=window)

                # Frame de botones al final de la ventana
                button_frame = ttk.Frame(window)
                button_frame.pack(side='bottom', pady=20)

                ttk.Button(
                    button_frame,
                    text="Guardar",
                    command=save_invoice,
                    style='Action.TButton',
                    width=15
                ).pack(side=tk.LEFT, padx=10)

                ttk.Button(
                    button_frame,
                    text="Cancelar",
                    command=window.destroy,
                    style='delete.TButton',
                    width=15
                ).pack(side=tk.LEFT, padx=10)


    def change_invoice_status(self):
        """Ventana para cambiar el estado de una factura."""
        # Obtener el item seleccionado
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor seleccione una factura")
            return

        # Obtener datos del item seleccionado
        item_data = self.tree.item(selected_item[0])
        id_factura = item_data['values'][0]
        current_status = item_data['values'][6]

        # Crear ventana
        window = tk.Toplevel(self.root)
        window.title("Cambiar Estado de Factura")
        window.geometry("300x150")
        
        # Centrar la ventana
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

        # Frame principal
        main_frame = ttk.Frame(window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Variable para el nuevo estado
        nuevo_estado = tk.StringVar(value=current_status)

        # Campos del formulario
        ttk.Label(main_frame, text="Nuevo Estado:").grid(row=0, column=0, sticky="w", pady=5)
        estado_combo = ttk.Combobox(
            main_frame,
            textvariable=nuevo_estado,
            values=["pendiente", "facturada"],
            state="readonly"
        )
        estado_combo.grid(row=0, column=1, sticky="ew", pady=5)

        def save_status():
            try:
                if update_invoice_status(id_factura, nuevo_estado.get()):
                    messagebox.showinfo("Éxito", "Estado actualizado correctamente")
                    window.destroy()
                    self.show_invoices()  # Actualizar lista
                else:
                    messagebox.showerror("Error", "No se pudo actualizar el estado")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {str(e)}")

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=20)

        ttk.Button(
            button_frame,
            text="Guardar",
            command=save_status
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancelar",
            command=window.destroy
        ).pack(side=tk.LEFT, padx=5)
   #=======================================================
   #                EMPRESAS Y CONTACTOS
   #=======================================================
    def show_empresas(self):
        try:
            # Limpiar solo el contenido principal
            self._clear_main_content()
            
            # Actualizar el título
            self._update_title_label("Listado de Empresas")
            
            # Crear frame para el contenido principal
            content_frame = ttk.Frame(self.main_frame)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Frame para botones
            button_frame = ttk.Frame(content_frame)
            button_frame.pack(fill=tk.X, pady=(0, 5))
            
            # Botones de acción
            ttk.Button(
                button_frame,
                text="Gestionar Empresa",
                command=self.manage_empresa_window,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=2)

            ttk.Button(
                button_frame,
                text="Gestionar Contactos",
                command=self.manage_contacts_window,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=2)
            
            # Frame para el treeview y scrollbars
            tree_frame = ttk.Frame(content_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            # Scrollbars
            vscroll = ttk.Scrollbar(tree_frame, orient="vertical")
            hscroll = ttk.Scrollbar(tree_frame, orient="horizontal")

            # Crear Treeview
            self.tree = ttk.Treeview(
                tree_frame,
                selectmode="extended",
                yscrollcommand=vscroll.set,
                xscrollcommand=hscroll.set
            )

            # Configurar grid
            self.tree.grid(row=0, column=0, sticky="nsew")
            vscroll.grid(row=0, column=1, sticky="ns")
            hscroll.grid(row=1, column=0, sticky="ew")

            # Configurar scrollbars
            vscroll.configure(command=self.tree.yview)
            hscroll.configure(command=self.tree.xview)

            # Configurar menú contextual
            self.context_menu = tk.Menu(tree_frame, tearoff=0)
            self.context_menu.add_command(label="Copiar celda", command=self._copy_selected_cell)
            self.context_menu.add_command(label="Copiar fila", command=self._copy_selected_row)

            # Variables para tracking
            self.last_click_x = 0
            self.last_click_y = 0

            # Bindings para el menú contextual
            self.tree.bind("<Button-3>", self._show_context_menu)
            self.tree.bind("<Button-1>", self._save_click_position)
            self.tree.bind("<ButtonRelease-3>", self._save_click_position)

            # Configurar tags
            self.tree.tag_configure('oddrow', background='#f5f5f5')
            self.tree.tag_configure('evenrow', background='#ffffff')
            
            # Definir columnas y headers
            columns = (
                "id_empresa", 
                "rut_empresa", 
                "direccion_empresa", 
                "nombre_contacto", 
                "correo_contacto", 
                "telefono_contacto", 
                "rol_contacto"
            )
            
            headers = (
                "Nombre Empresa", 
                "RUT", 
                "Dirección", 
                "Contacto", 
                "Email", 
                "Teléfono", 
                "Rol"
            )

            # Obtener datos
            empresas = fetch_all_empresas()
            
            # Configurar el tree
            self.tree.config(columns=columns, show="headings")
            
            # Configurar columnas con sus anchos optimizados
            column_widths = {
                "id_empresa": (150, True),
                "rut_empresa": (100, False),
                "direccion_empresa": (200, True),
                "nombre_contacto": (150, True),
                "correo_contacto": (200, True),
                "telefono_contacto": (120, False),
                "rol_contacto": (120, False)
            }

            # Aplicar configuración de columnas
            for column, header in zip(columns, headers):
                self.tree.heading(column, text=header, anchor=tk.CENTER)
                width, stretch = column_widths.get(column, (100, False))
                self.tree.column(column, width=width, stretch=stretch, anchor=tk.CENTER)
                
            # Insertar datos con colores alternados
            if empresas:
                for i, empresa in enumerate(empresas):
                    formatted_row = format_empresa_data(empresa)
                    tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                    self.tree.insert("", tk.END, values=formatted_row, tags=(tag,))
            else:
                print("No se encontraron empresas registradas")

        except Exception as e:
            print(f"Error al mostrar empresas: {e}")
            import traceback
            traceback.print_exc()

    def manage_empresa_window(self):
        """
        Ventana unificada para gestionar empresas (añadir/editar)
        """
        window = tk.Toplevel(self.root)
        window.title("Gestión de Empresas")
        window.configure(bg="#f0f5ff")
        window.grab_set()
        window.focus_force()

        # Configuración de la ventana
        width, height = 900, 600
        x = (window.winfo_screenwidth() - width) // 2
        y = (window.winfo_screenheight() - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

        try:
            window.iconbitmap(resource_path('assets/logo1.ico'))
        except Exception as e:
            print(f"Error al cargar ícono: {e}")

        # Definir el estilo para los botones
        style = ttk.Style(window)
        # Usar un tema que permita la personalización de los botones
        style.theme_use('clam')  
        style.configure('Custom.TButton',
                        background='#022e86',
                        foreground='white',
                        font=('Helvetica', 10, 'bold'))
        # Cambiar el color cuando el botón está activo o al pasar el mouse
        style.map('Custom.TButton',
                background=[('active', '#021f5e')],
                foreground=[('active', 'white')])

        # Frame principal
        main_frame = ttk.Frame(window, padding="20")
        main_frame.pack(fill='both', expand=True)

        # Variables
        modo_var = tk.StringVar(value="nuevo")  # 'nuevo' o 'editar'
        id_empresa_var = tk.StringVar()
        rut_empresa_var = tk.StringVar()
        direccion_var = tk.StringVar()

        # Frame superior para modo y búsqueda
        top_frame = ttk.LabelFrame(main_frame, text="Modo", padding="10")
        top_frame.pack(fill='x', pady=(0, 20))

        # Radiobuttons para seleccionar modo
        ttk.Radiobutton(
            top_frame,
            text="Nueva Empresa",
            variable=modo_var,
            value="nuevo",
            command=lambda: toggle_mode("nuevo")
        ).pack(side='left', padx=20)

        ttk.Radiobutton(
            top_frame,
            text="Editar Empresa",
            variable=modo_var,
            value="editar",
            command=lambda: toggle_mode("editar")
        ).pack(side='left', padx=20)

        # Frame de búsqueda (visible solo en modo editar)
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side='left', padx=20, fill='x', expand=True)
        
        ttk.Label(search_frame, text="ID Empresa:").pack(side='left', padx=(0, 10))
        search_entry = ttk.Entry(search_frame, width=30)
        search_entry.pack(side='left', padx=(0, 10))
        
        search_button = ttk.Button(
            search_frame,
            text="Buscar",
            command=lambda: buscar_empresa(search_entry.get()),
            style='Custom.TButton'
        )
        search_button.pack(side='left')

        # Frame de datos
        data_frame = ttk.LabelFrame(main_frame, text="Datos de la Empresa", padding="20")
        data_frame.pack(fill='both', expand=True, pady=(0, 20))

        # Función para crear campos
        def create_field(parent, label, variable, row, disabled=False):
            ttk.Label(parent, text=label).grid(row=row, column=0, padx=5, pady=10, sticky='e')
            entry = ttk.Entry(parent, textvariable=variable, width=40)
            if disabled:
                entry.state(['disabled'])
            entry.grid(row=row, column=1, padx=5, pady=10, sticky='w')
            return entry

        # Campos
        id_entry = create_field(data_frame, "ID Empresa:", id_empresa_var, 0)
        rut_entry = create_field(data_frame, "RUT Empresa:", rut_empresa_var, 1)
        dir_entry = create_field(data_frame, "Dirección:", direccion_var, 2)

        # Configurar grid
        data_frame.grid_columnconfigure(1, weight=1)

        def toggle_mode(mode):
            """Cambia entre modos añadir/editar"""
            if mode == "nuevo":
                search_frame.pack_forget()
                id_entry.state(['!disabled'])
                clear_fields()
            else:
                search_frame.pack(side='left', padx=20, fill='x', expand=True)
                id_entry.state(['disabled'])

        def clear_fields():
            """Limpia todos los campos"""
            id_empresa_var.set("")
            rut_empresa_var.set("")
            direccion_var.set("")

        def buscar_empresa(id_empresa):
            """Busca y carga los datos de una empresa"""
            if not id_empresa:
                messagebox.showwarning("Error", "Ingrese un ID de empresa", parent=window)
                return

            empresa = fetch_empresa_by_id(id_empresa)
            if empresa:
                id_empresa_var.set(empresa['id_empresa'])
                rut_empresa_var.set(empresa['rut_empresa'])
                direccion_var.set(empresa['direccion_empresa'] or "")
            else:
                messagebox.showerror("Error", "Empresa no encontrada", parent=window)

        def save_changes():
            """Guarda los cambios (nuevo registro o actualización)"""
            # Validar campos requeridos
            if not id_empresa_var.get().strip() or not rut_empresa_var.get().strip():
                messagebox.showwarning("Error", "ID y RUT de empresa son obligatorios", parent=window)
                return

            # Validar RUT
            if not validar_rut(rut_empresa_var.get().strip()):
                messagebox.showerror("Error", "RUT inválido", parent=window)
                return

            # Preparar datos
            empresa_data = {
                'id_empresa': id_empresa_var.get().strip(),
                'rut_empresa': rut_empresa_var.get().strip(),
                'direccion_empresa': direccion_var.get().strip() or None
            }

            # Guardar
            is_update = modo_var.get() == "editar"
            if save_empresa(empresa_data, is_update):
                messagebox.showinfo(
                    "Éxito",
                    "Empresa actualizada correctamente" if is_update else "Empresa agregada correctamente",
                    parent=window
                )
                self.show_empresas()  # Actualizar lista
                window.destroy()
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo guardar los cambios",
                    parent=window
                )

        # Frame de botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=20)

        ttk.Button(
            button_frame,
            text="Guardar",
            command=save_changes,
            style="Action.TButton"
        ).pack(side='right', padx=5)

        ttk.Button(
            button_frame,
            text="Limpiar",
            command=clear_fields,
            style="delete.TButton"
        ).pack(side='right', padx=5)

        # Inicializar modo
        toggle_mode("nuevo")

    def manage_contacts_window(self):
        """
        Ventana unificada para gestionar contactos de empresas
        """
        window = tk.Toplevel(self.root)
        window.title("Gestión de Contactos")
        window.configure(bg="#f0f5ff")
        window.grab_set()
        window.focus_force()

        # Configuración de la ventana
        window.state("zoomed")

        try:
            window.iconbitmap(resource_path('assets/logo1.ico'))
        except Exception as e:
            print(f"Error al cargar ícono: {e}")


        # Frame principal
        main_frame = ttk.Frame(window, padding="20")
        main_frame.pack(fill='both', expand=True)

        # Frame superior
        top_frame = ttk.LabelFrame(main_frame, text="Selección de Empresa", padding="10")
        top_frame.pack(fill='x', pady=(0, 20))

        # Combobox para seleccionar empresa
        empresa_var = tk.StringVar()
        empresas = fetch_all_empresas_for_combo()
        empresa_combo = ttk.Combobox(
            top_frame, 
            textvariable=empresa_var,
            values=[f"{e['id_empresa']} - {e['rut_empresa']}" for e in empresas],
            width=50,
            state="readonly"
        )
        empresa_combo.pack(side='left', padx=20)

        # Frame central dividido
        central_frame = ttk.Frame(main_frame)
        central_frame.pack(fill='both', expand=True, pady=10)

        # Frame izquierdo para lista de contactos
        list_frame = ttk.LabelFrame(central_frame, text="Contactos existentes", padding="10")
        list_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Treeview para contactos
        columns = ("ID", "Nombre", "Rol", "Correo", "Teléfono")
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='browse')

        # Configurar columnas
        column_widths = {
            "ID": 80,
            "Nombre": 200,
            "Rol": 150,
            "Correo": 200,
            "Teléfono": 150
        }

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=column_widths[col], anchor=tk.CENTER)

        # Scrollbar para el tree
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Frame derecho para formulario
        form_frame = ttk.LabelFrame(central_frame, text="Detalles del Contacto", padding="20")
        form_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))

        # Variables para el formulario
        contact_vars = {
            'id_contacto': tk.StringVar(),
            'nombre_contacto': tk.StringVar(),
            'rol_contacto': tk.StringVar(),
            'correo_contacto': tk.StringVar(),
            'telefono_contacto': tk.StringVar()
        }

        # Crear campos del formulario
        campos = [
            ("Nombre:", 'nombre_contacto'),
            ("Rol:", 'rol_contacto'),
            ("Correo:", 'correo_contacto'),
            ("Teléfono:", 'telefono_contacto')
        ]

        for i, (label, var_name) in enumerate(campos):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, padx=5, pady=10, sticky='e')
            ttk.Entry(
                form_frame,
                textvariable=contact_vars[var_name],
                width=40
            ).grid(row=i, column=1, padx=5, pady=10, sticky='w')

        def clear_form():
            """Limpia el formulario"""
            for var in contact_vars.values():
                var.set("")
            tree.selection_remove(*tree.selection())

        def load_contacts():
            """Carga los contactos de la empresa seleccionada"""
            tree.delete(*tree.get_children())
            if not empresa_var.get():
                return

            id_empresa = empresa_var.get().split(' - ')[0]
            contacts = fetch_contactos_by_empresa(id_empresa)
            
            for contact in contacts:
                tree.insert("", "end", values=(
                    contact['id_contacto'],
                    contact['nombre_contacto'],
                    contact['rol_contacto'],
                    contact['correo_contacto'],
                    contact['telefono_contacto']
                ))

        def on_tree_select(event):
            """Carga los datos del contacto seleccionado en el formulario"""
            selected = tree.selection()
            if not selected:
                return
                
            values = tree.item(selected[0])['values']
            contact_vars['id_contacto'].set(values[0])
            contact_vars['nombre_contacto'].set(values[1])
            contact_vars['rol_contacto'].set(values[2])
            contact_vars['correo_contacto'].set(values[3])
            contact_vars['telefono_contacto'].set(values[4])

        def save_contact():
            """Guarda o actualiza un contacto"""
            if not empresa_var.get():
                messagebox.showwarning("Error", "Seleccione una empresa", parent=window)
                return

            if not contact_vars['nombre_contacto'].get().strip():
                messagebox.showwarning("Error", "El nombre es obligatorio", parent=window)
                return

            id_empresa = empresa_var.get().split(' - ')[0]
            is_update = bool(contact_vars['id_contacto'].get())
            
            contact_data = {
                'id_empresa': id_empresa,
                'nombre_contacto': contact_vars['nombre_contacto'].get().strip(),
                'rol_contacto': contact_vars['rol_contacto'].get().strip(),
                'correo_contacto': contact_vars['correo_contacto'].get().strip(),
                'telefono_contacto': contact_vars['telefono_contacto'].get().strip()
            }

            if is_update:
                contact_data['id_contacto'] = contact_vars['id_contacto'].get()
                self.show_empresas()  # Actualizar lista

            if save_contacto_empresa(contact_data, is_update):
                messagebox.showinfo(
                    "Éxito",
                    "Contacto actualizado" if is_update else "Contacto agregado",
                    parent=window
                )
                self.show_empresas()  # Actualizar lista
                load_contacts()
                clear_form()
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo guardar el contacto",
                    parent=window
                )

        def delete_contact():
            """Elimina el contacto seleccionado"""
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Error", "Seleccione un contacto", parent=window)
                return

            if messagebox.askyesno("Confirmar", "¿Eliminar el contacto seleccionado?", parent=window):
                contact_id = tree.item(selected[0])['values'][0]
                if delete_contacto_empresa(contact_id):
                    messagebox.showinfo("Éxito", "Contacto eliminado", parent=window)
                    self.show_empresas()  # Actualizar lista
                    load_contacts()
                    clear_form()
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el contacto", parent=window)

        # Botones del formulario
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=len(campos), column=0, columnspan=2, pady=20)

        ttk.Button(
            button_frame,
            text="Guardar",
            command=save_contact,
            style="Action.TButton"
        ).pack(side='left', padx=5)

        ttk.Button(
            button_frame,
            text="Limpiar",
            command=clear_form,
            style="Action.TButton"
        ).pack(side='left', padx=5)

        ttk.Button(
            button_frame,
            text="Eliminar",
            command=delete_contact,
            style="delete.TButton"
        ).pack(side='left', padx=5)

        # Eventos
        tree.bind('<<TreeviewSelect>>', on_tree_select)
        empresa_combo.bind('<<ComboboxSelected>>', lambda e: load_contacts())


    #========================================================
    #                    COTIZACIONES
    #========================================================

    def show_cotizaciones(self):
        """
        Muestra la lista de cotizaciones en el treeview
        """
        try:
            # Limpiar solo el contenido principal
            self._clear_main_content()
            
            # Actualizar el título
            self._update_title_label("Listado de Cotizaciones")
            
            # Crear frame para el contenido principal
            content_frame = ttk.Frame(self.main_frame)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Frame para botones
            button_frame = ttk.Frame(content_frame)
            button_frame.pack(fill=tk.X, pady=(0, 5))
            
            # Botón de acción
            ttk.Button(
                button_frame,
                text="Generar Cotización",
                command=self.show_cotizacion_window,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=2)
            
            # Frame para el treeview y scrollbars
            tree_frame = ttk.Frame(content_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            # Scrollbars
            vscroll = ttk.Scrollbar(tree_frame, orient="vertical")
            hscroll = ttk.Scrollbar(tree_frame, orient="horizontal")

            # Crear Treeview
            self.tree = ttk.Treeview(
                tree_frame,
                selectmode="extended",
                yscrollcommand=vscroll.set,
                xscrollcommand=hscroll.set
            )

            # Configurar grid
            self.tree.grid(row=0, column=0, sticky="nsew")
            vscroll.grid(row=0, column=1, sticky="ns")
            hscroll.grid(row=1, column=0, sticky="ew")

            # Configurar scrollbars
            vscroll.configure(command=self.tree.yview)
            hscroll.configure(command=self.tree.xview)

            # Configurar menú contextual
            self.context_menu = tk.Menu(tree_frame, tearoff=0)
            self.context_menu.add_command(label="Copiar celda", command=self._copy_selected_cell)
            self.context_menu.add_command(label="Copiar fila", command=self._copy_selected_row)

            # Variables para tracking
            self.last_click_x = 0
            self.last_click_y = 0

            # Bindings para el menú contextual
            self.tree.bind("<Button-3>", self._show_context_menu)
            self.tree.bind("<Button-1>", self._save_click_position)
            self.tree.bind("<ButtonRelease-3>", self._save_click_position)

            # Configurar tags
            self.tree.tag_configure('oddrow', background='#f5f5f5')
            self.tree.tag_configure('evenrow', background='#ffffff')
            
            # Definir columnas y headers
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

            # Obtener datos
            cotizaciones = fetch_cotizaciones()
            
            # Configurar el tree
            self.tree.config(columns=columns, show="headings")
            
            # Configurar columnas con sus anchos optimizados
            column_widths = {
                "id_cotizacion": (80, False),
                "nombre_contacto": (150, True),
                "origen": (150, True),
                "fecha_cotizacion": (120, False),
                "fecha_vencimiento": (120, False),
                "email": (200, True),
                "modo_pago": (100, False),
                "cantidad_total_cursos": (100, False)
            }

            # Aplicar configuración de columnas
            for column, header in zip(columns, headers):
                self.tree.heading(column, text=header, anchor=tk.CENTER)
                width, stretch = column_widths.get(column, (100, False))
                self.tree.column(column, width=width, stretch=stretch, anchor=tk.CENTER)
                
            # Insertar datos con colores alternados
            for i, cotizacion in enumerate(cotizaciones):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.tree.insert("", "end", values=cotizacion, tags=(tag,))

        except Exception as e:
            print(f"Error al mostrar Cotizaciones: {e}")
            import traceback
            traceback.print_exc()
    
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
            window.iconbitmap(resource_path('assets/logo1.ico'))
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
            logo = tk.PhotoImage(file=resource_path('assets/logomarco.png'))
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

    #================================================================
    #                   TRAMITACIONES 
    #================================================================
    def show_tramitaciones(self):
            try:
                # Limpiar contenido principal
                self._clear_main_content()
                # Actualizar título
                self._update_title_label("Gestión de Tramitaciones")
                self.tramite_alert()  # Mostrar alerta de trámites
                
                # Frame principal
                content_frame = ttk.Frame(self.main_frame)
                content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

                # Frame superior para búsqueda y filtros
                search_frame = ttk.Frame(content_frame)
                search_frame.pack(fill=tk.X, pady=(0, 5))

                # Campo de búsqueda por RUT
                ttk.Label(search_frame, text="RUT Alumno:").pack(side=tk.LEFT, padx=5)
                self.rut_search = ttk.Entry(search_frame)
                self.rut_search.pack(side=tk.LEFT, padx=5)
                
                # Botones de filtrado
                ttk.Button(
                    search_frame,
                    text="Buscar por RUT",
                    command=lambda: self._filter_tramitaciones_by_rut(),
                    style='Action.TButton'
                ).pack(side=tk.LEFT, padx=2)

                ttk.Button(
                    search_frame,
                    text="Ver Activas",
                    command=lambda: self._show_active_tramitaciones(),
                    style='Action.TButton'
                ).pack(side=tk.LEFT, padx=2)

                ttk.Button(
                    search_frame,
                    text="Ver Todas",
                    command=lambda: self._refresh_tramitaciones(),
                    style='Action.TButton'
                ).pack(side=tk.LEFT, padx=2)

                ttk.Button(
                    search_frame,
                    text="Finalizar Tramitacion",
                    command=lambda: self._update_tramitacion_status(),
                    style='Action.TButton'
                ).pack(side=tk.LEFT, padx=2)

                # Botón para agregar observación
                ttk.Button(
                    search_frame,
                    text="Agregar Observación",
                    command=self._add_observation,  # Apunta a la función que definiremos
                    style='Action.TButton'
                ).pack(side=tk.LEFT, padx=2)

                # Botón para ver historial de observaciones
                ttk.Button(
                    search_frame,
                    text="Ver Historial",
                    command=self._view_observation_history,  # Apunta a la función que definiremos
                    style='Action.TButton'
                ).pack(side=tk.LEFT, padx=2)


                # Frame para el treeview principal
                tree_frame = ttk.Frame(content_frame)
                tree_frame.pack(fill=tk.BOTH, expand=True)

                # Scrollbars
                vscroll = ttk.Scrollbar(tree_frame, orient="vertical")
                hscroll = ttk.Scrollbar(tree_frame, orient="horizontal")

                # Treeview principal
                self.tramitaciones_tree = ttk.Treeview(
                    tree_frame,
                    selectmode="extended",
                    yscrollcommand=vscroll.set,
                    xscrollcommand=hscroll.set
                )

                # Configurar grid
                self.tramitaciones_tree.grid(row=0, column=0, sticky="nsew")
                vscroll.grid(row=0, column=1, sticky="ns")
                hscroll.grid(row=1, column=0, sticky="ew")
                tree_frame.grid_rowconfigure(0, weight=1)
                tree_frame.grid_columnconfigure(0, weight=1)

                # Configurar scrollbars
                vscroll.config(command=self.tramitaciones_tree.yview)
                hscroll.config(command=self.tramitaciones_tree.xview)

                # Configurar columnas según las nuevas queries
                columns = (
                    "id_inscripcion",
                    "rut",
                    "nombre_completo",
                    "estado_general",
                    "fecha_ultimo_cambio",
                    "observacion",
                    "total_documentos",
                    "id_tramitacion"  # Columna adicional oculta
                )
                
                headers = (
                    "ID Inscripción",
                    "RUT",
                    "Nombre Completo",
                    "Estado",
                    "Última Actualización",
                    "Observaciones",
                    "Total Docs",
                    ""  # Header vacío para la columna oculta
                )

                self.tramitaciones_tree.config(columns=columns, show="headings")

                # Configurar encabezados y ancho de columnas
                column_widths = {
                    "id_inscripcion": 100,
                    "rut": 120,
                    "nombre_completo": 250,
                    "estado_general": 120,
                    "fecha_ultimo_cambio": 150,
                    "observacion": 300,
                    "total_documentos": 100,
                    "id_tramitacion": 0  # Ancho 0 para ocultar la columna
                }

                for column, header in zip(columns, headers):
                    self.tramitaciones_tree.heading(column, text=header, anchor=tk.CENTER)
                    self.tramitaciones_tree.column(column, width=column_widths.get(column, 100), anchor=tk.CENTER)

                # Frame para detalles de documentos
                detail_frame = ttk.LabelFrame(content_frame, text="Documentos de la Tramitación")
                detail_frame.pack(fill=tk.BOTH, expand=True, pady=5)

                # Treeview para documentos con las columnas actualizadas
                self.docs_tree = ttk.Treeview(
                    detail_frame,
                    columns=("doc_num", "nombre_tramite", "fecha_emision", "estado"),
                    show="headings",
                    height=5
                )

                self.docs_tree.pack(fill=tk.BOTH, expand=True)

                # Configurar columnas de documentos
                doc_headers = ("N° Documento", "Nombre Trámite", "Fecha Emisión", "Estado")
                doc_widths = (100, 200, 150, 100)

                for col, header, width in zip(self.docs_tree["columns"], doc_headers, doc_widths):
                    self.docs_tree.heading(col, text=header, anchor=tk.CENTER)
                    self.docs_tree.column(col, width=width, anchor=tk.CENTER)

                # Binding para mostrar documentos al seleccionar una tramitación
                self.tramitaciones_tree.bind('<<TreeviewSelect>>', self._show_tramitacion_docs)

                # Cargar datos iniciales
                self._show_active_tramitaciones()

            except Exception as e:
                print(f"Error al mostrar tramitaciones: {e}")
                import traceback
                traceback.print_exc()
    def center_window(self, window):
        """Centra la ventana 'window' en la pantalla."""
        window.update_idletasks()  # Para calcular tamaño real
        w = window.winfo_width()
        h = window.winfo_height()
        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        window.geometry(f"{w}x{h}+{x}+{y}")

    def _add_observation(self):
        """Abre una ventana para agregar una nueva observación a la tramitación seleccionada."""
        selection = self.tramitaciones_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Debe seleccionar una tramitación.")
            return

        # Obtenemos los valores de la fila seleccionada.
        item = self.tramitaciones_tree.item(selection[0])
        row_values = item["values"]
        id_tramitacion = row_values[7]

        # Creamos una ventana Toplevel para ingresar la observación
        obs_window = tk.Toplevel(self.main_frame)
        obs_window.title("Agregar Observación")
        obs_window.iconbitmap(resource_path('assets/logo1.ico'))

        tk.Label(obs_window, text="Nueva observación:").pack(padx=10, pady=5)

        obs_text = tk.Text(obs_window, width=60, height=6)
        obs_text.pack(padx=10, pady=5)

        def save_observation():
            new_obs = obs_text.get("1.0", tk.END).strip()
            if not new_obs:
                messagebox.showwarning("Advertencia", "Debe ingresar una observación.")
                return

            try:
                conn = connect_db()
                cursor = conn.cursor()

                # Concatenamos la nueva observación con la existente, agregando la fecha/hora
                query = """
                    UPDATE tramitaciones
                    SET observacion = CONCAT(
                        IFNULL(observacion, ''), 
                        '\n[', NOW(), '] ', %s
                    ),
                    fecha_ultimo_cambio = NOW()
                    WHERE id_tramitacion = %s
                """
                cursor.execute(query, (new_obs, id_tramitacion))
                conn.commit()

                messagebox.showinfo("Éxito", "Observación agregada correctamente.")
                obs_window.destroy()

                # Refrescamos la vista principal (para ver la observación actualizada en el Treeview)
                self._refresh_tramitaciones()

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la observación: {e}")
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

        ttk.Button(obs_window, text="Guardar", command=save_observation).pack(pady=5)

        # Centrar la ventana emergente
        obs_window.update_idletasks()  # Asegura que se hayan calculado sus dimensiones
        self.center_window(obs_window)




    def _view_observation_history(self):
        """Abre una ventana que muestra todas las observaciones acumuladas para la tramitación seleccionada."""
        selection = self.tramitaciones_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Debe seleccionar una tramitación.")
            return

        item = self.tramitaciones_tree.item(selection[0])
        row_values = item["values"]
        id_tramitacion = row_values[7]  # Ajusta si tu ID está en otra columna

        try:
            conn = connect_db()
            cursor = conn.cursor()
            query = "SELECT observacion FROM tramitaciones WHERE id_tramitacion = %s"
            cursor.execute(query, (id_tramitacion,))
            row = cursor.fetchone()
            observaciones = row[0] if row and row[0] else ""
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener la observación: {e}")
            traceback.print_exc()
            return
        finally:
            if cursor: 
                cursor.close()
            if conn:
                conn.close()

        # Creamos una sola ventana para mostrar el historial
        hist_window = tk.Toplevel(self.main_frame)
        hist_window.title("Historial de Observaciones")
        hist_window.iconbitmap(resource_path('assets/logo1.ico'))

        text_widget = tk.Text(hist_window, width=80, height=15)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text_widget.insert(tk.END, observaciones)
        text_widget.config(state="disabled")  # Solo lectura

        # Centrar la ventana
        hist_window.update_idletasks()
        self.center_window(hist_window)



    def _filter_tramitaciones_by_rut(self):
        """Filtra las tramitaciones por RUT"""
        rut = self.rut_search.get().strip()
        if not rut:
            messagebox.showwarning("Advertencia", "Por favor ingrese un RUT")
            return
        
        # Limpiar treeview
        for item in self.tramitaciones_tree.get_children():
            self.tramitaciones_tree.delete(item)
        
        # Obtener y mostrar tramitaciones filtradas
        tramitaciones = fetch_tramitaciones_by_rut(rut)
        self._populate_tramitaciones_tree(tramitaciones)

    def _show_active_tramitaciones(self):
        """Muestra solo las tramitaciones activas"""
        # Limpiar treeview
        for item in self.tramitaciones_tree.get_children():
            self.tramitaciones_tree.delete(item)
        
        # Obtener y mostrar tramitaciones activas
        tramitaciones = fetch_tramitaciones_activas()
        self._populate_tramitaciones_tree(tramitaciones)

    def _refresh_tramitaciones(self):
        """Actualiza la vista con todas las tramitaciones"""
        # Limpiar treeview
        for item in self.tramitaciones_tree.get_children():
            self.tramitaciones_tree.delete(item)
        
        # Obtener y mostrar todas las tramitaciones
        tramitaciones = fetch_tramitaciones()
        self._populate_tramitaciones_tree(tramitaciones)

    def _get_last_line_of_observation(self, full_text):
        """
        Devuelve la última línea no vacía de 'full_text'.
        Si no hay líneas, retorna cadena vacía.
        """
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        if lines:
            return lines[-1]  # La última línea
        return ""


    def _populate_tramitaciones_tree(self, tramitaciones):
        """Puebla el treeview con las tramitaciones, mostrando solo la última observación."""
        for i, row in enumerate(tramitaciones):
            # row es una tupla, conviértela a lista para poder modificarla
            row = list(row)
            
            # Extraer todo el texto de observación
            full_observation = row[5] if row[5] else ""
            
            # Obtener solo la última línea
            last_line = self._get_last_line_of_observation(full_observation)
            
            # Reemplazar en la posición 5 (columna 'observacion') la última línea
            row[5] = last_line
            
            # Insertar en el Treeview
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.tramitaciones_tree.insert("", "end", values=row, tags=(tag,))


    def _show_tramitacion_docs(self, event):
        """Muestra los documentos de la tramitación seleccionada"""
        selection = self.tramitaciones_tree.selection()
        if not selection:
            return
        
        # Limpiar treeview de documentos
        for item in self.docs_tree.get_children():
            self.docs_tree.delete(item)
        
        # Obtener id_tramitacion de la columna oculta (índice 7)
        tramitacion_id = self.tramitaciones_tree.item(selection[0])['values'][7]
        
        
        # Obtener y mostrar documentos
        documentos = fetch_tipos_tramite(tramitacion_id)
        for i, doc in enumerate(documentos):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.docs_tree.insert("", "end", values=doc, tags=(tag,))

    def _update_tramitacion_status(self):
        """Actualiza el estado de la tramitación seleccionada"""
        selected = self.tramitaciones_tree.selection()
        if not selected:
            messagebox.showwarning("Selección", "Por favor seleccione una tramitación")
            return

        conn = None
        cursor = None
        try:
            item = self.tramitaciones_tree.item(selected[0])
            id_tramitacion = item['values'][-1]  # El id_tramitacion está en la última columna
            estado_actual = item['values'][3]  # El estado está en la cuarta columna

            if estado_actual == 'completado':
                messagebox.showinfo("Info", "Esta tramitación ya está completada")
                return

            # Confirmar actualización
            if not messagebox.askyesno("Confirmar", 
                "¿Está seguro que desea marcar esta tramitación como completada?\n\n" +
                "Esto indicará que todos los trámites han finalizado."):
                return

            # Establecer conexión
            conn = connect_db()
            cursor = conn.cursor()
                
            # Actualizar estado
            query = """
                UPDATE tramitaciones 
                SET estado_general = 'completado',
                    fecha_final = CURDATE()
                WHERE id_tramitacion = %s
            """
                
            cursor.execute(query, (id_tramitacion,))
            conn.commit()
                
            messagebox.showinfo("Éxito", "Tramitación marcada como completada")
            self._refresh_tramitaciones()  # Actualizar vista

        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Error", f"Error al actualizar tramitación: {str(e)}")
            print(f"Error en _update_tramitacion_status: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def show_tramitar(self):
        """Muestra la ventana de tramitaciones integrada en el frame principal"""
        try:
            # Limpiar solo el contenido principal
            self._clear_main_content()
            
            # Actualizar el título
            self._update_title_label("  ")

            # Crear frame para el contenido principal
            content_frame = ttk.Frame(self.main_frame)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Crear la instancia de TramitacionesFrame
            self.tramitaciones = IntegratedTramitacionesFrame(content_frame)
            self.tramitaciones.pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            print(f"Error al mostrar tramitaciones: {e}")
            import traceback
            traceback.print_exc()
# ---------------------------------------------------
#       Funciones Libro de Clases
# ---------------------------------------------------



    def show_carpetas(self, show_all=False):
        """Muestra la lista de carpetas en la ventana principal."""
        try:
            # Actualizar el estado actual de la vista
            self.show_all_carpetas = show_all
            
            # Limpiar contenido principal
            self._clear_main_content()
            
            # Actualizar título
            self._update_title_label("Carpetas de Libros de Clase")
            
            # Frame para botones
            button_frame = ttk.Frame(self.main_frame)
            button_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Botón para mostrar todas las carpetas
            mostrar_todas_button = ttk.Button(
                button_frame,
                text="Mostrar Todas",
                command=lambda: self.show_carpetas(show_all=True),
                style='Action.TButton'
            )
            mostrar_todas_button.pack(side=tk.LEFT, padx=2)
            # Botón para cambiar estado
            cambiar_estado_button = ttk.Button(
                button_frame,
                text="Cambiar Estado",
                command=self.toggle_estado_carpeta,
                style='Action.TButton'
            )
            cambiar_estado_button.pack(side=tk.LEFT, padx=2)
            
            # Botón para eliminar una carpeta seleccionada
            eliminar_button = ttk.Button(
                button_frame,
                text="Eliminar",
                command=self.delete_selected_carpeta,
                style='delete.TButton'
            )
            eliminar_button.pack(side=tk.LEFT, padx=2)
            
            # Frame para Treeview
            tree_frame = ttk.Frame(self.main_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Configurar estilo para aumentar la altura de las filas
            style = ttk.Style()
            style.configure("Custom.Treeview",
                            rowheight=30,  # Ajusta este valor según tus necesidades
                            font=('Helvetica', 9))  # Opcional: Ajusta el tamaño de la fuente
            
            # Scrollbars
            vsb = ttk.Scrollbar(tree_frame, orient="vertical")
            hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
            
            # Configurar Treeview con el estilo personalizado
            self.carpetas_tree = ttk.Treeview(
                tree_frame,
                style="Custom.Treeview",  # Aplica el estilo personalizado
                columns=(
                    "id", "numero_acta", "id_curso", "nombre_curso",
                    "fecha_inicio", "fecha_termino", "estado", 
                    "total_alumnos", "total_libros"
                ),
                show="headings",
                selectmode="browse",
                yscrollcommand=vsb.set,
                xscrollcommand=hsb.set
            )
            
            # Configurar grid
            self.carpetas_tree.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")
            hsb.grid(row=1, column=0, sticky="ew")
            
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)
            
            # Configurar scrollbars
            vsb.configure(command=self.carpetas_tree.yview)
            hsb.configure(command=self.carpetas_tree.xview)
            
            # Configurar columnas
            headers = {
                "id": ("ID", 60),
                "numero_acta": ("N° Acta", 100),
                "id_curso": ("ID Curso", 100),
                "nombre_curso": ("Nombre Curso", 400),
                "fecha_inicio": ("F. Inicio", 100),
                "fecha_termino": ("F. Término", 100),
                "estado": ("Estado", 100),
                "total_alumnos": ("Total Alumnos", 100),
                "total_libros": ("Total Libros", 100)
            }
            
            for col, (header, width) in headers.items():
                self.carpetas_tree.heading(col, text=header, anchor=tk.CENTER)
                self.carpetas_tree.column(
                    col, 
                    width=width, 
                    minwidth=50,
                    anchor=tk.W if col == "nombre_curso" else tk.CENTER
                )
            
            # Configurar tags para colores
            self.carpetas_tree.tag_configure('activo', background='#90EE90')
            self.carpetas_tree.tag_configure('finalizado', background='#FFB6C1')
            
            # Cargar datos
            carpetas = fetch_carpetas_formacion(active_only=not show_all)
            
            # Limpiar el Treeview antes de insertar nuevos datos
            for item in self.carpetas_tree.get_children():
                self.carpetas_tree.delete(item)
            
            if carpetas:
                for carpeta in carpetas:
                    fecha_inicio = carpeta[4].strftime('%Y-%m-%d') if carpeta[4] else ''
                    fecha_termino = carpeta[5].strftime('%Y-%m-%d') if carpeta[5] else ''
                    
                    values = [
                        carpeta[0],            # id_carpeta
                        carpeta[1],            # numero_acta
                        carpeta[2],            # id_curso
                        carpeta[3],            # nombre_curso
                        fecha_inicio,          # fecha_inicio
                        fecha_termino,         # fecha_termino
                        carpeta[6].upper(),    # estado
                        carpeta[7],            # total_alumnos
                        carpeta[8]             # total_libros
                    ]
                    
                    tag = 'activo' if carpeta[6].lower() == 'activo' else 'finalizado'
                    self.carpetas_tree.insert("", "end", values=values, tags=(tag,))
            
            # Binding para doble click
            self.carpetas_tree.bind("<Double-1>", self.abrir_libros_window)
            
        except Exception as e:
            print(f"Error al mostrar carpetas: {e}")
            traceback.print_exc()
            messagebox.showerror(
                "Error",
                "Error al mostrar carpetas. Consulte la consola para más detalles."
            )

    def toggle_estado_carpeta(self):
        """Cambia el estado de la carpeta entre activo y finalizado."""
        try:
            selected_item = self.carpetas_tree.selection()
            if not selected_item:
                messagebox.showwarning("Advertencia", "No se ha seleccionado ninguna carpeta.")
                return
            
            # Obtener los valores de la carpeta seleccionada
            carpeta = self.carpetas_tree.item(selected_item)['values']
            id_carpeta = carpeta[0]
            estado_actual = carpeta[6].lower()  # Índice 6 corresponde al estado
            
            # Determinar nuevo estado
            nuevo_estado = 'finalizado' if estado_actual == 'activo' else 'activo'
            
            # Confirmar cambio - Corregido el llamado a messagebox
            mensaje = f"¿Está seguro de que desea cambiar el estado de la carpeta a '{nuevo_estado.upper()}'?"
            confirm = messagebox.askyesno("Confirmar Cambio de Estado", mensaje)
            
            if not confirm:
                return
            
            # Actualizar en la base de datos
            self.actualizar_estado_carpeta(id_carpeta, nuevo_estado)
            
            # Actualizar la vista
            self.show_carpetas(show_all=self.show_all_carpetas)
            
            messagebox.showinfo("Éxito", f"El estado de la carpeta ha sido actualizado a {nuevo_estado.upper()}")
            
        except Exception as e:
            print(f"Error al cambiar estado de carpeta: {e}")
            traceback.print_exc()
            messagebox.showerror("Error", "Error al cambiar el estado de la carpeta.")

    def actualizar_estado_carpeta(self, id_carpeta, nuevo_estado):
        """Actualiza el estado de una carpeta en la base de datos y la fecha de término si corresponde."""
        try:
            conn = connect_db()
            cursor = conn.cursor()
            
            if nuevo_estado == 'finalizado':
                # Si se está finalizando, actualizamos también la fecha de término
                cursor.execute(
                    """UPDATE carpeta_libros 
                    SET estado = %s, fecha_termino = CURDATE() 
                    WHERE id_carpeta = %s""",
                    (nuevo_estado, id_carpeta)
                )
            else:
                # Si se está reactivando, limpiamos la fecha de término
                cursor.execute(
                    """UPDATE carpeta_libros 
                    SET estado = %s, fecha_termino = NULL 
                    WHERE id_carpeta = %s""",
                    (nuevo_estado, id_carpeta)
                )
            
            conn.commit()
            
        except mysql.connector.Error as err:
            print(f"Error al actualizar estado de carpeta: {err}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def delete_selected_carpeta(self):
        """Elimina la carpeta seleccionada."""
        try:
            selected_item = self.carpetas_tree.selection()
            if not selected_item:
                messagebox.showwarning("Advertencia", "No se ha seleccionado ninguna carpeta para eliminar.")
                return
            
            # Obtener los valores de la carpeta seleccionada
            carpeta = self.carpetas_tree.item(selected_item)['values']
            id_carpeta = carpeta[0]  # Asumiendo que el primer valor es id_carpeta
            
            # Confirmar eliminación
            confirm = messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar la carpeta '{carpeta[3]}'?")
            if not confirm:
                return
            
            # Realizar la eliminación en la base de datos
            self.eliminar_carpeta(id_carpeta)
            
            # Actualizar la vista
            self.show_carpetas(show_all=self.show_all_carpetas)
            
            messagebox.showinfo("Éxito", "La carpeta ha sido eliminada exitosamente.")
            
        except Exception as e:
            print(f"Error al eliminar carpeta: {e}")
            traceback.print_exc()
            messagebox.showerror("Error", "Error al eliminar la carpeta. Consulte la consola para más detalles.")

    def eliminar_carpeta(self, id_carpeta):
        """Elimina una carpeta de la base de datos."""
        try:
            conn = connect_db()
            cursor = conn.cursor()
            # Reemplazar '?' por '%s'
            cursor.execute("DELETE FROM carpeta_libros WHERE id_carpeta = %s", (id_carpeta,))
            conn.commit()
        except mysql.connector.Error as err:
            print(f"Error al eliminar carpeta de la base de datos: {err}")
            traceback.print_exc()
            messagebox.showerror("Error", "Error al eliminar la carpeta de la base de datos.")
        except Exception as e:
            print(f"Error al eliminar carpeta de la base de datos: {e}")
            traceback.print_exc()
            messagebox.showerror("Error", "Error al eliminar la carpeta de la base de datos.")
        finally:
            cursor.close()
            conn.close()


    def abrir_libros_window(self, event=None):
        """Abre la ventana de gestión de libros para la carpeta seleccionada"""
        selected = self.carpetas_tree.selection()
        if not selected:
            messagebox.showwarning("Selección requerida", "Por favor seleccione una carpeta")
            return

        carpeta_info = self.carpetas_tree.item(selected[0])['values']
        
        # Verificar si hay una instancia previa y eliminarla
        if hasattr(self, 'libro_manager') and self.libro_manager is not None:
            try:
                self.libro_manager.close_window()
            except:
                pass
            self.libro_manager = None
        
        # Crear nueva instancia
        self.libro_manager = LibrosManager(self.root)
        self.libro_manager.show_libros(carpeta_info)
        
        # Configurar cierre
        def on_closing():
            if hasattr(self, 'libro_manager') and self.libro_manager is not None:
                self.libro_manager.close_window()
                self.libro_manager = None
                
        self.libro_manager.window.protocol("WM_DELETE_WINDOW", on_closing)



#================================================================
#           Funciones de estado activo
#================================================================
    def _register_contact(self, tree):
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un alumno")
            return
            
        item = tree.item(selection[0])
        id_inscripcion = item['values'][0]

        dialog = tk.Toplevel(self.root)
        dialog.title("Registrar Contacto")
        dialog.geometry("400x500")
        dialog.grab_set()
        dialog.configure(bg="white")
        
        # Centrar la ventana
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"400x500+{x}+{y}")
        
        # Intentar cargar icono
        try:
            if os.path.exists(resource_path('assets/logo1.ico')):
                dialog.iconbitmap(resource_path('assets/logo1.ico'))
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")
        
        # Frame principal
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        ttk.Label(main_frame, text="Método de Contacto:").pack(pady=5)
        metodo = ttk.Combobox(
            main_frame, 
            values=['llamada', 'mensaje', 'correo'], 
            state='readonly',
            width=28
        )
        metodo.pack(pady=5)
        metodo.set('llamada')
        
        ttk.Label(main_frame, text="Asistencia Actual (%):").pack(pady=5)
        asistencia = ttk.Entry(main_frame, width=30)
        asistencia.pack(pady=5)
        
        ttk.Label(main_frame, text="Observaciones:").pack(pady=5)
        observacion = tk.Text(main_frame, height=10, width=35)
        observacion.pack(pady=5)
        
        def save():
            try:
                asist = float(asistencia.get())
                if not (0 <= asist <= 100):
                    raise ValueError("Asistencia debe estar entre 0 y 100")
                
                update_student_contact(
                    id_inscripcion,
                    asist,
                    metodo.get(),
                    observacion.get("1.0", "end-1c")
                )
                dialog.destroy()
                self.show_current_students()  # Recargar la vista completa
                
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        # Frame para botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=20)

        ttk.Button(
            button_frame,
            text="Cancelar",
            command=dialog.destroy,
            style='Secondary.TButton'
        ).pack(side='right', padx=5)

        ttk.Button(
            button_frame,
            text="Guardar",
            command=save,
            style='Action.TButton'
        ).pack(side='right', padx=5)

    def show_contact_history(self):
        # Obtener la selección actual
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un alumno para ver su historial")
            return
            
        item = self.tree.item(selection[0])
        id_inscripcion = item['values'][0]
        nombre_alumno = item['values'][2]

        # Crear ventana de historial
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Historial de Contactos - {nombre_alumno}")
        dialog.configure(bg="white")
        
        # Configurar tamaño y posición
        width = 800
        height = 500
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.grab_set()
        
        try:
            if os.path.exists(resource_path('assets/logo1.ico')):
                dialog.iconbitmap(resource_path('assets/logo1.ico'))
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")

        # Frame principal
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Frame para el treeview
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill='both', expand=True)

        # Scrollbars
        vscroll = ttk.Scrollbar(tree_frame, orient="vertical")
        hscroll = ttk.Scrollbar(tree_frame, orient="horizontal")

        # Crear Treeview
        history_tree = ttk.Treeview(
            tree_frame,
            selectmode="browse",
            yscrollcommand=vscroll.set,
            xscrollcommand=hscroll.set
        )

        # Configurar grid
        history_tree.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Configurar scrollbars
        vscroll.configure(command=history_tree.yview)
        hscroll.configure(command=history_tree.xview)

        # Definir columnas
        columns = ("fecha", "asistencia", "metodo", "observacion")
        headers = ("Fecha de Contacto", "Asistencia %", "Método", "Observaciones")

        history_tree.config(columns=columns, show="headings")

        # Configurar columnas
        column_widths = {
            "fecha": 150,
            "asistencia": 100,
            "metodo": 100,
            "observacion": 400
        }

        for column, header in zip(columns, headers):
            history_tree.heading(column, text=header, anchor=tk.CENTER)
            width = column_widths.get(column, 100)
            history_tree.column(column, width=width, minwidth=50, anchor=tk.CENTER)

        # Cargar datos del historial
        try:
            conn = connect_db()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    fecha_actualizacion,
                    asistencia_current,
                    metodo_contacto,
                    observacion
                FROM current_alumnos_history
                WHERE id_inscripcion = %s
                ORDER BY fecha_actualizacion DESC
            """
            
            cursor.execute(query, (id_inscripcion,))
            history = cursor.fetchall()
            cursor.close()
            conn.close()

            for record in history:
                history_tree.insert('', 'end', values=(
                    record['fecha_actualizacion'].strftime('%Y-%m-%d %H:%M:%S'),
                    f"{record['asistencia_current']:.1f}%",
                    record['metodo_contacto'] if record['metodo_contacto'] else 'N/A',
                    record['observacion'] if record['observacion'] else ''
                ))

        except Exception as e:
            print(f"Error cargando historial: {e}")
            messagebox.showerror("Error", f"Error al cargar el historial: {e}")

        # Frame para botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(
            button_frame,
            text="Cerrar",
            command=dialog.destroy,
            style='Secondary.TButton'
        ).pack(side='right', padx=5)

    def show_current_students(self):
        try:
            # Actualizar la tabla de alumnos activos
            update_current_students_table()
            
            # Limpiar el contenido principal
            self._clear_main_content()
            
            # Actualizar el título
            self._update_title_label("Alumnos Activos")
            
            # Crear frame principal
            content_frame = ttk.Frame(self.main_frame)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Frame para los botones
            button_frame = ttk.Frame(content_frame)
            button_frame.pack(fill=tk.X, pady=(0, 5))
            
            # Botones
            ttk.Button(
                button_frame,
                text="Registrar Contacto",
                command=lambda: self._register_contact(self.tree),
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=2)

            ttk.Button(
                button_frame,
                text="Ver Historial",
                command=lambda: self.show_contact_history(),
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=2)

            # Frame para el treeview
            tree_frame = ttk.Frame(content_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            
            # Scrollbars
            vscroll = ttk.Scrollbar(tree_frame, orient="vertical")
            hscroll = ttk.Scrollbar(tree_frame, orient="horizontal")

            # Crear Treeview
            self.tree = ttk.Treeview(
                tree_frame,
                selectmode="extended",
                yscrollcommand=vscroll.set,
                xscrollcommand=hscroll.set,
                style='Taller.Treeview'  # Nuevo estilo personalizado
            )

            # Configurar estilo personalizado
            style = ttk.Style()
            style.configure(
                "Taller.Treeview",
                rowheight=40,     # Aumentar altura de las filas
                font=('Segoe UI', 10)  # Opcional: ajustar fuente
            )
            
            # También podemos ajustar la altura de los encabezados
            style.configure(
                "Taller.Treeview.Heading",
                padding=10,
                font=('Segoe UI', 10, 'bold')
            )

            # Configurar grid
            self.tree.grid(row=0, column=0, sticky="nsew")
            vscroll.grid(row=0, column=1, sticky="ns")
            hscroll.grid(row=1, column=0, sticky="ew")
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            # Configurar scrollbars
            vscroll.configure(command=self.tree.yview)
            hscroll.configure(command=self.tree.xview)

            # Configurar tags para colores
            self.tree.tag_configure('contacto_reciente', background='#D4EDDA')  # Verde suave
            self.tree.tag_configure('contacto_medio', background='#FFF3CD')     # Amarillo suave
            self.tree.tag_configure('contacto_urgente', background='#F8D7DA')   # Rojo suave

            # Definir columnas
            columns = (
                "id_inscripcion", "rut", "nombre_completo", "curso", 
                "fecha_inicio", "fecha_termino", "asistencia", "ultimo_contacto", 
                "metodo_contacto"
            )
            
            headers = (
                "ID", "RUT", "Nombre Completo", "Curso",
                "F. Inicio", "F. Término", "Asistencia %", "Último Contacto",
                "Método Contacto"
            )

            # Configurar Treeview
            self.tree.config(columns=columns, show="headings")
            
            # Configurar columnas
            column_widths = {
                "id_inscripcion": 50,
                "rut": 100,
                "nombre_completo": 200,
                "curso": 200,
                "fecha_inicio": 100,
                "fecha_termino": 100,
                "asistencia": 100,
                "ultimo_contacto": 120,
                "metodo_contacto": 100
            }

            for column, header in zip(columns, headers):
                self.tree.heading(column, text=header, anchor=tk.CENTER)
                width = column_widths.get(column, 100)
                self.tree.column(column, width=width, minwidth=60, anchor=tk.CENTER)

            # Menú contextual
            self.context_menu = tk.Menu(tree_frame, tearoff=0)
            self.context_menu.add_command(label="Copiar celda", command=self._copy_selected_cell)
            self.context_menu.add_command(label="Copiar fila", command=self._copy_selected_row)
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Ver Historial", command=self.show_contact_history)

            # Bindings para el menú contextual
            self.tree.bind("<Button-3>", self._show_context_menu)
            self.tree.bind("<Button-1>", self._save_click_position)
            self.tree.bind("<ButtonRelease-3>", self._save_click_position)

            # Cargar datos
            students = fetch_active_students()
            
            for student in students:
                # Determinar color basado en la fecha de último contacto
                if student['fecha_actualizacion']:
                    days_diff = (datetime.now() - student['fecha_actualizacion']).days
                    if days_diff <= 5:
                        tag = ('contacto_reciente',)
                    elif days_diff <= 7:
                        tag = ('contacto_medio',)
                    else:
                        tag = ('contacto_urgente',)
                else:
                    tag = ('contacto_urgente',)
                
                self.tree.insert('', 'end', values=(
                    student['id_inscripcion'],
                    student['rut'],
                    student['nombre_completo'],
                    student['nombre_curso'],
                    student['fecha_inscripcion'].strftime('%Y-%m-%d'),
                    student['fecha_termino_condicional'].strftime('%Y-%m-%d'),
                    f"{student['asistencia_current']:.1f}%",
                    student['fecha_actualizacion'].strftime('%Y-%m-%d') if student['fecha_actualizacion'] else 'Sin contacto',
                    student['metodo_contacto'] if student['metodo_contacto'] else 'N/A'
                ), tags=tag)

        except Exception as e:
            print(f"Error al mostrar alumnos activos: {e}")
            messagebox.showerror("Error", f"Error al mostrar alumnos activos: {e}")

#================================================================
#                        DEUDORES
#================================================================
    def show_deudores(self):
        try:
            # Limpiar el contenido principal y actualizar el título
            # Actualizar automáticamente los deudores vencidos antes de mostrar la lista
            check_overdue_debtors()
            self._clear_main_content()
            self._update_title_label("Listado de Deudores")

            # Frame principal de contenido
            content_frame = ttk.Frame(self.main_frame)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Frame para botones de acción
            button_frame = ttk.Frame(content_frame)
            button_frame.pack(fill=tk.X, pady=(0, 5))

            # Botones de acción
            ttk.Button(
                button_frame,
                text="Nuevo Deudor",
                command=self.add_deudor_window,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                button_frame,
                text="Buscar Deudor",
                command=self.search_deudor_window,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                button_frame,
                text="Eliminar Deudor",
                command=self.delete_deudor,
                style='delete.TButton'
            ).pack(side=tk.LEFT, padx=5)

            # Frame para el Treeview y scrollbars
            tree_frame = ttk.Frame(content_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            # Configurar estilo del Treeview
            style = ttk.Style()
            style.configure("Treeview",
                            background="#ffffff",
                            foreground="black",
                            rowheight=35,
                            fieldbackground="#ffffff")
            style.configure("Treeview.Heading",
                            background="#e1e1e1",
                            foreground="black",
                            relief="flat")
            style.map('Treeview',
                      background=[('selected', '#0078D7')],
                      foreground=[('selected', 'white')])

            # Scrollbars
            vscroll = ttk.Scrollbar(tree_frame, orient="vertical")
            hscroll = ttk.Scrollbar(tree_frame, orient="horizontal")

            # Crear Treeview
            self.tree = ttk.Treeview(
                tree_frame,
                selectmode="extended",
                yscrollcommand=vscroll.set,
                xscrollcommand=hscroll.set
            )
            self.tree.grid(row=0, column=0, sticky="nsew")
            vscroll.grid(row=0, column=1, sticky="ns")
            hscroll.grid(row=1, column=0, sticky="ew")
            vscroll.configure(command=self.tree.yview)
            hscroll.configure(command=self.tree.xview)

            # Definir columnas y encabezados
            columns = ("ID", "Inscripcion", "RUT Alumno", "Fecha Registro", "Motivo", "Cuotas", "Monto", "Estado")
            headers = ("ID", "Inscripción", "RUT Alumno", "Fecha Registro", "Motivo", "Cuotas Vencidas", "Monto Total", "Estado")

            self.tree.config(columns=columns, show="headings")
            column_widths = {
                "ID": 60,
                "Inscripcion": 80,
                "RUT Alumno": 100,
                "Fecha Registro": 120,
                "Motivo": 120,
                "Cuotas": 80,
                "Monto": 100,
                "Estado": 80
            }
            for column, header in zip(columns, headers):
                self.tree.heading(column, text=header, anchor=tk.CENTER)
                width = column_widths.get(column, 100)
                self.tree.column(column, width=width, minwidth=50, anchor=tk.CENTER)

            # Obtener datos de deudores y formatearlos
            data_raw = fetch_deudores()
            formatted_data = []
            if data_raw:
                for deudor in data_raw:
                    # deudor: (id_deudor, id_inscripcion, rut_alumno, fecha_registro, motivo, cuotas, monto_total, estado)
                    fecha_registro = deudor[3].strftime('%Y-%m-%d') if deudor[3] else ''
                    monto_total = f"${deudor[6]:,.2f}"
                    row = [
                        deudor[0],
                        deudor[1],
                        deudor[2],
                        fecha_registro,
                        deudor[4],
                        deudor[5],
                        monto_total,
                        deudor[7]
                    ]
                    formatted_data.append(row)

            # Insertar datos en el Treeview con tags para diferenciar el estado
            for i, item in enumerate(formatted_data):
                tag = 'activo' if item[7].lower() == 'activo' else 'resuelto'
                row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.tree.insert("", "end", values=item, tags=(tag, row_tag))

            # Configurar colores para los tags
            self.tree.tag_configure('activo', background='#D4EDDA')    # Verde claro
            self.tree.tag_configure('resuelto', background='#F8D7DA')   # Rojo claro
            self.tree.tag_configure('evenrow', background='#f5f5f5')
            self.tree.tag_configure('oddrow', background='#ffffff')

            self.tree.update_idletasks()

        except Exception as e:
            print(f"Error al mostrar deudores: {e}")
            import traceback
            traceback.print_exc()

    def center_window(self,window, width, height):
        """
        Centra la ventana en la pantalla con el ancho y alto especificados.
        """
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    def add_deudor_window(self):
        """Muestra una ventana para agregar un nuevo deudor."""
        add_win = tk.Toplevel(self.main_frame)
        add_win.title("Agregar Deudor")
        add_win.grab_set()
        add_win.iconbitmap(resource_path('assets/logo1.ico'))
        # Define el tamaño de la ventana y céntrala
        window_width = 400
        window_height = 300
        self.center_window(add_win, window_width, window_height)

        frame = ttk.Frame(add_win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Campos para ingresar datos del deudor
        ttk.Label(frame, text="ID Inscripción (opcional):").grid(row=0, column=0, sticky=tk.W, pady=5)
        id_inscripcion_entry = ttk.Entry(frame)
        id_inscripcion_entry.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="RUT Alumno:").grid(row=1, column=0, sticky=tk.W, pady=5)
        rut_entry = ttk.Entry(frame)
        rut_entry.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Motivo:").grid(row=2, column=0, sticky=tk.W, pady=5)
        motivo_var = tk.StringVar()
        motivo_combo = ttk.Combobox(frame, textvariable=motivo_var, state="readonly")
        motivo_combo['values'] = ("CuotasVencidas", "NoPago")
        motivo_combo.grid(row=2, column=1, pady=5)
        motivo_combo.current(0)

        ttk.Label(frame, text="Cuotas Vencidas:").grid(row=3, column=0, sticky=tk.W, pady=5)
        cuotas_entry = ttk.Entry(frame)
        cuotas_entry.grid(row=3, column=1, pady=5)

        ttk.Label(frame, text="Monto Total:").grid(row=4, column=0, sticky=tk.W, pady=5)
        monto_entry = ttk.Entry(frame)
        monto_entry.grid(row=4, column=1, pady=5)

        # Mostrar estado predeterminado (activo)
        ttk.Label(frame, text="Estado: Activo").grid(row=5, column=0, sticky=tk.W, pady=5)

        def guardar_deudor():
            try:
                # Obtener el texto del campo, eliminando espacios en blanco
                id_inscripcion_val = id_inscripcion_entry.get().strip()

                # Verificar si el usuario ingresó algo
                if id_inscripcion_val:
                    # Manejar el caso en que lo ingresado no sea un número
                    try:
                        id_inscripcion = int(id_inscripcion_val)
                    except ValueError:
                        messagebox.showerror(
                            "Error",
                            "El campo 'ID Inscripción' debe ser un número válido o dejarse vacío.",
                            parent=add_win
                        )
                        return
                else:
                    # Campo vacío => None
                    id_inscripcion = None

                rut_alumno = rut_entry.get().strip()
                motivo = motivo_var.get()

                # Validar cuotas vencidas
                cuotas_val = cuotas_entry.get().strip()
                if not cuotas_val:
                    cuotas = 0
                else:
                    cuotas = int(cuotas_val)

                # Validar monto total
                monto_val = monto_entry.get().strip()
                if not monto_val:
                    monto = 0.0
                else:
                    monto = float(monto_val)

                estado = "activo"

                # Llamar a la función que inserta el deudor en la BD
                if insert_deudor(id_inscripcion, rut_alumno, motivo, cuotas, monto, estado):
                    messagebox.showinfo("Éxito", "Deudor agregado exitosamente.")
                    add_win.destroy()
                    self.show_deudores()  # Actualiza la lista
                else:
                    messagebox.showerror("Error", "No se pudo agregar el deudor.")
            except Exception as ex:
                messagebox.showerror("Error", f"Error al guardar deudor: {ex}", parent=add_win)

        ttk.Button(frame, text="Guardar", command=guardar_deudor, style='Action.TButton') \
            .grid(row=6, column=0, columnspan=2, pady=10)

    def search_deudor_window(self):
        """Muestra una ventana para buscar deudores por RUT o ID de inscripción."""
        search_win = tk.Toplevel(self.main_frame)
        search_win.title("Buscar Deudor")
        search_win.grab_set()
        # Define el tamaño y centra la ventana de búsqueda
        window_width = 400
        window_height = 150
        self.center_window(search_win, window_width, window_height)
        
        search_win.iconbitmap(resource_path('assets/logo1.ico'))

        frame = ttk.Frame(search_win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Buscar por RUT o ID Inscripción:") \
            .grid(row=0, column=0, sticky=tk.W, pady=5)
        search_entry = ttk.Entry(frame)
        search_entry.grid(row=0, column=1, pady=5)

        def buscar():
            term = search_entry.get().strip()
            if not term:
                messagebox.showwarning("Atención", "Ingrese un término de búsqueda.", parent=search_win)
                return

            # Se llama a la función fetch_deudores con el filtro
            data = fetch_deudores(search_term=term)
            
            # Limpia el TreeView principal
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Si hay datos, los formateamos y los insertamos
            if data:
                formatted_data = []
                for deudor in data:
                    # deudor = (id_deudor, id_inscripcion, rut_alumno, fecha_registro, motivo,
                    #           numero_cuotas_vencidas, monto_total, estado)
                    fecha_registro = deudor[3].strftime('%Y-%m-%d') if deudor[3] else ''
                    monto_total = f"${deudor[6]:,.2f}"
                    row = [
                        deudor[0],   # id_deudor
                        deudor[1],   # id_inscripcion
                        deudor[2],   # rut_alumno
                        fecha_registro,
                        deudor[4],   # motivo
                        deudor[5],   # numero_cuotas_vencidas
                        monto_total, # monto_total
                        deudor[7]    # estado
                    ]
                    formatted_data.append(row)
                
                for i, item in enumerate(formatted_data):
                    tag = 'activo' if item[7].lower() == 'activo' else 'resuelto'
                    row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                    self.tree.insert("", "end", values=item, tags=(tag, row_tag))
            else:
                # Si no se encontraron resultados, podrías opcionalmente mostrar un aviso
                messagebox.showinfo("Sin resultados", "No se encontraron deudores con ese criterio.", parent=search_win)

            # Cerrar la ventana de búsqueda para mostrar el TreeView actualizado en la ventana principal
            search_win.destroy()

        ttk.Button(frame, text="Buscar", command=buscar, style='Action.TButton') \
            .grid(row=1, column=0, columnspan=2, pady=10)
    
    def delete_deudor(self):
        """Elimina el/los deudor(es) seleccionado(s) en el Treeview."""
        try:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("Atención", "Seleccione un deudor para eliminar.")
                return
            confirm = messagebox.askyesno("Confirmar", "¿Está seguro de eliminar el deudor seleccionado?")
            if confirm:
                for item in selected:
                    values = self.tree.item(item, 'values')
                    deudor_id = values[0]
                    delete_deudor_db(deudor_id)
                    self.tree.delete(item)
                messagebox.showinfo("Éxito", "Deudor(es) eliminado(s) correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar deudor: {e}")

# ------------------------ MAIN ------------------------
if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.iconbitmap(resource_path(resource_path('assets/logo1.ico')))
        small_icon_path = os.path.abspath(os.path.join('assets', 'logo2.ico'))
        root.call('wm', 'iconphoto', root._w, tk.PhotoImage(file=small_icon_path))
    except Exception as e:
        print(f"Error al cargar íconos: {e}")

    app = App(root)
    root.mainloop()
