from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSizePolicy,
    QSpacerItem,
)


class _Tile(QPushButton):
    """Compact tile that grows but never huge."""

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setMinimumSize(120, 80)
        self.setMaximumSize(300, 200)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.setStyleSheet(
            """
            QPushButton {
                border: 1px solid #555;
                border-radius: 6px;
                background: #3a3a3a;
                color: #ddd;
                font-size: 13px;
            }
            QPushButton:hover { background: #505050; }
            QPushButton:pressed { background: #2c2c2c; }
            """
        )


class WelcomePage(QWidget):
    yt_clicked = pyqtSignal()
    fprint_clicked = pyqtSignal()
    scan_clicked = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- first row (two tiles) ---
        row1 = QHBoxLayout()
        row1.setSpacing(24)
        row1.addWidget(self._make_tile("📺  Download from YouTube", self.yt_clicked))
        row1.addWidget(self._make_tile("🎛  Create Fingerprint DB", self.fprint_clicked))
        outer.addLayout(row1)

        # --- second row (one wide tile) ---
        row2 = QHBoxLayout()
        row2.addStretch(1)
        row2.addWidget(self._make_tile("🔍  Identify Unknown Songs", self.scan_clicked))
        row2.addStretch(1)
        outer.addSpacing(20)
        outer.addLayout(row2)

        # caption
        caption = QLabel("Welcome — choose an action to begin.")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caption.setStyleSheet("color:#aaa; font-size:14px; margin-top:25px;")
        outer.addWidget(caption)

        # push everything to centre vertically
        outer.insertSpacerItem(0, QSpacerItem(0, 0, vPolicy=QSizePolicy.Policy.Expanding))
        outer.addSpacerItem(QSpacerItem(0, 0, vPolicy=QSizePolicy.Policy.Expanding))

    # helper
    def _make_tile(self, text: str, sig):
        btn = _Tile(text)
        btn.clicked.connect(sig.emit)
        return btn
