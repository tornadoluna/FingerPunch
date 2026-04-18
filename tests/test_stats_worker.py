"""
Test suite for StatsWorker keystroke counting.

These tests verify the actual StatsWorker implementation from statsWorker.py,
ensuring that changes to the real code are properly tested.
"""

import pytest
from statsWorker import StatsWorker


class MockApp:
    """Mock application object that StatsWorker expects."""
    def __init__(self, sample_text="hello world"):
        self.sample_text = sample_text
        self.start_time = None
        # Mock the signal - we don't need it for these tests
        self.text_updated = type('Signal', (), {'connect': lambda x, y: None})()


@pytest.fixture
def mock_app():
    """Provide a mock app for testing."""
    return MockApp()


@pytest.fixture
def stats_worker(mock_app):
    """Provide a StatsWorker instance for testing."""
    worker = StatsWorker(mock_app)
    # Reset stats to clean state
    worker.reset_stats()
    return worker


def test_scenario_1_simple_typing(stats_worker):
    """Test 1: Simple typing without errors."""
    # Type "hello" character by character
    stats_worker.receive_text("h")
    stats_worker.receive_text("he")
    stats_worker.receive_text("hel")
    stats_worker.receive_text("hell")
    stats_worker.receive_text("hello")

    assert stats_worker.total_keystrokes == 5, f"Expected 5 keystrokes, got {stats_worker.total_keystrokes}"
    assert stats_worker.additions == 5, f"Expected 5 additions, got {stats_worker.additions}"
    assert stats_worker.deletions == 0, f"Expected 0 deletions, got {stats_worker.deletions}"


def test_scenario_2_type_and_backspace(stats_worker):
    """Test 2: Type, make error, backspace and fix."""
    # Type "hello"
    stats_worker.receive_text("h")
    stats_worker.receive_text("he")
    stats_worker.receive_text("hel")
    stats_worker.receive_text("hell")
    stats_worker.receive_text("hello")

    # Backspace all characters
    stats_worker.receive_text("hell")  # backspace 'o'
    stats_worker.receive_text("hel")   # backspace 'l'
    stats_worker.receive_text("he")    # backspace 'l'
    stats_worker.receive_text("h")     # backspace 'e'
    stats_worker.receive_text("")      # backspace 'h'

    # Type "hi"
    stats_worker.receive_text("h")
    stats_worker.receive_text("hi")

    assert stats_worker.total_keystrokes == 12, f"Expected 12 keystrokes, got {stats_worker.total_keystrokes}"
    assert stats_worker.additions == 7, f"Expected 7 additions, got {stats_worker.additions}"
    assert stats_worker.deletions == 5, f"Expected 5 deletions, got {stats_worker.deletions}"


def test_scenario_3_correction_mid_word(stats_worker):
    """Test 3: Correct single character mid-word."""
    # Type "hallo" (correct typing)
    stats_worker.receive_text("h")
    stats_worker.receive_text("ha")
    stats_worker.receive_text("hal")
    stats_worker.receive_text("hall")
    stats_worker.receive_text("hallo")

    assert stats_worker.total_keystrokes == 5, f"Expected 5 keystrokes, got {stats_worker.total_keystrokes}"
    assert stats_worker.additions == 5, f"Expected 5 additions, got {stats_worker.additions}"
    assert stats_worker.deletions == 0, f"Expected 0 deletions, got {stats_worker.deletions}"


def test_scenario_4_multiple_corrections(stats_worker):
    """Test 4: Multiple corrections in realistic scenario."""
    # Type "the quick brown" with corrections
    stats_worker.receive_text("t")
    stats_worker.receive_text("th")
    stats_worker.receive_text("the")
    stats_worker.receive_text("the ")
    stats_worker.receive_text("the q")
    stats_worker.receive_text("the qu")
    stats_worker.receive_text("the qui")
    stats_worker.receive_text("the quic")
    stats_worker.receive_text("the quick")
    stats_worker.receive_text("the quick ")
    stats_worker.receive_text("the quick b")
    stats_worker.receive_text("the quick br")
    stats_worker.receive_text("the quick bro")
    stats_worker.receive_text("the quick brow")
    stats_worker.receive_text("the quick brown")

    assert stats_worker.total_keystrokes == 15, f"Expected 15 keystrokes, got {stats_worker.total_keystrokes}"
    assert stats_worker.additions == 15, f"Expected 15 additions, got {stats_worker.additions}"
    assert stats_worker.deletions == 0, f"Expected 0 deletions, got {stats_worker.deletions}"


def test_scenario_5_efficiency_metric():
    """Test 5: Verify efficiency metric calculation."""
    # Create a worker with sample text that matches what we'll type
    mock_app = MockApp(sample_text="hhhhhhhhhh")  # 10 h's
    worker = StatsWorker(mock_app)
    worker.reset_stats()

    # Set up mock app with start time
    worker.app.start_time = 0  # Mock start time

    # Type 10 correct characters
    for i in range(1, 11):
        worker.receive_text("h" * i)

    # Get final stats
    stats = worker.get_final_stats()

    assert stats['total_chars'] == 10, f"Expected 10 total chars, got {stats['total_chars']}"
    assert stats['keystrokes'] == 10, f"Expected 10 keystrokes, got {stats['keystrokes']}"
    assert stats['efficiency'] == 100.0, f"Expected 100% efficiency, got {stats['efficiency']}"


def test_reset_stats_functionality(stats_worker):
    """Test that reset_stats properly clears all counters."""
    # Add some keystrokes
    stats_worker.receive_text("hello")
    assert stats_worker.total_keystrokes > 0

    # Reset stats
    stats_worker.reset_stats()

    # Verify all counters are zero
    assert stats_worker.total_keystrokes == 0
    assert stats_worker.additions == 0
    assert stats_worker.deletions == 0
    assert stats_worker.previous_text == ""
    assert stats_worker.current_text == ""


def test_character_replacement_detection(stats_worker):
    """Test that character replacements (corrections) are counted properly."""
    # Start with "abc"
    stats_worker.receive_text("a")
    stats_worker.receive_text("ab")
    stats_worker.receive_text("abc")

    # Replace 'b' with 'x' (simulating backspace + new char)
    # This should trigger the same-length different-content logic
    stats_worker.receive_text("axc")  # 'b' → 'x'

    # The logic should detect this as a 2-keystroke correction
    assert stats_worker.total_keystrokes == 5, f"Expected 5 keystrokes (3 add + 2 correction), got {stats_worker.total_keystrokes}"

