"""A small dark-theme design system shared by FingerPunch's widgets.

A handful of neutral surfaces, one accent color, and a few semantic colors
(success/danger/warning) rather than a different saturated color per widget.
"""

from __future__ import annotations

from PySide6.QtGui import QFont

BG_WINDOW = "#18181b"
BG_SURFACE = "#212124"
BG_SURFACE_HOVER = "#2a2a2e"
BORDER = "#333338"
BORDER_STRONG = "#52525b"
TEXT_PRIMARY = "#f4f4f5"
TEXT_SECONDARY = "#a1a1aa"
TEXT_MUTED = "#71717a"


ACCENT = "#6366f1"
ACCENT_HOVER = "#4f46e5"
ACCENT_PRESSED = "#4338ca"
ACCENT_MUTED = "#312e81"


SUCCESS = "#22c55e"
DANGER = "#ef4444"
DANGER_HOVER = "#dc2626"
WARNING = "#f59e0b"

WINDOW_STYLE = f"background-color: {BG_WINDOW}; color: {TEXT_PRIMARY};"

_FONT_FAMILIES = ["Segoe UI", "Inter", "SF Pro Text", "Helvetica Neue", "Arial", "sans-serif"]


def ui_font(size: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """A QFont using a cross-platform fallback chain instead of a hardcoded family."""
    font = QFont()
    font.setFamilies(_FONT_FAMILIES)
    font.setPointSize(size)
    font.setWeight(weight)
    return font


def panel_style(border_color: str = BORDER, title_color: str = TEXT_SECONDARY) -> str:
    """A subtly-bordered content panel, replacing thick colored-border group boxes."""
    return f"""
        QGroupBox {{
            font-weight: 600;
            border: 1px solid {border_color};
            border-radius: 10px;
            margin-top: 14px;
            background-color: {BG_SURFACE};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 6px;
            color: {title_color};
            font-size: 11px;
        }}
    """


def primary_button_style(min_width: int = 100) -> str:
    return f"""
        QPushButton {{
            padding: 10px 22px;
            background-color: {ACCENT};
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            min-width: {min_width}px;
        }}
        QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
        QPushButton:pressed {{ background-color: {ACCENT_PRESSED}; }}
        QPushButton:disabled {{ background-color: {BORDER}; color: {TEXT_MUTED}; }}
    """


def secondary_button_style(min_width: int = 100) -> str:
    return f"""
        QPushButton {{
            padding: 10px 22px;
            background-color: transparent;
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_STRONG};
            border-radius: 8px;
            font-weight: 600;
            min-width: {min_width}px;
        }}
        QPushButton:hover {{ background-color: {BG_SURFACE_HOVER}; border-color: {ACCENT}; }}
        QPushButton:pressed {{ background-color: {BG_SURFACE}; }}
    """


def danger_button_style(min_width: int = 100) -> str:
    """A muted outline for reset/destructive actions, not a solid alarm-red fill."""
    return f"""
        QPushButton {{
            padding: 10px 22px;
            background-color: transparent;
            color: {DANGER};
            border: 1px solid {DANGER};
            border-radius: 8px;
            font-weight: 600;
            min-width: {min_width}px;
        }}
        QPushButton:hover {{ background-color: rgba(239, 68, 68, 0.12); }}
        QPushButton:pressed {{ background-color: rgba(239, 68, 68, 0.20); }}
    """


def text_surface_style(padding: int = 16, border_radius: int = 10) -> str:
    """Shared style for the large QTextEdit/QTextBrowser reading/typing surfaces."""
    return f"""
        QTextEdit, QTextBrowser {{
            border: 1px solid {BORDER};
            border-radius: {border_radius}px;
            padding: {padding}px;
            background-color: {BG_SURFACE};
            color: {TEXT_PRIMARY};
            selection-background-color: {ACCENT_MUTED};
        }}
        QTextEdit:focus, QTextBrowser:focus {{
            border: 1px solid {ACCENT};
        }}
        QScrollBar:vertical, QScrollBar:horizontal {{
            background: transparent;
            width: 0px;
            height: 0px;
        }}
    """


TEXT_BROWSER_COMPACT_STYLE = f"""
    QTextBrowser {{
        padding: 10px;
        color: {TEXT_PRIMARY};
        background-color: {BG_SURFACE};
        border-radius: 8px;
        border: 1px solid {BORDER};
    }}
"""

PROGRESS_BAR_STYLE = f"""
    QProgressBar {{
        border: none;
        border-radius: 4px;
        background-color: {BORDER};
        height: 8px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background-color: {ACCENT};
        border-radius: 4px;
    }}
"""


def combo_box_style(min_width: int = 120) -> str:
    return f"""
        QComboBox {{
            padding: 8px 12px;
            border: 1px solid {BORDER};
            border-radius: 8px;
            background-color: {BG_SURFACE};
            color: {TEXT_PRIMARY};
            min-width: {min_width}px;
        }}
        QComboBox:focus {{ border: 1px solid {ACCENT}; }}
        QComboBox::drop-down {{ border: none; }}
        QComboBox QAbstractItemView {{
            background-color: {BG_SURFACE};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
            selection-background-color: {ACCENT_MUTED};
        }}
    """


LABEL_CHIP_STYLE = f"""
    QLabel {{
        padding: 8px 12px;
        color: {TEXT_SECONDARY};
    }}
"""


def style_chart_background(figure, *axes) -> None:
    figure.patch.set_facecolor(BG_SURFACE)
    for ax in axes:
        ax.set_facecolor(BG_SURFACE)
        for spine in ax.spines.values():
            spine.set_color(BORDER)
        ax.grid(True, color=BORDER, alpha=0.4, linewidth=0.6)
        ax.title.set_color(TEXT_PRIMARY)


def style_chart_labels(ax) -> None:
    ax.tick_params(colors=TEXT_SECONDARY)
    ax.xaxis.label.set_color(TEXT_SECONDARY)
    ax.yaxis.label.set_color(TEXT_SECONDARY)


def style_chart_legend(legend) -> None:
    if legend is None:
        return
    legend.get_frame().set_facecolor(BG_SURFACE)
    legend.get_frame().set_edgecolor(BORDER)
    for text in legend.get_texts():
        text.set_color(TEXT_PRIMARY)
