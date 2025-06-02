from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtGui import QPixmap

class WelcomePage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Logo at the top ---
        logo_path = "assets\splash.png"  # <-- Put your logo path here!
        logo = QLabel()
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaledToWidth(180, Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pixmap)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo.setStyleSheet("margin-bottom: 24px;")
            outer.addWidget(logo)
        else:
            # fallback if image not found
            logo.setText("Lostwave Community")
            logo.setStyleSheet("font-size: 26px; font-weight: bold; margin-bottom: 18px; color: #67d;")
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            outer.addWidget(logo)

        # --- App Title ---
        title = QLabel("Welcome to the Lostwave Music Toolkit")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 16px; color: #fff;")
        outer.addWidget(title)

        # --- App Description / Tabs ---
        desc = QLabel(
            "<b>Download from YouTube</b> — "
            "Fetch and save music from YouTube with just a link.<br><br>"
            "<b>Create Fingerprint DB</b> — "
            "Analyze your music collection and generate a fingerprint database for fast song identification.<br><br>"
            "<b>Identify Unknown Songs</b> — "
            "Drag in an audio sample and instantly search your database for possible matches."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 15px; color: #ccc; margin-bottom: 28px;")
        outer.addWidget(desc)

        # Spacer for visual breathing room
        outer.addSpacerItem(QSpacerItem(0, 0, vPolicy=QSizePolicy.Policy.Expanding))

        # --- Special Thanks at the bottom ---
        thanks = QLabel(
            "<b>Special thanks to:</b><br>"
            "• <a href='https://github.com/dpwe/audfprint'>audfprint</a> devs<br>"
            "• <a href='https://ffmpeg.org/'>FFmpeg</a> team<br>"
            "• <a href='https://github.com/yt-dlp/yt-dlp'>yt-dlp</a><br>"
            "• <a href='https://www.python.org/'>Python</a>, <a href='https://www.qt.io/'>Qt</a>, and the open source community"
        )
        thanks.setOpenExternalLinks(True)
        thanks.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thanks.setStyleSheet("font-size: 13px; color: #aaa; margin-top: 16px; margin-bottom: 6px;")
        outer.addWidget(thanks)

        # push everything to centre vertically
        outer.insertSpacerItem(0, QSpacerItem(0, 0, vPolicy=QSizePolicy.Policy.Expanding))
        outer.addSpacerItem(QSpacerItem(0, 0, vPolicy=QSizePolicy.Policy.Expanding))
