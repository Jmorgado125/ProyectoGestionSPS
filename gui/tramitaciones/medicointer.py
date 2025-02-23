import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import os
from docxtpl import DocxTemplate
from path_utils import resource_path
# IMPORTAMOS LAS FUNCIONES que CREAN el registro en la tabla tramitaciones/tipos_tramite
from database.queries import (
    connect_db,
    fetch_alumno_curso_inscripcion,
    get_or_create_tramitacion,        # para obtener/crear la fila en 'tramitaciones'
    create_document_for_tramitacion   # para insertar el doc en 'tipos_tramite'
)

class MedicoInterWindow(ttk.Frame):
    def __init__(self, parent, connection=None):
        """
        parent: Toplevel o la ventana raíz
        connection: la conexión a tu BD
        """
        super().__init__(parent)
        self.parent = parent
        self.connection = connection

        # Tratar de establecer el ícono
        try:
            self.parent.iconbitmap(resource_path("assets/logo1.ico"))
        except:
            pass

        # Plantilla .docx
        self.template_path = resource_path("formatos/medico_inter_template.docx")
        # Variables
        self.id_inscripcion_var = tk.StringVar()
        self.especialidad_var = tk.StringVar(value="CUBIERTA")

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
        self.parent.title("Documento Médico Internacional")

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(side='top', fill='x')

        # ID Inscripción
        ttk.Label(main_frame, text="ID Inscripción:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        ttk.Entry(main_frame, textvariable=self.id_inscripcion_var, width=20).grid(
            row=0, column=1, padx=5, pady=5, sticky='w'
        )

        ttk.Button(
            main_frame, 
            text="Buscar",style="Action.TButton", 
            command=self.cargar_datos_bd
        ).grid(row=0, column=2, padx=5, pady=5, sticky='w')

        # Especialidad
        ttk.Label(main_frame, text="Especialidad:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        combo_especialidad = ttk.Combobox(
            main_frame,
            textvariable=self.especialidad_var,
            values=["CUBIERTA", "MAQUINA"],
            state="readonly",
            width=18
        )
        combo_especialidad.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        # Recuadro Info Alumno
        info_frame = ttk.LabelFrame(main_frame, text="Datos del Alumno", padding=10)
        info_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=10, sticky='ew')

        self.lbl_nombre = ttk.Label(info_frame, text="Nombre: --", font=("Arial", 10))
        self.lbl_nombre.pack(anchor='w', pady=2)

        self.lbl_rut = ttk.Label(info_frame, text="RUT: --", font=("Arial", 10))
        self.lbl_rut.pack(anchor='w', pady=2)

        # Botones
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
        """
        Obtiene los datos del alumno (nombre/rut) para la inscripción
        usando fetch_alumno_curso_inscripcion.
        """
        ins_str = self.id_inscripcion_var.get().strip()
        if not ins_str:
            messagebox.showerror("Error", "Debe ingresar un ID de inscripción.")
            return

        try:
            id_ins = int(ins_str)
        except ValueError:
            messagebox.showerror("Error", "El ID de inscripción debe ser un número.")
            return

        data = fetch_alumno_curso_inscripcion(id_ins)
        if not data:
            messagebox.showwarning("Sin datos", "No se encontró info para esa inscripción.")
            self.lbl_nombre.config(text="Nombre: --")
            self.lbl_rut.config(text="RUT: --")
            return

        self.nombre_completo = data["nombre_alumno"]
        self.rut = data["rut_alumno"]

        self.lbl_nombre.config(text=f"Nombre: {self.nombre_completo}")
        self.lbl_rut.config(text=f"RUT: {self.rut}")

    def generar_documento(self):
        """
        1) Verifica datos del alumno.
        2) get_or_create_tramitacion => para la carpeta de tramites
        3) create_document_for_tramitacion => crea fila en tipos_tramite, obtiene doc_num
        4) Genera doc Word con docxtpl
        5) Cierra la ventana
        """
        if not self.nombre_completo or not self.rut:
            messagebox.showerror("Error", 
                "No hay datos del alumno. Presione 'Buscar' primero.")
            return

        # Conexión
        conn = self.connection or connect_db()
        if not conn:
            messagebox.showerror("Error", "No hay conexión a BD.")
            return

        try:

            # Tomamos la inscripcion
            id_ins_str = self.id_inscripcion_var.get().strip()
            id_ins = int(id_ins_str)

            # 1) Obtenemos/creamos la "carpeta" en tramitaciones
            id_tramitacion = get_or_create_tramitacion(conn, id_ins)

            # 2) Creamos la fila del documento en 'tipos_tramite'
            #    doc_type_name = "MEDICOINTER"
            id_tipo_tramite, doc_num = create_document_for_tramitacion(conn, id_tramitacion, "TITULO INTERNACIONAL")

            # 3) Generamos el doc Word
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

            default_filename = f"medicointer_{doc_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            output_path = filedialog.asksaveasfilename(
                defaultextension=".docx",
                filetypes=[("Documento Word", "*.docx")],
                initialfile=default_filename,
                title="Guardar documento como"
            )
            if not output_path:
                return

            doc.save(output_path)

            messagebox.showinfo(
                "Éxito",
                f"Documento guardado en:\n{output_path}\n"
                f"Tramitación #{id_tramitacion}, tipos_tramite #{id_tipo_tramite}, doc_num={doc_num}."
            )

            # Cierra la ventana
            self.parent.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar documento: {str(e)}")

    def limpiar_formulario(self):
        self.id_inscripcion_var.set("")
        self.especialidad_var.set("CUBIERTA")
        self.nombre_completo = ""
        self.rut = ""

        self.lbl_nombre.config(text="Nombre: --")
        self.lbl_rut.config(text="RUT: --")
