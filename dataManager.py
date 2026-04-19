import sqlite3
import os
from datetime import datetime
import json

class DataManager:
    def __init__(self, db_path="typingStats.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database and create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create sessions table
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

            # Create settings table for user preferences
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
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

    def get_sessions_by_date_range(self, start_date, end_date):
        """Get sessions within a date range."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sessions WHERE date >= ? AND date <= ? ORDER BY date DESC',
                         (start_date, end_date))
            return cursor.fetchall()

    def get_session_stats(self):
        """Get aggregate statistics across all sessions."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get total sessions
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

            # Get averages and bests
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

    def get_recent_sessions(self, days=30):
        """Get sessions from the last N days."""
        from datetime import datetime, timedelta
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        return self.get_sessions_by_date_range(start_date, datetime.now().isoformat())

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

    def get_daily_activity(self, days=30):
        """Get daily test activity for the last N days."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DATE(date) as day, COUNT(*) as tests
                FROM sessions
                WHERE date >= date('now', '-{} days')
                GROUP BY DATE(date)
                ORDER BY day
            '''.format(days))
            return cursor.fetchall()

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

            # Best WPM
            cursor.execute('SELECT MAX(wpm), date FROM sessions')
            best_wpm_result = cursor.fetchone()

            # Best accuracy
            cursor.execute('SELECT MAX(accuracy), date FROM sessions')
            best_accuracy_result = cursor.fetchone()

            # Best efficiency
            cursor.execute('SELECT MAX(efficiency), date FROM sessions')
            best_efficiency_result = cursor.fetchone()

            # Most characters typed
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

        # Sort by date (oldest first)
        sessions_sorted = sorted(sessions, key=lambda x: x[1])

        # Get first and last 10 sessions for comparison
        first_sessions = sessions_sorted[:min(10, len(sessions_sorted)//2)]
        last_sessions = sessions_sorted[-min(10, len(sessions_sorted)//2):]

        if not first_sessions or not last_sessions:
            return {
                'wpm_improvement': 0,
                'accuracy_improvement': 0,
                'consistency_score': 0,
                'total_improvement': 0
            }

        # Calculate averages
        first_avg_wpm = sum(s[2] for s in first_sessions) / len(first_sessions)
        last_avg_wpm = sum(s[2] for s in last_sessions) / len(last_sessions)
        first_avg_accuracy = sum(s[3] for s in first_sessions) / len(first_sessions)
        last_avg_accuracy = sum(s[3] for s in last_sessions) / len(last_sessions)

        wpm_improvement = last_avg_wpm - first_avg_wpm
        accuracy_improvement = last_avg_accuracy - first_avg_accuracy

        # Calculate consistency (lower standard deviation = more consistent)
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

    def get_time_based_stats(self, period='daily'):
        """Get statistics grouped by time period."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if period == 'daily':
                group_by = "DATE(date)"
            elif period == 'weekly':
                group_by = "strftime('%Y-%W', date)"
            elif period == 'monthly':
                group_by = "strftime('%Y-%m', date)"
            else:
                group_by = "DATE(date)"

            cursor.execute(f'''
                SELECT {group_by} as period,
                       AVG(wpm) as avg_wpm,
                       MAX(wpm) as max_wpm,
                       AVG(accuracy) as avg_accuracy,
                       COUNT(*) as test_count
                FROM sessions
                GROUP BY {group_by}
                ORDER BY period
            ''')

            return cursor.fetchall()

    def get_recent_performance_trend(self, days=7):
        """Get recent performance trend for the last N days."""
        sessions = self.get_recent_sessions(days)
        if not sessions:
            return []

        # Group by day and calculate daily averages
        from collections import defaultdict
        daily_stats = defaultdict(list)

        for session in sessions:
            date = session[1][:10]  # Get date part only
            daily_stats[date].append(session)

        trend_data = []
        for date in sorted(daily_stats.keys()):
            day_sessions = daily_stats[date]
            avg_wpm = sum(s[2] for s in day_sessions) / len(day_sessions)
            avg_accuracy = sum(s[3] for s in day_sessions) / len(day_sessions)
            test_count = len(day_sessions)

            trend_data.append({
                'date': date,
                'avg_wpm': round(avg_wpm, 1),
                'avg_accuracy': round(avg_accuracy, 1),
                'test_count': test_count
            })

        return trend_data
