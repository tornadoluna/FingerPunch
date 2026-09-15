from __future__ import annotations

from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from fingerpunch.ui import styles


class TypingInput(QTextEdit):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(False)

    def canInsertFromMimeData(self, source: QMimeData) -> bool:
        return False

    def insertFromMimeData(self, source: QMimeData) -> None:
        return


def _message_dialog(parent: QWidget, title: str, message: str) -> tuple[QDialog, QVBoxLayout]:
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

    return dialog, layout


def show_message(parent: QWidget, title: str, message: str) -> None:
    """A simple modal message box, styled to match the app."""
    dialog, layout = _message_dialog(parent, title, message)

    close_button = QPushButton("Close")
    close_button.setFont(styles.ui_font(12, QFont.Weight.DemiBold))
    close_button.setStyleSheet(styles.secondary_button_style())
    close_button.clicked.connect(dialog.reject)
    layout.addWidget(close_button, alignment=Qt.AlignCenter)

    dialog.setLayout(layout)
    dialog.exec()


def confirm(parent: QWidget, title: str, message: str, confirm_label: str = "Delete") -> bool:
    dialog, layout = _message_dialog(parent, title, message)

    buttons = QHBoxLayout()
    buttons.setSpacing(12)

    cancel_button = QPushButton("Cancel")
    cancel_button.setFont(styles.ui_font(12, QFont.Weight.DemiBold))
    cancel_button.setStyleSheet(styles.secondary_button_style())
    cancel_button.setDefault(True)
    cancel_button.clicked.connect(dialog.reject)
    buttons.addWidget(cancel_button)

    confirm_button = QPushButton(confirm_label)
    confirm_button.setFont(styles.ui_font(12, QFont.Weight.DemiBold))
    confirm_button.setStyleSheet(styles.danger_button_style())
    confirm_button.clicked.connect(dialog.accept)
    buttons.addWidget(confirm_button)

    layout.addLayout(buttons)
    dialog.setLayout(layout)
    return dialog.exec() == QDialog.Accepted
