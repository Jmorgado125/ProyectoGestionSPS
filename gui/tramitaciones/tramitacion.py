import tkinter as tk
from tkinter import Canvas, Button, PhotoImage
from pathlib import Path
from PIL import Image, ImageTk

# Importamos las ventanas específicas
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

        # Ventanas secundarias (se reutilizarán para evitar recrearlas cada vez)
        self.ap4_window = None
        self.medico_window = None
        self.nacional_window = None
        self.carta_omi_window = None
        self.habilitacion_sin_window = None
        self.habilitacion_con_window = None
        self.nave_menor_window = None
        self.libro_window = None
        self.ap6_window = None

        # Rutas de archivos
        self.OUTPUT_PATH = Path(__file__).parent
        self.ASSETS_PATH = self.OUTPUT_PATH / "assets" / "frame0"

        # Diccionarios para almacenar botones, imágenes y textos
        self.buttons = {}
        self.images = {}          # Cachea PhotoImage (botones y fondo)
        self.text_labels = {}

        # Imágenes de fondo originales (PIL), IDs en el canvas y posiciones originales
        self.bg_original_images = {}
        self.bg_image_ids = {}
        self.bg_positions = {}

        # Tamaño de diseño original
        self.design_width = 1440
        self.design_height = 720

        # Configuración de cada botón (coordenadas y tamaño)
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

        self.setup_frame()

    def relative_to_assets(self, path: str) -> Path:
        """Devuelve la ruta completa para un archivo dentro de la carpeta assets."""
        return self.ASSETS_PATH / Path(path)

    def on_resize(self, event):
        """Optimiza el redimensionamiento usando debounce para evitar múltiples ejecuciones."""
        if hasattr(self, '_resize_job'):
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(100, self._perform_resize, event.width, event.height)

    def _perform_resize(self, width, height):
        self.canvas.configure(width=width, height=height)

        scale_x = width / self.design_width
        scale_y = height / self.design_height
        scale = min(scale_x, scale_y)

        # Reposicionar y redimensionar botones y sus etiquetas
        for btn_name, button in self.buttons.items():
            original = self.button_configs[btn_name]
            new_x = original['x'] * scale
            new_y = original['y'] * scale
            new_w = original['width'] * scale
            new_h = original['height'] * scale
            button.place(x=new_x, y=new_y, width=new_w, height=new_h)

            if btn_name in self.text_labels:
                label = self.text_labels[btn_name]
                label.place(x=new_x - 5, y=new_y - 38)
                label.lift()

        # Redimensionar imágenes de fondo
        for name, orig_pos in self.bg_positions.items():
            orig_x, orig_y = orig_pos
            new_x = orig_x * scale
            new_y = orig_y * scale
            self.canvas.coords(self.bg_image_ids[name], new_x, new_y)

            orig_img = self.bg_original_images[name]
            new_width = int(orig_img.width * scale)
            new_height = int(orig_img.height * scale)
            resized_img = orig_img.resize((new_width, new_height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(resized_img)
            self.images[name] = photo
            self.canvas.itemconfig(self.bg_image_ids[name], image=photo)

    def setup_frame(self):
        """Configura el canvas principal, carga imágenes y crea botones."""
        self.canvas = Canvas(
            self,
            bg="#FFFFFF",
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.pack(fill="both", expand=True)

        # Vincula el evento de redimensionado con debounce
        self.bind("<Configure>", self.on_resize)

        self.load_background_images()
        self.create_buttons()
        self.add_text_labels()

    def load_background_images(self):
        """Carga y posiciona las imágenes de fondo en el canvas."""
        # Imagen de fondo principal
        img1 = Image.open(self.relative_to_assets("image_1.png"))
        self.bg_original_images["image_1"] = img1
        self.bg_positions["image_1"] = (720.0, 360.0)
        photo1 = ImageTk.PhotoImage(img1)
        self.images["image_1"] = photo1
        id1 = self.canvas.create_image(720.0, 360.0, image=photo1)
        self.bg_image_ids["image_1"] = id1

        # Otras imágenes de fondo con sus posiciones originales
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
        for name, (x, y) in image_positions.items():
            img = Image.open(self.relative_to_assets(f"{name}.png"))
            self.bg_original_images[name] = img
            self.bg_positions[name] = (x, y)
            photo = ImageTk.PhotoImage(img)
            self.images[name] = photo
            id_img = self.canvas.create_image(x, y, image=photo)
            self.bg_image_ids[name] = id_img

    def create_buttons(self):
        """Crea y posiciona los botones según la configuración definida."""
        for btn_name, config in self.button_configs.items():
            image = PhotoImage(file=self.relative_to_assets(f"{btn_name}.png"))
            self.images[btn_name] = image

            button = Button(
                self,
                image=image,
                borderwidth=0,
                highlightthickness=0,
                command=lambda n=btn_name: self.handle_button_click(n),
                relief="flat",
                bg="#FFFFFF",
                activebackground="#FFFFFF"
            )
            button.place(
                x=config['x'],
                y=config['y'], 
                width=config['width'],
                height=config['height']
            )
            self.buttons[btn_name] = button

    def add_text_labels(self):
        """Agrega etiquetas de texto sobre cada botón."""
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

    def handle_button_click(self, button_name):
        """Abre la ventana correspondiente al presionar un botón."""
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

    # Función auxiliar para crear ventanas Toplevel sin mostrar animación de redimensionamiento
    def _create_toplevel(self, title, geometry=None, state=None, resizable=(True, True), transient=True, grab=True):
        window = tk.Toplevel(self)
        window.withdraw()  # Oculta la ventana mientras se configura
        window.title(title)
        if geometry:
            window.geometry(geometry)
        if state:
            window.state(state)
        window.resizable(*resizable)
        if transient:
            window.transient(self)
        if grab:
            window.grab_set()
        # Se inicia transparente para evitar que se muestre en un estado intermedio
        window.attributes("-alpha", 0.0)
        return window

    # Cada función de apertura usa la función auxiliar para que la ventana ya aparezca en su tamaño final

    def open_apendice4(self):
        if self.ap4_window is None or not self.ap4_window.winfo_exists():
            window = self._create_toplevel(title="Apéndice N° 4", state="zoomed")
            self.ap4_window = Apendice4Window(window)
            self.ap4_window.pack(fill='both', expand=True)
            window.update_idletasks()
            window.attributes("-alpha", 1.0)
            window.deiconify()
        else:
            self.ap4_window.lift()

    def open_apendice6(self):
        if self.ap6_window is None or not self.ap6_window.winfo_exists():
            window = self._create_toplevel(title="Apéndice N° 6", state="zoomed")
            self.ap6_window = Apendice6Window(window)
            self.apendice6_pack(window)
            self.ap6_window.pack(fill='both', expand=True)
            window.update_idletasks()
            window.attributes("-alpha", 1.0)
            window.deiconify()
        else:
            self.ap6_window.lift()

    def open_libro(self):
        if self.libro_window is None or not self.libro_window.winfo_exists():
            geom = self._center_geometry(470, 420)
            window = self._create_toplevel(title="Habilitación Sin Título Internacional", geometry=geom, resizable=(False, False))
            self.libro_window = LibroClasesFrame(window)
            self.libro_window.pack(fill='both', expand=True)
            window.update_idletasks()
            window.attributes("-alpha", 1.0)
            window.deiconify()
        else:
            self.libro_window.lift()

    def open_medico_inter(self):
        if self.medico_window is None or not self.medico_window.winfo_exists():
            geom = self._center_geometry(400, 300)
            window = self._create_toplevel(title="Médico Internacional", geometry=geom)
            self.medico_window = MedicoInterWindow(window)
            self.medico_window.pack(fill='both', expand=True)
            window.update_idletasks()
            window.attributes("-alpha", 1.0)
            window.deiconify()
        else:
            self.medico_window.lift()

    def open_titulo_nacional(self):
        if self.nacional_window is None or not self.nacional_window.winfo_exists():
            geom = self._center_geometry(400, 300)
            window = self._create_toplevel(title="Titulo Nacional", geometry=geom)
            self.nacional_window = TituloNacionalWindow(window)
            self.nacional_window.pack(fill='both', expand=True)
            window.update_idletasks()
            window.attributes("-alpha", 1.0)
            window.deiconify()
        else:
            self.nacional_window.lift()

    def open_habilitacion_sin(self):
        if self.habilitacion_sin_window is None or not self.habilitacion_sin_window.winfo_exists():
            geom = self._center_geometry(470, 420)
            window = self._create_toplevel(title="Habilitación Sin Título Internacional", geometry=geom, resizable=(False, False))
            self.habilitacion_sin_window = HabilitacionSinWindow(window)
            self.habilitacion_sin_window.pack(fill='both', expand=True)
            window.update_idletasks()
            window.attributes("-alpha", 1.0)
            window.deiconify()
        else:
            self.habilitacion_sin_window.lift()

    def open_nave_menor(self):
        if self.nave_menor_window is None or not self.nave_menor_window.winfo_exists():
            geom = self._center_geometry(470, 420)
            window = self._create_toplevel(title="Habilitación Sin Título Internacional", geometry=geom, resizable=(False, False))
            self.nave_menor_window = HabilitacionNaveMenorWindow(window)
            self.nave_menor_window.pack(fill='both', expand=True)
            window.update_idletasks()
            window.attributes("-alpha", 1.0)
            window.deiconify()
        else:
            self.nave_menor_window.lift()

    def open_habilitacion_con(self):
        if self.habilitacion_con_window is None or not self.habilitacion_con_window.winfo_exists():
            geom = self._center_geometry(470, 420)
            window = self._create_toplevel(title="Habilitación Sin Titulo", geometry=geom, resizable=(False, False))
            self.habilitacion_con_window = HabilitacionWindow(window)
            self.habilitacion_con_window.pack(fill='both', expand=True)
            window.update_idletasks()
            window.attributes("-alpha", 1.0)
            window.deiconify()
        else:
            self.habilitacion_con_window.lift()

    def open_carta_omi(self):
        if self.carta_omi_window is None or not self.carta_omi_window.winfo_exists():
            geom = self._center_geometry(600, 570)
            window = self._create_toplevel(title="Carta Internacional OMI", geometry=geom, resizable=(False, False))
            self.carta_omi_window = OMICertificationWindow(window)
            self.carta_omi_window.pack(fill='both', expand=True)
            window.update_idletasks()
            window.attributes("-alpha", 1.0)
            window.deiconify()
        else:
            self.carta_omi_window.lift()
            self.carta_omi_window.focus_force()

    def _center_geometry(self, width, height):
        """Calcula la geometría centrada para una ventana de ancho 'width' y alto 'height'."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        return f"{width}x{height}+{x}+{y}"

    # Ejemplo: método para empaquetar Apendice6 (si necesitas lógica adicional, de lo contrario puedes omitirlo)
    def apendice6_pack(self, window):
        pass  # Ajusta según lo que requiera Apendice6Window


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1440x720")
    app = IntegratedTramitacionesFrame(root)
    app.pack(fill="both", expand=True)
    root.mainloop()
