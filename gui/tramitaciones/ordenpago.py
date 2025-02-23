import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
from docxtpl import DocxTemplate
from database.db_config import connect_db
from path_utils import resource_path

class OrdenCompraWindow(ttk.Frame):
    def __init__(self, parent, connection=None):
        super().__init__(parent)
        self.parent = parent
        self.connection = connection

        # Configurar la ventana principal
        self.parent.title("Generación de Orden de Compra")
        
        try:
            self.parent.iconbitmap(resource_path("assets/logo1.ico"))
        except:
            pass

        # Plantilla .docx
        self.template_path = resource_path("formatos/orden_compra_template.docx")

        # Variables
        self.rut_search_var = tk.StringVar()
        self.acta_search_var = tk.StringVar()
        self.inscripcion_search_var = tk.StringVar()
        
        # Variables para datos adicionales
        self.encargado_var = tk.StringVar()
        self.detalle_var = tk.StringVar()
        self.metodo_pago_var = tk.StringVar(value="Transferencia")

        # Configurar estilos y UI
        self.setup_styles()
        self.setup_ui()
        self.pack(fill='both', expand=True)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Estilo para botones de acción
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

        # Estilo para botones de eliminación/cancelación
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

        # Estilo para el Treeview
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

    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)

        # Frame de búsqueda
        search_frame = ttk.LabelFrame(main_frame, text="Buscar Pago", padding=10)
        search_frame.pack(fill='x', padx=5, pady=5)

        # RUT
        ttk.Label(search_frame, text="RUT:").pack(side='left', padx=5)
        ttk.Entry(search_frame, textvariable=self.rut_search_var, width=15).pack(side='left', padx=5)

        # Número de Acta
        ttk.Label(search_frame, text="N° Acta:").pack(side='left', padx=5)
        ttk.Entry(search_frame, textvariable=self.acta_search_var, width=15).pack(side='left', padx=5)

        # ID Inscripción
        ttk.Label(search_frame, text="ID Inscripción:").pack(side='left', padx=5)
        ttk.Entry(search_frame, textvariable=self.inscripcion_search_var, width=15).pack(side='left', padx=5)

        ttk.Button(search_frame, text="Buscar", style="Action.TButton",
                command=self.buscar_pagos).pack(side='left', padx=5)

        # Frame para datos adicionales
        datos_frame = ttk.LabelFrame(main_frame, text="Datos de la Orden", padding=10)
        datos_frame.pack(fill='x', padx=5, pady=5)

        # Grid para los campos adicionales
        # Columna 1
        ttk.Label(datos_frame, text="Encargado:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        ttk.Entry(datos_frame, textvariable=self.encargado_var, width=30).grid(row=0, column=1, padx=5, pady=5, sticky='w')

        # Columna 2
        ttk.Label(datos_frame, text="Método de Pago:").grid(row=0, column=2, padx=5, pady=5, sticky='e')
        metodo_combo = ttk.Combobox(datos_frame, textvariable=self.metodo_pago_var, width=27,
                                values=["Transferencia", "Efectivo", "Cheque", "Tarjeta"],
                                state="readonly")
        metodo_combo.grid(row=0, column=3, padx=5, pady=5, sticky='w')

        # Detalles (fila completa)
        ttk.Label(datos_frame, text="Detalle:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        ttk.Entry(datos_frame, textvariable=self.detalle_var, width=87).grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky='ew')

        # Configurar el grid
        datos_frame.columnconfigure(1, weight=1)
        datos_frame.columnconfigure(3, weight=1)

        # Frame para la tabla
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Crear tabla
        columns = (
            'id_pago', 'numero_orden', 'rut', 'nombre', 'curso', 'num_acta', 'tipo_pago',
            'valor_total', 'estado', 'estado_orden'
        )
        self.tabla = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)

        # Configurar columnas
        self.tabla.heading('id_pago', text='ID Pago')
        self.tabla.heading('numero_orden', text='N° Orden')
        self.tabla.heading('rut', text='RUT')
        self.tabla.heading('nombre', text='Nombre')
        self.tabla.heading('curso', text='Curso')
        self.tabla.heading('num_acta', text='N° Acta')
        self.tabla.heading('tipo_pago', text='Tipo Pago')
        self.tabla.heading('valor_total', text='Valor Total')
        self.tabla.heading('estado', text='Estado')
        self.tabla.heading('estado_orden', text='Estado Orden')

        # Ajustar anchos
        self.tabla.column('id_pago', width=70, anchor='center')
        self.tabla.column('numero_orden', width=100, anchor='center')
        self.tabla.column('rut', width=100, anchor='center')
        self.tabla.column('nombre', width=200)
        self.tabla.column('curso', width=200)
        self.tabla.column('num_acta', width=100, anchor='center')
        self.tabla.column('tipo_pago', width=100, anchor='center')
        self.tabla.column('valor_total', width=100, anchor='e')
        self.tabla.column('estado', width=100, anchor='center')
        self.tabla.column('estado_orden', width=100, anchor='center')

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)

        self.tabla.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Frame de botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', padx=5, pady=(0, 10))  # Añadido padding abajo para los botones

        ttk.Button(btn_frame, text="Generar Orden", style="Action.TButton",
                command=self.generar_orden).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Limpiar", style="delete.TButton",
                command=self.limpiar_formulario).pack(side='right', padx=5)

    def setup_table(self, parent_frame):
        # Frame para la tabla
        table_frame = ttk.Frame(parent_frame)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Crear tabla
        columns = (
            'id_pago', 'numero_orden', 'rut', 'nombre', 'curso', 'num_acta', 'tipo_pago',
            'valor_total', 'estado', 'estado_orden'
        )
        self.tabla = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)

        # Configurar columnas
        self.tabla.heading('id_pago', text='ID Pago')
        self.tabla.heading('numero_orden', text='N° Orden')
        self.tabla.heading('rut', text='RUT')
        self.tabla.heading('nombre', text='Nombre')
        self.tabla.heading('curso', text='Curso')
        self.tabla.heading('num_acta', text='N° Acta')
        self.tabla.heading('tipo_pago', text='Tipo Pago')
        self.tabla.heading('valor_total', text='Valor Total')
        self.tabla.heading('estado', text='Estado')
        self.tabla.heading('estado_orden', text='Estado Orden')

        # Ajustar anchos
        self.tabla.column('id_pago', width=70, anchor='center')
        self.tabla.column('numero_orden', width=100, anchor='center')
        self.tabla.column('rut', width=100, anchor='center')
        self.tabla.column('nombre', width=200)
        self.tabla.column('curso', width=200)
        self.tabla.column('num_acta', width=100, anchor='center')
        self.tabla.column('tipo_pago', width=100, anchor='center')
        self.tabla.column('valor_total', width=100, anchor='e')
        self.tabla.column('estado', width=100, anchor='center')
        self.tabla.column('estado_orden', width=100, anchor='center')

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)

        self.tabla.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def buscar_pagos(self):
        try:
            conn = self.connection or connect_db()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT p.*, a.rut, CONCAT(a.nombre, ' ', a.apellido) as nombre_completo,
                       c.nombre_curso, i.numero_acta
                FROM pagos p
                INNER JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
                INNER JOIN alumnos a ON i.id_alumno = a.rut
                INNER JOIN cursos c ON i.id_curso = c.id_curso
                WHERE 1=1
            """
            params = []

            if self.rut_search_var.get().strip():
                query += " AND a.rut = %s"
                params.append(self.rut_search_var.get().strip())

            if self.acta_search_var.get().strip():
                query += " AND i.numero_acta = %s"
                params.append(self.acta_search_var.get().strip())

            if self.inscripcion_search_var.get().strip():
                query += " AND i.id_inscripcion = %s"
                params.append(self.inscripcion_search_var.get().strip())

            cursor.execute(query, params)
            results = cursor.fetchall()

            # Limpiar tabla
            for item in self.tabla.get_children():
                self.tabla.delete(item)

            for row in results:
                self.tabla.insert('', 'end', values=(
                    row['id_pago'],
                    row.get('numero_orden', 'Sin Orden'),
                    row['rut'],
                    row['nombre_completo'],
                    row['nombre_curso'],
                    row['numero_acta'],
                    row['tipo_pago'],
                    f"${row['valor_total']:,.0f}",
                    row['estado'],
                    row.get('estado_orden', 'SIN EMITIR')
                ))

            if not results:
                messagebox.showinfo("Información", "No se encontraron pagos con los criterios especificados")

        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar pagos: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn and not self.connection:
                conn.close()

    def generar_orden(self):
        selected = self.tabla.selection()
        if not selected:
            messagebox.showinfo("Seleccione", "Debe seleccionar un pago para generar la orden")
            return

        # Validar campos adicionales
        if not self.encargado_var.get().strip():
            messagebox.showwarning("Advertencia", "Debe ingresar el encargado")
            return

        if not self.detalle_var.get().strip():
            messagebox.showwarning("Advertencia", "Debe ingresar el detalle")
            return

        try:
            conn = self.connection or connect_db()
            cursor = conn.cursor()
            
            item = self.tabla.item(selected[0])
            valores = item['values']

            if valores[9] != 'SIN EMITIR':
                messagebox.showinfo("Aviso", "Este pago ya tiene una orden emitida")
                return

            # Obtener siguiente número de orden
            cursor.execute("""
                INSERT IGNORE INTO doc_sequences (doc_type, last_number)
                VALUES ('orden_compra', 0)
            """)
            
            # Actualizar y obtener número
            cursor.execute("""
                UPDATE doc_sequences 
                SET last_number = last_number + 1
                WHERE doc_type = 'orden_compra'
            """)
            
            cursor.execute("""
                SELECT last_number
                FROM doc_sequences
                WHERE doc_type = 'orden_compra'
            """)
            
            result = cursor.fetchone()
            if not result:
                messagebox.showerror("Error", "No se pudo generar número de orden")
                return
                
            num_orden = str(result[0]).zfill(4)
            
            # Obtener datos adicionales del curso
            cursor.execute("""
                SELECT c.id_curso
                FROM pagos p
                INNER JOIN inscripciones i ON p.id_inscripcion = i.id_inscripcion
                INNER JOIN cursos c ON i.id_curso = c.id_curso
                WHERE p.id_pago = %s
            """, (valores[0],))
            curso_result = cursor.fetchone()
            id_curso = curso_result[0] if curso_result else ''

            # Preparar datos para el template con fecha actual
            fecha_actual = datetime.now()
            dia = fecha_actual.strftime("%d")
            mes = fecha_actual.strftime("%m")
            anio = fecha_actual.strftime("%Y")
            
            # Formato de fecha completo para el documento
            fecha_formato = f"{dia}/{mes}/{anio}"

            context = {
                'num_orden': num_orden,
                'fecha_emi': fecha_formato,  # Fecha formateada
                'dia': dia,                 # Día actual
                'mes': mes,                 # Mes actual
                'año': anio,                # Año actual
                'rut': valores[2],
                'nombre_alum': valores[3],
                'id_curso': id_curso,
                'nombre_curso': valores[4],
                'valor': valores[7].replace('$', '').replace(',', ''),
                'detalle': self.detalle_var.get(),
                'encargado': self.encargado_var.get(),
                'metodo_pago': self.metodo_pago_var.get()
            }

            # Generar documento
            doc = DocxTemplate(self.template_path)
            doc.render(context)

            # Guardar documento
            default_filename = f"orden_compra_{num_orden}_{fecha_actual.strftime('%Y%m%d_%H%M%S')}.docx"
            output_path = filedialog.asksaveasfilename(
                defaultextension=".docx",
                filetypes=[("Documento Word", "*.docx")],
                initialfile=default_filename,
                title="Guardar orden de compra como"
            )

            if not output_path:
                return

            doc.save(output_path)

            # Actualizar estado en BD con la fecha actual
            update_query = """
                UPDATE pagos 
                SET estado_orden = 'EMITIDO',
                    numero_orden = %s,
                    detalle = %s,
                    encargado = %s,
                    metodo_pago = %s,
                    fecha_pago = %s
                WHERE id_pago = %s
            """
            cursor.execute(update_query, (
                num_orden, 
                self.detalle_var.get(),
                self.encargado_var.get(),
                self.metodo_pago_var.get(),
                fecha_actual,
                valores[0]
            ))
            conn.commit()

            messagebox.showinfo("Éxito", 
                f"Orden de compra N° {num_orden} generada exitosamente.\n" +
                f"Documento guardado en: {output_path}")

            self.buscar_pagos()
            self.limpiar_datos_adicionales()

        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Error", f"Error al generar orden: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            if cursor:
                cursor.close()
            if conn and not self.connection:
                conn.close()

    def limpiar_formulario(self):
        """Limpia todos los campos y la tabla"""
        self.rut_search_var.set("")
        self.acta_search_var.set("")
        self.inscripcion_search_var.set("")
        self.limpiar_datos_adicionales()
        
        for item in self.tabla.get_children():
            self.tabla.delete(item)

    def limpiar_datos_adicionales(self):
        """Limpia solo los campos adicionales"""
        self.encargado_var.set("")
        self.detalle_var.set("")
        self.metodo_pago_var.set("Transferencia")

    def _show_context_menu(self, event):
        """Muestra el menú contextual"""
        try:
            self.tabla.selection_clear()
            item = self.tabla.identify_row(event.y)
            if item:
                self.tabla.selection_add(item)
                self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _copy_selected_cell(self):
        """Copia el contenido de la celda seleccionada"""
        selected_items = self.tabla.selection()
        if not selected_items:
            return
            
        item = selected_items[0]
        column = self.tabla.identify_column(self.last_click_x)
        cell_value = self.tabla.item(item)['values'][int(column[1]) - 1]
        
        self.parent.clipboard_clear()
        self.parent.clipboard_append(str(cell_value))

    def _copy_selected_row(self):
        """Copia la fila completa seleccionada"""
        selected_items = self.tabla.selection()
        if not selected_items:
            return
            
        item = selected_items[0]
        row_values = self.tabla.item(item)['values']
        
        self.parent.clipboard_clear()
        self.parent.clipboard_append('\t'.join(str(x) for x in row_values))

    def _save_click_position(self, event):
        """Guarda la posición del último clic"""
        self.last_click_x = event.x
        self.last_click_y = event.y

if __name__ == "__main__":
    root = tk.Tk()
    app = OrdenCompraWindow(root)
    root.mainloop()