import time
from unittest.mock import MagicMock

import pytest

from fingerpunch.camera.source import (
    CameraUnavailable,
    Frame,
    OpenCVCamera,
    load_opencv,
)


class FakeArray:
    def __init__(self, width=4, height=3):
        self.shape = (height, width, 3)


class FakeCapture:
    def __init__(self, opened=True, frames=None):
        self._opened = opened
        self._frames = list(frames) if frames is not None else [FakeArray()]
        self.released = False

    def isOpened(self):
        return self._opened

    def read(self):
        if not self._frames:
            return False, None
        return True, self._frames.pop(0)

    def release(self):
        self.released = True


@pytest.fixture
def fake_cv2(monkeypatch):
    module = MagicMock()
    monkeypatch.setattr("fingerpunch.camera.source.load_opencv", lambda: module)
    return module


class TestOpeningTheCamera:
    def test_a_working_device_opens(self, fake_cv2):
        capture = FakeCapture(opened=True)
        fake_cv2.VideoCapture.return_value = capture

        camera = OpenCVCamera(device_index=0)
        camera.open()

        assert camera.read() is not None

    def test_a_missing_device_raises_camera_unavailable(self, fake_cv2):
        fake_cv2.VideoCapture.return_value = FakeCapture(opened=False)

        with pytest.raises(CameraUnavailable, match="index 2"):
            OpenCVCamera(device_index=2).open()

    def test_a_missing_device_is_released_rather_than_leaked(self, fake_cv2):
        capture = FakeCapture(opened=False)
        fake_cv2.VideoCapture.return_value = capture

        with pytest.raises(CameraUnavailable):
            OpenCVCamera().open()

        assert capture.released is True

    def test_opening_twice_reuses_the_same_capture(self, fake_cv2):
        fake_cv2.VideoCapture.return_value = FakeCapture()

        camera = OpenCVCamera()
        camera.open()
        camera.open()

        assert fake_cv2.VideoCapture.call_count == 1

    def test_the_requested_device_index_is_used(self, fake_cv2):
        fake_cv2.VideoCapture.return_value = FakeCapture()

        OpenCVCamera(device_index=3).open()

        fake_cv2.VideoCapture.assert_called_once_with(3)


class TestReadingFrames:
    def test_a_frame_carries_its_size_and_a_timestamp(self, fake_cv2):
        fake_cv2.VideoCapture.return_value = FakeCapture(frames=[FakeArray(width=640, height=480)])
        camera = OpenCVCamera()
        camera.open()

        before = time.monotonic()
        frame = camera.read()

        assert isinstance(frame, Frame)
        assert (frame.width, frame.height) == (640, 480)
        assert before <= frame.timestamp <= time.monotonic()

    def test_reading_before_opening_returns_nothing(self):
        assert OpenCVCamera().read() is None

    def test_a_failed_read_returns_nothing(self, fake_cv2):
        fake_cv2.VideoCapture.return_value = FakeCapture(frames=[])
        camera = OpenCVCamera()
        camera.open()

        assert camera.read() is None

    def test_reading_after_closing_returns_nothing(self, fake_cv2):
        fake_cv2.VideoCapture.return_value = FakeCapture()
        camera = OpenCVCamera()
        camera.open()
        camera.close()

        assert camera.read() is None


class TestClosing:
    def test_closing_releases_the_device(self, fake_cv2):
        capture = FakeCapture()
        fake_cv2.VideoCapture.return_value = capture
        camera = OpenCVCamera()
        camera.open()

        camera.close()

        assert capture.released is True

    def test_closing_twice_is_harmless(self, fake_cv2):
        fake_cv2.VideoCapture.return_value = FakeCapture()
        camera = OpenCVCamera()
        camera.open()

        camera.close()
        camera.close()

    def test_closing_without_opening_is_harmless(self):
        OpenCVCamera().close()

    def test_a_camera_can_be_reopened_after_closing(self, fake_cv2):
        fake_cv2.VideoCapture.return_value = FakeCapture(frames=[FakeArray(), FakeArray()])
        camera = OpenCVCamera()
        camera.open()
        camera.close()
        fake_cv2.VideoCapture.return_value = FakeCapture()

        camera.open()

        assert camera.read() is not None


class TestOpenCVImport:
    def test_a_missing_opencv_reports_camera_unavailable(self, monkeypatch):
        import builtins

        real_import = builtins.__import__

        def refuse(name, *args, **kwargs):
            if name == "cv2":
                raise ImportError("no cv2")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", refuse)

        with pytest.raises(CameraUnavailable, match="OpenCV is not installed"):
            load_opencv()


class TestQuietOpenCV:
    def test_it_restores_the_previous_log_level(self):
        import cv2

        from fingerpunch.camera.source import quiet_opencv

        before = cv2.utils.logging.getLogLevel()
        with quiet_opencv():
            during = cv2.utils.logging.getLogLevel()

        assert during == cv2.utils.logging.LOG_LEVEL_SILENT
        assert cv2.utils.logging.getLogLevel() == before

    def test_stderr_is_restored_afterwards(self):
        import os

        from fingerpunch.camera.source import quiet_opencv

        before = os.fstat(2)
        with quiet_opencv():
            pass

        assert os.fstat(2) == before

    def test_it_is_a_no_op_when_opencv_cannot_be_imported(self, monkeypatch):
        import builtins

        from fingerpunch.camera.source import quiet_opencv

        real_import = builtins.__import__

        def refuse(name, *args, **kwargs):
            if name == "cv2":
                raise ImportError("no cv2")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", refuse)

        with quiet_opencv():
            entered = True

        assert entered

    def test_it_is_a_no_op_when_opencv_has_no_logging_module(self, monkeypatch):
        import sys
        import types

        from fingerpunch.camera.source import quiet_opencv

        stub = types.ModuleType("cv2")
        monkeypatch.setitem(sys.modules, "cv2", stub)

        with quiet_opencv():
            entered = True

        assert entered

    def test_the_log_level_is_restored_even_if_the_body_raises(self):
        import cv2
        import pytest as _pytest

        from fingerpunch.camera.source import quiet_opencv

        before = cv2.utils.logging.getLogLevel()
        with _pytest.raises(ValueError), quiet_opencv():
            raise ValueError("boom")

        assert cv2.utils.logging.getLogLevel() == before
