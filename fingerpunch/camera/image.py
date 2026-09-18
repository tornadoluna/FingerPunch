from __future__ import annotations

from PySide6.QtGui import QImage

from fingerpunch.camera.source import Frame


def frame_to_image(frame: Frame) -> QImage:
    data = frame.data
    bytes_per_line = data.strides[0] if hasattr(data, "strides") else frame.width * 3
    image = QImage(data.data, frame.width, frame.height, bytes_per_line, QImage.Format_BGR888)
    return image.copy()
