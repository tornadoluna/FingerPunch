"""
Test suite for TypingPracticeApp.

These tests drive a real widget on Qt's offscreen platform, so the session
lifecycle, progress rendering and completion handling are exercised through the
same signal wiring the running application uses.
"""

import sqlite3
from unittest.mock import patch

from PySide6.QtWidgets import QDialog, QLabel

from fingerpunch.ui import main_window
from fingerpunch.ui.results_dialog import NEW_TEXT_RESULT
from tests.conftest import SAMPLE


def type_text(window, text):
    window.input_edit.setPlainText(text)


def saved_sessions(window):
    with sqlite3.connect(window.data_manager.db_path) as conn:
        return conn.execute("SELECT wpm, accuracy, sample_text FROM sessions").fetchall()


class TestSessionLifecycle:
    def test_a_new_window_is_idle(self, window):
        assert window.start_time is None
        assert window.is_done is False
        assert window.elapsed_time == 0
        assert not window.timer.isActive()

    def test_start_practice_starts_the_clock(self, window):
        window.start_practice()

        assert window.start_time is not None
        assert window.timer.isActive()
        assert window.timer.interval() == 1000

    def test_start_practice_does_not_restart_a_running_session(self, window):
        window.start_practice()
        original_start = window.start_time

        window.start_practice()

        assert window.start_time == original_start

    def test_typing_starts_the_session_without_pressing_start(self, window):
        type_text(window, "t")

        assert window.start_time is not None
        assert window.timer.isActive()
        assert window.timer.interval() == 1000

    def test_typing_does_not_move_the_start_time_of_a_running_session(self, window):
        type_text(window, "t")
        original_start = window.start_time

        type_text(window, "th")

        assert window.start_time == original_start

    def test_reset_returns_the_window_to_idle(self, window):
        window.start_practice()
        type_text(window, "the quick")

        window.reset_practice()

        assert window.start_time is None
        assert window.elapsed_time == 0
        assert window.is_done is False
        assert not window.timer.isActive()
        assert window.input_edit.toPlainText() == ""
        assert window.progress_bar.value() == 0

    def test_reset_emits_zeroed_stats(self, window):
        received = []
        window.stats_updated.connect(lambda *args: received.append(args))

        window.reset_practice()

        assert received == [("0", "0%", "0s")]

    def test_reset_clears_the_stats_worker(self, window):
        type_text(window, "the")

        window.reset_practice()

        assert window.stats_worker.total_keystrokes == 0
        assert window.stats_worker.samples == []


class TestProgressRendering:
    def test_progress_tracks_correctly_typed_characters(self, window):
        type_text(window, "the ")

        assert window.progress_bar.value() == int(4 / len(SAMPLE) * 100)

    def test_incorrect_characters_do_not_count_toward_progress(self, window):
        type_text(window, "thX ")

        assert window.progress_bar.value() == int(3 / len(SAMPLE) * 100)

    def test_progress_reaches_100_on_an_exact_match(self, window):
        type_text(window, SAMPLE)

        assert window.progress_bar.value() == 100

    def test_typing_past_the_end_does_not_exceed_100(self, window):
        type_text(window, SAMPLE + " and then some")

        assert window.progress_bar.value() == 100

    def test_correct_and_incorrect_characters_are_coloured_differently(self, window):
        type_text(window, "thX")
        html = window.text_label.toHtml().lower()

        assert main_window.styles.SUCCESS.lower() in html
        assert main_window.styles.DANGER.lower() in html

    def test_html_special_characters_in_the_sample_are_escaped(self, window):
        window.sample_text = "a <b> & c"

        type_text(window, "a <b>")

        assert window.text_label.toPlainText().startswith("a <b> & c")

    def test_an_empty_sample_does_not_divide_by_zero(self, window):
        window.sample_text = ""

        type_text(window, "anything")

        assert window.progress_bar.value() == 0

    def test_typed_text_is_forwarded_to_listeners(self, window):
        received = []
        window.text_updated.connect(received.append)

        type_text(window, "the")

        assert received[-1] == "the"


class TestCompletion:
    def test_an_exact_match_finishes_the_session(self, window, results_dialog):
        type_text(window, SAMPLE)

        assert window.is_done is True
        assert not window.timer.isActive()
        results_dialog.assert_called_once()

    def test_a_full_length_mismatch_does_not_finish_the_session(self, window, results_dialog):
        wrong = "X" + SAMPLE[1:]

        type_text(window, wrong)

        assert len(wrong) == len(SAMPLE)
        assert window.is_done is False
        results_dialog.assert_not_called()

    def test_results_are_shown_only_once_per_session(self, window, results_dialog):
        type_text(window, SAMPLE)
        type_text(window, SAMPLE)

        results_dialog.assert_called_once()

    def test_finishing_saves_the_session(self, window):
        type_text(window, SAMPLE)

        rows = saved_sessions(window)
        assert len(rows) == 1
        assert rows[0][2] == SAMPLE

    def test_finishing_records_a_final_sample_for_the_graph(self, window):
        window.start_practice()

        type_text(window, SAMPLE)

        assert window.stats_worker.samples != []

    def test_finishing_updates_the_streak(self, window):
        type_text(window, SAMPLE)

        assert window.data_manager.get_streak_info()["current_streak"] == 1


class TestResultsDialogRouting:
    def test_try_again_resets_the_same_sample(self, window, results_dialog):
        results_dialog.return_value.exec.return_value = QDialog.Accepted

        type_text(window, SAMPLE)

        assert window.sample_text == SAMPLE
        assert window.is_done is False
        assert window.input_edit.toPlainText() == ""

    def test_new_text_loads_a_fresh_sample(self, window, results_dialog, monkeypatch):
        results_dialog.return_value.exec.return_value = NEW_TEXT_RESULT
        monkeypatch.setattr(main_window, "generate_mixed_text", lambda length: "a brand new sample")

        type_text(window, SAMPLE)

        assert window.sample_text == "a brand new sample"
        assert window.is_done is False

    def test_closing_leaves_the_finished_session_alone(self, window, results_dialog):
        results_dialog.return_value.exec.return_value = QDialog.Rejected

        type_text(window, SAMPLE)

        assert window.is_done is True
        assert window.input_edit.toPlainText() == SAMPLE


class TestSampleLength:
    def test_choosing_a_word_count_regenerates_the_sample(self, window, monkeypatch):
        requested = []
        monkeypatch.setattr(
            main_window, "generate_mixed_text", lambda length: requested.append(length) or "regenerated"
        )

        window.word_count_combo.setCurrentText("100")

        assert window.text_length == 100
        assert requested == [100]
        assert window.sample_text == "regenerated"

    def test_loading_new_text_resets_progress(self, window):
        type_text(window, "the quick")

        window.load_new_sample_text()

        assert window.input_edit.toPlainText() == ""
        assert window.progress_bar.value() == 0
        assert window.start_time is None


class TestVisualConsistency:
    def test_no_toolbar_button_carries_a_platform_icon(self, window):
        buttons = [
            window.start_button,
            window.reset_button,
            window.new_text_button,
            window.history_button,
        ]

        assert all(button.icon().isNull() for button in buttons)

    def test_button_labels_are_not_clipped(self, qapp, window):
        window.show()
        qapp.processEvents()

        for button in (window.start_button, window.reset_button,
                       window.new_text_button, window.history_button):
            needed = button.fontMetrics().boundingRect(button.text())
            assert button.width() >= needed.width(), button.text()
            assert button.height() >= needed.height(), button.text()

    def test_only_the_primary_action_is_filled(self, window):
        assert "background-color" in window.start_button.styleSheet()
        for button in (window.reset_button, window.new_text_button, window.history_button):
            assert "background-color: transparent" in button.styleSheet(), button.text()


class TestWindowSizing:
    def test_the_window_is_tall_enough_for_its_contents(self, window):
        window.show()

        assert window.layout().minimumSize().height() <= window.height()

    def test_the_minimum_height_follows_the_layout(self, window):
        window.show()

        assert window.minimumHeight() >= window.layout().minimumSize().height()

    def test_showing_the_camera_preview_grows_the_window(self, qapp, window):
        window.show()
        qapp.processEvents()
        before = window.height()

        window.camera_panel.preview.show()
        qapp.processEvents()

        assert window.height() > before
        assert window.layout().minimumSize().height() <= window.height()
        assert window.layout().minimumSize().height() <= window.height()

    def test_hiding_the_preview_lowers_the_minimum_again(self, qapp, window):
        window.show()
        window.camera_panel.preview.show()
        qapp.processEvents()
        grown = window.minimumHeight()

        window.camera_panel.preview.hide()
        qapp.processEvents()

        assert window.minimumHeight() < grown

    def test_no_explicit_minimum_height_overrides_the_layout(self, qapp, window):
        window.show()
        qapp.processEvents()

        assert window.minimumHeight() == window.layout().minimumSize().height()

    def test_the_window_is_wide_enough(self, window):
        window.show()

        assert window.width() >= window.minimumWidth()


class TestLiveStats:
    def test_stats_before_the_session_starts_are_ignored(self, window):
        received = []
        window.stats_updated.connect(lambda *args: received.append(args))

        window.update_stats("42", "99%")

        assert received == []

    def test_stats_are_forwarded_and_remembered(self, window):
        received = []
        window.stats_updated.connect(lambda *args: received.append(args))
        window.start_practice()

        window.update_stats("42", "99%")

        assert window.last_wpm == "42"
        assert window.last_accuracy == "99%"
        assert received[-1][:2] == ("42", "99%")

    def test_the_tick_reuses_the_last_known_stats(self, window):
        window.start_practice()
        window.update_stats("42", "99%")
        received = []
        window.stats_updated.connect(lambda *args: received.append(args))

        window.update_time()

        assert received[-1][:2] == ("42", "99%")

    def test_the_tick_does_nothing_before_the_session_starts(self, window):
        received = []
        window.stats_updated.connect(lambda *args: received.append(args))

        window.update_time()

        assert received == []
        assert window.stats_worker.samples == []


class TestHistory:
    def test_history_reports_when_there_is_nothing_to_show(self, window, history_dialog):
        with patch.object(main_window, "show_message") as message:
            window.show_history_dialog()

        message.assert_called_once()
        history_dialog.assert_not_called()

    def test_history_opens_once_a_session_exists(self, window, history_dialog):
        type_text(window, SAMPLE)

        with patch.object(main_window, "show_message") as message:
            window.show_history_dialog()

        message.assert_not_called()
        history_dialog.assert_called_once_with(window.data_manager, window)
        history_dialog.return_value.exec.assert_called_once()


class TestMessageBox:
    def test_show_message_builds_a_dismissable_dialog(self, window):
        shown = []

        with patch.object(QDialog, "exec", lambda self: shown.append(self)):
            main_window.show_message(window, "A title", "A message")

        assert len(shown) == 1
        dialog = shown[0]
        assert dialog.windowTitle() == "A title"
        assert [label.text() for label in dialog.findChildren(QLabel)] == ["A message"]
