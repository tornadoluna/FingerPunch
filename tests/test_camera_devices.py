import pytest

from fingerpunch.camera.devices import (
    DEVICE_SETTING,
    RESOLUTION_SETTING,
    CameraDevice,
    delivers_frames,
    device_name,
    is_capture_node,
    probe_devices,
    remember_device_index,
    remember_resolution,
    saved_device_index,
    saved_resolution,
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
def _guard(no_real_camera, monkeypatch, tmp_path):
    from fingerpunch.camera import devices

    monkeypatch.setattr(devices, "V4L_SYSFS", tmp_path / "no-sysfs-here")
    return no_real_camera


class TestResolutionSetting:
    def test_the_default_is_seven_twenty(self):
        assert saved_resolution(FakeSettings()) == (1280, 720)

    def test_a_stored_resolution_is_returned(self):
        assert saved_resolution(FakeSettings({RESOLUTION_SETTING: [1920, 1080]})) == (1920, 1080)

    def test_a_stored_tuple_is_accepted(self):
        assert saved_resolution(FakeSettings({RESOLUTION_SETTING: (640, 480)})) == (640, 480)

    @pytest.mark.parametrize("stored", [
        "1280x720",
        [1280],
        [1280, 720, 30],
        ["1280", "720"],
        [1280, "720"],
        [0, 720],
        [1280, 0],
        [-1280, -720],
        [1280.0, 720.0],
        None,
        {},
    ])
    def test_a_nonsense_stored_resolution_falls_back(self, stored):
        assert saved_resolution(FakeSettings({RESOLUTION_SETTING: stored})) == (1280, 720)

    def test_no_settings_store_uses_the_default(self):
        assert saved_resolution(None) == (1280, 720)

    def test_an_explicit_default_is_honoured(self):
        assert saved_resolution(None, default=(800, 600)) == (800, 600)

    def test_a_choice_is_stored_as_a_plain_list(self):
        settings = FakeSettings()

        remember_resolution(settings, (1920, 1080))

        assert settings.stored[RESOLUTION_SETTING] == [1920, 1080]

    def test_storing_without_a_settings_store_is_harmless(self):
        remember_resolution(None, (640, 480))

    def test_the_choice_survives_a_round_trip(self):
        settings = FakeSettings()

        remember_resolution(settings, (1920, 1080))

        assert saved_resolution(settings) == (1920, 1080)

    def test_it_round_trips_through_a_real_database(self, tmp_path):
        from fingerpunch.data_manager import DataManager

        db = DataManager(str(tmp_path / "r.db"))

        remember_resolution(db, (1920, 1080))

        assert saved_resolution(db) == (1920, 1080)


def make_sysfs(tmp_path, nodes):
    for index, (name, node_index) in nodes.items():
        directory = tmp_path / f"video{index}"
        directory.mkdir()
        if name is not None:
            (directory / "name").write_text(name + "\n")
        if node_index is not None:
            (directory / "index").write_text(f"{node_index}\n")
    return tmp_path


class TestDeviceNames:
    def test_a_name_is_read_from_sysfs(self, tmp_path):
        sysfs = make_sysfs(tmp_path, {0: ("C505 HD Webcam", 0)})

        assert device_name(0, sysfs) == "C505 HD Webcam"

    def test_a_truncated_duplicate_suffix_is_trimmed(self, tmp_path):
        sysfs = make_sysfs(tmp_path, {0: ("Integrated Camera: Integrated C", 0)})

        assert device_name(0, sysfs) == "Integrated Camera"

    def test_a_genuine_colon_in_the_name_is_kept(self, tmp_path):
        sysfs = make_sysfs(tmp_path, {0: ("Logitech: StreamCam", 0)})

        assert device_name(0, sysfs) == "Logitech: StreamCam"

    def test_a_missing_node_has_no_name(self, tmp_path):
        assert device_name(9, tmp_path) is None

    def test_an_empty_name_is_treated_as_missing(self, tmp_path):
        sysfs = make_sysfs(tmp_path, {0: ("   ", 0)})

        assert device_name(0, sysfs) is None

    def test_a_platform_without_sysfs_has_no_names(self, tmp_path):
        assert device_name(0, tmp_path / "does-not-exist") is None


class TestCaptureNodes:
    def test_index_zero_is_a_capture_node(self, tmp_path):
        sysfs = make_sysfs(tmp_path, {0: ("Cam", 0)})

        assert is_capture_node(0, sysfs) is True

    def test_index_one_is_a_metadata_node(self, tmp_path):
        sysfs = make_sysfs(tmp_path, {1: ("Cam", 1)})

        assert is_capture_node(1, sysfs) is False

    def test_an_unknown_node_is_probed_anyway(self, tmp_path):
        assert is_capture_node(0, tmp_path / "does-not-exist") is True

    def test_an_unreadable_index_is_probed_anyway(self, tmp_path):
        sysfs = make_sysfs(tmp_path, {0: ("Cam", None)})

        assert is_capture_node(0, sysfs) is True

    def test_a_nonsense_index_is_probed_anyway(self, tmp_path):
        directory = tmp_path / "video0"
        directory.mkdir()
        (directory / "index").write_text("banana")

        assert is_capture_node(0, tmp_path) is True


class TestScanningWithSysfs:
    def test_metadata_nodes_are_never_opened(self, tmp_path):
        sysfs = make_sysfs(tmp_path, {
            0: ("Integrated Camera", 0),
            1: ("Integrated Camera", 1),
            2: ("C505 HD Webcam", 0),
            3: ("C505 HD Webcam", 1),
        })
        created = []

        probe_devices(4, factory_for({0, 1, 2, 3}, created), sysfs)

        assert [camera.index for camera in created] == [0, 2]

    def test_devices_are_labelled_with_their_names(self, tmp_path):
        sysfs = make_sysfs(tmp_path, {
            0: ("Integrated Camera", 0),
            1: ("Integrated Camera", 1),
            2: ("C505 HD Webcam", 0),
        })

        found = probe_devices(3, factory_for({0, 1, 2}), sysfs)

        assert [device.label for device in found] == [
            "Integrated Camera (640x480)",
            "C505 HD Webcam (640x480)",
        ]

    def test_skipping_a_metadata_node_does_not_count_as_a_gap(self, tmp_path):
        sysfs = make_sysfs(tmp_path, {
            0: ("Cam A", 0), 1: ("Cam A", 1), 2: ("Cam A", 1), 3: ("Cam B", 0),
        })

        found = probe_devices(4, factory_for({0, 3}), sysfs)

        assert [device.index for device in found] == [0, 3]

    def test_without_sysfs_every_index_is_still_probed(self, tmp_path):
        found = probe_devices(3, factory_for({0, 1, 2}), tmp_path / "none")

        assert [device.index for device in found] == [0, 1, 2]
        assert [device.label for device in found] == [
            "Camera 0 (640x480)",
            "Camera 1 (640x480)",
            "Camera 2 (640x480)",
        ]
