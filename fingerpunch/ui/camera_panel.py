from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from fingerpunch.camera.devices import (
    RESOLUTION_CHOICES,
    SettingsStore,
    probe_devices,
    remember_device_index,
    remember_resolution,
    saved_device_index,
    saved_resolution,
)
from fingerpunch.camera.image import frame_to_image
from fingerpunch.camera.source import Frame, OpenCVCamera
from fingerpunch.camera.worker import CameraController
from fingerpunch.ui import styles

logger = logging.getLogger(__name__)


def _default_controller_factory(
    device_index: int, resolution: tuple[int, int]
) -> CameraController:
    return CameraController(source_factory=lambda: OpenCVCamera(device_index, resolution))

PREVIEW_WIDTH = 288
PREVIEW_HEIGHT = 162
OFF_MESSAGE = "Camera off"
STARTING_MESSAGE = "Starting the camera..."
LIVE_MESSAGE = "Camera live"
NO_DEVICES_MESSAGE = "No cameras detected"


class CameraPanel(QGroupBox):
    frame_ready = Signal(object)

    def __init__(
        self,
        settings: SettingsStore | None = None,
        controller_factory: Callable[[int, tuple[int, int]], CameraController] | None = None,
        probe: Callable[[], list[int]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("CAMERA", parent)
        self._settings = settings
        self._probe = probe if probe is not None else probe_devices
        if controller_factory is None:
            controller_factory = _default_controller_factory
        self._controller_factory = controller_factory
        self.device_index = saved_device_index(settings)
        self.resolution = saved_resolution(settings)
        self.setFont(styles.ui_font(11, QFont.Weight.DemiBold))
        self.setStyleSheet(styles.panel_style())

        self._controller = self._controller_factory(self.device_index, self.resolution)
        self._controller.frame_ready.connect(self._on_frame)
        self._controller.failed.connect(self._on_failed)

        self.preview = QLabel()
        self.preview.setFixedSize(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet(
            f"QLabel {{ border: 1px solid {styles.BORDER}; border-radius: 10px;"
            f" background-color: {styles.BG_WINDOW}; }}"
        )
        self.preview.hide()

        controls = self._build_controls()
        controls.addStretch()

        layout = QHBoxLayout()
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(self.preview, alignment=Qt.AlignTop)
        layout.addLayout(controls, stretch=1)

        self.setLayout(layout)

    def _build_controls(self) -> QVBoxLayout:
        column = QVBoxLayout()
        column.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(12)

        self.toggle = QPushButton("Enable Camera")
        self.toggle.setCheckable(True)
        self.toggle.setFont(styles.ui_font(12, QFont.Weight.DemiBold))
        self.toggle.setStyleSheet(styles.secondary_button_style(min_width=150))
        self.toggle.toggled.connect(self._on_toggled)
        top.addWidget(self.toggle)

        self.status = QLabel(OFF_MESSAGE)
        self.status.setFont(styles.ui_font(11))
        self.status.setStyleSheet(styles.label_style(styles.TEXT_MUTED))
        self.status.setWordWrap(True)
        top.addWidget(self.status, stretch=1)
        column.addLayout(top)

        device_row = QHBoxLayout()
        device_row.setSpacing(8)
        device_row.addWidget(self._field_label("Device", width=72))

        self.device_combo = QComboBox()
        self.device_combo.setFont(styles.ui_font(12))
        self.device_combo.setStyleSheet(styles.combo_box_style(min_width=180))
        self.device_combo.addItem(f"Camera {self.device_index}", self.device_index)
        self.device_combo.currentIndexChanged.connect(self._on_device_changed)
        device_row.addWidget(self.device_combo, stretch=1)

        self.detect_button = QPushButton("Detect")
        self.detect_button.setFont(styles.ui_font(12, QFont.Weight.DemiBold))
        self.detect_button.setStyleSheet(styles.secondary_button_style(min_width=80))
        self.detect_button.clicked.connect(self.detect_devices)
        device_row.addWidget(self.detect_button)
        column.addLayout(device_row)

        resolution_row = QHBoxLayout()
        resolution_row.setSpacing(8)
        resolution_row.addWidget(self._field_label("Resolution", width=72))

        self.resolution_combo = QComboBox()
        self.resolution_combo.setFont(styles.ui_font(12))
        self.resolution_combo.setStyleSheet(styles.combo_box_style(min_width=140))
        for choice in RESOLUTION_CHOICES:
            self.resolution_combo.addItem(f"{choice[0]}x{choice[1]}", choice)
        if self.resolution in RESOLUTION_CHOICES:
            self.resolution_combo.setCurrentIndex(RESOLUTION_CHOICES.index(self.resolution))
        self.resolution_combo.currentIndexChanged.connect(self._on_resolution_changed)
        resolution_row.addWidget(self.resolution_combo)
        resolution_row.addStretch()
        column.addLayout(resolution_row)

        return column

    @staticmethod
    def _field_label(text: str, width: int = 0) -> QLabel:
        label = QLabel(text)
        label.setFont(styles.ui_font(11))
        label.setStyleSheet(styles.label_style(styles.TEXT_MUTED))
        if width:
            label.setFixedWidth(width)
        return label

    @property
    def is_enabled(self) -> bool:
        return self.toggle.isChecked()

    def detect_devices(self) -> None:
        found = self._probe()
        if not found:
            self._set_status(NO_DEVICES_MESSAGE, styles.DANGER)
            return

        indices = [device.index for device in found]
        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        for device in found:
            self.device_combo.addItem(device.title, device.index)
        if self.device_index in indices:
            self.device_combo.setCurrentIndex(indices.index(self.device_index))
        else:
            self._select_device(indices[0])
        self.device_combo.blockSignals(False)

        self._set_status(f"Found {len(found)} camera(s)", styles.TEXT_SECONDARY)

    def _on_resolution_changed(self, position: int) -> None:
        resolution = self.resolution_combo.itemData(position)
        if resolution is None or tuple(resolution) == self.resolution:
            return

        self.resolution = tuple(resolution)
        remember_resolution(self._settings, self.resolution)
        self._rebuild_controller()

    def _on_device_changed(self, position: int) -> None:
        index = self.device_combo.itemData(position)
        if index is None or index == self.device_index:
            return
        self._select_device(index)

    def _select_device(self, index: int) -> None:
        self.device_index = index
        remember_device_index(self._settings, index)
        self._rebuild_controller()

    def _rebuild_controller(self) -> None:
        was_enabled = self.toggle.isChecked()
        if was_enabled:
            self.toggle.setChecked(False)

        self._controller = self._controller_factory(self.device_index, self.resolution)
        self._controller.frame_ready.connect(self._on_frame)
        self._controller.failed.connect(self._on_failed)

        if was_enabled:
            self.toggle.setChecked(True)

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
        self.status.setStyleSheet(styles.label_style(color))

    def shutdown(self) -> None:
        self._controller.stop()
