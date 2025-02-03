# 📊 Proyecto de Gestión de Cursos

Sistema de escritorio para la gestión de cursos, inscripciones, tramitaciones y documentación, desarrollado en **Python** con interfaz gráfica en **Tkinter** y base de datos **MySQL**.

## 🚀 Características Principales

- Gestión de alumnos y cursos.
- Control de inscripciones y pagos.
- Generación automática de documentos (Word, Excel).
- Interfaz intuitiva basada en Tkinter.
- Exportación de informes.

## 🌟 Tecnologías Utilizadas

- **Python 3.8+**
- **Tkinter** (Interfaz Gráfica)
- **MySQL** (Base de Datos)
- **DocxTemplate** (Generación de Documentos)
- **OpenPyXL** (Manipulación de Excel)
- **PyInstaller** (Compilación a Ejecutable)

---

## 📂 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tuusuario/proyecto-gestion-cursos.git
cd proyecto-gestion-cursos
```

### 2. Configurar la Base de Datos

1. Instalar MySQL Server.
2. Crear la base de datos:

```bash
mysql -u root -p < esquema.sql
```

3. Configurar `database/db_config.py` con tus credenciales de MySQL.

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

Si no hay un `requirements.txt`, instala manualmente:

```bash
pip install mysql-connector-python tk docxtpl openpyxl pillow
```

### 4. Ejecutar la Aplicación

```bash
python main.py
```

---

## 📦 Compilación del Ejecutable

1. Instalar PyInstaller:

```bash
pip install pyinstaller
```

2. Compilar:

```bash
pyinstaller --noconfirm --onefile --windowed --add-data "formatos;formatos" --add-data "assets;assets" main.py
```

El ejecutable estará en la carpeta `dist/`.

---

## 🌐 Despliegue en Otros Equipos

1. Copiar el ejecutable de `dist/`.
2. Asegurar que el equipo tenga:
   - MySQL Client instalado (si usa base de datos remota).
   - Visual C++ Redistributable (si es necesario).

---

## 🚜 Contribuciones

1. Haz un fork.
2. Crea una rama (`git checkout -b feature-nueva`).
3. Realiza tus cambios.
4. Haz un pull request.

---

## 💚 Licencia

Este proyecto está bajo la [MIT License](LICENSE).

---

## 🚀 Contacto

- **Autor:** Jorge Morgado
- **GitHub:** [@Jmorgado125](https://github.com/Jmorgado125)

---

✨ *Desarrollado con pasión y Python* 🚀

