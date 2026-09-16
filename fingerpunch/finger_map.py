from __future__ import annotations

from enum import Enum
from typing import NamedTuple


class Hand(Enum):
    LEFT = "left"
    RIGHT = "right"


class Digit(Enum):
    THUMB = "thumb"
    INDEX = "index"
    MIDDLE = "middle"
    RING = "ring"
    PINKY = "pinky"


class Finger(NamedTuple):
    hand: Hand
    digit: Digit

    def __str__(self) -> str:
        return f"{self.hand.value} {self.digit.value}"


_ASSIGNED_KEYS: dict[Finger, str] = {
    Finger(Hand.LEFT, Digit.PINKY): "`1qaz",
    Finger(Hand.LEFT, Digit.RING): "2wsx",
    Finger(Hand.LEFT, Digit.MIDDLE): "3edc",
    Finger(Hand.LEFT, Digit.INDEX): "45rtfgvb",
    Finger(Hand.LEFT, Digit.THUMB): " ",
    Finger(Hand.RIGHT, Digit.THUMB): " ",
    Finger(Hand.RIGHT, Digit.INDEX): "67yuhjnm",
    Finger(Hand.RIGHT, Digit.MIDDLE): "8ik,",
    Finger(Hand.RIGHT, Digit.RING): "9ol.",
    Finger(Hand.RIGHT, Digit.PINKY): r"0-=[]\;'/p",
}

HOME_KEYS: dict[str, Finger] = {
    "a": Finger(Hand.LEFT, Digit.PINKY),
    "s": Finger(Hand.LEFT, Digit.RING),
    "d": Finger(Hand.LEFT, Digit.MIDDLE),
    "f": Finger(Hand.LEFT, Digit.INDEX),
    "j": Finger(Hand.RIGHT, Digit.INDEX),
    "k": Finger(Hand.RIGHT, Digit.MIDDLE),
    "l": Finger(Hand.RIGHT, Digit.RING),
    ";": Finger(Hand.RIGHT, Digit.PINKY),
}


def _build_key_index() -> dict[str, frozenset[Finger]]:
    index: dict[str, set[Finger]] = {}
    for finger, keys in _ASSIGNED_KEYS.items():
        for key in keys:
            index.setdefault(key, set()).add(finger)
    return {key: frozenset(fingers) for key, fingers in index.items()}


_KEY_INDEX = _build_key_index()

FINGERS: tuple[Finger, ...] = tuple(_ASSIGNED_KEYS)


def expected_fingers(key: str) -> frozenset[Finger]:
    return _KEY_INDEX.get(key.lower(), frozenset())
