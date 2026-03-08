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
        self.total_typed_chars = 0
        self.correct_typed_chars = 0
        self.app.text_updated.connect(self.receive_text)

    def run(self):
        while self.running:
            self.request_text.emit()
            self.msleep(100)  # Update stats every 100ms

    def receive_text(self, text):
        self.current_text = text

        # Track new characters typed
        prev_len = len(self.previous_text)
        current_len = len(self.current_text)

        if current_len > prev_len:
            # Characters were added
            for i in range(prev_len, current_len):
                self.total_typed_chars += 1
                if i < len(self.app.sample_text) and self.current_text[i] == self.app.sample_text[i]:
                    self.correct_typed_chars += 1

        # Calculate accuracy based on session statistics (penalizes mistakes even if corrected)
        accuracy = (self.correct_typed_chars / self.total_typed_chars * 100) if self.total_typed_chars > 0 else 0

        if self.app.start_time:
            elapsed = time.time() - self.app.start_time
            wpm = (self.correct_typed_chars / 5) / (elapsed / 60) if elapsed > 0 else 0
            self.stats_updated.emit(f"{wpm:.2f}", f"{accuracy:.2f}%")

        self.previous_text = self.current_text

    def reset_stats(self):
        self.total_typed_chars = 0
        self.correct_typed_chars = 0
        self.previous_text = ""
        self.current_text = ""

    def stop_worker(self):
        self.running = False
        self.wait()
