# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for FileX — Universal File Converter.
Builds standalone Windows application in --onedir mode without console window.
"""

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
project_root = os.path.abspath(SPECPATH)

# Assets and resources
datas = [
    (os.path.join(project_root, 'assets'), 'assets'),
]

# Include bin directory (FFmpeg / FFprobe) if present
bin_dir = os.path.join(project_root, 'bin')
if os.path.exists(bin_dir) and any(f.endswith('.exe') for f in os.listdir(bin_dir)):
    datas.append((bin_dir, 'bin'))

# Hidden imports to ensure dynamic modules are packaged
hiddenimports = [
    'PySide6.QtPdf',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'pypdf',
    'docx',
    'pptx',
    'openpyxl',
    'pandas',
    'PIL',
    'PIL.Image',
    'pydub',
    'ffmpeg',
    'reportlab',
    'reportlab.platypus',
    'reportlab.lib.pagesizes',
    'reportlab.lib.styles',
    'sqlite3',
    'winreg',
    'ctypes',
    'platformdirs',
    'psutil',
    'markdown',
    'odf',
    'bs4',
    'html2text',
]

# Collect submodules
hiddenimports += collect_submodules('core')
hiddenimports += collect_submodules('converters')
hiddenimports += collect_submodules('ui')
hiddenimports += collect_submodules('utils')
hiddenimports += collect_submodules('reportlab')

icon_path = os.path.join(project_root, 'assets', 'images', 'logo.ico')
if not os.path.exists(icon_path):
    icon_path = None

a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'IPython', 'notebook', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FileX',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='FileX',
)
