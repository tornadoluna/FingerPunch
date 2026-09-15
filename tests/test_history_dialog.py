"""Tests for the history dialog's table rendering and analytics charts."""

import sqlite3
from datetime import datetime, timedelta

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QLabel, QTextBrowser

from fingerpunch.data_manager import DataManager, Session
from fingerpunch.ui import history_dialog
from fingerpunch.ui.history_dialog import SESSION_COLUMNS, HistoryDialog

CHART_TYPES = ["Performance Overview", "Recent Activity", "Performance by Length"]


@pytest.fixture
def db(tmp_path):
    return DataManager(db_path=str(tmp_path / "history.db"))


def insert_session_at(db, date, wpm=50.0, accuracy=95.0, text_length=100,
                      total_chars=200, keystrokes=210, efficiency=95.0):
    with sqlite3.connect(db.db_path) as conn:
        conn.execute(
            'INSERT INTO sessions (date, wpm, accuracy, time_taken, total_chars,'
            ' keystrokes, efficiency, text_length, sample_text)'
            ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (date, wpm, accuracy, 30.0, total_chars, keystrokes, efficiency, text_length, 'sample'),
        )
        conn.commit()


def session_row(date="2026-03-01T14:30:00", wpm=50.0, accuracy=95.0, time_taken=30.0,
                total_chars=200, keystrokes=210, efficiency=90.0, text_length=100):
    return Session(1, date, wpm, accuracy, time_taken, total_chars, keystrokes, efficiency,
                   text_length, "sample text")


@pytest.fixture
def dialog(qapp):
    created = []

    def build(data_manager):
        widget = HistoryDialog(data_manager)
        created.append(widget)
        return widget

    yield build
    for widget in created:
        widget.deleteLater()


class TestSessionTable:
    def test_an_empty_history_shows_headers_and_no_rows(self, dialog, db):
        widget = dialog(db)

        assert widget.sessions_table.rowCount() == 0
        headers = [
            widget.sessions_table.horizontalHeaderItem(i).text()
            for i in range(widget.sessions_table.columnCount())
        ]
        assert headers == SESSION_COLUMNS

    def test_each_session_becomes_one_row(self, dialog, db):
        for _ in range(3):
            insert_session_at(db, datetime.now().isoformat())
        widget = dialog(db)

        assert widget.sessions_table.rowCount() == 3

    def test_each_value_lands_in_its_own_column(self):
        cells = HistoryDialog._session_cells(
            session_row(wpm=61.25, accuracy=93.46, total_chars=237, keystrokes=259, efficiency=88.4)
        )

        assert cells == ["2026-03-01", "14:30", "61.2", "93.5%", "237", "259", "88.4%"]

    def test_the_timestamp_is_split_into_date_and_time(self):
        cells = HistoryDialog._session_cells(session_row(date="2026-12-25T09:05:59"))

        assert cells[:2] == ["2026-12-25", "09:05"]

    def test_time_taken_is_not_mistaken_for_a_displayed_column(self):
        cells = HistoryDialog._session_cells(session_row(time_taken=1234.5, total_chars=237))

        assert "1234.5" not in cells
        assert "237" in cells

    def test_the_row_carries_the_session_id(self, dialog, db):
        insert_session_at(db, datetime.now().isoformat())
        widget = dialog(db)

        stored = widget.sessions_table.item(0, 0).data(Qt.UserRole)
        assert stored == db.get_all_sessions()[0][0]

    def test_cells_cannot_be_edited(self, dialog, db):
        insert_session_at(db, datetime.now().isoformat())
        widget = dialog(db)

        assert widget.sessions_table.editTriggers() == QAbstractItemView.NoEditTriggers


class TestDeleteSession:
    def test_the_delete_button_starts_disabled(self, dialog, db):
        insert_session_at(db, datetime.now().isoformat())
        widget = dialog(db)

        assert widget.delete_button.isEnabled() is False

    def test_selecting_a_row_enables_the_delete_button(self, dialog, db):
        insert_session_at(db, datetime.now().isoformat())
        widget = dialog(db)

        widget.sessions_table.selectRow(0)

        assert widget.delete_button.isEnabled() is True

    def test_confirming_removes_the_session(self, dialog, db, monkeypatch):
        insert_session_at(db, datetime.now().isoformat(), wpm=40.0)
        insert_session_at(db, datetime.now().isoformat(), wpm=90.0)
        widget = dialog(db)
        monkeypatch.setattr(history_dialog, "confirm", lambda *args, **kwargs: True)

        widget.sessions_table.selectRow(0)
        widget._delete_selected_session()

        assert len(db.get_all_sessions()) == 1
        assert widget.sessions_table.rowCount() == 1

    def test_cancelling_keeps_the_session(self, dialog, db, monkeypatch):
        insert_session_at(db, datetime.now().isoformat())
        widget = dialog(db)
        monkeypatch.setattr(history_dialog, "confirm", lambda *args, **kwargs: False)

        widget.sessions_table.selectRow(0)
        widget._delete_selected_session()

        assert len(db.get_all_sessions()) == 1
        assert widget.sessions_table.rowCount() == 1

    def test_deleting_with_nothing_selected_does_nothing(self, dialog, db, monkeypatch):
        insert_session_at(db, datetime.now().isoformat())
        widget = dialog(db)
        asked = []
        monkeypatch.setattr(history_dialog, "confirm", lambda *a, **k: asked.append(True) or True)

        widget._delete_selected_session()

        assert asked == []
        assert len(db.get_all_sessions()) == 1

    def test_the_row_removed_is_the_row_selected(self, dialog, db, monkeypatch):
        insert_session_at(db, "2026-03-01T10:00:00", wpm=40.0)
        insert_session_at(db, "2026-03-02T10:00:00", wpm=90.0)
        widget = dialog(db)
        monkeypatch.setattr(history_dialog, "confirm", lambda *args, **kwargs: True)

        doomed = widget.sessions_table.item(0, 0).data(Qt.UserRole)
        widget.sessions_table.selectRow(0)
        widget._delete_selected_session()

        remaining = [session[0] for session in db.get_all_sessions()]
        assert doomed not in remaining

    def test_deleting_updates_the_summary_line(self, dialog, db, monkeypatch):
        insert_session_at(db, datetime.now().isoformat(), wpm=40.0)
        insert_session_at(db, datetime.now().isoformat(), wpm=900.0)
        widget = dialog(db)
        monkeypatch.setattr(history_dialog, "confirm", lambda *args, **kwargs: True)
        assert "Best WPM: 900.0" in widget.summary_label.text()

        row = next(
            i for i in range(widget.sessions_table.rowCount())
            if widget.sessions_table.item(i, 2).text() == "900.0"
        )
        widget.sessions_table.selectRow(row)
        widget._delete_selected_session()

        assert "Best WPM: 40.0" in widget.summary_label.text()

    def test_deleting_the_last_session_hides_the_summary(self, dialog, db, monkeypatch):
        insert_session_at(db, datetime.now().isoformat())
        widget = dialog(db)
        monkeypatch.setattr(history_dialog, "confirm", lambda *args, **kwargs: True)

        widget.sessions_table.selectRow(0)
        widget._delete_selected_session()

        assert widget.summary_label.text() == ""
        assert widget.sessions_table.rowCount() == 0

    def test_deleting_recalculates_the_streak(self, dialog, db, monkeypatch):
        insert_session_at(db, (datetime.now() - timedelta(days=1)).isoformat())
        insert_session_at(db, datetime.now().isoformat())
        db.update_streaks()
        widget = dialog(db)
        monkeypatch.setattr(history_dialog, "confirm", lambda *args, **kwargs: True)
        assert db.get_streak_info()["current_streak"] == 2

        today = datetime.now().strftime("%Y-%m-%d")
        row = next(
            i for i in range(widget.sessions_table.rowCount())
            if widget.sessions_table.item(i, 0).text() == today
        )
        widget.sessions_table.selectRow(row)
        widget._delete_selected_session()

        assert db.get_streak_info()["current_streak"] == 0

    def test_the_delete_button_disables_again_after_the_last_row_goes(self, dialog, db, monkeypatch):
        insert_session_at(db, datetime.now().isoformat())
        widget = dialog(db)
        monkeypatch.setattr(history_dialog, "confirm", lambda *args, **kwargs: True)

        widget.sessions_table.selectRow(0)
        widget._delete_selected_session()

        assert widget.delete_button.isEnabled() is False


class TestAnalyticsCharts:
    def test_every_chart_type_renders_on_an_empty_database(self, dialog, db):
        widget = dialog(db)

        for chart_type in CHART_TYPES:
            widget._update_analytics_chart(chart_type)

    def test_every_chart_type_renders_with_sessions(self, dialog, db):
        for offset in range(3):
            insert_session_at(db, (datetime.now() - timedelta(days=offset)).isoformat())
        widget = dialog(db)

        for chart_type in CHART_TYPES:
            widget._update_analytics_chart(chart_type)

    def test_performance_by_length_renders_across_several_lengths(self, dialog, db):
        for length in (10, 50, 200):
            insert_session_at(db, datetime.now().isoformat(), text_length=length)
        widget = dialog(db)

        widget._update_analytics_chart("Performance by Length")

        assert widget.analytics_canvas.figure.axes != []

    def test_selecting_a_chart_from_the_combo_box_redraws(self, dialog, db):
        insert_session_at(db, datetime.now().isoformat())
        widget = dialog(db)

        for chart_type in CHART_TYPES:
            widget.chart_combo.setCurrentText(chart_type)
            assert widget.chart_combo.currentText() == chart_type

    def test_the_combo_box_offers_exactly_the_supported_charts(self, dialog, db):
        widget = dialog(db)

        offered = [widget.chart_combo.itemText(i) for i in range(widget.chart_combo.count())]
        assert offered == CHART_TYPES

    def test_an_unknown_chart_type_clears_the_figure_without_raising(self, dialog, db):
        insert_session_at(db, datetime.now().isoformat())
        widget = dialog(db)

        widget._update_analytics_chart("Not A Chart")

        assert widget.analytics_canvas.figure.axes == []

    def test_recent_activity_ignores_sessions_older_than_thirty_days(self, dialog, db):
        insert_session_at(db, (datetime.now() - timedelta(days=90)).isoformat())
        widget = dialog(db)

        widget._update_analytics_chart("Recent Activity")

        assert widget.analytics_canvas.figure.axes == []

    def test_recent_activity_plots_sessions_inside_the_window(self, dialog, db):
        insert_session_at(db, (datetime.now() - timedelta(days=90)).isoformat())
        insert_session_at(db, (datetime.now() - timedelta(days=2)).isoformat())
        widget = dialog(db)

        widget._update_analytics_chart("Recent Activity")

        assert len(widget.analytics_canvas.figure.axes[0].lines[0].get_xdata()) == 1


class TestSummaryLine:
    def test_an_empty_database_shows_no_summary(self, dialog, db):
        widget = dialog(db)

        texts = [label.text() for label in widget.findChildren(QLabel)]
        assert not any(text.startswith("Total Sessions:") for text in texts)

    def test_the_summary_reports_the_session_count(self, dialog, db):
        insert_session_at(db, datetime.now().isoformat(), wpm=80.0)
        insert_session_at(db, datetime.now().isoformat(), wpm=40.0)
        widget = dialog(db)

        texts = [label.text() for label in widget.findChildren(QLabel)]
        summary = next(text for text in texts if text.startswith("Total Sessions:"))
        assert "Total Sessions: 2" in summary
        assert "Best WPM: 80.0" in summary


class TestProgressTab:
    def test_an_empty_database_explains_there_are_no_bests_yet(self, dialog, db):
        widget = dialog(db)

        texts = [label.text() for label in widget.findChildren(QLabel)]
        assert any("No personal bests yet" in text for text in texts)

    def test_personal_bests_are_listed_once_sessions_exist(self, dialog, db):
        insert_session_at(db, datetime.now().isoformat(), wpm=77.0)
        widget = dialog(db)

        texts = [label.text() for label in widget.findChildren(QLabel)]
        assert "Best WPM:" in texts
        assert "77.0" in texts

    def test_a_session_scoring_zero_still_counts_as_having_bests(self, dialog, db):
        insert_session_at(db, datetime.now().isoformat(), wpm=0.0, accuracy=0.0, efficiency=0.0)
        widget = dialog(db)

        texts = [label.text() for label in widget.findChildren(QLabel)]
        assert not any("No personal bests yet" in text for text in texts)
        assert "Best WPM:" in texts

    def test_the_current_and_longest_streak_are_shown(self, dialog, db):
        insert_session_at(db, (datetime.now() - timedelta(days=1)).isoformat())
        insert_session_at(db, datetime.now().isoformat())
        db.update_streaks()
        widget = dialog(db)

        texts = [label.text() for label in widget.findChildren(QLabel)]
        assert "Current Streak: 2 days" in texts
        assert "Longest Streak: 2 days" in texts

    def test_streak_history_lists_the_recorded_days(self, dialog, db):
        insert_session_at(db, datetime.now().isoformat())
        db.update_streaks()
        widget = dialog(db)

        browsers = [b.toPlainText() for b in widget.findChildren(QTextBrowser)]
        assert any("Recent Streak History" in text for text in browsers)

    def test_a_database_with_sessions_but_no_streak_rows_still_renders(self, dialog, db):
        insert_session_at(db, datetime.now().isoformat())

        widget = dialog(db)

        texts = [label.text() for label in widget.findChildren(QLabel)]
        assert "Current Streak: 0 days" in texts
