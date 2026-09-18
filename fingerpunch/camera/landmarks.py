from __future__ import annotations

import logging
from typing import Any, NamedTuple, Protocol

from fingerpunch.camera.source import Frame
from fingerpunch.finger_map import Digit, Finger, Hand

logger = logging.getLogger(__name__)

FINGERTIP_LANDMARKS: dict[Digit, int] = {
    Digit.THUMB: 4,
    Digit.INDEX: 8,
    Digit.MIDDLE: 12,
    Digit.RING: 16,
    Digit.PINKY: 20,
}
LANDMARKS_PER_HAND = 21
MAX_HANDS = 2


class LandmarkNotReady(RuntimeError):
    pass


class Point(NamedTuple):
    x: float
    y: float
    z: float


class DetectedHand(NamedTuple):
    hand: Hand
    points: tuple[Point, ...]
    confidence: float

    def fingertip(self, digit: Digit) -> Point:
        return self.points[FINGERTIP_LANDMARKS[digit]]

    def fingertips(self) -> dict[Finger, Point]:
        return {
            Finger(self.hand, digit): self.points[index]
            for digit, index in FINGERTIP_LANDMARKS.items()
        }


class LandmarkSnapshot(NamedTuple):
    timestamp: float
    hands: tuple[DetectedHand, ...]

    def fingertips(self) -> dict[Finger, Point]:
        tips: dict[Finger, Point] = {}
        for hand in self.hands:
            tips.update(hand.fingertips())
        return tips


class HandDetector(Protocol):
    def detect(self, frame: Frame) -> LandmarkSnapshot: ...

    def close(self) -> None: ...


def _hand_from_label(label: str) -> Hand | None:
    normalised = label.strip().lower()
    if normalised == "left":
        return Hand.LEFT
    if normalised == "right":
        return Hand.RIGHT
    return None


def snapshot_from_result(
    result: Any, timestamp: float, flip_handedness: bool = True
) -> LandmarkSnapshot:
    hands: list[DetectedHand] = []
    handedness = getattr(result, "handedness", None) or []
    landmarks = getattr(result, "hand_landmarks", None) or []

    for categories, points in zip(handedness, landmarks):
        if not categories or len(points) != LANDMARKS_PER_HAND:
            continue

        category = categories[0]
        hand = _hand_from_label(getattr(category, "category_name", ""))
        if hand is None:
            continue
        if flip_handedness:
            hand = Hand.RIGHT if hand is Hand.LEFT else Hand.LEFT

        hands.append(
            DetectedHand(
                hand=hand,
                points=tuple(Point(point.x, point.y, point.z) for point in points),
                confidence=float(getattr(category, "score", 0.0)),
            )
        )

    return LandmarkSnapshot(timestamp, tuple(hands))
