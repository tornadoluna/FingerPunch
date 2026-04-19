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
