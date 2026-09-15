"""Tests for the end-of-session results dialog."""

import pytest
from PySide6.QtWidgets import QDialog, QLabel

from fingerpunch.ui.results_dialog import NEW_TEXT_RESULT, ResultsDialog


def make_stats(wpm=50.0, accuracy=95.0, time=30.0, total_chars=200, keystrokes=210,
               efficiency=95.0, samples=None):
    return {
        'wpm': wpm,
        'accuracy': accuracy,
        'time': time,
        'total_chars': total_chars,
        'keystrokes': keystrokes,
        'efficiency': efficiency,
        'samples': [] if samples is None else samples,
    }


def make_samples(*errors):
    return [
        {'t': float(i + 1) * 5, 'wpm': 40.0 + i, 'raw_wpm': 45.0 + i, 'errors': count}
        for i, count in enumerate(errors)
    ]


@pytest.fixture
def dialog(qapp):
    created = []

    def build(stats):
        widget = ResultsDialog(stats)
        created.append(widget)
        return widget

    yield build
    for widget in created:
        widget.deleteLater()


def error_marker_times(canvas):
    points = []
    for collection in canvas.figure.axes[0].collections:
        points.extend(offset[0] for offset in collection.get_offsets())
    return points


class TestPerformanceMessage:
    @pytest.mark.parametrize("accuracy, wpm, expected", [
        (98.0, 60.0, "Excellent! You're a typing master."),
        (100.0, 120.0, "Excellent! You're a typing master."),
        (97.9, 60.0, "Great job! Keep practicing to improve your speed."),
        (98.0, 59.9, "Great job! Keep practicing to improve your speed."),
        (95.0, 40.0, "Great job! Keep practicing to improve your speed."),
        (94.9, 40.0, "Good work! Focus on accuracy and speed will follow."),
        (95.0, 39.9, "Good work! Focus on accuracy and speed will follow."),
        (90.0, 0.0, "Good work! Focus on accuracy and speed will follow."),
        (89.9, 200.0, "Keep practicing! Accuracy is the foundation of good typing."),
        (80.0, 0.0, "Keep practicing! Accuracy is the foundation of good typing."),
        (79.9, 0.0, "Don't give up! Every expert was once a beginner."),
        (0.0, 0.0, "Don't give up! Every expert was once a beginner."),
    ])
    def test_the_message_ladder_picks_the_right_tier(self, dialog, accuracy, wpm, expected):
        widget = dialog(make_stats(wpm=wpm, accuracy=accuracy))

        assert widget._performance_message() == expected

    def test_the_message_is_shown_in_the_dialog(self, dialog):
        widget = dialog(make_stats(wpm=100.0, accuracy=99.0))

        texts = [label.text() for label in widget.findChildren(QLabel)]
        assert "Excellent! You're a typing master." in texts

    def test_accuracy_gates_the_top_tier_regardless_of_speed(self, dialog):
        fast_but_sloppy = dialog(make_stats(wpm=150.0, accuracy=85.0))

        assert "Keep practicing" in fast_but_sloppy._performance_message()


class TestChartVisibility:
    @pytest.mark.parametrize("sample_count, expected", [
        (0, False),
        (1, False),
        (2, True),
        (5, True),
    ])
    def test_the_chart_needs_at_least_two_samples(self, dialog, sample_count, expected):
        widget = dialog(make_stats(samples=make_samples(*([0] * sample_count))))

        assert widget._has_chart() is expected

    def test_stats_without_a_samples_key_do_not_crash(self, dialog):
        stats = make_stats()
        del stats['samples']

        widget = dialog(stats)

        assert widget._has_chart() is False

    def test_a_charted_dialog_is_taller_than_a_bare_one(self, dialog):
        bare = dialog(make_stats(samples=[]))
        charted = dialog(make_stats(samples=make_samples(0, 0, 0)))

        assert charted.height() > bare.height()


class TestChartErrorMarkers:
    def test_no_markers_when_the_error_count_never_rises(self, dialog):
        widget = dialog(make_stats(samples=make_samples(0, 0, 0, 0)))

        assert error_marker_times(widget._build_chart()) == []

    def test_a_marker_lands_on_the_sample_where_errors_rose(self, dialog):
        widget = dialog(make_stats(samples=make_samples(0, 0, 1, 1)))

        assert error_marker_times(widget._build_chart()) == [15.0]

    def test_every_rise_gets_its_own_marker(self, dialog):
        widget = dialog(make_stats(samples=make_samples(0, 1, 1, 2, 5)))

        assert error_marker_times(widget._build_chart()) == [10.0, 20.0, 25.0]

    def test_an_error_in_the_very_first_sample_is_marked(self, dialog):
        widget = dialog(make_stats(samples=make_samples(3, 3)))

        assert error_marker_times(widget._build_chart()) == [5.0]

    def test_a_falling_error_count_is_not_marked(self, dialog):
        widget = dialog(make_stats(samples=make_samples(5, 2, 2)))

        assert error_marker_times(widget._build_chart()) == [5.0]

    def test_the_chart_plots_both_net_and_raw_speed(self, dialog):
        widget = dialog(make_stats(samples=make_samples(0, 1, 1)))

        labels = [line.get_label() for line in widget._build_chart().figure.axes[0].lines]
        assert "WPM" in labels
        assert "Raw" in labels

    def test_the_speed_axis_starts_at_zero(self, dialog):
        widget = dialog(make_stats(samples=make_samples(0, 0, 0)))

        assert widget._build_chart().figure.axes[0].get_ylim()[0] == 0


class TestDialogOutcome:
    def test_new_text_reports_its_own_result_code(self, dialog):
        widget = dialog(make_stats())

        widget.new_text()

        assert widget.result() == NEW_TEXT_RESULT
        assert widget.result() not in (QDialog.Accepted, QDialog.Rejected)

    def test_try_again_reports_accepted(self, dialog):
        widget = dialog(make_stats())

        widget.accept()

        assert widget.result() == QDialog.Accepted

    def test_closing_reports_rejected(self, dialog):
        widget = dialog(make_stats())

        widget.reject()

        assert widget.result() == QDialog.Rejected


class TestStatDisplay:
    def test_the_headline_figures_are_rendered_to_one_decimal_place(self, dialog):
        widget = dialog(make_stats(wpm=61.25, accuracy=93.46, time=42.07))

        texts = [label.text() for label in widget.findChildren(QLabel)]
        assert "61.2 WPM" in texts
        assert "93.5%" in texts
        assert "42.1s" in texts

    def test_counts_are_rendered_without_decimals(self, dialog):
        widget = dialog(make_stats(total_chars=237, keystrokes=259))

        texts = [label.text() for label in widget.findChildren(QLabel)]
        assert "237" in texts
        assert "259" in texts

    def test_a_zeroed_session_renders_without_crashing(self, dialog):
        widget = dialog(make_stats(wpm=0.0, accuracy=0.0, time=0.0, total_chars=0,
                                   keystrokes=0, efficiency=0.0))

        texts = [label.text() for label in widget.findChildren(QLabel)]
        assert "0.0 WPM" in texts
