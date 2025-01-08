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
    """
    try:
        # Configurar locale para formato de números
        locale.setlocale(locale.LC_ALL, 'es_CL.UTF-8')
        
        # Obtener la ruta del template
        template_path = os.path.join('formatos', 'cotizacion_template.doc')
        doc = DocxTemplate(template_path)
        
        # Preparar los detalles formateados
        detalles_formato = []
        for detalle in detalles:
            detalles_formato.append({
                'curso': detalle['nombre_curso'],
                'cantidad': detalle['cantidad'],
                'valor_unitario': locale.format_string("%d", detalle['valor_curso'], grouping=True),
                'valor_total': locale.format_string("%d", detalle['valor_total'], grouping=True)
            })
        
        # Preparar el contexto para el template
        context = {
            'numero_cotizacion': str(cotizacion_data['id_cotizacion']).zfill(4),
            'fecha': cotizacion_data['fecha_cotizacion'].strftime('%d de %B de %Y'),
            'fecha_vencimiento': cotizacion_data['fecha_vencimiento'].strftime('%d de %B de %Y'),
            'cliente': cotizacion_data['origen'],
            'contacto': cotizacion_data['nombre_contacto'],
            'email': cotizacion_data['email'],
            'detalles': detalles_formato,
            'subtotal': locale.format_string("%d", cotizacion_data['total'] - cotizacion_data['valor_iva'], grouping=True),
            'iva': locale.format_string("%d", cotizacion_data['valor_iva'], grouping=True),
            'total': locale.format_string("%d", cotizacion_data['total'], grouping=True),
            'forma_pago': cotizacion_data['modo_pago'],
            'metodo_pago': cotizacion_data['metodo_pago'],
            'num_cuotas': cotizacion_data['num_cuotas'] if cotizacion_data['num_cuotas'] else 'N/A',
            'observaciones': cotizacion_data['detalle'] if cotizacion_data['detalle'] else ''
        }
        
        # Renderizar el documento
        doc.render(context)
        
        # Solicitar al usuario la ubicación donde guardar el archivo
        default_filename = f"COT_{str(cotizacion_data['id_cotizacion']).zfill(4)}_{datetime.now().strftime('%Y%m%d')}.docx"
        output_path = filedialog.asksaveasfilename(
            parent=parent_window,
            defaultextension=".docx",
            initialfile=default_filename,
            filetypes=[("Documento Word", "*.docx"), ("Todos los archivos", "*.*")]
        )
        
        if not output_path:  # Si el usuario cancela la selección
            return None
        
        # Guardar el documento
        doc.save(output_path)
        return output_path
        
    except Exception as e:
        print(f"Error generando documento de cotización: {e}")
        return None