import time

import numpy as np
import pytest
from PySide6.QtCore import QObject, Signal

from fingerpunch.camera.image import frame_to_image
from fingerpunch.camera.source import Frame
from fingerpunch.ui import camera_panel
from fingerpunch.ui.camera_panel import (
    LIVE_MESSAGE,
    OFF_MESSAGE,
    STARTING_MESSAGE,
    CameraPanel,
)


class FakeController(QObject):
    frame_ready = Signal(object)
    failed = Signal(str)

    def __init__(self):
        super().__init__()
        self.started = 0
        self.stopped = 0

    def start(self):
        self.started += 1

    def stop(self):
        self.stopped += 1


def a_frame(width=4, height=3):
    data = np.zeros((height, width, 3), dtype=np.uint8)
    data[0, 0] = (255, 0, 0)
    return Frame(time.monotonic(), width, height, data)


@pytest.fixture
def panel(qapp):
    controller = FakeController()
    widget = CameraPanel(controller_factory=lambda: controller)
    widget._fake = controller
    yield widget
    widget.deleteLater()


class TestControllerSubstitution:
    def test_the_default_controller_is_resolved_at_construction_time(self, qapp, monkeypatch):
        created = []
        monkeypatch.setattr(
            camera_panel, "CameraController", lambda: created.append(1) or FakeController()
        )

        widget = CameraPanel()

        assert created == [1]
        widget.deleteLater()

    def test_the_suite_cannot_reach_a_real_camera(self):
        from fingerpunch.camera import source

        with pytest.raises(AssertionError, match="real camera"):
            source.load_opencv()


class TestDefaultState:
    def test_the_camera_starts_disabled(self, panel):
        assert panel.is_enabled is False
        assert panel._fake.started == 0

    def test_no_preview_is_shown_until_enabled(self, panel):
        assert panel.preview.isVisibleTo(panel) is False

    def test_the_status_says_the_camera_is_off(self, panel):
        assert panel.status.text() == OFF_MESSAGE


class TestEnabling:
    def test_enabling_starts_the_controller(self, panel):
        panel.toggle.setChecked(True)

        assert panel._fake.started == 1

    def test_enabling_shows_the_preview_and_a_starting_message(self, panel):
        panel.toggle.setChecked(True)

        assert panel.preview.isVisibleTo(panel) is True
        assert panel.status.text() == STARTING_MESSAGE

    def test_the_button_offers_to_disable_once_enabled(self, panel):
        panel.toggle.setChecked(True)

        assert "Disable" in panel.toggle.text()


class TestFrames:
    def test_a_frame_is_shown_in_the_preview(self, panel):
        panel.toggle.setChecked(True)

        panel._fake.frame_ready.emit(a_frame(320, 180))

        assert panel.preview.pixmap() is not None
        assert not panel.preview.pixmap().isNull()

    def test_the_status_switches_to_live_on_the_first_frame(self, panel):
        panel.toggle.setChecked(True)

        panel._fake.frame_ready.emit(a_frame())

        assert panel.status.text() == LIVE_MESSAGE

    def test_frames_are_forwarded_to_listeners(self, panel):
        received = []
        panel.frame_ready.connect(received.append)
        panel.toggle.setChecked(True)
        frame = a_frame()

        panel._fake.frame_ready.emit(frame)

        assert received == [frame]

    def test_a_frame_arriving_after_disabling_is_ignored(self, panel):
        panel.toggle.setChecked(True)
        panel.toggle.setChecked(False)
        received = []
        panel.frame_ready.connect(received.append)

        panel._fake.frame_ready.emit(a_frame())

        assert received == []


class TestDisabling:
    def test_disabling_stops_the_controller(self, panel):
        panel.toggle.setChecked(True)

        panel.toggle.setChecked(False)

        assert panel._fake.stopped == 1

    def test_disabling_clears_and_hides_the_preview(self, panel):
        panel.toggle.setChecked(True)
        panel._fake.frame_ready.emit(a_frame())

        panel.toggle.setChecked(False)

        assert panel.preview.pixmap().isNull()
        assert panel.preview.isVisibleTo(panel) is False

    def test_disabling_restores_the_off_message(self, panel):
        panel.toggle.setChecked(True)

        panel.toggle.setChecked(False)

        assert panel.status.text() == OFF_MESSAGE


class TestFailure:
    def test_a_failure_turns_the_toggle_back_off(self, panel):
        panel.toggle.setChecked(True)

        panel._fake.failed.emit("No camera found at index 0")

        assert panel.is_enabled is False

    def test_a_failure_shows_the_reason(self, panel):
        panel.toggle.setChecked(True)

        panel._fake.failed.emit("No camera found at index 0")

        assert panel.status.text() == "No camera found at index 0"

    def test_a_failure_stops_the_controller_without_recursing(self, panel):
        panel.toggle.setChecked(True)

        panel._fake.failed.emit("gone")

        assert panel._fake.stopped == 1

    def test_the_camera_can_be_retried_after_a_failure(self, panel):
        panel.toggle.setChecked(True)
        panel._fake.failed.emit("gone")

        panel.toggle.setChecked(True)

        assert panel._fake.started == 2
        assert panel.status.text() == STARTING_MESSAGE


class TestShutdown:
    def test_shutdown_stops_the_controller(self, panel):
        panel.toggle.setChecked(True)

        panel.shutdown()

        assert panel._fake.stopped == 1

    def test_shutdown_is_safe_when_never_enabled(self, panel):
        panel.shutdown()

        assert panel._fake.stopped == 1

    def test_closing_the_window_shuts_the_camera_down(self, window, monkeypatch):
        controller = FakeController()
        monkeypatch.setattr(camera_panel, "CameraController", lambda: controller)
        window.camera_panel._controller = controller

        window.close()

        assert controller.stopped == 1


class TestImageConversion:
    def test_the_image_matches_the_frame_size(self, qapp):
        image = frame_to_image(a_frame(8, 6))

        assert (image.width(), image.height()) == (8, 6)

    def test_the_image_does_not_alias_the_capture_buffer(self, qapp):
        frame = a_frame()
        image = frame_to_image(frame)
        before = image.pixel(0, 0)

        frame.data[0, 0] = (0, 0, 255)

        assert image.pixel(0, 0) == before

    def test_channels_are_read_as_bgr(self, qapp):
        frame = a_frame()

        image = frame_to_image(frame)

        assert image.pixel(0, 0) == 0xFF0000FF
