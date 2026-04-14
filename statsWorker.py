from PySide6.QtCore import QThread, Signal
import time

class StatsWorker(QThread):
    stats_updated = Signal(str, str)
    request_text = Signal()

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.running = True
        self.current_text = ""
        self.previous_text = ""
        self.total_keystrokes = 0
        self.app.text_updated.connect(self.receive_text)

    def run(self):
        while self.running:
            self.request_text.emit()
            self.msleep(100)  # Update stats every 100ms

    def receive_text(self, text):
        self.current_text = text

        prev_len = len(self.previous_text)
        current_len = len(self.current_text)

        if current_len != prev_len:
            keystroke_diff = abs(current_len - prev_len)
            self.total_keystrokes += keystroke_diff

        typed_length = len(self.current_text)
        sample_length = len(self.app.sample_text)
        correct_chars = 0

        for i in range(min(typed_length, sample_length)):
            if self.current_text[i] == self.app.sample_text[i]:
                correct_chars += 1

        accuracy = (correct_chars / typed_length * 100) if typed_length > 0 else 100.0

        if self.app.start_time:
            elapsed = time.time() - self.app.start_time
            wpm = (correct_chars / 5) / (elapsed / 60) if elapsed > 0 else 0
            self.stats_updated.emit(f"{wpm:.2f}", f"{accuracy:.2f}%")

        self.previous_text = self.current_text

    def reset_stats(self):
        self.total_keystrokes = 0
        self.previous_text = ""
        self.current_text = ""

    def stop_worker(self):
        self.running = False
        self.wait()

    def get_final_stats(self):
        typed_length = len(self.current_text)
        sample_length = len(self.app.sample_text)
        correct_chars = 0

        for i in range(min(typed_length, sample_length)):
            if self.current_text[i] == self.app.sample_text[i]:
                correct_chars += 1

        accuracy = (correct_chars / typed_length * 100) if typed_length > 0 else 100.0

        if self.app.start_time:
            elapsed = time.time() - self.app.start_time
            wpm = (correct_chars / 5) / (elapsed / 60) if elapsed > 0 else 0
        else:
            elapsed = 0
            wpm = 0

        return {
            'wpm': wpm,
            'accuracy': accuracy,
            'time': elapsed,
            'correct_chars': correct_chars,
            'total_chars': typed_length,
            'keystrokes': self.total_keystrokes,
            'efficiency': (correct_chars / self.total_keystrokes * 100) if self.total_keystrokes > 0 else 100.0
        }
