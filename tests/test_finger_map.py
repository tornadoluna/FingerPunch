import string

import pytest

from fingerpunch.finger_map import (
    FINGERS,
    HOME_KEYS,
    Digit,
    Finger,
    Hand,
    expected_fingers,
)


class TestCoverage:
    def test_all_ten_fingers_are_defined(self):
        assert len(FINGERS) == 10
        assert len(set(FINGERS)) == 10

    def test_every_hand_and_digit_combination_exists(self):
        assert set(FINGERS) == {Finger(hand, digit) for hand in Hand for digit in Digit}

    @pytest.mark.parametrize("letter", string.ascii_lowercase)
    def test_every_letter_has_exactly_one_finger(self, letter):
        assert len(expected_fingers(letter)) == 1

    @pytest.mark.parametrize("digit", string.digits)
    def test_every_number_row_key_has_exactly_one_finger(self, digit):
        assert len(expected_fingers(digit)) == 1

    def test_every_finger_except_the_thumbs_owns_letters(self):
        for finger in FINGERS:
            if finger.digit is Digit.THUMB:
                continue
            owned = [c for c in string.ascii_lowercase if finger in expected_fingers(c)]
            assert owned, finger

    def test_no_key_other_than_space_is_shared(self):
        printable = string.ascii_lowercase + string.digits + r"`-=[]\;',./"
        shared = [key for key in printable if len(expected_fingers(key)) > 1]
        assert shared == []


class TestAssignments:
    def test_the_home_row_sits_under_its_own_fingers(self):
        for key, finger in HOME_KEYS.items():
            assert expected_fingers(key) == frozenset({finger}), key

    @pytest.mark.parametrize("key, hand, digit", [
        ("q", Hand.LEFT, Digit.PINKY),
        ("z", Hand.LEFT, Digit.PINKY),
        ("w", Hand.LEFT, Digit.RING),
        ("e", Hand.LEFT, Digit.MIDDLE),
        ("r", Hand.LEFT, Digit.INDEX),
        ("t", Hand.LEFT, Digit.INDEX),
        ("b", Hand.LEFT, Digit.INDEX),
        ("y", Hand.RIGHT, Digit.INDEX),
        ("n", Hand.RIGHT, Digit.INDEX),
        ("m", Hand.RIGHT, Digit.INDEX),
        ("i", Hand.RIGHT, Digit.MIDDLE),
        ("o", Hand.RIGHT, Digit.RING),
        ("p", Hand.RIGHT, Digit.PINKY),
        (".", Hand.RIGHT, Digit.RING),
        (",", Hand.RIGHT, Digit.MIDDLE),
    ])
    def test_known_keys_land_on_the_touch_typing_finger(self, key, hand, digit):
        assert expected_fingers(key) == frozenset({Finger(hand, digit)})

    def test_the_index_fingers_each_cover_two_columns(self):
        left = [c for c in string.ascii_lowercase
                if Finger(Hand.LEFT, Digit.INDEX) in expected_fingers(c)]
        right = [c for c in string.ascii_lowercase
                 if Finger(Hand.RIGHT, Digit.INDEX) in expected_fingers(c)]
        assert sorted(left) == list("bfgrtv")
        assert sorted(right) == list("hjmnuy")

    def test_space_belongs_to_either_thumb(self):
        assert expected_fingers(" ") == frozenset({
            Finger(Hand.LEFT, Digit.THUMB),
            Finger(Hand.RIGHT, Digit.THUMB),
        })

    def test_the_thumbs_own_nothing_but_space(self):
        printable = string.ascii_lowercase + string.digits + r"`-=[]\;',./"
        for finger in (Finger(Hand.LEFT, Digit.THUMB), Finger(Hand.RIGHT, Digit.THUMB)):
            assert not any(finger in expected_fingers(key) for key in printable)


class TestLookup:
    @pytest.mark.parametrize("letter", string.ascii_lowercase)
    def test_uppercase_resolves_to_the_same_finger_as_lowercase(self, letter):
        assert expected_fingers(letter.upper()) == expected_fingers(letter)

    @pytest.mark.parametrize("key", ["\t", "\n", "\x00", "€", "😀"])
    def test_an_unmapped_key_yields_no_finger(self, key):
        assert expected_fingers(key) == frozenset()

    def test_an_empty_key_yields_no_finger(self):
        assert expected_fingers("") == frozenset()

    def test_a_multi_character_string_yields_no_finger(self):
        assert expected_fingers("ab") == frozenset()

    def test_the_result_cannot_be_mutated_by_a_caller(self):
        assert isinstance(expected_fingers("a"), frozenset)


class TestFingerIdentity:
    def test_fingers_read_as_hand_and_digit(self):
        assert str(Finger(Hand.LEFT, Digit.PINKY)) == "left pinky"
        assert str(Finger(Hand.RIGHT, Digit.INDEX)) == "right index"

    def test_the_same_finger_compares_equal(self):
        assert Finger(Hand.LEFT, Digit.INDEX) == Finger(Hand.LEFT, Digit.INDEX)

    def test_hands_are_distinct(self):
        assert Finger(Hand.LEFT, Digit.INDEX) != Finger(Hand.RIGHT, Digit.INDEX)

    def test_fingers_can_be_used_as_dictionary_keys(self):
        counts = {finger: 0 for finger in FINGERS}
        counts[Finger(Hand.LEFT, Digit.PINKY)] += 1

        assert counts[Finger(Hand.LEFT, Digit.PINKY)] == 1
