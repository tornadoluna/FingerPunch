import random

import pytest

from fingerpunch.stats import StatsWorker


class FakeSession:
    def __init__(self, sample_text):
        self.sample_text = sample_text
        self.start_time = None
        self.text_updated = type("Signal", (), {"connect": lambda self, slot: None})()


def brute_force_correct(typed, sample):
    return sum(1 for i in range(min(len(typed), len(sample))) if typed[i] == sample[i])


def worker_for(sample):
    worker = StatsWorker(FakeSession(sample))
    worker.reset_stats()
    return worker


class TestIncrementalCorrectCount:
    @pytest.mark.parametrize("sample, keystrokes", [
        ("hello world", ["h", "he", "hel", "hell", "hello"]),
        ("hello", ["x", "xe", "x", "", "h", "he"]),
        ("abc", ["abc", "ab", "a", "", "abc"]),
        ("abc", ["xyz", "ayz", "abz", "abc"]),
        ("abc", ["abcdef", "abc"]),
    ])
    def test_it_matches_brute_force_at_every_step(self, sample, keystrokes):
        worker = worker_for(sample)

        for typed in keystrokes:
            worker.receive_text(typed)
            assert worker.correct_chars == brute_force_correct(typed, sample), typed

    def test_typing_past_the_end_of_the_sample_is_ignored(self):
        worker = worker_for("ab")

        worker.receive_text("abcdefgh")

        assert worker.correct_chars == 2

    def test_an_empty_sample_never_counts_anything(self):
        worker = worker_for("")

        worker.receive_text("anything at all")

        assert worker.correct_chars == 0

    def test_resetting_clears_the_count(self):
        worker = worker_for("hello")
        worker.receive_text("hello")
        assert worker.correct_chars == 5

        worker.reset_stats()

        assert worker.correct_chars == 0

    @pytest.mark.parametrize("seed", range(25))
    def test_random_edit_sequences_stay_in_step_with_brute_force(self, seed):
        rng = random.Random(seed)
        alphabet = "abcde"
        sample = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 40)))
        worker = worker_for(sample)

        typed = ""
        for _ in range(60):
            action = rng.random()
            if action < 0.45 or not typed:
                typed += rng.choice(alphabet)
            elif action < 0.75:
                typed = typed[:-1]
            elif action < 0.9:
                index = rng.randrange(len(typed))
                typed = typed[:index] + rng.choice(alphabet) + typed[index + 1:]
            else:
                typed = typed[: rng.randrange(len(typed) + 1)]

            worker.receive_text(typed)
            assert worker.correct_chars == brute_force_correct(typed, sample), (
                f"seed={seed} typed={typed!r} sample={sample!r}"
            )

    @pytest.mark.parametrize("seed", range(10))
    def test_wpm_matches_a_freshly_counted_worker(self, seed):
        rng = random.Random(seed)
        sample = "the quick brown fox jumps over the lazy dog"
        worker = worker_for(sample)

        typed = ""
        for _ in range(40):
            if rng.random() < 0.7 or not typed:
                typed += rng.choice("the quickbrownfxjmpsvlazydg")
            else:
                typed = typed[:-1]
            worker.receive_text(typed)

        assert worker._final_correct_chars() == brute_force_correct(typed, sample)
