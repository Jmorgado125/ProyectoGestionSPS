# excel_export.py
from tkinter import filedialog, messagebox
from openpyxl import Workbook
from PIL import Image, ImageTk

class ExcelExporter:
    def __init__(self):
        self.excel_icon = None
        self._load_excel_icon()
    
    def _load_excel_icon(self):
        """Carga el ícono de Excel desde assets"""
        try:
            excel_img = Image.open("assets/excel.png")
            excel_img = excel_img.resize((20, 20), Image.LANCZOS)
            self.excel_icon = ImageTk.PhotoImage(excel_img)
        except Exception as e:
            print(f"Error al cargar el ícono de Excel: {e}")
            self.excel_icon = None

    def export_to_excel(self, tree, title):
        """
        Exporta los datos del Treeview a Excel
        
        Args:
            tree: El Treeview que contiene los datos
            title: Título para el archivo Excel
        """
        try:
            # Preparar nombre del archivo
            filename = f"{title}.xlsx"
            filename = filename.replace(" ", "_").lower()
            
            # Crear nuevo libro Excel
            wb = Workbook()
            ws = wb.active
            
            # Obtener y escribir encabezados
            headers = []
            for col in tree["columns"]:
                headers.append(tree.heading(col)["text"])
            ws.append(headers)
            
            # Obtener y escribir datos
            for item in tree.get_children():
                row = list(tree.item(item)["values"])
                ws.append(row)
            
            # Ajustar anchos de columna
            for column_cells in ws.columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                ws.column_dimensions[column_cells[0].column_letter].width = length + 2
            
            # Diálogo para guardar archivo
            save_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                initialfile=filename,
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if save_path:
                wb.save(save_path)
                messagebox.showinfo("Éxito", "Datos exportados correctamente")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")

    def get_excel_icon(self):
        """Retorna el ícono de Excel cargado"""
        return self.excel_icon