from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QGroupBox
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QFont
import time
from statsWorker import StatsWorker
from textGenerator import generate_mixed_text

class TypingPracticeApp(QWidget):
    stats_updated = Signal(str, str, str)
    text_updated = Signal(str)

    def __init__(self):
        super().__init__()
        self.sample_text = generate_mixed_text(length=250)
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
        self.setGeometry(100, 100, 800, 500)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        sample_group = QGroupBox("Sample Text")
        sample_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        sample_layout = QVBoxLayout()
        self.text_label = QLabel(self.sample_text)
        self.text_label.setWordWrap(True)
        self.text_label.setFont(QFont("Arial", 14))
        self.text_label.setStyleSheet("padding: 10px; color: #000000; background-color: #ffffff;")
        sample_layout.addWidget(self.text_label)
        sample_group.setLayout(sample_layout)
        main_layout.addWidget(sample_group)

        input_group = QGroupBox("Your Typing")
        input_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        input_layout = QVBoxLayout()
        self.input_edit = QTextEdit()
        self.input_edit.setFont(QFont("Arial", 14))
        self.input_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #aaaaaa;
                border-radius: 3px;
                padding: 10px;
                background-color: #ffffff;
                color: #000000;
            }
            QTextEdit:focus {
                border: 2px solid #4a90e2;
            }
        """)
        self.input_edit.setMinimumHeight(120)
        self.input_edit.textChanged.connect(self.check_progress)
        input_layout.addWidget(self.input_edit)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        control_group = QGroupBox("Statistics And Controls")
        control_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        control_layout = QVBoxLayout()

        self.stats_label = QLabel("WPM: 0 | Accuracy: 0% | Time: 0s")
        self.stats_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.stats_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #e8f4fd;
                border-radius: 3px;
                border: 1px solid #4a90e2;
                color: #000000;
            }
        """)
        control_layout.addWidget(self.stats_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.start_button = QPushButton("Start")
        self.start_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.start_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)
        self.start_button.clicked.connect(self.start_practice)
        button_layout.addWidget(self.start_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.reset_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self.reset_button.clicked.connect(self.reset_practice)
        button_layout.addWidget(self.reset_button)

        self.new_text_button = QPushButton("New Text")
        self.new_text_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.new_text_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
        """)
        self.new_text_button.clicked.connect(self.load_new_sample_text)
        button_layout.addWidget(self.new_text_button)

        button_layout.addStretch()
        control_layout.addLayout(button_layout)

        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        self.setLayout(main_layout)

    def start_practice(self):
        if not self.start_time:
            self.start_time = time.time()
            self.timer.start(1000)
            self.input_edit.setFocus()

    def reset_practice(self):
        self.start_time = None
        self.elapsed_time = 0
        self.is_done = False
        self.stats_worker.reset_stats()
        self.timer.stop()
        self.input_edit.clear()
        self.stats_updated.emit("0", "0%", "0s")

    def load_new_sample_text(self):
        self.sample_text = generate_mixed_text(length=250)
        self.text_label.setText(self.sample_text)
        self.reset_practice()

    def update_time(self):
        if self.start_time:
            self.elapsed_time = time.time() - self.start_time
            self.stats_updated.emit(self.last_wpm, self.last_accuracy, f"{int(self.elapsed_time)}s")

    def check_progress(self):
        typed_text = self.input_edit.toPlainText()
        self.text_updated.emit(typed_text)

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
        self.stats_worker.stop_worker()
        super().closeEvent(event)
