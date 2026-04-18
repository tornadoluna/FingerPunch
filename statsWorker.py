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
        self.deletions = 0
        self.additions = 0
        self.app.text_updated.connect(self.receive_text)

    def run(self):
        while self.running:
            self.request_text.emit()
            self.msleep(100)

    def receive_text(self, text):
        self.current_text = text
        self._update_keystroke_stats()

    def _update_keystroke_stats(self):

        prev_len = len(self.previous_text)
        current_len = len(self.current_text)

        if prev_len == current_len:
            if self.previous_text != self.current_text:
                for i in range(current_len):
                    if i < len(self.previous_text) and self.current_text[i] != self.previous_text[i]:
                        self.total_keystrokes += 2
        elif current_len > prev_len:
            chars_added = current_len - prev_len
            self.additions += chars_added
            self.total_keystrokes += chars_added
        else:
            chars_deleted = prev_len - current_len
            self.deletions += chars_deleted
            self.total_keystrokes += chars_deleted

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
        self.deletions = 0
        self.additions = 0
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
            'total_chars': typed_length,
            'keystrokes': self.total_keystrokes,
            'efficiency': (correct_chars / self.total_keystrokes * 100) if self.total_keystrokes > 0 else 100.0
        }
