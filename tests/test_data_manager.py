"""Tests for the SQLite persistence layer."""

import json
import sqlite3
from datetime import datetime, timedelta

import pytest

from fingerpunch.data_manager import DataManager


@pytest.fixture
def db(tmp_path):
    """A DataManager backed by a throwaway database."""
    return DataManager(db_path=str(tmp_path / "test.db"))


def make_stats(wpm=50.0, accuracy=95.0, time=30.0, total_chars=200, keystrokes=210, efficiency=95.0):
    return {
        'wpm': wpm,
        'accuracy': accuracy,
        'time': time,
        'total_chars': total_chars,
        'keystrokes': keystrokes,
        'efficiency': efficiency,
    }


def insert_session_at(db, date, wpm=50.0, accuracy=95.0, text_length=100):
    """Insert a session with an explicit date, which save_session cannot do."""
    with sqlite3.connect(db.db_path) as conn:
        conn.execute(
            'INSERT INTO sessions (date, wpm, accuracy, time_taken, total_chars,'
            ' keystrokes, efficiency, text_length, sample_text)'
            ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (date, wpm, accuracy, 30.0, 200, 210, 95.0, text_length, 'sample'),
        )
        conn.commit()


class TestSaveAndRetrieve:
    def test_saved_session_round_trips(self, db):
        db.save_session(make_stats(wpm=61.5, accuracy=97.25), 'hello world')

        sessions = db.get_all_sessions()
        assert len(sessions) == 1
        _id, _date, wpm, accuracy, time_taken, total_chars, keystrokes, efficiency, text_length, sample_text = sessions[0]
        assert wpm == 61.5
        assert accuracy == 97.25
        assert time_taken == 30.0
        assert total_chars == 200
        assert keystrokes == 210
        assert efficiency == 95.0
        assert text_length == len('hello world')
        assert sample_text == 'hello world'

    def test_sample_text_is_truncated_but_length_is_not(self, db):
        long_text = 'x' * 500
        db.save_session(make_stats(), long_text)

        session = db.get_all_sessions()[0]
        assert session[8] == 500, "text_length should record the true length"
        assert session[9] == 'x' * 200, "only the first 200 chars are stored"

    def test_get_all_sessions_is_empty_for_a_new_database(self, db):
        assert db.get_all_sessions() == []

    def test_get_all_sessions_respects_limit(self, db):
        for i in range(5):
            insert_session_at(db, f'2026-01-0{i + 1}T10:00:00')

        assert len(db.get_all_sessions()) == 5
        assert len(db.get_all_sessions(limit=2)) == 2

    def test_get_all_sessions_orders_newest_first(self, db):
        insert_session_at(db, '2026-01-01T10:00:00', wpm=10.0)
        insert_session_at(db, '2026-03-01T10:00:00', wpm=30.0)
        insert_session_at(db, '2026-02-01T10:00:00', wpm=20.0)

        assert [s[2] for s in db.get_all_sessions()] == [30.0, 20.0, 10.0]

    def test_date_range_query_is_inclusive_of_both_ends(self, db):
        insert_session_at(db, '2026-01-01T00:00:00', wpm=1.0)
        insert_session_at(db, '2026-01-15T00:00:00', wpm=2.0)
        insert_session_at(db, '2026-02-01T00:00:00', wpm=3.0)

        found = db.get_sessions_by_date_range('2026-01-01T00:00:00', '2026-01-15T00:00:00')

        assert sorted(s[2] for s in found) == [1.0, 2.0]


class TestDeleteSession:
    def test_deleting_removes_only_that_session(self, db):
        db.save_session(make_stats(wpm=40.0))
        db.save_session(make_stats(wpm=90.0))
        doomed = db.get_all_sessions()[0][0]

        assert db.delete_session(doomed) is True

        remaining = db.get_all_sessions()
        assert len(remaining) == 1
        assert remaining[0][0] != doomed

    def test_deleting_a_missing_session_reports_nothing_removed(self, db):
        db.save_session(make_stats())

        assert db.delete_session(9999) is False
        assert len(db.get_all_sessions()) == 1

    def test_deleting_from_an_empty_database_is_harmless(self, db):
        assert db.delete_session(1) is False

    def test_aggregates_reflect_the_deletion(self, db):
        db.save_session(make_stats(wpm=40.0))
        db.save_session(make_stats(wpm=900.0))
        outlier = next(s[0] for s in db.get_all_sessions() if s[2] == 900.0)

        db.delete_session(outlier)

        assert db.get_session_stats()["best_wpm"] == 40.0

    def test_personal_bests_reflect_the_deletion(self, db):
        db.save_session(make_stats(wpm=40.0))
        db.save_session(make_stats(wpm=900.0))
        outlier = next(s[0] for s in db.get_all_sessions() if s[2] == 900.0)

        db.delete_session(outlier)

        assert db.get_personal_bests()["best_wpm"]["value"] == 40.0

    def test_streaks_recalculate_after_a_deletion(self, db):
        insert_session_at(db, (datetime.now() - timedelta(days=1)).isoformat())
        insert_session_at(db, datetime.now().isoformat())
        db.update_streaks()
        assert db.get_streak_info()["current_streak"] == 2

        today = datetime.now().date().isoformat()
        doomed = next(s[0] for s in db.get_all_sessions() if s[1].startswith(today))
        db.delete_session(doomed)
        db.update_streaks()

        assert db.get_streak_info()["current_streak"] == 0


class TestSessionStats:
    def test_empty_database_returns_zeros_rather_than_none(self, db):
        stats = db.get_session_stats()

        assert stats == {
            'total_sessions': 0,
            'avg_wpm': 0,
            'best_wpm': 0,
            'avg_accuracy': 0,
            'best_accuracy': 0,
            'total_time': 0,
        }

    def test_single_session_makes_average_equal_best(self, db):
        db.save_session(make_stats(wpm=42.0, accuracy=91.0))

        stats = db.get_session_stats()

        assert stats['total_sessions'] == 1
        assert stats['avg_wpm'] == stats['best_wpm'] == 42.0
        assert stats['avg_accuracy'] == stats['best_accuracy'] == 91.0

    def test_aggregates_across_sessions(self, db):
        insert_session_at(db, '2026-01-01T10:00:00', wpm=40.0, accuracy=90.0)
        insert_session_at(db, '2026-01-02T10:00:00', wpm=60.0, accuracy=100.0)

        stats = db.get_session_stats()

        assert stats['total_sessions'] == 2
        assert stats['avg_wpm'] == 50.0
        assert stats['best_wpm'] == 60.0
        assert stats['avg_accuracy'] == 95.0
        assert stats['best_accuracy'] == 100.0
        assert stats['total_time'] == 60.0

    def test_averages_are_rounded_to_one_decimal_place(self, db):
        insert_session_at(db, '2026-01-01T10:00:00', wpm=40.0, accuracy=90.0)
        insert_session_at(db, '2026-01-02T10:00:00', wpm=41.0, accuracy=91.0)
        insert_session_at(db, '2026-01-03T10:00:00', wpm=41.0, accuracy=91.0)

        stats = db.get_session_stats()

        assert stats['avg_wpm'] == 40.7, "40.666... rounds to one decimal place"
        assert stats['avg_accuracy'] == 90.7


class TestSettings:
    @pytest.mark.parametrize("value", [42, "a string", 3.5, True, None, {"a": 1}, [1, 2, 3]])
    def test_settings_round_trip_json_types(self, db, value):
        db.save_setting('key', value)

        assert db.get_setting('key') == value

    def test_missing_setting_returns_the_default(self, db):
        assert db.get_setting('nope') is None
        assert db.get_setting('nope', default='fallback') == 'fallback'

    def test_saving_the_same_key_overwrites(self, db):
        db.save_setting('theme', 'dark')
        db.save_setting('theme', 'light')

        assert db.get_setting('theme') == 'light'


class TestPersonalBests:
    def test_empty_database_reports_zero_with_no_dates(self, db):
        bests = db.get_personal_bests()

        for key in ('best_wpm', 'best_accuracy', 'best_efficiency', 'most_chars'):
            assert bests[key]['value'] == 0
            assert bests[key]['date'] is None

    def test_best_is_reported_with_the_date_it_was_achieved(self, db):
        insert_session_at(db, '2026-01-01T10:00:00', wpm=40.0)
        insert_session_at(db, '2026-06-15T10:00:00', wpm=95.0)
        insert_session_at(db, '2026-02-01T10:00:00', wpm=55.0)

        bests = db.get_personal_bests()

        assert bests['best_wpm']['value'] == 95.0
        assert bests['best_wpm']['date'] == '2026-06-15T10:00:00'


class TestImprovementMetrics:
    def test_fewer_than_two_sessions_yields_zeros(self, db):
        assert db.get_improvement_metrics()['wpm_improvement'] == 0

        db.save_session(make_stats())
        assert db.get_improvement_metrics()['wpm_improvement'] == 0

    def test_improvement_is_positive_when_later_sessions_are_faster(self, db):
        insert_session_at(db, '2026-01-01T10:00:00', wpm=30.0, accuracy=80.0)
        insert_session_at(db, '2026-02-01T10:00:00', wpm=70.0, accuracy=95.0)

        metrics = db.get_improvement_metrics()

        assert metrics['wpm_improvement'] == 40.0
        assert metrics['accuracy_improvement'] == 15.0

    def test_improvement_is_negative_when_performance_declines(self, db):
        insert_session_at(db, '2026-01-01T10:00:00', wpm=70.0)
        insert_session_at(db, '2026-02-01T10:00:00', wpm=30.0)

        assert db.get_improvement_metrics()['wpm_improvement'] == -40.0

    def test_consistency_score_stays_within_bounds(self, db):
        for i, wpm in enumerate([10.0, 90.0, 20.0, 80.0]):
            insert_session_at(db, f'2026-01-0{i + 1}T10:00:00', wpm=wpm)

        score = db.get_improvement_metrics()['consistency_score']

        assert 0 <= score <= 100


class TestPerformanceByLength:
    def test_empty_database_returns_no_buckets(self, db):
        assert db.get_performance_by_length() == []

    def test_sessions_group_into_one_bucket_per_length(self, db):
        insert_session_at(db, '2026-01-01T10:00:00', wpm=40.0, text_length=50)
        insert_session_at(db, '2026-01-02T10:00:00', wpm=60.0, text_length=50)
        insert_session_at(db, '2026-01-03T10:00:00', wpm=80.0, text_length=100)

        rows = db.get_performance_by_length()

        assert [r[0] for r in rows] == [50, 100], "buckets are ordered by length"
        assert rows[0][1] == 50.0, "average WPM within the 50-word bucket"
        assert rows[0][2] == 60.0, "best WPM within the 50-word bucket"
        assert rows[0][5] == 2, "two sessions in the 50-word bucket"


class TestStreaks:
    def test_empty_database_reports_no_streak(self, db):
        assert db.get_streak_info() == {'current_streak': 0, 'longest_streak': 0}

    def test_a_session_today_starts_a_streak(self, db):
        db.save_session(make_stats())

        db.update_streaks()

        assert db.get_streak_info()['current_streak'] == 1

    def test_no_sessions_means_no_streak(self, db):
        db.update_streaks()

        assert db.get_streak_info()['current_streak'] == 0

    def test_updating_twice_in_one_day_does_not_create_duplicate_rows(self, db):
        db.save_session(make_stats())

        db.update_streaks()
        db.update_streaks()

        with sqlite3.connect(db.db_path) as conn:
            rows = conn.execute('SELECT COUNT(*) FROM streaks').fetchone()[0]
        assert rows == 1, "one row per day; streaks.date has no UNIQUE constraint so OR REPLACE cannot replace"

    def test_consecutive_days_report_a_two_day_streak(self, db):
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        insert_session_at(db, yesterday)
        insert_session_at(db, datetime.now().isoformat())

        db.update_streaks()
        db.update_streaks()

        assert db.get_streak_info()['current_streak'] == 2

    def test_three_consecutive_days_build_a_three_day_streak(self, db):
        for offset in (2, 1, 0):
            insert_session_at(db, (datetime.now() - timedelta(days=offset)).isoformat())

        db.update_streaks()

        assert db.get_streak_info()['current_streak'] == 3

    def test_a_missed_day_breaks_the_current_streak_but_not_the_longest(self, db):
        for offset in (5, 4, 3):
            insert_session_at(db, (datetime.now() - timedelta(days=offset)).isoformat())
        insert_session_at(db, datetime.now().isoformat())

        db.update_streaks()
        info = db.get_streak_info()

        assert info['current_streak'] == 1, "the three-day run is not consecutive with today"
        assert info['longest_streak'] == 3, "the earlier run is still the longest"

    def test_update_streaks_is_idempotent(self, db):
        for offset in (1, 0):
            insert_session_at(db, (datetime.now() - timedelta(days=offset)).isoformat())

        for _ in range(5):
            db.update_streaks()

        assert db.get_streak_info()['current_streak'] == 2, "repeat calls must not inflate the streak"
        with sqlite3.connect(db.db_path) as conn:
            assert conn.execute('SELECT COUNT(*) FROM streaks').fetchone()[0] == 1

    def test_streak_spans_a_month_boundary(self, db, monkeypatch):
        from fingerpunch import data_manager

        frozen = datetime(2026, 3, 1, 12, 0, 0)

        class FrozenDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return frozen

        monkeypatch.setattr(data_manager, 'datetime', FrozenDateTime)

        insert_session_at(db, datetime(2026, 2, 27, 10, 0, 0).isoformat())
        insert_session_at(db, datetime(2026, 2, 28, 10, 0, 0).isoformat())
        insert_session_at(db, frozen.isoformat())

        db.update_streaks()

        assert db.get_streak_info()['current_streak'] == 3, "Feb 27, Feb 28 and Mar 1 are consecutive"


class TestExportImport:
    def test_exported_data_can_be_imported_into_a_fresh_database(self, db, tmp_path):
        db.save_session(make_stats(wpm=55.0), 'hello')
        db.save_session(make_stats(wpm=65.0), 'world')
        export_path = tmp_path / 'export.json'

        db.export_data(str(export_path))
        restored = DataManager(db_path=str(tmp_path / 'restored.db'))
        restored.import_data(str(export_path))

        assert sorted(s[2] for s in restored.get_all_sessions()) == [55.0, 65.0]

    def test_export_writes_readable_json(self, db, tmp_path):
        db.save_session(make_stats())
        export_path = tmp_path / 'export.json'

        db.export_data(str(export_path))

        payload = json.loads(export_path.read_text())
        assert payload['stats']['total_sessions'] == 1
        assert len(payload['sessions']) == 1


class TestProgressInsights:
    def test_empty_database_produces_no_insights(self, db):
        insights = db.get_progress_insights()

        assert insights['insights'] == []
        assert insights['stats']['total_sessions'] == 0

    def test_session_count_is_reported(self, db):
        db.save_session(make_stats())

        insights = db.get_progress_insights()

        assert any('1 typing sessions' in line for line in insights['insights'])

    def test_century_club_is_awarded_at_100_wpm(self, db):
        insert_session_at(db, '2026-01-01T10:00:00', wpm=105.0)

        insights = db.get_progress_insights()

        assert any('Century Club' in line for line in insights['insights'])


class TestSchemaResilience:
    def test_initialising_an_existing_database_is_safe(self, tmp_path):
        path = str(tmp_path / 'reopen.db')
        first = DataManager(db_path=path)
        first.save_session(make_stats(wpm=44.0))

        second = DataManager(db_path=path)

        assert len(second.get_all_sessions()) == 1
        assert second.get_all_sessions()[0][2] == 44.0
