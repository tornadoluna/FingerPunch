"""Tests for the typing input area, which must not accept pasted text."""

import sqlite3

import pytest
from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from fingerpunch.ui.widgets import TypingInput


@pytest.fixture
def clipboard(qapp):
    board = QApplication.clipboard()
    original = board.text()
    yield board
    board.setText(original)


@pytest.fixture
def typing_input(qapp):
    widget = TypingInput()
    yield widget
    widget.deleteLater()


def text_mime(text="smuggled"):
    data = QMimeData()
    data.setText(text)
    return data


class TestPasteIsRefused:
    def test_the_paste_method_inserts_nothing(self, typing_input, clipboard):
        clipboard.setText("the quick brown fox")

        typing_input.paste()

        assert typing_input.toPlainText() == ""

    def test_the_paste_shortcut_inserts_nothing(self, typing_input, clipboard):
        clipboard.setText("the quick brown fox")
        typing_input.setFocus()

        QTest.keySequence(typing_input, QKeySequence.Paste)

        assert typing_input.toPlainText() == ""

    def test_pasting_does_not_disturb_text_already_typed(self, typing_input, clipboard):
        typing_input.setPlainText("the qui")
        clipboard.setText("ck brown fox")

        typing_input.paste()

        assert typing_input.toPlainText() == "the qui"

    def test_the_widget_reports_that_it_cannot_accept_text(self, typing_input):
        assert typing_input.canInsertFromMimeData(text_mime()) is False

    def test_inserting_mime_data_directly_is_a_no_op(self, typing_input):
        typing_input.insertFromMimeData(text_mime())

        assert typing_input.toPlainText() == ""

    def test_the_widget_does_not_accept_drops(self, typing_input):
        assert typing_input.acceptDrops() is False


class TestTypingStillWorks:
    def test_keystrokes_are_inserted(self, typing_input):
        typing_input.setFocus()

        QTest.keyClicks(typing_input, "hello")

        assert typing_input.toPlainText() == "hello"

    def test_backspace_still_deletes(self, typing_input):
        typing_input.setFocus()
        QTest.keyClicks(typing_input, "hello")

        QTest.keyClick(typing_input, Qt.Key_Backspace)

        assert typing_input.toPlainText() == "hell"

    def test_setting_text_programmatically_still_works(self, typing_input):
        typing_input.setPlainText("set directly")

        assert typing_input.toPlainText() == "set directly"

    def test_clearing_still_works(self, typing_input):
        typing_input.setPlainText("something")

        typing_input.clear()

        assert typing_input.toPlainText() == ""

    def test_text_changes_are_still_announced(self, typing_input):
        seen = []
        typing_input.textChanged.connect(lambda: seen.append(typing_input.toPlainText()))
        typing_input.setFocus()

        QTest.keyClicks(typing_input, "ab")

        assert seen == ["a", "ab"]


class TestSessionCannotBePasted:
    def test_pasting_the_sample_does_not_finish_the_session(self, window, clipboard):
        clipboard.setText(window.sample_text)
        window.start_practice()

        window.input_edit.paste()

        assert window.input_edit.toPlainText() == ""
        assert window.is_done is False

    def test_pasting_the_sample_records_no_session(self, window, clipboard):
        clipboard.setText(window.sample_text)
        window.start_practice()

        window.input_edit.paste()

        with sqlite3.connect(window.data_manager.db_path) as conn:
            assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0

    def test_pasting_does_not_advance_the_progress_bar(self, window, clipboard):
        clipboard.setText(window.sample_text)

        window.input_edit.paste()

        assert window.progress_bar.value() == 0

    def test_typing_the_sample_by_hand_still_finishes_the_session(self, window, results_dialog):
        window.input_edit.setFocus()

        QTest.keyClicks(window.input_edit, window.sample_text)

        assert window.is_done is True
        results_dialog.assert_called_once()

    def test_the_window_uses_the_paste_proof_input(self, window):
        assert isinstance(window.input_edit, TypingInput)
