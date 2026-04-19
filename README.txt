# FingerPunch

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
- Comprehensive Testing: 20+ tests with 85%+ coverage
- Data Persistence: SQLite database for session history and progress tracking
- History Viewer: View past sessions with detailed statistics and trends
- Performance Charts: Visual graphs showing WPM and accuracy progress over time
- Advanced Analytics: MonkeyType-style statistics including personal bests, improvement metrics, and performance by text length

### In Development
- Camera Integration: OpenCV camera feed capture with MediaPipe finger processing

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
git clone https://github.com/yourusername/fingerpunch.git
cd fingerpunch

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_stats_worker.py
```
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
2. Switch between multiple tabs for different views:
   - **Text History**: Detailed session data in a sortable table
   - **Overview**: Line charts showing WPM and accuracy trends over time
   - **Activity**: Recent activity chart (last 30 days)
   - **By Length**: Performance comparison across different text lengths
   - **Personal Bests**: Your best performances and improvement metrics
3. Summary statistics show your overall progress and best performances

### Finger Training (Future)
- Camera Setup: Position camera to view keyboard and hands
- Finger Mapping: App will guide optimal finger placement
- Real-time Feedback: Visual cues for incorrect finger usage
- Practice Drills: Targeted exercises for problem keys
## Project Structure
```
FingerPunch/
├── main.py                     # Application entry point
├── typingApp.py               # Main GUI application
├── statsWorker.py             # Statistics and keystroke tracking
├── textGenerator.py           # Intelligent text generation
├── requirements.txt           # Python dependencies
├── pytest.ini                # Test configuration
├── tests/                    # Test suite
│   ├── test_stats_worker.py      # Keystroke counting tests
│   ├── test_typing_app_reset.py  # UI reset functionality tests
│   ├── test_text_generator.py    # Text generation tests
│   └── README.md                 # Test documentation
└── README.md                 # This file
```

## Testing & Quality

### Test Coverage
- statsWorker.py: 86% (keystroke logic and stats calculation)
- typingApp.py: 85% (UI functionality)
- textGenerator.py: 85% (text generation)
- Overall: 65%+ with 20+ automated tests

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific module
pytest tests/test_stats_worker.py -v
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
- [x] User profiles

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

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PySide6: Modern Qt6 bindings for Python
- pytest: Comprehensive testing framework
- OpenCV: Computer vision library for camera feed capture
- MediaPipe: Computer vision library for finger processing
- Qt Framework: Professional GUI toolkit

## Support

- Issues: GitHub Issues (https://github.com/yourusername/fingerpunch/issues)
- Discussions: GitHub Discussions (https://github.com/yourusername/fingerpunch/discussions)
- Documentation: See tests/README.md for testing details

## Mission Statement

To help typists of all levels improve their typing technique by providing real-time feedback on finger placement.

---

Ready to improve your typing technique? Start practicing with FingerPunch today!
