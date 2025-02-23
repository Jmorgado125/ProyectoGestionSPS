import mysql.connector
from mysql.connector import Error

def connect_db():
    """Establece una conexión con la base de datos."""
    try:
        conn = mysql.connector.connect(
            #host="localhost",       # Cambia si el servidor está en otra máquina
            #user="root",            # Usuario de MySQL
            host="192.168.1.57",       # Cambia si el servidor está en otra máquina
            user="gestor",            # Usuario de MySQL
            password="@Rip.nicok2003",  # Contraseña configurada
            database="cursosmarina"  # Nombre de la base de datos
        )
        
        return conn
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None
