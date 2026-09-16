# FingerPunch

[![CI](https://github.com/tornadoluna/FingerPunch/actions/workflows/ci.yml/badge.svg)](https://github.com/tornadoluna/FingerPunch/actions/workflows/ci.yml)

*A camera-integrated typing practice application that will help users learn optimal finger placement for efficient typing.*

## Vision

FingerPunch will fill a niche in typing practice by combining traditional typing practice with computer vision technology to provide real-time feedback on finger placement. Unlike standard typing tutors that focus only on speed and accuracy, FingerPunch will teach users to use the optimal fingers for each key, leading to more efficient, ergonomic, and faster typing.

### Personal Motivation

As someone who developed the inefficient habit of "fingerpunching" - typing with only two fingers - I created FingerPunch to help unlearn this bad habit. Traditional typing practice focuses on speed and accuracy but doesn't address finger placement. FingerPunch will provide the targeted feedback needed to develop proper typing technique and break inefficient habits.

## Key Goals

### 1. Optimal Finger Training
- Camera Integration: Real-time finger tracking to monitor which fingers press which keys
- Finger Mapping: Learn the standard QWERTY finger placement (e.g., left pinky for A/S/Z/X)
- Correction Feedback: Visual and audio cues when using incorrect fingers
- Progress Tracking: Monitor improvement in finger accuracy over time

### 2. Comprehensive Typing Practice
- Real-time Metrics: WPM, accuracy, and efficiency calculations
- Color-coded Feedback: Visual indication of correct/incorrect typing
- Customizable Difficulty: Adjustable text length and complexity
- Session Statistics: Detailed performance analysis

### 3. Ergonomic Awareness
- Posture Guidance: Tips for proper typing posture
- Customizable Layouts: Support for different keyboard layouts
## Current Features

### Implemented
- Text Generation: Intelligent sentence generation using parts-of-speech
- Real-time Typing Interface: Color-coded feedback (green/red for correct/incorrect)
- Performance Metrics: WPM, accuracy, and progress tracking
- Results Display: Comprehensive statistics dialog
- Reset Functionality: "Try Again" and "New Text" options
- Text Customization: Adjustable word count (10-500 words)
- Professional UI: Modern, responsive design with dynamic resizing
- Automated Testing: 303 pytest tests with 99% coverage, enforced in CI (see Testing & Quality below)
- Data Persistence: SQLite database for session history and progress tracking
- History Viewer: View past sessions with detailed statistics and trends
- Performance Charts: Visual graphs showing WPM and accuracy progress over time
- Advanced Analytics: MonkeyType-style statistics including personal bests, improvement metrics, and performance by text length
- Streak Tracking: Monitor daily practice streaks and build typing habits
- Session Management: Delete a session from the history when a result is not worth keeping
- Paste Protection: The typing area refuses pasted and dropped text, so a result reflects real typing
- Versioned Storage: Schema migrations tracked with `PRAGMA user_version`, so the database upgrades in place
- Error Handling: Storage failures are reported in the interface rather than crashing, and a failed save still shows your results
- Logging: Rotating log file beside the database, with unhandled exceptions recorded
- Incremental Rendering: Only the characters that changed are repainted, so keystroke cost stays flat as sample length grows

### In Development
- Camera Integration: OpenCV camera feed capture with MediaPipe finger processing (not yet started)

### Future Enhancements
- Improve text generation with markov chains or GPT-3 for more natural sentences
- Adaptive Difficulty: Dynamic text complexity based on user performance
- Keyboard Layout Support: QWERTY, Dvorak, Colemak, etc.
- Accessibility Features: Screen reader support, high contrast modes
## Technology Stack
- Frontend: PySide6 (Qt6) - Modern, cross-platform GUI
- Backend: Python 3.12+ - Core application logic
- Testing: pytest + pytest-cov - Comprehensive test suite
- Data Visualization: matplotlib - Performance charts and progress tracking
- Computer Vision: OpenCV + MediaPipe (planned) - Camera feed capture and finger processing
- Data Storage: SQLite - Session persistence
- Build System: Standard Python packaging
## Quick Start

### Prerequisites
```bash
Python 3.12+
pip
```

### Installation
```bash
# Clone the repository
git clone https://github.com/tornadoluna/FingerPunch.git
cd FingerPunch

# Install dependencies
pip install -r requirements.txt
# ...or, to also run the tests/linter: pip install -r requirements-dev.txt

# Install the app (provides the `fingerpunch` command)
pip install -e .

# Run the application
fingerpunch
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=fingerpunch --cov-report=html

# Run specific test file
pytest tests/test_stats_worker.py
```
## Where Your Data Lives

Sessions are stored in a SQLite database under your platform's user data
directory, not in the working directory you launch from:

| Platform | Location |
| --- | --- |
| Linux | `~/.local/share/FingerPunch/typingStats.db` |
| macOS | `~/Library/Application Support/FingerPunch/typingStats.db` |
| Windows | `%LOCALAPPDATA%\FingerPunch\typingStats.db` |

To print the exact path on your machine:

```bash
python -c "from fingerpunch.paths import default_database_path; print(default_database_path())"
```

A rotating log file, `fingerpunch.log`, sits beside the database in the same
directory. It records startup, finished sessions, storage failures and any
unhandled exception, and rotates at 512 KB keeping three previous files.

The schema is versioned with `PRAGMA user_version` and migrated in place on
startup, so upgrading the app keeps existing history. Databases created before
versioning was introduced are detected and brought up to date automatically.

If you used the app before the database moved, copy your old `typingStats.db`
to the path above to keep your history.

## How to Use

### Basic Typing Practice
1. Launch the application
2. Select desired text length (10-500 words)
3. Click "Start" or begin typing to start the timer
4. Type the displayed text as accurately as possible
5. View results in the completion dialog
6. Choose "Try Again" or "New Text" to continue

### Understanding Metrics
- WPM (Words Per Minute): Typing speed
- Accuracy: Percentage of correct characters
- Efficiency: Correct keystrokes / total keystrokes
- Progress: Real-time completion percentage

### Viewing Progress History
1. Click the "View History" button in the main interface
2. Switch between three main tabs for different views:
   - **📊 Sessions**: Detailed session data in a table, with the option to delete a session
   - **📈 Analytics**: Interactive charts with dropdown selector for Performance Overview, Recent Activity, and Performance by Length
   - **🚀 Progress**: Personal Bests, improvement metrics, and Streaks
3. Summary statistics show your overall progress and best performances

### Finger Training (Future)
- Camera Setup: Position camera to view keyboard and hands
- Finger Mapping: App will guide optimal finger placement
- Real-time Feedback: Visual cues for incorrect finger usage
- Practice Drills: Targeted exercises for problem keys
## Project Structure
```
FingerPunch/
├── fingerpunch/                  # Application package
│   ├── __main__.py               # Entry point
│   ├── stats.py                  # Statistics and keystroke tracking
│   ├── text_generator.py         # Sentence generation
│   ├── paths.py                  # User data directory resolution
│   ├── text_diff.py              # Changed-range calculation shared by stats and UI
│   ├── logging_config.py         # Log file setup and exception hook
│   ├── data_manager.py           # SQLite session persistence and migrations
│   └── ui/                       # Qt presentation layer
│       ├── main_window.py        # Main practice window
│       ├── results_dialog.py     # End-of-session results
│       ├── history_dialog.py     # History, analytics, progress
│       ├── widgets.py            # Typing input and shared dialogs
│       └── styles.py             # Shared dark-theme design system
├── tests/                        # Test suite
│   ├── conftest.py               # Shared Qt and window fixtures
│   ├── test_stats_worker.py      # Keystroke, accuracy and sampling
│   ├── test_data_manager.py      # SQLite persistence and migrations
│   ├── test_paths.py             # Data directory resolution
│   ├── test_text_diff.py         # Changed-range calculation
│   ├── test_stats_incremental.py # Incremental counting vs brute force
│   ├── test_logging_config.py    # Logging setup and exception hook
│   ├── test_error_handling.py    # Storage failure boundaries
│   ├── test_main_entry.py        # Startup and startup failure
│   ├── test_main_window.py       # Session lifecycle and rendering
│   ├── test_results_dialog.py    # End-of-session results
│   ├── test_history_dialog.py    # History table, charts, deletion
│   ├── test_typing_input.py      # Paste protection
│   ├── test_widgets.py           # Message and confirmation dialogs
│   ├── test_text_generator.py    # Text generation
│   └── README.md                 # Test documentation
├── .github/workflows/ci.yml      # Lint, test and coverage gate
├── pyproject.toml                # Packaging, entry point, lint config
├── requirements.txt              # Runtime dependencies
├── requirements-dev.txt          # Dev dependencies (test/lint tooling)
├── pytest.ini                    # Test configuration
└── README.md                     # This file
```

## Testing & Quality

### Test Coverage
- fingerpunch/logging_config.py: 100%
- fingerpunch/paths.py: 100%
- fingerpunch/text_diff.py: 100%
- fingerpunch/ui/main_window.py: 100%
- fingerpunch/ui/results_dialog.py: 100%
- fingerpunch/ui/widgets.py: 100%
- fingerpunch/data_manager.py: 99%
- fingerpunch/stats.py: 99%
- fingerpunch/ui/history_dialog.py: 98%
- fingerpunch/ui/styles.py: 98%
- fingerpunch/__main__.py: 96%
- fingerpunch/text_generator.py: 95%
- Overall: 99% across 303 automated tests

CI fails if overall coverage drops below 90%. Qt tests run against a real
widget on the offscreen platform rather than against mocks, so they exercise
the same signal wiring the running application uses.

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=fingerpunch --cov-report=html

# Specific module
pytest tests/test_stats_worker.py -v

# Lint
ruff check .
```

## Development Roadmap

### Phase 1: Core Functionality
- [x] Basic typing interface
- [x] Real-time metrics
- [x] Text generation
- [x] Results display
- [x] Comprehensive testing

### Phase 2: Data Persistence
- [x] SQLite database integration
- [x] Session history storage
- [x] Progress visualization
- [ ] User profiles

### Phase 3: Camera Integration
- [ ] OpenCV setup
- [ ] MediaPipe finger tracking
- [ ] Real-time finger to keystroke mapping
- [ ] Finger placement feedback

### Phase 4: Advanced Features
- [ ] Adaptive difficulty
- [ ] Multi-language support
- [ ] Performance analytics

## Performance Metrics

### Current Benchmarks
- Startup Time: < 2 seconds
- Real-time Updates: 100ms intervals
- Memory Usage: ~50MB
- Test Execution: < 1 second for full suite

### Accuracy Metrics
- Keystroke Counting: 100% accurate (including backspace)
- WPM Calculation: Standard 5-character word formula
- Accuracy Tracking: Character-level precision

## Privacy & Security

- No Data Collection: All practice data stored locally
- Camera Usage: Optional, only for finger tracking features
- Local Storage: SQLite database for session history
- No External Dependencies: Self-contained application

## License

This project is licensed under the GNU Lesser General Public License v3.0 (LGPLv3) - see the LICENSE file for details.

## Acknowledgments

- PySide6: Modern Qt6 bindings for Python
- pytest: Comprehensive testing framework
- OpenCV: Computer vision library for camera feed capture
- MediaPipe: Computer vision library for finger processing
- Qt Framework: Professional GUI toolkit

## Support

- Issues: GitHub Issues (https://github.com/tornadoluna/FingerPunch/issues)
- Discussions: GitHub Discussions (https://github.com/tornadoluna/FingerPunch/discussions)
- Documentation: See tests/README.md for testing details

## Mission Statement

To help typists of all levels improve their typing technique by providing real-time feedback on finger placement.

---

Ready to improve your typing technique? Start practicing with FingerPunch today!
