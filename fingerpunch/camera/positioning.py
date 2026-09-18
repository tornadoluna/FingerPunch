from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

from fingerpunch.camera.landmarks import LANDMARKS_PER_HAND, LandmarkSnapshot
from fingerpunch.finger_map import Hand

SAMPLE_SECONDS = 3.0
MIN_SAMPLES = 10
MIN_VISIBLE_RATE = 0.7
MIN_CONFIDENCE = 0.6
EDGE_MARGIN = 0.02

NO_FRAMES = "No frames arrived from the camera."
TOO_FEW_FRAMES = "Not enough frames to judge; try again."
NO_HANDS = "No hands detected. Point the camera at your hands on the keyboard."
GOOD = "Both hands are fully visible. The camera is well positioned."

EDGE_NAMES = {"left": "left", "right": "right", "top": "top", "bottom": "bottom"}


class PositioningReport(NamedTuple):
    ok: bool
    messages: tuple[str, ...]
    visible_rate: float
    hands_seen: frozenset[Hand]


def _edges_touched(snapshot: LandmarkSnapshot) -> set[str]:
    touched: set[str] = set()
    for hand in snapshot.hands:
        for point in hand.points:
            if point.x < EDGE_MARGIN:
                touched.add("left")
            if point.x > 1 - EDGE_MARGIN:
                touched.add("right")
            if point.y < EDGE_MARGIN:
                touched.add("top")
            if point.y > 1 - EDGE_MARGIN:
                touched.add("bottom")
    return touched


def evaluate(snapshots: Sequence[LandmarkSnapshot]) -> PositioningReport:
    if not snapshots:
        return PositioningReport(False, (NO_FRAMES,), 0.0, frozenset())
    if len(snapshots) < MIN_SAMPLES:
        return PositioningReport(False, (TOO_FEW_FRAMES,), 0.0, frozenset())

    with_hands = [snapshot for snapshot in snapshots if snapshot.hands]
    visible_rate = len(with_hands) / len(snapshots)
    hands_seen = frozenset(hand.hand for snapshot in with_hands for hand in snapshot.hands)

    if not with_hands:
        return PositioningReport(False, (NO_HANDS,), 0.0, frozenset())

    messages: list[str] = []

    missing = set(Hand) - set(hands_seen)
    for hand in sorted(missing, key=lambda h: h.value):
        messages.append(f"Your {hand.value} hand is not visible.")

    if visible_rate < MIN_VISIBLE_RATE:
        messages.append(
            f"Hands were only visible in {visible_rate * 100:.0f}% of frames;"
            " detection is unsteady."
        )

    edges: set[str] = set()
    for snapshot in with_hands:
        edges |= _edges_touched(snapshot)
    for edge in sorted(edges):
        messages.append(f"Fingers are leaving the {EDGE_NAMES[edge]} of the frame.")

    incomplete = any(
        len(hand.points) != LANDMARKS_PER_HAND for snapshot in with_hands for hand in snapshot.hands
    )
    if incomplete:
        messages.append("Part of a hand is hidden; move it fully into view.")

    confidences = [hand.confidence for snapshot in with_hands for hand in snapshot.hands]
    if confidences and sum(confidences) / len(confidences) < MIN_CONFIDENCE:
        messages.append("Detection is weak; try more light or a closer camera.")

    if messages:
        return PositioningReport(False, tuple(messages), visible_rate, hands_seen)
    return PositioningReport(True, (GOOD,), visible_rate, hands_seen)
