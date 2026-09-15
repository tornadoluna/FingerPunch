from __future__ import annotations

from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import QTextEdit, QWidget


class TypingInput(QTextEdit):
    """A text area that accepts typing but refuses pasted and dropped text."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(False)

    def canInsertFromMimeData(self, source: QMimeData) -> bool:
        return False

    def insertFromMimeData(self, source: QMimeData) -> None:
        return
