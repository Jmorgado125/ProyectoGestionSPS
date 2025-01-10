from docxtpl import DocxTemplate
import os
from datetime import datetime
import locale
from tkinter import filedialog

def generate_cotizacion_doc(cotizacion_data, detalles, parent_window=None):
    """
    Genera un documento de cotización usando el template.

    Args:
        cotizacion_data (dict): Datos de la cotización
        detalles (list): Lista de detalles de la cotización
        parent_window: Ventana padre para el diálogo de archivo

    Returns:
        str: Ruta del archivo generado o None si hubo un error
    """
    try:
        # Configurar locale para formato de números
        try:
            locale.setlocale(locale.LC_ALL, 'es_CL.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
            except locale.Error:
                print("Warning: No se pudo configurar el locale español")
                locale.setlocale(locale.LC_ALL, '')
        
        # Validar que existe el directorio de formatos
        formatos_dir = 'formatos'
        if not os.path.exists(formatos_dir):
            os.makedirs(formatos_dir)
            raise FileNotFoundError(f"El directorio '{formatos_dir}' no existía y ha sido creado. Por favor, coloque el template en este directorio.")
        
        # Obtener la ruta del template, solo .docx
        template_path_docx = os.path.join(formatos_dir, 'cotizacion_template.docx')
        
        if os.path.exists(template_path_docx):
            template_path = template_path_docx
        else:
            raise FileNotFoundError(f"No se encontró el template 'cotizacion_template.docx' en: {formatos_dir}")
        
        doc = DocxTemplate(template_path)
        
        # Validar datos requeridos
        required_fields = [
            'id_cotizacion', 'fecha_cotizacion', 'fecha_vencimiento', 
            'origen', 'nombre_contacto', 'email', 'modo_pago', 
            'metodo_pago', 'total'
        ]
        
        for field in required_fields:
            if field not in cotizacion_data:
                raise ValueError(f"Campo requerido faltante: {field}")
        
        # Preparar los detalles formateados, incluyendo el código del curso
        detalles_formato = []
        for detalle in detalles:
            if not all(k in detalle for k in ['id_curso', 'curso', 'cantidad', 'valor_curso', 'valor_total']):
                raise ValueError("Detalle incompleto: debe incluir id_curso, curso, cantidad, valor_curso y valor_total")
                
            detalle_formateado = {
                'codigo_curso': detalle['id_curso'],  # Incluyendo el código del curso
                'curso': detalle['curso'],
                'cantidad': str(detalle['cantidad']),
                'valor_unitario': f"${locale.format_string('%d', detalle['valor_curso'], grouping=True)}",
                'valor_total': f"${locale.format_string('%d', detalle['valor_total'], grouping=True)}"
            }
            detalles_formato.append(detalle_formateado)
        
        # Calcular subtotal (ya está calculado en ventana.py, pero se asegura aquí)
        subtotal = cotizacion_data['total']  # Sin IVA
        
        # Formatear fechas
        fecha = cotizacion_data['fecha_cotizacion'].strftime('%d de %B de %Y')
        fecha_vencimiento = cotizacion_data['fecha_vencimiento'].strftime('%d de %B de %Y')
        
        # Asignar el mes de la cotización
        mes = cotizacion_data['fecha_cotizacion'].strftime('%B')
        
        # Construir modo_completo
        modo_completo = f"{cotizacion_data['modo_pago']} - {cotizacion_data['metodo_pago']}"
        if cotizacion_data.get('num_cuotas'):
            modo_completo += f" ({cotizacion_data['num_cuotas']} cuotas)"
        
        # Preparar el contexto para el template
        context = {
            'numero_cotizacion': str(cotizacion_data['id_cotizacion']).zfill(4),
            'fecha': fecha,
            'fecha_vencimiento': fecha_vencimiento,
            'mes': mes,  # Incluido el mes de la cotización
            'cliente': cotizacion_data['origen'],
            'contacto': cotizacion_data['nombre_contacto'],
            'email': cotizacion_data['email'],
            'encargado': cotizacion_data.get('encargado', 'N/A'),
            'detalles': detalles_formato,
            'subtotal': f"${locale.format_string('%d', subtotal, grouping=True)}",
            'total': f"${locale.format_string('%d', cotizacion_data['total'], grouping=True)}",
            'forma_pago': cotizacion_data['modo_pago'],
            'metodo_pago': cotizacion_data['metodo_pago'],
            'num_cuotas': cotizacion_data.get('num_cuotas', 'N/A'),
            'observaciones': cotizacion_data.get('detalle', ''),
            'modo_completo': modo_completo,
            'year': datetime.now().year  # Agregado para el pie de página
        }
        
        # Renderizar el documento
        doc.render(context)
        
        # Crear el directorio de salida si no existe
        output_dir = os.path.join(os.getcwd(), 'cotizaciones_generadas')
        os.makedirs(output_dir, exist_ok=True)
        
        # Crear nombre de archivo con fecha y hora
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"COT_{str(cotizacion_data['id_cotizacion']).zfill(4)}_{timestamp}.docx"
        
        # Solicitar al usuario la ubicación donde guardar el archivo
        output_path = filedialog.asksaveasfilename(
            parent=parent_window,
            defaultextension=".docx",
            initialfile=default_filename,
            initialdir=output_dir,
            filetypes=[("Documento Word", "*.docx"), ("Todos los archivos", "*.*")]
        )
        
        if not output_path:  # Si el usuario cancela la selección
            return None
        
        # Asegurar que la extensión sea .docx
        if not output_path.lower().endswith('.docx'):
            output_path += '.docx'
        
        # Guardar el documento
        doc.save(output_path)
        return output_path
        
    except Exception as e:
        print(f"Error generando documento de cotización: {e}")
        import traceback
        traceback.print_exc()
        return None

def format_currency(value):
    """Función auxiliar para formatear valores monetarios"""
    try:
        return f"${locale.format_string('%d', value, grouping=True)}"
    except:
        return f"${value:,.0f}"
