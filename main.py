import tkinter as tk
from gui.app_gui import App
import os

if __name__ == "__main__":
    try:
        # Intentar importar TkinterDnD
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except:
        # Si falla, usar Tk normal
        root = tk.Tk()
        
    # Establecer el icono de la ventana
    try:
        root.iconbitmap(os.path.join(os.getcwd(), "assets", "logo.ico"))
    except Exception as e:
        print("Error al establecer el icono:", e)
    app = App(root)
    root.mainloop()
