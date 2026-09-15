import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication, QDialog

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SAMPLE = "the quick brown fox"


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def results_dialog():
    from fingerpunch.ui import main_window

    with patch.object(main_window, "ResultsDialog") as dialog:
        dialog.return_value.exec.return_value = QDialog.Rejected
        yield dialog


@pytest.fixture
def history_dialog():
    from fingerpunch.ui import main_window

    with patch.object(main_window, "HistoryDialog") as dialog:
        dialog.return_value.exec.return_value = QDialog.Rejected
        yield dialog


@pytest.fixture
def window(qapp, tmp_path, monkeypatch, results_dialog, history_dialog):
    from fingerpunch.data_manager import DataManager
    from fingerpunch.ui import main_window

    db_path = tmp_path / "sessions.db"
    monkeypatch.setattr(main_window, "DataManager", lambda: DataManager(str(db_path)))
    monkeypatch.setattr(main_window, "generate_mixed_text", lambda length: SAMPLE)

    widget = main_window.TypingPracticeApp()
    yield widget
    widget.deleteLater()
