# Testing Framework Design

**Purpose**: Automated testing framework to validate every major update to the fall detection system.

**Philosophy**: Test early, test often, fail fast.

---

## 🏗️ Testing Architecture

### 4-Layer Testing Pyramid

```
                      ┌─────────────────┐
                      │  E2E Tests (5%) │  ← Slow, comprehensive
                      │  Full pipeline  │
                      └─────────────────┘
                    ┌───────────────────────┐
                    │ Integration Tests (15%)│  ← Component interaction
                    │  Module chains        │
                    └───────────────────────┘
                ┌─────────────────────────────────┐
                │   Component Tests (30%)         │  ← Individual modules
                │   Serial reader, analyzer, etc. │
                └─────────────────────────────────┘
        ┌───────────────────────────────────────────────┐
        │         Unit Tests (50%)                      │  ← Fast, focused
        │  Functions, algorithms, data parsing          │
        └───────────────────────────────────────────────┘
```

---

## 📝 Test Categories

### 1. Unit Tests (`tests/unit/`)

**Target**: Individual functions and algorithms

**Examples**:
- JSON parsing logic
- Temporal smoothing algorithm
- Metric calculations (precision, recall)
- Data validation functions

**Characteristics**:
- ⚡ Fast (< 10ms per test)
- 🔒 No external dependencies
- 🎯 Single responsibility
- 🤖 Run on every commit

**Example Test**:
```python
# tests/unit/test_temporal_smoothing.py
import pytest
from src.local_testing.detection_logic import TemporalSmoother

def test_temporal_smoother_triggers_on_majority():
    """Verify fall event triggers when 60% of buffer shows fall."""
    smoother = TemporalSmoother(buffer_size=5, threshold=0.6)

    # Feed 3 fall detections (60%)
    smoother.add(True)   # fall
    smoother.add(True)   # fall
    smoother.add(False)  # no fall
    smoother.add(True)   # fall
    smoother.add(False)  # no fall

    assert smoother.is_fall_event() == True

def test_temporal_smoother_no_trigger_below_threshold():
    """Verify no trigger when below 60% threshold."""
    smoother = TemporalSmoother(buffer_size=5, threshold=0.6)

    # Feed 2 fall detections (40%)
    smoother.add(True)   # fall
    smoother.add(False)  # no fall
    smoother.add(False)  # no fall
    smoother.add(True)   # fall
    smoother.add(False)  # no fall

    assert smoother.is_fall_event() == False

def test_temporal_smoother_buffer_overflow():
    """Verify buffer correctly discards old values."""
    smoother = TemporalSmoother(buffer_size=3, threshold=0.6)

    smoother.add(True)   # [T]
    smoother.add(True)   # [T, T]
    smoother.add(True)   # [T, T, T] → 100% fall
    assert smoother.is_fall_event() == True

    smoother.add(False)  # [T, T, F] → 66% fall
    assert smoother.is_fall_event() == True

    smoother.add(False)  # [T, F, F] → 33% fall
    smoother.add(False)  # [F, F, F] → 0% fall
    assert smoother.is_fall_event() == False
```

---

### 2. Component Tests (`tests/component/`)

**Target**: Individual modules (serial reader, metrics analyzer, etc.)

**Examples**:
- Serial reader can parse valid JSON
- Metrics analyzer calculates correct precision/recall
- Dashboard updates without crashing

**Characteristics**:
- 🕐 Medium speed (100ms - 1s per test)
- 🔌 May use mocks for hardware
- 📦 Tests one module at a time
- 🤖 Run before merge

**Example Test**:
```python
# tests/component/test_serial_reader.py
import pytest
from src.local_testing.grove_serial_reader import GroveSerialReader
from unittest.mock import Mock, patch

@pytest.fixture
def mock_serial():
    """Mock serial port that returns test data."""
    mock = Mock()
    mock.is_open = True
    mock.in_waiting = 100
    return mock

def test_serial_reader_parses_valid_json(mock_serial):
    """Test parsing of valid detection JSON."""
    test_json = '{"timestamp": 12345, "fps": 30.0, "detections": [{"class": "fall", "confidence": 0.85}], "fall_event": true}\n'
    mock_serial.readline.return_value = test_json.encode()

    with patch('serial.Serial', return_value=mock_serial):
        reader = GroveSerialReader(port='COM3')
        data = reader.read_frame()

    assert data is not None
    assert data['timestamp'] == 12345
    assert data['fps'] == 30.0
    assert data['fall_event'] == True
    assert len(data['detections']) == 1
    assert data['detections'][0]['class'] == 'fall'

def test_serial_reader_handles_malformed_json(mock_serial):
    """Test graceful handling of corrupted data."""
    mock_serial.readline.return_value = b'{invalid json\n'

    with patch('serial.Serial', return_value=mock_serial):
        reader = GroveSerialReader(port='COM3')
        data = reader.read_frame()

    assert data is None  # Should return None, not crash

def test_serial_reader_auto_reconnect(mock_serial):
    """Test auto-reconnection after disconnect."""
    mock_serial.is_open = False

    with patch('serial.Serial', return_value=mock_serial):
        reader = GroveSerialReader(port='COM3', auto_reconnect=True)
        reader.connect()

    # Should attempt reconnection
    assert mock_serial.open.called
```

---

### 3. Integration Tests (`tests/integration/`)

**Target**: Multiple components working together

**Examples**:
- Serial reader → Parser → Metrics analyzer chain
- Detection data → Dashboard visualization
- Logger → CSV export → Metrics calculation

**Characteristics**:
- ⏱️ Slower (1-10s per test)
- 🔗 Tests component interactions
- 🎭 Uses mock hardware or test fixtures
- 🤖 Run before release

**Example Test**:
```python
# tests/integration/test_detection_pipeline.py
import pytest
import json
from pathlib import Path
from src.local_testing.grove_serial_reader import GroveSerialReader
from src.local_testing.metrics_analyzer import MetricsAnalyzer
from unittest.mock import patch, Mock

@pytest.fixture
def test_detection_stream():
    """Load test detection data from fixture."""
    fixture_path = Path('tests/fixtures/mock_detections.json')
    with open(fixture_path, 'r') as f:
        return json.load(f)

def test_full_pipeline_with_mock_data(test_detection_stream, tmp_path):
    """Test serial → parser → metrics → CSV pipeline."""

    # Setup mock serial that returns test data
    mock_serial = Mock()
    mock_serial.is_open = True

    detection_lines = [
        json.dumps(det) + '\n' for det in test_detection_stream['scenario_1_actual_fall']
    ]
    mock_serial.readline.side_effect = [line.encode() for line in detection_lines]

    # Run pipeline
    with patch('serial.Serial', return_value=mock_serial):
        reader = GroveSerialReader(port='COM3')
        analyzer = MetricsAnalyzer()

        # Process all frames
        for _ in range(len(detection_lines)):
            frame_data = reader.read_frame()
            if frame_data:
                analyzer.add_frame(frame_data)

        # Export to CSV
        csv_path = tmp_path / "test_output.csv"
        analyzer.export_csv(csv_path)

    # Verify CSV was created and contains data
    assert csv_path.exists()

    import pandas as pd
    df = pd.read_csv(csv_path)
    assert len(df) == 6  # 6 frames in scenario_1
    assert 'class' in df.columns
    assert 'confidence' in df.columns

    # Verify fall event was detected
    metrics = analyzer.get_metrics()
    assert metrics['fall_events'] >= 1

def test_precision_recall_calculation(tmp_path):
    """Test metrics calculation against ground truth."""

    # Load test data
    detections = [
        {'timestamp': 1.0, 'fall_event': True},   # TP
        {'timestamp': 2.0, 'fall_event': True},   # TP
        {'timestamp': 3.0, 'fall_event': False},  # TN
        {'timestamp': 4.0, 'fall_event': True},   # FP (not in ground truth)
        {'timestamp': 5.0, 'fall_event': False},  # FN (missed, was in ground truth)
    ]

    ground_truth = {
        'fall_events': [
            {'start_sec': 0.5, 'end_sec': 2.5},  # Covers timestamp 1.0 and 2.0
            {'start_sec': 4.5, 'end_sec': 5.5},  # Covers timestamp 5.0 (missed)
        ]
    }

    analyzer = MetricsAnalyzer()
    for det in detections:
        analyzer.add_frame(det)

    metrics = analyzer.calculate_metrics(ground_truth)

    # Expected: TP=2, FP=1, FN=1
    # Precision = TP / (TP + FP) = 2 / (2 + 1) = 0.667
    # Recall = TP / (TP + FN) = 2 / (2 + 1) = 0.667

    assert abs(metrics['precision'] - 0.667) < 0.01
    assert abs(metrics['recall'] - 0.667) < 0.01
```

---

### 4. End-to-End Tests (`tests/e2e/`)

**Target**: Full system with real hardware

**Examples**:
- Complete test session with Grove V2 hardware
- 10-minute continuous operation
- Performance validation against targets

**Characteristics**:
- 🐌 Slow (minutes to hours)
- 🔌 Requires real hardware
- 🎯 Tests production scenarios
- 🤖 Run manually or nightly

**Example Test**:
```python
# tests/e2e/test_grove_hardware.py
import pytest
import time
from src.local_testing.grove_serial_reader import GroveSerialReader
from src.local_testing.metrics_analyzer import MetricsAnalyzer

@pytest.mark.hardware
@pytest.mark.slow
def test_grove_continuous_operation():
    """Test Grove Vision AI V2 runs continuously for 10 minutes."""

    reader = GroveSerialReader(port='COM3', auto_reconnect=True)
    analyzer = MetricsAnalyzer()

    start_time = time.time()
    duration = 600  # 10 minutes
    frame_count = 0
    error_count = 0

    while time.time() - start_time < duration:
        try:
            frame_data = reader.read_frame()
            if frame_data:
                analyzer.add_frame(frame_data)
                frame_count += 1
        except Exception as e:
            error_count += 1
            print(f"Error: {e}")

    elapsed = time.time() - start_time
    avg_fps = frame_count / elapsed

    # Assertions
    assert frame_count > 0, "No frames received"
    assert avg_fps >= 20, f"FPS too low: {avg_fps:.1f}"
    assert error_count < frame_count * 0.01, "Error rate > 1%"

    print(f"\n✅ 10-minute test passed:")
    print(f"   Frames: {frame_count}")
    print(f"   Avg FPS: {avg_fps:.1f}")
    print(f"   Errors: {error_count}")

@pytest.mark.hardware
@pytest.mark.slow
def test_grove_fall_detection_accuracy(ground_truth_file):
    """Test fall detection accuracy against controlled tests."""

    # This test requires:
    # 1. Grove V2 set up and running
    # 2. Perform controlled falls in front of camera
    # 3. Ground truth annotations ready

    pytest.skip("Manual test - requires controlled fall setup")

    # Load ground truth
    import json
    with open(ground_truth_file, 'r') as f:
        gt = json.load(f)

    # Run detection
    reader = GroveSerialReader(port='COM3')
    analyzer = MetricsAnalyzer()

    # Collect data for duration of test
    # ... implementation ...

    # Calculate metrics
    metrics = analyzer.calculate_metrics(gt)

    # Assert performance targets
    assert metrics['recall'] >= 0.90, f"Recall too low: {metrics['recall']:.2%}"
    assert metrics['precision'] >= 0.70, f"Precision too low: {metrics['precision']:.2%}"
```

---

## 🤖 Continuous Testing Workflow

### Git Hooks (Pre-commit)
```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running unit tests..."
pytest tests/unit/ -v --maxfail=1

if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed. Commit blocked."
    exit 1
fi

echo "✅ Unit tests passed."
```

### Pre-merge Checks
```bash
# Run before merging to main
pytest tests/unit/ tests/component/ -v --cov=src
```

### Nightly Tests
```bash
# Scheduled via GitHub Actions or cron
pytest tests/ -v --html=report.html
```

---

## 📊 Test Fixtures & Mock Data

### Directory Structure
```
tests/
├── fixtures/
│   ├── mock_detections.json         # Simulated detection data
│   ├── ground_truth_sample.json     # Sample ground truth
│   ├── invalid_json_samples.txt     # Malformed data for error handling
│   └── performance_baseline.json    # Expected performance benchmarks
├── unit/
├── component/
├── integration/
└── e2e/
```

### Mock Detection Data Format
```json
{
  "scenario_1_actual_fall": [
    {
      "timestamp": 1000,
      "fps": 30.0,
      "detections": [
        {"class": "fall", "class_id": 0, "confidence": 0.87, "bbox": {"x": 100, "y": 80, "w": 120, "h": 160}}
      ],
      "fall_event": true
    }
  ],
  "scenario_2_false_alarm": [
    {
      "timestamp": 2000,
      "fps": 30.0,
      "detections": [
        {"class": "sitting", "class_id": 2, "confidence": 0.91, "bbox": {"x": 110, "y": 90, "w": 100, "h": 140}}
      ],
      "fall_event": false
    }
  ]
}
```

---

## 🎯 Test Coverage Requirements

### Minimum Coverage Targets

| Component | Coverage | Test Types |
|-----------|----------|------------|
| `grove_serial_reader.py` | 90% | Unit + Component |
| `metrics_analyzer.py` | 95% | Unit + Integration |
| `detection_logic.py` | 100% | Unit |
| `live_dashboard.py` | 70% | Component |
| `annotate_ground_truth.py` | 60% | Manual |

### Critical Paths (Must be 100% covered)
- JSON parsing
- Temporal smoothing algorithm
- Precision/Recall calculation
- Serial reconnection logic

---

## 🚦 Test Status Dashboard

### Example Test Run Output
```
===================================================================
TEST SUMMARY
===================================================================
Platform: Windows 11, Python 3.10.11
Test Time: 2026-03-05 14:30:25

─── Unit Tests ───
tests/unit/test_temporal_smoothing.py ...................... PASSED (15/15)
tests/unit/test_json_parser.py ............................. PASSED (12/12)
tests/unit/test_metrics.py ................................. PASSED (20/20)

─── Component Tests ───
tests/component/test_serial_reader.py ...................... PASSED (8/8)
tests/component/test_metrics_analyzer.py ................... PASSED (10/10)
tests/component/test_dashboard.py .......................... PASSED (5/5)

─── Integration Tests ───
tests/integration/test_detection_pipeline.py ............... PASSED (6/6)

─── E2E Tests ───
tests/e2e/test_grove_hardware.py ........................... SKIPPED (requires hardware)

───────────────────────────────────────────────────────────────────
Total: 76 tests
Passed: 76 (100%)
Failed: 0
Skipped: 1 (hardware test)
Coverage: 87%
Time: 12.3s

✅ ALL TESTS PASSED
===================================================================
```

---

## 🔧 Running Tests

### Install Test Dependencies
```bash
pip install pytest pytest-cov pytest-timeout pytest-mock
```

### Run All Tests
```bash
# All tests (except hardware)
pytest tests/ -v

# With coverage report
pytest tests/ --cov=src --cov-report=html

# Specific category
pytest tests/unit/ -v
pytest tests/component/ -v
pytest tests/integration/ -v

# Hardware tests (manual)
pytest tests/e2e/ -m hardware
```

### Generate HTML Report
```bash
pytest tests/ --html=report.html --self-contained-html
```

---

## 🎓 Test-Driven Development (TDD) Workflow

### For Each New Feature

1. **Write test first** (Red phase)
```python
def test_new_feature():
    result = new_feature()
    assert result == expected_value
```

2. **Run test** → Should FAIL (no implementation yet)

3. **Write minimal code** to pass test (Green phase)
```python
def new_feature():
    return expected_value
```

4. **Run test** → Should PASS

5. **Refactor** code while keeping test green

6. **Commit** with passing tests

---

## 📋 Test Checklist for Major Updates

Before merging any major update:

- [ ] All unit tests pass
- [ ] All component tests pass
- [ ] All integration tests pass
- [ ] Code coverage ≥ 85%
- [ ] No new warnings or errors
- [ ] Performance tests pass (if applicable)
- [ ] Manual testing completed (if hardware change)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

---

## 🚀 Quick Start: Adding Your First Test

### Example: Test a New Function

**1. Create the function** (src/local_testing/utils.py):
```python
def calculate_fps(frame_count: int, duration_sec: float) -> float:
    """Calculate frames per second."""
    if duration_sec <= 0:
        raise ValueError("Duration must be positive")
    return frame_count / duration_sec
```

**2. Create the test** (tests/unit/test_utils.py):
```python
import pytest
from src.local_testing.utils import calculate_fps

def test_calculate_fps_normal():
    """Test FPS calculation with normal values."""
    assert calculate_fps(300, 10.0) == 30.0

def test_calculate_fps_zero_duration():
    """Test error handling for zero duration."""
    with pytest.raises(ValueError):
        calculate_fps(100, 0)

def test_calculate_fps_negative_duration():
    """Test error handling for negative duration."""
    with pytest.raises(ValueError):
        calculate_fps(100, -5.0)
```

**3. Run the test**:
```bash
pytest tests/unit/test_utils.py -v
```

**4. Expected output**:
```
tests/unit/test_utils.py::test_calculate_fps_normal PASSED
tests/unit/test_utils.py::test_calculate_fps_zero_duration PASSED
tests/unit/test_utils.py::test_calculate_fps_negative_duration PASSED

3 passed in 0.05s
```

---

**Document Status**: Testing Framework Design
**Next Action**: Review → Get approval → Implement test infrastructure alongside features
