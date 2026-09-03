from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QFont, QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStyle,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import styles
from dataManager import DataManager
from historyDialog import HistoryDialog
from resultsDialog import NEW_TEXT_RESULT, ResultsDialog
from statsWorker import StatsWorker
from textGenerator import generate_mixed_text


def show_message(parent: QWidget, title: str, message: str) -> None:
    """A simple modal message box, styled to match the app."""
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setStyleSheet(styles.WINDOW_STYLE)
    dialog.setFixedSize(400, 200)

    layout = QVBoxLayout()
    layout.setSpacing(16)
    layout.setContentsMargins(24, 24, 24, 24)

    msg_label = QLabel(message)
    msg_label.setFont(styles.ui_font(12))
    msg_label.setStyleSheet(f"color: {styles.TEXT_SECONDARY};")
    msg_label.setWordWrap(True)
    layout.addWidget(msg_label)

    close_button = QPushButton("Close")
    close_button.setFont(styles.ui_font(12, QFont.Weight.DemiBold))
    close_button.setStyleSheet(styles.secondary_button_style())
    close_button.clicked.connect(dialog.reject)
    layout.addWidget(close_button, alignment=Qt.AlignCenter)

    dialog.setLayout(layout)
    dialog.exec()


class TypingPracticeApp(QWidget):
    stats_updated = Signal(str, str, str)
    text_updated = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.text_length: int = 50
        self.sample_text: str = generate_mixed_text(length=50)
        self.start_time: float | None = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.elapsed_time: float = 0
        self.is_done: bool = False
        self.last_wpm: str = "0"
        self.last_accuracy: str = "0%"
        self.last_scroll_position: int = 0
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(styles.PROGRESS_BAR_STYLE)
        self.data_manager = DataManager()
        self._init_ui()

        self.stats_worker = StatsWorker(self)
        self.stats_worker.stats_updated.connect(self.update_stats)

    def _init_ui(self) -> None:
        self.setWindowTitle("FingerPunch")
        self.resize(900, 700)
        self.setMinimumSize(800, 700)
        self.setStyleSheet(styles.WINDOW_STYLE)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.addWidget(self._build_sample_group())
        main_layout.addWidget(self._build_input_group())
        main_layout.addWidget(self._build_control_group())
        main_layout.addStretch()
        self.setLayout(main_layout)

    def _build_sample_group(self) -> QGroupBox:
        group = QGroupBox("SAMPLE TEXT")
        group.setFont(styles.ui_font(11, QFont.Weight.DemiBold))
        group.setStyleSheet(styles.panel_style())

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 20, 16, 16)

        self.text_label = QTextBrowser()
        self.text_label.setText(self.sample_text)
        self.text_label.setFont(styles.ui_font(16))
        self.text_label.setStyleSheet(styles.text_surface_style())
        self.text_label.setReadOnly(True)
        self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.text_label)
        layout.addWidget(self.progress_bar)

        group.setLayout(layout)
        group.setMinimumHeight(200)
        return group

    def _build_input_group(self) -> QGroupBox:
        group = QGroupBox("YOUR TYPING")
        group.setFont(styles.ui_font(11, QFont.Weight.DemiBold))
        group.setStyleSheet(styles.panel_style())

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 20, 16, 16)

        self.input_edit = QTextEdit()
        self.input_edit.setFont(styles.ui_font(16))
        self.input_edit.setStyleSheet(styles.text_surface_style())
        self.input_edit.setMinimumHeight(140)
        self.input_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.input_edit.textChanged.connect(self.check_progress)
        layout.addWidget(self.input_edit)

        group.setLayout(layout)
        group.setMinimumHeight(200)
        return group

    def _build_control_group(self) -> QGroupBox:
        group = QGroupBox("CONTROLS")
        group.setFont(styles.ui_font(11, QFont.Weight.DemiBold))
        group.setStyleSheet(styles.panel_style())

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 20, 16, 16)
        layout.addLayout(self._build_length_row())
        layout.addLayout(self._build_button_row())

        group.setLayout(layout)
        group.setMinimumHeight(120)
        return group

    def _build_length_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(15)

        label = QLabel("Sample Text Length:")
        label.setFont(styles.ui_font(12))
        label.setStyleSheet(styles.LABEL_CHIP_STYLE)
        row.addWidget(label)

        self.word_count_combo = QComboBox()
        self.word_count_combo.setFont(styles.ui_font(12))
        self.word_count_combo.setStyleSheet(styles.combo_box_style())
        self.word_count_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.word_count_combo.addItems(
            ["10", "20", "30", "40", "50", "60", "70", "80", "90", "100", "150", "200", "300", "500"]
        )
        self.word_count_combo.setCurrentText("50")
        self.word_count_combo.setToolTip("Select the number of words for the sample text")
        self.word_count_combo.currentTextChanged.connect(self.on_word_count_changed)
        row.addWidget(self.word_count_combo)
        row.addStretch()
        return row

    def _build_button_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)

        self.start_button = QPushButton("Start")
        self.start_button.setFont(styles.ui_font(12, QFont.Weight.DemiBold))
        self.start_button.setIcon(QIcon(self.style().standardIcon(QStyle.SP_MediaPlay)))
        self.start_button.setStyleSheet(styles.primary_button_style())
        self.start_button.clicked.connect(self.start_practice)
        row.addWidget(self.start_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setFont(styles.ui_font(12, QFont.Weight.DemiBold))
        self.reset_button.setIcon(QIcon(self.style().standardIcon(QStyle.SP_BrowserReload)))
        self.reset_button.setStyleSheet(styles.danger_button_style())
        self.reset_button.clicked.connect(self.reset_practice)
        row.addWidget(self.reset_button)

        self.new_text_button = QPushButton("New Text")
        self.new_text_button.setFont(styles.ui_font(12, QFont.Weight.DemiBold))
        self.new_text_button.setIcon(QIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder)))
        self.new_text_button.setStyleSheet(styles.secondary_button_style())
        self.new_text_button.clicked.connect(self.load_new_sample_text)
        row.addWidget(self.new_text_button)

        self.history_button = QPushButton("View History")
        self.history_button.setFont(styles.ui_font(12, QFont.Weight.DemiBold))
        self.history_button.setIcon(QIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView)))
        self.history_button.setStyleSheet(styles.secondary_button_style(min_width=120))
        self.history_button.clicked.connect(self.show_history_dialog)
        row.addWidget(self.history_button)

        row.addStretch()
        return row

    def start_practice(self) -> None:
        if not self.start_time:
            self.start_time = time.time()
            self.timer.start(1000)
            self.input_edit.setFocus()

    def reset_practice(self) -> None:
        self.start_time = None
        self.elapsed_time = 0
        self.is_done = False
        self.stats_worker.reset_stats()
        self.timer.stop()
        self.input_edit.clear()
        self.progress_bar.setValue(0)
        self.stats_updated.emit("0", "0%", "0s")

    def load_new_sample_text(self) -> None:
        self.sample_text = generate_mixed_text(length=self.text_length)
        self.text_label.setText(self.sample_text)
        self.reset_practice()

    def on_word_count_changed(self, text: str) -> None:
        self.text_length = int(text)
        self.load_new_sample_text()

    def update_time(self) -> None:
        if self.start_time:
            self.elapsed_time = time.time() - self.start_time
            self.stats_worker.record_sample()
            self.stats_updated.emit(self.last_wpm, self.last_accuracy, f"{int(self.elapsed_time)}s")

    def check_progress(self) -> None:
        typed_text = self.input_edit.toPlainText()
        self.text_updated.emit(typed_text)

        html = ""
        correct_count = 0
        for i, char in enumerate(self.sample_text):
            escaped_char = char.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if i < len(typed_text):
                if typed_text[i] == char:
                    html += f'<span style="color: {styles.SUCCESS};">{escaped_char}</span>'
                    correct_count += 1
                else:
                    html += f'<span style="color: {styles.DANGER};">{escaped_char}</span>'
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

        if len(typed_text) == len(self.sample_text) and typed_text == self.sample_text and not self.is_done:
            self.is_done = True
            self.timer.stop()
            self.stats_worker.record_sample()
            self.show_results_dialog()

    def update_stats(self, wpm: str, accuracy: str) -> None:
        if self.start_time is None:
            return
        elapsed_time = time.time() - self.start_time
        self.last_wpm = wpm
        self.last_accuracy = accuracy
        self.stats_updated.emit(f"{wpm}", f"{accuracy}", f"{int(elapsed_time)}s")

    def show_results_dialog(self) -> None:
        stats = self.stats_worker.get_final_stats()
        self.data_manager.save_session(stats, self.sample_text)
        self.data_manager.update_streaks()

        dialog = ResultsDialog(stats, self)
        result = dialog.exec()

        if result == QDialog.Accepted:
            self.reset_practice()
        elif result == NEW_TEXT_RESULT:
            self.load_new_sample_text()

    def show_history_dialog(self) -> None:
        sessions = self.data_manager.get_all_sessions()
        if not sessions:
            show_message(self, "No history found", "You have no typing history recorded.")
            return
        HistoryDialog(self.data_manager, self).exec()

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)
