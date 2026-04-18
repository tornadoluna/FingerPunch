from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QGroupBox, QProgressBar, QComboBox, QSizePolicy, QTextBrowser, QDialog, QDialogButtonBox
from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtGui import QFont, QIcon, QTextCursor
from PySide6.QtWidgets import QStyle
import time
from statsWorker import StatsWorker
from textGenerator import generate_mixed_text

class ResultsDialog(QDialog):
    def __init__(self, stats, parent=None):
        super().__init__(parent)
        self.stats = stats
        self.setWindowTitle("Typing Session Complete!")
        self.setModal(True)
        self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")
        self.resize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("🎉 Session Complete! 🎉")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(title)

        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(15)

        primary_stats = [
            ("Words Per Minute", f"{self.stats['wpm']:.1f} WPM"),
            ("Accuracy", f"{self.stats['accuracy']:.1f}%"),
            ("Time Taken", f"{self.stats['time']:.1f}s")
        ]

        for label, value in primary_stats:
            stat_layout = QHBoxLayout()
            stat_label = QLabel(f"{label}:")
            stat_label.setFont(QFont("Segoe UI", 14))
            stat_label.setStyleSheet("color: #cccccc;")
            stat_label.setMinimumWidth(150)

            stat_value = QLabel(value)
            stat_value.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            stat_value.setStyleSheet("color: #ffffff;")
            stat_value.setAlignment(Qt.AlignRight)

            stat_layout.addWidget(stat_label)
            stat_layout.addWidget(stat_value)
            stats_layout.addLayout(stat_layout)

        separator = QLabel("")
        separator.setStyleSheet("border-top: 1px solid #555; margin: 10px 0;")
        stats_layout.addWidget(separator)

        detailed_stats = [
            ("Characters Typed", f"{self.stats['total_chars']}"),
            ("Total Keystrokes", f"{self.stats['keystrokes']}"),
            ("Typing Efficiency", f"{self.stats['efficiency']:.1f}%")
        ]

        for label, value in detailed_stats:
            stat_layout = QHBoxLayout()
            stat_label = QLabel(f"{label}:")
            stat_label.setFont(QFont("Segoe UI", 12))
            stat_label.setStyleSheet("color: #aaaaaa;")
            stat_label.setMinimumWidth(150)

            stat_value = QLabel(value)
            stat_value.setFont(QFont("Segoe UI", 12))
            stat_value.setStyleSheet("color: #cccccc;")
            stat_value.setAlignment(Qt.AlignRight)

            stat_layout.addWidget(stat_label)
            stat_layout.addWidget(stat_value)
            stats_layout.addLayout(stat_layout)

        layout.addLayout(stats_layout)

        performance_msg = self.get_performance_message()
        msg_label = QLabel(performance_msg)
        msg_label.setFont(QFont("Segoe UI", 12))
        msg_label.setStyleSheet("color: #4CAF50; padding: 10px; background-color: #3c3c3c; border-radius: 5px;")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)

        button_box = QDialogButtonBox()
        button_box.setStyleSheet("""
            QDialogButtonBox {
                border: none;
            }
            QPushButton {
                padding: 8px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)

        retry_button = button_box.addButton("Try Again", QDialogButtonBox.ButtonRole.AcceptRole)
        new_text_button = button_box.addButton("New Text", QDialogButtonBox.ButtonRole.ActionRole)
        close_button = button_box.addButton("Close", QDialogButtonBox.ButtonRole.RejectRole)

        retry_button.clicked.connect(self.accept)
        new_text_button.clicked.connect(self.new_text)
        close_button.clicked.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def get_performance_message(self):
        wpm = self.stats['wpm']
        accuracy = self.stats['accuracy']

        if accuracy >= 98 and wpm >= 60:
            return "🏆 Excellent! You're a typing master!"
        elif accuracy >= 95 and wpm >= 40:
            return "💪 Great job! Keep practicing to improve your speed."
        elif accuracy >= 90:
            return "👍 Good work! Focus on accuracy and speed will follow."
        elif accuracy >= 80:
            return "📚 Keep practicing! Accuracy is the foundation of good typing."
        else:
            return "🎯 Don't give up! Every expert was once a beginner. Keep trying!"

    def new_text(self):
        self.done(2)

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
        self.last_scroll_position = 0
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

        self.stats_worker = StatsWorker(self)
        self.stats_worker.stats_updated.connect(self.update_stats)
        self.stats_worker.start()

    def init_ui(self):
        self.setWindowTitle("FingerPunch")
        self.resize(900, 700)
        self.setMinimumSize(800, 700)
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
        self.text_label = QTextBrowser()
        self.text_label.setText(self.sample_text)
        self.text_label.setFont(QFont("Segoe UI", 16))
        self.text_label.setStyleSheet("""
            QTextBrowser {
                padding: 15px;
                color: #ffffff;
                background-color: #3c3c3c;
                border-radius: 5px;
                border: none;
            }
            QTextBrowser QScrollBar:vertical {
                width: 0px;
                background: transparent;
            }
            QTextBrowser QScrollBar:horizontal {
                height: 0px;
                background: transparent;
            }
        """)
        self.text_label.setReadOnly(True)
        self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sample_layout.addWidget(self.text_label)
        sample_layout.addWidget(self.progress_bar)
        sample_group.setLayout(sample_layout)
        sample_group.setMinimumHeight(200)
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

        input_group.setLayout(input_layout)
        input_group.setMinimumHeight(200)
        main_layout.addWidget(input_group)

        control_group = QGroupBox("Controls")
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


        length_layout = QHBoxLayout()
        length_layout.setSpacing(15)

        length_label = QLabel("Sample Text Length:")
        length_label.setFont(QFont("Segoe UI", 12))
        length_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                border: 2px solid #555;
                border-radius: 8px;
                background-color: #3c3c3c;
                color: #ffffff;
            }
        """)
        length_layout.addWidget(length_label)

        self.word_count_combo = QComboBox()
        self.word_count_combo.setFont(QFont("Segoe UI", 12))
        self.word_count_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #555;
                border-radius: 8px;
                background-color: #3c3c3c;
                color: #ffffff;
                min-width: 120px;
            }
            QComboBox:focus {
                border: 2px solid #4a90e2;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #3c3c3c;
            }
        """)
        self.word_count_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.word_count_combo.addItems(["10", "20", "30", "40", "50", "60", "70", "80", "90", "100", "150", "200", "300", "500"])
        self.word_count_combo.setCurrentText("50")
        self.word_count_combo.setToolTip("Select the number of words for the sample text")
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
        control_group.setMinimumHeight(120)
        main_layout.addWidget(control_group)

        main_layout.addStretch()

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
                    html += f'<span style="color: #4CAF50;">{escaped_char}</span>'
                    correct_count += 1
                else:
                    html += f'<span style="color: red;">{escaped_char}</span>'
            else:
                html += escaped_char
        self.text_label.setHtml(html)

        cursor = self.text_label.textCursor()
        cursor.setPosition(min(len(typed_text), len(self.sample_text)))
        self.text_label.setTextCursor(cursor)
        self.text_label.ensureCursorVisible()

        progress = min(correct_count / len(self.sample_text) * 100, 100) if self.sample_text else 0
        self.progress_bar.setValue(int(progress))

        if not self.start_time and typed_text:
            self.start_time = time.time()
            self.timer.start(1000)

        if len(typed_text) == len(self.sample_text) and typed_text == self.sample_text:
            if not self.is_done:
                self.is_done = True
                self.timer.stop()
                self.show_results_dialog()

    def update_stats(self, wpm, accuracy):
        elapsed_time = time.time() - self.start_time
        self.last_wpm = wpm
        self.last_accuracy = accuracy
        self.stats_updated.emit(f"{wpm}", f"{accuracy}", f"{int(elapsed_time)}s")


    def show_results_dialog(self):
        stats = self.stats_worker.get_final_stats()
        dialog = ResultsDialog(stats, self)
        result = dialog.exec()

        if result == QDialog.Accepted:
            self.reset_practice()
        elif result == 2:  # New Text button
            self.load_new_sample_text()

    def closeEvent(self, event):
        self.stats_worker.stop_worker()
        super().closeEvent(event)
