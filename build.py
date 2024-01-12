from cx_Freeze import setup, Executable
import os
import sys
import serial
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

build_exe_options = {
    "packages": ["sqlite3"],
}

includes = ["time", "cv2", "pyzbar", "serial", "os"]

build_exe_options = {
    "includes": includes,
    "excludes": [],
    "packages": [],
    "include_files": [],
}

base = None

executables = [Executable("CAM.py", base=base)]

setup(
    name="Test_camera",
    options={"build_exe": build_exe_options},
    version="1.0",
    description="description",
    executables=executables
)