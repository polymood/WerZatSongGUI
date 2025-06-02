from PyQt6.QtCore import (
    QUrl,
    QSettings,
    QTranslator,
    QLocale,
    QLibraryInfo,
    Qt
)
from PyQt6.QtGui import QDesktopServices, QAction, QIcon
from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QTabBar,
    QMessageBox,
    QApplication
)

from .dialogs.ffmpeg_jobs import FfmpegJobsWidget
from .dialogs.fingerprint_jobs import FingerprintJobsWidget
from .dialogs.scan_jobs import ScanJobsWidget
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.youtube_jobs import YouTubeJobsWidget
from .widgets.welcome import WelcomePage

import multiprocessing
import platform
import os
import subprocess
import sys


class MainWindow(QMainWindow):
    """Main window with Home plus job tabs and live QSettings + translation support."""

    def __init__(self) -> None:
        super().__init__()

        # 1) QSettings must be created after QApplication.setOrganizationName/appName
        self.settings = QSettings()

        # 2) Keep references to translators to remove later
        self.app_translator = None
        self.qt_translator = None

        # 3) Load saved language before building UI
        saved_lang = self.settings.value(
            "general/language", type=str, defaultValue="English"
        )
        self._load_language(saved_lang)

        # 4) Build menus + main window properties
        self._create_menu_bar()
        self.setWindowTitle(self.tr("WerZatSong GUI"))
        self.setWindowIcon(QIcon("assets/favicon.ico"))
        self.resize(1200, 800)

        # 5) Central QTabWidget
        self.tabs = QTabWidget(movable=True, tabsClosable=False)
        self.setCentralWidget(self.tabs)

        # ----- Home ---------------------------------------------------------
        self.home = WelcomePage()
        self.home_index = self.tabs.addTab(self.home, self.tr("Home"))
        # Remove close button for home tab
        self.tabs.tabBar().setTabButton(
            self.home_index, QTabBar.ButtonPosition.RightSide, None
        )

        # ----- Job tabs -----------------------------------------------------
        self.youtube_page = YouTubeJobsWidget()
        self.fprint_page = FingerprintJobsWidget()
        self.scan_page = ScanJobsWidget()
        self.ffmpeg_page = FfmpegJobsWidget()

        self.youtube_index = self.tabs.addTab(
            self.youtube_page, self.tr("YouTube Jobs (yt-dlp)")
        )
        self.fprint_index = self.tabs.addTab(
            self.fprint_page, self.tr("Fingerprint Jobs (audfprint)")
        )
        self.scan_index = self.tabs.addTab(
            self.scan_page, self.tr("Scan Jobs")
        )
        self.ffmpeg_index = self.tabs.addTab(
            self.ffmpeg_page, self.tr("FFmpeg Jobs")
        )

        self.tabs.setCurrentIndex(self.home_index)

        # 6) Prepare SettingsDialog and connect its language_changed signal
        self.settings_dlg = SettingsDialog(self)
        self.settings_dlg.language_changed.connect(self._on_language_changed)

    # ----------------------------------------------------------------------
    def _create_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu(self.tr("File"))
        act_exit = QAction(self.tr("Exit"), self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # Tools menu
        tools_menu = menubar.addMenu(self.tr("Tools"))
        act_rescan = QAction(self.tr("Rescan System Info"), self)
        act_rescan.triggered.connect(self._rescan_system_info)
        tools_menu.addAction(act_rescan)

        # Settings menu
        settings_menu = menubar.addMenu(self.tr("Settings"))
        act_settings = QAction(self.tr("App Settings"), self)
        act_settings.triggered.connect(self._open_settings)
        act_edit_config = QAction(self.tr("Open settings storage"), self)
        act_edit_config.triggered.connect(self._open_settings_storage)
        settings_menu.addAction(act_settings)
        settings_menu.addAction(act_edit_config)

        # Help menu
        help_menu = menubar.addMenu(self.tr("Help"))
        act_about = QAction(self.tr("About"), self)
        act_about.triggered.connect(self._show_about)
        act_docs = QAction(self.tr("Documentation"), self)
        act_docs.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://yourdocsurl.com"))
        )
        act_feedback = QAction(self.tr("Report a Bug / Feedback"), self)
        act_feedback.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl("mailto:your@email.com"))
        )
        help_menu.addAction(act_about)
        help_menu.addAction(act_docs)
        help_menu.addAction(act_feedback)

    def _show_about(self):
        """
        Display an About dialog. Reads version and platform from QSettings,
        with defaults if not set, and wraps text in tr().
        """
        app_version = self.settings.value("app/version", type=str, defaultValue="?")
        plt = self.settings.value("app/platform", type=str, defaultValue="?")
        QMessageBox.about(
            self,
            self.tr("About WerZatSong"),
            (
                f"<b>{self.tr('WerZatSong')}</b><br>"
                f"{self.tr('Version')}: {app_version}<br>"
                f"{self.tr('Platform')}: {plt}<br>"
                "&copy; Lostwave Community<br><br>"
                f"{self.tr('Powered by audfprint, ffmpeg, yt-dlp, PyQt, and open source contributors.')}<br>"
            )
        )

    def _open_settings(self):
        """
        Open the SettingsDialog. Any changes are saved immediately into QSettings.
        """
        self.settings_dlg.exec()

    def _open_settings_storage(self):
        """
        Attempt to open the underlying settings file (INI/PLIST) or do nothing if registry.
        """
        fmt = self.settings.format()
        if fmt == QSettings.Format.NativeFormat:
            return  # Registry on Windows has no single file
        path = self.settings.fileName()
        if path:
            if sys.platform.startswith(("linux", "darwin")):
                opener = "xdg-open" if sys.platform.startswith("linux") else "open"
                subprocess.Popen([opener, path])
            else:
                try:
                    os.startfile(path)
                except OSError:
                    pass

    def _rescan_system_info(self):
        """
        Re‐compute system info (CPU count, platform) and save to QSettings.
        """
        cpu_count = multiprocessing.cpu_count()
        self.settings.setValue("audio/max_cores", cpu_count)
        self.settings.setValue("audio/cpu_count", cpu_count)

        plat_str = platform.system() + " " + platform.release()
        self.settings.setValue("app/platform", plat_str)

        QMessageBox.information(
            self,
            self.tr("Scan complete"),
            self.tr("System info has been rescanned and saved to settings.")
        )

    # ----------------------------------------------------------------------
    def _on_language_changed(self, new_lang: str):
        """
        Slot called whenever SettingsDialog emits language_changed.
        Reload translators and retranslate UI.
        """
        self._load_language(new_lang)
        self._retranslate_all()

    def _load_language(self, lang: str):
        """
        Remove old translators, load the new .qm for app strings and Qt base, and install them.
        """
        if self.app_translator:
            QApplication.instance().removeTranslator(self.app_translator)
            self.app_translator = None
        if self.qt_translator:
            QApplication.instance().removeTranslator(self.qt_translator)
            self.qt_translator = None

        code = "fr" if lang == "French" else "en"
        self.app_translator = QTranslator()
        qm_path = f"gui/translations/werzatsong_{code}.qm"
        if self.app_translator.load(qm_path):
            QApplication.instance().installTranslator(self.app_translator)

        self.qt_translator = QTranslator()
        locale_name = QLocale(code).name()  # e.g. "fr_FR" or "en_US"
        qt_ts_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        if self.qt_translator.load(f"qtbase_{locale_name}", qt_ts_path):
            QApplication.instance().installTranslator(self.qt_translator)

    def _retranslate_all(self):
        """
        Re‐apply tr() to all visible UI elements: window title, menus, tabs, pages.
        """
        self.setWindowTitle(self.tr("WerZatSong GUI"))

        self.menuBar().clear()
        self._create_menu_bar()

        self.tabs.setTabText(self.home_index, self.tr("Home"))
        self.tabs.setTabText(self.youtube_index, self.tr("YouTube Jobs (yt-dlp)"))
        self.tabs.setTabText(self.fprint_index, self.tr("Fingerprint Jobs (audfprint)"))
        self.tabs.setTabText(self.scan_index, self.tr("Scan Jobs"))
        self.tabs.setTabText(self.ffmpeg_index, self.tr("FFmpeg Jobs"))

        for page in (
            self.home,
            self.youtube_page,
            self.fprint_page,
            self.scan_page,
            self.ffmpeg_page
        ):
            if hasattr(page, "retranslateUi"):
                page.retranslateUi()
