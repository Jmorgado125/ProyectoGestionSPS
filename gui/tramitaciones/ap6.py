import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
from docxtpl import DocxTemplate

from database.queries import get_apendice6_data

class Apendice6Window(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        try:
            self.parent.iconbitmap('assets/logo2.ico')
        except Exception as e:
            print(f"Error al cargar íconos: {e}")
        
        self.template_path = 'formatos/ap6_template.docx'
        
        # Variables para datos del curso
        self.nombre_curso = ""
        self.fecha_inicio = None
        self.fecha_termino = None
        self.horas_cronologicas = None
        self.horas_pedagogicas = None
        self.relator = tk.StringVar()  # Nueva variable para el relator
        
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
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)

        # ---------- SECCIÓN SUPERIOR: DATOS GENERALES ---------- 
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill='x', pady=5)
        
        # Búsqueda por acta
        search_frame = ttk.LabelFrame(top_frame, text="Búsqueda", padding=5)
        search_frame.pack(side='left', fill='x', expand=True, padx=5)
        
        ttk.Label(search_frame, text="N° Acta:").pack(side='left', padx=5)
        self.acta_var = tk.StringVar()
        self.acta_entry = ttk.Entry(search_frame, textvariable=self.acta_var, width=15)
        self.acta_entry.pack(side='left', padx=5)
        ttk.Button(search_frame, text="Buscar",style='Action.TButton', command=self.cargar_datos_bd).pack(side='left', padx=5)
        
        # Campo para relator
        relator_frame = ttk.LabelFrame(top_frame, text="Relator", padding=5)
        relator_frame.pack(side='left', fill='x', padx=5)
        
        self.relator_entry = ttk.Entry(relator_frame, textvariable=self.relator, width=25)
        self.relator_entry.pack(padx=5)

        # ---------- SECCIÓN MEDIA: OBSERVACIONES ---------- 
        obs_frame = ttk.LabelFrame(main_frame, text="Observaciones", padding=5)
        obs_frame.pack(fill='x', padx=5, pady=5)
        
        self.observaciones_txt = tk.Text(obs_frame, height=3)
        self.observaciones_txt.pack(fill='x', padx=5, pady=5)

        # ---------- SECCIÓN ALUMNOS: TABLA EDITABLE ---------- 
        table_frame = ttk.LabelFrame(main_frame, text="Alumnos", padding=5)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Configuración del Treeview con nueva columna
        columns = ("num", "nombre", "rut", "titulo", "alu_titulo", "mmn")
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        # Configurar columnas
        self.tree.heading("num", text="N°")
        self.tree.heading("nombre", text="Nombre Completo")
        self.tree.heading("rut", text="RUT")
        self.tree.heading("titulo", text="Título Base")
        self.tree.heading("alu_titulo", text="Título a Validar")
        self.tree.heading("mmn", text="MMN")
        
        # Ajustar anchos
        self.tree.column("num", width=50, anchor='center')
        self.tree.column("nombre", width=250)
        self.tree.column("rut", width=100, anchor='center')
        self.tree.column("titulo", width=150)
        self.tree.column("alu_titulo", width=150)
        self.tree.column("mmn", width=80, anchor='center')
        
        # Scrollbar y empaquetado
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Evento para editar celdas
        self.tree.bind("<Double-1>", self.editar_celda)

        # ---------- BOTONES INFERIORES ---------- 
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(button_frame, text="Limpiar",style="delete.TButton", command=self.limpiar_formulario).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Vista Previa",style="Action.TButton", command=self.vista_previa).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Generar",style="Action.TButton", command=self.generar_documento).pack(side='right', padx=5)

    def editar_celda(self, event):
        """Permite editar la columna 'alu_titulo' en la tabla"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return
        
        column = self.tree.identify_column(event.x)
        item = self.tree.focus()
        
        if column == "#5":  # Columna 'alu_titulo'
            x, y, width, height = self.tree.bbox(item, column)
            value = self.tree.item(item, "values")[4]
            
            # Crear ventana de edición
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
                
                # Actualizar datos en la lista alumnos_data
                idx = int(current_values[0]) - 1
                if 0 <= idx < len(self.alumnos_data):
                    self.alumnos_data[idx]["alu_titulo"] = new_value
                
                edit_win.destroy()
            
            entry.bind("<Return>", lambda e: guardar_cambio())
            entry.bind("<Escape>", lambda e: edit_win.destroy())
            entry.bind("<FocusOut>", lambda e: guardar_cambio())
            entry.focus_set()

    def cargar_datos_bd(self):
        """Carga los datos desde la base de datos según el número de acta"""
        acta_num = self.acta_var.get().strip()
        if not acta_num:
            messagebox.showerror("Error", "Debe ingresar un número de acta.")
            return

        # Limpiar tabla y datos actuales
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.alumnos_data.clear()

        try:
            data_bd = get_apendice6_data(acta_num)
            if not data_bd:
                messagebox.showwarning("Sin datos", "No se encontró información para este número de acta.")
                return

            # Extraer datos generales del primer registro
            row0 = data_bd[0]
            self.nombre_curso = row0["nombre_curso"]
            self.fecha_inicio = row0["fecha_inicio"]
            self.fecha_termino = row0["fecha_termino"]
            self.horas_cronologicas = row0.get("horas_cronologicas", "")
            self.horas_pedagogicas = row0.get("horas_pedagogicas", 0)

            # Poblar la tabla y lista de alumnos
            for idx, row in enumerate(data_bd, start=1):
                nombre_completo = f"{row['apellido']} {row['nombre']}"
                
                self.alumnos_data.append({
                    "N": idx,
                    "nombre_completo": nombre_completo,
                    "rut": row["rut"],
                    "titulo": row.get("profesion", ""),
                    "alu_titulo": "",  # Campo nuevo inicializado vacío
                    "mmn": row.get("mmn", "")
                })
                
                self.tree.insert("", "end", values=(
                    idx,
                    nombre_completo,
                    row["rut"],
                    row.get("profesion", ""),
                    "",  # Título a validar (inicialmente vacío)
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

        # Validar campo relator
        if not self.relator.get().strip():
            messagebox.showerror("Error", "Debe ingresar el nombre del relator.")
            return

        try:
            doc = DocxTemplate(self.template_path)
            context = {
                "num_acta": acta,
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
        self.relator.set("")  # Limpiar campo de relator
        self.observaciones_txt.delete("1.0", tk.END)
        
        self.nombre_curso = ""
        self.fecha_inicio = None
        self.fecha_termino = None
        self.horas_cronologicas = None
        self.horas_pedagogicas = None
        
        self.alumnos_data.clear()