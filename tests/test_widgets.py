import pytest
from PySide6.QtWidgets import QDialog, QLabel, QPushButton

from fingerpunch.ui.widgets import confirm, show_message


@pytest.fixture
def parent(qapp):
    from PySide6.QtWidgets import QWidget

    widget = QWidget()
    yield widget
    widget.deleteLater()


def capture_dialog(result):
    shown = []

    def fake_exec(self):
        shown.append(self)
        return result

    return shown, fake_exec


class TestShowMessage:
    def test_it_shows_the_title_and_message(self, parent):
        shown, fake_exec = capture_dialog(QDialog.Rejected)

        with pytest.MonkeyPatch.context() as m:
            m.setattr(QDialog, "exec", fake_exec)
            show_message(parent, "A title", "A message")

        assert shown[0].windowTitle() == "A title"
        assert [label.text() for label in shown[0].findChildren(QLabel)] == ["A message"]

    def test_it_offers_only_a_close_button(self, parent):
        shown, fake_exec = capture_dialog(QDialog.Rejected)

        with pytest.MonkeyPatch.context() as m:
            m.setattr(QDialog, "exec", fake_exec)
            show_message(parent, "A title", "A message")

        assert [b.text() for b in shown[0].findChildren(QPushButton)] == ["Close"]


class TestConfirm:
    def test_accepting_returns_true(self, parent):
        _, fake_exec = capture_dialog(QDialog.Accepted)

        with pytest.MonkeyPatch.context() as m:
            m.setattr(QDialog, "exec", fake_exec)
            assert confirm(parent, "Delete session", "Are you sure?") is True

    def test_rejecting_returns_false(self, parent):
        _, fake_exec = capture_dialog(QDialog.Rejected)

        with pytest.MonkeyPatch.context() as m:
            m.setattr(QDialog, "exec", fake_exec)
            assert confirm(parent, "Delete session", "Are you sure?") is False

    def test_closing_the_dialog_any_other_way_returns_false(self, parent):
        _, fake_exec = capture_dialog(0)

        with pytest.MonkeyPatch.context() as m:
            m.setattr(QDialog, "exec", fake_exec)
            assert confirm(parent, "Delete session", "Are you sure?") is False

    def test_it_offers_cancel_and_a_named_confirm_button(self, parent):
        shown, fake_exec = capture_dialog(QDialog.Rejected)

        with pytest.MonkeyPatch.context() as m:
            m.setattr(QDialog, "exec", fake_exec)
            confirm(parent, "Delete session", "Are you sure?", confirm_label="Delete")

        assert [b.text() for b in shown[0].findChildren(QPushButton)] == ["Cancel", "Delete"]

    def test_cancel_is_the_default_button(self, parent):
        shown, fake_exec = capture_dialog(QDialog.Rejected)

        with pytest.MonkeyPatch.context() as m:
            m.setattr(QDialog, "exec", fake_exec)
            confirm(parent, "Delete session", "Are you sure?")

        cancel = next(b for b in shown[0].findChildren(QPushButton) if b.text() == "Cancel")
        assert cancel.isDefault() is True
