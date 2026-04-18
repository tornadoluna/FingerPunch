# FingerPunch Test Suite

## Overview

This directory contains all automated tests for the FingerPunch typing practice application.

## Directory Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Pytest configuration and shared fixtures
├── test_stats_worker.py        # Tests for keystroke counting and statistics
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
```

### Run specific test function
```bash
pytest tests/test_stats_worker.py::test_scenario_1_simple_typing
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

**Coverage:**
- Simple typing without errors
- Typing with backspace and corrections
- Character replacements (inline corrections)
- Multiple corrections in realistic scenarios
- Efficiency metric calculations

**Test Scenarios:**
- ✅ Test 1: Simple typing (no mistakes)
- ✅ Test 2: Type → Backspace all → Retype
- ✅ Test 3: Correct first try
- ✅ Test 4: Multiple corrections
- ✅ Test 5: Efficiency metric calculation

## Writing New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Example Test Structure
```python
def test_feature_behavior():
    """Clear description of what is being tested."""
    # Arrange - set up test data
    counter = NewKeystrokeCounter()
    
    # Act - perform the action being tested
    counter.count_new("hello")
    
    # Assert - verify the expected outcome
    assert counter.total_keystrokes == 5
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
| statsWorker.py | 90%+ | 100% |
| typingApp.py | 70%+ | - |
| textGenerator.py | 80%+ | - |

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

