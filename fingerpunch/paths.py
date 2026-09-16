from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QStandardPaths

APP_DIRECTORY_NAME = "FingerPunch"
DATABASE_FILENAME = "typingStats.db"


def app_data_dir() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.GenericDataLocation)
    root = Path(base) if base else Path.home() / ".local" / "share"
    return root / APP_DIRECTORY_NAME


def default_database_path() -> Path:
    return app_data_dir() / DATABASE_FILENAME
