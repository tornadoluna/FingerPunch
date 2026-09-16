from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from fingerpunch.camera.image import frame_to_image
from fingerpunch.camera.source import Frame
from fingerpunch.camera.worker import CameraController
from fingerpunch.ui import styles

logger = logging.getLogger(__name__)

PREVIEW_WIDTH = 320
PREVIEW_HEIGHT = 180
OFF_MESSAGE = "Camera off"
STARTING_MESSAGE = "Starting the camera..."
LIVE_MESSAGE = "Camera live"


class CameraPanel(QGroupBox):
    frame_ready = Signal(object)

    def __init__(
        self,
        controller_factory: Callable[[], CameraController] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("CAMERA", parent)
        if controller_factory is None:
            controller_factory = CameraController
        self.setFont(styles.ui_font(11, QFont.Weight.DemiBold))
        self.setStyleSheet(styles.panel_style())

        self._controller = controller_factory()
        self._controller.frame_ready.connect(self._on_frame)
        self._controller.failed.connect(self._on_failed)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(10)
        layout.addLayout(self._build_controls())

        self.preview = QLabel()
        self.preview.setFixedSize(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet(styles.text_surface_style())
        self.preview.hide()
        layout.addWidget(self.preview, alignment=Qt.AlignLeft)

        self.setLayout(layout)

    def _build_controls(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)

        self.toggle = QPushButton("Enable Camera")
        self.toggle.setCheckable(True)
        self.toggle.setFont(styles.ui_font(12, QFont.Weight.DemiBold))
        self.toggle.setStyleSheet(styles.secondary_button_style(min_width=140))
        self.toggle.toggled.connect(self._on_toggled)
        row.addWidget(self.toggle)

        self.status = QLabel(OFF_MESSAGE)
        self.status.setFont(styles.ui_font(11))
        self.status.setStyleSheet(f"color: {styles.TEXT_MUTED};")
        self.status.setWordWrap(True)
        self.status.setMinimumWidth(320)
        row.addWidget(self.status)
        row.addStretch()
        return row

    @property
    def is_enabled(self) -> bool:
        return self.toggle.isChecked()

    def _on_toggled(self, enabled: bool) -> None:
        if enabled:
            self.toggle.setText("Disable Camera")
            self._set_status(STARTING_MESSAGE, styles.TEXT_SECONDARY)
            self.preview.show()
            self._controller.start()
        else:
            self._controller.stop()
            self.toggle.setText("Enable Camera")
            self._set_status(OFF_MESSAGE, styles.TEXT_MUTED)
            self.preview.clear()
            self.preview.hide()

    def _on_frame(self, frame: Frame) -> None:
        if not self.toggle.isChecked():
            return

        if self.status.text() != LIVE_MESSAGE:
            self._set_status(LIVE_MESSAGE, styles.SUCCESS)

        pixmap = QPixmap.fromImage(frame_to_image(frame))
        self.preview.setPixmap(
            pixmap.scaled(
                self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        self.frame_ready.emit(frame)

    def _on_failed(self, message: str) -> None:
        logger.warning("Camera unavailable: %s", message)
        self._controller.stop()
        self.toggle.blockSignals(True)
        self.toggle.setChecked(False)
        self.toggle.setText("Enable Camera")
        self.toggle.blockSignals(False)
        self.preview.clear()
        self.preview.hide()
        self._set_status(message, styles.DANGER)

    def _set_status(self, message: str, color: str) -> None:
        self.status.setText(message)
        self.status.setStyleSheet(f"color: {color};")

    def shutdown(self) -> None:
        self._controller.stop()
