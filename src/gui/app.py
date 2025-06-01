# src/gui/app.py
import sys
from PyQt6.QtWidgets import QApplication
from .main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.showMaximized()             # always start maximised
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
