import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import os
from docxtpl import DocxTemplate
from path_utils import resource_path
# Importamos las funciones necesarias para tramitaciones
from database.queries import (
    connect_db,
    fetch_alumno_curso_inscripcion,
    get_or_create_tramitacion,        
    create_document_for_tramitacion   
)

class TituloNacionalWindow(ttk.Frame):
    def __init__(self, parent, connection=None):
        """
        Inicializa la ventana de Título Nacional.
        
        Args:
            parent: Ventana padre (Toplevel o root)
            connection: Conexión opcional a la base de datos
        """
        super().__init__(parent)
        self.parent = parent
        self.connection = connection

        # Configurar ícono de la ventana
        try:
            self.parent.iconbitmap(resource_path("assets/logo1.ico"))
        except Exception:
            pass

        # Ruta de la plantilla Word
        self.template_path = resource_path("formatos/titulo_nacional_template.docx")

        # Variables de la interfaz
        self.id_inscripcion_var = tk.StringVar()
        self.especialidad_var = tk.StringVar(value="CUBIERTA")

        # Variables para datos del alumno
        self.nombre_completo = ""
        self.rut = ""

        self.setup_ui()
        self.pack(fill='both', expand=True)

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

    def setup_ui(self):
        """Configura la interfaz gráfica de la ventana"""
        self.parent.title("Título Nacional - SPS")
        
        # Frame principal con padding
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(side='top', fill='x')

        # 1. Sección ID Inscripción
        ttk.Label(main_frame, text="ID Inscripción:").grid(
            row=0, column=0, padx=5, pady=5, sticky='e'
        )
        ttk.Entry(
            main_frame, 
            textvariable=self.id_inscripcion_var, 
            width=20
        ).grid(row=0, column=1, padx=5, pady=5, sticky='w')

        ttk.Button(
            main_frame, 
            text="Buscar",style="Action.TButton", 
            command=self.cargar_datos_bd
        ).grid(row=0, column=2, padx=5, pady=5, sticky='w')

        # 2. Sección Especialidad
        ttk.Label(main_frame, text="Especialidad:").grid(
            row=1, column=0, padx=5, pady=5, sticky='e'
        )
        combo_especialidad = ttk.Combobox(
            main_frame,
            textvariable=self.especialidad_var,
            values=["CUBIERTA", "MAQUINA"],
            state="readonly",
            width=18
        )
        combo_especialidad.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        # 3. Marco de información del alumno
        info_frame = ttk.LabelFrame(main_frame, text="Datos del Alumno", padding=10)
        info_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=10, sticky='ew')

        self.lbl_nombre = ttk.Label(
            info_frame, 
            text="Nombre: --", 
            font=("Arial", 10)
        )
        self.lbl_nombre.pack(anchor='w', pady=2)

        self.lbl_rut = ttk.Label(
            info_frame, 
            text="RUT: --", 
            font=("Arial", 10)
        )
        self.lbl_rut.pack(anchor='w', pady=2)

        # 4. Frame de botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=10, sticky='e')

        ttk.Button(
            btn_frame, 
            text="Generar Documento",style="Action.TButton",
            command=self.generar_documento
        ).pack(side='right', padx=5)

        ttk.Button(
            btn_frame, 
            text="Limpiar",style="delete.TButton",
            command=self.limpiar_formulario
        ).pack(side='right', padx=5)

    def cargar_datos_bd(self):
        """Carga los datos del alumno desde la base de datos"""
        ins_str = self.id_inscripcion_var.get().strip()
        if not ins_str:
            messagebox.showerror("Error", "Debe ingresar un ID de inscripción.")
            return

        try:
            id_inscripcion = int(ins_str)
        except ValueError:
            messagebox.showerror("Error", "El ID de inscripción debe ser un número.")
            return

        data = fetch_alumno_curso_inscripcion(id_inscripcion)
        if not data:
            messagebox.showwarning(
                "Sin datos", 
                "No se encontró información para esa inscripción."
            )
            self.limpiar_datos_alumno()
            return

        self.nombre_completo = data["nombre_alumno"]
        self.rut = data["rut_alumno"]

        self.actualizar_labels_alumno()

    def generar_documento(self):
        """
        Genera el Título Nacional y lo registra en tramitaciones:
        1) Verifica datos del alumno
        2) Crea/obtiene tramitación
        3) Registra documento en tipos_tramite
        4) Genera documento Word
        5) Cierra ventana
        """
        if not self.validar_datos():
            return

        # Conexión a la base de datos
        conn = self.connection or connect_db()
        if not conn:
            messagebox.showerror("Error", "No hay conexión a la base de datos.")
            return

        try:
            # Obtener ID de inscripción
            id_ins = int(self.id_inscripcion_var.get().strip())

            # 1. Crear o obtener tramitación
            id_tramitacion = get_or_create_tramitacion(conn, id_ins)

            # 2. Crear documento en tipos_tramite
            id_tipo_tramite, doc_num = create_document_for_tramitacion(
                conn, 
                id_tramitacion, 
                "TITULO NACIONAL"
            )

            # 3. Generar documento Word
            doc = self.crear_documento_word(doc_num)
            if not doc:
                return

            # 4. Guardar documento
            if self.guardar_documento(doc, doc_num):
                self.mostrar_mensaje_exito(id_tramitacion, id_tipo_tramite, doc_num)
                self.parent.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar documento: {str(e)}")

    def validar_datos(self):
        """Valida que existan los datos necesarios del alumno"""
        if not self.nombre_completo or not self.rut:
            messagebox.showerror(
                "Error", 
                "No hay datos del alumno. Presione 'Buscar' primero."
            )
            return False
        return True

    def crear_documento_word(self, doc_num):
        """Crea el documento Word con los datos del contexto"""
        try:
            fecha_emi_str = date.today().strftime("%d-%m-%Y")
            context = {
                "nombre_completo": self.nombre_completo,
                "rut": self.rut,
                "especialidad": self.especialidad_var.get(),
                "fecha_emi": fecha_emi_str,
                "num_doc": doc_num
            }

            doc = DocxTemplate(self.template_path)
            doc.render(context)
            return doc
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear documento Word: {str(e)}")
            return None

    def guardar_documento(self, doc, doc_num):
        """Guarda el documento Word en la ubicación seleccionada"""
        try:
            default_filename = f"titulon_{doc_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            output_path = filedialog.asksaveasfilename(
                defaultextension=".docx",
                filetypes=[("Documento Word", "*.docx")],
                initialfile=default_filename,
                title="Guardar documento como"
            )
            
            if not output_path:
                return False

            doc.save(output_path)
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar documento: {str(e)}")
            return False

    def mostrar_mensaje_exito(self, id_tramitacion, id_tipo_tramite, doc_num):
        """Muestra mensaje de éxito con los detalles del documento generado"""
        messagebox.showinfo(
            "Éxito",
            f"Documento guardado exitosamente\n\n"
            f"Detalles:\n"
            f"- Tramitación #{id_tramitacion}\n"
            f"- Tipo Trámite #{id_tipo_tramite}\n"
            f"- Documento N° {doc_num}"
        )

    def limpiar_formulario(self):
        """Limpia todos los campos del formulario"""
        self.id_inscripcion_var.set("")
        self.especialidad_var.set("CUBIERTA")
        self.limpiar_datos_alumno()

    def limpiar_datos_alumno(self):
        """Limpia los datos del alumno y actualiza las etiquetas"""
        self.nombre_completo = ""
        self.rut = ""
        self.actualizar_labels_alumno()

    def actualizar_labels_alumno(self):
        """Actualiza las etiquetas con la información del alumno"""
        self.lbl_nombre.config(text=f"Nombre: {self.nombre_completo or '--'}")
        self.lbl_rut.config(text=f"RUT: {self.rut or '--'}")