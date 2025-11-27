import sys
import os
import shutil

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow
from .constants import MINECRAFT_DIR, IMAGES_DIR, MODS_DIR, ICON_CACHE_DIR

try:
    from rich.traceback import install

    install(show_locals=True)
except Exception:
    pass # aww the user doesnt have vim


def check_dirs() -> None:
    if not os.path.exists(MINECRAFT_DIR):
        os.makedirs(MINECRAFT_DIR)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(MODS_DIR, exist_ok=True)
    os.makedirs(ICON_CACHE_DIR, exist_ok=True)


def main():
    check_dirs()
    app = QApplication(sys.argv)

    font = QFont("Segoe UI")
    if font.family() != "Segoe UI":
        font = QFont("Inter") # try inter next
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
