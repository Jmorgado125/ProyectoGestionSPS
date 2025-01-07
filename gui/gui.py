# gui/gui.py
from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Entry, Button, PhotoImage
import os

class LoginFrame:
    def __init__(self, parent, callback):
        """
        parent: la ventana (root) o Frame padre.
        callback: la función a la que llamaremos cuando el usuario haga login.
        """
        self.parent = parent
        self.callback = callback

        # Maximiza la ventana (Windows: muestra barra de tareas).
        self.parent.state('zoomed')

        # Tamaño base para el escalado.
        self.original_width = 1280
        self.original_height = 832
        self.last_width = self.original_width
        self.last_height = self.original_height

        # Frame principal
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Ruta a la carpeta de assets
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        self.ASSETS_PATH = Path(project_root) / "assets"

        # Canvas con fondo (lo ponemos azul oscuro para que no se vea blanco)
        self.canvas = Canvas(
            self.frame,
            bg="#FFFFFF",  # color de fondo (oscuro)
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Almacén de imágenes
        self.images = {}
        self.image_items = {}

        # Escalado en evento <Configure>
        self.frame.bind('<Configure>', self.on_resize)

        # Creamos la interfaz
        self.setup_login_interface()

    def relative_to_assets(self, path: str) -> Path:
        return self.ASSETS_PATH / Path(path)

    def on_resize(self, event):
        """ Escala los elementos del canvas y recoloca los widgets. """
        new_width = event.width
        new_height = event.height
        scale_x = new_width / self.last_width
        scale_y = new_height / self.last_height

        # Escalamos todo lo que tenga "login_group"
        self.canvas.scale("login_group", 0, 0, scale_x, scale_y)

        self.canvas.config(width=new_width, height=new_height)

        # Reubicar los Entry y el botón
        self.update_widget_positions(new_width, new_height)

        self.last_width = new_width
        self.last_height = new_height

    def update_widget_positions(self, new_width, new_height):
        """ Recalcula posiciones para Entry y Botón (no se escalan con .scale). """
        scale_x = new_width / self.original_width
        scale_y = new_height / self.original_height

        # Usuario
        self.entry_2.place(
            x=954.0 * scale_x,
            y=415.0 * scale_y,
            width=157.0 * scale_x,
            height=18.0 * scale_y
        )

        # Contraseña
        self.entry_1.place(
            x=954.0 * scale_x,
            y=506.0 * scale_y,
            width=157.0 * scale_x,
            height=18.0 * scale_y
        )

        # Botón (un poco más de altura para el PNG)
        self.button_1.place(
            x=903.0  * scale_x,
            y=565.0  * scale_y,   # un poco más arriba o abajo según tu preferencia
            width=230.0 * scale_x,
            height=40.0 * scale_y # más alto para que no se vea cortado
        )

    def setup_login_interface(self):
        """ Carga imágenes y crea los widgets en posiciones fijas de diseño. """
        # Imagen de fondo principal (por ejemplo "image_3" si ese es tu background)
        # Moverla lo más a la izquierda, x=0. Ajusta y según tu imagen:
        # OJO: Si tu imagen de fondo es 'image_3.png', ajusta aquí:
        self.images['bg_main'] = PhotoImage(file=self.relative_to_assets("image_3.png"))
        # Lo situamos con x=0, y=0 para que ocupe la parte izquierda
        self.canvas.create_image(
            0, 0,
            image=self.images['bg_main'],
            anchor="nw",       # ancla en la esquina superior izquierda
            tags="login_group"
        )

        # Entry Contraseña (fondo)
        self.entry_image_1 = PhotoImage(file=self.relative_to_assets("entry_1.png"))
        self.canvas.create_image(
            1032.5, 516.0,
            image=self.entry_image_1,
            tags="login_group"
        )
        self.entry_1 = Entry(
            self.frame,
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0,
            show="*"
        )
        self.entry_1.place(x=954.0, y=506.0, width=157.0, height=18.0)

        # Entry Usuario (fondo)
        self.entry_image_2 = PhotoImage(file=self.relative_to_assets("entry_2.png"))
        self.canvas.create_image(
            1032.5, 425.0,
            image=self.entry_image_2,
            tags="login_group"
        )
        self.entry_2 = Entry(
            self.frame,
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0
        )
        self.entry_2.place(x=954.0, y=415.0, width=157.0, height=18.0)

        # Círculos y otras imágenes decorativas
        # Mover a la parte inferior izquierda. No importa si se cortan.
        image_positions = {
            # Nota: Ajusta las posiciones de modo que queden abajo a la izquierda
            4: (150.0, 750.0),  # Uno de los círculos
            5: (280.0, 720.0),  # Otro círculo
            # Resto de imágenes decorativas
            1: (1018.0, 423.0),
            2: (1018.0, 515.0),
            6: (417.0, 192.0),
            7: (417.0, 442.0),
            8: (1016.0, 327.0),
            9: (947.0, 481.0),
            10: (923.0, 515.0),
            11: (932.0, 377.0),
            12: (921.0, 423.0)
        }

        for i in image_positions:
            filename = f"image_{i}.png"
            img = PhotoImage(file=self.relative_to_assets(filename))
            self.images[f'image_{i}'] = img
            x, y = image_positions[i]
            item_id = self.canvas.create_image(
                x, y,
                image=img,
                tags="login_group"
            )
            self.image_items[f'image_{i}'] = item_id

        # Botón "Ingresar"
        self.button_image = PhotoImage(file=self.relative_to_assets("button_1.png"))
        self.button_1 = Button(
            self.frame,
            image=self.button_image,
            borderwidth=0,
            highlightthickness=0,
            command=self.handle_login,
            relief="flat",
            cursor="hand2"
        )
        # Ajustar para mayor altura
        self.button_1.place(
            x=903.0, y=565.0,
            width=230.0, height=40.0
        )

    def handle_login(self):
        """ Cuando se hace clic en el botón "Ingresar". """
        username = self.entry_2.get()
        password = self.entry_1.get()
        self.callback(username, password)

    def show(self):
        """ Muestra el frame y (opcional) maximiza la ventana. """
        self.parent.state('zoomed')
        self.last_width = self.original_width
        self.last_height = self.original_height
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """ Oculta este frame. """
        self.frame.pack_forget()
