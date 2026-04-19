from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QGroupBox, QProgressBar, QComboBox, QSizePolicy, QTextBrowser, QDialog, QDialogButtonBox, QTabWidget
from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtGui import QFont, QIcon, QTextCursor
from PySide6.QtWidgets import QStyle
import time
from statsWorker import StatsWorker
from textGenerator import generate_mixed_text
from dataManager import DataManager

# Set up matplotlib for Qt integration
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime

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
        self.data_manager = DataManager()
        # Initialize achievements system
        self.data_manager.init_achievements()
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

        self.history_button = QPushButton("View History")
        self.history_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.history_button.setIcon(QIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView)))
        self.history_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 8px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #8e24aa;
            }
            QPushButton:pressed {
                background-color: #7b1fa2;
            }
        """)
        self.history_button.clicked.connect(self.show_history_dialog)
        button_layout.addWidget(self.history_button)

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
        # Save session data
        self.data_manager.save_session(stats, self.sample_text)

        # Update streaks and check achievements
        self.data_manager.update_streaks()
        self.data_manager.check_achievements()

        dialog = ResultsDialog(stats, self)
        result = dialog.exec()

        if result == QDialog.Accepted:
            self.reset_practice()
        elif result == 2:  # New Text button
            self.load_new_sample_text()

    def show_history_dialog(self):
        sessions = self.data_manager.get_all_sessions()
        if not sessions:
            self.show_message("No history found", "You have no typing history recorded.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Typing History")
        dialog.setModal(True)
        dialog.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")
        dialog.resize(800, 500)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🕒 Typing History")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #9C27B0; margin-bottom: 10px;")
        layout.addWidget(title)

        # Add summary stats
        stats = self.data_manager.get_session_stats()
        if stats['total_sessions'] > 0:
            summary_text = f"Total Sessions: {stats['total_sessions']} | Best WPM: {stats['best_wpm']} | Best Accuracy: {stats['best_accuracy']}% | Avg WPM: {stats['avg_wpm']} | Avg Accuracy: {stats['avg_accuracy']}%"
            summary_label = QLabel(summary_text)
            summary_label.setFont(QFont("Segoe UI", 12))
            summary_label.setStyleSheet("color: #4CAF50; padding: 10px; background-color: #3c3c3c; border-radius: 5px;")
            summary_label.setWordWrap(True)
            layout.addWidget(summary_label)

        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 12px 20px;
                border: 2px solid #555;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #45a049;
            }
        """)

        # ===== SESSIONS TAB =====
        sessions_widget = QWidget()
        sessions_layout = QVBoxLayout()
        sessions_layout.setSpacing(10)
        sessions_layout.setContentsMargins(10, 10, 10, 10)

        history_list = QTextBrowser()
        history_list.setFont(QFont("Segoe UI", 12))
        history_list.setStyleSheet("""
            QTextBrowser {
                padding: 10px;
                color: #ffffff;
                background-color: #3c3c3c;
                border-radius: 5px;
                border: none;
            }
        """)
        history_list.setReadOnly(True)
        history_list.setHtml(self.get_history_html(sessions))
        sessions_layout.addWidget(history_list)

        sessions_widget.setLayout(sessions_layout)
        tab_widget.addTab(sessions_widget, "📊 Sessions")

        # ===== ANALYTICS TAB =====
        analytics_widget = QWidget()
        analytics_layout = QVBoxLayout()
        analytics_layout.setSpacing(15)
        analytics_layout.setContentsMargins(15, 15, 15, 15)

        # Chart type selector
        chart_selector_layout = QHBoxLayout()
        chart_selector_layout.addWidget(QLabel("Chart Type:"))

        self.chart_combo = QComboBox()
        self.chart_combo.addItems(["Performance Overview", "Recent Activity", "Performance by Length"])
        self.chart_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #555;
                border-radius: 8px;
                background-color: #3c3c3c;
                color: #ffffff;
                min-width: 200px;
            }
        """)
        self.chart_combo.currentTextChanged.connect(self.update_analytics_chart)
        chart_selector_layout.addWidget(self.chart_combo)
        chart_selector_layout.addStretch()
        analytics_layout.addLayout(chart_selector_layout)

        # Chart display area
        self.analytics_canvas = FigureCanvas(Figure(figsize=(12, 7)))
        analytics_layout.addWidget(self.analytics_canvas)

        # Initialize with overview chart
        self.update_analytics_chart("Performance Overview")

        analytics_widget.setLayout(analytics_layout)
        tab_widget.addTab(analytics_widget, "📈 Analytics")

        # ===== PROGRESS TAB =====
        progress_widget = QWidget()
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(20)
        progress_layout.setContentsMargins(20, 20, 20, 20)

        # Personal Bests Section
        bests_group = QGroupBox("🏆 Personal Bests")
        bests_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #2a2a2a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #4CAF50;
                font-size: 14px;
            }
        """)
        bests_layout = QVBoxLayout()
        bests_layout.setSpacing(10)
        self.create_personal_bests_display(bests_layout)
        bests_group.setLayout(bests_layout)
        progress_layout.addWidget(bests_group)

        # Achievements and Streaks in horizontal layout
        achievements_streaks_layout = QHBoxLayout()
        achievements_streaks_layout.setSpacing(15)

        # Achievements Section
        achievements_group = QGroupBox("🎯 Achievements")
        achievements_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #9C27B0;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #2a2a2a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #9C27B0;
                font-size: 14px;
            }
        """)
        achievements_layout = QVBoxLayout()
        achievements_layout.setSpacing(10)
        self.create_achievements_display(achievements_layout)
        achievements_group.setLayout(achievements_layout)
        achievements_streaks_layout.addWidget(achievements_group)

        # Streaks Section
        streaks_group = QGroupBox("🔥 Streaks")
        streaks_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #FF9800;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #2a2a2a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #FF9800;
                font-size: 14px;
            }
        """)
        streaks_layout = QVBoxLayout()
        streaks_layout.setSpacing(10)
        self.create_streaks_display(streaks_layout)
        streaks_group.setLayout(streaks_layout)
        achievements_streaks_layout.addWidget(streaks_group)

        progress_layout.addLayout(achievements_streaks_layout)

        # Goals Section
        goals_group = QGroupBox("🎯 Goals")
        goals_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2196F3;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #2a2a2a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #2196F3;
                font-size: 14px;
            }
        """)
        goals_layout = QVBoxLayout()
        goals_layout.setSpacing(10)
        self.create_goals_display(goals_layout)
        goals_group.setLayout(goals_layout)
        progress_layout.addWidget(goals_group)

        progress_widget.setLayout(progress_layout)
        tab_widget.addTab(progress_widget, "🚀 Progress")

        layout.addWidget(tab_widget)

        close_button = QPushButton("Close")
        close_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        close_button.setStyleSheet("""
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
        close_button.clicked.connect(dialog.reject)
        layout.addWidget(close_button, alignment=Qt.AlignCenter)

        dialog.setLayout(layout)
        dialog.exec()

    def update_analytics_chart(self, chart_type):
        # Clear the canvas
        self.analytics_canvas.figure.clear()

        if chart_type == "Performance Overview":
            # Get all sessions
            sessions = self.data_manager.get_all_sessions()
            if not sessions:
                return

            # Extract data for the chart
            dates = [datetime.fromisoformat(session[1]) for session in sessions]
            wpms = [session[2] for session in sessions]
            accuracies = [session[3] for session in sessions]

            # Create the plot
            ax = self.analytics_canvas.figure.add_subplot(111)
            ax.clear()
            ax.plot(dates, wpms, label="WPM", color="#4CAF50", marker="o")
            ax.plot(dates, accuracies, label="Accuracy", color="#2196F3", marker="o")

            # Format the date axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
            ax.xaxis.set_major_locator(mdates.DayLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

            # Labels and title
            ax.set_xlabel("Date")
            ax.set_ylabel("WPM / Accuracy")
            ax.set_title("Typing Performance Over Time")
            ax.legend()

        elif chart_type == "Recent Activity":
            # Get the current session data
            sessions = self.data_manager.get_all_sessions()
            if not sessions:
                return

            # Extract the last 30 days' data
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=30)
            recent_sessions = [session for session in sessions if datetime.fromisoformat(session[1]) >= cutoff_date]

            if not recent_sessions:
                return

            dates = [datetime.fromisoformat(session[1]) for session in recent_sessions]
            wpms = [session[2] for session in recent_sessions]
            accuracies = [session[3] for session in recent_sessions]

            # Create the plot
            ax = self.analytics_canvas.figure.add_subplot(111)
            ax.clear()
            ax.plot(dates, wpms, label="WPM", color="#4CAF50", marker="o")
            ax.plot(dates, accuracies, label="Accuracy", color="#2196F3", marker="o")

            # Format the date axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

            # Labels and title
            ax.set_xlabel("Date")
            ax.set_ylabel("WPM / Accuracy")
            ax.set_title("Typing Activity - Last 30 Days")
            ax.legend()

        elif chart_type == "Performance by Length":
            # Get performance by length data
            length_data = self.data_manager.get_performance_by_length()
            if not length_data:
                return

            # Extract data
            lengths = [row[0] for row in length_data]
            avg_wpms = [row[1] for row in length_data]
            best_wpms = [row[2] for row in length_data]
            avg_accuracies = [row[3] for row in length_data]
            best_accuracies = [row[4] for row in length_data]

            # Clear the canvas
            self.length_canvas.figure.clear()

            # Create subplots
            ax1 = self.length_canvas.figure.add_subplot(111)

            x = list(range(len(lengths)))
            width = 0.35

            # Bar chart for WPM
            ax1.bar([i - width/2 for i in x], avg_wpms, width, label='Avg WPM', color='#4CAF50', alpha=0.7)
            ax1.bar([i + width/2 for i in x], best_wpms, width, label='Best WPM', color='#66BB6A', alpha=0.7)
            ax1.set_xlabel('Text Length (words)')
            ax1.set_ylabel('WPM', color='#4CAF50')
            ax1.tick_params(axis='y', labelcolor='#4CAF50')

            # Line chart for accuracy on secondary axis
            ax2 = ax1.twinx()
            ax2.plot(x, avg_accuracies, 'o-', label='Avg Accuracy', color='#2196F3', linewidth=2, markersize=6)
            ax2.plot(x, best_accuracies, 's-', label='Best Accuracy', color='#42A5F5', linewidth=2, markersize=6)
            ax2.set_ylabel('Accuracy (%)', color='#2196F3')
            ax2.tick_params(axis='y', labelcolor='#2196F3')

            # X-axis labels
            ax1.set_xticks(x)
            ax1.set_xticklabels(lengths)

            # Title
            ax1.set_title('Typing Performance by Text Length')

            # Combine legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        # Refresh the canvas
        self.analytics_canvas.draw()

    def create_personal_bests_display(self, layout):
        # Get personal bests
        bests = self.data_manager.get_personal_bests()
        if not bests:
            label = QLabel("No personal bests yet. Complete some sessions to generate personal bests.")
            label.setFont(QFont("Segoe UI", 12))
            label.setStyleSheet("color: #cccccc;")
            label.setWordWrap(True)
            layout.addWidget(label)
            return

        # Get improvement metrics
        improvements = self.data_manager.get_improvement_metrics()

        # Create a grid layout for better organization
        from PySide6.QtWidgets import QGridLayout, QGroupBox
        grid = QGridLayout()
        grid.setSpacing(10)

        row = 0
        for key, data in bests.items():
            # Format the key name
            display_name = key.replace('_', ' ').title()
            if key == 'best_wpm':
                display_name = 'Best WPM'
            elif key == 'best_accuracy':
                display_name = 'Best Accuracy'
            elif key == 'best_efficiency':
                display_name = 'Best Efficiency'
            elif key == 'most_chars':
                display_name = 'Most Characters'

            # Create labels
            name_label = QLabel(f"{display_name}:")
            name_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            name_label.setStyleSheet("color: #ffffff;")

            if key in ['best_wpm', 'best_accuracy', 'best_efficiency']:
                value_text = f"{data['value']:.1f}"
            else:
                value_text = f"{data['value']}"

            value_label = QLabel(value_text)
            value_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            value_label.setStyleSheet("color: #4CAF50;")

            # Add date if available
            date_label = QLabel("")
            if data['date']:
                from datetime import datetime
                date_obj = datetime.fromisoformat(data['date'])
                date_text = date_obj.strftime("%Y-%m-%d %H:%M")
                date_label = QLabel(f"({date_text})")
                date_label.setFont(QFont("Segoe UI", 10))
                date_label.setStyleSheet("color: #aaaaaa;")

            grid.addWidget(name_label, row, 0)
            grid.addWidget(value_label, row, 1)
            grid.addWidget(date_label, row, 2)
            row += 1

        # Add improvement metrics
        if improvements and improvements['wpm_improvement'] != 0:
            separator = QLabel("")
            separator.setStyleSheet("height: 2px; background-color: #555; margin: 10px 0;")
            grid.addWidget(separator, row, 0, 1, 3)
            row += 1

            improvement_title = QLabel("Improvement Metrics:")
            improvement_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            improvement_title.setStyleSheet("color: #ffffff;")
            grid.addWidget(improvement_title, row, 0, 1, 3)
            row += 1

            wpm_imp_label = QLabel(f"WPM Improvement: {improvements['wpm_improvement']:+.1f}")
            wpm_imp_label.setFont(QFont("Segoe UI", 11))
            wpm_imp_label.setStyleSheet("color: #4CAF50;" if improvements['wpm_improvement'] > 0 else "color: #f44336;")
            grid.addWidget(wpm_imp_label, row, 0, 1, 3)
            row += 1

            acc_imp_label = QLabel(f"Accuracy Improvement: {improvements['accuracy_improvement']:+.1f}%")
            acc_imp_label.setFont(QFont("Segoe UI", 11))
            acc_imp_label.setStyleSheet("color: #4CAF50;" if improvements['accuracy_improvement'] > 0 else "color: #f44336;")
            grid.addWidget(acc_imp_label, row, 0, 1, 3)
            row += 1

            consistency_label = QLabel(f"Consistency Score: {improvements['consistency_score']:.1f}/100")
            consistency_label.setFont(QFont("Segoe UI", 11))
            consistency_label.setStyleSheet("color: #2196F3;")
            grid.addWidget(consistency_label, row, 0, 1, 3)

        layout.addLayout(grid)

    def create_goals_display(self, layout):
        # Get goals
        goals = self.data_manager.get_goals()
        if not goals:
            label = QLabel("No goals set yet. Create some goals to track your progress.")
            label.setFont(QFont("Segoe UI", 12))
            label.setStyleSheet("color: #cccccc;")
            label.setWordWrap(True)
            layout.addWidget(label)
            return

        # Create a list view for goals
        from PySide6.QtWidgets import QListView, QAbstractItemView
        list_view = QListView()
        list_view.setFont(QFont("Segoe UI", 12))
        list_view.setStyleSheet("""
            QListView {
                border: 2px solid #555;
                border-radius: 8px;
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QListView::item {
                padding: 10px;
                border-bottom: 1px solid #555;
            }
            QListView::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)
        list_view.setSelectionMode(QAbstractItemView.SingleSelection)
        list_view.setSpacing(5)

        # Set model for list view
        from PySide6.QtGui import QStandardItemModel, QStandardItem
        model = QStandardItemModel()
        for goal in goals:
            goal_id, goal_type, target_value, current_value, created_date, target_date, achieved, achieved_date = goal
            status = "✅ Achieved" if achieved else f"📊 {current_value}/{target_value}"
            item_text = f"{goal_type.title()} Goal: {status}"
            item = QStandardItem(item_text)
            item.setData(goal, role=Qt.UserRole)
            model.appendRow(item)
        list_view.setModel(model)

        # Connect signal for item selection
        list_view.selectionModel().selectionChanged.connect(lambda: self.on_goal_selected(list_view, model))

        layout.addWidget(list_view)

        # Goal details
        self.goal_details = QTextBrowser()
        self.goal_details.setFont(QFont("Segoe UI", 12))
        self.goal_details.setStyleSheet("""
            QTextBrowser {
                padding: 10px;
                color: #ffffff;
                background-color: #3c3c3c;
                border-radius: 5px;
                border: none;
            }
        """)
        self.goal_details.setOpenExternalLinks(True)
        layout.addWidget(self.goal_details)

        # Load first goal details by default if goals exist
        if goals:
            self.load_goal_details(goals[0])

    def on_goal_selected(self, list_view, model):
        selected = list_view.selectedIndexes()
        if not selected:
            return
        index = selected[0].row()
        goal = model.item(index).data(Qt.UserRole)
        self.load_goal_details(goal)

    def load_goal_details(self, goal):
        goal_id, goal_type, target_value, current_value, created_date, target_date, achieved, achieved_date = goal
        status = "✅ Achieved" if achieved else f"📊 In Progress ({current_value}/{target_value})"

        html = f"""
        <style>
        .title {{
            font-size: 18px;
            font-weight: bold;
            color: #4CAF50;
        }}
        .subtitle {{
            font-size: 14px;
            font-weight: bold;
            color: #ffffff;
        }}
        .text {{
            font-size: 12px;
            color: #cccccc;
        }}
        </style>
        <div class="title">{goal_type.title()} Goal</div>
        <div class="subtitle">Target: {target_value}</div>
        <div class="subtitle">Current: {current_value}</div>
        <div class="subtitle">Status: {status}</div>
        <div class="text">Created: {created_date[:10]}</div>
        """
        if target_date:
            html += f'<div class="text">Target Date: {target_date[:10]}</div>'
        if achieved and achieved_date:
            html += f'<div class="text">Achieved: {achieved_date[:10]}</div>'

        self.goal_details.setHtml(html)

    def create_achievements_display(self, layout):
        # Get achievements
        achievements = self.data_manager.get_achievements()
        if not achievements:
            label = QLabel("No achievements earned yet. Complete sessions to unlock achievements.")
            label.setFont(QFont("Segoe UI", 12))
            label.setStyleSheet("color: #cccccc;")
            label.setWordWrap(True)
            layout.addWidget(label)
            return

        # Create a list view for achievements
        from PySide6.QtWidgets import QListView, QAbstractItemView
        list_view = QListView()
        list_view.setFont(QFont("Segoe UI", 12))
        list_view.setStyleSheet("""
            QListView {
                border: 2px solid #555;
                border-radius: 8px;
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QListView::item {
                padding: 10px;
                border-bottom: 1px solid #555;
            }
            QListView::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)
        list_view.setSelectionMode(QAbstractItemView.SingleSelection)
        list_view.setSpacing(5)

        # Set model for list view
        from PySide6.QtGui import QStandardItemModel, QStandardItem
        model = QStandardItemModel()
        for achievement in achievements:
            ach_id, name, desc, icon, category, req_type, req_value, unlocked, unlocked_date, progress = achievement
            status_icon = icon if unlocked else "🔒"
            item_text = f"{status_icon} {name}"
            item = QStandardItem(item_text)
            item.setData(achievement, role=Qt.UserRole)
            model.appendRow(item)
        list_view.setModel(model)

        # Connect signal for item selection
        list_view.selectionModel().selectionChanged.connect(lambda: self.on_achievement_selected(list_view, model))

        layout.addWidget(list_view)

        # Achievement details
        self.achievement_details = QTextBrowser()
        self.achievement_details.setFont(QFont("Segoe UI", 12))
        self.achievement_details.setStyleSheet("""
            QTextBrowser {
                padding: 10px;
                color: #ffffff;
                background-color: #3c3c3c;
                border-radius: 5px;
                border: none;
            }
        """)
        self.achievement_details.setOpenExternalLinks(True)
        layout.addWidget(self.achievement_details)

        # Load first achievement details by default if achievements exist
        if achievements:
            self.load_achievement_details(achievements[0])

    def on_achievement_selected(self, list_view, model):
        selected = list_view.selectedIndexes()
        if not selected:
            return
        index = selected[0].row()
        achievement = model.item(index).data(Qt.UserRole)
        self.load_achievement_details(achievement)

    def load_achievement_details(self, achievement):
        ach_id, name, desc, icon, category, req_type, req_value, unlocked, unlocked_date, progress = achievement

        status = "✅ Unlocked" if unlocked else f"🔒 Locked ({progress}/{req_value})"
        unlock_date = f"Unlocked: {unlocked_date[:10]}" if unlocked and unlocked_date else ""

        html = f"""
        <style>
        .title {{
            font-size: 18px;
            font-weight: bold;
            color: #4CAF50;
        }}
        .subtitle {{
            font-size: 14px;
            font-weight: bold;
            color: #ffffff;
        }}
        .text {{
            font-size: 12px;
            color: #cccccc;
        }}
        </style>
        <div class="title">{icon} {name}</div>
        <div class="subtitle">Category: {category.title()}</div>
        <div class="subtitle">Status: {status}</div>
        <div class="text">{desc}</div>
        """
        if unlock_date:
            html += f'<div class="text">{unlock_date}</div>'

        self.achievement_details.setHtml(html)

    def create_streaks_display(self, layout):
        # Get streak info
        streak_info = self.data_manager.get_streak_info()
        if not streak_info:
            label = QLabel("No streaks recorded yet. Complete sessions to build your streak.")
            label.setFont(QFont("Segoe UI", 12))
            label.setStyleSheet("color: #cccccc;")
            label.setWordWrap(True)
            layout.addWidget(label)
            return

        # Display current streak info
        current_streak_label = QLabel(f"🔥 Current Streak: {streak_info['current_streak']} days")
        current_streak_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        current_streak_label.setStyleSheet("color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(current_streak_label)

        longest_streak_label = QLabel(f"🏆 Longest Streak: {streak_info['longest_streak']} days")
        longest_streak_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        longest_streak_label.setStyleSheet("color: #2196F3; margin-bottom: 20px;")
        layout.addWidget(longest_streak_label)

        # Get streak history
        streak_history = self.data_manager.get_streak_history(14)  # Last 14 days

        if streak_history:
            # Create a simple text display of recent streak history
            history_text = "Recent Streak History:\n\n"
            for streak in streak_history[-7:]:  # Show last 7 days
                date, sessions_count, current_streak = streak
                history_text += f"{date}: {sessions_count} sessions (streak: {current_streak})\n"

            history_browser = QTextBrowser()
            history_browser.setFont(QFont("Segoe UI", 12))
            history_browser.setStyleSheet("""
                QTextBrowser {
                    padding: 10px;
                    color: #ffffff;
                    background-color: #3c3c3c;
                    border-radius: 5px;
                    border: none;
                }
            """)
            history_browser.setPlainText(history_text)
            history_browser.setMaximumHeight(200)
            layout.addWidget(history_browser)

        # Motivation text
        motivation_label = QLabel("💪 Keep practicing daily to build your streak!")
        motivation_label.setFont(QFont("Segoe UI", 12))
        motivation_label.setStyleSheet("color: #cccccc; margin-top: 20px;")
        motivation_label.setWordWrap(True)
        layout.addWidget(motivation_label)

    def get_history_html(self, sessions):
        from datetime import datetime
        html = '<style>table {width: 100%; border-collapse: collapse; font-size: 12px;} th, td {padding: 6px; text-align: left; border-bottom: 1px solid #555;} th {background-color: #4CAF50; color: white; font-weight: bold;} tr:nth-child(even) {background-color: #2a2a2a;} tr:hover {background-color: #3e8e41;}</style>'
        html += '<table>'
        html += '<tr><th>Date</th><th>Time</th><th>WPM</th><th>Accuracy</th><th>Chars</th><th>Keystrokes</th><th>Efficiency</th></tr>'
        for session in sessions:
            # session format: (id, date, wpm, accuracy, time_taken, total_chars, keystrokes, efficiency, text_length, sample_text)
            date_obj = datetime.fromisoformat(session[1])
            date_str = date_obj.strftime("%Y-%m-%d")
            time_str = date_obj.strftime("%H:%M")
            html += f'<tr><td>{date_str}</td><td>{time_str}</td><td>{session[2]:.1f}</td><td>{session[3]:.1f}%</td><td>{session[5]}</td><td>{session[6]}</td><td>{session[7]:.1f}%</td></tr>'
        html += '</table>'
        return html

    def show_message(self, title, message):
        msg_box = QDialog(self)
        msg_box.setWindowTitle(title)
        msg_box.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")
        msg_box.setFixedSize(400, 200)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        msg_label = QLabel(message)
        msg_label.setFont(QFont("Segoe UI", 12))
        msg_label.setStyleSheet("color: #cccccc;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        close_button = QPushButton("Close")
        close_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        close_button.setStyleSheet("""
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
        close_button.clicked.connect(msg_box.reject)
        layout.addWidget(close_button, alignment=Qt.AlignCenter)

        msg_box.setLayout(layout)
        msg_box.exec()

    def closeEvent(self, event):
        self.stats_worker.stop_worker()
        super().closeEvent(event)
