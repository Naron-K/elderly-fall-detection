# Session Notes

Quick notes from work sessions. Read this to continue from where you left off.

---

## 2026-03-08: Laptop Camera Testing Setup

### What We Did
- Created laptop camera testing framework (bypasses Grove V2 hardware issues)
- Built real-time fall detection script for webcam
- Built model comparison tool
- Analyzed SenseCraft pre-trained model (YOLOv5, 10 classes)

### Files Created
- `src/local_testing/webcam_fall_detection.py` - Real-time detection on laptop camera
- `src/local_testing/compare_models.py` - Compare multiple models
- `src/local_testing/requirements.txt` - Dependencies
- `src/local_testing/README.md` - **Complete guide (START HERE)**

### SenseCraft Model Analysis
**Found**: Patient fall detection model at https://sensecraft.seeed.cc/ai/view-model/60676-patientfalldetection
- Architecture: YOLOv5
- Classes (10): bed, fall, move, patient, person, sit, stand, walker, wheelchair
- Already deployed to your Grove V2 (but USB connection unstable)
- Cannot easily download for offline comparison

### Decision Made
**Test on laptop camera first**, then deploy to Grove V2 later:
1. Train YOLOv8n model (newer than YOLOv5)
2. Test on laptop camera (no hardware issues)
3. Compare different models
4. Deploy best model to Grove V2

### Next Steps (See `src/local_testing/README.md`)

**Quick Test (15 mins)**:
```bash
pip install ultralytics opencv-python
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
python src\local_testing\webcam_fall_detection.py --model yolov8n.pt
```

**Full Training (2-4 hours)**:
```bash
pip install -r src\local_testing\requirements.txt
cd fall_detection
python train_fall_detection.py prepare --api-key YOUR_KEY
python train_fall_detection.py train --epochs 50
cd ..
python src\local_testing\webcam_fall_detection.py \
  --model fall_detection\work_dirs\fall_detection_swift_yolo\weights\best.pt
```

### Performance Targets
- FPS ≥15 (laptop), ≥20 (Grove V2)
- Recall ≥90%, Precision ≥70%
- Model size <2 MB (for Grove V2)

---

## Future Sessions

Add notes here after each session.

