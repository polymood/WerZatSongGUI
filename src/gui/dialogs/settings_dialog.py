from PyQt6.QtCore import QSettings, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QStackedWidget,
    QWidget, QPushButton, QLineEdit, QFileDialog, QSpinBox, QCheckBox,
    QComboBox, QFormLayout
)


class SettingsDialog(QDialog):
    # Emitted whenever the language combo changes
    language_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Settings"))
        self.resize(720, 400)

        # QSettings uses application/organization names (set up in main.py)
        self.settings = QSettings()

        layout = QHBoxLayout(self)

        # --- Sidebar (categories) ---
        self.sidebar = QTreeWidget()
        self.sidebar.setHeaderHidden(True)

        cats = [
            (self.tr("General"),  self._panel_general()),
            (self.tr("Paths"),    self._panel_paths()),
            (self.tr("Audio"),    self._panel_audio()),
            (self.tr("Advanced"), self._panel_advanced()),
        ]

        self.panels = QStackedWidget()
        for name, panel in cats:
            QTreeWidgetItem(self.sidebar, [name])
            self.panels.addWidget(panel)

        self.sidebar.currentItemChanged.connect(
            lambda curr, _: self.panels.setCurrentIndex(
                self.sidebar.indexOfTopLevelItem(curr)
            )
        )
        self.sidebar.setCurrentItem(self.sidebar.topLevelItem(0))

        layout.addWidget(self.sidebar, 1)
        layout.addWidget(self.panels, 4)

        # --- Bottom row (buttons) --- (optional; can be removed if you want)
        btn_row   = QHBoxLayout()
        btn_close = QPushButton(self.tr("Close"))
        btn_close.clicked.connect(self.accept)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_close)

        layout2 = QVBoxLayout()
        layout2.addLayout(layout)
        layout2.addLayout(btn_row)
        self.setLayout(layout2)

    # === Panels ===
    def _panel_general(self):
        panel = QWidget()
        form = QFormLayout(panel)

        # 1) Language combo
        self.combo_lang = QComboBox()
        self.combo_lang.addItems([self.tr("English"), self.tr("French")])
        # Load last‐saved value (default = "English")
        lang = self.settings.value("general/language", type=str, defaultValue="English")
        self.combo_lang.setCurrentText(lang)
        # Save on change, and emit signal
        self.combo_lang.currentTextChanged.connect(self._save_language)

        # 2) Start maximized checkbox
        self.chk_startup = QCheckBox(self.tr("Start app maximized"))
        start_max = self.settings.value("general/start_maximized", type=bool, defaultValue=True)
        self.chk_startup.setChecked(start_max)
        self.chk_startup.stateChanged.connect(self._save_start_maximized)

        form.addRow(self.tr("Language:"), self.combo_lang)
        form.addRow(self.chk_startup)
        return panel

    def _panel_paths(self):
        panel = QWidget()
        form = QFormLayout(panel)

        # 1) ffmpeg path
        self.edit_ffmpeg = QLineEdit()
        ffmpeg_path = self.settings.value("paths/ffmpeg_path", type=str, defaultValue="")
        self.edit_ffmpeg.setText(ffmpeg_path)
        # If user types manually, save immediately:
        self.edit_ffmpeg.textChanged.connect(
            lambda text: self.settings.setValue("paths/ffmpeg_path", text)
        )
        btn_ffmpeg = QPushButton(self.tr("Browse…"))
        btn_ffmpeg.clicked.connect(lambda: self._browse_path(self.edit_ffmpeg, "ffmpeg", "paths/ffmpeg_path"))

        # 2) yt-dlp path
        self.edit_ytdlp = QLineEdit()
        ytdlp_path = self.settings.value("paths/yt_dlp_path", type=str, defaultValue="")
        self.edit_ytdlp.setText(ytdlp_path)
        self.edit_ytdlp.textChanged.connect(
            lambda text: self.settings.setValue("paths/yt_dlp_path", text)
        )
        btn_ytdlp = QPushButton(self.tr("Browse…"))
        btn_ytdlp.clicked.connect(lambda: self._browse_path(self.edit_ytdlp, "yt-dlp", "paths/yt_dlp_path"))

        # 3) Default database folder
        self.edit_dbdir = QLineEdit()
        dbdir = self.settings.value("paths/default_data_dir", type=str, defaultValue="")
        self.edit_dbdir.setText(dbdir)
        self.edit_dbdir.textChanged.connect(
            lambda text: self.settings.setValue("paths/default_data_dir", text)
        )
        btn_dbdir = QPushButton(self.tr("Browse…"))
        btn_dbdir.clicked.connect(lambda: self._browse_dir(self.edit_dbdir, "paths/default_data_dir"))

        form.addRow(self.tr("ffmpeg path:"), self._row(self.edit_ffmpeg, btn_ffmpeg))
        form.addRow(self.tr("yt-dlp path:"), self._row(self.edit_ytdlp, btn_ytdlp))
        form.addRow(self.tr("Default database folder:"), self._row(self.edit_dbdir, btn_dbdir))
        return panel

    def _panel_audio(self):
        panel = QWidget()
        form = QFormLayout(panel)

        # 1) CPU cores spinbox
        max_cores = self.settings.value("audio/max_cores", type=int, defaultValue=4)
        self.spin_cores = QSpinBox()
        self.spin_cores.setRange(1, max_cores)
        current_cores = self.settings.value("audio/cpu_count", type=int, defaultValue=max_cores)
        self.spin_cores.setValue(current_cores)
        self.spin_cores.valueChanged.connect(
            lambda val: self.settings.setValue("audio/cpu_count", val)
        )

        # 2) Default sample rate combo
        self.combo_sr = QComboBox()
        self.combo_sr.addItems(["11025", "22050", "44100", "48000"])
        default_sr = self.settings.value("audio/default_sr", type=int, defaultValue=11025)
        self.combo_sr.setCurrentText(str(default_sr))
        self.combo_sr.currentTextChanged.connect(
            lambda text: self.settings.setValue("audio/default_sr", int(text))
        )

        form.addRow(self.tr("CPU cores:"), self.spin_cores)
        form.addRow(self.tr("Default sample rate:"), self.combo_sr)
        return panel

    def _panel_advanced(self):
        panel = QWidget()
        form = QFormLayout(panel)

        # “Rescan system info” button (rescans and immediately saves inside its slot)
        self.btn_rescan = QPushButton(self.tr("Rescan system info"))
        self.btn_rescan.clicked.connect(self._on_rescan)

        # “Open settings storage” button (just opens the file/registry)
        self.btn_open_config = QPushButton(self.tr("Open config storage"))
        self.btn_open_config.clicked.connect(self._on_open_config)

        form.addRow(self.btn_rescan)
        form.addRow(self.btn_open_config)
        return panel

    # === Helper rows ===
    @staticmethod
    def _row(*widgets):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        for wid in widgets:
            h.addWidget(wid)
        return w

    # ————— Slots for immediate saving —————

    def _save_language(self, new_lang: str):
        """
        Called whenever combo_lang changes.
        Save to QSettings and emit language_changed.
        """
        self.settings.setValue("general/language", new_lang)
        self.language_changed.emit(new_lang)

    def _save_start_maximized(self, state: int):
        """
        Called whenever chk_startup changes.
        state is 0 (unchecked) or 2 (checked) in Qt6.
        """
        is_checked = (state == Qt.CheckState.Checked)
        self.settings.setValue("general/start_maximized", is_checked)

    def _browse_path(self, edit: QLineEdit, prog: str, settings_key: str):
        """
        Open a file dialog to pick an executable. As soon as the user picks one,
        set edit.text() and save into QSettings under settings_key.
        """
        title = self.tr(f"Find {prog} executable")
        file_path, _ = QFileDialog.getOpenFileName(self, title)
        if file_path:
            edit.setText(file_path)
            self.settings.setValue(settings_key, file_path)

    def _browse_dir(self, edit: QLineEdit, settings_key: str):
        """
        Open a folder dialog. As soon as the user picks one,
        set edit.text() and save into QSettings under settings_key.
        """
        title = self.tr("Select folder")
        folder = QFileDialog.getExistingDirectory(self, title)
        if folder:
            edit.setText(folder)
            self.settings.setValue(settings_key, folder)

    def _on_rescan(self):
        """
        Re‐compute system info (e.g. cpu_count, platform) and save.
        """
        import multiprocessing, platform
        new_cpu_count = multiprocessing.cpu_count()
        self.settings.setValue("audio/max_cores", new_cpu_count)
        # Also update the spinbox’s range/value to reflect new max:
        self.spin_cores.setMaximum(new_cpu_count)
        self.spin_cores.setValue(new_cpu_count)

        # Example: save “platform” if you want to show it in About:
        plat_str = platform.system() + " " + platform.release()
        self.settings.setValue("app/platform", plat_str)

    def _on_open_config(self):
        """
        Open the underlying settings store (INI/PLIST file or registry).
        """
        config_file = self._settings_path()
        if config_file:
            import os, subprocess, sys
            if sys.platform.startswith(("linux", "darwin")):
                opener = "xdg-open" if sys.platform.startswith("linux") else "open"
                subprocess.Popen([opener, config_file])
            else:
                try:
                    os.startfile(config_file)
                except OSError:
                    pass

    def _settings_path(self) -> str | None:
        """
        Return the path to the settings file on disk, if applicable.
        On Windows (NativeFormat = registry), return None.
        """
        fmt = self.settings.format()
        if fmt == QSettings.Format.NativeFormat:
            return None
        else:
            return self.settings.fileName()
