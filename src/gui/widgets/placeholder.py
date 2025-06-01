# src/gui/widgets/placeholder.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class Placeholder(QWidget):
    """Simple 'coming-soon' centre label."""

    def __init__(self, text: str = "Placeholder") -> None:
        super().__init__()
        vbox = QVBoxLayout(self)
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #888;")
        vbox.addWidget(label)
