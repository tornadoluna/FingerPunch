import pytest
from PySide6.QtGui import QImage

from fingerpunch.camera.landmarks import (
    FINGERTIP_LANDMARKS,
    LANDMARKS_PER_HAND,
    DetectedHand,
    LandmarkSnapshot,
    Point,
)
from fingerpunch.camera.overlay import HAND_CONNECTIONS, draw_hands
from fingerpunch.finger_map import Hand


def blank(width=160, height=90):
    image = QImage(width, height, QImage.Format_RGB32)
    image.fill(0xFF000000)
    return image


def a_hand(side=Hand.LEFT, spread=0.4):
    points = tuple(
        Point(0.5 + spread * (i % 5 - 2) / 5, 0.5 + spread * (i // 5 - 2) / 5, 0.0)
        for i in range(LANDMARKS_PER_HAND)
    )
    return DetectedHand(side, points, 0.95)


def painted_pixels(image):
    return sum(
        1
        for y in range(image.height())
        for x in range(image.width())
        if image.pixel(x, y) != 0xFF000000
    )


class TestTopology:
    def test_every_connection_is_within_a_hand(self):
        for start, end in HAND_CONNECTIONS:
            assert 0 <= start < LANDMARKS_PER_HAND
            assert 0 <= end < LANDMARKS_PER_HAND

    def test_every_landmark_is_connected_to_something(self):
        connected = {index for pair in HAND_CONNECTIONS for index in pair}

        assert connected == set(range(LANDMARKS_PER_HAND))

    def test_the_wrist_anchors_the_hand(self):
        from_wrist = [pair for pair in HAND_CONNECTIONS if 0 in pair]

        assert len(from_wrist) >= 3

    def test_each_fingertip_terminates_a_chain(self):
        for tip in FINGERTIP_LANDMARKS.values():
            assert any(tip in pair for pair in HAND_CONNECTIONS)


class TestDrawing:
    def test_an_empty_snapshot_returns_the_image_untouched(self, qapp):
        image = blank()

        result = draw_hands(image, LandmarkSnapshot(0.0, ()))

        assert result is image
        assert painted_pixels(result) == 0

    def test_a_hand_paints_onto_the_image(self, qapp):
        result = draw_hands(blank(), LandmarkSnapshot(0.0, (a_hand(),)))

        assert painted_pixels(result) > 0

    def test_the_original_image_is_not_modified(self, qapp):
        image = blank()

        draw_hands(image, LandmarkSnapshot(0.0, (a_hand(),)))

        assert painted_pixels(image) == 0

    def test_two_hands_paint_more_than_one(self, qapp):
        one = draw_hands(blank(), LandmarkSnapshot(0.0, (a_hand(Hand.LEFT),)))
        two = draw_hands(
            blank(), LandmarkSnapshot(0.0, (a_hand(Hand.LEFT), a_hand(Hand.RIGHT, spread=0.2)))
        )

        assert painted_pixels(two) > painted_pixels(one)

    def test_the_hands_are_drawn_in_different_colours(self, qapp):
        left = draw_hands(blank(), LandmarkSnapshot(0.0, (a_hand(Hand.LEFT),)))
        right = draw_hands(blank(), LandmarkSnapshot(0.0, (a_hand(Hand.RIGHT),)))

        left_colors = {left.pixel(x, y) for x in range(left.width()) for y in range(left.height())}
        right_colors = {
            right.pixel(x, y) for x in range(right.width()) for y in range(right.height())
        }
        assert left_colors != right_colors

    def test_the_image_keeps_its_size(self, qapp):
        result = draw_hands(blank(200, 120), LandmarkSnapshot(0.0, (a_hand(),)))

        assert (result.width(), result.height()) == (200, 120)

    @pytest.mark.parametrize("count", [1, 5, 20])
    def test_a_short_hand_does_not_raise(self, qapp, count):
        points = tuple(Point(0.5, 0.5, 0.0) for _ in range(count))

        draw_hands(blank(), LandmarkSnapshot(0.0, (DetectedHand(Hand.LEFT, points, 1.0),)))

    def test_landmarks_outside_the_frame_do_not_raise(self, qapp):
        points = tuple(Point(-2.0, 3.0, 0.0) for _ in range(LANDMARKS_PER_HAND))

        draw_hands(blank(), LandmarkSnapshot(0.0, (DetectedHand(Hand.RIGHT, points, 1.0),)))
