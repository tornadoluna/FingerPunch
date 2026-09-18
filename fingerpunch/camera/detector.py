from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fingerpunch.camera.landmarks import (
    MAX_HANDS,
    LandmarkNotReady,
    LandmarkSnapshot,
    snapshot_from_result,
)
from fingerpunch.camera.source import Frame

logger = logging.getLogger(__name__)

MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5


def load_mediapipe() -> Any:
    try:
        import mediapipe
    except ImportError as error:
        raise LandmarkNotReady(
            "MediaPipe is not installed, so hand tracking cannot be used"
        ) from error
    return mediapipe


class MediaPipeDetector:
    def __init__(
        self,
        model_file: Path,
        max_hands: int = MAX_HANDS,
        flip_handedness: bool = False,
    ) -> None:
        mediapipe = load_mediapipe()
        vision = mediapipe.tasks.vision

        options = vision.HandLandmarkerOptions(
            base_options=mediapipe.tasks.BaseOptions(model_asset_path=str(model_file)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        )
        self._mediapipe = mediapipe
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._flip_handedness = flip_handedness
        self._last_stamp_ms = -1

    def detect(self, frame: Frame) -> LandmarkSnapshot:
        image = self._to_image(frame)
        stamp_ms = max(int(frame.timestamp * 1000), self._last_stamp_ms + 1)
        self._last_stamp_ms = stamp_ms

        result = self._landmarker.detect_for_video(image, stamp_ms)
        return snapshot_from_result(result, frame.timestamp, self._flip_handedness)

    def _to_image(self, frame: Frame) -> Any:
        import cv2

        rgb = cv2.cvtColor(frame.data, cv2.COLOR_BGR2RGB)
        return self._mediapipe.Image(
            image_format=self._mediapipe.ImageFormat.SRGB, data=rgb
        )

    def close(self) -> None:
        closer = getattr(self._landmarker, "close", None)
        if closer is not None:
            closer()
