from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QGroupBox, QProgressBar, QComboBox, QSizePolicy
from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QStyle
import time
from statsWorker import StatsWorker
from textGenerator import generate_mixed_text

class TypingPracticeApp(QWidget):
    stats_updated = Signal(str, str, str)
    text_updated = Signal(str)

    def __init__(self):
        super().__init__()
        self.text_length = 50
        self.sample_text = generate_mixed_text(length=50)
        self.start_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.elapsed_time = 0
        self.is_done = False
        self.last_wpm = "0"
        self.last_accuracy = "0%"
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        self.init_ui()
        self.stats_updated.connect(self.display_stats)

        self.stats_worker = StatsWorker(self)
        self.stats_worker.stats_updated.connect(self.update_stats)
        self.stats_worker.start()

    def init_ui(self):
        self.setWindowTitle("FingerPunch")
        self.resize(900, 600)
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(25, 25, 25, 25)

        sample_group = QGroupBox("Sample Text")
        sample_group.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        sample_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 1ex;
                background-color: #3c3c3c;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #ffffff;
            }
        """)
        sample_layout = QVBoxLayout()
        self.text_label = QLabel(self.sample_text)
        self.text_label.setWordWrap(True)
        self.text_label.setFont(QFont("Segoe UI", 16))
        self.text_label.setStyleSheet("padding: 15px; color: #ffffff; background-color: #3c3c3c; border-radius: 5px;")
        self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sample_layout.addWidget(self.text_label)
        sample_group.setLayout(sample_layout)
        sample_group.setMinimumHeight(150)
        main_layout.addWidget(sample_group)

        input_group = QGroupBox("Your Typing")
        input_group.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        input_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 1ex;
                background-color: #3c3c3c;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #ffffff;
            }
        """)
        input_layout = QVBoxLayout()
        self.input_edit = QTextEdit()
        self.input_edit.setFont(QFont("Segoe UI", 16))
        self.input_edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid #555;
                border-radius: 8px;
                padding: 15px;
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QTextEdit:focus {
                border: 2px solid #4a90e2;
            }
        """)
        self.input_edit.setMinimumHeight(140)
        self.input_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.input_edit.textChanged.connect(self.check_progress)
        input_layout.addWidget(self.input_edit)

        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        input_layout.addWidget(self.progress_bar)

        input_group.setLayout(input_layout)
        input_group.setMinimumHeight(200)
        main_layout.addWidget(input_group)

        control_group = QGroupBox("Statistics and Controls")
        control_group.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        control_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 1ex;
                background-color: #3c3c3c;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #ffffff;
            }
        """)
        control_layout = QVBoxLayout()

        self.stats_label = QLabel("WPM: 0 | Accuracy: 0% | Time: 0s")
        self.stats_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.stats_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: #4a4a4a;
                border-radius: 8px;
                border: 1px solid #666;
                color: #ffffff;
            }
        """)
        control_layout.addWidget(self.stats_label)

        length_layout = QHBoxLayout()
        length_layout.setSpacing(15)

        length_label = QLabel("Text Length (words):")
        length_label.setFont(QFont("Segoe UI", 12))
        length_label.setStyleSheet("color: #ffffff;")
        length_layout.addWidget(length_label)

        self.word_count_combo = QComboBox()
        self.word_count_combo.setFont(QFont("Segoe UI", 12))
        self.word_count_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #555;
                border-radius: 5px;
                background-color: #3c3c3c;
                color: #ffffff;
                min-width: 120px;
            }
            QComboBox:focus {
                border: 2px solid #4a90e2;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png); /* Optional: custom arrow */
                width: 12px;
                height: 12px;
            }
        """)
        self.word_count_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.word_count_combo.addItems(["10", "20", "30", "40", "50", "60", "70", "80", "90", "100", "150", "200", "300", "500"])
        self.word_count_combo.setCurrentText("50")
        self.word_count_combo.currentTextChanged.connect(self.on_word_count_changed)
        length_layout.addWidget(self.word_count_combo)
        length_layout.addStretch()

        control_layout.addLayout(length_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.start_button = QPushButton("Start")
        self.start_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.start_button.setIcon(QIcon(self.style().standardIcon(QStyle.SP_MediaPlay)))
        self.start_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                min-width: 100px;
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
        self.reset_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.reset_button.setIcon(QIcon(self.style().standardIcon(QStyle.SP_BrowserReload)))
        self.reset_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 8px;
                min-width: 100px;
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
        self.new_text_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.new_text_button.setIcon(QIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder)))
        self.new_text_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                min-width: 100px;
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
        control_group.setMinimumHeight(180)
        main_layout.addWidget(control_group)

        main_layout.addStretch()  # Allow sections to expand

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
        self.progress_bar.setValue(0)
        self.stats_updated.emit("0", "0%", "0s")

    def load_new_sample_text(self):
        self.sample_text = generate_mixed_text(length=self.text_length)
        self.text_label.setText(self.sample_text)
        self.reset_practice()

    def on_word_count_changed(self, text):
        self.text_length = int(text)
        self.load_new_sample_text()

    def update_time(self):
        if self.start_time:
            self.elapsed_time = time.time() - self.start_time
            self.stats_updated.emit(self.last_wpm, self.last_accuracy, f"{int(self.elapsed_time)}s")

    def check_progress(self):
        typed_text = self.input_edit.toPlainText()
        self.text_updated.emit(typed_text)

        html = ""
        correct_count = 0
        for i, char in enumerate(self.sample_text):
            escaped_char = char.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            if i < len(typed_text):
                if typed_text[i] == char:
                    html += f'<span style="color: #4CAF50;">{escaped_char}</span>'  # Green for correct
                    correct_count += 1
                else:
                    html += f'<span style="color: red;">{escaped_char}</span>'  # Red for incorrect
            else:
                html += escaped_char
        self.text_label.setText(html)

        progress = min(correct_count / len(self.sample_text) * 100, 100) if self.sample_text else 0
        self.progress_bar.setValue(int(progress))

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
