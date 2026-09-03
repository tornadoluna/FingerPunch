from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

import styles
from statsWorker import StatsDict

NEW_TEXT_RESULT = 2
MIN_SAMPLES_FOR_CHART = 2


class ResultsDialog(QDialog):
    def __init__(self, stats: StatsDict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.stats = stats
        self.setWindowTitle("Typing Session Complete!")
        self.setModal(True)
        self.setStyleSheet(styles.WINDOW_STYLE)
        self.resize(560, 640 if self._has_chart() else 420)
        self._init_ui()

    def _has_chart(self) -> bool:
        return len(self.stats.get("samples", [])) >= MIN_SAMPLES_FOR_CHART

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)

        title = QLabel("Session Complete")
        title.setFont(styles.ui_font(20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {styles.TEXT_PRIMARY};")
        layout.addWidget(title)

        if self._has_chart():
            layout.addWidget(self._build_chart())

        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(14)

        primary_stats = [
            ("Words Per Minute", f"{self.stats['wpm']:.1f} WPM"),
            ("Accuracy", f"{self.stats['accuracy']:.1f}%"),
            ("Time Taken", f"{self.stats['time']:.1f}s"),
        ]
        for label, value in primary_stats:
            stats_layout.addLayout(self._stat_row(label, value, 14, styles.TEXT_PRIMARY))

        separator = QLabel("")
        separator.setStyleSheet(f"border-top: 1px solid {styles.BORDER}; margin: 6px 0;")
        stats_layout.addWidget(separator)

        detailed_stats = [
            ("Characters Typed", f"{self.stats['total_chars']}"),
            ("Total Keystrokes", f"{self.stats['keystrokes']}"),
            ("Typing Efficiency", f"{self.stats['efficiency']:.1f}%"),
        ]
        for label, value in detailed_stats:
            stats_layout.addLayout(self._stat_row(label, value, 12, styles.TEXT_SECONDARY))

        layout.addLayout(stats_layout)

        performance_msg = self._performance_message()
        msg_label = QLabel(performance_msg)
        msg_label.setFont(styles.ui_font(12))
        msg_label.setStyleSheet(
            f"color: {styles.ACCENT}; padding: 12px; "
            f"background-color: {styles.BG_SURFACE}; border-radius: 8px;"
        )
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)

        button_box = QDialogButtonBox()
        retry_button = button_box.addButton("Try Again", QDialogButtonBox.ButtonRole.AcceptRole)
        new_text_button = button_box.addButton("New Text", QDialogButtonBox.ButtonRole.ActionRole)
        close_button = button_box.addButton("Close", QDialogButtonBox.ButtonRole.RejectRole)
        retry_button.setStyleSheet(styles.primary_button_style(min_width=90))
        new_text_button.setStyleSheet(styles.secondary_button_style(min_width=90))
        close_button.setStyleSheet(styles.secondary_button_style(min_width=90))

        retry_button.clicked.connect(self.accept)
        new_text_button.clicked.connect(self.new_text)
        close_button.clicked.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def _build_chart(self) -> FigureCanvas:
        samples = self.stats["samples"]
        canvas = FigureCanvas(Figure(figsize=(6, 3.0)))
        canvas.setMinimumHeight(215)
        ax = canvas.figure.add_subplot(111)

        times = [s["t"] for s in samples]
        wpms = [s["wpm"] for s in samples]
        raw_wpms = [s["raw_wpm"] for s in samples]

        ax.plot(times, raw_wpms, label="Raw", color=styles.TEXT_MUTED, linestyle="--", linewidth=1.2)
        ax.plot(times, wpms, label="WPM", color=styles.ACCENT, linewidth=2)

        error_times = []
        error_values = []
        previous_errors = 0
        for sample in samples:
            if sample["errors"] > previous_errors:
                error_times.append(sample["t"])
                error_values.append(sample["wpm"])
            previous_errors = sample["errors"]
        if error_times:
            ax.scatter(error_times, error_values, color=styles.DANGER, s=28, zorder=5, label="Errors")

        ax.set_xlabel("Seconds")
        ax.set_ylabel("WPM")
        ax.set_ylim(bottom=0)

        styles.style_chart_background(canvas.figure, ax)
        styles.style_chart_labels(ax)
        styles.style_chart_legend(ax.legend(loc="upper left", fontsize=7, framealpha=0.85))
        canvas.figure.tight_layout(pad=1.4)
        return canvas

    def _stat_row(self, label: str, value: str, size: int, value_color: str) -> QHBoxLayout:
        row = QHBoxLayout()
        label_widget = QLabel(f"{label}:")
        label_widget.setFont(styles.ui_font(size))
        label_widget.setStyleSheet(f"color: {styles.TEXT_SECONDARY};")
        label_widget.setMinimumWidth(150)

        value_widget = QLabel(value)
        value_widget.setFont(styles.ui_font(size, QFont.Weight.Bold))
        value_widget.setStyleSheet(f"color: {value_color};")
        value_widget.setAlignment(Qt.AlignRight)

        row.addWidget(label_widget)
        row.addWidget(value_widget)
        return row

    def _performance_message(self) -> str:
        wpm = self.stats["wpm"]
        accuracy = self.stats["accuracy"]

        if accuracy >= 98 and wpm >= 60:
            return "Excellent! You're a typing master."
        elif accuracy >= 95 and wpm >= 40:
            return "Great job! Keep practicing to improve your speed."
        elif accuracy >= 90:
            return "Good work! Focus on accuracy and speed will follow."
        elif accuracy >= 80:
            return "Keep practicing! Accuracy is the foundation of good typing."
        else:
            return "Don't give up! Every expert was once a beginner."

    def new_text(self) -> None:
        self.done(NEW_TEXT_RESULT)
