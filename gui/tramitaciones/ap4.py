import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from path_utils import resource_path

from database.queries import get_apendice4_data

class Apendice4Window(ttk.Frame):
    def __init__(self, parent):
        """
        Inicializa la ventana para generar el Apéndice 4.
        """
        super().__init__(parent)
        self.parent = parent
        try:
            self.parent.iconbitmap(resource_path('assets/logo2.ico'))
        except Exception as e:
            print(f"Error al cargar íconos: {e}")
        
        # Ruta de la plantilla .docx
        self.template_path = resource_path('formatos/apendice4_template.docx')
        
        # Variables para almacenar información del curso
        self.nombre_curso = ""
        self.fecha_inicio = None
        self.fecha_termino = None
        self.horas_cronologicas = None
        self.horas_pedagogicas = None

        # Lista donde se almacenará la información de los alumnos
        self.alumnos_data = []
        
        # Variable para almacenar la firma (ruta de imagen)
        self.firma_path = ""
        
        # Construcción de la interfaz
        self.setup_ui()
        self.pack(fill='both', expand=True)
  
    def setup_styles(self):
        style = ttk.Style()
        style.configure('Action.TButton',
                        font=('Helvetica', 10, 'bold'),
                        padding=(10, 5),
                        background='#00239c',
                        foreground='white',
                        relief='raised',
                        borderwidth=1)
        style.map('Action.TButton',
                  background=[('active', '#001970'),
                              ('pressed', '#00239c')],
                  foreground=[('active', 'white'),
                              ('pressed', 'white')],
                  relief=[('pressed', 'sunken')])
        
        style.configure('delete.TButton',
                        font=('Helvetica', 10, 'bold'),
                        padding=(10, 5),
                        background='#b50707',
                        foreground='white',
                        relief='raised',
                        borderwidth=1)
        style.map('delete.TButton',
                  background=[('active', '#990606'),
                              ('pressed', '#b50707')],
                  foreground=[('active', 'white'),
                              ('pressed', 'white')],
                  relief=[('pressed', 'sunken')])
          
    def setup_ui(self):
        """Crea y dispone todos los widgets en la ventana."""
        # Frame superior: datos de acta, año, firma, relatores, horarios, observaciones y botones
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(side='top', fill='x')
        
        # --- FILA 0: Número de Acta y Año ---
        ttk.Label(top_frame, text="Número de Acta:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.acta_var = tk.StringVar()
        self.acta_entry = ttk.Entry(top_frame, textvariable=self.acta_var, width=20)
        self.acta_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(top_frame, text="Año:").grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.anio_var = tk.StringVar()
        current_year = datetime.now().year
        years = [str(y) for y in range(2000, current_year + 1)]
        self.anio_combo = ttk.Combobox(top_frame, textvariable=self.anio_var, values=years, width=6, state="readonly")
        self.anio_combo.grid(row=0, column=3, padx=5, pady=5, sticky='w')
        self.anio_combo.set(str(current_year))
        
        buscar_btn = ttk.Button(top_frame, text="Buscar", style='Action.TButton', command=self.cargar_datos_bd)
        buscar_btn.grid(row=0, column=4, padx=5, pady=5, sticky='w')
        
        # --- FILA 1: Selección de Firma ---
        firma_frame = ttk.LabelFrame(top_frame, text="Firma del Relator", padding=5)
        firma_frame.grid(row=1, column=0, columnspan=5, sticky='ew', padx=5, pady=5)
        ttk.Button(firma_frame, text="Seleccionar Firma", style='Action.TButton', command=self.seleccionar_firma)\
            .grid(row=0, column=0, padx=5, pady=5)
        self.firma_label = ttk.Label(firma_frame, text="Ningún archivo seleccionado", wraplength=150)
        self.firma_label.grid(row=0, column=1, padx=5, pady=5)
        
        # --- FILA 2: Relatores ---
        relatores_frame = ttk.LabelFrame(top_frame, text="Relatores", padding=5)
        relatores_frame.grid(row=2, column=0, columnspan=5, sticky='ew', padx=5, pady=5)
        self.relatores_vars = [tk.StringVar() for _ in range(4)]
        for i in range(4):
            ttk.Label(relatores_frame, text=f"Relator {i+1}:").grid(row=i, column=0, padx=5, pady=2, sticky='e')
            ttk.Entry(relatores_frame, textvariable=self.relatores_vars[i], width=30)\
                .grid(row=i, column=1, padx=5, pady=2, sticky='w')
        
        # --- FILA 3: Horarios y exámenes ---
        middle_frame = ttk.Frame(top_frame)
        middle_frame.grid(row=3, column=0, columnspan=5, sticky='ew', padx=5, pady=5)
        
        ttk.Label(middle_frame, text="Horario Teóricas:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.horario_teoricas_var = tk.StringVar()
        ttk.Entry(middle_frame, textvariable=self.horario_teoricas_var, width=50)\
            .grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(middle_frame, text="Detalle Prácticas:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.detalle_practicas_var = tk.StringVar()
        ttk.Entry(middle_frame, textvariable=self.detalle_practicas_var, width=50)\
            .grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(middle_frame, text="Examen Teórico:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.detalle_ex_teo_var = tk.StringVar()
        ttk.Entry(middle_frame, textvariable=self.detalle_ex_teo_var, width=50)\
            .grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(middle_frame, text="Examen Práctico:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.detalle_ex_prac_var = tk.StringVar()
        ttk.Entry(middle_frame, textvariable=self.detalle_ex_prac_var, width=50)\
            .grid(row=3, column=1, padx=5, pady=5)
        
        # --- FILA 4: Observaciones ---
        obs_frame = ttk.LabelFrame(top_frame, text="Observaciones", padding=5)
        obs_frame.grid(row=4, column=0, columnspan=5, sticky='ew', padx=5, pady=5)
        self.observaciones_txt = tk.Text(obs_frame, height=3)
        self.observaciones_txt.pack(fill='x', expand=True)
        
        # --- FILA 5: Botones finales ---
        btns_frame = ttk.Frame(top_frame)
        btns_frame.grid(row=5, column=0, columnspan=5, padx=5, pady=10, sticky='e')
        ttk.Button(btns_frame, text="Limpiar", style="delete.TButton", command=self.limpiar_formulario)\
            .pack(side='right', padx=5)
        ttk.Button(btns_frame, text="Vista Previa", style="Action.TButton", command=self.vista_previa)\
            .pack(side='right', padx=5)
        ttk.Button(btns_frame, text="Generar Documento", style="Action.TButton", command=self.generar_documento)\
            .pack(side='right', padx=5)
        
        # --- Frame inferior: Treeview con alumnos ---
        bottom_frame = ttk.LabelFrame(self, text="Alumnos con este Acta", padding=5)
        bottom_frame.pack(side='bottom', fill='both', expand=True, padx=10, pady=10)
        
        columns = ("col_n", "col_nombre", "col_rut", "col_profesion")
        self.tree = ttk.Treeview(bottom_frame, columns=columns, show='headings', height=8)
        self.tree.heading("col_n", text="N°")
        self.tree.heading("col_nombre", text="Nombre")
        self.tree.heading("col_rut", text="RUT")
        self.tree.heading("col_profesion", text="Profesión")
        
        self.tree.column("col_n", width=40, anchor='center')
        self.tree.column("col_nombre", width=250, anchor='w')
        self.tree.column("col_rut", width=100, anchor='center')
        self.tree.column("col_profesion", width=150, anchor='w')
        self.tree.pack(fill='both', expand=True)
    
    def seleccionar_firma(self):
        """Abre el diálogo para seleccionar la imagen de la firma, sobre la ventana actual."""
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Seleccionar firma del relator",
            filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.gif"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.firma_path = file_path
            file_name = os.path.basename(file_path)
            self.firma_label.config(text=file_name)
    
    def cargar_datos_bd(self):
        """Obtiene la información del acta desde la BD y muestra los alumnos en la tabla."""
        acta_num = self.acta_var.get().strip()
        anio = self.anio_var.get().strip()
        if not acta_num:
            messagebox.showerror("Error", "Debe ingresar un número de acta para buscar.")
            return
        if not anio:
            messagebox.showerror("Error", "Debe seleccionar un año.")
            return
        
        # Limpiar la tabla y la lista local
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.alumnos_data.clear()
        
        data_bd = get_apendice4_data(acta_num, anio)
        if not data_bd:
            messagebox.showwarning("Sin datos", "No se encontró información para este número de acta.")
            return
        
        # Se utiliza la primera fila para extraer datos generales (curso, fechas, horas)
        row0 = data_bd[0]
        self.nombre_curso = row0["nombre_curso"]
        self.fecha_inicio = row0["fecha_inicio"]
        self.fecha_termino = row0["fecha_termino"]
        self.horas_cronologicas = row0.get("horas_cronologicas", "")
        self.horas_pedagogicas = row0.get("horas_pedagogicas", "")
        
        # Agregar cada alumno a la lista y al Treeview
        for idx, row in enumerate(data_bd, start=1):
            full_name = f"{row['nombre_alumno']} {row['apellido_alumno']}"
            self.alumnos_data.append({
                "N": idx,
                "nombre_alumno": full_name,
                "rut_alumno": row["rut_alumno"],
                "profesion": row.get("profesion_alumno", "") or ""
            })
            self.tree.insert("", "end",
                             values=(idx, full_name, row["rut_alumno"], row.get("profesion_alumno", "") or ""))
    
    def generar_documento(self):
        """Genera el documento Word usando docxtpl con los datos recopilados."""
        acta = self.acta_var.get().strip()
        if not acta:
            messagebox.showerror("Error", "Debe ingresar un número de acta antes de generar el documento.")
            return
        if not self.alumnos_data or not self.nombre_curso:
            messagebox.showerror("Error", "No hay datos de BD cargados. Busque un acta válida primero.")
            return
        
        try:
            doc = DocxTemplate(self.template_path)
            context = {
                "fecha_doc": datetime.now().strftime("%d-%m-%Y"),
                "num_acta": acta,
                "nombre_curso": self.nombre_curso,
                "fecha_inicio": self.fecha_inicio.strftime("%d-%m-%Y") if self.fecha_inicio else "",
                "fecha_termino": self.fecha_termino.strftime("%d-%m-%Y") if self.fecha_termino else "",
                "horas_cronologicas": self.horas_cronologicas if self.horas_cronologicas else "",
                "horas_pedagogicas": self.horas_pedagogicas if self.horas_pedagogicas else "",
                "nombre_relator1": self.relatores_vars[0].get().strip(),
                "nombre_relator2": self.relatores_vars[1].get().strip(),
                "nombre_relator3": self.relatores_vars[2].get().strip(),
                "nombre_relator4": self.relatores_vars[3].get().strip(),
                "horario_teoricas": self.horario_teoricas_var.get().strip(),
                "detalle_clases_prac": self.detalle_practicas_var.get().strip(),
                "detalle_ex_teo": self.detalle_ex_teo_var.get().strip(),
                "detalle_ex_prac": self.detalle_ex_prac_var.get().strip(),
                "observaciones": self.observaciones_txt.get("1.0", tk.END).strip(),
                "alumnos": self.alumnos_data,
                # Se añade la firma (ajusta el ancho/alto según sea necesario)
                "firma": InlineImage(doc, self.firma_path, width=Mm(40)) if self.firma_path else ""
            }
            doc.render(context)
            
            default_filename = f"apendice4_{acta}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            output_path = filedialog.asksaveasfilename(
                defaultextension=".docx",
                filetypes=[("Documento Word", "*.docx")],
                initialfile=default_filename,
                title="Guardar documento como"
            )
            if not output_path:
                return
            doc.save(output_path)
            messagebox.showinfo("Éxito", f"Documento guardado en:\n{output_path}")
            self.winfo_toplevel().destroy()
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar documento: {str(e)}")
    
    def vista_previa(self):
        """Genera un documento temporal y lo abre, sin guardarlo de forma definitiva."""
        acta = self.acta_var.get().strip()
        if not acta:
            messagebox.showerror("Error", "Ingrese un número de acta primero.")
            return
        if not self.alumnos_data or not self.nombre_curso:
            messagebox.showerror("Error", "No hay datos de BD cargados. Busque un acta válida primero.")
            return
        
        try:
            doc = DocxTemplate(self.template_path)
            context = {
                "fecha_doc": datetime.now().strftime("%d-%m-%Y"),
                "num_acta": acta,
                "nombre_curso": self.nombre_curso,
                "fecha_inicio": self.fecha_inicio.strftime("%d-%m-%Y") if self.fecha_inicio else "",
                "fecha_termino": self.fecha_termino.strftime("%d-%m-%Y") if self.fecha_termino else "",
                "horas_cronologicas": self.horas_cronologicas if self.horas_cronologicas else "",
                "horas_pedagogicas": self.horas_pedagogicas if self.horas_pedagogicas else "",
                "nombre_relator1": self.relatores_vars[0].get().strip(),
                "nombre_relator2": self.relatores_vars[1].get().strip(),
                "nombre_relator3": self.relatores_vars[2].get().strip(),
                "nombre_relator4": self.relatores_vars[3].get().strip(),
                "horario_teoricas": self.horario_teoricas_var.get().strip(),
                "detalle_clases_prac": self.detalle_practicas_var.get().strip(),
                "detalle_ex_teo": self.detalle_ex_teo_var.get().strip(),
                "detalle_ex_prac": self.detalle_ex_prac_var.get().strip(),
                "observaciones": self.observaciones_txt.get("1.0", tk.END).strip(),
                "alumnos": self.alumnos_data,
                "firma": InlineImage(doc, self.firma_path, width=Mm(40)) if self.firma_path else ""
            }
            doc.render(context)
            
            temp_dir = os.path.join(os.getcwd(), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_filename = f"preview_ap4_{acta}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            temp_path = os.path.join(temp_dir, temp_filename)
            doc.save(temp_path)
            os.startfile(temp_path)
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar vista previa: {str(e)}")
    
    def limpiar_formulario(self):
        """Limpia todos los campos y la tabla de alumnos."""
        self.acta_var.set("")
        self.anio_var.set("")
        for var in self.relatores_vars:
            var.set("")
        self.horario_teoricas_var.set("")
        self.detalle_practicas_var.set("")
        self.detalle_ex_teo_var.set("")
        self.detalle_ex_prac_var.set("")
        self.observaciones_txt.delete("1.0", tk.END)
        
        self.nombre_curso = ""
        self.fecha_inicio = None
        self.fecha_termino = None
        self.horas_cronologicas = None
        self.horas_pedagogicas = None
        self.alumnos_data.clear()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.firma_path = ""
        self.firma_label.config(text="Ningún archivo seleccionado")
