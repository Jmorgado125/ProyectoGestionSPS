import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from path_utils import resource_path

from database.queries import (
    get_apendice6_data,
    connect_db,
    get_or_create_tramitacion,
    create_document_for_tramitacion
)

class Apendice6Window(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        try:
            self.parent.iconbitmap(resource_path('assets/logo2.ico'))
        except Exception as e:
            print(f"Error al cargar íconos: {e}")
        
        self.template_path = resource_path('formatos/ap6_template.docx')
        
        # Variables para datos del curso
        self.id_curso = ""
        self.nombre_curso = ""
        self.fecha_inicio = None
        self.fecha_termino = None
        self.horas_cronologicas = None
        self.horas_pedagogicas = None
        self.relator = tk.StringVar()
        
        # Variable para la firma del relator
        self.firma_relator_path = ""
        
        # Lista para datos de alumnos
        self.alumnos_data = []
        
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
        """Configura la interfaz de usuario usando grid layout"""
        # Frame superior para todos los controles
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(side='top', fill='x')
        
        # --- FILA 0: Búsqueda ---
        search_frame = ttk.LabelFrame(top_frame, text="Búsqueda", padding=5)
        search_frame.grid(row=0, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        
        ttk.Label(search_frame, text="N° Acta:").grid(row=0, column=0, padx=5)
        self.acta_var = tk.StringVar()
        self.acta_entry = ttk.Entry(search_frame, textvariable=self.acta_var, width=15)
        self.acta_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(search_frame, text="Año:").grid(row=0, column=2, padx=5)
        self.anio_var = tk.StringVar()
        current_year = datetime.now().year
        years = [str(year) for year in range(2000, current_year + 1)]
        self.anio_combo = ttk.Combobox(search_frame, textvariable=self.anio_var, values=years, width=6, state="readonly")
        self.anio_combo.grid(row=0, column=3, padx=5)
        self.anio_combo.set(str(current_year))
        
        ttk.Button(search_frame, text="Buscar", style='Action.TButton', command=self.cargar_datos_bd)\
            .grid(row=0, column=4, padx=5)
        
        # --- FILA 1: Relator y Firma ---
        relator_frame = ttk.Frame(top_frame)
        relator_frame.grid(row=1, column=0, columnspan=4, sticky='ew', pady=5)
        
        # Relator
        relator_label_frame = ttk.LabelFrame(relator_frame, text="Relator", padding=5)
        relator_label_frame.pack(side='left', fill='x', expand=True, padx=5)
        self.relator_entry = ttk.Entry(relator_label_frame, textvariable=self.relator, width=30)
        self.relator_entry.pack(padx=5, pady=5)
        
        # Firma
        firma_frame = ttk.LabelFrame(relator_frame, text="Firma del Relator", padding=5)
        firma_frame.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(firma_frame, text="Seleccionar Firma", style='Action.TButton', command=self.seleccionar_firma)\
            .pack(side='left', padx=5, pady=5)
        self.firma_label = ttk.Label(firma_frame, text="Ningún archivo seleccionado", wraplength=150)
        self.firma_label.pack(side='left', padx=5, pady=5)
        
        # --- FILA 2: Observaciones ---
        obs_frame = ttk.LabelFrame(top_frame, text="Observaciones", padding=5)
        obs_frame.grid(row=2, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        self.observaciones_txt = tk.Text(obs_frame, height=3)
        self.observaciones_txt.pack(fill='x', padx=5, pady=5)
        
        # --- FILA 3: Botones ---
        btn_frame = ttk.Frame(top_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, sticky='e', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Limpiar", style="delete.TButton", command=self.limpiar_formulario)\
            .pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Vista Previa", style="Action.TButton", command=self.vista_previa)\
            .pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Generar", style="Action.TButton", command=self.generar_documento)\
            .pack(side='right', padx=5)
        
        # --- Frame inferior: Tabla de alumnos ---
        table_frame = ttk.LabelFrame(self, text="Alumnos", padding=5)
        table_frame.pack(side='bottom', fill='both', expand=True, padx=10, pady=5)
        
        # Configuración del Treeview
        columns = ("num", "nombre", "rut", "titulo", "alu_titulo", "mmn")
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)
        
        self.tree.heading("num", text="N°")
        self.tree.heading("nombre", text="Nombre Completo")
        self.tree.heading("rut", text="RUT")
        self.tree.heading("titulo", text="Título Base")
        self.tree.heading("alu_titulo", text="Título a Validar")
        self.tree.heading("mmn", text="MMN")
        
        self.tree.column("num", width=50, anchor='center')
        self.tree.column("nombre", width=250)
        self.tree.column("rut", width=100, anchor='center')
        self.tree.column("titulo", width=150)
        self.tree.column("alu_titulo", width=150)
        self.tree.column("mmn", width=80, anchor='center')
        
        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar Treeview y scrollbar
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Mantener el evento de doble clic para editar
        self.tree.bind("<Double-1>", self.editar_celda)
    
    def seleccionar_firma(self):
        """Permite seleccionar el archivo de imagen para la firma del relator.
           El diálogo se abre como ventana hija (modal) de la ventana actual."""
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Seleccionar firma del relator",
            filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.gif"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.firma_relator_path = file_path
            file_name = os.path.basename(file_path)
            self.firma_label.config(text=file_name)
    
    def editar_celda(self, event):
        """Permite editar la columna 'alu_titulo' en la tabla"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        
        column = self.tree.identify_column(event.x)
        item = self.tree.focus()
        
        if column == "#5":  # Columna 'alu_titulo'
            x, y, width, height = self.tree.bbox(item, column)
            value = self.tree.item(item, "values")[4]
            
            edit_win = tk.Toplevel(self)
            edit_win.geometry(f"{width}x{height}+{x+self.winfo_x()+20}+{y+self.winfo_y()+50}")
            edit_win.overrideredirect(True)
            
            entry = ttk.Entry(edit_win)
            entry.insert(0, value)
            entry.pack(fill='both', expand=True)
            
            def guardar_cambio():
                new_value = entry.get()
                current_values = list(self.tree.item(item, "values"))
                current_values[4] = new_value
                self.tree.item(item, values=current_values)
                
                idx = int(current_values[0]) - 1
                if 0 <= idx < len(self.alumnos_data):
                    self.alumnos_data[idx]["alu_titulo"] = new_value
                
                edit_win.destroy()
            
            entry.bind("<Return>", lambda e: guardar_cambio())
            entry.bind("<Escape>", lambda e: edit_win.destroy())
            entry.bind("<FocusOut>", lambda e: guardar_cambio())
            entry.focus_set()
    
    def cargar_datos_bd(self):
        """Carga los datos desde la base de datos según el número de acta y año"""
        acta_num = self.acta_var.get().strip()
        anio = self.anio_var.get().strip()
        if not acta_num:
            messagebox.showerror("Error", "Debe ingresar un número de acta.")
            return
        if not anio:
            messagebox.showerror("Error", "Debe seleccionar un año.")
            return
        
        # Limpiar tabla y datos actuales
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.alumnos_data.clear()
        
        try:
            data_bd = get_apendice6_data(acta_num, anio)
            if not data_bd:
                messagebox.showwarning("Sin datos", "No se encontró información para este número de acta y año.")
                return
            
            # Extraer datos generales del primer registro
            row0 = data_bd[0]
            self.id_curso = row0.get("id_curso", "")
            self.nombre_curso = row0["nombre_curso"]
            self.fecha_inicio = row0["fecha_inicio"]
            self.fecha_termino = row0["fecha_termino"]
            self.horas_cronologicas = row0.get("horas_cronologicas", "")
            self.horas_pedagogicas = row0.get("horas_pedagogicas", 0)
            
            # Poblar la tabla y la lista de alumnos
            for idx, row in enumerate(data_bd, start=1):
                nombre_completo = f"{row['apellido']} {row['nombre']}"
                # Se incluye el id_inscripcion en cada registro
                alumno_dict = {
                    "N": idx,
                    "nombre_completo": nombre_completo,
                    "rut": row["rut"],
                    "titulo": row.get("profesion", ""),
                    "alu_titulo": "",
                    "mmn": row.get("mmn", ""),
                    "id_inscripcion": row.get("id_inscripcion")
                }
                self.alumnos_data.append(alumno_dict)
                
                self.tree.insert("", "end", values=(
                    idx,
                    nombre_completo,
                    row["rut"],
                    row.get("profesion", ""),
                    "",
                    row.get("mmn", "")
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {str(e)}")
    
    def generar_documento(self):
        """Genera el documento Word usando la plantilla y los datos recopilados"""
        acta = self.acta_var.get().strip()
        if not acta or not self.alumnos_data:
            messagebox.showerror("Error", "Debe buscar un acta válida primero.")
            return
        
        if not self.relator.get().strip():
            messagebox.showerror("Error", "Debe ingresar el nombre del relator.")
            return
        
        try:
            doc = DocxTemplate(self.template_path)
            context = {
                "num_acta": acta,
                "id_curso": self.id_curso,
                "dia": datetime.now().strftime("%d"),
                "mes": datetime.now().strftime("%m"),
                "año": datetime.now().strftime("%Y"),
                "relator": self.relator.get().strip(),
                "nombre_curso": self.nombre_curso,
                "fecha_inicio": self.fecha_inicio.strftime("%d-%m-%Y") if self.fecha_inicio else "",
                "fecha_termino": self.fecha_termino.strftime("%d-%m-%Y") if self.fecha_termino else "",
                "hrs_cron": self.horas_cronologicas,
                "hrs_ped": int(float(self.horas_pedagogicas)) if self.horas_pedagogicas else "",
                "observaciones": self.observaciones_txt.get("1.0", tk.END).strip(),
                "alumnos": self.alumnos_data
            }
            
            # Agregar la imagen de la firma si se seleccionó
            if self.firma_relator_path:
                context["firma_relator"] = InlineImage(doc, self.firma_relator_path, width=Mm(20))
            else:
                context["firma_relator"] = ""
            
            default_filename = f"apendice6_{acta}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            output_path = filedialog.asksaveasfilename(
                defaultextension=".docx",
                filetypes=[("Documento Word", "*.docx")],
                initialfile=default_filename,
                title="Guardar Apéndice 6"
            )
            
            if output_path:
                doc.render(context)
                doc.save(output_path)
                
                # --- Registro de tramitaciones para cada alumno ---
                conn = connect_db()
                for alumno in self.alumnos_data:
                    # Se requiere que cada alumno tenga el campo 'id_inscripcion'
                    if alumno.get("id_inscripcion"):
                        id_inscripcion = alumno["id_inscripcion"]
                        # Obtiene (o crea) la tramitación de la inscripción
                        id_tramitacion = get_or_create_tramitacion(conn, id_inscripcion)
                        # Crea el documento en la tabla tipos_tramite usando el tipo "APENDICE 6"
                        id_tipo_tramite, doc_num = create_document_for_tramitacion(conn, id_tramitacion, "APENDICE 6")
                        # Opcional: Puedes almacenar o mostrar el doc_num de cada alumno si lo necesitas
                conn.close()
                # ------------------------------------------------------
                
                messagebox.showinfo("Éxito", f"Documento guardado en:\n{output_path}")
                self.winfo_toplevel().destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar documento: {str(e)}")

    
    def vista_previa(self):
        """Genera una vista previa temporal del documento"""
        if not self.acta_var.get().strip() or not self.alumnos_data:
            messagebox.showerror("Error", "Debe buscar un acta válida primero.")
            return
        
        if not self.relator.get().strip():
            messagebox.showerror("Error", "Debe ingresar el nombre del relator.")
            return
        
        try:
            temp_dir = os.path.join(os.getcwd(), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            doc = DocxTemplate(self.template_path)
            context = {
                "num_acta": self.acta_var.get().strip(),
                "id_curso": self.id_curso,
                "dia": datetime.now().strftime("%d"),
                "mes": datetime.now().strftime("%m"),
                "año": datetime.now().strftime("%Y"),
                "relator": self.relator.get().strip(),
                "nombre_curso": self.nombre_curso,
                "fecha_inicio": self.fecha_inicio.strftime("%d-%m-%Y") if self.fecha_inicio else "",
                "fecha_termino": self.fecha_termino.strftime("%d-%m-%Y") if self.fecha_termino else "",
                "hrs_cron": self.horas_cronologicas,
                "hrs_ped": int(float(self.horas_pedagogicas)) if self.horas_pedagogicas else "",
                "observaciones": self.observaciones_txt.get("1.0", tk.END).strip(),
                "alumnos": self.alumnos_data
            }
            
            if self.firma_relator_path:
                context["firma_relator"] = InlineImage(doc, self.firma_relator_path, width=Mm(60), height=Mm(50))
            else:
                context["firma_relator"] = ""
            
            temp_filename = f"preview_ap6_{self.acta_var.get()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            doc.render(context)
            doc.save(temp_path)
            os.startfile(temp_path)
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar vista previa: {str(e)}")
    
    def limpiar_formulario(self):
        """Limpia todos los campos del formulario"""
        self.acta_var.set("")
        self.anio_var.set("")
        self.relator.set("")
        self.observaciones_txt.delete("1.0", tk.END)
        
        self.id_curso = ""
        self.nombre_curso = ""
        self.fecha_inicio = None
        self.fecha_termino = None
        self.horas_cronologicas = None
        self.horas_pedagogicas = None
        
        self.alumnos_data.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.firma_relator_path = ""
        self.firma_label.config(text="Ningún archivo seleccionado")
