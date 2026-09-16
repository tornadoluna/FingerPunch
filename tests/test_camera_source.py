import os
import time
from unittest.mock import MagicMock

import pytest

from fingerpunch.camera import source
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
    def __init__(self, opened=True, frames=None, granted=(1280, 720), size=(4, 3)):
        self._opened = opened
        self._frames = list(frames) if frames is not None else None
        self._size = size
        self.released = False
        self.settings = {}
        self._granted = granted

    def set(self, prop, value):
        self.settings[prop] = value
        return True

    def get(self, prop):
        return {3: self._granted[0], 4: self._granted[1]}.get(prop, 0)

    def isOpened(self):
        return self._opened

    def read(self):
        if self._frames is None:
            return True, FakeArray(*self._size)
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
        fake_cv2.VideoCapture.return_value = FakeCapture(size=(640, 480))
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
        fake_cv2.VideoCapture.return_value = FakeCapture()
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


class TestCaptureFormat:
    def test_it_asks_for_mjpg_and_the_requested_size(self, fake_cv2):
        capture = FakeCapture()
        fake_cv2.VideoCapture.return_value = capture
        fake_cv2.CAP_PROP_FOURCC = 6
        fake_cv2.CAP_PROP_FRAME_WIDTH = 3
        fake_cv2.CAP_PROP_FRAME_HEIGHT = 4
        fake_cv2.VideoWriter_fourcc.return_value = 1196444237

        OpenCVCamera(0, resolution=(1280, 720)).open()

        fake_cv2.VideoWriter_fourcc.assert_called_once_with("M", "J", "P", "G")
        assert capture.settings[3] == 1280
        assert capture.settings[4] == 720

    def test_the_default_resolution_is_seven_twenty(self):
        assert OpenCVCamera().resolution == (1280, 720)

    def test_a_requested_resolution_is_kept(self):
        assert OpenCVCamera(0, resolution=(1920, 1080)).resolution == (1920, 1080)

    def test_a_backend_that_rejects_the_request_still_opens(self, fake_cv2):
        class Awkward(FakeCapture):
            def set(self, prop, value):
                raise AttributeError("no such property")

        fake_cv2.VideoCapture.return_value = Awkward()

        camera = OpenCVCamera(0)
        camera.open()

        assert camera.read() is not None


class TestCorruptStreamFallback:
    def test_a_clean_stream_keeps_the_requested_codec(self, fake_cv2, monkeypatch):
        fake_cv2.VideoCapture.return_value = FakeCapture()
        monkeypatch.setattr(source, "stream_decodes_cleanly", lambda capture, **kw: True)

        OpenCVCamera(0).open()

        assert fake_cv2.VideoCapture.call_count == 1

    def test_a_corrupt_stream_reopens_without_the_codec(self, fake_cv2, monkeypatch):
        first, second = FakeCapture(), FakeCapture()
        fake_cv2.VideoCapture.side_effect = [first, second]
        monkeypatch.setattr(source, "stream_decodes_cleanly", lambda capture, **kw: False)

        camera = OpenCVCamera(0)
        camera.open()

        assert fake_cv2.VideoCapture.call_count == 2
        assert first.released is True
        assert camera.read() is not None

    def test_the_fallback_still_requests_the_resolution(self, fake_cv2, monkeypatch):
        first, second = FakeCapture(), FakeCapture()
        fake_cv2.VideoCapture.side_effect = [first, second]
        fake_cv2.CAP_PROP_FRAME_WIDTH = 3
        fake_cv2.CAP_PROP_FRAME_HEIGHT = 4
        monkeypatch.setattr(source, "stream_decodes_cleanly", lambda capture, **kw: False)

        OpenCVCamera(0, resolution=(1280, 720)).open()

        assert second.settings[3] == 1280
        assert second.settings[4] == 720

    def test_a_device_that_will_not_reopen_reports_unavailable(self, fake_cv2, monkeypatch):
        fake_cv2.VideoCapture.side_effect = [FakeCapture(), FakeCapture(opened=False)]
        monkeypatch.setattr(source, "stream_decodes_cleanly", lambda capture, **kw: False)

        with pytest.raises(CameraUnavailable):
            OpenCVCamera(0).open()


class TestStreamDecodeCheck:
    def test_a_quiet_stream_is_clean(self):
        assert source.stream_decodes_cleanly(FakeCapture(), samples=2) is True

    def test_libjpeg_complaints_mark_the_stream_dirty(self):
        class Noisy(FakeCapture):
            def read(self):
                os.write(2, b"Corrupt JPEG data: 4 extraneous bytes before marker 0xd4\n")
                return super().read()

        assert source.stream_decodes_cleanly(Noisy(), samples=2) is False

    def test_unrelated_stderr_output_does_not_count_as_corruption(self):
        class Chatty(FakeCapture):
            def read(self):
                os.write(2, b"[ WARN:0] some unrelated backend warning\n")
                return super().read()

        assert source.stream_decodes_cleanly(Chatty(), samples=2) is True

    def test_stderr_is_restored_afterwards(self):
        before = os.fstat(2)

        source.stream_decodes_cleanly(FakeCapture(), samples=1)

        assert os.fstat(2) == before
