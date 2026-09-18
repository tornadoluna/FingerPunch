import types
from types import SimpleNamespace

import numpy as np
import pytest

from fingerpunch.camera import detector as detector_module
from fingerpunch.camera.detector import MediaPipeDetector, load_mediapipe
from fingerpunch.camera.landmarks import LANDMARKS_PER_HAND, LandmarkNotReady
from fingerpunch.camera.source import Frame


class FakeLandmarker:
    def __init__(self):
        self.calls = []
        self.closed = False
        self.result = SimpleNamespace(handedness=[], hand_landmarks=[])

    def detect_for_video(self, image, stamp_ms):
        self.calls.append((image, stamp_ms))
        return self.result

    def close(self):
        self.closed = True


def fake_mediapipe(landmarker):
    module = types.ModuleType("mediapipe")
    module.Image = lambda image_format, data: SimpleNamespace(format=image_format, data=data)
    module.ImageFormat = SimpleNamespace(SRGB="srgb")
    vision = SimpleNamespace(
        HandLandmarkerOptions=lambda **kwargs: SimpleNamespace(**kwargs),
        RunningMode=SimpleNamespace(VIDEO="video"),
        HandLandmarker=SimpleNamespace(create_from_options=lambda options: landmarker),
    )
    module.tasks = SimpleNamespace(vision=vision, BaseOptions=lambda **kw: SimpleNamespace(**kw))
    return module


@pytest.fixture
def landmarker():
    return FakeLandmarker()


@pytest.fixture
def detector(monkeypatch, landmarker):
    monkeypatch.setattr(detector_module, "load_mediapipe", lambda: fake_mediapipe(landmarker))
    return MediaPipeDetector(model_file="/tmp/fake.task")


def bgr_frame(timestamp=1.0, width=4, height=3):
    data = np.zeros((height, width, 3), dtype=np.uint8)
    data[0, 0] = (255, 0, 0)
    return Frame(timestamp, width, height, data)


class TestConstruction:
    def test_it_asks_for_video_mode_and_the_model_file(self, monkeypatch, landmarker):
        captured = {}

        def options(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(**kwargs)

        module = fake_mediapipe(landmarker)
        module.tasks.vision.HandLandmarkerOptions = options
        monkeypatch.setattr(detector_module, "load_mediapipe", lambda: module)

        MediaPipeDetector(model_file="/models/hand.task")

        assert captured["running_mode"] == "video"
        assert captured["num_hands"] == 2
        assert "hand.task" in str(captured["base_options"].model_asset_path)

    def test_a_missing_mediapipe_reports_landmark_not_ready(self, monkeypatch):
        import builtins

        real_import = builtins.__import__

        def refuse(name, *args, **kwargs):
            if name == "mediapipe":
                raise ImportError("no mediapipe")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", refuse)

        with pytest.raises(LandmarkNotReady, match="MediaPipe is not installed"):
            load_mediapipe()


class TestTimestamps:
    def test_a_frame_time_becomes_milliseconds(self, detector, landmarker):
        detector.detect(bgr_frame(timestamp=2.5))

        assert landmarker.calls[0][1] == 2500

    def test_timestamps_strictly_increase_when_frames_repeat(self, detector, landmarker):
        for _ in range(3):
            detector.detect(bgr_frame(timestamp=1.0))

        stamps = [stamp for _, stamp in landmarker.calls]
        assert stamps == sorted(set(stamps))
        assert len(stamps) == 3

    def test_a_frame_that_goes_backwards_still_advances(self, detector, landmarker):
        detector.detect(bgr_frame(timestamp=10.0))
        detector.detect(bgr_frame(timestamp=1.0))

        first, second = (stamp for _, stamp in landmarker.calls)
        assert second > first


class TestImageConversion:
    def test_frames_are_converted_from_bgr_to_rgb(self, detector, landmarker):
        detector.detect(bgr_frame())

        image = landmarker.calls[0][0]
        assert tuple(image.data[0, 0]) == (0, 0, 255)

    def test_the_image_is_tagged_as_srgb(self, detector, landmarker):
        detector.detect(bgr_frame())

        assert landmarker.calls[0][0].format == "srgb"


class TestResults:
    def test_an_empty_result_becomes_an_empty_snapshot(self, detector):
        snapshot = detector.detect(bgr_frame(timestamp=7.0))

        assert snapshot.hands == ()
        assert snapshot.timestamp == 7.0

    def test_a_detected_hand_is_converted(self, detector, landmarker):
        landmarker.result = SimpleNamespace(
            handedness=[[SimpleNamespace(category_name="Left", score=0.9)]],
            hand_landmarks=[[SimpleNamespace(x=0.1, y=0.2, z=0.3)] * LANDMARKS_PER_HAND],
        )

        snapshot = detector.detect(bgr_frame())

        assert len(snapshot.hands) == 1
        assert snapshot.hands[0].confidence == pytest.approx(0.9)


class TestShutdown:
    def test_closing_closes_the_landmarker(self, detector, landmarker):
        detector.close()

        assert landmarker.closed is True

    def test_closing_a_landmarker_without_close_is_harmless(self, monkeypatch):
        bare = SimpleNamespace(detect_for_video=lambda image, stamp: None)
        monkeypatch.setattr(detector_module, "load_mediapipe", lambda: fake_mediapipe(bare))

        MediaPipeDetector(model_file="/tmp/fake.task").close()
