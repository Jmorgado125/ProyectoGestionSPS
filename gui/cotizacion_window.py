import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from database.queries import (
    insert_cotizacion,
    insert_detalle_cotizacion,
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
        self.parent.geometry("800x600")  # Tamaño inicial de la ventana
        
        # Empaquetar el frame principal
        self.pack(fill='both', expand=True)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame principal con padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Sección de información general
        info_frame = ttk.LabelFrame(main_frame, text="Información General", padding="5")
        info_frame.pack(fill='x', padx=5, pady=5)
        
        # Grid para campos
        for i, (label, var_name) in enumerate([
            ("Origen:", "origen"),
            ("Contacto:", "contacto"),
            ("Email:", "email")
        ]):
            ttk.Label(info_frame, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='e')
            entry = ttk.Entry(info_frame, width=40)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='w')
            setattr(self, var_name + "_entry", entry)
        
        # Modo de pago
        ttk.Label(info_frame, text="Modo de Pago:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.modo_pago_var = tk.StringVar(value="Al Contado")
        modo_pago_frame = ttk.Frame(info_frame)
        modo_pago_frame.grid(row=3, column=1, sticky='w')
        ttk.Radiobutton(modo_pago_frame, text="Al Contado", variable=self.modo_pago_var, 
                       value="Al Contado", command=self.toggle_cuotas).pack(side='left')
        ttk.Radiobutton(modo_pago_frame, text="Pagaré", variable=self.modo_pago_var,
                       value="Pagaré", command=self.toggle_cuotas).pack(side='left')
        
        # Método de pago y número de cuotas
        self.metodo_pago_frame = ttk.Frame(info_frame)
        self.metodo_pago_frame.grid(row=4, column=0, columnspan=2, sticky='w', padx=5)
        self.metodo_pago_var = tk.StringVar()
        self.num_cuotas_var = tk.StringVar()
        self.setup_metodo_pago()
        
        # Sección de detalles
        detalles_frame = ttk.LabelFrame(main_frame, text="Detalles de Cotización")
        detalles_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Frame para agregar detalles
        add_frame = ttk.Frame(detalles_frame)
        add_frame.pack(fill='x', padx=5, pady=5)
        
        # Combobox para cursos
        self.cursos = fetch_courses()
        self.curso_var = tk.StringVar()
        self.curso_combo = ttk.Combobox(add_frame, textvariable=self.curso_var, width=40)
        self.curso_combo['values'] = [curso[1] for curso in self.cursos]
        self.curso_combo.pack(side='left', padx=5)
        
        # Cantidad
        self.cantidad_var = tk.StringVar(value="1")
        cantidad_entry = ttk.Entry(add_frame, textvariable=self.cantidad_var, width=10)
        cantidad_entry.pack(side='left', padx=5)
        
        # Botón agregar
        ttk.Button(add_frame, text="Agregar", command=self.agregar_detalle).pack(side='left', padx=5)
        
        # Tabla de detalles
        self.tabla = ttk.Treeview(detalles_frame, columns=('curso', 'cantidad', 'valor_unit', 'valor_total'),
                                 show='headings', height=5)
        self.tabla.heading('curso', text='Curso')
        self.tabla.heading('cantidad', text='Cantidad')
        self.tabla.heading('valor_unit', text='Valor Unitario')
        self.tabla.heading('valor_total', text='Valor Total')
        
        # Configurar anchos de columna
        self.tabla.column('curso', width=300)
        self.tabla.column('cantidad', width=100)
        self.tabla.column('valor_unit', width=150)
        self.tabla.column('valor_total', width=150)
        
        self.tabla.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Scrollbar para la tabla
        scrollbar = ttk.Scrollbar(detalles_frame, orient="vertical", command=self.tabla.yview)
        scrollbar.pack(side='right', fill='y')
        self.tabla.configure(yscrollcommand=scrollbar.set)
        
        # Botón eliminar detalle
        ttk.Button(detalles_frame, text="Eliminar Seleccionado", 
                  command=self.eliminar_detalle).pack(pady=5)
        
        # Frame de totales
        totales_frame = ttk.Frame(main_frame)
        totales_frame.pack(fill='x', padx=5, pady=5)
        
        self.subtotal_var = tk.StringVar(value="$0")
        self.iva_var = tk.StringVar(value="$0")
        self.total_var = tk.StringVar(value="$0")
        
        # Alinear totales a la derecha
        for label, var in [
            ("Total Neto:", self.subtotal_var),
            ("IVA (19%):", self.iva_var),
            ("Total:", self.total_var)
        ]:
            frame = ttk.Frame(totales_frame)
            frame.pack(side='right', padx=10)
            ttk.Label(frame, text=label).pack(side='left')
            ttk.Label(frame, textvariable=var, width=15).pack(side='left')
        
        # Observaciones
        obs_frame = ttk.LabelFrame(main_frame, text="Observaciones")
        obs_frame.pack(fill='x', padx=5, pady=5)
        self.observaciones_text = tk.Text(obs_frame, height=4)
        self.observaciones_text.pack(fill='x', padx=5, pady=5)
        
        # Botones finales
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill='x', padx=5, pady=10)
        ttk.Button(buttons_frame, text="Generar Cotización", 
                  command=self.generar_cotizacion).pack(side='right', padx=5)
        ttk.Button(buttons_frame, text="Limpiar", 
                  command=self.limpiar_formulario).pack(side='right', padx=5)
    
    def setup_metodo_pago(self):
        """Configura los widgets de método de pago"""
        for widget in self.metodo_pago_frame.winfo_children():
            widget.destroy()
            
        ttk.Label(self.metodo_pago_frame, text="Método de Pago:").pack(side='left', padx=5)
        if self.modo_pago_var.get() == "Al Contado":
            metodos = ["Efectivo", "Transferencia", "Tarjeta"]
        else:
            metodos = ["Pagaré"]
            
        self.metodo_combo = ttk.Combobox(self.metodo_pago_frame, 
                                        textvariable=self.metodo_pago_var,
                                        values=metodos, 
                                        state="readonly",
                                        width=15)
        self.metodo_combo.pack(side='left', padx=5)
        
        if self.modo_pago_var.get() == "Pagaré":
            ttk.Label(self.metodo_pago_frame, text="N° Cuotas:").pack(side='left', padx=5)
            self.cuotas_entry = ttk.Entry(self.metodo_pago_frame, 
                                        textvariable=self.num_cuotas_var,
                                        width=5)
            self.cuotas_entry.pack(side='left', padx=5)
    
    def toggle_cuotas(self):
        """Actualiza la UI cuando cambia el modo de pago"""
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
            
            # Agregar a la tabla
            self.tabla.insert('', 'end', values=(
                curso[1],  # nombre_curso
                cantidad,
                f"${valor_unit:,.0f}",
                f"${valor_total:,.0f}"
            ))
            
            # Guardar detalle para procesar después
            self.detalles.append({
                'id_curso': curso[0],
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
        iva = int(subtotal * 0.19)
        total = subtotal + iva
        
        self.subtotal_var.set(f"${subtotal:,.0f}")
        self.iva_var.set(f"${iva:,.0f}")
        self.total_var.set(f"${total:,.0f}")
    
    def limpiar_formulario(self):
        """Limpia todos los campos del formulario"""
        self.origen_entry.delete(0, 'end')
        self.contacto_entry.delete(0, 'end')
        self.email_entry.delete(0, 'end')
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
    
    def generar_cotizacion(self):
        """Genera la cotización y el documento"""
        try:
            # Validar campos requeridos
            if not self.origen_entry.get().strip():
                messagebox.showerror("Error", "El origen es requerido")
                return
            if not self.contacto_entry.get().strip():
                messagebox.showerror("Error", "El contacto es requerido")
                return
            if not self.email_entry.get().strip():
                messagebox.showerror("Error", "El email es requerido")
                return
            if not self.detalles:
                messagebox.showerror("Error", "Debe agregar al menos un detalle")
                return
            
            # Preparar datos
            fecha_cotizacion = datetime.now()
            fecha_vencimiento = fecha_cotizacion + timedelta(days=30)  # Validez de 30 días
            
            subtotal = sum(detalle['valor_total'] for detalle in self.detalles)
            iva = int(subtotal * 0.19)
            total = subtotal + iva
            
            # Insertar cotización
            id_cotizacion = insert_cotizacion(
                fecha_cotizacion=fecha_cotizacion,
                fecha_vencimiento=fecha_vencimiento,
                origen=self.origen_entry.get().strip(),
                nombre_contacto=self.contacto_entry.get().strip(),
                email=self.email_entry.get().strip(),
                modo_pago=self.modo_pago_var.get(),
                metodo_pago=self.metodo_pago_var.get(),
                num_cuotas=int(self.num_cuotas_var.get()) if self.num_cuotas_var.get() else None,
                detalle=self.observaciones_text.get('1.0', 'end-1c'),
                total=total,
                valor_iva=iva
            )
            
            if not id_cotizacion:
                messagebox.showerror("Error", "No se pudo crear la cotización")
                return
            
            # Insertar detalles
            for detalle in self.detalles:
                insert_detalle_cotizacion(
                    id_cotizacion=id_cotizacion,
                    id_curso=detalle['id_curso'],
                    cantidad=detalle['cantidad'],
                    valor_curso=detalle['valor_curso'],
                    valor_total=detalle['valor_total']
                )
            
            # Generar documento
            cotizacion_data = {
                'id_cotizacion': id_cotizacion,
                'fecha_cotizacion': fecha_cotizacion,
                'fecha_vencimiento': fecha_vencimiento,
                'origen': self.origen_entry.get().strip(),
                'nombre_contacto': self.contacto_entry.get().strip(),
                'email': self.email_entry.get().strip(),
                'modo_pago': self.modo_pago_var.get(),
                'metodo_pago': self.metodo_pago_var.get(),
                'num_cuotas': self.num_cuotas_var.get() if self.num_cuotas_var.get() else None,
                'detalle': self.observaciones_text.get('1.0', 'end-1c'),
                'total': total,
                'valor_iva': iva
            }
            
            doc_path = generate_cotizacion_doc(cotizacion_data, self.detalles, parent_window=self)
            
            if doc_path:
                messagebox.showinfo("Éxito", 
                    f"Cotización generada exitosamente.\nDocumento guardado en: {doc_path}")
                self.limpiar_formulario()
            else:
                messagebox.showerror("Error", 
                    "La cotización se guardó pero hubo un error al generar el documento")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar la cotización: {str(e)}")