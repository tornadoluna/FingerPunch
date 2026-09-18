from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QMetaObject, QObject, Qt, QThread, QTimer, Signal, Slot

from fingerpunch.camera.landmarks import HandDetector
from fingerpunch.camera.source import CameraUnavailable, FrameSource, OpenCVCamera

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_MS = 33
MAX_CONSECUTIVE_MISSES = 15


class CameraWorker(QObject):
    frame_ready = Signal(object)
    landmarks_ready = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        source: FrameSource,
        interval_ms: int = DEFAULT_INTERVAL_MS,
        detector_factory: Callable[[], HandDetector] | None = None,
    ) -> None:
        super().__init__()
        self._source = source
        self._interval_ms = interval_ms
        self._detector_factory = detector_factory
        self._detector: HandDetector | None = None
        self._timer: QTimer | None = None
        self._misses = 0

    @property
    def is_grabbing(self) -> bool:
        return self._timer is not None

    @Slot()
    def start(self) -> None:
        if self._timer is not None:
            return

        try:
            self._source.open()
        except CameraUnavailable as error:
            logger.warning("Camera could not be opened: %s", error)
            self.failed.emit(str(error))
            return
        except Exception as error:
            logger.exception("Unexpected failure opening the camera")
            self.failed.emit(str(error))
            return

        if self._detector_factory is not None and self._detector is None:
            try:
                self._detector = self._detector_factory()
            except Exception as error:
                logger.exception("Hand tracking could not start")
                self.failed.emit(str(error))
                self._source.close()
                return

        self._misses = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.grab)
        self._timer.start(self._interval_ms)

    @Slot()
    def stop(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer.deleteLater()
            self._timer = None
        if self._detector is not None:
            self._detector.close()
            self._detector = None
        self._source.close()

    @Slot()
    def grab(self) -> None:
        try:
            frame = self._source.read()
        except Exception as error:
            logger.exception("Reading a camera frame failed")
            self.stop()
            self.failed.emit(str(error))
            return

        if frame is None:
            self._misses += 1
            if self._misses >= MAX_CONSECUTIVE_MISSES:
                logger.warning("Camera delivered no frames %s times", self._misses)
                self.stop()
                self.failed.emit("The camera stopped delivering frames")
            return

        self._misses = 0
        if self._detector is not None:
            try:
                self.landmarks_ready.emit(self._detector.detect(frame))
            except Exception:
                logger.exception("Hand tracking failed on a frame")
        self.frame_ready.emit(frame)


class CameraController(QObject):
    frame_ready = Signal(object)
    landmarks_ready = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        source_factory: Callable[[], FrameSource] = OpenCVCamera,
        interval_ms: int = DEFAULT_INTERVAL_MS,
        detector_factory: Callable[[], HandDetector] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._source_factory = source_factory
        self._interval_ms = interval_ms
        self._detector_factory = detector_factory
        self._thread: QThread | None = None
        self._worker: CameraWorker | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None

    def start(self) -> None:
        if self._thread is not None:
            return

        self._worker = CameraWorker(
            self._source_factory(), self._interval_ms, self._detector_factory
        )
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.start)
        self._worker.frame_ready.connect(self.frame_ready)
        self._worker.landmarks_ready.connect(self.landmarks_ready)
        self._worker.failed.connect(self._on_failed)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None or self._worker is None:
            return

        QMetaObject.invokeMethod(self._worker, "stop", Qt.BlockingQueuedConnection)
        self._thread.quit()
        self._thread.wait()
        self._worker.deleteLater()
        self._worker = None
        self._thread = None

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self.failed.emit(message)
