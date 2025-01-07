from gui.app_gui import App
import tkinter as tk
from tkinterdnd2 import TkinterDnD
from gui.app_gui import App

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = App(root)
    root.mainloop()
