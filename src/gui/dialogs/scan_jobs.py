from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class ScanJobsWidget(QWidget):
    """Placeholder pane for ‘identify unknown songs’ jobs."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        vbox = QVBoxLayout(self)
        label = QLabel("Scan jobs queue -- UI coming soon …", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #888;")
        vbox.addWidget(label)
