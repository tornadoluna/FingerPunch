from __future__ import annotations

import logging
from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from fingerpunch.data_manager import DataManager, Session, StorageError
from fingerpunch.ui import styles
from fingerpunch.ui.widgets import confirm, show_message

logger = logging.getLogger(__name__)

SESSION_COLUMNS = ["Date", "Time", "WPM", "Accuracy", "Chars", "Keystrokes", "Efficiency"]


class HistoryDialog(QDialog):
    """Tabbed view of session history, performance analytics, and progress."""

    def __init__(self, data_manager: DataManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data_manager = data_manager
        self.setWindowTitle("Typing History")
        self.setModal(True)
        self.setStyleSheet(styles.WINDOW_STYLE)
        self.resize(850, 600)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Typing History")
        title.setFont(styles.ui_font(18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(styles.label_style(styles.TEXT_PRIMARY))
        layout.addWidget(title)

        self.summary_label = QLabel()
        self.summary_label.setFont(styles.ui_font(12))
        self.summary_label.setStyleSheet(
            f"QLabel {{ color: {styles.TEXT_SECONDARY}; padding: 10px;"
            f" background-color: {styles.BG_SURFACE}; border: 1px solid {styles.BORDER};"
            f" border-radius: 8px; }}"
        )
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        self._update_summary()

        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {styles.BORDER};
                border-radius: 8px;
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {styles.TEXT_SECONDARY};
                padding: 10px 18px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 12px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                color: {styles.TEXT_PRIMARY};
                border-bottom: 2px solid {styles.ACCENT};
            }}
            QTabBar::tab:hover:!selected {{
                color: {styles.TEXT_PRIMARY};
            }}
        """)
        self.tabs = tab_widget
        layout.addWidget(tab_widget)
        self._rebuild_tabs()

        close_button = QPushButton("Close")
        close_button.setFont(styles.ui_font(12, QFont.Weight.DemiBold))
        close_button.setStyleSheet(styles.secondary_button_style())
        close_button.clicked.connect(self.reject)
        layout.addWidget(close_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def _update_summary(self) -> None:
        stats = self.data_manager.get_session_stats()
        if stats["total_sessions"] == 0:
            self.summary_label.setText("")
            self.summary_label.hide()
            return

        self.summary_label.setText(
            f"Total Sessions: {stats['total_sessions']} | "
            f"Best WPM: {stats['best_wpm']} | Best Accuracy: {stats['best_accuracy']}% | "
            f"Avg WPM: {stats['avg_wpm']} | Avg Accuracy: {stats['avg_accuracy']}%"
        )
        self.summary_label.show()

    def _rebuild_tabs(self) -> None:
        current = max(self.tabs.currentIndex(), 0)
        while self.tabs.count():
            widget = self.tabs.widget(0)
            self.tabs.removeTab(0)
            widget.deleteLater()

        self.tabs.addTab(self._build_sessions_tab(), "Sessions")
        self.tabs.addTab(self._build_analytics_tab(), "Analytics")
        self.tabs.addTab(self._build_progress_tab(), "Progress")
        self.tabs.setCurrentIndex(min(current, self.tabs.count() - 1))

    def _build_sessions_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(len(SESSION_COLUMNS))
        self.sessions_table.setHorizontalHeaderLabels(SESSION_COLUMNS)
        self.sessions_table.setFont(styles.ui_font(12))
        self.sessions_table.setStyleSheet(styles.TABLE_STYLE)
        self.sessions_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sessions_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sessions_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sessions_table.verticalHeader().setVisible(False)
        self.sessions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sessions_table.itemSelectionChanged.connect(self._update_delete_button)
        layout.addWidget(self.sessions_table)

        self.delete_button = QPushButton("Delete Session")
        self.delete_button.setFont(styles.ui_font(12, QFont.Weight.DemiBold))
        self.delete_button.setStyleSheet(styles.danger_button_style())
        self.delete_button.clicked.connect(self._delete_selected_session)
        layout.addWidget(self.delete_button, alignment=Qt.AlignRight)

        self._populate_sessions_table()

        widget.setLayout(layout)
        return widget

    @staticmethod
    def _session_cells(session: Session) -> list[str]:
        date_obj = datetime.fromisoformat(session.date)
        return [
            date_obj.strftime("%Y-%m-%d"),
            date_obj.strftime("%H:%M"),
            f"{session.wpm:.1f}",
            f"{session.accuracy:.1f}%",
            f"{session.total_chars}",
            f"{session.keystrokes}",
            f"{session.efficiency:.1f}%",
        ]

    def _populate_sessions_table(self) -> None:
        sessions = self.data_manager.get_all_sessions()
        self.sessions_table.setRowCount(len(sessions))
        for row, session in enumerate(sessions):
            for column, text in enumerate(self._session_cells(session)):
                item = QTableWidgetItem(text)
                if column == 0:
                    item.setData(Qt.UserRole, session.id)
                self.sessions_table.setItem(row, column, item)
        self._update_delete_button()

    def _selected_session_id(self) -> int | None:
        row = self.sessions_table.currentRow()
        if row < 0 or not self.sessions_table.selectionModel().hasSelection():
            return None
        item = self.sessions_table.item(row, 0)
        return None if item is None else item.data(Qt.UserRole)

    def _update_delete_button(self) -> None:
        self.delete_button.setEnabled(self._selected_session_id() is not None)

    def _delete_selected_session(self) -> None:
        session_id = self._selected_session_id()
        if session_id is None:
            return

        if not confirm(self, "Delete session", "Delete this session? This cannot be undone."):
            return

        try:
            self.data_manager.delete_session(session_id)
            self.data_manager.update_streaks()
        except StorageError:
            logger.exception("Could not delete session %s", session_id)
            show_message(
                self,
                "Session not deleted",
                "That session could not be removed. Check the log for details.",
            )
            return

        logger.info("Deleted session %s", session_id)
        self._update_summary()
        self._rebuild_tabs()

    def _build_analytics_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Chart Type:"))

        self.chart_combo = QComboBox()
        self.chart_combo.addItems(["Performance Overview", "Recent Activity", "Performance by Length"])
        self.chart_combo.setStyleSheet(styles.combo_box_style(min_width=200))
        self.chart_combo.currentTextChanged.connect(self._update_analytics_chart)
        selector_row.addWidget(self.chart_combo)
        selector_row.addStretch()
        layout.addLayout(selector_row)

        self.analytics_canvas = FigureCanvas(Figure(figsize=(12, 7)))
        layout.addWidget(self.analytics_canvas)

        self._update_analytics_chart("Performance Overview")

        widget.setLayout(layout)
        return widget

    def _style_dark_background(self, *axes) -> None:
        styles.style_chart_background(self.analytics_canvas.figure, *axes)

    def _style_legend(self, legend) -> None:
        styles.style_chart_legend(legend)

    def _update_analytics_chart(self, chart_type: str) -> None:
        self.analytics_canvas.figure.clear()

        if chart_type == "Performance Overview":
            sessions = self.data_manager.get_all_sessions()
            if not sessions:
                return

            dates = [datetime.fromisoformat(session.date) for session in sessions]
            wpms = [session.wpm for session in sessions]
            accuracies = [session.accuracy for session in sessions]

            ax = self.analytics_canvas.figure.add_subplot(111)
            ax.plot(dates, wpms, label="WPM", color=styles.SUCCESS, marker="o")
            ax.plot(dates, accuracies, label="Accuracy", color=styles.ACCENT, marker="o")

            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
            ax.xaxis.set_major_locator(mdates.DayLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

            ax.set_xlabel("Date")
            ax.set_ylabel("WPM / Accuracy")
            ax.set_title("Typing Performance Over Time")
            self._style_dark_background(ax)
            ax.tick_params(colors=styles.TEXT_SECONDARY)
            ax.xaxis.label.set_color(styles.TEXT_SECONDARY)
            ax.yaxis.label.set_color(styles.TEXT_SECONDARY)
            self._style_legend(ax.legend())

        elif chart_type == "Recent Activity":
            sessions = self.data_manager.get_all_sessions()
            if not sessions:
                return

            cutoff_date = datetime.now() - timedelta(days=30)
            recent_sessions = [
                session for session in sessions if datetime.fromisoformat(session.date) >= cutoff_date
            ]
            if not recent_sessions:
                return

            dates = [datetime.fromisoformat(session.date) for session in recent_sessions]
            wpms = [session.wpm for session in recent_sessions]
            accuracies = [session.accuracy for session in recent_sessions]

            ax = self.analytics_canvas.figure.add_subplot(111)
            ax.plot(dates, wpms, label="WPM", color=styles.SUCCESS, marker="o")
            ax.plot(dates, accuracies, label="Accuracy", color=styles.ACCENT, marker="o")

            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

            ax.set_xlabel("Date")
            ax.set_ylabel("WPM / Accuracy")
            ax.set_title("Typing Activity - Last 30 Days")
            self._style_dark_background(ax)
            ax.tick_params(colors=styles.TEXT_SECONDARY)
            ax.xaxis.label.set_color(styles.TEXT_SECONDARY)
            ax.yaxis.label.set_color(styles.TEXT_SECONDARY)
            self._style_legend(ax.legend())

        elif chart_type == "Performance by Length":
            length_data = self.data_manager.get_performance_by_length()
            if not length_data:
                return

            lengths = [row.text_length for row in length_data]
            avg_wpms = [row.avg_wpm for row in length_data]
            best_wpms = [row.best_wpm for row in length_data]
            avg_accuracies = [row.avg_accuracy for row in length_data]
            best_accuracies = [row.best_accuracy for row in length_data]

            ax1 = self.analytics_canvas.figure.add_subplot(111)

            x = list(range(len(lengths)))
            width = 0.35

            ax1.bar([i - width / 2 for i in x], avg_wpms, width, label="Avg WPM", color=styles.SUCCESS, alpha=0.7)
            ax1.bar([i + width / 2 for i in x], best_wpms, width, label="Best WPM", color="#66BB6A", alpha=0.7)
            ax1.set_xlabel("Text Length (words)")
            ax1.set_ylabel("WPM", color=styles.SUCCESS)
            ax1.tick_params(axis="y", labelcolor=styles.SUCCESS)

            ax2 = ax1.twinx()
            ax2.plot(x, avg_accuracies, "o-", label="Avg Accuracy", color=styles.ACCENT, linewidth=2, markersize=6)
            ax2.plot(x, best_accuracies, "s-", label="Best Accuracy", color="#818CF8", linewidth=2, markersize=6)
            ax2.set_ylabel("Accuracy (%)", color=styles.ACCENT)
            ax2.tick_params(axis="y", labelcolor=styles.ACCENT)

            ax1.set_xticks(x)
            ax1.set_xticklabels(lengths)
            ax1.set_title("Typing Performance by Text Length")

            self._style_dark_background(ax1, ax2)
            ax1.tick_params(axis="x", colors=styles.TEXT_SECONDARY)
            ax1.xaxis.label.set_color(styles.TEXT_SECONDARY)
            ax2.grid(False)  # avoid a doubled grid from the twin axis

            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            self._style_legend(ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left"))

        self.analytics_canvas.draw()

    def _build_progress_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        bests_group = QGroupBox("PERSONAL BESTS")
        bests_group.setFont(styles.ui_font(11, QFont.Weight.DemiBold))
        bests_group.setStyleSheet(styles.panel_style())
        bests_layout = QVBoxLayout()
        bests_layout.setSpacing(10)
        self._build_personal_bests(bests_layout)
        bests_group.setLayout(bests_layout)
        layout.addWidget(bests_group)

        streaks_group = QGroupBox("STREAKS")
        streaks_group.setFont(styles.ui_font(11, QFont.Weight.DemiBold))
        streaks_group.setStyleSheet(styles.panel_style())
        streaks_layout = QVBoxLayout()
        streaks_layout.setSpacing(10)
        self._build_streaks(streaks_layout)
        streaks_group.setLayout(streaks_layout)
        layout.addWidget(streaks_group)

        widget.setLayout(layout)
        return widget

    def _build_personal_bests(self, layout: QVBoxLayout) -> None:
        bests = self.data_manager.get_personal_bests()
        if not any(best["date"] for best in bests.values()):
            label = QLabel("No personal bests yet. Complete some sessions to generate personal bests.")
            label.setFont(styles.ui_font(12))
            label.setStyleSheet(styles.label_style())
            label.setWordWrap(True)
            layout.addWidget(label)
            return

        improvements = self.data_manager.get_improvement_metrics()

        grid = QGridLayout()
        grid.setSpacing(10)

        display_names = {
            "best_wpm": "Best WPM",
            "best_accuracy": "Best Accuracy",
            "best_efficiency": "Best Efficiency",
            "most_chars": "Most Characters",
        }

        row = 0
        for key, data in bests.items():
            display_name = display_names.get(key, key.replace("_", " ").title())

            name_label = QLabel(f"{display_name}:")
            name_label.setFont(styles.ui_font(12, QFont.Weight.Bold))
            name_label.setStyleSheet(styles.label_style(styles.TEXT_PRIMARY))

            if key in ("best_wpm", "best_accuracy", "best_efficiency"):
                value_text = f"{data['value']:.1f}"
            else:
                value_text = f"{data['value']}"

            value_label = QLabel(value_text)
            value_label.setFont(styles.ui_font(14, QFont.Weight.Bold))
            value_label.setStyleSheet(styles.label_style(styles.ACCENT))

            date_label = QLabel("")
            if data["date"]:
                date_obj = datetime.fromisoformat(data["date"])
                date_text = date_obj.strftime("%Y-%m-%d %H:%M")
                date_label = QLabel(f"({date_text})")
                date_label.setFont(styles.ui_font(10))
                date_label.setStyleSheet(styles.label_style(styles.TEXT_MUTED))

            grid.addWidget(name_label, row, 0)
            grid.addWidget(value_label, row, 1)
            grid.addWidget(date_label, row, 2)
            row += 1

        if improvements and improvements["wpm_improvement"] != 0:
            separator = QLabel("")
            separator.setStyleSheet(f"border-top: 1px solid {styles.BORDER}; margin: 10px 0; background: transparent;")
            grid.addWidget(separator, row, 0, 1, 3)
            row += 1

            improvement_title = QLabel("Improvement Metrics:")
            improvement_title.setFont(styles.ui_font(12, QFont.Weight.Bold))
            improvement_title.setStyleSheet(styles.label_style(styles.TEXT_PRIMARY))
            grid.addWidget(improvement_title, row, 0, 1, 3)
            row += 1

            wpm_color = styles.SUCCESS if improvements["wpm_improvement"] > 0 else styles.DANGER
            wpm_imp_label = QLabel(f"WPM Improvement: {improvements['wpm_improvement']:+.1f}")
            wpm_imp_label.setFont(styles.ui_font(11))
            wpm_imp_label.setStyleSheet(styles.label_style(wpm_color))
            grid.addWidget(wpm_imp_label, row, 0, 1, 3)
            row += 1

            acc_color = styles.SUCCESS if improvements["accuracy_improvement"] > 0 else styles.DANGER
            acc_imp_label = QLabel(f"Accuracy Improvement: {improvements['accuracy_improvement']:+.1f}%")
            acc_imp_label.setFont(styles.ui_font(11))
            acc_imp_label.setStyleSheet(styles.label_style(acc_color))
            grid.addWidget(acc_imp_label, row, 0, 1, 3)
            row += 1

            consistency_label = QLabel(f"Consistency Score: {improvements['consistency_score']:.1f}/100")
            consistency_label.setFont(styles.ui_font(11))
            consistency_label.setStyleSheet(styles.label_style(styles.TEXT_SECONDARY))
            grid.addWidget(consistency_label, row, 0, 1, 3)

        layout.addLayout(grid)

    def _build_streaks(self, layout: QVBoxLayout) -> None:
        streak_info = self.data_manager.get_streak_info()
        if not streak_info:
            label = QLabel("No streaks recorded yet. Complete sessions to build your streak.")
            label.setFont(styles.ui_font(12))
            label.setStyleSheet(styles.label_style())
            label.setWordWrap(True)
            layout.addWidget(label)
            return

        current_streak_label = QLabel(f"Current Streak: {streak_info['current_streak']} days")
        current_streak_label.setFont(styles.ui_font(15, QFont.Weight.Bold))
        current_streak_label.setStyleSheet(styles.label_style(styles.ACCENT))
        layout.addWidget(current_streak_label)

        longest_streak_label = QLabel(f"Longest Streak: {streak_info['longest_streak']} days")
        longest_streak_label.setFont(styles.ui_font(13, QFont.Weight.Bold))
        longest_streak_label.setStyleSheet(styles.label_style())
        layout.addWidget(longest_streak_label)

        streak_history = self.data_manager.get_streak_history(14)
        if streak_history:
            history_text = "Recent Streak History:\n\n"
            for streak in streak_history[-7:]:
                history_text += (
                    f"{streak.date}: {streak.sessions_count} sessions"
                    f" (streak: {streak.current_streak})\n"
                )

            history_browser = QTextBrowser()
            history_browser.setFont(styles.ui_font(12))
            history_browser.setStyleSheet(styles.TEXT_BROWSER_COMPACT_STYLE)
            history_browser.setPlainText(history_text)
            lines = history_text.count("\n") + 1
            history_browser.setFixedHeight(min(200, 34 + lines * 20))
            layout.addWidget(history_browser)

        motivation_label = QLabel("Keep practicing daily to build your streak!")
        motivation_label.setFont(styles.ui_font(12))
        motivation_label.setStyleSheet(styles.label_style(styles.TEXT_MUTED))
        motivation_label.setWordWrap(True)
        layout.addWidget(motivation_label)
