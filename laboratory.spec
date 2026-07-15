# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Laboratory Management System
Builds the application into a single .exe file for Windows
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include the logo image
        ('img/logo.png', 'img'),
        ('img/logo.ico', 'img'),
        ('img/logo.svg', 'img'),
        ('img/logo.gif', 'img'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'pandas',
        'openpyxl',
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.lib',
        'reportlab.platypus',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'bcrypt',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib.tests',
        'pandas.tests',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LaboratoryManagement',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='img/logo.ico',  # Application icon
)
