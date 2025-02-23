# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_all
import tkinterdnd2

# Directorio actual y ruta al módulo tkdnd
current_dir = os.getcwd()
tkdnd_dir = os.path.join(os.path.dirname(tkinterdnd2.__file__), 'tkdnd')

# Datos a incluir (carpetas y archivos necesarios)
datas = [
    ('assets', 'assets'),
    ('formatos', 'formatos'),
    ('database', 'database'),
    ('gui', 'gui'),
    ('helpers', 'helpers'),
    (tkdnd_dir, 'tkinterdnd2/tkdnd'),
]

binaries = []
hiddenimports = [
    'PIL._tkinter_finder',
    'PIL.Image',
    'PIL.ImageTk',
    'mysql.connector',  # Asegúrate de tener instalado mysql-connector-python
    'docxtpl',
    'tkcalendar',
    'pandas',
    'openpyxl',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'babel.numbers',
    'mysql.connector.plugins',
    'mysql.connector.plugins.caching_sha2_password',
    'tkinterdnd2'
]

# Recolectar recursos de PIL
PIL_datas, PIL_binaries, PIL_hiddenimports = collect_all('PIL')
datas.extend(PIL_datas)
binaries.extend(PIL_binaries)
hiddenimports.extend(PIL_hiddenimports)

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Se genera el ejecutable sin incluir los binarios (más adelante se agregan con COLLECT)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GestionCursos',
    debug=False,                 # Debug desactivado para producción
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,               # Oculta la consola
    icon=os.path.join(current_dir, 'assets', 'logo.ico')
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GestionCursos'
)
