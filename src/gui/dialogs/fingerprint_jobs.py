from __future__ import annotations

import os
import sys
import subprocess
from collections import defaultdict
from pathlib import Path

from PyQt6.QtCore import Qt, QDir, QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QTreeView,
    QComboBox,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QTextEdit,
    QSpinBox,
    QCheckBox,
)

from PyQt6.QtGui import QFileSystemModel

from ..widgets.job_table import JobTableView, JobItem  # relative import

AUDFPRINT_PY = (
    Path(__file__).parents[2] / "scripts" / "audfprint" / "audfprint.py"
)


# ═════════════════════════════ Worker ═══════════════════════════════════════
class FPWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(int)  # rc 0 = ok

    def __init__(
        self,
        src: str,
        db_pklz: str,
        recurse: bool,
        pattern: str,
        ncores: int,
        verbose: bool,
        skip_errors: bool,
    ):
        super().__init__()
        self.src = src
        self.db_pklz = db_pklz
        self.recurse = recurse
        self.pattern = pattern
        self.ncores = ncores
        self.verbose = verbose
        self.skip_errors = skip_errors
        self._proc: subprocess.Popen | None = None

    # ------------------------------------------------------------------ API
    def stop(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()

    # ------------------------------------------------------------------ main
    def run(self):
        mode = "new" if not Path(self.db_pklz).exists() else "add"
        cmd: list[str] = [
            sys.executable,
            str(AUDFPRINT_PY),
            mode,
            "--dbase",
            self.db_pklz,
        ]

        if self.skip_errors:
            cmd.append("-C")

        cmd.append(self.src)

        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in self._proc.stdout:  # type: ignore[assignment]
            self.log.emit(line.rstrip())
        self._proc.wait()
        self.progress.emit(100)
        self.finished.emit(self._proc.returncode)


# ═══════════════════════════ UI widget ═════════════════════════════════════
class FingerprintJobsWidget(QWidget):
    """audfprint queue with user-configurable options."""

    # ------------------------------------------------------------ ctor
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        root_layout = QVBoxLayout(self)

        # 1) Drive combo + file tree
        self.drive_combo = QComboBox()
        self._populate_drives()
        self.drive_combo.currentTextChanged.connect(self._drive_changed)

        drive_row = QHBoxLayout()
        drive_row.addWidget(self.drive_combo)
        drive_row.addStretch(1)
        root_layout.addLayout(drive_row)

        # model
        self.model = QFileSystemModel(self)
        self.model.setFilter(
            self.model.filter() | QDir.Filter.AllDirs
        )
        root_path = self.drive_combo.currentText()

        # tree
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.tree.setColumnWidth(0, 260)
        self._set_tree_root(root_path)  # tree is defined, no AttributeError
        root_layout.addWidget(self.tree, stretch=2)

        # 2) Output + options form
        form = QFormLayout()
        self.out_edit = QLineEdit()
        browse = QPushButton("…")
        browse.clicked.connect(self._browse_out)
        form.addRow(
            "Fingerprint DB (folder or *.pklz):", self._hrow(self.out_edit, browse)
        )

        self.chk_recurse = QCheckBox("Include sub-folders")
        self.chk_recurse.setChecked(True)
        self.le_pattern = QLineEdit("*.mp3,*.flac,*.wav")
        self.spin_cores = QSpinBox()
        self.spin_cores.setRange(1, os.cpu_count() or 1)
        self.spin_cores.setValue(os.cpu_count() or 1)
        self.chk_verbose = QCheckBox("Verbose output")
        self.chk_skip = QCheckBox("Skip unreadable files")
        self.chk_skip.setChecked(True)

        form.addRow("Match patterns:", self.le_pattern)
        form.addRow("CPU cores:", self.spin_cores)
        form.addRow("", self.chk_recurse)
        form.addRow("", self.chk_skip)
        form.addRow("", self.chk_verbose)

        btn_add = QPushButton("➕ Add Selected")
        btn_add.clicked.connect(self._add_selected)
        form.addRow("", btn_add)

        root_layout.addLayout(form)

        # 3) Job table + toolbar
        self.table = JobTableView()
        root_layout.addWidget(self.table, stretch=1)

        toolbar = QHBoxLayout()
        self.btn_start = QPushButton("Start Selected")
        self.btn_stop = QPushButton("Stop Current")
        self.btn_stop.setEnabled(False)
        self.btn_start.clicked.connect(self._start_selected)
        self.btn_stop.clicked.connect(self._stop_current)
        toolbar.addWidget(self.btn_start)
        toolbar.addWidget(self.btn_stop)
        toolbar.addStretch(1)
        root_layout.addLayout(toolbar)

        # 4) Log pane
        self.log = QTextEdit(readOnly=True)
        self.log.setFixedHeight(150)
        root_layout.addWidget(self.log)

        # internal state
        self._queue: list[int] = []
        self._row_logs: dict[int, list[str]] = defaultdict(list)
        self._current_row: int | None = None
        self._worker: FPWorker | None = None

        self.table.selectionModel().selectionChanged.connect(
            self._sel_changed,  # type: ignore[arg-type]
        )

    # ───────────────────────────── helpers ──────────────────────────────
    @staticmethod
    def _hrow(*widgets) -> QWidget:  # satisfy PyCharm static-method hint
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        for wid in widgets:
            h.addWidget(wid)
        return w

    def _populate_drives(self) -> None:
        drives = [d.absolutePath() for d in QDir.drives()] or ["/"]
        self.drive_combo.addItems(drives)

    def _set_tree_root(self, root_path: str) -> None:
        self.model.setRootPath(root_path)
        self.tree.setRootIndex(self.model.index(root_path))

    # ───────────────────────────── UI slots ─────────────────────────────
    def _drive_changed(self, root: str):
        self._set_tree_root(root)

    def _browse_out(self):
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.out_edit.setText(folder)

    def _add_selected(self):
        out_dir = self.out_edit.text().strip()
        if not out_dir:
            QMessageBox.warning(
                self, "Missing folder", "Select output folder first."
            )
            return
        for idx in self.tree.selectionModel().selectedRows():
            path = self.model.filePath(idx)
            self.table.model.add_job(JobItem(path, out_dir))

    # ───────────────────────── queue control ────────────────────────────
    def _start_selected(self):
        rows = {i.row() for i in self.table.selectionModel().selectedRows()}
        if not rows:
            QMessageBox.information(
                self, "Nothing selected", "Select one or more jobs."
            )
            return
        for r in sorted(rows):
            job = self.table.model.jobs[r]
            if job.state in ("Queued", "⚠ Stopped", "✖ Error"):
                self._queue.append(r)
                job.state = "⏳ Queued"
        self.table.viewport().update()
        self._kick()

    def _kick(self):
        if self._worker or not self._queue:
            return
        row = self._queue.pop(0)
        self._run_row(row)

    def _run_row(self, row: int):
        job = self.table.model.jobs[row]
        self._current_row = row
        job.state = "Running"
        self.table.viewport().update()
        self.log.clear()

        db_path = (
            Path(job.folder)
            if job.folder.lower().endswith(".pklz")
            else Path(job.folder) / "database.pklz"
        )

        self._worker = FPWorker(
            src=job.url,
            db_pklz=str(db_path),
            recurse=self.chk_recurse.isChecked(),
            pattern=self.le_pattern.text().strip(),
            ncores=self.spin_cores.value(),
            verbose=self.chk_verbose.isChecked(),
            skip_errors=self.chk_skip.isChecked(),
        )
        self._worker.progress.connect(
            lambda p: self._update_progress(row, p),  # type: ignore[arg-type]
        )
        self._worker.log.connect(
            lambda s: self._append_log(row, s),  # type: ignore[arg-type]
        )
        self._worker.finished.connect(
            lambda rc: self._row_finished(row, rc),  # type: ignore[arg-type]
        )
        self._worker.start()
        self.btn_stop.setEnabled(True)

    def _stop_current(self):
        if self._worker:
            self._worker.stop()

    # ─────────── worker signal handlers ───────────
    def _update_progress(self, row: int, pct: int):
        job = self.table.model.jobs[row]
        job.progress = pct
        self.table.model.dataChanged.emit(
            self.table.model.index(row, 2), self.table.model.index(row, 2)
        )

    def _append_log(self, row: int, line: str):
        self._row_logs[row].append(line)
        if row == self._current_row:
            self.log.append(line)
            self.log.moveCursor(QTextCursor.MoveOperation.End)

    def _row_finished(self, row: int, rc: int):
        self.btn_stop.setEnabled(False)
        self._worker = None

        job = self.table.model.jobs[row]
        if rc == 0:
            job.state, job.progress = "✔ Done", 100
        else:
            job.state = "✖ Error"
        self.table.viewport().update()
        self._kick()

    # ─────────── log display when user clicks row ───────────
    def _sel_changed(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            return
        row = sel[0].row()
        self.log.clear()
        self.log.append("\n".join(self._row_logs[row]))
        self.log.moveCursor(QTextCursor.MoveOperation.End)
