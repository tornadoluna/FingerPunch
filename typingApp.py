from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QFont
import time
from statsWorker import StatsWorker

class TypingPracticeApp(QWidget):
    # Signal to update stats
    stats_updated = Signal(str, str, str)
    text_updated = Signal(str)

    def __init__(self):
        super().__init__()
        self.sample_text = "The quick brown fox jumps over the lazy dog. This is a sample text for typing practice."
        self.start_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.elapsed_time = 0
        self.is_done = False
        self.last_wpm = "0"
        self.last_accuracy = "0%"
        self.init_ui()
        self.stats_updated.connect(self.display_stats)

        self.stats_worker = StatsWorker(self)
        self.stats_worker.stats_updated.connect(self.update_stats)
        self.stats_worker.start()

    def init_ui(self):
        self.setWindowTitle("Typing Practice App")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        # Sample text display
        self.text_label = QLabel(self.sample_text)
        self.text_label.setWordWrap(True)
        self.text_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.text_label)

        # Input area
        self.input_edit = QTextEdit()
        self.input_edit.setFont(QFont("Arial", 12))
        self.input_edit.textChanged.connect(self.check_progress)
        layout.addWidget(self.input_edit)

        # Buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_practice)
        button_layout.addWidget(self.start_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_practice)
        button_layout.addWidget(self.reset_button)

        layout.addLayout(button_layout)

        # Stats display
        self.stats_label = QLabel("WPM: 0 | Accuracy: 0% | Time: 0s")
        layout.addWidget(self.stats_label)

        self.setLayout(layout)

    def start_practice(self):
        if not self.start_time:
            self.start_time = time.time()
            self.timer.start(1000)  # Update every second
            self.input_edit.setFocus()

    def reset_practice(self):
        self.start_time = None
        self.elapsed_time = 0
        self.is_done = False
        self.stats_worker.reset_stats()
        self.timer.stop()
        self.input_edit.clear()
        self.stats_updated.emit("0", "0%", "0s")

    def update_time(self):
        if self.start_time:
            self.elapsed_time = time.time() - self.start_time
            self.stats_updated.emit(self.last_wpm, self.last_accuracy, f"{int(self.elapsed_time)}s")

    def check_progress(self):
        typed_text = self.input_edit.toPlainText()
        self.text_updated.emit(typed_text)  # Emit signal with current text

        if not self.start_time and typed_text:
            self.start_time = time.time()
            self.timer.start(1000)

        if len(typed_text) == len(self.sample_text) and typed_text == self.sample_text:
            if not self.is_done:
                self.is_done = True
                self.timer.stop()

    def update_stats(self, wpm, accuracy):
        elapsed_time = time.time() - self.start_time
        self.last_wpm = wpm
        self.last_accuracy = accuracy
        self.stats_updated.emit(f"{wpm}", f"{accuracy}", f"{int(elapsed_time)}s")

    def display_stats(self, wpm, accuracy, time_str):
        self.stats_label.setText(f"WPM: {wpm} | Accuracy: {accuracy} | Time: {time_str}")

    def closeEvent(self, event):
        # Stop the stats worker thread on close
        self.stats_worker.stop_worker()
        super().closeEvent(event)
