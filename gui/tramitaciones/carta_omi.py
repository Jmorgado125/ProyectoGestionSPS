import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import os
from docxtpl import DocxTemplate
from path_utils import resource_path
from database.db_config import connect_db
from database.queries import (
    fetch_omi_courses,
    fetch_inscription,
    get_or_create_tramitacion,
    create_document_for_tramitacion
)

class OMICertificationWindow(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # Configuración de la ventana
        try:
            self.parent.iconbitmap(resource_path("assets/logo1.ico"))
        except:
            pass

        self.template_path = resource_path("formatos/carta_omi_template.docx")
        self.rut_var = tk.StringVar()
        self.student_data = None
        
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
        """Configura la interfaz de usuario"""
        self.parent.title("Certificación OMI")
        
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # RUT input
        rut_frame = ttk.Frame(main_frame)
        rut_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(rut_frame, text="RUT Alumno:").pack(side='left', padx=(0, 10))
        ttk.Entry(rut_frame, textvariable=self.rut_var, width=15).pack(side='left', padx=(0, 10))
        ttk.Button(rut_frame, text="Buscar",style="Action.TButton", command=self.search_student).pack(side='left')

        # Información del alumno
        info_frame = ttk.LabelFrame(main_frame, text="Datos del Alumno", padding=10)
        info_frame.pack(fill='x', pady=(0, 15))
        
        self.lbl_nombre = ttk.Label(info_frame, text="Nombre: --")
        self.lbl_nombre.pack(anchor='w')

        # Frame para cursos
        courses_frame = ttk.LabelFrame(main_frame, text="Cursos de Competencia", padding=10)
        courses_frame.pack(fill='both', expand=True)

        # Treeview y scrollbar
        tree_frame = ttk.Frame(courses_frame)
        tree_frame.pack(fill='both', expand=True)
        
        # Configurar el Treeview
        self.courses_tree = ttk.Treeview(tree_frame, show='headings', height=8)
        
        # Definir las columnas
        self.courses_tree["columns"] = ("inscripcion", "id", "nombre", "acta")
        
        # Configurar columnas
        self.courses_tree.column("inscripcion", width=0, stretch=False)  # Oculta esta columna
        self.courses_tree.column("id", width=100, anchor="center")
        self.courses_tree.column("nombre", width=300)
        self.courses_tree.column("acta", width=100, anchor="center")
        
        # Configurar encabezados
        self.courses_tree.heading("inscripcion", text="ID Inscripción")
        self.courses_tree.heading("id", text="ID Curso")
        self.courses_tree.heading("nombre", text="Nombre del Curso")
        self.courses_tree.heading("acta", text="N° Acta")

        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.courses_tree.yview)
        self.courses_tree.configure(yscrollcommand=scrollbar.set)
        
        self.courses_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(15, 0))
        
        ttk.Button(btn_frame, text="Generar Certificación",style="Action.TButton",
                  command=self.generate_certification).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Limpiar",style="delete.TButton",
                  command=self.clear_form).pack(side='right', padx=5)



    def search_student(self):
        """Busca al alumno y sus cursos de competencia"""
        rut = self.rut_var.get().strip()
        if not rut:
            messagebox.showerror("Error", "Debe ingresar un RUT")
            return

        try:
            alumno, cursos = fetch_omi_courses(rut)
            
            if not alumno:
                messagebox.showwarning("Sin datos", "No se encontró el alumno")
                self.clear_form()
                return

            # Guardar datos del alumno
            self.student_data = {
                'rut': alumno[0],
                'nombre': alumno[1],
                'apellido': alumno[2]
            }

            # Actualizar nombre en la interfaz
            nombre_completo = f"{alumno[1]} {alumno[2]}"
            self.lbl_nombre.config(text=f"Nombre: {nombre_completo}")

            # Limpiar y actualizar tabla de cursos
            for item in self.courses_tree.get_children():
                self.courses_tree.delete(item)

            if not cursos:
                messagebox.showinfo("Información", "El alumno no tiene cursos de competencia registrados")
                return

            # Insertar cursos en la tabla
            for curso in cursos:
                self.courses_tree.insert('', 'end', values=(
                    curso[0],  # id_inscripcion (oculto)
                    curso[1],  # id_curso
                    curso[2],  # nombre_curso
                    curso[3]   # numero_acta
                ))

        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar datos: {str(e)}")

    def generate_certification(self):
        """Genera el documento de certificación OMI"""
        if not self.student_data:
            messagebox.showerror("Error", "No hay datos del alumno")
            return

        selection = self.courses_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Debe seleccionar un curso")
            return

        try:
            # Obtener datos del curso seleccionado
            valores = self.courses_tree.item(selection[0])['values']
            id_inscripcion = valores[0]  # Primera columna (oculta)
            id_curso = valores[1]
            numero_acta = valores[3]

            conn = connect_db()
            if not conn:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos")
                return

            # Crear tramitación usando id_inscripcion
            id_tramitacion = get_or_create_tramitacion(conn,id_inscripcion)

            # Crear documento
            doc_type = f"OMI-{id_curso}"
            id_tipo_tramite, doc_num = create_document_for_tramitacion(conn, id_tramitacion, doc_type)

            # Preparar datos para la plantilla
            context = {
                "num_doc": doc_num,
                "fecha_emi": date.today().strftime("%d-%m-%Y"),
                "nombre_completo": f"{self.student_data['nombre']} {self.student_data['apellido']}",
                "rut": self.student_data['rut'],
                "n_acta": numero_acta,
                "id_cur": id_curso
            }

            # Generar documento
            doc = DocxTemplate(self.template_path)
            doc.render(context)

            # Guardar documento
            default_filename = f"omi_cert_{doc_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            output_path = filedialog.asksaveasfilename(
                defaultextension=".docx",
                filetypes=[("Documento Word", "*.docx")],
                initialfile=default_filename,
                title="Guardar certificación como"
            )
            
            if output_path:
                doc.save(output_path)
                messagebox.showinfo(
                    "Éxito",
                    f"Certificación guardada en:\n{output_path}\n"
                    f"Tramitación #{id_tramitacion}, tipos_tramite #{id_tipo_tramite}, doc_num={doc_num}"
                )
                self.parent.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar certificación: {str(e)}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def clear_form(self):
        """Limpia el formulario"""
        self.rut_var.set("")
        self.student_data = None
        self.lbl_nombre.config(text="Nombre: --")
        for item in self.courses_tree.get_children():
            self.courses_tree.delete(item)