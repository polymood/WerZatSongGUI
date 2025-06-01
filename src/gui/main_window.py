from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QTabBar,
    QMenuBar,
    QMenu,
)

from PyQt6.QtGui import QAction

from .widgets.welcome import WelcomePage
from .dialogs.youtube_jobs import YouTubeJobsWidget
from .dialogs.fingerprint_jobs import FingerprintJobsWidget
from .dialogs.scan_jobs import ScanJobsWidget


class MainWindow(QMainWindow):
    """Main window with Home plus three job tabs (loaded from dialogs/*)."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WerZatSong GUI")
        self.resize(1200, 800)

        # ------------------------------------------------- central QTabWidget
        self.tabs = QTabWidget(movable=True, tabsClosable=False)
        self.setCentralWidget(self.tabs)

        # ----- Home ---------------------------------------------------------
        self.home = WelcomePage()
        self.home_index = self.tabs.addTab(self.home, "Home")
        self.tabs.tabBar().setTabButton(
            self.home_index, QTabBar.ButtonPosition.RightSide, None
        )

        # ----- Job tabs -----------------------------------------------------
        self.youtube_page = YouTubeJobsWidget()
        self.fprint_page = FingerprintJobsWidget()
        self.scan_page = ScanJobsWidget()

        self.youtube_index = self.tabs.addTab(self.youtube_page, "YouTube Jobs")
        self.fprint_index = self.tabs.addTab(self.fprint_page, "Fingerprint Jobs")
        self.scan_index = self.tabs.addTab(self.scan_page, "Scan Jobs")

        # Home buttons just jump to the appropriate tab
        self.home.yt_clicked.connect(lambda: self.tabs.setCurrentIndex(self.youtube_index))
        self.home.fprint_clicked.connect(lambda: self.tabs.setCurrentIndex(self.fprint_index))
        self.home.scan_clicked.connect(lambda: self.tabs.setCurrentIndex(self.scan_index))

        self.tabs.setCurrentIndex(self.home_index)   # land on Home

        # ------------------------------------------------------------- menu
        self._build_menubar()

    # ----------------------------------------------------------------------
    def _build_menubar(self) -> None:
        bar = QMenuBar(self)
        self.setMenuBar(bar)

        file_menu = QMenu("&File", self)
        file_menu.addAction(QAction("E&xit", self, triggered=self.close))
        bar.addMenu(file_menu)
