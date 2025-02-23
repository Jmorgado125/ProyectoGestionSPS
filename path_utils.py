import sys
import os

def resource_path(relative_path):
    """
    Obtiene la ruta absoluta del recurso, compatible con PyInstaller.

    Args:
        relative_path (str): Ruta relativa del recurso (ej: 'assets/logo1.ico').

    Returns:
        str: Ruta absoluta al recurso, válida tanto en modo desarrollo como en ejecutable.
    """
    try:
        # PyInstaller usa _MEIPASS para almacenar archivos temporales al ejecutar el .exe
        base_path = sys._MEIPASS
    except AttributeError:
        # En modo desarrollo, usa la carpeta actual del proyecto
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
