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

            # Create goals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL, -- 'wpm', 'accuracy', 'sessions'
                    target_value REAL NOT NULL,
                    current_value REAL DEFAULT 0,
                    created_date TEXT NOT NULL,
                    target_date TEXT,
                    achieved BOOLEAN DEFAULT FALSE,
                    achieved_date TEXT
                )
            ''')

            # Create achievements table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    icon TEXT,
                    category TEXT,
                    requirement_type TEXT,
                    requirement_value REAL,
                    unlocked BOOLEAN DEFAULT FALSE,
                    unlocked_date TEXT,
                    progress REAL DEFAULT 0
                )
            ''')

            # Create streaks table
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

    # ===== GOALS MANAGEMENT =====

    def create_goal(self, goal_type, target_value, target_date=None):
        """Create a new goal."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO goals (type, target_value, created_date, target_date)
                VALUES (?, ?, ?, ?)
            ''', (goal_type, target_value, datetime.now().isoformat(), target_date))
            conn.commit()
            return cursor.lastrowid

    def get_goals(self):
        """Get all goals."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM goals ORDER BY created_date DESC')
            return cursor.fetchall()

    def update_goal_progress(self, goal_id, current_value):
        """Update goal progress and check if achieved."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT target_value, achieved FROM goals WHERE id = ?', (goal_id,))
            result = cursor.fetchone()

            if result:
                target_value, achieved = result
                if not achieved and current_value >= target_value:
                    cursor.execute('''
                        UPDATE goals 
                        SET current_value = ?, achieved = TRUE, achieved_date = ?
                        WHERE id = ?
                    ''', (current_value, datetime.now().isoformat(), goal_id))
                else:
                    cursor.execute('UPDATE goals SET current_value = ? WHERE id = ?', (current_value, goal_id))
                conn.commit()

    def delete_goal(self, goal_id):
        """Delete a goal."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
            conn.commit()

    # ===== ACHIEVEMENTS SYSTEM =====

    def init_achievements(self):
        """Initialize default achievements."""
        achievements = [
            # Beginner achievements
            ("First Steps", "Complete your first typing session", "🎯", "beginner", "sessions", 1),
            ("Getting Started", "Complete 10 typing sessions", "🚀", "beginner", "sessions", 10),
            ("Century Club", "Reach 100 WPM", "💯", "speed", "wpm", 100),
            ("Accuracy Master", "Achieve 98% accuracy", "🎯", "accuracy", "accuracy", 98),

            # Speed achievements
            ("Speed Demon", "Reach 120 WPM", "⚡", "speed", "wpm", 120),
            ("Lightning Fast", "Reach 150 WPM", "⚡", "speed", "wpm", 150),
            ("Typing God", "Reach 200 WPM", "👑", "speed", "wpm", 200),

            # Consistency achievements
            ("Consistent", "Complete sessions for 7 consecutive days", "🔥", "consistency", "streak", 7),
            ("Dedicated", "Complete sessions for 30 consecutive days", "🔥", "consistency", "streak", 30),
            ("Unstoppable", "Complete sessions for 100 consecutive days", "🔥", "consistency", "streak", 100),

            # Volume achievements
            ("Century Sessions", "Complete 100 typing sessions", "📊", "volume", "sessions", 100),
            ("Half Thousand", "Complete 500 typing sessions", "📊", "volume", "sessions", 500),
            ("Thousand Club", "Complete 1000 typing sessions", "📊", "volume", "sessions", 1000),

            # Time achievements
            ("Hour of Practice", "Spend 1 hour total practicing", "⏰", "time", "total_time", 3600),
            ("Practice Veteran", "Spend 10 hours total practicing", "⏰", "time", "total_time", 36000),
            ("Time Master", "Spend 100 hours total practicing", "⏰", "time", "total_time", 360000),
        ]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for name, desc, icon, category, req_type, req_value in achievements:
                cursor.execute('''
                    INSERT OR IGNORE INTO achievements 
                    (name, description, icon, category, requirement_type, requirement_value)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, desc, icon, category, req_type, req_value))
            conn.commit()

    def check_achievements(self):
        """Check and update achievement progress."""
        stats = self.get_session_stats()
        bests = self.get_personal_bests()
        streaks = self.get_streak_info()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get all achievements
            cursor.execute('SELECT * FROM achievements')
            achievements = cursor.fetchall()

            for achievement in achievements:
                ach_id, name, desc, icon, category, req_type, req_value, unlocked, unlocked_date, progress = achievement

                if unlocked:
                    continue

                # Check requirement based on type
                achieved = False
                new_progress = 0

                if req_type == "sessions":
                    new_progress = stats['total_sessions']
                    achieved = new_progress >= req_value
                elif req_type == "wpm":
                    new_progress = bests['best_wpm']['value']
                    achieved = new_progress >= req_value
                elif req_type == "accuracy":
                    new_progress = bests['best_accuracy']['value']
                    achieved = new_progress >= req_value
                elif req_type == "streak":
                    new_progress = streaks['longest_streak']
                    achieved = new_progress >= req_value
                elif req_type == "total_time":
                    new_progress = stats['total_time']
                    achieved = new_progress >= req_value

                # Update achievement
                if achieved and not unlocked:
                    cursor.execute('''
                        UPDATE achievements 
                        SET unlocked = TRUE, unlocked_date = ?, progress = ?
                        WHERE id = ?
                    ''', (datetime.now().isoformat(), new_progress, ach_id))
                elif new_progress > progress:
                    cursor.execute('UPDATE achievements SET progress = ? WHERE id = ?', (new_progress, ach_id))

            conn.commit()

    def get_achievements(self):
        """Get all achievements with progress."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM achievements ORDER BY category, requirement_value')
            return cursor.fetchall()

    # ===== STREAK TRACKING =====

    def update_streaks(self):
        """Update daily streak information."""
        today = datetime.now().date().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get today's sessions count
            cursor.execute('SELECT COUNT(*) FROM sessions WHERE DATE(date) = ?', (today,))
            today_sessions = cursor.fetchone()[0]

            # Get yesterday's date
            yesterday = (datetime.now().date().replace(day=datetime.now().day-1)).isoformat()
            cursor.execute('SELECT COUNT(*) FROM sessions WHERE DATE(date) = ?', (yesterday,))
            yesterday_sessions = cursor.fetchone()[0]

            # Get current streak info
            cursor.execute('SELECT current_streak, longest_streak FROM streaks ORDER BY date DESC LIMIT 1')
            streak_result = cursor.fetchone()

            current_streak = 1 if today_sessions > 0 else 0
            longest_streak = current_streak

            if streak_result:
                prev_current, prev_longest = streak_result
                if yesterday_sessions > 0 and today_sessions > 0:
                    current_streak = prev_current + 1
                elif today_sessions == 0:
                    current_streak = 0
                longest_streak = max(prev_longest, current_streak)

            # Insert/update today's streak
            cursor.execute('''
                INSERT OR REPLACE INTO streaks (date, sessions_count, current_streak, longest_streak)
                VALUES (?, ?, ?, ?)
            ''', (today, today_sessions, current_streak, longest_streak))

            conn.commit()

    def get_streak_info(self):
        """Get current streak information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT current_streak, longest_streak FROM streaks ORDER BY date DESC LIMIT 1')
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
            cursor.execute('''
                SELECT date, sessions_count, current_streak 
                FROM streaks 
                WHERE date >= date('now', '-{} days')
                ORDER BY date
            '''.format(days))
            return cursor.fetchall()

    # ===== PROGRESS INSIGHTS =====

    def get_progress_insights(self):
        """Generate comprehensive progress insights."""
        stats = self.get_session_stats()
        bests = self.get_personal_bests()
        improvements = self.get_improvement_metrics()
        streaks = self.get_streak_info()

        insights = {
            'stats': stats,
            'bests': bests,
            'improvements': improvements,
            'streaks': streaks,
            'insights': []
        }

        # Generate insights based on data
        if stats['total_sessions'] > 0:
            insights['insights'].append(f"You've completed {stats['total_sessions']} typing sessions!")

            if improvements['wpm_improvement'] > 0:
                insights['insights'].append(f"Your WPM has improved by {improvements['wpm_improvement']} over time!")
            elif improvements['wpm_improvement'] < 0:
                insights['insights'].append(f"Your WPM has decreased by {abs(improvements['wpm_improvement'])}. Keep practicing!")

            if bests['best_wpm']['value'] >= 100:
                insights['insights'].append("🏆 You're in the Century Club (100+ WPM)!")

            if improvements['consistency_score'] > 80:
                insights['insights'].append("🎯 You're very consistent in your typing speed!")

            if streaks['current_streak'] >= 7:
                insights['insights'].append(f"🔥 You're on a {streaks['current_streak']}-day streak!")

            if streaks['longest_streak'] >= 30:
                insights['insights'].append(f"💪 Your longest streak is {streaks['longest_streak']} days!")

        return insights
