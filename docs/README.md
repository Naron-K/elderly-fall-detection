# Documentation Index

**Project**: AI-Powered Elderly Fall Detection System
**Architecture**: Hybrid Edge-Cloud (Grove Vision AI V2 + Gemini VLM)
**Status**: Phase 0 - Planning Complete

---

## 📚 Documentation Structure

### For New Contributors / AI Agents

**Read documents in this order:**

1. **[roadmap.md](roadmap.md)** ⭐ START HERE
   - High-level project phases and current status
   - What's completed and what's next
   - Quick overview of the entire project

2. **[development_guide.md](development_guide.md)** 📖 ARCHITECTURE
   - Original system architecture (hybrid edge-cloud)
   - Technical specifications and design decisions
   - Component descriptions and data flow

3. **[getting_started.md](getting_started.md)** 🚀 PHASE 0 GUIDE
   - Step-by-step model training instructions
   - Commands to run for Phase 0
   - Troubleshooting and expected outputs

4. **[local_testing_plan.md](local_testing_plan.md)** 🧪 PHASE 1-5 PLAN
   - Detailed testing infrastructure plan
   - Phase 1-5 implementation breakdown
   - Success criteria and deliverables

5. **[testing_framework.md](testing_framework.md)** 🔬 TESTING STRATEGY
   - 4-layer testing pyramid design
   - Code examples for each test type
   - TDD workflow and best practices

6. **[SESSION_NOTES.md](SESSION_NOTES.md)** 📝 SESSION HISTORY
   - Quick notes from work sessions
   - What was done and what's next
   - Continue from where you left off

7. **[../src/local_testing/README.md](../src/local_testing/README.md)** 💻 LAPTOP TESTING
   - Test models on laptop camera (no hardware needed)
   - Real-time detection and model comparison
   - Quick start for training and testing

---

## 🗺️ Quick Navigation

### I want to...

| Goal | Read This |
|------|-----------|
| **Understand the project** | [roadmap.md](roadmap.md) |
| **Know the architecture** | [development_guide.md](development_guide.md) |
| **Start training a model** | [getting_started.md](getting_started.md) |
| **Build testing infrastructure** | [local_testing_plan.md](local_testing_plan.md) |
| **Write tests for new code** | [testing_framework.md](testing_framework.md) |
| **Test on laptop camera** | [../src/local_testing/README.md](../src/local_testing/README.md) |
| **Check current status** | [roadmap.md](roadmap.md) or [SESSION_NOTES.md](SESSION_NOTES.md) |
| **See what's next** | [SESSION_NOTES.md](SESSION_NOTES.md) |

---

## 📋 Document Summaries

### [roadmap.md](roadmap.md)
**Purpose**: Master timeline and phase tracker
**Contains**:
- Current phase and status
- Phase 0: Model Training & Deployment
- Phase 1: Local Testing Infrastructure
- Phase 2: Model Validation
- Phase 3: Cloud VLM Integration
- Phase 4: Backend & API
- Phase 5: Mobile App
- Phase 6: Production Deployment

**When to update**: When completing a major phase or milestone

---

### [development_guide.md](development_guide.md)
**Purpose**: Technical architecture reference
**Contains**:
- Hybrid edge-cloud architecture design
- Edge layer: YOLOv8-Pose + heuristics (or Grove Vision AI V2)
- Cloud layer: Gemini 2.0 Flash VLM verification
- Application layer: FastAPI + mobile app
- Data persistence strategy (SQLite → Cloud)
- Privacy policy and security considerations

**When to update**: When making architectural decisions

---

### [getting_started.md](getting_started.md)
**Purpose**: Hands-on guide for Phase 0
**Contains**:
- Environment setup commands
- Dataset download instructions
- Model training walkthrough
- Export and deployment to Grove V2
- Troubleshooting common issues
- Completion checklist

**When to update**: When changing Phase 0 workflow or adding new troubleshooting tips

---

### [local_testing_plan.md](local_testing_plan.md)
**Purpose**: Implementation plan for local testing (Phase 1-5)
**Contains**:
- Testing architecture (Grove V2 → XIAO → PC)
- 6 components to build (serial reader, dashboard, metrics, etc.)
- Phase 1-5 breakdown with task lists
- Success criteria and test protocols
- Expected test results and performance targets

**When to update**: When completing phases or adjusting timeline

---

### [testing_framework.md](testing_framework.md)
**Purpose**: Testing strategy and code examples
**Contains**:
- 4-layer testing pyramid (Unit → Component → Integration → E2E)
- Concrete test code examples
- Mock data fixtures
- CI/CD workflow (pre-commit hooks, etc.)
- Coverage requirements
- TDD best practices

**When to update**: When adding new test patterns or discovering best practices

---

## 🎯 Current Project Status

**Phase**: Phase 0 - Model Training & Deployment
**Hardware**: ✅ Grove Vision AI V2 + XIAO ready
**Model**: 🔄 Training from scratch
**Timeline**: ASAP (2-3 weeks for Phase 1-5)

**Next Actions**:
1. Train fall detection model (see [getting_started.md](getting_started.md))
2. Deploy to Grove Vision AI V2
3. Build testing infrastructure (see [local_testing_plan.md](local_testing_plan.md))

---

## 🔄 Document Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                         roadmap.md                              │
│              (Master timeline, links to all others)             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ├─────────────────────────────────┐
                              │                                 │
                              ▼                                 ▼
                   ┌──────────────────────┐      ┌──────────────────────┐
                   │ development_guide.md │      │  getting_started.md  │
                   │   (Architecture)     │      │    (Phase 0 HOW-TO)  │
                   └──────────────────────┘      └──────────────────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │local_testing_plan.md │
                   │  (Phase 1-5 PLAN)    │
                   └──────────────────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │testing_framework.md  │
                   │  (Testing STRATEGY)  │
                   └──────────────────────┘
```

---

## 📝 Documentation Guidelines

### For Contributors

When adding new documentation:

1. **Update this README.md** with links to new docs
2. **Link from roadmap.md** if it's a new phase/milestone
3. **Keep docs focused** - one document = one purpose
4. **Use consistent formatting** - follow existing style
5. **Add to Quick Navigation** table above

### For AI Agents

**To understand the project**:
1. Read [roadmap.md](roadmap.md) first (current status + phases)
2. Check "Current Project Status" section in this file
3. Consult specific docs based on the task:
   - Training model? → [getting_started.md](getting_started.md)
   - Building features? → [local_testing_plan.md](local_testing_plan.md)
   - Writing tests? → [testing_framework.md](testing_framework.md)
   - Architectural questions? → [development_guide.md](development_guide.md)

**Before making changes**:
- Check [roadmap.md](roadmap.md) for current phase
- Review relevant plan document for task breakdown
- Follow [testing_framework.md](testing_framework.md) for test requirements

---

## 🔍 Quick Reference

| Concept | Location |
|---------|----------|
| **System Architecture** | [development_guide.md](development_guide.md#architecture) |
| **Phase 0 Tasks** | [getting_started.md](getting_started.md) |
| **Phase 1-5 Tasks** | [local_testing_plan.md](local_testing_plan.md#implementation-phases) |
| **Testing Pyramid** | [testing_framework.md](testing_framework.md#testing-architecture) |
| **Success Criteria** | [local_testing_plan.md](local_testing_plan.md#success-criteria) |
| **Current Status** | [roadmap.md](roadmap.md) (top section) |
| **Hardware Requirements** | [development_guide.md](development_guide.md#prerequisites) |
| **Timeline** | [roadmap.md](roadmap.md) |
| **Troubleshooting** | [getting_started.md](getting_started.md#troubleshooting) |

---

## 📞 Additional Resources

- **Main README**: `../README.md` (project root - to be created)
- **Training Code**: `../fall_detection/README.md`
- **API Documentation**: To be added in Phase 4
- **Mobile App Docs**: To be added in Phase 5

---

**Last Updated**: 2026-03-08
**Maintained By**: Project team
**For Questions**: See relevant document or create an issue
