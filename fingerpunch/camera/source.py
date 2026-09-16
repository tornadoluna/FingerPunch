from __future__ import annotations

import logging
import os
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, NamedTuple, Protocol

logger = logging.getLogger(__name__)

DEFAULT_DEVICE_INDEX = 0
DEFAULT_RESOLUTION = (1280, 720)
CAPTURE_CODEC = "MJPG"
FORMAT_CHECK_FRAMES = 5
CORRUPT_MARKER = "Corrupt JPEG data"


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


def _request_format(cv2: Any, capture: Any, resolution: tuple[int, int]) -> tuple[int, int]:
    try:
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*CAPTURE_CODEC))
    except (AttributeError, TypeError, ValueError):
        logger.warning("Could not request %s from camera", CAPTURE_CODEC)
    return _request_size(cv2, capture, resolution)


def _request_size(cv2: Any, capture: Any, resolution: tuple[int, int]) -> tuple[int, int]:
    width, height = resolution
    try:
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        return (
            int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
    except (AttributeError, TypeError, ValueError):
        logger.warning("Could not request %sx%s from camera", width, height)
        return resolution


def stream_decodes_cleanly(capture: Any, samples: int = FORMAT_CHECK_FRAMES) -> bool:
    with tempfile.TemporaryFile() as buffer:
        stderr = os.dup(2)
        try:
            os.dup2(buffer.fileno(), 2)
            for _ in range(samples):
                capture.read()
        finally:
            os.dup2(stderr, 2)
            os.close(stderr)

        buffer.seek(0)
        noise = buffer.read()

    if isinstance(noise, bytes):
        noise = noise.decode("utf-8", errors="replace")
    return CORRUPT_MARKER not in noise


@contextmanager
def quiet_opencv() -> Iterator[None]:
    try:
        import cv2

        logging_module = cv2.utils.logging
        previous = logging_module.getLogLevel()
        logging_module.setLogLevel(logging_module.LOG_LEVEL_SILENT)
    except (ImportError, AttributeError, OSError):
        yield
        return

    stderr = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(stderr, 2)
        os.close(devnull)
        os.close(stderr)
        logging_module.setLogLevel(previous)


class OpenCVCamera:
    def __init__(
        self,
        device_index: int = DEFAULT_DEVICE_INDEX,
        resolution: tuple[int, int] = DEFAULT_RESOLUTION,
    ) -> None:
        self.device_index = device_index
        self.resolution = resolution
        self._capture: Any = None

    def open(self) -> None:
        if self._capture is not None:
            return

        cv2 = load_opencv()
        capture = cv2.VideoCapture(self.device_index)
        if not capture.isOpened():
            capture.release()
            raise CameraUnavailable(f"No camera found at index {self.device_index}")

        granted = _request_format(cv2, capture, self.resolution)
        codec = CAPTURE_CODEC

        if not stream_decodes_cleanly(capture):
            logger.warning(
                "Camera %s produced corrupt %s frames; falling back to the driver default",
                self.device_index,
                CAPTURE_CODEC,
            )
            capture.release()
            capture = cv2.VideoCapture(self.device_index)
            if not capture.isOpened():
                capture.release()
                raise CameraUnavailable(f"No camera found at index {self.device_index}")
            granted = _request_size(cv2, capture, self.resolution)
            codec = "default"

        logger.info(
            "Opened camera %s at %sx%s in %s (requested %sx%s)",
            self.device_index,
            granted[0],
            granted[1],
            codec,
            self.resolution[0],
            self.resolution[1],
        )
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
