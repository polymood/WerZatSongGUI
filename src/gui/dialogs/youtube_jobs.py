# src/gui/dialogs/youtube_jobs.py
import json
import subprocess
import shlex
from pathlib import Path
from collections import defaultdict

from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QTextEdit,
)

from gui.widgets.job_table import JobTableView, JobItem


YTDLP = "yt-dlp"                                               # adjust path if needed


# ════════════════════════════════════════════════════════════════════════════
# Worker thread
# ════════════════════════════════════════════════════════════════════════════
class JobWorker(QThread):
    progress = pyqtSignal(int)           # percent 0-100
    log_line = pyqtSignal(str)
    finished = pyqtSignal(int)           # rc (0 ok, >0 error)

    def __init__(self, url: str, folder: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.folder = folder
        self._total = 1
        self._current = 0
        self._proc: subprocess.Popen | None = None

    # -- helpers ------------------------------------------------------------
    def _probe_total(self):
        try:
            data = subprocess.check_output(
                [YTDLP, "--flat-playlist", "--dump-single-json", self.url],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            raw = json.loads(data)
            self._total = max(len(raw.get("entries", [])), 1)
        except Exception:
            self._total = 1

    def _run_download(self) -> int:
        out_tpl = (
            f"{Path(self.folder) / '%(uploader)s/%(playlist_title)s/%(title)s.%(ext)s'}"
        )
        cmd = [YTDLP, "--newline", "-o", out_tpl, self.url]
        self._proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in self._proc.stdout:
            self.log_line.emit(line.rstrip())

            # playlist progress line
            if "Downloading video" in line and "of" in line:
                parts = line.split()
                try:
                    idx = parts.index("video") + 1
                    self._current = int(parts[idx])
                    pct = int(self._current / self._total * 100)
                    self.progress.emit(pct)
                except Exception:
                    pass
            # single-video completion
            elif line.startswith("[download]") and "100%" in line:
                self.progress.emit(100)

        self._proc.wait()
        return self._proc.returncode

    # -- public stop --------------------------------------------------------
    def stop(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()

    # -- run ----------------------------------------------------------------
    def run(self):
        try:
            self._probe_total()
            rc = self._run_download()
        except Exception:
            rc = 1
        self.finished.emit(rc)


# ════════════════════════════════════════════════════════════════════════════
# UI widget
# ════════════════════════════════════════════════════════════════════════════
class YouTubeJobsWidget(QWidget):
    """yt-dlp queue UI with sequential execution + stop."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # -------------- add job form --------------------------------------
        form_box = QWidget()
        form = QFormLayout(form_box)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.url_edit = QLineEdit()
        self.folder_edit = QLineEdit()
        browse = QPushButton("…")
        browse.clicked.connect(self._browse)
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder_edit)
        folder_row.addWidget(browse)

        form.addRow("URL (video / playlist / channel):", self.url_edit)
        form.addRow("Save to folder:", folder_row)
        add = QPushButton("➕ Add to queue")
        add.clicked.connect(self._add_job)
        form.addRow("", add)

        # -------------- table ---------------------------------------------
        self.table = JobTableView()

        # -------------- toolbar -------------------------------------------
        tb = QHBoxLayout()
        self.start_btn = QPushButton("Start Selected")
        self.stop_btn = QPushButton("Stop Current")
        self.start_btn.clicked.connect(self._start_selected)
        self.stop_btn.clicked.connect(self._stop_current)
        self.stop_btn.setEnabled(False)
        tb.addWidget(self.start_btn)
        tb.addWidget(self.stop_btn)
        tb.addStretch(1)

        # -------------- log -----------------------------------------------
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(150)

        # -------------- layout --------------------------------------------
        vbox = QVBoxLayout(self)
        vbox.addWidget(form_box)
        vbox.addWidget(self.table)
        vbox.addLayout(tb)
        vbox.addWidget(self.log)

        # -------------- state ---------------------------------------------
        self._queue: list[int] = []        # rows pending
        self._row_logs = defaultdict(list)  # row → list[str]
        self._current_row: int | None = None
        self._worker: JobWorker | None = None

        self.table.selectionModel().selectionChanged.connect(self._sel_changed)

    # ═════════════════════ adding jobs ════════════════════════════════════
    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select output folder")
        if d:
            self.folder_edit.setText(d)

    def _add_job(self):
        url, folder = self.url_edit.text().strip(), self.folder_edit.text().strip()
        if not url or not folder:
            QMessageBox.warning(self, "Missing data", "Please enter URL and folder.")
            return
        self.table.model.add_job(JobItem(url, folder))
        self.url_edit.clear()

    # ═════════════════════ starting / stopping ════════════════════════════
    def _start_selected(self):
        rows = {i.row() for i in self.table.selectionModel().selectedRows()}
        if not rows:
            QMessageBox.information(self, "Nothing selected", "Select one or more jobs.")
            return
        # enqueue only queued jobs
        for r in sorted(rows):
            job = self.table.model.jobs[r]
            if job.state in ("Queued", "⚠ Stopped", "✖ Error"):
                self._queue.append(r)
                job.state = "⏳ Queued"
        self.table.viewport().update()
        self._kick_queue()

    def _kick_queue(self):
        if self._worker or not self._queue:
            return
        row = self._queue.pop(0)
        self._start_row(row)

    def _start_row(self, row: int):
        job = self.table.model.jobs[row]
        self._current_row = row
        job.state = "Running"
        self.table.viewport().update()
        self.log.clear()
        self._worker = JobWorker(job.url, job.folder)
        self._worker.progress.connect(lambda p: self._on_progress(row, p))
        self._worker.log_line.connect(lambda s: self._on_log(row, s))
        self._worker.finished.connect(lambda rc: self._on_finished(row, rc))
        self._worker.start()
        self.stop_btn.setEnabled(True)

    def _stop_current(self):
        if self._worker:
            self._worker.stop()

    # ═════════════════════ worker slots ═══════════════════════════════════
    def _on_progress(self, row: int, pct: int):
        job = self.table.model.jobs[row]
        job.progress = pct
        idx = self.table.model.index(row, 2)
        self.table.model.dataChanged.emit(idx, idx)

    def _on_log(self, row: int, line: str):
        self._row_logs[row].append(line)
        if row == self._current_row:
            self.log.append(line)
            self.log.moveCursor(QTextCursor.MoveOperation.End)

    def _on_finished(self, row: int, rc: int):
        self.stop_btn.setEnabled(False)
        self._worker = None
        job = self.table.model.jobs[row]
        if rc == 0:
            job.progress = 100
            job.state = "✔ Done"
        else:
            job.state = "✖ Error"
        self.table.viewport().update()
        self._kick_queue()  # start next

    # ═════════════════════ GUI helpers ═══════════════════════════════════
    def _sel_changed(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return
        row = indexes[0].row()
        self.log.clear()
        self.log.append("\n".join(self._row_logs[row]))
        self.log.moveCursor(QTextCursor.MoveOperation.End)
