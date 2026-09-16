import sqlite3
from unittest.mock import patch

import pytest

from fingerpunch.data_manager import DataManager, StorageError
from fingerpunch.ui import history_dialog, main_window


class TestStorageErrors:
    def test_a_corrupt_database_raises_a_storage_error(self, tmp_path):
        corrupt = tmp_path / "corrupt.db"
        corrupt.write_bytes(b"not a database" * 100)

        with pytest.raises(StorageError):
            DataManager(str(corrupt))

    def test_a_corrupt_database_does_not_leak_sqlite3_errors(self, tmp_path):
        corrupt = tmp_path / "corrupt.db"
        corrupt.write_bytes(b"not a database" * 100)

        try:
            DataManager(str(corrupt))
        except StorageError as error:
            assert isinstance(error.__cause__, sqlite3.Error)

    def test_an_uncreatable_directory_raises_a_storage_error(self, tmp_path):
        blocked = tmp_path / "blocked"
        blocked.mkdir()
        blocked.chmod(0o500)
        try:
            with pytest.raises(StorageError):
                DataManager(str(blocked / "sub" / "x.db"))
        finally:
            blocked.chmod(0o700)

    def test_a_query_failure_is_wrapped(self, tmp_path):
        db = DataManager(str(tmp_path / "ok.db"))
        with sqlite3.connect(db.db_path) as conn:
            conn.execute("DROP TABLE sessions")
            conn.commit()

        with pytest.raises(StorageError):
            db.get_all_sessions()

    def test_connections_do_not_accumulate(self, tmp_path):
        import os

        db = DataManager(str(tmp_path / "ok.db"))
        db.get_all_sessions()
        before = len(os.listdir(f"/proc/{os.getpid()}/fd"))

        for _ in range(50):
            db.get_all_sessions()

        assert len(os.listdir(f"/proc/{os.getpid()}/fd")) <= before


class TestFinishingASessionSurvivesStorageFailure:
    def test_the_results_are_still_shown(self, window, results_dialog):
        with patch.object(window.data_manager, "save_session", side_effect=StorageError("full")), \
             patch.object(main_window, "show_message"):
            window.input_edit.setPlainText(window.sample_text)

        results_dialog.assert_called_once()

    def test_the_user_is_told_the_session_was_not_saved(self, window, results_dialog):
        with patch.object(window.data_manager, "save_session", side_effect=StorageError("full")), \
             patch.object(main_window, "show_message") as message:
            window.input_edit.setPlainText(window.sample_text)

        message.assert_called_once()
        assert message.call_args[0][1] == "Session not saved"

    def test_a_streak_failure_is_handled_too(self, window, results_dialog):
        with patch.object(window.data_manager, "update_streaks", side_effect=StorageError("full")), \
             patch.object(main_window, "show_message") as message:
            window.input_edit.setPlainText(window.sample_text)

        message.assert_called_once()
        results_dialog.assert_called_once()

    def test_a_successful_save_shows_no_warning(self, window, results_dialog):
        with patch.object(main_window, "show_message") as message:
            window.input_edit.setPlainText(window.sample_text)

        message.assert_not_called()
        results_dialog.assert_called_once()


class TestHistorySurvivesStorageFailure:
    def test_an_unreadable_history_reports_instead_of_crashing(self, window, history_dialog_patch):
        with patch.object(window.data_manager, "get_all_sessions", side_effect=StorageError("gone")), \
             patch.object(main_window, "show_message") as message:
            window.show_history_dialog()

        message.assert_called_once()
        assert message.call_args[0][1] == "History unavailable"
        history_dialog_patch.assert_not_called()

    def test_a_dialog_that_fails_to_build_reports_instead_of_crashing(self, window, history_dialog_patch):
        window.input_edit.setPlainText(window.sample_text)
        history_dialog_patch.side_effect = StorageError("gone")

        with patch.object(main_window, "show_message") as message:
            window.show_history_dialog()

        message.assert_called_once()
        assert message.call_args[0][1] == "History unavailable"


class TestDeleteSurvivesStorageFailure:
    def test_a_failed_delete_reports_and_leaves_the_table_alone(self, qapp, tmp_path, monkeypatch):
        db = DataManager(str(tmp_path / "h.db"))
        db.save_session(
            {'wpm': 50.0, 'accuracy': 95.0, 'time': 30.0, 'total_chars': 200,
             'keystrokes': 210, 'efficiency': 95.0},
            "sample",
        )
        dialog = history_dialog.HistoryDialog(db)
        dialog.sessions_table.selectRow(0)
        monkeypatch.setattr(history_dialog, "confirm", lambda *a, **k: True)
        monkeypatch.setattr(db, "delete_session", _raise_storage_error)

        with patch.object(history_dialog, "show_message") as message:
            dialog._delete_selected_session()

        message.assert_called_once()
        assert dialog.sessions_table.rowCount() == 1
        dialog.deleteLater()


def _raise_storage_error(*args, **kwargs):
    raise StorageError("locked")


class TestShutdown:
    def test_closing_stops_the_timer(self, window):
        window.start_practice()
        assert window.timer.isActive()

        window.close()

        assert not window.timer.isActive()

    def test_closing_an_idle_window_is_harmless(self, window):
        window.close()

        assert not window.timer.isActive()


@pytest.fixture
def history_dialog_patch():
    with patch.object(main_window, "HistoryDialog") as dialog:
        dialog.return_value.exec.return_value = 0
        yield dialog
