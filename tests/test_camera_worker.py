import time

import pytest

from fingerpunch.camera.source import CameraUnavailable, Frame
from fingerpunch.camera.worker import (
    MAX_CONSECUTIVE_MISSES,
    CameraController,
    CameraWorker,
)


class FakeSource:
    def __init__(self, frames=None, open_error=None, read_error=None):
        self.frames = list(frames) if frames is not None else []
        self.open_error = open_error
        self.read_error = read_error
        self.opened = False
        self.closed = False
        self.reads = 0

    def open(self):
        if self.open_error is not None:
            raise self.open_error
        self.opened = True

    def read(self):
        self.reads += 1
        if self.read_error is not None:
            raise self.read_error
        return self.frames.pop(0) if self.frames else None

    def close(self):
        self.closed = True


def a_frame(timestamp=None):
    return Frame(timestamp if timestamp is not None else time.monotonic(), 4, 3, object())


class TestWorkerStartup:
    def test_starting_opens_the_source(self, qapp):
        source = FakeSource()
        worker = CameraWorker(source)

        worker.start()

        assert source.opened is True
        assert worker.is_grabbing is True
        worker.stop()

    def test_an_unavailable_camera_reports_instead_of_raising(self, qapp):
        source = FakeSource(open_error=CameraUnavailable("no device"))
        worker = CameraWorker(source)
        failures = []
        worker.failed.connect(failures.append)

        worker.start()

        assert failures == ["no device"]
        assert worker.is_grabbing is False

    def test_an_unexpected_open_failure_is_also_reported(self, qapp):
        source = FakeSource(open_error=OSError("permission denied"))
        worker = CameraWorker(source)
        failures = []
        worker.failed.connect(failures.append)

        worker.start()

        assert failures == ["permission denied"]
        assert worker.is_grabbing is False

    def test_starting_twice_does_not_open_twice(self, qapp):
        source = FakeSource()
        worker = CameraWorker(source)

        worker.start()
        source.opened = False
        worker.start()

        assert source.opened is False
        worker.stop()


class TestGrabbing:
    def test_a_frame_is_emitted(self, qapp):
        frame = a_frame()
        worker = CameraWorker(FakeSource(frames=[frame]))
        received = []
        worker.frame_ready.connect(received.append)
        worker.start()

        worker.grab()

        assert received == [frame]
        worker.stop()

    def test_an_occasional_dropped_frame_is_tolerated(self, qapp):
        worker = CameraWorker(FakeSource(frames=[]))
        failures = []
        worker.failed.connect(failures.append)
        worker.start()

        for _ in range(MAX_CONSECUTIVE_MISSES - 1):
            worker.grab()

        assert failures == []
        assert worker.is_grabbing is True
        worker.stop()

    def test_a_camera_that_stops_delivering_is_reported(self, qapp):
        source = FakeSource(frames=[])
        worker = CameraWorker(source)
        failures = []
        worker.failed.connect(failures.append)
        worker.start()

        for _ in range(MAX_CONSECUTIVE_MISSES):
            worker.grab()

        assert failures == ["The camera stopped delivering frames"]
        assert worker.is_grabbing is False
        assert source.closed is True

    def test_the_miss_count_resets_after_a_good_frame(self, qapp):
        source = FakeSource(frames=[])
        worker = CameraWorker(source)
        failures = []
        worker.failed.connect(failures.append)
        worker.start()

        for _ in range(MAX_CONSECUTIVE_MISSES - 1):
            worker.grab()
        source.frames.append(a_frame())
        worker.grab()
        for _ in range(MAX_CONSECUTIVE_MISSES - 1):
            worker.grab()

        assert failures == []
        worker.stop()

    def test_a_read_that_raises_stops_and_reports(self, qapp):
        source = FakeSource(read_error=OSError("device disappeared"))
        worker = CameraWorker(source)
        failures = []
        worker.failed.connect(failures.append)
        worker.start()

        worker.grab()

        assert failures == ["device disappeared"]
        assert worker.is_grabbing is False
        assert source.closed is True


class TestWorkerShutdown:
    def test_stopping_closes_the_source(self, qapp):
        source = FakeSource()
        worker = CameraWorker(source)
        worker.start()

        worker.stop()

        assert source.closed is True
        assert worker.is_grabbing is False

    def test_stopping_without_starting_is_harmless(self, qapp):
        source = FakeSource()

        CameraWorker(source).stop()

        assert source.closed is True

    def test_stopping_twice_is_harmless(self, qapp):
        worker = CameraWorker(FakeSource())
        worker.start()

        worker.stop()
        worker.stop()

        assert worker.is_grabbing is False


class TestController:
    def test_it_starts_and_stops_a_thread(self, qapp):
        controller = CameraController(source_factory=FakeSource)
        assert controller.is_running is False

        controller.start()
        assert controller.is_running is True

        controller.stop()
        assert controller.is_running is False

    def test_starting_twice_keeps_one_thread(self, qapp):
        controller = CameraController(source_factory=FakeSource)
        controller.start()

        controller.start()

        assert controller.is_running is True
        controller.stop()

    def test_stopping_without_starting_is_harmless(self, qapp):
        CameraController(source_factory=FakeSource).stop()

    def test_frames_reach_the_controller_from_the_worker_thread(self, qapp):
        frames = [a_frame() for _ in range(5)]
        controller = CameraController(
            source_factory=lambda: FakeSource(frames=frames), interval_ms=1
        )
        received = []
        controller.frame_ready.connect(received.append)

        controller.start()
        deadline = time.monotonic() + 5
        while not received and time.monotonic() < deadline:
            qapp.processEvents()
        controller.stop()

        assert received

    def test_a_failure_reaches_the_controller(self, qapp):
        controller = CameraController(
            source_factory=lambda: FakeSource(open_error=CameraUnavailable("nope")),
            interval_ms=1,
        )
        failures = []
        controller.failed.connect(failures.append)

        controller.start()
        deadline = time.monotonic() + 5
        while not failures and time.monotonic() < deadline:
            qapp.processEvents()
        controller.stop()

        assert failures == ["nope"]

    def test_the_source_is_closed_when_the_controller_stops(self, qapp):
        sources = []

        def factory():
            source = FakeSource(frames=[a_frame()])
            sources.append(source)
            return source

        controller = CameraController(source_factory=factory, interval_ms=1)
        controller.start()
        deadline = time.monotonic() + 5
        while not sources and time.monotonic() < deadline:
            qapp.processEvents()

        controller.stop()

        assert sources and sources[0].closed is True


@pytest.fixture(autouse=True)
def _no_real_camera(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("a test tried to open a real camera")

    monkeypatch.setattr("fingerpunch.camera.source.load_opencv", refuse)
