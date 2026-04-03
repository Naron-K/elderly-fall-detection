# Development Guide: AI-Powered Elderly Fall Detection System (MVP)

**Goal**: Build a hybrid edge-cloud fall detection system that uses local computer vision for fast detection and cloud-based Vision-Language Models (VLM) for accurate verification and context understanding.

**Reference Architecture**: Hybrid Edge-Cloud (Local Heuristic → Cloud Reasoning)

## Prerequisites

> [!IMPORTANT]
> **Hardware**: For this MVP, we run the "Edge" component on your Windows machine. You need a webcam or an RTSP stream (e.g., "IP Webcam" app on Android).

> [!NOTE]
> **API Key**: You need a Google Gemini API key. We use **Gemini 2.0 Flash** for speed and intelligence.

## Architecture

### 1. Edge Layer (Local PC)
- **Input**: RTSP Stream or USB Camera.
- **Processing**:
    - **YOLOv8-Pose**: Extracts 17 skeletal keypoints per frame.
    - **Heuristic Engine**:
        - **Fall Detection**: Monitors vertical velocity of hips/shoulders + torso angle.
        - **Activity Logging**: Periodically classifies user state (pose + location).
- **Output**:
    - **IMMEDIATE**: Triggers "Potential Fall" event → sends frames to Cloud.
    - **PERIODIC** (every 60s): The local PC interprets the raw image data to derive an "Activity Heartbeat" (e.g., "Standing in Kitchen") and saves this to the local DB for pattern learning. *(Note: Since your Grove Vision AI v2 provides image data, the Edge PC will run the YOLO pose estimation to generate this heartbeat).*

### 2. Cloud Layer (Reasoning & Learning)
- **Component**: Anomaly Detection Engine (VLM-based)
- **Inputs**:
    1. **Video**: 5-frame sequence (JPEG, base64-encoded).
        - *Why 5 frames?* A single frame cannot show motion. The VLM needs temporal context (~1-2 seconds) to distinguish a fast controlled movement (sitting down) from an uncontrolled fall.
        - *Optimization Check*: You can reduce this to **3 frames** to save bandwidth and lower API latency, or increase to **10 frames** for higher accuracy.
        ```json
        {
          "timestamp": "2024-03-20T10:05:00Z",
          "velocity_max": 2.5,
          "body_angle": 15,
          "keypoints": [[0.5, 0.3], [0.52, 0.35]]
        }
        ```
    3. **Anonymized Rules (Dynamic)**: E.g., "Rule 1: Expect motion at 10 AM".
        - *Privacy Note*: All sensitive profile data (Name, Age, Health) is securely stored **locally on the user's mobile phone**. The mobile app uses AI to translate this profile into anonymous "monitoring rules" and sends *only* those rules to the cloud under a pseudonym (e.g., "User_A1B2").
    4. **Activity Log** (last 2 hours):
        ```json
        [
          {"time": "09:55", "action": "Walking", "location": "Bedroom"},
          {"time": "10:00", "action": "Sitting", "location": "Living Room"},
          {"time": "10:05", "action": "Lying Down", "location": "Living Room", "duration_sec": 300}
        ]
        ```
- **Process (Gemini 2.0 Flash)**:
    - *Scenario 1 (Fall)*: Heuristic detects fall → VLM confirms accident → **Alert**.
    - *Scenario 2 (Anomaly)*: No movement at 10 AM (wake-up habit) → VLM flags deviation → **Warning**.
    - *Scenario 3 (Normal)*: 10 AM motion in Living Room matches "Morning Exercise" hobby → **Dismiss**.
- **Output**: Verified Alert or Safety Confirmation (JSON).

### VLM Code Example
A Vision-Language Model (VLM) is an AI that can "see" images. We send images + text; no training needed:

```python
import google.generativeai as genai
from PIL import Image
from config.settings import GEMINI_API_KEY, GEMINI_MODEL

genai.configure(api_key=GEMINI_API_KEY)

def analyze_event(frames: list[Image.Image], user_profile: dict, telemetry: dict) -> dict:
    """Send frames + context to Gemini for fall verification."""
    model = genai.GenerativeModel(GEMINI_MODEL)

    context = f"""
    3. **Anonymized Rules (Dynamic)**: E.g., "Rule 1: Expect motion at 10 AM".
        - *Privacy Note*: All sensitive profile data (Name, Age, Health) is securely stored **locally on the user's mobile phone**. The mobile app uses AI to translate this profile into anonymous "monitoring rules" and sends *only* those rules to the cloud under a pseudonym (e.g., "User_A1B2").
    Telemetry: Velocity={telemetry['velocity_max']}m/s, Angle={telemetry['body_angle']}°
    """

    prompt = (
        "Analyze these sequential frames of an elderly person. "
        "Classify as FALL, CONTROLLED_ACTION, or NORMAL_ACTIVITY. "
        "Return JSON: {\"status\": \"...\", \"confidence\": 0.0-1.0, \"reasoning\": \"...\"}"
    )

    try:
        response = model.generate_content([prompt, context, *frames])
        return json.loads(response.text)
    except Exception as e:
        # Safety-first: if VLM fails, treat as potential fall
        return {"status": "FALL", "confidence": 0.5, "reasoning": f"VLM error: {e}"}
```

### 3. Application Layer
- **FastAPI Backend**: Manages lifecycle, exposes `/status` and `/webhook/alert`.
- **Alert Escalation Logic**:
    1. Send Push Notification to mobile app.
    2. Wait 30s for user acknowledgment (press "I'm OK" button).
    3. If no response → Auto-call emergency contact / hotline.

## Privacy Policy (Enforced in Code)
- ❌ **Video frames are NEVER persisted to disk or cloud.** They exist only in memory during analysis.
- ✅ Only telemetry JSON and VLM response JSON are stored.
- ✅ Frames sent to Gemini are subject to Google's API data policies.

## Project Structure
```text
elderly-fall-detection/
├── config/
│   ├── __init__.py
│   ├── settings.py          # Thresholds, API Keys, constants
│   └── user_profile.json    # User-specific data (Age, Habits)
├── src/
│   ├── __init__.py
│   ├── ingestion.py         # StreamManager (RTSP/Webcam, threaded)
│   ├── vision.py            # PoseEstimator (YOLOv8-pose)
│   ├── heuristics.py        # Fall detection math (velocity + angle)
│   ├── frame_buffer.py      # Sliding window of recent frames
│   ├── activity_logger.py   # Logs recognized states to DB
│   ├── cloud_llm.py         # VLM Client (Gemini 2.0 Flash)
│   └── alerting.py          # Push notification + call escalation
├── tests/
│   ├── test_heuristics.py   # Unit tests for fall math
│   └── dataset_test.py      # Validation against fall dataset
├── docs/
│   ├── development_guide.md
│   └── roadmap.md
├── main.py                  # Entry point (FastAPI)
├── requirements.txt
└── .env                     # GEMINI_API_KEY (gitignored)
```

## Implementation Steps

### Step 1 — Setup & Infrastructure
- Initialize Python venv, install dependencies from `requirements.txt`.
- Create `config/settings.py` and `config/user_profile.json` with sample data.

### Step 2 — Edge Implementation ("Fast Path")
- `ingestion.py`: Threaded frame reader (non-blocking).
- `vision.py`: Load YOLOv8-pose, run inference, return keypoints.
- `heuristics.py`: Velocity + angle logic. Triggers on: `V_y > threshold AND angle < 30°`.

### Step 3 — Cloud Integration ("Smart Path")
- `cloud_llm.py`: `GeminiClient` with retry logic and timeout.
- `frame_buffer.py`: Circular buffer of last N frames.
- `activity_logger.py`: Persists activity states to SQLite.

### Step 4 — Alerting & API
- `main.py`: FastAPI app with background detection loop.
- `alerting.py`: Push notification → wait → emergency call escalation.

### Step 5 — Calibration
- Download subset of **UR Fall Detection Dataset**.
- Run heuristic engine against known "Fall" and "ADL" videos.
- **Target metrics**: Recall ≥ 90%, Precision ≥ 70% (prioritize catching falls over avoiding false alarms).

## Data Persistence (MVP → Production)

### MVP: SQLite (Local)
All data stored in a single local `data.db` file. Zero setup.

| Table | Contents |
|-------|----------|
| `activity_log` | Timestamped activity states (action, location, duration) |
| `alerts` | Triggered alerts with VLM reasoning and resolution status |
| `user_profile` | Cached profile data |

### Production: Cloud Stack (AWS VPS)

| Data Type | Service | Why |
|-----------|---------|-----|
| **Telemetry & Activity Logs** | **InfluxDB OSS** or **TimescaleDB** | Hosted directly on your AWS EC2 instance. Time-series optimized for fast pattern queries. |
| **User Profiles & Auth** | **PostgreSQL** | Self-hosted on the same EC2 instance. Handles relational data securely without relying on 3rd party SaaS. |
| **Video Frames (emergency)** | **AWS S3** | Create an S3 bucket with a 30-day lifecycle expiration policy for cheap, secure, and reliable blob storage. |

> [!TIP]
> **Why AWS VPS?** Renting a Virtual Private Server (e.g., EC2) on AWS gives you maximum control and predictable costs. You can deploy your FastAPI backend via Docker alongside your self-hosted databases (InfluxDB/Postgres). AWS S3 handles the video blobs efficiently, and you can easily use Firebase Cloud Messaging (FCM) or AWS SNS for mobile push notifications directly from your EC2.

## Future: Mobile Alert App (iOS & Android)

### Recommended Approach: React Native + Expo
- **One codebase** → builds for both iOS and Android.
- **Push Notifications**: Firebase Cloud Messaging (FCM) for Android, APNs for iOS — both handled by Expo's `expo-notifications`.
- **Key Screens**:
    1. **Dashboard**: Live status ("Last seen: Walking in Kitchen, 2 min ago").
    2. **Alert Screen**: Full-screen red alert with "I'm OK" dismiss button + 30s countdown.
    3. **Profile Setup**: Age, habits, emergency contacts.
    4. **History**: Timeline of daily activity + past alerts.
- **Emergency Call**: Uses `expo-linking` to trigger native phone dialer (`tel:+84...`).

### Alert Flow (End-to-End)
```
Edge detects fall → Cloud VLM confirms → FastAPI triggers FCM push
    → Phone vibrates + loud sound + full-screen alert
    → User has 30 seconds to press "I'm OK"
    → If no response → Auto-dial emergency contact
    → If still no response after 60s → Auto-dial emergency hotline (115)
```

## Verification Plan

### Automated Tests
- `test_heuristics.py`: Unit tests for velocity/angle math with known inputs.
- `dataset_test.py`: Batch-process 10+ fall videos, assert Recall ≥ 90%.

### Manual Verification
1. Perform "sitting down" → should be ignored or cloud-dismissed.
2. Perform "fall-like" motion (safely!) → should trigger local + cloud alert.
3. Measure end-to-end latency (target: < 5 seconds from fall to notification).
