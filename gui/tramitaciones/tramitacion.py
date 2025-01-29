import tkinter as tk
from tkinter import Canvas, Button, PhotoImage
from pathlib import Path

# Importamos tus ventanas específicas
from gui.tramitaciones.ap4 import Apendice4Window
from gui.tramitaciones.medicointer import MedicoInterWindow
from gui.tramitaciones.nacional import TituloNacionalWindow
from gui.tramitaciones.carta_omi import OMICertificationWindow
from gui.tramitaciones.habilitacion_sin import HabilitacionSinWindow
from gui.tramitaciones.habilitacion_con import HabilitacionWindow
from gui.tramitaciones.nave_menor import HabilitacionNaveMenorWindow
from gui.tramitaciones.ap6 import Apendice6Window
from gui.tramitaciones.libro import LibroClasesFrame


class IntegratedTramitacionesFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(bg="#FFFFFF")

        # Referencias a ventanas secundarias
        self.ap4_window = None
        self.medico_window = None
        self.nacional_window = None
        self.carta_omi_window = None
        self.habilitacion_sin_window = None
        self.habilitacion_con_window = None
        self.nave_menor_window= None
        self.libro_window = None
        self.ap6_window = None
        
        # Rutas de archivo
        self.OUTPUT_PATH = Path(__file__).parent
        self.ASSETS_PATH = self.OUTPUT_PATH / "assets" / "frame0"
        
        # Diccionarios para almacenar botones, imágenes y textos
        self.buttons = {}
        self.images = {}
        self.text_labels = {}
        
        # Tamaño de diseño original (p. ej. 1440x720)
        self.design_width = 1440
        self.design_height = 720
        
        # Coordenadas y tamaños originales de cada botón
        self.button_configs = {
            'button_1': {'x': 443.0, 'y': 294.0, 'width': 95.0, 'height': 40.0},
            'button_2': {'x': 676.0, 'y': 294.0, 'width': 95.0, 'height': 39.0},
            'button_3': {'x': 933.0, 'y': 294.0, 'width': 95.0, 'height': 40.0},
            'button_4': {'x': 443.0, 'y': 398.0, 'width': 95.0, 'height': 39.0},
            'button_5': {'x': 676.0, 'y': 402.0, 'width': 95.0, 'height': 39.0},
            'button_6': {'x': 933.0, 'y': 398.0, 'width': 95.0, 'height': 40.0},
            'button_7': {'x': 443.0, 'y': 494.0, 'width': 95.0, 'height': 39.0},
            'button_8': {'x': 676.0, 'y': 498.0, 'width': 95.0, 'height': 40.0},
            'button_9': {'x': 933.0, 'y': 494.0, 'width': 95.0, 'height': 40.0}
        }

        # Configurar el frame principal
        self.setup_frame()

    def relative_to_assets(self, path: str) -> Path:
        """Devuelve la ruta completa para un archivo dentro de la carpeta de assets."""
        return self.ASSETS_PATH / Path(path)

    def on_resize(self, event):
        """Maneja el evento de redimensionamiento de la ventana."""
        width = event.width
        height = event.height
        
        # Ajustamos el tamaño del canvas
        self.canvas.configure(width=width, height=height)
        
        # Calculamos la escala con base en el tamaño original de diseño
        scale_x = width / self.design_width
        scale_y = height / self.design_height
        scale = min(scale_x, scale_y)  # Mantenemos proporciones
        
        # Reposicionar y escalar cada botón desde sus coordenadas originales
        for btn_name, button in self.buttons.items():
            original = self.button_configs[btn_name]
            
            new_x = original['x'] * scale + 75
            new_y = original['y'] * scale
            new_w = original['width'] * scale
            new_h = original['height'] * scale
            
            button.place(x=new_x, y=new_y, width=new_w, height=new_h)
            
            # Si hay etiqueta asignada a este botón, reposicionarla justo encima
            if btn_name in self.text_labels:
                label = self.text_labels[btn_name]
                label.place(x=new_x - 5, y=new_y - 38)
                label.lift()  # Se asegura que la etiqueta quede encima

    def setup_frame(self):
        """Configura el frame principal con su Canvas y elementos."""
        # Canvas principal
        self.canvas = Canvas(
            self,
            bg="#FFFFFF",
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.pack(fill="both", expand=True)

        # Vinculamos el evento de redimensionado
        self.bind("<Configure>", self.on_resize)

        # Cargar imágenes de fondo
        self.load_background_images()
        
        # Crear y ubicar los botones
        self.create_buttons()
        
        # Agregar los textos (etiquetas) sobre los botones
        self.add_text_labels()

    def load_background_images(self):
        """Carga las imágenes de fondo en el canvas."""
        self.image_image_1 = PhotoImage(file=self.relative_to_assets("image_1.png"))
        self.canvas.create_image(720.0, 360.0, image=self.image_image_1)
        self.images['background'] = self.image_image_1

        image_positions = {
            'image_2': (248.0, 587.0),
            'image_3': (1269.0, 310.0),
            'image_4': (720.0, 76.0),
            'image_5': (720.0, 370.0),
            'image_6': (227.0, 245.0),
            'image_7': (720.0, 65.0),
            'image_8': (1225.0, 507.0),
            'image_9': (730.0, 157.0),
            'image_10': (1131.0, 141.0)
        }

        # Carga cada imagen de acuerdo a su posición
        for image_name, (x, y) in image_positions.items():
            image = PhotoImage(file=self.relative_to_assets(f"{image_name}.png"))
            self.images[image_name] = image
            self.canvas.create_image(x, y, image=image)

    def create_buttons(self):
        """Crea y ubica los botones con base en la configuración original."""
        for btn_name, config in self.button_configs.items():
            image = PhotoImage(file=self.relative_to_assets(f"{btn_name}.png"))
            self.images[btn_name] = image
            
            button = Button(
                self,
                image=image,
                borderwidth=0,
                highlightthickness=0,
                command=lambda n=btn_name: self.handle_button_click(n),
                relief="flat"
            )
            # Ubicación y tamaño originales
            button.place(
                x=config['x'],
                y=config['y'],
                width=config['width'],
                height=config['height']
            )
            self.buttons[btn_name] = button

    def handle_button_click(self, button_name):
        """Maneja la acción de cada botón."""
        if button_name == 'button_1':
            self.open_apendice4()
        elif button_name == 'button_2':
            self.open_medico_inter()
        elif button_name == 'button_3':
            self.open_titulo_nacional()
        elif button_name == 'button_4':
            self.open_carta_omi()
        elif button_name == 'button_5':
            self.open_habilitacion_sin()
        elif button_name == 'button_6':
            self.open_habilitacion_con()
        elif button_name == 'button_7':
            self.open_nave_menor()
        elif button_name == 'button_8':
            self.open_libro()
        elif button_name == 'button_9':
            self.open_apendice6()
        else:
            print(f"{button_name} clicked")

    def open_apendice4(self):
        """Abre la ventana de Apéndice 4 en un Toplevel."""
        if self.ap4_window is None or not self.ap4_window.winfo_exists():
            window = tk.Toplevel(self)
            window.title("Apéndice N° 4")
            window.state('zoomed')  # Maximizar ventana
            
            self.ap4_window = Apendice4Window(window)
            self.ap4_window.pack(fill='both', expand=True)
        else:
            self.ap4_window.lift()
    
    def open_apendice6(self):
        """Abre la ventana de Apéndice 6 en un Toplevel."""
        if self.ap6_window is None or not self.ap6_window.winfo_exists():
            window = tk.Toplevel(self)
            window.title("Apéndice N° 6")
            window.state('zoomed')  # Maximizar ventana
            
            self.ap6_window = Apendice6Window(window)
            self.ap6_window.pack(fill='both', expand=True)
        else:
            self.ap6_window.lift()

    def open_libro(self):
        """Abre la ventana de libro de curso en un Toplevel."""
        if self.libro_window is None or not self.libro_window.winfo_exists():
            window = tk.Toplevel(self)
            window.title("Habilitación Sin Título Internacional")
            
            # Establecer un tamaño fijo más compacto
            window_width = 470
            window_height = 420
            
            # Obtener dimensiones de la pantalla
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            
            # Calcular posición para centrar
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            # Configurar geometría y posición
            window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Prevenir redimensión
            window.resizable(False, False)
            
            # Asegurar que esta ventana sea modal
            window.transient(self)
            window.grab_set()
            
            # Crear y empaquetar la ventana de habilitación
            self.libro_window = LibroClasesFrame(window)
            self.libro_window.pack(fill='both', expand=True)
        else:
            self.libro_window.lift()

    def open_medico_inter(self):
        """Abre la ventana de MedicoInter en un Toplevel."""
        if self.medico_window is None or not self.medico_window.winfo_exists():
            window = tk.Toplevel(self)
            window.title("Médico Internacional")
            window.geometry("400x300")  # Establecer tamaño de la ventana más pequeño
            window.update_idletasks()
            x = (window.winfo_screenwidth() - window.winfo_reqwidth()) // 2
            y = (window.winfo_screenheight() - window.winfo_reqheight()) // 2
            window.geometry(f"+{x}+{y}")  # Centrar la ventana

            self.medico_window = MedicoInterWindow(window)
            self.medico_window.pack(fill='both', expand=True)
        else:
            self.medico_window.lift()

    def open_titulo_nacional(self):
        """Abre la ventana de titulo nacional en un Toplevel."""
        if self.nacional_window is None or not self.nacional_window.winfo_exists():
            window = tk.Toplevel(self)
            window.title("Titulo Nacional")
            window.geometry("400x300")  # Establecer tamaño de la ventana más pequeño
            window.update_idletasks()
            x = (window.winfo_screenwidth() - window.winfo_reqwidth()) // 2
            y = (window.winfo_screenheight() - window.winfo_reqheight()) // 2
            window.geometry(f"+{x}+{y}")  # Centrar la ventana

            self.nacional_window = TituloNacionalWindow(window)
            self.nacional_window.pack(fill='both', expand=True)
        else:
            self.nacional_window.lift()
    
    def open_habilitacion_sin(self):
        """Abre la ventana de habilitación sin título en un Toplevel."""
        if self.habilitacion_sin_window is None or not self.habilitacion_sin_window.winfo_exists():
            window = tk.Toplevel(self)
            window.title("Habilitación Sin Título Internacional")
            
            # Establecer un tamaño fijo más compacto
            window_width = 470
            window_height = 420
            
            # Obtener dimensiones de la pantalla
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            
            # Calcular posición para centrar
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            # Configurar geometría y posición
            window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Prevenir redimensión
            window.resizable(False, False)
            
            # Asegurar que esta ventana sea modal
            window.transient(self)
            window.grab_set()
            
            # Crear y empaquetar la ventana de habilitación
            self.habilitacion_sin_window = HabilitacionSinWindow(window)
            self.habilitacion_sin_window.pack(fill='both', expand=True)
        else:
            self.habilitacion_sin_window.lift()

    def open_nave_menor(self):
        """Abre la ventana de habilitación sin título en un Toplevel."""
        if self.nave_menor_window is None or not self.nave_menor_window.winfo_exists():
            window = tk.Toplevel(self)
            window.title("Habilitación Sin Título Internacional")
            
            # Establecer un tamaño fijo más compacto
            window_width = 470
            window_height = 420
            
            # Obtener dimensiones de la pantalla
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            
            # Calcular posición para centrar
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            # Configurar geometría y posición
            window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Prevenir redimensión
            window.resizable(False, False)
            
            # Asegurar que esta ventana sea modal
            window.transient(self)
            window.grab_set()
            
            # Crear y empaquetar la ventana de habilitación
            self.nave_menor_window = HabilitacionNaveMenorWindow(window)
            self.nave_menor_window.pack(fill='both', expand=True)
        else:
            self.nave_menor_window.lift()


    def open_habilitacion_con(self):
        """Abre la ventana de titulo nacional en un Toplevel."""
        if self.habilitacion_con_window is None or not self.habilitacion_con_window.winfo_exists():
            window = tk.Toplevel(self)
            window.title("Habilitacón Sin Titulo")
            # Establecer un tamaño fijo más compacto
            window_width = 470
            window_height = 420
            # Obtener dimensiones de la pantalla
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight() 
            # Calcular posición para centrar
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2 
            # Configurar geometría y posición
            window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            # Prevenir redimensión
            window.resizable(False, False)
            # Asegurar que esta ventana sea modal
            window.transient(self)
            window.grab_set()
            self.habilitacion_con_window = HabilitacionWindow(window)
            self.habilitacion_con_window.pack(fill='both', expand=True)    
        else:
            self.habilitacion_con_window.lift()   
             

    def open_carta_omi(self):
        """Abre la ventana de carta OMI en un Toplevel."""
        if self.carta_omi_window is None or not self.carta_omi_window.winfo_exists():
            window = tk.Toplevel(self)
            window.title("Carta Internacional OMI")
            
            # Establecer tamaño fijo
            width = 600
            height = 570
            window.geometry(f"{width}x{height}")
            
            # Deshabilitar redimensionamiento
            window.resizable(False, False)
            
            # Centrar la ventana
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            window.geometry(f"+{x}+{y}")
            
            # Hacer que la ventana sea modal
            window.transient(self)
            window.grab_set()
            
            # Crear la instancia de OMICertificationWindow
            self.carta_omi_window = OMICertificationWindow(window)
            self.carta_omi_window.pack(fill='both', expand=True)
        else:
            self.carta_omi_window.lift()
            self.carta_omi_window.focus_force() 

    def add_text_labels(self):
        """
        Agrega los textos (títulos) justo encima de cada botón.
        Puedes personalizar el texto de cada botón según tu necesidad.
        """
        textos_por_boton = {
            'button_1': "Apéndice N° 4",
            'button_2': "Titulo y Médico\nIntern.",
            'button_3': "Título Nacional",
            'button_4': "Carta OMI",
            'button_5': "Habilitación Nave\nmayor Sin Titulo",
            'button_6': "Habilitación Nave\nmayor Con Titulo",
            'button_7': "Habilitación\nNave Menor",
            'button_8': "Libro de Curso\nFormación",
            'button_9': "Apéndice N° 6"
        }
        
        for btn_name, text in textos_por_boton.items():
            label = tk.Label(
                self,
                text=text,
                bg="#FFFFFF",  
                fg="#000000",
                font=("Arial Black", 8)
            )
            config = self.button_configs[btn_name]
            label.place(
                x=config['x'],
                y=config['y'] - 25
            )
            label.lift()
            self.text_labels[btn_name] = label


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1440x720")
    app = IntegratedTramitacionesFrame(root)
    app.pack(fill="both", expand=True)
    root.mainloop()
