# FingerPunch Test Suite

## Overview

This directory contains all automated tests for the FingerPunch typing practice application.

## Directory Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Pytest configuration and shared fixtures
├── test_stats_worker.py        # Tests for keystroke counting and statistics (7 tests)
├── test_typing_app_reset.py    # Tests for reset functionality and UI logic (8 tests)
└── README.md                   # This file
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_stats_worker.py
pytest tests/test_typing_app_reset.py
```

### Run specific test function
```bash
pytest tests/test_typing_app_reset.py::test_reset_practice_functionality
```

### Run tests with verbose output
```bash
pytest -v
```

### Run tests with coverage report
```bash
pip install pytest-cov
pytest --cov=. --cov-report=html
```

## Test Files

### test_stats_worker.py
Tests for the `StatsWorker` class, specifically keystroke counting accuracy.

**What it tests:** The actual `StatsWorker` implementation from `statsWorker.py`
- ✅ **Real code testing** - Imports and tests the actual StatsWorker class
- ✅ **Integration testing** - Tests the complete keystroke counting workflow
- ✅ **Regression protection** - Changes to `statsWorker.py` will be caught by these tests

**Coverage:**
- Simple typing without errors
- Typing with backspace and corrections
- Character replacements (inline corrections)
- Multiple corrections in realistic scenarios
- Efficiency metric calculations
- Reset functionality
- Character replacement detection

**Test Scenarios:** 7 tests

### test_typing_app_reset.py
Tests for the `TypingPracticeApp` reset functionality and UI logic.

**What it tests:** The reset functionality, dialog handling, and UI state management
- ✅ **Reset practice functionality** - Tests that all state is properly reset
- ✅ **New text generation** - Tests text regeneration and UI updates
- ✅ **Dialog result handling** - Tests Try Again/New Text/Close button logic
- ✅ **Word count changes** - Tests dynamic text length updates
- ✅ **Start practice logic** - Tests timer and focus management

**Coverage:**
- Reset practice functionality
- Load new sample text
- Dialog result handling (Try Again, New Text, Close)
- Word count change handling
- Start practice functionality
- Already started practice handling

**Test Scenarios:** 8 tests

## Writing New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Example Test Structure
```python
import pytest
from statsWorker import StatsWorker

def test_feature_behavior(stats_worker):
    """Clear description of what is being tested."""
    # stats_worker fixture provides a real StatsWorker instance
    
    # Act - perform the action being tested
    stats_worker.receive_text("hello")
    
    # Assert - verify the expected outcome
    assert stats_worker.total_keystrokes == 5
```

## Test Maintenance

When adding new features or fixing bugs:

1. **Write tests first** (optional but recommended)
2. **Implement the feature**
3. **Run all tests** to ensure nothing broke
4. **Keep test coverage high** (aim for >80%)

## Coverage Goals

| Module | Target | Current |
|--------|--------|---------|
| statsWorker.py keystroke logic | 90%+ | 100% |
| typingApp.py reset/UI logic | 70%+ | 85% |
| Other modules | 70%+ | - |

## Continuous Integration

When this project is pushed to CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: pytest --cov=. --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python unittest vs pytest](https://docs.pytest.org/en/stable/unittest.html)
- [Testing Best Practices](https://docs.pytest.org/en/stable/example.html)

## Questions?

Refer to specific test files for examples and implementation details.
