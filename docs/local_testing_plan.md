# Local Testing Plan: Grove Vision AI V2 + PC Validation (No Cloud)

**Goal**: Test and validate Grove Vision AI V2 fall detection performance using only local PC processing, before adding cloud/backend infrastructure.

**Strategy**: Phased implementation with automated testing at each stage.

---

## 📌 Project Status

**Hardware**: ✅ Grove Vision AI V2 + XIAO setup available
**Model**: 🔄 Will train from scratch using existing training pipeline
**Timeline**: 🚀 ASAP - Accelerated Phase 1 completion
**Current Phase**: Phase 0 - Planning Complete, Ready to Begin Implementation

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: Local Testing Setup                 │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  Grove Vision    │  I2C    │   XIAO ESP32     │  USB    │   Windows PC     │
│  AI V2           │────────>│   (Bridge)       │────────>│                  │
│                  │         │                  │ Serial  │  • Serial reader │
│  • Runs model    │         │  • Reads boxes   │         │  • Visualizer    │
│  • Detects falls │         │  • Formats JSON  │         │  • Metrics logger│
│  • 20-30 FPS     │         │  • Sends via USB │         │  • Test harness  │
└──────────────────┘         └──────────────────┘         └──────────────────┘
```

---

## 📦 Components to Build

### 1. Arduino Firmware (XIAO + Grove V2)
**File**: `fall_detection/grove_serial_bridge.ino`

**Purpose**: Enhanced version of the existing `.ino` that outputs structured JSON data over serial.

**Output Format**:
```json
{
  "timestamp": 1234567890,
  "fps": 25.3,
  "detections": [
    {
      "class": "fall",
      "class_id": 0,
      "confidence": 0.87,
      "bbox": {"x": 120, "y": 80, "w": 100, "h": 150}
    }
  ],
  "fall_event": true
}
```

**Test Criteria**:
- ✅ Outputs valid JSON every frame
- ✅ Maintains stable FPS (20-30 FPS)
- ✅ Temporal smoothing works (5-frame buffer)

---

### 2. Python Serial Reader
**File**: `src/local_testing/grove_serial_reader.py`

**Purpose**: Read JSON data from XIAO via serial port.

**Features**:
- Auto-detect COM port (Windows)
- Parse JSON detections
- Handle malformed data gracefully
- Buffer incoming frames
- Calculate real FPS

**Test Criteria**:
- ✅ Successfully connects to XIAO
- ✅ Parses 100% of valid JSON messages
- ✅ Handles disconnection/reconnection
- ✅ No data loss at 30 FPS

---

### 3. Real-Time Visualization Dashboard
**File**: `src/local_testing/live_dashboard.py`

**Purpose**: Display fall detections in real-time using matplotlib/OpenCV.

**Features**:
- Live detection count graph
- Fall event timeline
- Confidence distribution histogram
- FPS counter
- Alert indicators

**Test Criteria**:
- ✅ Updates at 10+ FPS (UI refresh)
- ✅ Displays last 60 seconds of data
- ✅ Visual alert when fall detected

---

### 4. Metrics Logger & Analyzer
**File**: `src/local_testing/metrics_analyzer.py`

**Purpose**: Log all detections to CSV/JSON and calculate performance metrics.

**Logged Data**:
- Timestamp
- Detections (class, confidence, bbox)
- Fall events (with temporal smoothing)
- FPS
- Inference time (if available from Grove)

**Calculated Metrics**:
- **Detection Rate**: % of frames with detections
- **Fall Event Count**: Number of fall events detected
- **False Positive Rate**: Falls detected during non-fall periods (requires ground truth)
- **Precision/Recall**: Against manually annotated ground truth

**Test Criteria**:
- ✅ Logs 1000+ detections without data loss
- ✅ Generates CSV report
- ✅ Calculates metrics from ground truth JSON

---

### 5. Ground Truth Annotation Tool
**File**: `src/local_testing/annotate_ground_truth.py`

**Purpose**: Simple GUI to mark when falls actually occur in test videos.

**Features**:
- Play test video
- Mark fall start/end times
- Export to JSON format
- Load existing annotations

**Output Format**:
```json
{
  "test_session_1": {
    "description": "Sitting down quickly vs actual fall",
    "fall_events": [
      {"start_sec": 5.2, "end_sec": 7.8, "type": "forward_fall"},
      {"start_sec": 15.0, "end_sec": 17.5, "type": "backward_fall"}
    ],
    "non_fall_events": [
      {"start_sec": 10.0, "end_sec": 12.0, "type": "sitting_down"}
    ]
  }
}
```

**Test Criteria**:
- ✅ Can load and playback test session
- ✅ Saves annotations to JSON
- ✅ Loads existing annotations for editing

---

### 6. Automated Test Harness
**File**: `tests/test_grove_local.py`

**Purpose**: Automated tests that validate the entire pipeline.

**Test Scenarios**:

#### Test 1: Serial Communication
- Connect to XIAO
- Verify JSON parsing
- Measure data throughput
- Check for dropped frames

#### Test 2: Detection Logic
- Feed known test sequences
- Verify temporal smoothing (5 frames at 60% threshold)
- Confirm fall events triggered correctly

#### Test 3: Performance Metrics
- Run against ground truth dataset
- Calculate precision, recall, F1
- Verify target: Recall ≥ 90%, Precision ≥ 70%

#### Test 4: Stress Test
- Run for 10 minutes continuous
- Verify no memory leaks
- Confirm stable FPS
- Check log file integrity

**Test Criteria**:
- ✅ All unit tests pass
- ✅ Integration test completes without errors
- ✅ Performance meets targets

---

## 🧪 Testing Framework Architecture

### Testing Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: End-to-End Testing                                │
│  - Full pipeline test with real Grove hardware              │
│  - Compare against ground truth                             │
│  - Generate performance report                              │
└─────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Integration Testing                               │
│  - Serial → Parser → Analyzer chain                         │
│  - Mock hardware with simulated data                        │
└─────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Component Testing                                 │
│  - Test each Python module independently                    │
│  - Test Arduino JSON formatting                             │
└─────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Unit Testing                                      │
│  - Test individual functions                                │
│  - Test data parsing logic                                  │
│  - Test temporal smoothing algorithm                        │
└─────────────────────────────────────────────────────────────┘
```

### Test Data Strategy

**Simulated Test Data** (for early testing without hardware):
```python
# tests/fixtures/mock_detections.json
{
  "scenario_1_actual_fall": [
    {"frame": 0, "class": "standing", "conf": 0.92},
    {"frame": 1, "class": "fall", "conf": 0.85},
    {"frame": 2, "class": "fall", "conf": 0.91},
    {"frame": 3, "class": "fall", "conf": 0.88},
    {"frame": 4, "class": "fall", "conf": 0.90},
    {"frame": 5, "class": "fall", "conf": 0.87}
  ],
  "scenario_2_false_positive_sitting": [
    {"frame": 0, "class": "standing", "conf": 0.95},
    {"frame": 1, "class": "sitting", "conf": 0.89},
    {"frame": 2, "class": "sitting", "conf": 0.91},
    {"frame": 3, "class": "sitting", "conf": 0.93}
  ]
}
```

**Real Hardware Test Protocol**:
1. **Controlled Falls** (safely performed):
   - Forward fall onto mat
   - Backward fall
   - Side fall
   - Fall from sitting position

2. **Non-Fall Activities** (should NOT trigger):
   - Sitting down quickly
   - Bending to pick up object
   - Lying down on bed/couch
   - Exercise movements (squats, lunges)

3. **Edge Cases**:
   - Partial occlusion
   - Poor lighting
   - Fast movements
   - Multiple people in frame

---

## 📝 Implementation Phases

**Timeline**: ASAP - Accelerated completion target (2-3 weeks total)

---

### Phase 0: Model Training & Deployment (Days 1-3)
**Goal**: Train and deploy fall detection model to Grove Vision AI V2

**Prerequisites**: ✅ Grove Vision AI V2 + XIAO hardware ready

**Tasks**:
- [ ] Download fall detection dataset from Roboflow (using existing `train_fall_detection.py`)
- [ ] Train Swift-YOLO model (300 epochs, ~8-12 hours on GPU)
- [ ] Export to TFLite INT8 format
- [ ] Compile with Vela for Ethos-U55
- [ ] Deploy `*_int8_vela.tflite` to Grove Vision AI V2 via SenseCraft Web Toolkit
- [ ] Test: Model runs on hardware at 20-30 FPS
- [ ] Test: Can detect basic fall motions

**Deliverable**: Working fall detection model deployed on Grove V2 hardware

**Estimated Time**: 2-3 days (most time is training)

---

### Phase 1: Foundation (Days 4-5)
**Goal**: Get basic serial communication working

- [ ] Update Arduino firmware to output JSON (enhance existing `fall_detection_alert.ino`)
- [ ] Create Python serial reader with unit tests
- [ ] Test: Can receive and parse 100 consecutive frames
- [ ] Test: No data loss at 30 FPS
- [ ] Test: All unit tests pass

**Deliverable**: Working serial bridge with automated tests

**Estimated Time**: 1-2 days

---

### Phase 2: Visualization (Days 6-8)
**Goal**: See what the Grove is detecting in real-time

- [ ] Build live dashboard (matplotlib/OpenCV)
- [ ] Add detection visualization (bboxes, labels)
- [ ] Add FPS counter and metrics display
- [ ] Test: Dashboard updates at 10+ FPS
- [ ] Test: Displays fall alerts correctly
- [ ] Test: Component tests pass

**Deliverable**: Real-time monitoring dashboard

**Estimated Time**: 2-3 days

---

### Phase 3: Metrics & Logging (Days 9-11)
**Goal**: Quantify performance

- [ ] Implement metrics logger with CSV/JSON export
- [ ] Create ground truth annotation tool
- [ ] Build automated metrics calculator (precision/recall)
- [ ] Test: Log 10-minute session without errors
- [ ] Test: Calculate metrics from ground truth
- [ ] Test: Integration tests pass

**Deliverable**: Performance measurement tools

**Estimated Time**: 2-3 days

---

### Phase 4: Validation (Days 12-16)
**Goal**: Verify model performance meets targets

- [ ] Perform 20+ controlled fall tests (safely on mat)
- [ ] Record 20+ non-fall activities
- [ ] Annotate ground truth for all test sessions
- [ ] Run automated test harness
- [ ] Analyze results and generate report
- [ ] Test: Recall ≥ 90%, Precision ≥ 70%

**Deliverable**: Validated fall detection model with performance report

**Estimated Time**: 4-5 days (includes testing and annotation)

---

### Phase 5: Optimization (Days 17-21)
**Goal**: Tune for maximum accuracy

- [ ] Adjust confidence thresholds
- [ ] Tune temporal smoothing parameters
- [ ] Re-train model if needed
- [ ] Test: Improved metrics
- [ ] Test: End-to-end latency < 500ms

**Deliverable**: Production-ready edge inference system

---

## 🎯 Success Criteria

Before moving to Phase 2 (Cloud + Backend), we must achieve:

### Performance Targets
- ✅ **Recall ≥ 90%**: Catches 9/10 actual falls
- ✅ **Precision ≥ 70%**: 7/10 alerts are real falls (acceptable false positive rate)
- ✅ **Latency < 500ms**: From fall to alert trigger
- ✅ **FPS ≥ 20**: Maintains real-time performance

### Reliability Targets
- ✅ **Uptime**: Runs continuously for 1 hour without crash
- ✅ **Data Integrity**: Zero dropped frames at 30 FPS
- ✅ **Recovery**: Auto-reconnects after serial disconnect

### Testing Targets
- ✅ **Unit Test Coverage**: 100% of critical functions
- ✅ **Integration Tests**: All components pass
- ✅ **Real Hardware Tests**: 40+ test scenarios (20 falls + 20 non-falls)

---

## 📁 Project Structure (After Implementation)

```
elderly-fall-detection/
├── fall_detection/                      # Existing Grove training code
│   ├── grove_serial_bridge.ino          # NEW: Enhanced Arduino firmware
│   ├── train_fall_detection.py
│   ├── Fall_Detection_Grove_Vision_AI_V2.ipynb
│   └── README.md
│
├── src/
│   └── local_testing/                   # NEW: Local testing infrastructure
│       ├── __init__.py
│       ├── grove_serial_reader.py       # Serial communication
│       ├── live_dashboard.py            # Real-time visualization
│       ├── metrics_analyzer.py          # Performance metrics
│       ├── annotate_ground_truth.py     # Ground truth annotation tool
│       └── config.py                    # Configuration (COM port, thresholds)
│
├── tests/                               # NEW: Automated testing
│   ├── __init__.py
│   ├── test_serial_reader.py            # Unit tests
│   ├── test_metrics.py
│   ├── test_temporal_smoothing.py
│   ├── test_grove_local.py              # Integration tests
│   └── fixtures/
│       ├── mock_detections.json
│       └── ground_truth_sample.json
│
├── data/                                # NEW: Test data and logs
│   ├── test_sessions/                   # Ground truth annotations
│   ├── logs/                            # Detection logs (CSV/JSON)
│   └── reports/                         # Performance reports
│
├── docs/
│   ├── development_guide.md
│   ├── roadmap.md
│   └── local_testing_plan.md            # THIS FILE
│
└── requirements.txt                     # Update with new dependencies
```

---

## 🔧 Required Dependencies

Add to `requirements.txt`:

```txt
# Existing dependencies
ultralytics>=8.3.0
roboflow>=1.1.0
# ... (keep existing)

# NEW: Local testing dependencies
pyserial>=3.5          # Serial communication
matplotlib>=3.7.0      # Live dashboard
opencv-python>=4.8.0   # Video playback for annotation
pandas>=2.0.0          # Metrics analysis
pytest>=7.4.0          # Testing framework
pytest-timeout>=2.1.0  # Test timeouts
```

---

## 🚀 Quick Start Guide (After Implementation)

### 1. Setup Hardware
```bash
# Connect: Grove Vision AI V2 → XIAO → PC (USB)
# Upload grove_serial_bridge.ino to XIAO
# Deploy fall detection model to Grove V2
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Live Dashboard
```bash
cd src/local_testing
python live_dashboard.py --port COM3
```

### 4. Run Test Suite
```bash
pytest tests/ -v
```

### 5. Log Test Session
```bash
python metrics_analyzer.py --port COM3 --duration 300 --output test_session_1.csv
```

### 6. Annotate Ground Truth
```bash
python annotate_ground_truth.py --session test_session_1
```

### 7. Generate Performance Report
```bash
python metrics_analyzer.py --analyze --log test_session_1.csv --ground-truth test_session_1_gt.json
```

---

## 📊 Expected Test Results

### Example Performance Report
```
===================================================================
GROVE VISION AI V2 - FALL DETECTION PERFORMANCE REPORT
===================================================================
Test Date: 2026-03-05
Model: fall_detection_swift_yolo_v1_int8_vela.tflite
Duration: 15 minutes
Total Frames: 27,000

─── Detection Statistics ───
Frames with detections:     26,543 (98.3%)
Average FPS:                 30.1
Inference latency (avg):     25ms

─── Fall Event Statistics ───
Actual falls (ground truth): 20
Detected falls:              19
Missed falls:                1
False positives:             4

─── Performance Metrics ───
Precision:                   82.6%  (19 / 23)
Recall:                      95.0%  (19 / 20)
F1 Score:                    88.4%

─── Latency ───
Fall to alert (avg):         420ms
Fall to alert (max):         680ms

─── Verdict ───
✅ PASS - Exceeds minimum requirements
   (Recall: 95.0% ≥ 90%, Precision: 82.6% ≥ 70%)

Ready for Phase 2: Cloud Integration
===================================================================
```

---

## 🎯 Next Steps After Local Validation

Once local testing passes all criteria:

1. ✅ **Edge layer is production-ready**
2. 🔄 **Begin Phase 2**: Add cloud VLM verification layer (Gemini 2.0 Flash)
3. 🔄 **Begin Phase 3**: Build FastAPI backend
4. 🔄 **Begin Phase 4**: Develop mobile alert app

This local testing phase de-risks the entire project by validating the most critical component (fall detection accuracy) before investing in cloud infrastructure.

---

**Document Status**: Planning Document
**Next Action**: Review plan → Get approval → Begin Phase 1 implementation
