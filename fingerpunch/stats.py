from __future__ import annotations

import time
from typing import Any, Protocol, TypedDict

from PySide6.QtCore import QObject, Signal


class TypingSession(Protocol):
    sample_text: str
    start_time: float | None
    text_updated: Any


class SampleDict(TypedDict):
    t: float
    wpm: float
    raw_wpm: float
    errors: int


class StatsDict(TypedDict):
    wpm: float
    accuracy: float
    time: float
    total_chars: int
    keystrokes: int
    efficiency: float
    samples: list[SampleDict]


class StatsWorker(QObject):
    stats_updated = Signal(str, str)

    def __init__(self, app: TypingSession) -> None:
        super().__init__()
        self.app = app
        self.current_text = ""
        self.previous_text = ""
        self.total_keystrokes = 0
        self.deletions = 0
        self.additions = 0
        self.correct_char_events = 0
        self.total_char_events = 0
        self.samples: list[SampleDict] = []
        self.app.text_updated.connect(self.receive_text)

    def receive_text(self, text: str) -> None:
        self.current_text = text
        self._update_keystroke_stats()

    def _final_correct_chars(self) -> int:
        typed_length = len(self.current_text)
        sample_length = len(self.app.sample_text)

        return sum(
            1
            for i in range(min(typed_length, sample_length))
            if self.current_text[i] == self.app.sample_text[i]
        )

    def _accuracy(self) -> float:
        if self.total_char_events == 0:
            return 100.0
        return self.correct_char_events / self.total_char_events * 100

    def record_sample(self) -> None:
        if self.app.start_time is None:
            return

        elapsed = time.time() - self.app.start_time
        if elapsed <= 0:
            return

        minutes = elapsed / 60
        self.samples.append(
            {
                "t": elapsed,
                "wpm": (self._final_correct_chars() / 5) / minutes,
                "raw_wpm": (self.total_char_events / 5) / minutes,
                "errors": self.total_char_events - self.correct_char_events,
            }
        )

    def _record_char_events(self, start: int, end: int) -> None:
        sample_text = self.app.sample_text
        for i in range(start, end):
            if i < len(sample_text):
                self.total_char_events += 1
                if self.current_text[i] == sample_text[i]:
                    self.correct_char_events += 1

    def _update_keystroke_stats(self) -> None:

        prev_len = len(self.previous_text)
        current_len = len(self.current_text)

        if prev_len == current_len:
            if self.previous_text != self.current_text:
                changed_positions = [
                    i for i in range(current_len) if self.current_text[i] != self.previous_text[i]
                ]
                self.total_keystrokes += 2 * len(changed_positions)
                for i in changed_positions:
                    self._record_char_events(i, i + 1)
        elif current_len > prev_len:
            chars_added = current_len - prev_len
            self.additions += chars_added
            self.total_keystrokes += chars_added
            self._record_char_events(prev_len, current_len)
        else:
            chars_deleted = prev_len - current_len
            self.deletions += chars_deleted
            self.total_keystrokes += chars_deleted

        correct_chars = self._final_correct_chars()
        accuracy = self._accuracy()

        if self.app.start_time:
            elapsed = time.time() - self.app.start_time
            wpm = (correct_chars / 5) / (elapsed / 60) if elapsed > 0 else 0
            self.stats_updated.emit(f"{wpm:.2f}", f"{accuracy:.2f}%")

        self.previous_text = self.current_text

    def reset_stats(self) -> None:
        self.total_keystrokes = 0
        self.deletions = 0
        self.additions = 0
        self.correct_char_events = 0
        self.total_char_events = 0
        self.samples = []
        self.previous_text = ""
        self.current_text = ""

    def get_final_stats(self) -> StatsDict:
        typed_length = len(self.current_text)
        correct_chars = self._final_correct_chars()
        accuracy = self._accuracy()

        if self.app.start_time:
            elapsed = time.time() - self.app.start_time
            wpm = (correct_chars / 5) / (elapsed / 60) if elapsed > 0 else 0
        else:
            elapsed = 0
            wpm = 0

        return {
            'wpm': wpm,
            'accuracy': accuracy,
            'time': elapsed,
            'total_chars': typed_length,
            'keystrokes': self.total_keystrokes,
            'efficiency': (correct_chars / self.total_keystrokes * 100) if self.total_keystrokes > 0 else 100.0,
            'samples': list(self.samples),
        }
