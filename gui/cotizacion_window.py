import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from database.queries import (
    insertar_cotizacion,
    fetch_courses,
)
from helpers.document_generator import generate_cotizacion_doc

class CotizacionWindow(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.detalles = []
        
        # Configurar la ventana principal
        self.parent.title("Nueva Cotización")
        self.parent.state("zoomed")
        self.parent.iconbitmap("assets/logo1.ico")
        # Empaquetar el frame principal
        self.pack(fill='both', expand=True)
        
        # Definir el estilo para los botones
        style = ttk.Style(self)
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

        self.setup_ui()
        
    def setup_ui(self):
        # Frame principal con padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)

        
        # Sección de información general organizada horizontalmente
        info_frame = ttk.LabelFrame(main_frame, text="Información General", padding="10")
        info_frame.pack(fill='x', padx=5, pady=5)
        
        # Configuración de columnas para organizar los campos horizontalmente
        for col in range(4):
            info_frame.columnconfigure(col, weight=1, pad=5)
        
        # Campos de Información General distribuidos en dos filas y dos columnas
        labels = ["Origen:", "Contacto:", "Email:", "Encargado:"]
        var_names = ["origen", "contacto", "email", "encargado"]
        
        for i, (label, var_name) in enumerate(zip(labels, var_names)):
            row = i // 2
            column = (i % 2) * 2  # 0 y 2 para las etiquetas
            ttk.Label(info_frame, text=label).grid(row=row, column=column, padx=5, pady=5, sticky='e')
            entry = ttk.Entry(info_frame, width=30)
            entry.grid(row=row, column=column + 1, padx=5, pady=5, sticky='w')
            setattr(self, var_name + "_entry", entry)
        
        # Modo de pago
        ttk.Label(info_frame, text="Modo de Pago:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.modo_pago_var = tk.StringVar(value="Al Contado")
        modo_pago_frame = ttk.Frame(info_frame)
        modo_pago_frame.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        ttk.Radiobutton(modo_pago_frame, text="Al Contado", variable=self.modo_pago_var, 
                       value="Al Contado", command=self.toggle_cuotas).pack(side='left', padx=5)
        ttk.Radiobutton(modo_pago_frame, text="Pagaré", variable=self.modo_pago_var,
                       value="Pagaré", command=self.toggle_cuotas).pack(side='left', padx=5)
        
        # Método de pago y número de cuotas
        self.metodo_pago_frame = ttk.Frame(info_frame)
        self.metodo_pago_frame.grid(row=2, column=2, columnspan=2, sticky='w', padx=5, pady=5)
        self.metodo_pago_var = tk.StringVar()
        self.num_cuotas_var = tk.StringVar()
        self.setup_metodo_pago()
        
        # Sección de detalles
        detalles_frame = ttk.LabelFrame(main_frame, text="Detalles de Cotización", padding="10")
        detalles_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Frame para agregar detalles
        add_frame = ttk.Frame(detalles_frame)
        add_frame.pack(fill='x', padx=5, pady=5)
        
        # Combobox para cursos
        self.cursos = fetch_courses()
        self.curso_var = tk.StringVar()
        self.curso_combo = ttk.Combobox(add_frame, textvariable=self.curso_var, width=40, state="readonly")
        self.curso_combo['values'] = [curso[1] for curso in self.cursos]
        self.curso_combo.pack(side='left', padx=5)
        
        # Cantidad
        self.cantidad_var = tk.StringVar(value="1")
        cantidad_entry = ttk.Entry(add_frame, textvariable=self.cantidad_var, width=10)
        cantidad_entry.pack(side='left', padx=5)
        
        # Botón agregar con el estilo personalizado
        ttk.Button(add_frame, text="Agregar", command=self.agregar_detalle, style='Custom.TButton').pack(side='left', padx=5)
        
        # Tabla de detalles con columna adicional para Código del Curso
        self.tabla = ttk.Treeview(detalles_frame, columns=('codigo_curso', 'curso', 'cantidad', 'valor_unit', 'valor_total'),
                                 show='headings', height=5)
        self.tabla.heading('codigo_curso', text='Código del Curso')
        self.tabla.heading('curso', text='Curso')
        self.tabla.heading('cantidad', text='Cantidad')
        self.tabla.heading('valor_unit', text='Valor Unitario')
        self.tabla.heading('valor_total', text='Valor Total')
        
        # Configurar anchos de columna
        self.tabla.column('codigo_curso', width=100, anchor='center')
        self.tabla.column('curso', width=300)
        self.tabla.column('cantidad', width=100, anchor='center')
        self.tabla.column('valor_unit', width=150, anchor='e')
        self.tabla.column('valor_total', width=150, anchor='e')
        
        self.tabla.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Scrollbar para la tabla
        scrollbar = ttk.Scrollbar(detalles_frame, orient="vertical", command=self.tabla.yview)
        scrollbar.pack(side='right', fill='y')
        self.tabla.configure(yscrollcommand=scrollbar.set)
        
        # Botón eliminar detalle con el estilo personalizado
        ttk.Button(detalles_frame, text="Eliminar Seleccionado", 
                  command=self.eliminar_detalle, style='Custom.TButton').pack(pady=5)
        
        # Frame de totales
        totales_frame = ttk.Frame(main_frame)
        totales_frame.pack(fill='x', padx=5, pady=5)
        
        self.subtotal_var = tk.StringVar(value="$0")
        self.total_var = tk.StringVar(value="$0")
        
        # Alinear totales a la derecha
        for label, var in [
            ("Total Neto:", self.subtotal_var),
            ("Total:", self.total_var)
        ]:
            frame = ttk.Frame(totales_frame)
            frame.pack(side='right', padx=10)
            ttk.Label(frame, text=label).pack(side='left')
            ttk.Label(frame, textvariable=var, width=15, anchor='e').pack(side='left')
        
        # Observaciones
        obs_frame = ttk.LabelFrame(main_frame, text="Observaciones", padding="10")
        obs_frame.pack(fill='x', padx=5, pady=5)
        self.observaciones_text = tk.Text(obs_frame, height=4)
        self.observaciones_text.pack(fill='x', padx=5, pady=5)
        
        # Botones finales con el estilo personalizado
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill='x', padx=5, pady=10)
        ttk.Button(buttons_frame, text="Generar Cotización", 
                  command=self.generar_cotizacion, style='Custom.TButton').pack(side='right', padx=5)
        ttk.Button(buttons_frame, text="Limpiar", 
                  command=self.limpiar_formulario, style='Custom.TButton').pack(side='right', padx=5)

    def setup_metodo_pago(self):
        """Configura los widgets de método de pago"""
        # Como el método de pago no se solicita en la UI, lo configuramos aquí de forma programática
        for widget in self.metodo_pago_frame.winfo_children():
            widget.destroy()
        
        # Definir el método de pago basado en el modo de pago
        modo_pago = self.modo_pago_var.get()
        if modo_pago == "Al Contado":
            metodo_pago = "Transferencia"  # Valor por defecto para Al Contado
            self.num_cuotas_var.set("")  # No se requieren cuotas
        elif modo_pago == "Pagaré":
            metodo_pago = "Pagaré"
            # Mantener el campo de número de cuotas para Pagaré
        else:
            metodo_pago = "N/A"
        
        # Almacenar el método de pago en una variable de instancia
        self.metodo_pago_var.set(metodo_pago)
        
        # Mostrar u ocultar el campo de cuotas según el modo de pago
        if modo_pago == "Pagaré":
            ttk.Label(self.metodo_pago_frame, text="N° Cuotas:").pack(side='left', padx=5)
            self.cuotas_entry = ttk.Entry(self.metodo_pago_frame, 
                                        textvariable=self.num_cuotas_var,
                                        width=5)
            self.cuotas_entry.pack(side='left', padx=5)
        else:
            # Si no es Pagaré, eliminar el campo de cuotas si existe
            for widget in self.metodo_pago_frame.winfo_children():
                widget.destroy()

    def toggle_cuotas(self):
        """Actualiza la UI cuando cambia el modo de pago y configura el método de pago"""
        self.setup_metodo_pago()

    def agregar_detalle(self):
        """Agrega un detalle a la cotización"""
        try:
            curso_idx = self.curso_combo.current()
            if curso_idx < 0:
                messagebox.showerror("Error", "Debe seleccionar un curso")
                return
                
            cantidad = int(self.cantidad_var.get())
            if cantidad <= 0:
                messagebox.showerror("Error", "La cantidad debe ser mayor a 0")
                return
                
            curso = self.cursos[curso_idx]
            valor_unit = curso[7]  # Asumiendo que el valor está en esta posición
            valor_total = valor_unit * cantidad
            
            # Agregar a la tabla incluyendo el código del curso
            self.tabla.insert('', 'end', values=(
                curso[0],  # Código del curso
                curso[1],  # Nombre del curso
                cantidad,
                f"${valor_unit:,.0f}",
                f"${valor_total:,.0f}"
            ))
            
            # Guardar detalle para procesar después
            self.detalles.append({
                'id_curso': curso[0],
                'curso': curso[1],  # Nombre del curso
                'cantidad': cantidad,
                'valor_curso': valor_unit,
                'valor_total': valor_total
            })
            
            self.actualizar_totales()
            
        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número válido")

    def eliminar_detalle(self):
        """Elimina el detalle seleccionado"""
        selected = self.tabla.selection()
        if not selected:
            messagebox.showinfo("Información", "Debe seleccionar un detalle para eliminar")
            return
            
        idx = self.tabla.index(selected[0])
        self.tabla.delete(selected[0])
        del self.detalles[idx]
        self.actualizar_totales()

    def actualizar_totales(self):
        """Actualiza los totales de la cotización"""
        subtotal = sum(detalle['valor_total'] for detalle in self.detalles)
        
        total = subtotal 
        
        self.subtotal_var.set(f"${subtotal:,.0f}")
        self.total_var.set(f"${total:,.0f}")

    def limpiar_formulario(self):
        """Limpia todos los campos del formulario"""
        self.origen_entry.delete(0, 'end')
        self.contacto_entry.delete(0, 'end')
        self.email_entry.delete(0, 'end')
        self.encargado_entry.delete(0, 'end')
        self.modo_pago_var.set("Al Contado")
        self.metodo_pago_var.set("")
        self.num_cuotas_var.set("")
        self.observaciones_text.delete('1.0', 'end')
        self.cantidad_var.set("1")
        self.curso_var.set("")
        
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        self.detalles.clear()
        self.actualizar_totales()
        self.setup_metodo_pago()  # Reiniciar método de pago

    def generar_cotizacion(self):
        """Genera la cotización y el documento"""
        try:
            # Validar campos requeridos
            for var_name, field_name in [
                ("origen_entry", "El origen"),
                ("contacto_entry", "El contacto"),
                ("email_entry", "El email"),
                ("encargado_entry", "El encargado")
            ]:
                value = getattr(self, var_name).get().strip()
                if not value:
                    messagebox.showerror("Error", f"{field_name} es requerido")
                    return
            if not self.detalles:
                messagebox.showerror("Error", "Debe agregar al menos un detalle")
                return
            
            # Preparar datos
            fecha_cotizacion = datetime.now()
            fecha_vencimiento = fecha_cotizacion + timedelta(days=30)
            
            subtotal = sum(detalle['valor_total'] for detalle in self.detalles)
            
            total = subtotal 
            
            # Definir el método de pago basado en el modo de pago
            modo_pago = self.modo_pago_var.get()
            if modo_pago == "Al Contado":
                metodo_pago = "Transferencia"  # Valor por defecto o puedes elegir otro
                num_cuotas = None  # No se requieren cuotas
            elif modo_pago == "Pagaré":
                metodo_pago = "Pagaré"
                try:
                    num_cuotas = int(self.num_cuotas_var.get())
                    if num_cuotas <= 0:
                        messagebox.showerror("Error", "El número de cuotas debe ser mayor a 0")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Debe ingresar un número válido de cuotas")
                    return
            else:
                metodo_pago = "N/A"
                num_cuotas = None
            
            # Insertar cotización con todos los detalles
            id_cotizacion = insertar_cotizacion(
                fecha_cotizacion=fecha_cotizacion,
                fecha_vencimiento=fecha_vencimiento,
                origen=self.origen_entry.get().strip(),
                nombre_contacto=self.contacto_entry.get().strip(),
                email=self.email_entry.get().strip(),
                encargado=self.encargado_entry.get().strip(),
                modo_pago=modo_pago,
                metodo_pago=metodo_pago,
                num_cuotas=num_cuotas,
                detalle=self.observaciones_text.get('1.0', 'end-1c'),
                total=total,
                detalles_cursos=self.detalles
            )
            
            if not id_cotizacion:
                messagebox.showerror("Error", "No se pudo crear la cotización")
                return
                
            # Generar documento
            cotizacion_data = {
                'id_cotizacion': id_cotizacion,
                'fecha_cotizacion': fecha_cotizacion,
                'fecha_vencimiento': fecha_vencimiento,
                'origen': self.origen_entry.get().strip(),
                'nombre_contacto': self.contacto_entry.get().strip(),
                'email': self.email_entry.get().strip(),
                'encargado': self.encargado_entry.get().strip(),
                'modo_pago': modo_pago,
                'metodo_pago': metodo_pago,
                'num_cuotas': num_cuotas,
                'detalle': self.observaciones_text.get('1.0', 'end-1c'),
                'total': total,
            }
            
            doc_path = generate_cotizacion_doc(cotizacion_data, self.detalles, parent_window=self)
            
            if doc_path:
                messagebox.showinfo("Éxito", 
                    f"Cotización generada exitosamente.\nDocumento guardado en: {doc_path}")
                self.winfo_toplevel().destroy()
            else:
                messagebox.showerror("Error", 
                    "La cotización se guardó pero hubo un error al generar el documento")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar la cotización: {str(e)}")
            import traceback
            traceback.print_exc()  # Agregar este print para debugging
