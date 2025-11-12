import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow

try:
    from rich.traceback import install

    install(show_locals=True)
except Exception:
    pass # aww the user doesnt have vim


def main():
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
