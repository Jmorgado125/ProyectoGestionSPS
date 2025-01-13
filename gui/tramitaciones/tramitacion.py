import tkinter as tk
from tkinter import Canvas, Button, PhotoImage
from pathlib import Path

class IntegratedTramitacionesFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(bg="#FFFFFF")
        
        # Rutas de archivo
        self.OUTPUT_PATH = Path(__file__).parent
        self.ASSETS_PATH = self.OUTPUT_PATH / "assets" / "frame0"
        
        # Diccionarios para almacenar botones e imágenes
        self.buttons = {}
        self.images = {}
        
        # Tamaño de diseño original (p. ej. 1440x720)
        self.design_width = 1440
        self.design_height = 720
        
        # Coordenadas y tamaños originales de cada botón
        self.button_configs = {
            'button_1': {'x': 676.0, 'y': 294.0, 'width': 95.0, 'height': 40.0},
            'button_2': {'x': 676.0, 'y': 498.0, 'width': 95.0, 'height': 39.0},
            'button_3': {'x': 933.0, 'y': 494.0, 'width': 95.0, 'height': 40.0},
            'button_4': {'x': 443.0, 'y': 494.0, 'width': 95.0, 'height': 39.0},
            'button_5': {'x': 676.0, 'y': 402.0, 'width': 95.0, 'height': 39.0},
            'button_6': {'x': 933.0, 'y': 398.0, 'width': 95.0, 'height': 40.0},
            'button_7': {'x': 443.0, 'y': 398.0, 'width': 95.0, 'height': 39.0},
            'button_8': {'x': 443.0, 'y': 294.0, 'width': 95.0, 'height': 40.0},
            'button_9': {'x': 933.0, 'y': 294.0, 'width': 95.0, 'height': 40.0}
        }

        # Configurar el frame
        self.setup_frame()

    def relative_to_assets(self, path: str) -> Path:
        return self.ASSETS_PATH / Path(path)

    def on_resize(self, event):
        """Maneja el evento de redimensionamiento."""
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
            
            new_x = original['x'] * scale
            new_y = original['y'] * scale
            new_w = original['width'] * scale
            new_h = original['height'] * scale
            
            button.place(x=new_x, y=new_y, width=new_w, height=new_h)

    def setup_frame(self):
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
        
        # Agregar los textos
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
            'image_9': (738.0, 157.0),
            'image_10': (1131.0, 141.0)
        }

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
        print(f"{button_name} clicked")
        # Aquí agrega la lógica particular que necesites

    def add_text_labels(self):
        """Agrega los textos correspondientes en el canvas."""
        text_configs = [
            {"pos": (424.0, 269.0), "text": "text1"},
            {"pos": (662.0, 375.0), "text": "text4"},
            {"pos": (919.0, 375.0), "text": "text5"},
            {"pos": (432.0, 471.0), "text": "text6"},
            {"pos": (664.0, 468.0), "text": "text7"},
            {"pos": (919.0, 464.0), "text": "text8"},
            {"pos": (664.0, 269.0), "text": "text2"},
            {"pos": (921.0, 269.0), "text": "text3"},
            {"pos": (432.0, 375.0), "text": "text4"}
        ]
        
        for config in text_configs:
            self.canvas.create_text(
                config["pos"][0],
                config["pos"][1],
                anchor="nw",
                text=config["text"],
                fill="#000000",
                font=("Poppins SemiBold", 16 * -1)
            )