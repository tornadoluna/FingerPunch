from __future__ import annotations

import logging
import time

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import (
    QCloseEvent,
    QColor,
    QFont,
    QIcon,
    QTextCharFormat,
    QTextCursor,
)
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
    QVBoxLayout,
    QWidget,
)

from fingerpunch.data_manager import DataManager, StorageError
from fingerpunch.stats import StatsWorker
from fingerpunch.text_diff import dirty_range
from fingerpunch.text_generator import generate_mixed_text
from fingerpunch.ui import styles
from fingerpunch.ui.history_dialog import HistoryDialog
from fingerpunch.ui.results_dialog import NEW_TEXT_RESULT, ResultsDialog
from fingerpunch.ui.widgets import TypingInput, show_message

logger = logging.getLogger(__name__)


def _character_format(color: str | None) -> QTextCharFormat:
    text_format = QTextCharFormat()
    text_format.setForeground(QColor(color) if color else QColor(styles.TEXT_PRIMARY))
    return text_format


_CHARACTER_FORMATS = {
    "untyped": _character_format(None),
    "correct": _character_format(styles.SUCCESS),
    "incorrect": _character_format(styles.DANGER),
}


class TypingPracticeApp(QWidget):
    stats_updated = Signal(str, str, str)
    text_updated = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.text_length: int = 50
        self._sample_text: str = generate_mixed_text(length=50)
        self._highlighted: str = ""
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

    @property
    def sample_text(self) -> str:
        return self._sample_text

    @sample_text.setter
    def sample_text(self, text: str) -> None:
        self._sample_text = text
        self._highlighted = ""
        self.text_label.setPlainText(text)

    def _build_sample_group(self) -> QGroupBox:
        group = QGroupBox("SAMPLE TEXT")
        group.setFont(styles.ui_font(11, QFont.Weight.DemiBold))
        group.setStyleSheet(styles.panel_style())

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 20, 16, 16)

        self.text_label = QTextBrowser()
        self.text_label.setPlainText(self._sample_text)
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

        self.input_edit = TypingInput()
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

        self._repaint_sample(typed_text)
        self._highlighted = typed_text
        correct_count = self.stats_worker.correct_chars

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

    def _character_state(self, index: int, typed_text: str) -> str:
        if index >= len(typed_text):
            return "untyped"
        return "correct" if typed_text[index] == self.sample_text[index] else "incorrect"

    def _repaint_sample(self, typed_text: str) -> None:
        sample = self.sample_text
        previous = self._highlighted

        start, end = dirty_range(previous, typed_text, len(sample))

        if start < end:
            cursor = QTextCursor(self.text_label.document())
            run_start = start
            while run_start < end:
                state = self._character_state(run_start, typed_text)
                run_end = run_start + 1
                while run_end < end and self._character_state(run_end, typed_text) == state:
                    run_end += 1
                cursor.setPosition(run_start)
                cursor.setPosition(run_end, QTextCursor.KeepAnchor)
                cursor.setCharFormat(_CHARACTER_FORMATS[state])
                run_start = run_end

    def update_stats(self, wpm: str, accuracy: str) -> None:
        if self.start_time is None:
            return
        elapsed_time = time.time() - self.start_time
        self.last_wpm = wpm
        self.last_accuracy = accuracy
        self.stats_updated.emit(f"{wpm}", f"{accuracy}", f"{int(elapsed_time)}s")

    def show_results_dialog(self) -> None:
        stats = self.stats_worker.get_final_stats()
        try:
            self.data_manager.save_session(stats, self.sample_text)
            self.data_manager.update_streaks()
        except StorageError:
            logger.exception("Could not save the finished session")
            show_message(
                self,
                "Session not saved",
                "Your results are shown below, but they could not be written to the"
                " database. Check the log for details.",
            )
        else:
            logger.info(
                "Session finished: %.1f wpm, %.1f%% accuracy", stats["wpm"], stats["accuracy"]
            )

        dialog = ResultsDialog(stats, self)
        result = dialog.exec()

        if result == QDialog.Accepted:
            self.reset_practice()
        elif result == NEW_TEXT_RESULT:
            self.load_new_sample_text()

    def show_history_dialog(self) -> None:
        try:
            sessions = self.data_manager.get_all_sessions()
        except StorageError:
            logger.exception("Could not read the session history")
            show_message(
                self,
                "History unavailable",
                "Your typing history could not be read. Check the log for details.",
            )
            return

        if not sessions:
            show_message(self, "No history found", "You have no typing history recorded.")
            return

        try:
            HistoryDialog(self.data_manager, self).exec()
        except StorageError:
            logger.exception("Could not build the history dialog")
            show_message(
                self,
                "History unavailable",
                "Your typing history could not be read. Check the log for details.",
            )

    def closeEvent(self, event: QCloseEvent) -> None:
        self.timer.stop()
        logger.info("Shutting down")
        super().closeEvent(event)
