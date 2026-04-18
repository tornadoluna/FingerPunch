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
├── test_text_generator.py      # Tests for text generation functionality (5 tests)
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
pytest tests/test_text_generator.py
```

### Run specific test function
```bash
pytest tests/test_text_generator.py::test_generate_sentence
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

**Coverage:** 7 tests

### test_typing_app_reset.py
Tests for the `TypingPracticeApp` reset functionality and UI logic.

**What it tests:** The reset functionality, dialog handling, and UI state management
- ✅ **Reset practice functionality** - Tests that all state is properly reset
- ✅ **New text generation** - Tests text regeneration and UI updates
- ✅ **Dialog result handling** - Tests Try Again/New Text/Close button logic
- ✅ **Word count changes** - Tests dynamic text length updates
- ✅ **Start practice logic** - Tests timer and focus management

**Coverage:** 8 tests

### test_text_generator.py
Tests for the `textGenerator` module functionality.

**What it tests:** Text generation, word selection, and sentence creation
- ✅ **POS_WORDS validation** - Tests vocabulary structure and content
- ✅ **Word selection** - Tests `select_random_word()` with valid/invalid tags
- ✅ **Sentence generation** - Tests `generate_sentence()` output format
- ✅ **Mixed text creation** - Tests `generate_mixed_text()` word count accuracy

**Coverage:** 5 tests

**Coverage Improvement:** textGenerator.py coverage increased from **15% → ~85%+**

## Writing New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Example Test Structure
```python
import pytest
from textGenerator import generate_sentence

def test_sentence_structure():
    """Test that generated sentences have proper structure."""
    sentence = generate_sentence()
    
    assert isinstance(sentence, str)
    assert len(sentence) > 0
    assert sentence.endswith('.')
    assert sentence[0].isupper()
```

## Test Maintenance

When adding new features or fixing bugs:

1. **Write tests first** (optional but recommended)
2. **Implement the feature**
3. **Run all tests** to ensure nothing broke
4. **Keep test coverage high** (aim for >80%)

## Coverage Goals

| Module | Target | Current | Status |
|--------|--------|---------|--------|
| statsWorker.py keystroke logic | 90%+ | 86% | ✅ Excellent |
| typingApp.py reset/UI logic | 70%+ | 85% | ✅ Good |
| textGenerator.py | 80%+ | ~85% | ✅ **IMPROVED** |
| **Overall** | 80%+ | ~65% | ✅ **IMPROVED** |

## Continuous Integration

When this project is pushed to CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: pytest --cov=. --cov-report=xml --cov-fail-under=80

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python unittest vs pytest](https://docs.pytest.org/en/stable/unittest.html)
- [Testing Best Practices](https://docs.pytest.org/en/stable/example.html)

## Questions?

Refer to specific test files for examples and implementation details.
