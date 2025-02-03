from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Entry, Button, PhotoImage, ttk, messagebox
import os
from database.db_config import connect_db

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

        # Canvas con fondo
        self.canvas = Canvas(
            self.frame,
            bg="#FFFFFF",
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

    def setup_styles(self):
        style = ttk.Style()
        style.configure('Action.TButton',
                font=('Helvetica', 10, 'bold'),
                padding=(10, 5),
                background='#00239c',
                foreground='white',
                relief='raised',  # Cambiado a raised para dar el efecto 3D
                borderwidth=1)    # Añadido borde

        style.map('Action.TButton',
                    background=[('active', '#001970'),
                            ('pressed', '#00239c')],
                    foreground=[('active', 'white'),
                            ('pressed', 'white')],
                    relief=[('pressed', 'sunken')])  # Efecto presionado

        style.configure('delete.TButton',
                        font=('Helvetica', 10, 'bold'),
                        padding=(10, 5),
                        background='#b50707',
                        foreground='white',
                        relief='raised',  # Cambiado a raised para dar el efecto 3D
                        borderwidth=1)    # Añadido borde

        style.map('delete.TButton',
                    background=[('active', '#990606'),
                            ('pressed', '#b50707')],
                    foreground=[('active', 'white'),
                            ('pressed', 'white')],
                    relief=[('pressed', 'sunken')])  # Efecto presionado

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
        """ Recalcula posiciones para Entry y Botón. """
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
            y=565.0  * scale_y,
            width=230.0 * scale_x,
            height=40.0 * scale_y
        )

        # Admin Label (nuevo)
        self.admin_label.place(
            x=1000.0 * scale_x,
            y=615.0 * scale_y
        )

    def setup_login_interface(self):
        """ Carga imágenes y crea los widgets en posiciones fijas de diseño. """
        # Imagen de fondo principal
        self.images['bg_main'] = PhotoImage(file=self.relative_to_assets("image_3.png"))
        self.canvas.create_image(
            0, 0,
            image=self.images['bg_main'],
            anchor="nw",
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
        image_positions = {
            4: (150.0, 750.0),
            5: (280.0, 720.0),
            1: (1018.0, 423.0),
            2: (1018.0, 515.0),
            6: (417.0, 192.0),
            7: (417.0, 442.0),
            8: (1016.0, 327.0),
            9: (947.0, 481.0),
            10: (923.0, 515.0),
            11: (932.0, 377.0),
            12: (922.0, 423.0)
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
        self.button_1.place(
            x=903.0, y=565.0,
            width=230.0, height=40.0
        )

        # Nuevo: Admin Label
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
            x=1000.0, y=0
        )

    def handle_login(self):
        """ Cuando se hace clic en el botón "Ingresar". """
        username = self.entry_2.get()
        password = self.entry_1.get()
        self.callback(username, password)

    def show_admin_dialog(self, event):
        """Muestra diálogo para acceso administrativo"""
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
            """Muestra la ventana de gestión de usuarios"""
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
                if tree.selection():  # Solo mostrar si hay selección
                    context_menu.tk_popup(event.x_root, event.y_root)
            
            tree.bind("<Button-3>", show_context_menu)  # Click derecho
            
            # Cargar usuarios
            self.load_users(tree)

    def delete_selected_user(self, tree):
        """Elimina el usuario seleccionado"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un usuario para eliminar")
            return
        
        # Obtener el usuario seleccionado
        item = tree.item(selection[0])
        username = item['values'][0]
        
        # No permitir eliminar al último administrador
        if not self.can_delete_user(username):
            messagebox.showerror(
                "Error", 
                "No se puede eliminar el último usuario administrador"
            )
            return
        
        # Confirmar eliminación
        if not messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar el usuario {username}?"
        ):
            return
            
        # Intentar eliminar
        if self.delete_user_from_db(username):
            tree.delete(selection[0])
            messagebox.showinfo("Éxito", "Usuario eliminado correctamente")

    def delete_user_from_db(self, username):
        """Elimina un usuario de la base de datos"""
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
        """Verifica si se puede eliminar el usuario"""
        try:
            conn = connect_db()
            cursor = conn.cursor()
            
            # Obtener el rol del usuario a eliminar
            cursor.execute(
                "SELECT rol FROM usuarios WHERE username = %s",
                (username,)
            )
            user_role = cursor.fetchone()[0]
            
            # Si no es admin, se puede eliminar
            if user_role != 'admin':
                return True
                
            # Contar cuántos administradores hay
            cursor.execute(
                "SELECT COUNT(*) FROM usuarios WHERE rol = 'admin'"
            )
            admin_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            # Solo permitir eliminar si hay más de un admin
            return admin_count > 1
        except Exception as e:
            messagebox.showerror("Error", f"Error verificando usuario: {e}")
            return False     
    

    def show_user_form(self, parent, tree):
        """Muestra formulario para crear/editar usuario"""
        dialog = tk.Toplevel(parent)
        dialog.title("Nuevo Usuario")
        dialog.geometry("400x300")
        dialog.grab_set()
        dialog.iconbitmap(self.relative_to_assets("logo1.ico"))

        # Centrar la ventana
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
                self.load_users(tree)  # Ahora tree está disponible aquí
        
        ttk.Button(frame, text="Guardar", command=save_user).pack(pady=10)

    def load_users(self, tree):
        """Carga usuarios desde la base de datos"""
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
        """Guarda un nuevo usuario en la base de datos"""
        try:
            conn = connect_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO usuarios (username, password, nombre, rol)
                VALUES (%s, %s, %s, %s)
            """, (username, password, nombre, rol))
            
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
        self.last_width = self.original_width
        self.last_height = self.original_height
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """ Oculta este frame. """
        self.frame.pack_forget()