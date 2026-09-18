import time

import numpy as np
import pytest
from PySide6.QtCore import QObject, Signal

from fingerpunch.camera.devices import CameraDevice
from fingerpunch.camera.image import frame_to_image
from fingerpunch.camera.landmarks import LandmarkSnapshot
from fingerpunch.camera.source import Frame
from fingerpunch.ui import camera_panel
from fingerpunch.ui.camera_panel import (
    LIVE_MESSAGE,
    NO_DEVICES_MESSAGE,
    OFF_MESSAGE,
    STARTING_MESSAGE,
    CameraPanel,
)


class FakeController(QObject):
    frame_ready = Signal(object)
    landmarks_ready = Signal(object)
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


class FakeSettings:
    def __init__(self, stored=None):
        self.stored = dict(stored or {})

    def get_setting(self, key, default=None):
        return self.stored.get(key, default)

    def save_setting(self, key, value):
        self.stored[key] = value


@pytest.fixture
def panel(qapp):
    controllers = []

    def factory(device_index, resolution, track_hands=False):
        controller = FakeController()
        controller.device_index = device_index
        controller.resolution = resolution
        controller.track_hands = track_hands
        controllers.append(controller)
        return controller

    widget = CameraPanel(controller_factory=factory, probe=lambda: [CameraDevice(i, 640, 480) for i in (0, 1, 2)])
    widget._controllers = controllers
    widget._fake = controllers[0]
    yield widget
    widget.deleteLater()


class TestStartupNaming:
    def test_the_saved_device_is_named_without_opening_it(self, qapp, monkeypatch):
        monkeypatch.setattr(camera_panel, "device_name", lambda index: "C505 HD Webcam")
        settings = FakeSettings({"camera_device_index": 2})

        widget = CameraPanel(
            settings=settings,
            controller_factory=lambda i, r, t=False: FakeController(),
            probe=list,
        )

        assert widget.device_combo.currentText() == "C505 HD Webcam"
        widget.deleteLater()

    def test_an_unnamed_device_falls_back_to_its_index(self, qapp, monkeypatch):
        monkeypatch.setattr(camera_panel, "device_name", lambda index: None)
        settings = FakeSettings({"camera_device_index": 3})

        widget = CameraPanel(
            settings=settings,
            controller_factory=lambda i, r, t=False: FakeController(),
            probe=list,
        )

        assert widget.device_combo.currentText() == "Camera 3"
        widget.deleteLater()

    def test_naming_at_startup_opens_no_device(self, qapp, monkeypatch):
        opened = []
        monkeypatch.setattr(camera_panel, "device_name", lambda index: opened.append(index) or "Cam")

        widget = CameraPanel(
            controller_factory=lambda i, r, t=False: FakeController(), probe=list
        )

        assert opened == [0]
        widget.deleteLater()


class TestDeviceSelection:
    def test_it_starts_on_the_saved_device(self, qapp):
        settings = FakeSettings({"camera_device_index": 2})
        seen = []

        widget = CameraPanel(
            settings=settings,
            controller_factory=lambda i, r, t=False: seen.append(i) or FakeController(),
            probe=list,
        )

        assert widget.device_index == 2
        assert seen == [2]
        widget.deleteLater()

    def test_it_defaults_to_the_first_device(self, panel):
        assert panel.device_index == 0

    def test_detecting_lists_every_camera_found(self, panel):
        panel.detect_devices()

        labels = [panel.device_combo.itemText(i) for i in range(panel.device_combo.count())]
        assert labels == ["Camera 0", "Camera 1", "Camera 2"]

    def test_detecting_nothing_reports_it(self, qapp):
        widget = CameraPanel(controller_factory=lambda i, r, t=False: FakeController(), probe=list)

        widget.detect_devices()

        assert widget.status.text() == NO_DEVICES_MESSAGE
        widget.deleteLater()

    def test_choosing_a_device_rebuilds_the_controller_for_it(self, panel):
        panel.detect_devices()

        panel.device_combo.setCurrentIndex(1)

        assert panel.device_index == 1
        assert panel._controllers[-1].device_index == 1

    def test_choosing_a_device_is_remembered(self, qapp):
        settings = FakeSettings()
        widget = CameraPanel(
            settings=settings,
            controller_factory=lambda i, r, t=False: FakeController(),
            probe=lambda: [CameraDevice(i, 640, 480) for i in (0, 1)],
        )
        widget.detect_devices()

        widget.device_combo.setCurrentIndex(1)

        assert settings.stored["camera_device_index"] == 1
        widget.deleteLater()

    def test_switching_device_while_live_restarts_on_the_new_one(self, panel):
        panel.detect_devices()
        panel.toggle.setChecked(True)
        assert panel._controllers[0].started == 1

        panel.device_combo.setCurrentIndex(2)

        assert panel._controllers[0].stopped == 1
        assert panel._controllers[-1].device_index == 2
        assert panel._controllers[-1].started == 1

    def test_switching_device_while_off_does_not_start_it(self, panel):
        panel.detect_devices()

        panel.device_combo.setCurrentIndex(1)

        assert panel._controllers[-1].started == 0

    def test_detecting_keeps_the_current_device_when_still_present(self, panel):
        panel.detect_devices()
        panel.device_combo.setCurrentIndex(2)
        before = panel.device_index

        panel.detect_devices()

        assert panel.device_index == before

    def test_a_vanished_device_falls_back_to_the_first_found(self, qapp):
        settings = FakeSettings({"camera_device_index": 7})
        widget = CameraPanel(
            settings=settings,
            controller_factory=lambda i, r, t=False: FakeController(),
            probe=lambda: [CameraDevice(i, 640, 480) for i in (0, 1)],
        )

        widget.detect_devices()

        assert widget.device_index == 0
        widget.deleteLater()


class TestResolution:
    def test_it_defaults_to_seven_twenty(self, panel):
        assert panel.resolution == (1280, 720)

    def test_the_controller_is_built_with_the_resolution(self, panel):
        assert panel._controllers[0].resolution == (1280, 720)

    def test_a_saved_resolution_is_used(self, qapp):
        settings = FakeSettings({"camera_resolution": [1920, 1080]})
        seen = []

        widget = CameraPanel(
            settings=settings,
            controller_factory=lambda i, r, t=False: seen.append(r) or FakeController(),
            probe=list,
        )

        assert widget.resolution == (1920, 1080)
        assert seen == [(1920, 1080)]
        widget.deleteLater()

    def test_choosing_a_resolution_rebuilds_the_controller(self, panel):
        panel.resolution_combo.setCurrentIndex(0)

        assert panel.resolution == (640, 480)
        assert panel._controllers[-1].resolution == (640, 480)

    def test_choosing_a_resolution_is_remembered(self, qapp):
        settings = FakeSettings()
        widget = CameraPanel(
            settings=settings,
            controller_factory=lambda i, r, t=False: FakeController(),
            probe=list,
        )

        widget.resolution_combo.setCurrentIndex(2)

        assert settings.stored["camera_resolution"] == [1920, 1080]
        widget.deleteLater()

    def test_changing_resolution_while_live_restarts_the_camera(self, panel):
        panel.toggle.setChecked(True)
        assert panel._controllers[0].started == 1

        panel.resolution_combo.setCurrentIndex(0)

        assert panel._controllers[0].stopped == 1
        assert panel._controllers[-1].started == 1

    def test_a_nonsense_saved_resolution_falls_back(self, qapp):
        settings = FakeSettings({"camera_resolution": "big"})

        widget = CameraPanel(
            settings=settings,
            controller_factory=lambda i, r, t=False: FakeController(),
            probe=list,
        )

        assert widget.resolution == (1280, 720)
        widget.deleteLater()


class TestControllerSubstitution:
    def test_the_default_controller_is_resolved_at_construction_time(self, qapp, monkeypatch):
        created = []
        monkeypatch.setattr(
            camera_panel,
            "_default_controller_factory",
            lambda index, resolution, track=False: created.append(index) or FakeController(),
        )

        widget = CameraPanel()

        assert created == [0]
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


class TestHandTracking:
    def test_tracking_is_off_by_default(self, panel):
        assert panel.track_hands is False
        assert panel.track_checkbox.isChecked() is False
        assert panel._controllers[0].track_hands is False

    def test_enabling_tracking_rebuilds_the_controller_with_it_on(self, panel, monkeypatch):
        monkeypatch.setattr(camera_panel, "is_downloaded", lambda: True)

        panel.track_checkbox.setChecked(True)

        assert panel.track_hands is True
        assert panel._controllers[-1].track_hands is True

    def test_enabling_tracking_fetches_the_model(self, panel, monkeypatch):
        calls = []
        monkeypatch.setattr(camera_panel, "is_downloaded", lambda: calls.append(1) or True)

        panel.track_checkbox.setChecked(True)

        assert calls == [1]

    def test_a_cached_model_starts_tracking_without_downloading(self, panel, monkeypatch):
        started = []
        monkeypatch.setattr(camera_panel, "is_downloaded", lambda: True)
        monkeypatch.setattr(panel, "_start_model_download", lambda: started.append(1))

        panel.track_checkbox.setChecked(True)

        assert started == []
        assert panel.track_hands is True

    def test_a_missing_model_is_downloaded_before_tracking_starts(self, panel, monkeypatch):
        started = []
        monkeypatch.setattr(camera_panel, "is_downloaded", lambda: False)
        monkeypatch.setattr(panel, "_start_model_download", lambda: started.append(1))

        panel.track_checkbox.setChecked(True)

        assert started == [1]
        assert panel.track_hands is False
        assert panel.status.text() == camera_panel.PREPARING_TRACKING_MESSAGE

    def test_download_progress_is_reported(self, panel):
        panel._on_download_progress(42)

        assert "42%" in panel.status.text()

    def test_a_finished_download_turns_tracking_on(self, panel):
        panel._on_download_finished()

        assert panel.track_hands is True
        assert panel.track_checkbox.isEnabled() is True

    def test_a_failed_download_turns_tracking_back_off(self, panel, monkeypatch):
        monkeypatch.setattr(camera_panel, "is_downloaded", lambda: False)
        panel.track_checkbox.setChecked(True)

        panel._on_download_failed("no network")

        assert panel.track_hands is False
        assert panel.track_checkbox.isChecked() is False
        assert panel.track_checkbox.isEnabled() is True
        assert panel.status.text() == "no network"

    def test_enabling_tracking_with_the_camera_off_says_what_to_do_next(self, panel, monkeypatch):
        monkeypatch.setattr(camera_panel, "is_downloaded", lambda: True)

        panel.track_checkbox.setChecked(True)

        assert panel.track_hands is True
        assert panel.status.text() == camera_panel.TRACKING_READY_MESSAGE

    def test_disabling_tracking_with_the_camera_off_returns_to_the_off_message(
        self, panel, monkeypatch
    ):
        monkeypatch.setattr(camera_panel, "is_downloaded", lambda: True)
        panel.track_checkbox.setChecked(True)

        panel.track_checkbox.setChecked(False)

        assert panel.status.text() == camera_panel.OFF_MESSAGE

    def test_disabling_tracking_rebuilds_without_it(self, panel, monkeypatch):
        monkeypatch.setattr(camera_panel, "is_downloaded", lambda: True)
        panel.track_checkbox.setChecked(True)

        panel.track_checkbox.setChecked(False)

        assert panel.track_hands is False
        assert panel._controllers[-1].track_hands is False

    def test_landmarks_are_kept_for_the_next_frame(self, panel):
        snapshot = LandmarkSnapshot(1.0, ())

        panel._fake.landmarks_ready.emit(snapshot)

        assert panel._landmarks is snapshot

    def test_landmarks_are_discarded_when_tracking_is_switched(self, panel, monkeypatch):
        monkeypatch.setattr(camera_panel, "is_downloaded", lambda: True)
        panel._landmarks = LandmarkSnapshot(1.0, ())

        panel.track_checkbox.setChecked(True)

        assert panel._landmarks is None

    def test_the_overlay_is_only_drawn_when_tracking(self, panel, monkeypatch):
        drawn = []
        monkeypatch.setattr(camera_panel, "draw_hands", lambda img, snap: drawn.append(1) or img)
        panel.toggle.setChecked(True)
        panel._landmarks = LandmarkSnapshot(1.0, ())

        panel._fake.frame_ready.emit(a_frame())

        assert drawn == []

    def test_the_overlay_is_drawn_once_tracking_is_on(self, panel, monkeypatch):
        monkeypatch.setattr(camera_panel, "is_downloaded", lambda: True)
        drawn = []
        monkeypatch.setattr(camera_panel, "draw_hands", lambda img, snap: drawn.append(1) or img)
        panel.track_checkbox.setChecked(True)
        panel.toggle.setChecked(True)
        panel._landmarks = LandmarkSnapshot(1.0, ())

        panel._controllers[-1].frame_ready.emit(a_frame())

        assert drawn == [1]


class TestPositioningCheck:
    def _ready(self, panel, monkeypatch):
        monkeypatch.setattr(camera_panel, "is_downloaded", lambda: True)
        panel.track_checkbox.setChecked(True)
        panel.toggle.setChecked(True)
        return panel._controllers[-1]

    def test_it_refuses_without_tracking(self, panel):
        panel.toggle.setChecked(True)

        panel.check_positioning()

        assert panel._collecting is None
        assert panel.status.text() == camera_panel.CHECK_NEEDS_TRACKING

    def test_it_refuses_without_the_camera(self, panel, monkeypatch):
        monkeypatch.setattr(camera_panel, "is_downloaded", lambda: True)
        panel.track_checkbox.setChecked(True)

        panel.check_positioning()

        assert panel._collecting is None

    def test_starting_a_check_collects_landmarks(self, panel, monkeypatch):
        controller = self._ready(panel, monkeypatch)

        panel.check_positioning()
        controller.landmarks_ready.emit(LandmarkSnapshot(1.0, ()))
        controller.landmarks_ready.emit(LandmarkSnapshot(2.0, ()))

        assert len(panel._collecting) == 2

    def test_the_button_is_disabled_while_checking(self, panel, monkeypatch):
        self._ready(panel, monkeypatch)

        panel.check_positioning()

        assert panel.check_button.isEnabled() is False

    def test_live_frames_do_not_overwrite_the_checking_message(self, panel, monkeypatch):
        controller = self._ready(panel, monkeypatch)
        panel.check_positioning()

        controller.frame_ready.emit(a_frame())

        assert panel.status.text() == camera_panel.CHECKING_MESSAGE

    def test_the_report_survives_further_frames(self, panel, monkeypatch):
        controller = self._ready(panel, monkeypatch)
        panel.check_positioning()
        panel._finish_check()
        reported = panel.status.text()

        controller.frame_ready.emit(a_frame())

        assert panel.status.text() == reported

    def test_finishing_reports_and_re_enables_the_button(self, panel, monkeypatch):
        self._ready(panel, monkeypatch)
        panel.check_positioning()

        panel._finish_check()

        assert panel._collecting is None
        assert panel.check_button.isEnabled() is True
        assert panel.status.text() == camera_panel.NO_FRAMES_REPORT

    def test_the_report_is_emitted(self, panel, monkeypatch):
        self._ready(panel, monkeypatch)
        reports = []
        panel.positioning_checked.connect(reports.append)
        panel.check_positioning()

        panel._finish_check()

        assert len(reports) == 1
        assert reports[0].ok is False

    def test_changing_a_setting_releases_the_held_status(self, panel, monkeypatch):
        controller = self._ready(panel, monkeypatch)
        panel.check_positioning()
        panel._finish_check()

        panel.toggle.setChecked(False)
        panel.toggle.setChecked(True)
        panel._controllers[-1].frame_ready.emit(a_frame())

        assert panel.status.text() == LIVE_MESSAGE
        assert controller is not None

    def test_shutdown_abandons_a_running_check(self, panel, monkeypatch):
        self._ready(panel, monkeypatch)
        panel.check_positioning()

        panel.shutdown()

        assert panel._collecting is None


class TestShutdown:
    def test_shutdown_stops_the_controller(self, panel):
        panel.toggle.setChecked(True)

        panel.shutdown()

        assert panel._fake.stopped == 1

    def test_shutdown_is_safe_when_never_enabled(self, panel):
        panel.shutdown()

        assert panel._fake.stopped == 1

    def test_closing_the_window_shuts_the_camera_down(self, window):
        controller = FakeController()
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
