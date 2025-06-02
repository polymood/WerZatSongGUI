from typing import List
import os

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import (
    QTableView,
    QHeaderView,
    QWidget
)


class JobItem:
    """Lightweight data holder."""

    def __init__(self, url: str, folder: str) -> None:
        self.url = url
        self.folder = folder
        self.progress = 0        # %
        self.state = "Queued"    # Queued | Running | Paused | Done | Error


class JobTableModel(QAbstractTableModel):
    COLS = ["URL / Title", "Folder", "Progress", "State", ""]

    def __init__(self, jobs: List[JobItem] | None = None):
        super().__init__()
        self.jobs: List[JobItem] = jobs or []

    # ------------------------------------------------- Qt overrides
    def rowCount(self, parent: QModelIndex = ...) -> int:           # noqa: N802
        return len(self.jobs)

    def columnCount(self, parent: QModelIndex = ...) -> int:        # noqa: N802
        return len(self.COLS)

    def data(self, index: QModelIndex, role: int = ...) -> str:  # noqa: N802
        if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole,):
            return ""
        job = self.jobs[index.row()]
        col = index.column()
        if col == 0:
            return job.url
        if col == 1:
            if os.path.isdir(job.folder):
                return "📁 " + job.folder
            return job.folder
        if col == 2:
            return f"{job.progress:>3d} %"
        if col == 3:
            # Always ensure icon is present for all states:
            icon_map = {
                "Queued": "⏳ Queued",
                "Running": "▶ Running",
                "Paused": "⏸ Paused",
                "Done": "✔ Done",
                "Error": "✖ Error",
                "⚠ Stopped": "⚠ Stopped",
            }
            # If already has icon, don't double up
            for k, v in icon_map.items():
                if job.state.endswith(k):
                    return v
            return icon_map.get(job.state, job.state)
        return ""

    def headerData(                     # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.COLS[section]
        return super().headerData(section, orientation, role)

    # ------------------------------------------------- helpers (UI can call)
    def add_job(self, job: JobItem) -> None:
        self.beginInsertRows(QModelIndex(), len(self.jobs), len(self.jobs))
        self.jobs.append(job)
        self.endInsertRows()

    def remove_job(self, row: int) -> None:
        if 0 <= row < len(self.jobs):
            self.beginRemoveRows(QModelIndex(), row, row)
            self.jobs.pop(row)
            self.endRemoveRows()


class JobTableView(QTableView):
    """Reusable table widget for any job queue."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.model = JobTableModel()
        self.setModel(self.model)
        self.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.verticalHeader().hide()
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
