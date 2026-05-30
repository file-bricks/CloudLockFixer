# -*- coding: utf-8 -*-
"""Baut CloudLockFixer.exe via PyInstaller in einem lokalen Mirror
(C:\\_Local_DEV\\clf_build) -- vermeidet OneDrive-Sync-Last bei build/dist --
und legt die fertige App nach C:\\_Local_DEV\\CloudLockFixer.

Aufruf:  python build_exe.py
Voraussetzung: pip install pyinstaller pillow pyside6
Icon neu erzeugen: siehe resources/ (icon.ico). Danach Desktop-Verknuepfung
zeigt automatisch aufs neue Bundle.
"""
import os
import shutil

import PyInstaller.__main__

HERE = os.path.dirname(os.path.abspath(__file__))
B = r"C:\_Local_DEV\clf_build"
APP = r"C:\_Local_DEV\CloudLockFixer"

# Mirror frisch aufsetzen (Quelle bleibt im Projekt)
shutil.rmtree(B, ignore_errors=True)
os.makedirs(B, exist_ok=True)
shutil.copytree(os.path.join(HERE, "src"), os.path.join(B, "src"),
                ignore=shutil.ignore_patterns("__pycache__"))
shutil.copy(os.path.join(HERE, "resources", "icon.ico"), os.path.join(B, "icon.ico"))
shutil.copy(os.path.join(HERE, "clf_app.py"), os.path.join(B, "clf_app.py"))

PyInstaller.__main__.run([
    os.path.join(B, "clf_app.py"),
    "--name", "CloudLockFixer",
    "--noconsole", "--onedir", "--noconfirm", "--clean",
    "--icon", os.path.join(B, "icon.ico"),
    "--paths", os.path.join(B, "src"),
    "--add-data", os.path.join(B, "icon.ico") + os.pathsep + ".",
    "--distpath", os.path.join(B, "dist"),
    "--workpath", os.path.join(B, "work"),
    "--specpath", B,
])

# fertige App an stabilen, OneDrive-freien Ort
shutil.rmtree(APP, ignore_errors=True)
shutil.copytree(os.path.join(B, "dist", "CloudLockFixer"), APP)
print("Fertig:", os.path.join(APP, "CloudLockFixer.exe"))
