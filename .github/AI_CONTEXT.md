# AI Agent Context Guide

**For AI assistants, code analysis tools, and automated agents**

This file provides a quick orientation for AI agents working on this codebase.

---

## 🎯 Project Summary

**What**: Elderly fall detection system using Grove Vision AI V2 (edge) + Gemini VLM (cloud)
**Status**: Phase 0 - Model Training & Deployment
**Goal**: 90% recall, 70% precision, <500ms latency

---

## 📖 Required Reading Order

**For comprehensive understanding, read in this order:**

1. **[../README.md](../README.md)** (2 min)
   - Project overview and quick start
   - Current status and tech stack

2. **[../docs/README.md](../docs/README.md)** (3 min)
   - Documentation index
   - Navigation guide
   - Document relationships

3. **[../docs/roadmap.md](../docs/roadmap.md)** (5 min)
   - Current phase: Phase 0
   - Phase breakdown and timeline
   - What's completed vs pending

4. **Based on task, read ONE of:**
   - **Training model?** → [../docs/getting_started.md](../docs/getting_started.md)
   - **Building features?** → [../docs/local_testing_plan.md](../docs/local_testing_plan.md)
   - **Writing tests?** → [../docs/testing_framework.md](../docs/testing_framework.md)
   - **Architecture questions?** → [../docs/development_guide.md](../docs/development_guide.md)

**Total reading time**: ~15-20 minutes for full context

---

## 🗺️ Project State

### Current Phase
**Phase 0**: Model Training & Deployment (Days 1-3)
- Train Swift-YOLO on fall detection dataset
- Export to TFLite INT8 + Vela compilation
- Deploy to Grove Vision AI V2 hardware

### Next Phase
**Phase 1**: Local Testing Infrastructure (Days 4-5)
- Build serial bridge (Grove → XIAO → PC)
- Create Python serial reader + unit tests
- Real-time visualization dashboard

### Hardware
- ✅ **Available**: Grove Vision AI V2 + XIAO ESP32-C3
- 🔄 **Model**: Training from scratch (no pretrained model yet)

---

## 📂 Key Files by Purpose

### Documentation
```
docs/
├── README.md              # Documentation index ⭐ START
├── roadmap.md             # Current phase tracker
├── getting_started.md     # Phase 0 how-to guide
├── local_testing_plan.md  # Phase 1-5 implementation
├── testing_framework.md   # Testing strategy
└── development_guide.md   # System architecture
```

### Code (Existing)
```
fall_detection/
├── train_fall_detection.py    # Training pipeline (ready to use)
├── fall_detection_alert.ino    # Arduino firmware (basic version)
└── Fall_Detection_Grove_Vision_AI_V2.ipynb  # Colab notebook
```

### Code (To Be Implemented)
```
src/local_testing/          # Phase 1 - Python testing tools
tests/                      # Phase 1 - Automated tests
src/cloud/                  # Phase 3 - VLM integration
src/backend/                # Phase 4 - FastAPI server
```

---

## 🎯 Common Tasks

### "Understand the architecture"
1. Read [development_guide.md](../docs/development_guide.md#architecture)
2. See hybrid edge-cloud design
3. Note: Currently implementing edge-only (Grove V2), cloud comes later

### "What's the current status?"
1. Check [roadmap.md](../docs/roadmap.md) top section
2. Current: Phase 0 (model training)
3. Hardware: Ready
4. Code: Training pipeline exists, testing infrastructure pending

### "How do I train the model?"
1. Follow [getting_started.md](../docs/getting_started.md)
2. Step-by-step commands provided
3. Estimated time: 2-3 days (mostly GPU training time)

### "How do I add a new feature?"
1. Check [roadmap.md](../docs/roadmap.md) - is it planned?
2. Read relevant phase plan in [local_testing_plan.md](../docs/local_testing_plan.md)
3. Write tests first (see [testing_framework.md](../docs/testing_framework.md))
4. Implement with TDD approach

### "How should I write tests?"
1. Read [testing_framework.md](../docs/testing_framework.md)
2. Use 4-layer pyramid: Unit → Component → Integration → E2E
3. See code examples in the framework doc
4. Minimum 85% coverage for production code

---

## 🚨 Important Constraints

### Must Follow
- ✅ **Test everything**: Every feature needs unit + integration tests
- ✅ **No cloud yet**: Currently edge-only, cloud VLM comes in Phase 3
- ✅ **Privacy first**: Never store video frames, only JSON metadata
- ✅ **Performance targets**: 90% recall, 70% precision, <500ms latency

### Do NOT
- ❌ Skip writing tests for new code
- ❌ Implement cloud features before edge validation passes
- ❌ Store raw video frames (violates privacy policy)
- ❌ Change architecture without updating docs/development_guide.md

---

## 🧭 Decision-Making Guide

### "Should I implement this feature now?"
Check [roadmap.md](../docs/roadmap.md):
- ✅ If it's in current phase → Yes, implement
- ⏳ If it's in future phase → No, wait for phase to start
- ❓ If not in roadmap → Ask for clarification / add to roadmap first

### "Where should this code go?"
- **Model training**: `fall_detection/`
- **Testing tools**: `src/local_testing/`
- **Tests**: `tests/unit/`, `tests/component/`, `tests/integration/`, `tests/e2e/`
- **Cloud VLM**: `src/cloud/` (Phase 3 - not yet)
- **Backend**: `src/backend/` (Phase 4 - not yet)

### "What tests should I write?"
Follow [testing_framework.md](../docs/testing_framework.md):
1. **Unit tests** for functions and algorithms
2. **Component tests** for modules
3. **Integration tests** for multi-component flows
4. **E2E tests** for full hardware pipeline (manual)

---

## 📊 Success Metrics

**Phase 0 Gate** (before Phase 1):
- Model deployed to Grove V2
- Runs at 20-30 FPS
- Basic fall detection works

**Phase 1-2 Gate** (before Phase 3):
- Recall ≥ 90%
- Precision ≥ 70%
- Latency < 500ms
- All tests pass
- 1-hour uptime without crash

---

## 🔄 Context Refresh

**If you lose context or join conversation mid-project:**

```bash
# Quick refresh (30 seconds)
cat README.md                    # Project overview
cat docs/roadmap.md | head -50   # Current status

# Full refresh (5 minutes)
cat docs/README.md               # Doc index
cat docs/roadmap.md              # Full roadmap
cat docs/local_testing_plan.md | head -100  # Current phase details
```

---

## 🤖 For Code Generation

**Before generating code:**
1. Check if tests exist - write tests first (TDD)
2. Check which phase we're in (see roadmap.md)
3. Follow existing code style in similar files
4. Add docstrings and type hints
5. Update relevant plan document if implementing a checklist item

**After generating code:**
1. Write/update unit tests
2. Run tests: `pytest tests/unit/`
3. Check coverage: `pytest --cov=src`
4. Update roadmap checkboxes if completing a task

---

## 📝 Documentation Updates

**When to update docs:**
- ✏️ **Completing a phase**: Update roadmap.md checkboxes
- ✏️ **Changing architecture**: Update development_guide.md
- ✏️ **Adding new features**: Update relevant plan document
- ✏️ **Discovering bugs/solutions**: Update getting_started.md troubleshooting
- ✏️ **New test patterns**: Update testing_framework.md

---

## 🎓 Learning Resources

**To understand the hardware:**
- Grove Vision AI V2 Wiki: https://wiki.seeedstudio.com/grove_vision_ai_v2/
- SSCMA Framework: https://github.com/Seeed-Studio/ModelAssistant

**To understand the model:**
- YOLOv8 Docs: https://docs.ultralytics.com/
- Vela Compiler: https://github.com/ARM-software/ethos-u-vela

**To understand the architecture:**
- Read [docs/development_guide.md](../docs/development_guide.md)

---

## ❓ FAQ for AI Agents

**Q: What's the difference between the existing code and the plan?**
A: Existing code (fall_detection/) is edge-only training. Plan adds testing infrastructure, cloud VLM, backend, mobile app.

**Q: Can I start implementing Phase 3 (cloud) now?**
A: No. Must complete Phase 0-2 and validate edge performance first (90% recall gate).

**Q: Where do I put test files?**
A: `tests/unit/`, `tests/component/`, `tests/integration/`, or `tests/e2e/` based on test type.

**Q: Should I create a new doc file?**
A: Only if it serves a distinct purpose not covered by existing docs. Update docs/README.md if you do.

**Q: How do I know what to work on next?**
A: Check roadmap.md → find current phase → look for unchecked items.

---

**Last Updated**: 2026-03-05
**For Questions**: Read docs/README.md or ask for clarification
