from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, NamedTuple, TypedDict

from fingerpunch.paths import default_database_path

logger = logging.getLogger(__name__)


class StorageError(RuntimeError):
    pass


class Session(NamedTuple):
    id: int
    date: str
    wpm: float
    accuracy: float
    time_taken: float
    total_chars: int
    keystrokes: int
    efficiency: float
    text_length: int
    sample_text: str


class SessionStats(TypedDict):
    total_sessions: int
    avg_wpm: float
    best_wpm: float
    avg_accuracy: float
    best_accuracy: float
    total_time: float


class PersonalBest(TypedDict):
    value: float
    date: str | None


class PersonalBests(TypedDict):
    best_wpm: PersonalBest
    best_accuracy: PersonalBest
    best_efficiency: PersonalBest
    most_chars: PersonalBest


class ImprovementMetrics(TypedDict):
    wpm_improvement: float
    accuracy_improvement: float
    consistency_score: float
    total_improvement: float


class StreakInfo(TypedDict):
    current_streak: int
    longest_streak: int


class LengthPerformance(NamedTuple):
    text_length: int
    avg_wpm: float
    best_wpm: float
    avg_accuracy: float
    best_accuracy: float
    test_count: int


class StreakDay(NamedTuple):
    date: str
    sessions_count: int
    current_streak: int


def _migration_1_initial_schema(conn: sqlite3.Connection) -> None:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            wpm REAL NOT NULL,
            accuracy REAL NOT NULL,
            time_taken REAL NOT NULL,
            total_chars INTEGER NOT NULL,
            keystrokes INTEGER NOT NULL,
            efficiency REAL NOT NULL,
            text_length INTEGER NOT NULL,
            sample_text TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            sessions_count INTEGER DEFAULT 0,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0
        )
    ''')


def _migration_2_one_streak_row_per_day(conn: sqlite3.Connection) -> None:
    conn.execute('''
        DELETE FROM streaks
        WHERE id NOT IN (SELECT MAX(id) FROM streaks GROUP BY date)
    ''')
    conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_streaks_date ON streaks(date)')


MIGRATIONS = [
    _migration_1_initial_schema,
    _migration_2_one_streak_row_per_day,
]
SCHEMA_VERSION = len(MIGRATIONS)


class DataManager:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = str(db_path) if db_path is not None else str(default_database_path())
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            logger.exception("Could not create the database directory for %s", self.db_path)
            raise StorageError(f"Could not create the database directory: {error}") from error
        self.init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = None
        try:
            connection = sqlite3.connect(self.db_path)
            with connection:
                yield connection
        except sqlite3.Error as error:
            logger.exception("Database operation failed on %s", self.db_path)
            raise StorageError(str(error)) from error
        finally:
            if connection is not None:
                connection.close()

    def init_db(self) -> None:
        with self._connect() as conn:
            applied = conn.execute('PRAGMA user_version').fetchone()[0]
            for index in range(applied, SCHEMA_VERSION):
                MIGRATIONS[index](conn)
                conn.execute(f'PRAGMA user_version = {index + 1:d}')
            conn.commit()

    def schema_version(self) -> int:
        with self._connect() as conn:
            return conn.execute('PRAGMA user_version').fetchone()[0]

    def save_session(self, stats: dict[str, Any], sample_text: str = "") -> None:
        """Stores only the first 200 characters of sample_text."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (date, wpm, accuracy, time_taken, total_chars, keystrokes, efficiency, text_length, sample_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                stats['wpm'],
                stats['accuracy'],
                stats['time'],
                stats['total_chars'],
                stats['keystrokes'],
                stats['efficiency'],
                len(sample_text),
                sample_text[:200]  # Store first 200 chars of sample text
            ))
            conn.commit()

    def get_all_sessions(self, limit: int | None = None) -> list[Session]:
        with self._connect() as conn:
            cursor = conn.cursor()
            if limit:
                cursor.execute(
                    'SELECT id, date, wpm, accuracy, time_taken, total_chars, keystrokes,'
                    ' efficiency, text_length, sample_text'
                    ' FROM sessions ORDER BY date DESC LIMIT ?',
                    (limit,),
                )
            else:
                cursor.execute(
                    'SELECT id, date, wpm, accuracy, time_taken, total_chars, keystrokes,'
                    ' efficiency, text_length, sample_text'
                    ' FROM sessions ORDER BY date DESC'
                )
            return [Session(*row) for row in cursor.fetchall()]

    def delete_session(self, session_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_session_stats(self) -> SessionStats:
        with self._connect() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM sessions')
            total_sessions = cursor.fetchone()[0]

            if total_sessions == 0:
                return {
                    'total_sessions': 0,
                    'avg_wpm': 0,
                    'best_wpm': 0,
                    'avg_accuracy': 0,
                    'best_accuracy': 0,
                    'total_time': 0
                }

            cursor.execute('''
                SELECT
                    AVG(wpm), MAX(wpm),
                    AVG(accuracy), MAX(accuracy),
                    SUM(time_taken)
                FROM sessions
            ''')
            avg_wpm, best_wpm, avg_accuracy, best_accuracy, total_time = cursor.fetchone()

            return {
                'total_sessions': total_sessions,
                'avg_wpm': round(avg_wpm, 1),
                'best_wpm': round(best_wpm, 1),
                'avg_accuracy': round(avg_accuracy, 1),
                'best_accuracy': round(best_accuracy, 1),
                'total_time': round(total_time, 1)
            }

    def save_setting(self, key: str, value: Any) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                         (key, json.dumps(value)))
            conn.commit()

    def get_setting(self, key: str, default: Any = None) -> Any:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return default

    def export_data(self, filepath: str | Path) -> None:
        data = {
            'sessions': self.get_all_sessions(),
            'stats': self.get_session_stats()
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def import_data(self, filepath: str | Path) -> None:
        """Rows are inserted with fresh ids; existing rows are left untouched."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        with self._connect() as conn:
            cursor = conn.cursor()
            for row in data.get('sessions', []):
                session = Session(*row[:len(Session._fields)])
                cursor.execute('''
                    INSERT OR IGNORE INTO sessions
                    (date, wpm, accuracy, time_taken, total_chars, keystrokes, efficiency, text_length, sample_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.date,
                    session.wpm,
                    session.accuracy,
                    session.time_taken,
                    session.total_chars,
                    session.keystrokes,
                    session.efficiency,
                    session.text_length,
                    session.sample_text,
                ))
            conn.commit()

    def get_performance_by_length(self) -> list[LengthPerformance]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT text_length,
                       AVG(wpm) as avg_wpm,
                       MAX(wpm) as best_wpm,
                       AVG(accuracy) as avg_accuracy,
                       MAX(accuracy) as best_accuracy,
                       COUNT(*) as test_count
                FROM sessions
                GROUP BY text_length
                ORDER BY text_length
            ''')
            return [LengthPerformance(*row) for row in cursor.fetchall()]

    def get_personal_bests(self) -> PersonalBests:
        """Always returns all four keys, with a value of 0 and no date when unset."""
        with self._connect() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT MAX(wpm), date FROM sessions')
            best_wpm_result = cursor.fetchone()

            cursor.execute('SELECT MAX(accuracy), date FROM sessions')
            best_accuracy_result = cursor.fetchone()

            cursor.execute('SELECT MAX(efficiency), date FROM sessions')
            best_efficiency_result = cursor.fetchone()

            cursor.execute('SELECT MAX(total_chars), date FROM sessions')
            most_chars_result = cursor.fetchone()

            return {
                'best_wpm': {'value': best_wpm_result[0] if best_wpm_result[0] else 0, 'date': best_wpm_result[1] if best_wpm_result[1] else None},
                'best_accuracy': {'value': best_accuracy_result[0] if best_accuracy_result[0] else 0, 'date': best_accuracy_result[1] if best_accuracy_result[1] else None},
                'best_efficiency': {'value': best_efficiency_result[0] if best_efficiency_result[0] else 0, 'date': best_efficiency_result[1] if best_efficiency_result[1] else None},
                'most_chars': {'value': most_chars_result[0] if most_chars_result[0] else 0, 'date': most_chars_result[1] if most_chars_result[1] else None}
            }

    def get_improvement_metrics(self) -> ImprovementMetrics:
        sessions = self.get_all_sessions()
        if len(sessions) < 2:
            return {
                'wpm_improvement': 0,
                'accuracy_improvement': 0,
                'consistency_score': 0,
                'total_improvement': 0
            }

        sessions_sorted = sorted(sessions, key=lambda x: x[1])

        first_sessions = sessions_sorted[:min(10, len(sessions_sorted)//2)]
        last_sessions = sessions_sorted[-min(10, len(sessions_sorted)//2):]

        if not first_sessions or not last_sessions:
            return {
                'wpm_improvement': 0,
                'accuracy_improvement': 0,
                'consistency_score': 0,
                'total_improvement': 0
            }

        first_avg_wpm = sum(s[2] for s in first_sessions) / len(first_sessions)
        last_avg_wpm = sum(s[2] for s in last_sessions) / len(last_sessions)
        first_avg_accuracy = sum(s[3] for s in first_sessions) / len(first_sessions)
        last_avg_accuracy = sum(s[3] for s in last_sessions) / len(last_sessions)

        wpm_improvement = last_avg_wpm - first_avg_wpm
        accuracy_improvement = last_avg_accuracy - first_avg_accuracy

        all_wpms = [s[2] for s in sessions_sorted[-20:]]  # Last 20 sessions
        if len(all_wpms) > 1:
            wpm_mean = sum(all_wpms) / len(all_wpms)
            wpm_variance = sum((x - wpm_mean) ** 2 for x in all_wpms) / len(all_wpms)
            consistency_score = max(0, 100 - (wpm_variance ** 0.5))  # Convert to 0-100 scale
        else:
            consistency_score = 0

        total_improvement = (wpm_improvement * 0.7) + (accuracy_improvement * 0.3)

        return {
            'wpm_improvement': round(wpm_improvement, 1),
            'accuracy_improvement': round(accuracy_improvement, 1),
            'consistency_score': round(consistency_score, 1),
            'total_improvement': round(total_improvement, 1)
        }

    def update_streaks(self) -> None:
        """Derived from the distinct session dates, so it is idempotent and repairs bad rows."""
        with self._connect() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT DISTINCT DATE(date) FROM sessions')
            active_days = {date.fromisoformat(row[0]) for row in cursor.fetchall() if row[0]}

            today = datetime.now().date()
            cursor.execute('SELECT COUNT(*) FROM sessions WHERE DATE(date) = ?', (today.isoformat(),))
            today_sessions = cursor.fetchone()[0]

            current_streak = 0
            day = today
            while day in active_days:
                current_streak += 1
                day -= timedelta(days=1)

            longest_streak = 0
            run = 0
            previous = None
            for day in sorted(active_days):
                run = run + 1 if previous is not None and day - previous == timedelta(days=1) else 1
                longest_streak = max(longest_streak, run)
                previous = day

            cursor.execute(
                'SELECT id FROM streaks WHERE date = ? ORDER BY id DESC LIMIT 1',
                (today.isoformat(),),
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    'UPDATE streaks SET sessions_count = ?, current_streak = ?, longest_streak = ?'
                    ' WHERE date = ?',
                    (today_sessions, current_streak, longest_streak, today.isoformat()),
                )
            else:
                cursor.execute(
                    'INSERT INTO streaks (date, sessions_count, current_streak, longest_streak)'
                    ' VALUES (?, ?, ?, ?)',
                    (today.isoformat(), today_sessions, current_streak, longest_streak),
                )

            conn.commit()

    def get_streak_info(self) -> StreakInfo:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT current_streak, longest_streak FROM streaks ORDER BY date DESC, id DESC LIMIT 1'
            )
            result = cursor.fetchone()

            if result:
                current_streak, longest_streak = result
                return {
                    'current_streak': current_streak,
                    'longest_streak': longest_streak
                }
            else:
                return {
                    'current_streak': 0,
                    'longest_streak': 0
                }

    def get_streak_history(self, days: int = 30) -> list[StreakDay]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now().date() - timedelta(days=days)).isoformat()
            cursor.execute(
                'SELECT date, sessions_count, current_streak FROM streaks'
                ' WHERE date >= ? ORDER BY date',
                (cutoff,),
            )
            return [StreakDay(*row) for row in cursor.fetchall()]

