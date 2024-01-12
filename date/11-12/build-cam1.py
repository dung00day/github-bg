from cx_Freeze import setup, Executable
import os
import sys
import serial
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore
from datetime import datetime


build_exe_options = {
    "packages": ["sqlite3"],
}

base = None

executables = [Executable("CAM-01.py", base=base)]

setup(
    name="S4-200_1",
    options={"build_exe": build_exe_options},
    version="1.0",
    description="description",
    executables=executables
)