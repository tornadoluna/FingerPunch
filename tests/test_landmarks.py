from types import SimpleNamespace

import pytest

from fingerpunch.camera.landmarks import (
    FINGERTIP_LANDMARKS,
    LANDMARKS_PER_HAND,
    DetectedHand,
    LandmarkSnapshot,
    Point,
    snapshot_from_result,
)
from fingerpunch.finger_map import Digit, Finger, Hand


def points(count=LANDMARKS_PER_HAND, offset=0.0):
    return [SimpleNamespace(x=i / 100 + offset, y=i / 50 + offset, z=i / 200) for i in range(count)]


def result_for(*hands):
    return SimpleNamespace(
        handedness=[[SimpleNamespace(category_name=label, score=score)] for label, score, _ in hands],
        hand_landmarks=[marks for _, _, marks in hands],
    )


class TestConversion:
    def test_a_single_hand_becomes_a_snapshot(self):
        snapshot = snapshot_from_result(result_for(("Left", 0.9, points())), 12.5)

        assert snapshot.timestamp == 12.5
        assert len(snapshot.hands) == 1
        assert len(snapshot.hands[0].points) == LANDMARKS_PER_HAND
        assert snapshot.hands[0].confidence == pytest.approx(0.9)

    def test_handedness_is_taken_at_face_value(self):
        snapshot = snapshot_from_result(result_for(("Left", 0.9, points())), 0.0)

        assert snapshot.hands[0].hand is Hand.LEFT

    def test_a_right_hand_is_reported_as_right(self):
        snapshot = snapshot_from_result(result_for(("Right", 0.9, points())), 0.0)

        assert snapshot.hands[0].hand is Hand.RIGHT

    def test_handedness_can_be_flipped_for_a_mirrored_camera(self):
        snapshot = snapshot_from_result(
            result_for(("Left", 0.9, points())), 0.0, flip_handedness=True
        )

        assert snapshot.hands[0].hand is Hand.RIGHT

    def test_both_hands_are_converted(self):
        snapshot = snapshot_from_result(
            result_for(("Left", 0.9, points()), ("Right", 0.8, points(offset=0.5))), 0.0
        )

        assert {hand.hand for hand in snapshot.hands} == {Hand.LEFT, Hand.RIGHT}

    def test_coordinates_are_carried_through(self):
        marks = points()
        snapshot = snapshot_from_result(result_for(("Left", 1.0, marks)), 0.0)

        assert snapshot.hands[0].points[0] == Point(marks[0].x, marks[0].y, marks[0].z)

    def test_an_empty_result_yields_no_hands(self):
        snapshot = snapshot_from_result(SimpleNamespace(handedness=[], hand_landmarks=[]), 3.0)

        assert snapshot.hands == ()
        assert snapshot.timestamp == 3.0

    def test_a_result_missing_its_fields_yields_no_hands(self):
        assert snapshot_from_result(SimpleNamespace(), 0.0).hands == ()

    def test_an_incomplete_hand_is_discarded(self):
        snapshot = snapshot_from_result(result_for(("Left", 0.9, points(count=11))), 0.0)

        assert snapshot.hands == ()

    def test_an_unrecognised_handedness_label_is_discarded(self):
        snapshot = snapshot_from_result(result_for(("Middle", 0.9, points())), 0.0)

        assert snapshot.hands == ()

    def test_a_hand_with_no_handedness_category_is_discarded(self):
        result = SimpleNamespace(handedness=[[]], hand_landmarks=[points()])

        assert snapshot_from_result(result, 0.0).hands == ()

    @pytest.mark.parametrize("label", ["left", "LEFT", " Left "])
    def test_the_label_is_matched_loosely(self, label):
        snapshot = snapshot_from_result(result_for((label, 0.9, points())), 0.0)

        assert snapshot.hands[0].hand is Hand.LEFT


class TestFingertips:
    def test_every_digit_maps_to_a_landmark(self):
        assert set(FINGERTIP_LANDMARKS) == set(Digit)

    def test_the_mapping_matches_mediapipe(self):
        assert FINGERTIP_LANDMARKS == {
            Digit.THUMB: 4,
            Digit.INDEX: 8,
            Digit.MIDDLE: 12,
            Digit.RING: 16,
            Digit.PINKY: 20,
        }

    def test_a_fingertip_is_the_expected_landmark(self):
        marks = tuple(Point(i, i, i) for i in range(LANDMARKS_PER_HAND))
        hand = DetectedHand(Hand.LEFT, marks, 1.0)

        assert hand.fingertip(Digit.INDEX) == marks[8]

    def test_a_hand_reports_five_fingertips(self):
        marks = tuple(Point(i, i, i) for i in range(LANDMARKS_PER_HAND))
        hand = DetectedHand(Hand.RIGHT, marks, 1.0)

        tips = hand.fingertips()
        assert len(tips) == 5
        assert all(finger.hand is Hand.RIGHT for finger in tips)
        assert tips[Finger(Hand.RIGHT, Digit.PINKY)] == marks[20]

    def test_a_snapshot_reports_ten_fingertips_for_two_hands(self):
        marks = tuple(Point(i, i, i) for i in range(LANDMARKS_PER_HAND))
        snapshot = LandmarkSnapshot(
            0.0, (DetectedHand(Hand.LEFT, marks, 1.0), DetectedHand(Hand.RIGHT, marks, 1.0))
        )

        assert len(snapshot.fingertips()) == 10

    def test_a_snapshot_with_one_hand_reports_five(self):
        marks = tuple(Point(i, i, i) for i in range(LANDMARKS_PER_HAND))
        snapshot = LandmarkSnapshot(0.0, (DetectedHand(Hand.LEFT, marks, 1.0),))

        assert len(snapshot.fingertips()) == 5

    def test_an_empty_snapshot_reports_none(self):
        assert LandmarkSnapshot(0.0, ()).fingertips() == {}
