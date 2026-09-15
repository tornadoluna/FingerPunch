import json
import sqlite3
from datetime import datetime


class DataManager:
    def __init__(self, db_path="typingStats.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database and create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
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

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')


            cursor.execute('''
                CREATE TABLE IF NOT EXISTS streaks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    sessions_count INTEGER DEFAULT 0,
                    current_streak INTEGER DEFAULT 0,
                    longest_streak INTEGER DEFAULT 0
                )
            ''')

            conn.commit()

    def save_session(self, stats, sample_text=""):
        """Save a typing session to the database."""
        with sqlite3.connect(self.db_path) as conn:
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

    def get_all_sessions(self, limit=None):
        """Get all sessions ordered by date descending."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if limit:
                cursor.execute('SELECT * FROM sessions ORDER BY date DESC LIMIT ?', (limit,))
            else:
                cursor.execute('SELECT * FROM sessions ORDER BY date DESC')
            return cursor.fetchall()

    def delete_session(self, session_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_session_stats(self):
        """Get aggregate statistics across all sessions."""
        with sqlite3.connect(self.db_path) as conn:
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

    def save_setting(self, key, value):
        """Save a user setting."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                         (key, json.dumps(value)))
            conn.commit()

    def get_setting(self, key, default=None):
        """Get a user setting."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return default

    def export_data(self, filepath):
        """Export all data to a JSON file."""
        data = {
            'sessions': self.get_all_sessions(),
            'stats': self.get_session_stats()
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def import_data(self, filepath):
        """Import data from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for session in data.get('sessions', []):
                cursor.execute('''
                    INSERT OR IGNORE INTO sessions
                    (date, wpm, accuracy, time_taken, total_chars, keystrokes, efficiency, text_length, sample_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', session[1:])  # Skip id
            conn.commit()

    def get_performance_by_length(self):
        """Get average performance grouped by text length."""
        with sqlite3.connect(self.db_path) as conn:
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
            return cursor.fetchall()

    def get_personal_bests(self):
        """Get personal best performances."""
        with sqlite3.connect(self.db_path) as conn:
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

    def get_improvement_metrics(self):
        """Calculate improvement metrics over time."""
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

    def update_streaks(self):
        """Update daily streak information."""
        from datetime import date, timedelta

        with sqlite3.connect(self.db_path) as conn:
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

    def get_streak_info(self):
        """Get current streak information."""
        with sqlite3.connect(self.db_path) as conn:
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

    def get_streak_history(self, days=30):
        """Get streak history for the last N days."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT date, sessions_count, current_streak, MAX(id)
                FROM streaks
                WHERE date >= date('now', '-{days} days')
                GROUP BY date
                ORDER BY date
            ''')
            return [row[:3] for row in cursor.fetchall()]

