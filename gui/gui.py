from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Entry, Button, ttk, messagebox
import os
from database.db_config import connect_db
from PIL import Image, ImageTk  # Se usa PIL para poder redimensionar imágenes

class LoginFrame:
    def __init__(self, parent, callback):
        """
        parent: la ventana (root) o Frame padre.
        callback: función a la que se llamará cuando el usuario haga login.
        """
        self.parent = parent
        self.callback = callback

        # Maximiza la ventana (Windows: muestra barra de tareas).
        self.parent.state('zoomed')

        # Tamaño base para el escalado (diseño base).
        self.original_width = 1280
        self.original_height = 832

        # Frame principal
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Ruta a la carpeta de assets
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        self.ASSETS_PATH = Path(project_root) / "assets"

        # Canvas con fondo
        self.canvas = Canvas(
            self.frame,
            bg="#FFFFFF",
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Diccionarios para manejar imágenes y coordenadas originales
        self.original_images = {}      # Almacena las imágenes PIL originales
        self.images = {}               # Almacena las imágenes redimensionadas (ImageTk.PhotoImage)
        self.canvas_items = {}         # Guarda el ID de cada item del canvas
        self.canvas_item_orig_coords = {}  # Guarda las coordenadas originales (x, y, anchor) de cada item

        # Vinculamos el evento de redimensionado
        self.canvas.bind('<Configure>', self.on_resize)

        # Creamos la interfaz de login
        self.setup_login_interface()

    def setup_styles(self):
        style = ttk.Style()
        style.configure('Action.TButton',
                        font=('Helvetica', 10, 'bold'),
                        padding=(10, 5),
                        background='#00239c',
                        foreground='white',
                        relief='raised',
                        borderwidth=1)
        style.map('Action.TButton',
                  background=[('active', '#001970'),
                              ('pressed', '#00239c')],
                  foreground=[('active', 'white'),
                              ('pressed', 'white')],
                  relief=[('pressed', 'sunken')])
        style.configure('delete.TButton',
                        font=('Helvetica', 10, 'bold'),
                        padding=(10, 5),
                        background='#b50707',
                        foreground='white',
                        relief='raised',
                        borderwidth=1)
        style.map('delete.TButton',
                  background=[('active', '#990606'),
                              ('pressed', '#b50707')],
                  foreground=[('active', 'white'),
                              ('pressed', 'white')],
                  relief=[('pressed', 'sunken')])

    def relative_to_assets(self, path: str) -> Path:
        return self.ASSETS_PATH / Path(path)

    def on_resize(self, event):
        """
        Se ejecuta cada vez que cambia el tamaño de la ventana;
        actualiza el canvas y reposiciona/redimensiona las imágenes y widgets.
        """
        new_width = event.width
        new_height = event.height
            # Si las dimensiones son muy pequeñas, se omite la actualización
        if new_width < 100 or new_height < 100:
            return  

        # Actualizamos el tamaño del canvas
        self.canvas.config(width=new_width, height=new_height)

        # Actualizamos las imágenes del canvas y la posición de los widgets
        self.update_canvas_items(new_width, new_height)
        self.update_widget_positions(new_width, new_height)

    def update_canvas_items(self, new_width, new_height):
        # Escala para los elementos "normales"
        scale_x = new_width / self.original_width
        scale_y = new_height / self.original_height
        uniform_scale = min(scale_x, scale_y)

        for key, (orig_x, orig_y, anchor) in self.canvas_item_orig_coords.items():
            if key == "bg_main":
                # Para el fondo, queremos que su ancho sea el 75% del ancho del canvas
                new_bg_width = int(new_width * 0.65)
                orig_img = self.original_images[key]
                orig_bg_width, orig_bg_height = orig_img.size
                # Calcula la nueva altura manteniendo la relación de aspecto
                new_bg_height = int(new_bg_width * (orig_bg_height / orig_bg_width))
                # Redimensiona la imagen usando Image.Resampling.LANCZOS
                resized_img = orig_img.resize((new_bg_width, new_bg_height), resample=Image.Resampling.LANCZOS)
                new_photo = ImageTk.PhotoImage(resized_img)
                self.images[key] = new_photo
                # Coloca la imagen; por ejemplo, la ubicamos en (0,0)
                self.canvas.coords(self.canvas_items[key], 0, 0)
                self.canvas.itemconfig(self.canvas_items[key], image=new_photo)
            else:
                # Para los demás elementos, se usan las coordenadas originales escaladas
                new_x = orig_x * scale_x
                new_y = orig_y * scale_y
                self.canvas.coords(self.canvas_items[key], new_x, new_y)
                if key in self.original_images:
                    orig_img = self.original_images[key]
                    orig_img_width, orig_img_height = orig_img.size
                    new_img_width = max(1, int(orig_img_width * uniform_scale))
                    new_img_height = max(1, int(orig_img_height * uniform_scale))
                    resized_img = orig_img.resize((new_img_width, new_img_height), resample=Image.Resampling.LANCZOS)
                    new_photo = ImageTk.PhotoImage(resized_img)
                    self.images[key] = new_photo
                    self.canvas.itemconfig(self.canvas_items[key], image=new_photo)


    def update_widget_positions(self, new_width, new_height):
        scale_x = new_width / self.original_width
        scale_y = new_height / self.original_height
        offset_y = -100 * scale_y  # Ajusta el offset vertical según lo necesites

        # Actualizamos la posición y tamaño de los Entry (se mantienen con escala individual si lo deseas)
        self.entry_2.place(
            x=937.0 * scale_x,
            y=(415.0 * scale_y) ,
            width=155.0 * scale_x,
            height=18.0 * scale_y
        )
        self.entry_1.place(
            x=937.0 * scale_x,
            y=(506.0 * scale_y) ,
            width=155.0 * scale_x,
            height=18.0 * scale_y
        )

        # --- Para el botón "Ingresar" ---
        # Usamos un factor de escala uniforme para el botón
        uniform_scale = min(scale_x, scale_y)
        
        # Colocamos el botón con dimensiones calculadas uniformemente
        self.button_1.place(
            x=918.0 * scale_x,
            y=(565.0 * scale_y),
            width=230.0 * uniform_scale,
            height=40.0 * uniform_scale
        )
        
        # Redimensionar la imagen del botón manteniendo su relación de aspecto original
        orig_button_img = self.original_images['button_1']
        orig_w, orig_h = orig_button_img.size
        new_w = max(1, int(orig_w * uniform_scale))
        new_h = max(1, int(orig_h * uniform_scale))
        new_button_img = ImageTk.PhotoImage(
            orig_button_img.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
        )
        self.button_image = new_button_img
        self.button_1.config(image=self.button_image)

        # Actualizamos la posición del Label de versión (Admin Label)
        self.admin_label.place(
            x=1000.0 * scale_x,
            y=(615.0 * scale_y) 
        )

    def setup_login_interface(self):
        """
        Carga las imágenes (usando PIL) y crea los widgets en sus posiciones “base”.
        Luego se almacenan las coordenadas originales para usarlas en el escalado.
        """
        # --- Fondo principal ---
        self.original_images['bg_main'] = Image.open(self.relative_to_assets("image_3.png"))
        self.images['bg_main'] = ImageTk.PhotoImage(self.original_images['bg_main'])
        item_id = self.canvas.create_image(
            0, 0,
            image=self.images['bg_main'],
            anchor="nw",
            tags="login_group"
        )
        self.canvas_items['bg_main'] = item_id
        self.canvas_item_orig_coords['bg_main'] = (0, 0, "nw")

        # --- Fondo de Entry Contraseña ---
        self.original_images['entry_image_1'] = Image.open(self.relative_to_assets("entry_1.png"))
        self.images['entry_image_1'] = ImageTk.PhotoImage(self.original_images['entry_image_1'])
        item_id = self.canvas.create_image(
            1032.5, 516.0,
            image=self.images['entry_image_1'],
            tags="login_group"
        )
        self.canvas_items['entry_image_1'] = item_id
        self.canvas_item_orig_coords['entry_image_1'] = (1032.5, 516.0, "center")

        self.entry_1 = Entry(
            self.frame,
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0,
            show="*"
        )
        self.entry_1.place(x=954.0, y=506.0, width=157.0, height=18.0)

        # --- Fondo de Entry Usuario ---
        self.original_images['entry_image_2'] = Image.open(self.relative_to_assets("entry_2.png"))
        self.images['entry_image_2'] = ImageTk.PhotoImage(self.original_images['entry_image_2'])
        item_id = self.canvas.create_image(
            1032.5, 425.0,
            image=self.images['entry_image_2'],
            tags="login_group"
        )
        self.canvas_items['entry_image_2'] = item_id
        self.canvas_item_orig_coords['entry_image_2'] = (1032.5, 425.0, "center")

        self.entry_2 = Entry(
            self.frame,
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0
        )
        self.entry_2.place(x=954.0, y=415.0, width=157.0, height=18.0)

        # --- Imágenes decorativas (círculos y otras) ---
        image_positions = {
            4: (150.0, 750.0),
            5: (280.0, 720.0),
            1: (1008.0, 423.0),
            2: (1008.0, 515.0),
            6: (410.0, 192.0),
            7: (410.0, 442.0),
            8: (1006.0, 327.0),
            9: (946.0, 481.0),
            10: (928.0, 515.0),
            11: (940.0, 377.0),
            12: (928.0, 423.0)
        }
        for i, (x, y) in image_positions.items():
            key = f"image_{i}"
            self.original_images[key] = Image.open(self.relative_to_assets(f"image_{i}.png"))
            self.images[key] = ImageTk.PhotoImage(self.original_images[key])
            item_id = self.canvas.create_image(
                x, y,
                image=self.images[key],
                tags="login_group"
            )
            self.canvas_items[key] = item_id
            self.canvas_item_orig_coords[key] = (x, y, "center")

        # --- Botón "Ingresar" ---
        self.original_images['button_1'] = Image.open(self.relative_to_assets("button_1.png"))
        self.button_image = ImageTk.PhotoImage(self.original_images['button_1'])
        self.button_1 = Button(
            self.frame,
            image=self.button_image,
            borderwidth=0,
            highlightthickness=0,
            command=self.handle_login,
            relief="flat",
            cursor="hand2"
        )
        self.button_1.place(
            x=903.0, y=565.0,
            width=230.0, height=40.0
        )

        # --- Admin Label (versión) ---
        self.admin_label = tk.Label(
            self.frame,
            text="v1.0.0",
            font=("Arial", 8),
            fg="#666666",
            bg="#FFFFFF",
            cursor="hand2"
        )
        self.admin_label.bind("<Button-1>", self.show_admin_dialog)
        self.admin_label.place(
            x=1100.0, y=-20
        )

    def handle_login(self):
        """ Se ejecuta al pulsar el botón "Ingresar". """
        username = self.entry_2.get()
        password = self.entry_1.get()
        self.callback(username, password)

    def show_admin_dialog(self, event):
        """ Muestra un diálogo para acceso administrativo """
        dialog = tk.Toplevel(self.parent)
        dialog.title("Verificación")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.iconbitmap(self.relative_to_assets("logo1.ico"))
        
        # Centrar la ventana
        x = (dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (dialog.winfo_screenheight() // 2) - (150 // 2)
        dialog.geometry(f"300x150+{x}+{y}")
        
        frame = tk.Frame(dialog, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Código de administración:").pack()
        code_entry = tk.Entry(frame, show="*")
        code_entry.pack(pady=10)
        
        def verify_code():
            if code_entry.get() == "SPS2024admin":  # Código de admin
                dialog.destroy()
                self.show_user_management()
                
        tk.Button(frame, text="Verificar", command=verify_code).pack()

    def show_user_management(self):
        """ Muestra la ventana de gestión de usuarios """
        management = tk.Toplevel(self.parent)
        management.title("Gestión de Usuarios")
        management.geometry("600x400")
        management.iconbitmap(self.relative_to_assets("logo1.ico"))
        
        # Centrar la ventana
        x = (management.winfo_screenwidth() // 2) - (600 // 2)
        y = (management.winfo_screenheight() // 2) - (400 // 2)
        management.geometry(f"600x400+{x}+{y}")
        
        # Frame principal
        main_frame = ttk.Frame(management, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame para botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Treeview para usuarios
        columns = ("username", "nombre", "rol")
        tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        tree.heading("username", text="Usuario")
        tree.heading("nombre", text="Nombre")
        tree.heading("rol", text="Rol")
        tree.column("username", width=150)
        tree.column("nombre", width=250)
        tree.column("rol", width=100)
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Botones
        ttk.Button(
            button_frame,
            text="Nuevo Usuario",
            style="Action.TButton",
            command=lambda: self.show_user_form(management, tree)
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            button_frame,
            text="Eliminar Usuario",
            style="delete.TButton",
            command=lambda: self.delete_selected_user(tree)
        ).pack(side=tk.LEFT, padx=5)
        
        # Menú contextual
        context_menu = tk.Menu(tree, tearoff=0)
        context_menu.add_command(
            label="Eliminar Usuario", 
            command=lambda: self.delete_selected_user(tree)
        )
        def show_context_menu(event):
            if tree.selection():
                context_menu.tk_popup(event.x_root, event.y_root)
        tree.bind("<Button-3>", show_context_menu)
        
        # Cargar usuarios desde la base de datos
        self.load_users(tree)

    def delete_selected_user(self, tree):
        """ Elimina el usuario seleccionado """
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un usuario para eliminar")
            return
        
        item = tree.item(selection[0])
        username = item['values'][0]
        
        if not self.can_delete_user(username):
            messagebox.showerror("Error", "No se puede eliminar el último usuario administrador")
            return
        
        if not messagebox.askyesno("Confirmar Eliminación",
                                   f"¿Está seguro de eliminar el usuario {username}?"):
            return
            
        if self.delete_user_from_db(username):
            tree.delete(selection[0])
            messagebox.showinfo("Éxito", "Usuario eliminado correctamente")

    def delete_user_from_db(self, username):
        """ Elimina un usuario de la base de datos """
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM usuarios WHERE username = %s",
                (username,)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error eliminando usuario: {e}")
            return False

    def can_delete_user(self, username):
        """ Verifica si se puede eliminar el usuario """
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT rol FROM usuarios WHERE username = %s",
                (username,)
            )
            user_role = cursor.fetchone()[0]
            if user_role != 'admin':
                return True
            cursor.execute(
                "SELECT COUNT(*) FROM usuarios WHERE rol = 'admin'"
            )
            admin_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return admin_count > 1
        except Exception as e:
            messagebox.showerror("Error", f"Error verificando usuario: {e}")
            return False     

    def show_user_form(self, parent, tree):
        """ Muestra formulario para crear/editar usuario """
        dialog = tk.Toplevel(parent)
        dialog.title("Nuevo Usuario")
        dialog.geometry("400x300")
        dialog.grab_set()
        dialog.iconbitmap(self.relative_to_assets("logo1.ico"))

        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"400x300+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Usuario:").pack(anchor=tk.W)
        username_entry = ttk.Entry(frame)
        username_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Contraseña:").pack(anchor=tk.W)
        password_entry = ttk.Entry(frame, show="*")
        password_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Nombre:").pack(anchor=tk.W)
        nombre_entry = ttk.Entry(frame)
        nombre_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Rol:").pack(anchor=tk.W)
        rol_combo = ttk.Combobox(frame, values=["admin", "usuario"], state="readonly")
        rol_combo.pack(fill=tk.X, pady=(0, 10))
        rol_combo.set("usuario")
        
        def save_user():
            if self.save_user_to_db(
                username_entry.get(),
                password_entry.get(),
                nombre_entry.get(),
                rol_combo.get()
            ):
                dialog.destroy()
                self.load_users(tree)
        
        ttk.Button(frame, text="Guardar", command=save_user).pack(pady=10)

    def load_users(self, tree):
        """ Carga usuarios desde la base de datos """
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT username, nombre, rol FROM usuarios")
            for item in tree.get_children():
                tree.delete(item)
            for user in cursor.fetchall():
                tree.insert("", "end", values=user)
            cursor.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando usuarios: {e}")

    def save_user_to_db(self, username, password, nombre, rol):
        """ Guarda un nuevo usuario en la base de datos """
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO usuarios (username, password, nombre, rol)
                VALUES (%s, %s, %s, %s)
                """, (username, password, nombre, rol)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando usuario: {e}")
            return False

    def show(self):
        """ Muestra el frame y maximiza la ventana. """
        self.parent.state('zoomed')
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """ Oculta este frame. """
        self.frame.pack_forget()

# Si deseas probar el LoginFrame de forma independiente, podrías incluir lo siguiente:
if __name__ == "__main__":
    def dummy_login(user, pwd):
        print(f"Login con usuario: {user} y contraseña: {pwd}")
    root = tk.Tk()
    app = LoginFrame(root, dummy_login)
    root.mainloop()
