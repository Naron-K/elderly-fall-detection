# Roadmap: AI-Powered Elderly Fall Detection (MVP)

**Architecture**: Hybrid Edge-Cloud (Option C)
- **Edge**: Grove Vision AI V2 (low-power fall detection)
- **Cloud**: Gemini VLM verification (added later)
- **Backend**: FastAPI + mobile app (added later)

**Current Status**: 📍 Phase 0 - Model Training & Deployment
**Timeline**: ASAP completion (2-3 weeks for local testing, then cloud integration)

---

## Phase 0: Grove Vision AI V2 Setup ⚡ CURRENT PHASE
**Goal**: Train and deploy fall detection model to Grove hardware

**Status**: 🔄 In Progress

- [x] Hardware acquired (Grove Vision AI V2 + XIAO)
- [x] Existing training pipeline available (`fall_detection/train_fall_detection.py`)
- [ ] Download fall detection dataset from Roboflow
- [ ] Train Swift-YOLO model (192×192, INT8 quantized)
- [ ] Export to TFLite and compile with Vela
- [ ] Deploy model to Grove Vision AI V2
- [ ] Verify basic fall detection works (20-30 FPS)

**Estimated Time**: 2-3 days
**See**: [getting_started.md](getting_started.md) for step-by-step guide

---

## Phase 1: Local Testing Infrastructure
**Goal**: Build PC-based testing tools to validate Grove performance

**Status**: ⏳ Not Started (Starts after Phase 0)

### 1a. Project Setup & Infrastructure
- [x] Create project directory `elderly-fall-detection`
- [x] Create folder structure (`/src`, `/config`, `/docs`)
- [x] Planning documents created
- [ ] Initialize Python venv and install testing dependencies
- [ ] Create test framework structure (`/tests`)

### 1b. Serial Bridge & Communication
- [ ] Enhance Arduino firmware to output JSON (`grove_serial_bridge.ino`)
- [ ] Implement Python serial reader (`src/local_testing/grove_serial_reader.py`)
- [ ] Write unit tests for serial communication
- [ ] Test: 100 consecutive frames parsed successfully
- [ ] Test: No data loss at 30 FPS

### 1c. Real-Time Visualization
- [ ] Build live dashboard (`src/local_testing/live_dashboard.py`)
- [ ] Display detection boxes and labels in real-time
- [ ] Add FPS counter and metrics display
- [ ] Write component tests for dashboard
- [ ] Test: Dashboard updates at 10+ FPS

### 1d. Metrics & Logging
- [ ] Implement metrics analyzer (`src/local_testing/metrics_analyzer.py`)
- [ ] Create CSV/JSON export for detection logs
- [ ] Build ground truth annotation tool (`src/local_testing/annotate_ground_truth.py`)
- [ ] Write integration tests for full pipeline
- [ ] Test: Log 10-minute session without errors

**Estimated Time**: 1-2 weeks
**See**: [local_testing_plan.md](local_testing_plan.md) for detailed breakdown

---

## Phase 2: Model Validation & Optimization
**Goal**: Achieve target performance (Recall ≥90%, Precision ≥70%)

- [ ] Perform 20+ controlled fall tests (safely on mat)
- [ ] Record 20+ non-fall activities (sitting, bending, etc.)
- [ ] Annotate ground truth for all test sessions
- [ ] Run automated test harness
- [ ] Calculate precision, recall, F1 score
- [ ] Tune confidence thresholds and temporal smoothing
- [ ] Re-train model if needed
- [ ] Test: Performance meets targets
- [ ] Test: End-to-end latency < 500ms
- [ ] Generate performance report

**Estimated Time**: 1 week
**Deliverable**: ✅ Validated edge detection system ready for production

**Gate**: Must pass all tests before proceeding to cloud integration

---

## Phase 3: Cloud VLM Integration (After Edge Validation)
**Goal**: Add Gemini 2.0 Flash for intelligent fall verification

- [ ] Implement `FrameBuffer` — sliding window of recent frames (`src/frame_buffer.py`)
- [ ] Implement `ActivityLogger` — persist activity states to SQLite (`src/activity_logger.py`)
- [ ] Develop `VLMClient` — Gemini 2.0 Flash integration with retry logic (`src/cloud_llm.py`)
- [ ] Create API key management (`config/settings.py`)
- [ ] Construct VLM prompt (video + telemetry + activity context)
- [ ] Implement hybrid detection logic:
  - Edge triggers potential fall → Send to cloud
  - VLM confirms/dismisses → Return verdict
- [ ] Write integration tests for cloud pipeline
- [ ] Test: VLM reduces false positives by 50%+

**Estimated Time**: 1-2 weeks

---

## Phase 4: Backend & API
**Goal**: Build FastAPI server for alert management

- [ ] Build FastAPI server with endpoints:
  - `GET /status` — System health
  - `POST /webhook/alert` — Receive fall alerts
  - `GET /activity` — Recent activity log
- [ ] Implement SQLite database schema
- [ ] Create user profile management
- [ ] Implement Alert Escalation logic:
  1. Send push notification to mobile app
  2. Wait 30s for acknowledgment
  3. Auto-call emergency contact if no response
- [ ] Write API tests (unit + integration)
- [ ] Deploy locally for testing

**Estimated Time**: 1-2 weeks

---

## Phase 5: Mobile Alert App
**Goal**: React Native app for iOS/Android notifications

- [ ] Initialize React Native + Expo project
- [ ] Build Dashboard screen (live status)
- [ ] Build Alert screen (full-screen alert + "I'm OK" button)
- [ ] Build Profile Setup screen (emergency contacts, habits)
- [ ] Integrate Firebase Cloud Messaging (FCM)
- [ ] Implement emergency call escalation (`expo-linking`)
- [ ] Test end-to-end alert flow

**Estimated Time**: 2-3 weeks

---

## Phase 6: Production Deployment
**Goal**: Deploy to production environment

- [ ] Dockerize all components
- [ ] Deploy FastAPI backend to AWS EC2 or Google Cloud Run
- [ ] Set up PostgreSQL/InfluxDB on VPS
- [ ] Configure AWS S3 for emergency video storage (30-day expiration)
- [ ] Publish mobile app to App Store & Google Play
- [ ] Create user documentation and setup guide
- [ ] Perform end-to-end production test

**Estimated Time**: 2-3 weeks

---

## Future Phases (Post-MVP)

### Phase 7: Cloud Data Migration
- [ ] Deploy AWS EC2 (VPS) instance and configure Docker
- [ ] Migrate Activity Logs from SQLite → self-hosted InfluxDB/TimescaleDB on VPS
- [ ] Migrate User Profiles → self-hosted PostgreSQL on VPS
- [ ] Set up AWS S3 bucket for emergency video frames (with 30-day auto-delete policy)

### Phase 8: Mobile Alert App (iOS & Android)
- [ ] Initialize React Native + Expo project
- [ ] Build Dashboard screen (live status of monitored person)
- [ ] Build Alert screen (full-screen alert + "I'm OK" button + 30s countdown)
- [ ] Build Profile Setup screen (age, habits, emergency contacts)
- [ ] Integrate Firebase Cloud Messaging (FCM) for push notifications
- [ ] Implement emergency call escalation (auto-dial contact → hotline)

### Phase 9: Production Deployment
- [ ] Dockerize Edge + Cloud components
- [ ] Deploy FastAPI backend to Google Cloud Run
- [ ] Publish mobile app to App Store & Google Play
