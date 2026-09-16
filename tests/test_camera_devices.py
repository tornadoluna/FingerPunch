import pytest

from fingerpunch.camera.devices import (
    DEVICE_SETTING,
    probe_devices,
    remember_device_index,
    saved_device_index,
)
from fingerpunch.camera.source import CameraUnavailable


class StubCamera:
    def __init__(self, index, working):
        self.index = index
        self.working = working
        self.closed = False

    def open(self):
        if not self.working:
            raise CameraUnavailable(f"No camera found at index {self.index}")

    def read(self):
        return None

    def close(self):
        self.closed = True


def factory_for(working_indices, created=None):
    def make(index):
        camera = StubCamera(index, index in working_indices)
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
    def test_it_finds_the_working_devices(self):
        assert probe_devices(4, factory_for({0, 2})) == [0, 2]

    def test_it_reports_nothing_when_no_device_answers(self):
        assert probe_devices(4, factory_for(set())) == []

    def test_it_stops_at_the_requested_limit(self):
        assert probe_devices(2, factory_for({0, 1, 5})) == [0, 1]

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

        assert probe_devices(3, make) == [0, 2]


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
