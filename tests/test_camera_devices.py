import pytest

from fingerpunch.camera.devices import (
    DEVICE_SETTING,
    CameraDevice,
    delivers_frames,
    probe_devices,
    remember_device_index,
    saved_device_index,
)
from fingerpunch.camera.source import CameraUnavailable, Frame


class StubCamera:
    def __init__(self, index, working, delivers=True):
        self.index = index
        self.working = working
        self.delivers = delivers
        self.closed = False

    def open(self):
        if not self.working:
            raise CameraUnavailable(f"No camera found at index {self.index}")

    def read(self):
        if not self.delivers:
            return None
        return Frame(0.0, 640, 480, object())

    def close(self):
        self.closed = True


def factory_for(working_indices, created=None, silent_indices=()):
    def make(index):
        camera = StubCamera(
            index, index in working_indices, delivers=index not in silent_indices
        )
        if created is not None:
            created.append(camera)
        return camera

    return make


class FakeSettings:
    def __init__(self, stored=None):
        self.stored = dict(stored or {})

    def get_setting(self, key, default=None):
        return self.stored.get(key, default)

    def save_setting(self, key, value):
        self.stored[key] = value


class TestProbing:
    def test_a_device_reports_its_resolution(self):
        device = probe_devices(2, factory_for({0}))[0]

        assert device == CameraDevice(0, 640, 480)
        assert device.label == "Camera 0 (640x480)"

    def test_it_finds_the_working_devices(self):
        assert [d.index for d in probe_devices(4, factory_for({0, 2}))] == [0, 2]

    def test_it_reports_nothing_when_no_device_answers(self):
        assert probe_devices(4, factory_for(set())) == []

    def test_it_stops_at_the_requested_limit(self):
        assert [d.index for d in probe_devices(2, factory_for({0, 1, 5}))] == [0, 1]

    def test_a_device_that_opens_but_delivers_nothing_is_rejected(self):
        found = probe_devices(4, factory_for({0, 1, 2}, silent_indices={1}))

        assert [device.index for device in found] == [0, 2]

    def test_scanning_stops_after_consecutive_gaps_once_something_was_found(self):
        created = []

        probe_devices(10, factory_for({0}, created))

        assert [camera.index for camera in created] == [0, 1, 2]

    def test_scanning_continues_through_gaps_before_the_first_device(self):
        assert [d.index for d in probe_devices(6, factory_for({4}))] == [4]

    def test_a_single_device_check_reports_whether_it_delivers(self):
        assert delivers_frames(0, factory_for({0})) is True
        assert delivers_frames(0, factory_for({0}, silent_indices={0})) is False
        assert delivers_frames(1, factory_for({0})) is False

    def test_every_probed_device_is_closed_again(self):
        created = []

        probe_devices(3, factory_for({0, 1, 2}, created))

        assert [camera.closed for camera in created] == [True, True, True]

    def test_a_device_that_failed_to_open_is_still_closed(self):
        created = []

        probe_devices(3, factory_for(set(), created))

        assert all(camera.closed for camera in created)

    def test_an_unexpected_error_does_not_abort_the_scan(self):
        def make(index):
            if index == 1:
                raise RuntimeError("driver exploded")
            return StubCamera(index, True)

        assert [d.index for d in probe_devices(3, make)] == [0, 2]


class TestRememberingTheChoice:
    def test_the_default_is_used_when_nothing_is_stored(self):
        assert saved_device_index(FakeSettings()) == 0

    def test_a_stored_index_is_returned(self):
        assert saved_device_index(FakeSettings({DEVICE_SETTING: 3})) == 3

    def test_a_nonsense_stored_value_falls_back_to_the_default(self):
        assert saved_device_index(FakeSettings({DEVICE_SETTING: "second"})) == 0

    def test_no_settings_store_falls_back_to_the_default(self):
        assert saved_device_index(None) == 0

    def test_an_explicit_default_is_honoured(self):
        assert saved_device_index(None, default=2) == 2

    def test_choosing_a_device_stores_it(self):
        settings = FakeSettings()

        remember_device_index(settings, 4)

        assert settings.stored[DEVICE_SETTING] == 4

    def test_storing_without_a_settings_store_is_harmless(self):
        remember_device_index(None, 4)

    def test_the_choice_survives_a_round_trip(self):
        settings = FakeSettings()

        remember_device_index(settings, 2)

        assert saved_device_index(settings) == 2


class TestRealSettingsStore:
    def test_a_data_manager_satisfies_the_settings_protocol(self, tmp_path):
        from fingerpunch.data_manager import DataManager

        db = DataManager(str(tmp_path / "s.db"))

        remember_device_index(db, 3)

        assert saved_device_index(db) == 3

    def test_an_unset_device_defaults_to_zero(self, tmp_path):
        from fingerpunch.data_manager import DataManager

        assert saved_device_index(DataManager(str(tmp_path / "s.db"))) == 0


@pytest.fixture(autouse=True)
def _guard(no_real_camera):
    return no_real_camera
