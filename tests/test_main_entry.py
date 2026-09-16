from unittest.mock import MagicMock, patch

import pytest

from fingerpunch import __main__ as entry
from fingerpunch.data_manager import StorageError


@pytest.fixture
def stubbed_app(monkeypatch):
    app = MagicMock()
    app.exec.return_value = 0
    monkeypatch.setattr(entry, "QApplication", lambda argv: app)
    monkeypatch.setattr(entry, "configure_logging", MagicMock())
    monkeypatch.setattr(entry, "install_excepthook", MagicMock())
    return app


class TestStartup:
    def test_logging_is_configured_before_anything_else(self, stubbed_app, monkeypatch):
        monkeypatch.setattr(entry, "TypingPracticeApp", MagicMock())

        with pytest.raises(SystemExit):
            entry.main()

        entry.configure_logging.assert_called_once()
        entry.install_excepthook.assert_called_once()

    def test_the_application_name_is_set(self, stubbed_app, monkeypatch):
        monkeypatch.setattr(entry, "TypingPracticeApp", MagicMock())
        with patch.object(entry, "QCoreApplication") as core, pytest.raises(SystemExit):
            entry.main()

        core.setApplicationName.assert_called_once_with("FingerPunch")

    def test_the_window_is_shown_and_the_event_loop_runs(self, stubbed_app, monkeypatch):
        window = MagicMock()
        monkeypatch.setattr(entry, "TypingPracticeApp", lambda: window)

        with pytest.raises(SystemExit) as exit_info:
            entry.main()

        window.show.assert_called_once()
        stubbed_app.exec.assert_called_once()
        assert exit_info.value.code == 0


class TestStartupFailure:
    def test_a_storage_error_exits_non_zero_instead_of_crashing(self, stubbed_app, monkeypatch):
        monkeypatch.setattr(entry, "TypingPracticeApp", _raise_storage_error)

        with patch.object(entry, "show_message"), pytest.raises(SystemExit) as exit_info:
            entry.main()

        assert exit_info.value.code == 1

    def test_the_user_is_told_why_it_could_not_start(self, stubbed_app, monkeypatch):
        monkeypatch.setattr(entry, "TypingPracticeApp", _raise_storage_error)

        with patch.object(entry, "show_message") as message, pytest.raises(SystemExit):
            entry.main()

        message.assert_called_once()
        assert message.call_args[0][1] == "FingerPunch could not start"
        assert "disk is full" in message.call_args[0][2]

    def test_the_message_points_at_the_log_file(self, stubbed_app, monkeypatch):
        monkeypatch.setattr(entry, "TypingPracticeApp", _raise_storage_error)
        monkeypatch.setattr(entry, "log_file_path", lambda: "/tmp/somewhere/fingerpunch.log")

        with patch.object(entry, "show_message") as message, pytest.raises(SystemExit):
            entry.main()

        assert "/tmp/somewhere/fingerpunch.log" in message.call_args[0][2]

    def test_the_event_loop_never_starts(self, stubbed_app, monkeypatch):
        monkeypatch.setattr(entry, "TypingPracticeApp", _raise_storage_error)

        with patch.object(entry, "show_message"), pytest.raises(SystemExit):
            entry.main()

        stubbed_app.exec.assert_not_called()


def _raise_storage_error():
    raise StorageError("disk is full")
