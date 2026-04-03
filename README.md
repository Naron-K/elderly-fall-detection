# AI-Powered Elderly Fall Detection System

> Real-time fall detection using hybrid edge-cloud architecture: Grove Vision AI V2 (edge) + Gemini VLM (cloud verification)

**Status**: 🔄 Phase 0 - Model Training & Deployment
**Timeline**: ASAP (2-3 weeks for local testing validation)

---

## 🎯 Project Overview

An intelligent fall detection system designed for elderly care that combines:
- **Edge AI**: Ultra-low-power Grove Vision AI V2 for instant fall detection (0.35W, 20-30 FPS)
- **Cloud Intelligence**: Gemini 2.0 Flash VLM for contextual verification and anomaly detection
- **Mobile Alerts**: React Native app with emergency escalation (notification → auto-call)

### Key Features
- ✅ **Low Latency**: <500ms from fall to alert
- ✅ **High Accuracy**: Target 90%+ recall, 70%+ precision
- ✅ **Privacy-First**: Video frames never stored, only analyzed
- ✅ **Context-Aware**: Learns user habits to reduce false alarms
- ✅ **Emergency Escalation**: Auto-calls contacts if no response in 30s

---

## 📁 Project Structure

```
elderly-fall-detection/
├── docs/                          # 📚 All documentation
│   ├── README.md                  # Documentation index (START HERE)
│   ├── roadmap.md                 # Project phases and timeline
│   ├── development_guide.md       # System architecture
│   ├── getting_started.md         # Phase 0 setup guide
│   ├── local_testing_plan.md      # Phase 1-5 implementation plan
│   └── testing_framework.md       # Testing strategy
│
├── fall_detection/                # Grove Vision AI V2 training pipeline
│   ├── train_fall_detection.py    # Model training script
│   ├── Fall_Detection_Grove_Vision_AI_V2.ipynb  # Colab notebook
│   ├── fall_detection_alert.ino   # Arduino alert system (XIAO)
│   ├── requirements.txt
│   └── README.md
│
├── src/                           # Source code (to be implemented)
│   ├── local_testing/             # Phase 1: Testing infrastructure
│   ├── edge/                      # Phase 2: Edge processing (future)
│   ├── cloud/                     # Phase 3: Cloud VLM integration (future)
│   └── backend/                   # Phase 4: FastAPI server (future)
│
├── tests/                         # Automated tests
│   ├── unit/
│   ├── component/
│   ├── integration/
│   └── e2e/
│
├── config/                        # Configuration files (future)
└── data/                          # Test sessions and logs (future)
```

---

## 🚀 Quick Start

### For First-Time Setup

1. **Read the Documentation**
   ```bash
   # Navigate to docs folder and read the index
   cat docs/README.md
   ```

2. **Start with Phase 0** (Model Training)
   ```bash
   # Follow the step-by-step guide
   # See: docs/getting_started.md
   cd fall_detection
   python train_fall_detection.py prepare --api-key YOUR_ROBOFLOW_KEY
   python train_fall_detection.py train
   ```

3. **Check the Roadmap**
   - See [docs/roadmap.md](docs/roadmap.md) for current phase and next steps

### For AI Agents / Contributors

**To understand the project**:
1. Read [docs/README.md](docs/README.md) (documentation index)
2. Read [docs/roadmap.md](docs/roadmap.md) (current status + phases)
3. Consult specific docs based on your task

**Current Phase**: Phase 0 - Model Training & Deployment
**Next Phase**: Phase 1 - Local Testing Infrastructure

---

## 📊 System Architecture

### Current Implementation (Phase 0-2)

```
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  Grove Vision    │  I2C    │   XIAO ESP32     │  USB    │   Windows PC     │
│  AI V2           │────────>│   (Bridge)       │────────>│                  │
│                  │         │                  │ Serial  │  • Serial reader │
│  • Runs model    │         │  • Reads boxes   │         │  • Visualizer    │
│  • Detects falls │         │  • Formats JSON  │         │  • Metrics logger│
│  • 20-30 FPS     │         │  • Sends via USB │         │  • Test harness  │
└──────────────────┘         └──────────────────┘         └──────────────────┘
```

### Future Architecture (Phase 3+)

```
┌──────────────────────────────────────────────────────────────────┐
│                           Mobile App                             │
│                  (React Native - iOS/Android)                    │
│                • Alert notifications                             │
│                • "I'm OK" button                                 │
│                • Emergency auto-call                             │
└──────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Push Notifications
                              │
┌──────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│                 • Alert escalation logic                         │
│                 • User profiles & habits                         │
│                 • Activity logging (SQLite)                      │
└──────────────────────────────────────────────────────────────────┘
                              ▲
                              │ API Calls
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│    Edge Layer (Local)     │   │   Cloud Layer (VLM)       │
│                           │   │                           │
│  Grove Vision AI V2       │   │  Gemini 2.0 Flash         │
│  • Swift-YOLO detection   │──>│  • Video verification     │
│  • 20-30 FPS              │   │  • Context understanding  │
│  • Temporal smoothing     │   │  • Anomaly detection      │
│  • Trigger on suspicion   │   │  • Confirm/dismiss alert  │
└───────────────────────────┘   └───────────────────────────┘
```

See [docs/development_guide.md](docs/development_guide.md) for full architectural details.

---

## 📋 Current Status

**Phase 0: Model Training & Deployment**
- [x] Hardware acquired (Grove Vision AI V2 + XIAO)
- [x] Training pipeline available
- [x] Documentation complete
- [ ] Dataset downloaded
- [ ] Model trained
- [ ] Model deployed to hardware
- [ ] Basic fall detection verified

**Next**: Phase 1 - Build testing infrastructure (serial bridge, dashboard, metrics)

See [docs/roadmap.md](docs/roadmap.md) for detailed progress.

---

## 🧪 Testing

We use a **4-layer testing pyramid**:

1. **Unit Tests** (50%) - Fast, focused function tests
2. **Component Tests** (30%) - Individual module tests
3. **Integration Tests** (15%) - Multi-component chains
4. **E2E Tests** (5%) - Full system with real hardware

**Run Tests**:
```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific layer
pytest tests/unit/ -v
pytest tests/integration/ -v
```

See [docs/testing_framework.md](docs/testing_framework.md) for testing strategy and examples.

---

## 📚 Documentation

All documentation is in the [`docs/`](docs/) folder:

| Document | Purpose |
|----------|---------|
| **[docs/README.md](docs/README.md)** | Documentation index and navigation |
| **[docs/roadmap.md](docs/roadmap.md)** | Project phases and timeline |
| **[docs/development_guide.md](docs/development_guide.md)** | System architecture |
| **[docs/getting_started.md](docs/getting_started.md)** | Phase 0 setup guide |
| **[docs/local_testing_plan.md](docs/local_testing_plan.md)** | Phase 1-5 plan |
| **[docs/testing_framework.md](docs/testing_framework.md)** | Testing strategy |

**New to the project?** Start with [docs/README.md](docs/README.md)

---

## 🎯 Success Criteria

Before moving to cloud integration (Phase 3), we must achieve:

- ✅ **Recall ≥ 90%**: Catches 9/10 actual falls
- ✅ **Precision ≥ 70%**: 7/10 alerts are real falls
- ✅ **Latency < 500ms**: From fall to alert trigger
- ✅ **FPS ≥ 20**: Maintains real-time performance
- ✅ **Uptime**: Runs continuously for 1 hour without crash

---

## 🛠️ Tech Stack

### Edge (Current)
- **Hardware**: Grove Vision AI V2 (WiseEye2 HX6538, Ethos-U55)
- **Model**: Swift-YOLO Tiny (192×192, INT8 quantized)
- **Framework**: Ultralytics YOLOv8, SSCMA, Vela compiler
- **Microcontroller**: XIAO ESP32-C3 (serial bridge)

### Testing Infrastructure (Phase 1)
- **Language**: Python 3.10+
- **Testing**: pytest, pytest-cov, pytest-mock
- **Visualization**: matplotlib, OpenCV
- **Serial**: pyserial
- **Data**: pandas, numpy

### Cloud (Phase 3 - Future)
- **VLM**: Google Gemini 2.0 Flash
- **Backend**: FastAPI, SQLite (dev) → PostgreSQL (prod)
- **Storage**: AWS S3 (emergency video, 30-day expiration)

### Mobile (Phase 5 - Future)
- **Framework**: React Native + Expo
- **Notifications**: Firebase Cloud Messaging (FCM)
- **Platforms**: iOS, Android

---

## 🤝 Contributing

1. **Check the roadmap** - See [docs/roadmap.md](docs/roadmap.md) for current phase
2. **Read the plan** - See phase-specific docs for task breakdown
3. **Write tests** - Follow [docs/testing_framework.md](docs/testing_framework.md)
4. **Update docs** - Keep documentation in sync with code

---

## 📞 Getting Help

- **Documentation Issues**: Check [docs/README.md](docs/README.md) for navigation
- **Setup Problems**: See [docs/getting_started.md](docs/getting_started.md) troubleshooting
- **Architectural Questions**: See [docs/development_guide.md](docs/development_guide.md)
- **Testing Questions**: See [docs/testing_framework.md](docs/testing_framework.md)

---

## 📄 License

[To be determined]

---

## 🙏 Acknowledgments

- **Seeed Studio** - Grove Vision AI V2 hardware and SSCMA framework
- **Ultralytics** - YOLOv8 framework
- **Google** - Gemini VLM API
- **Roboflow** - Fall detection dataset

---

**Project Status**: Phase 0 - Model Training
**Last Updated**: 2026-03-05
**Maintainer**: [Your Name/Team]
