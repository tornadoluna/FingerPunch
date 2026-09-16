import pytest

from fingerpunch.text_diff import dirty_range

SAMPLE_LENGTH = 100


class TestDirtyRange:
    def test_appending_one_character_dirties_one_position(self):
        previous = "the quick brown"
        assert dirty_range(previous, previous + "x", SAMPLE_LENGTH) == (15, 16)

    def test_deleting_one_character_dirties_one_position(self):
        current = "the quick brow"
        assert dirty_range(current + "n", current, SAMPLE_LENGTH) == (14, 15)

    def test_no_change_dirties_nothing(self):
        assert dirty_range("unchanged", "unchanged", SAMPLE_LENGTH) == (9, 9)

    def test_changing_one_character_in_place_dirties_only_that_one(self):
        assert dirty_range("abcdef", "abXdef", SAMPLE_LENGTH) == (2, 6)

    def test_a_first_character_change_dirties_from_the_start(self):
        assert dirty_range("abcdef", "Xbcdef", SAMPLE_LENGTH) == (0, 6)

    def test_clearing_everything_dirties_the_whole_previous_text(self):
        assert dirty_range("abcdef", "", SAMPLE_LENGTH) == (0, 6)

    def test_typing_into_an_empty_field_dirties_what_was_typed(self):
        assert dirty_range("", "abc", SAMPLE_LENGTH) == (0, 3)

    def test_the_range_never_runs_past_the_sample(self):
        assert dirty_range("", "a" * 500, SAMPLE_LENGTH) == (0, SAMPLE_LENGTH)

    def test_edits_beyond_the_sample_produce_an_empty_range(self):
        long_previous = "a" * 150
        start, end = dirty_range(long_previous, long_previous + "b", SAMPLE_LENGTH)
        assert start == end

    def test_the_range_is_never_inverted(self):
        cases = [
            ("abc", ""),
            ("", "abc"),
            ("abc", "abc"),
            ("a" * 200, "b"),
            ("a" * 150, "a" * 150 + "b"),
            ("a" * 150 + "b", "a" * 150),
        ]
        for previous, current in cases:
            start, end = dirty_range(previous, current, SAMPLE_LENGTH)
            assert start <= end, (previous, current)

    @pytest.mark.parametrize("previous, current", [
        ("hello", "hello world"),
        ("hello world", "hello"),
        ("abc", "xyz"),
        ("", ""),
        ("same", "same"),
    ])
    def test_everything_outside_the_range_is_genuinely_unchanged(self, previous, current):
        start, end = dirty_range(previous, current, SAMPLE_LENGTH)

        for i in range(start):
            assert previous[i] == current[i]
        limit = min(len(previous), len(current))
        for i in range(end, limit):
            assert previous[i] == current[i]


class TestRepaintDoesMinimalWork:
    def test_one_keystroke_repaints_one_character(self, window, monkeypatch):
        window.sample_text = "the quick brown fox jumps over the lazy dog"
        window.input_edit.setPlainText("the quick brown")

        painted = []
        original = window._repaint_sample

        def spy(typed_text):
            painted.append(dirty_range(window._highlighted, typed_text, len(window.sample_text)))
            return original(typed_text)

        monkeypatch.setattr(window, "_repaint_sample", spy)
        window.input_edit.setPlainText("the quick brownf")

        start, end = painted[-1]
        assert end - start == 1

    def test_a_keystroke_late_in_a_long_sample_still_repaints_one_character(self, window):
        sample = "abcdefghij" * 40
        window.sample_text = sample
        window.input_edit.setPlainText(sample[:395])

        start, end = dirty_range(window._highlighted, sample[:396], len(sample))

        assert (start, end) == (395, 396)
