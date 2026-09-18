import pytest

from fingerpunch.camera.landmarks import (
    LANDMARKS_PER_HAND,
    DetectedHand,
    LandmarkSnapshot,
    Point,
)
from fingerpunch.camera.positioning import (
    GOOD,
    MIN_SAMPLES,
    NO_FRAMES,
    NO_HANDS,
    TOO_FEW_FRAMES,
    evaluate,
)
from fingerpunch.finger_map import Hand


def hand(side=Hand.LEFT, x=0.5, y=0.5, confidence=0.95, count=LANDMARKS_PER_HAND):
    points = tuple(
        Point(x + (i % 5 - 2) * 0.02, y + (i // 5 - 2) * 0.02, 0.0) for i in range(count)
    )
    return DetectedHand(side, points, confidence)


def stream(count=20, hands=None):
    hands = (hand(Hand.LEFT, 0.3), hand(Hand.RIGHT, 0.7)) if hands is None else hands
    return [LandmarkSnapshot(float(i), tuple(hands)) for i in range(count)]


def messages_of(report):
    return " ".join(report.messages)


class TestNotEnoughData:
    def test_no_frames_at_all(self):
        report = evaluate([])

        assert report.ok is False
        assert report.messages == (NO_FRAMES,)

    def test_too_few_frames_to_judge(self):
        report = evaluate(stream(count=MIN_SAMPLES - 1))

        assert report.ok is False
        assert report.messages == (TOO_FEW_FRAMES,)

    def test_frames_but_never_a_hand(self):
        report = evaluate([LandmarkSnapshot(float(i), ()) for i in range(20)])

        assert report.ok is False
        assert report.messages == (NO_HANDS,)
        assert report.hands_seen == frozenset()


class TestGoodPositioning:
    def test_two_centred_hands_pass(self):
        report = evaluate(stream())

        assert report.ok is True
        assert report.messages == (GOOD,)
        assert report.visible_rate == pytest.approx(1.0)
        assert report.hands_seen == {Hand.LEFT, Hand.RIGHT}

    def test_an_occasional_dropped_frame_still_passes(self):
        snapshots = stream(count=20)
        snapshots[3] = LandmarkSnapshot(3.0, ())
        snapshots[11] = LandmarkSnapshot(11.0, ())

        assert evaluate(snapshots).ok is True


class TestMissingHands:
    def test_only_the_left_hand_is_reported(self):
        report = evaluate(stream(hands=(hand(Hand.LEFT),)))

        assert report.ok is False
        assert "right hand is not visible" in messages_of(report)
        assert report.hands_seen == {Hand.LEFT}

    def test_only_the_right_hand_is_reported(self):
        report = evaluate(stream(hands=(hand(Hand.RIGHT),)))

        assert "left hand is not visible" in messages_of(report)


class TestSteadiness:
    def test_intermittent_detection_is_reported(self):
        snapshots = stream(count=20)
        for i in range(0, 20, 2):
            snapshots[i] = LandmarkSnapshot(float(i), ())

        report = evaluate(snapshots)

        assert report.ok is False
        assert "detection is unsteady" in messages_of(report)
        assert report.visible_rate == pytest.approx(0.5)


class TestClipping:
    @pytest.mark.parametrize("x, y, edge", [
        (0.005, 0.5, "left"),
        (0.995, 0.5, "right"),
        (0.5, 0.005, "top"),
        (0.5, 0.995, "bottom"),
    ])
    def test_a_hand_against_an_edge_is_reported(self, x, y, edge):
        points = tuple(Point(x, y, 0.0) for _ in range(LANDMARKS_PER_HAND))
        hands = (DetectedHand(Hand.LEFT, points, 0.9), hand(Hand.RIGHT, 0.7))

        report = evaluate(stream(hands=hands))

        assert report.ok is False
        assert f"leaving the {edge} of the frame" in messages_of(report)

    def test_a_centred_hand_reports_no_edges(self):
        assert "leaving the" not in messages_of(evaluate(stream()))

    def test_every_touched_edge_is_named(self):
        points = (Point(0.005, 0.005, 0.0),) + tuple(
            Point(0.995, 0.995, 0.0) for _ in range(LANDMARKS_PER_HAND - 1)
        )
        hands = (DetectedHand(Hand.LEFT, points, 0.9), hand(Hand.RIGHT, 0.7))

        report = evaluate(stream(hands=hands))

        for edge in ("left", "right", "top", "bottom"):
            assert f"leaving the {edge}" in messages_of(report)


class TestConfidence:
    def test_weak_detection_is_reported(self):
        hands = (hand(Hand.LEFT, 0.3, confidence=0.3), hand(Hand.RIGHT, 0.7, confidence=0.3))

        report = evaluate(stream(hands=hands))

        assert report.ok is False
        assert "Detection is weak" in messages_of(report)

    def test_confident_detection_is_not_reported(self):
        assert "Detection is weak" not in messages_of(evaluate(stream()))


class TestIncompleteHands:
    def test_a_partial_hand_is_reported(self):
        hands = (hand(Hand.LEFT, 0.3, count=12), hand(Hand.RIGHT, 0.7))

        report = evaluate(stream(hands=hands))

        assert report.ok is False
        assert "Part of a hand is hidden" in messages_of(report)


class TestCombinedProblems:
    def test_several_problems_are_all_reported(self):
        hands = (hand(Hand.LEFT, 0.01, confidence=0.2),)

        report = evaluate(stream(hands=hands))

        text = messages_of(report)
        assert "right hand is not visible" in text
        assert "leaving the left" in text
        assert "Detection is weak" in text

    def test_a_failing_report_never_claims_success(self):
        report = evaluate(stream(hands=(hand(Hand.LEFT),)))

        assert report.ok is False
        assert GOOD not in messages_of(report)
