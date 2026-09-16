from __future__ import annotations

import logging
import time
from typing import Any, NamedTuple, Protocol

logger = logging.getLogger(__name__)

DEFAULT_DEVICE_INDEX = 0


class CameraUnavailable(RuntimeError):
    pass


class Frame(NamedTuple):
    timestamp: float
    width: int
    height: int
    data: Any


class FrameSource(Protocol):
    def open(self) -> None: ...

    def read(self) -> Frame | None: ...

    def close(self) -> None: ...


def load_opencv() -> Any:
    try:
        import cv2
    except ImportError as error:
        raise CameraUnavailable(
            "OpenCV is not installed, so the camera cannot be used"
        ) from error
    return cv2


class OpenCVCamera:
    def __init__(self, device_index: int = DEFAULT_DEVICE_INDEX) -> None:
        self.device_index = device_index
        self._capture: Any = None

    def open(self) -> None:
        if self._capture is not None:
            return

        cv2 = load_opencv()
        capture = cv2.VideoCapture(self.device_index)
        if not capture.isOpened():
            capture.release()
            raise CameraUnavailable(f"No camera found at index {self.device_index}")

        logger.info("Opened camera %s", self.device_index)
        self._capture = capture

    def read(self) -> Frame | None:
        if self._capture is None:
            return None

        received, data = self._capture.read()
        if not received or data is None:
            return None

        height, width = data.shape[:2]
        return Frame(time.monotonic(), width, height, data)

    def close(self) -> None:
        if self._capture is None:
            return

        self._capture.release()
        self._capture = None
        logger.info("Closed camera %s", self.device_index)
