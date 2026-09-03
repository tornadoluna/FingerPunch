from __future__ import annotations

from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from fingerpunch.data_manager import DataManager
from fingerpunch.ui import styles


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
        title.setStyleSheet(f"color: {styles.TEXT_PRIMARY}; margin-bottom: 4px;")
        layout.addWidget(title)

        sessions = self.data_manager.get_all_sessions()
        stats = self.data_manager.get_session_stats()
        if stats["total_sessions"] > 0:
            summary_text = (
                f"Total Sessions: {stats['total_sessions']} | "
                f"Best WPM: {stats['best_wpm']} | Best Accuracy: {stats['best_accuracy']}% | "
                f"Avg WPM: {stats['avg_wpm']} | Avg Accuracy: {stats['avg_accuracy']}%"
            )
            summary_label = QLabel(summary_text)
            summary_label.setFont(styles.ui_font(12))
            summary_label.setStyleSheet(
                f"color: {styles.ACCENT}; padding: 10px; "
                f"background-color: {styles.BG_SURFACE}; border-radius: 8px;"
            )
            summary_label.setWordWrap(True)
            layout.addWidget(summary_label)

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
        tab_widget.addTab(self._build_sessions_tab(sessions), "Sessions")
        tab_widget.addTab(self._build_analytics_tab(), "Analytics")
        tab_widget.addTab(self._build_progress_tab(), "Progress")
        layout.addWidget(tab_widget)

        close_button = QPushButton("Close")
        close_button.setFont(styles.ui_font(12, QFont.Weight.DemiBold))
        close_button.setStyleSheet(styles.secondary_button_style())
        close_button.clicked.connect(self.reject)
        layout.addWidget(close_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def _build_sessions_tab(self, sessions: list) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        history_list = QTextBrowser()
        history_list.setFont(styles.ui_font(12))
        history_list.setStyleSheet(styles.TEXT_BROWSER_COMPACT_STYLE)
        history_list.setReadOnly(True)
        history_list.setHtml(self._history_html(sessions))
        layout.addWidget(history_list)

        widget.setLayout(layout)
        return widget

    @staticmethod
    def _history_html(sessions: list) -> str:
        html = (
            "<style>"
            "table { width: 100%; border-collapse: collapse; font-size: 12px; }"
            f"th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid {styles.BORDER}; }}"
            f"th {{ color: {styles.TEXT_SECONDARY}; font-weight: 600; }}"
            f"tr:hover {{ background-color: {styles.BG_SURFACE_HOVER}; }}"
            "</style>"
        )
        html += "<table>"
        html += (
            "<tr><th>Date</th><th>Time</th><th>WPM</th><th>Accuracy</th>"
            "<th>Chars</th><th>Keystrokes</th><th>Efficiency</th></tr>"
        )
        for session in sessions:
            # session format: (id, date, wpm, accuracy, time_taken, total_chars, keystrokes, efficiency, text_length, sample_text)
            date_obj = datetime.fromisoformat(session[1])
            date_str = date_obj.strftime("%Y-%m-%d")
            time_str = date_obj.strftime("%H:%M")
            html += (
                f"<tr><td>{date_str}</td><td>{time_str}</td><td>{session[2]:.1f}</td>"
                f"<td>{session[3]:.1f}%</td><td>{session[5]}</td><td>{session[6]}</td>"
                f"<td>{session[7]:.1f}%</td></tr>"
            )
        html += "</table>"
        return html

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

            dates = [datetime.fromisoformat(session[1]) for session in sessions]
            wpms = [session[2] for session in sessions]
            accuracies = [session[3] for session in sessions]

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
                session for session in sessions if datetime.fromisoformat(session[1]) >= cutoff_date
            ]
            if not recent_sessions:
                return

            dates = [datetime.fromisoformat(session[1]) for session in recent_sessions]
            wpms = [session[2] for session in recent_sessions]
            accuracies = [session[3] for session in recent_sessions]

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

            lengths = [row[0] for row in length_data]
            avg_wpms = [row[1] for row in length_data]
            best_wpms = [row[2] for row in length_data]
            avg_accuracies = [row[3] for row in length_data]
            best_accuracies = [row[4] for row in length_data]

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
        bests_group.setStyleSheet(styles.panel_style(border_color=styles.SUCCESS, title_color=styles.SUCCESS))
        bests_layout = QVBoxLayout()
        bests_layout.setSpacing(10)
        self._build_personal_bests(bests_layout)
        bests_group.setLayout(bests_layout)
        layout.addWidget(bests_group)

        streaks_group = QGroupBox("STREAKS")
        streaks_group.setStyleSheet(styles.panel_style(border_color=styles.WARNING, title_color=styles.WARNING))
        streaks_layout = QVBoxLayout()
        streaks_layout.setSpacing(10)
        self._build_streaks(streaks_layout)
        streaks_group.setLayout(streaks_layout)
        layout.addWidget(streaks_group)

        widget.setLayout(layout)
        return widget

    def _build_personal_bests(self, layout: QVBoxLayout) -> None:
        bests = self.data_manager.get_personal_bests()
        if not bests:
            label = QLabel("No personal bests yet. Complete some sessions to generate personal bests.")
            label.setFont(styles.ui_font(12))
            label.setStyleSheet(f"color: {styles.TEXT_SECONDARY};")
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
            name_label.setStyleSheet(f"color: {styles.TEXT_PRIMARY};")

            if key in ("best_wpm", "best_accuracy", "best_efficiency"):
                value_text = f"{data['value']:.1f}"
            else:
                value_text = f"{data['value']}"

            value_label = QLabel(value_text)
            value_label.setFont(styles.ui_font(14, QFont.Weight.Bold))
            value_label.setStyleSheet(f"color: {styles.SUCCESS};")

            date_label = QLabel("")
            if data["date"]:
                date_obj = datetime.fromisoformat(data["date"])
                date_text = date_obj.strftime("%Y-%m-%d %H:%M")
                date_label = QLabel(f"({date_text})")
                date_label.setFont(styles.ui_font(10))
                date_label.setStyleSheet(f"color: {styles.TEXT_MUTED};")

            grid.addWidget(name_label, row, 0)
            grid.addWidget(value_label, row, 1)
            grid.addWidget(date_label, row, 2)
            row += 1

        if improvements and improvements["wpm_improvement"] != 0:
            separator = QLabel("")
            separator.setStyleSheet(f"border-top: 1px solid {styles.BORDER}; margin: 10px 0;")
            grid.addWidget(separator, row, 0, 1, 3)
            row += 1

            improvement_title = QLabel("Improvement Metrics:")
            improvement_title.setFont(styles.ui_font(12, QFont.Weight.Bold))
            improvement_title.setStyleSheet(f"color: {styles.TEXT_PRIMARY};")
            grid.addWidget(improvement_title, row, 0, 1, 3)
            row += 1

            wpm_color = styles.SUCCESS if improvements["wpm_improvement"] > 0 else styles.DANGER
            wpm_imp_label = QLabel(f"WPM Improvement: {improvements['wpm_improvement']:+.1f}")
            wpm_imp_label.setFont(styles.ui_font(11))
            wpm_imp_label.setStyleSheet(f"color: {wpm_color};")
            grid.addWidget(wpm_imp_label, row, 0, 1, 3)
            row += 1

            acc_color = styles.SUCCESS if improvements["accuracy_improvement"] > 0 else styles.DANGER
            acc_imp_label = QLabel(f"Accuracy Improvement: {improvements['accuracy_improvement']:+.1f}%")
            acc_imp_label.setFont(styles.ui_font(11))
            acc_imp_label.setStyleSheet(f"color: {acc_color};")
            grid.addWidget(acc_imp_label, row, 0, 1, 3)
            row += 1

            consistency_label = QLabel(f"Consistency Score: {improvements['consistency_score']:.1f}/100")
            consistency_label.setFont(styles.ui_font(11))
            consistency_label.setStyleSheet(f"color: {styles.ACCENT};")
            grid.addWidget(consistency_label, row, 0, 1, 3)

        layout.addLayout(grid)

    def _build_streaks(self, layout: QVBoxLayout) -> None:
        streak_info = self.data_manager.get_streak_info()
        if not streak_info:
            label = QLabel("No streaks recorded yet. Complete sessions to build your streak.")
            label.setFont(styles.ui_font(12))
            label.setStyleSheet(f"color: {styles.TEXT_SECONDARY};")
            label.setWordWrap(True)
            layout.addWidget(label)
            return

        current_streak_label = QLabel(f"Current Streak: {streak_info['current_streak']} days")
        current_streak_label.setFont(styles.ui_font(15, QFont.Weight.Bold))
        current_streak_label.setStyleSheet(f"color: {styles.WARNING}; margin-bottom: 8px;")
        layout.addWidget(current_streak_label)

        longest_streak_label = QLabel(f"Longest Streak: {streak_info['longest_streak']} days")
        longest_streak_label.setFont(styles.ui_font(13, QFont.Weight.Bold))
        longest_streak_label.setStyleSheet(f"color: {styles.TEXT_SECONDARY}; margin-bottom: 16px;")
        layout.addWidget(longest_streak_label)

        streak_history = self.data_manager.get_streak_history(14)
        if streak_history:
            history_text = "Recent Streak History:\n\n"
            for streak in streak_history[-7:]:
                date, sessions_count, current_streak = streak
                history_text += f"{date}: {sessions_count} sessions (streak: {current_streak})\n"

            history_browser = QTextBrowser()
            history_browser.setFont(styles.ui_font(12))
            history_browser.setStyleSheet(styles.TEXT_BROWSER_COMPACT_STYLE)
            history_browser.setPlainText(history_text)
            history_browser.setMaximumHeight(200)
            layout.addWidget(history_browser)

        motivation_label = QLabel("Keep practicing daily to build your streak!")
        motivation_label.setFont(styles.ui_font(12))
        motivation_label.setStyleSheet(f"color: {styles.TEXT_SECONDARY}; margin-top: 16px;")
        motivation_label.setWordWrap(True)
        layout.addWidget(motivation_label)
