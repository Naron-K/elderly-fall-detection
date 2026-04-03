# Local Testing with Laptop Camera

**Skip Grove V2 hardware issues - test fall detection on your laptop camera first!**

This guide helps you:
1. ✅ Train a fall detection model
2. ✅ Test it on your laptop webcam in real-time
3. ✅ Compare different models
4. ✅ Deploy the best model to Grove V2 later

---

## 🚀 Quick Start (30 Minutes)

### Step 1: Install Dependencies

```bash
cd c:\Users\User\OneDrive\Documents\GitHub\elderly-fall-detection

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows

# Install local testing requirements
pip install -r src\local_testing\requirements.txt
```

### Step 2: Download a Pre-trained Model (Quick Test)

**Option A: Use YOLOv8 Pretrained (Fastest - No Training)**

```bash
# Download YOLOv8 nano model (6.3 MB)
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Test on laptop camera
python src\local_testing\webcam_fall_detection.py --model yolov8n.pt
```

**Note**: This won't detect falls yet (it's trained on COCO dataset), but verifies your camera works.

---

**Option B: Train Your Own Fall Detection Model**

```bash
cd fall_detection

# Download fall detection dataset from Roboflow
python train_fall_detection.py prepare --api-key YOUR_ROBOFLOW_KEY

# Quick training (50 epochs for fast test)
python train_fall_detection.py train --epochs 50

# Model will be saved to: work_dirs/fall_detection_swift_yolo/weights/best.pt
```

**Training time**:
- CPU: 2-4 hours (50 epochs)
- GPU: 30-60 minutes (50 epochs)
- Google Colab (free GPU): 30-45 minutes

---

### Step 3: Test on Laptop Camera

```bash
# Test your trained model
python src\local_testing\webcam_fall_detection.py \
  --model work_dirs\fall_detection_swift_yolo\weights\best.pt \
  --conf 0.25

# Save video recording
python src\local_testing\webcam_fall_detection.py \
  --model work_dirs\fall_detection_swift_yolo\weights\best.pt \
  --save output_test.mp4
```

**Controls**:
- `q` - Quit
- `r` - Reset statistics

**What to test**:
1. Stand in front of camera → Should detect "standing" or "person"
2. Sit down → Should detect "sitting"
3. Simulate fall (safely on mat) → Should trigger red alert banner
4. Bend down to pick something up → Should NOT trigger fall (test false positives)

---

### Step 4: Compare Models

Test multiple models side-by-side:

```bash
# Compare YOLOv8 nano vs small vs medium
python src\local_testing\compare_models.py \
  yolov8n.pt \
  yolov8s.pt \
  work_dirs\fall_detection_swift_yolo\weights\best.pt \
  --duration 30

# Results saved to: model_comparison_YYYYMMDD_HHMMSS.json
```

**Comparison metrics**:
- ⚡ FPS (frames per second) - Higher is better
- 💾 Model size - Smaller is better for Grove V2
- 🎯 Fall detections - More accurate is better
- ⏱️ Latency - Lower is better (<500ms target)

---

## 📊 Understanding Results

### Good Performance Indicators

| Metric | Target | Notes |
|--------|--------|-------|
| FPS | ≥20 | Real-time performance |
| Latency | <50ms | Per-frame inference time |
| Model Size | <2 MB | Will fit on Grove V2 |
| Fall Detection | Consistent | Detects all simulated falls |
| False Positives | Low | Doesn't flag bending/sitting as falls |

### If Performance Is Poor

**Low FPS (<10)**:
- Try smaller model: `yolov8n.pt` instead of `yolov8s.pt`
- Use CPU with `--device cpu` explicitly
- Close other applications

**Too Many False Positives**:
- Increase confidence: `--conf 0.5` (default is 0.25)
- The temporal smoothing buffer helps (5-frame window)
- May need more training data for your specific environment

**Missing Falls**:
- Lower confidence: `--conf 0.15`
- Add more diverse fall examples to training data
- Check camera angle (top-down vs side view affects detection)

---

## 🔬 Training Different Model Architectures

### YOLOv8 Variants (Recommended for Grove V2)

```bash
# Train different sizes
python fall_detection\train_fall_detection.py train --model yolov8n  # Nano (fastest)
python fall_detection\train_fall_detection.py train --model yolov8s  # Small (balanced)
python fall_detection\train_fall_detection.py train --model yolov8m  # Medium (most accurate, but slower)
```

**Comparison**:

| Model | Size | FPS (CPU) | FPS (GPU) | Accuracy | Best For |
|-------|------|-----------|-----------|----------|----------|
| YOLOv8n | 6 MB | 15-20 | 50-80 | Good | Grove V2 (edge device) |
| YOLOv8s | 22 MB | 8-12 | 40-60 | Better | Laptop testing |
| YOLOv8m | 52 MB | 4-8 | 30-50 | Best | Cloud inference |

**For Grove V2 deployment**: Use **YOLOv8n** (nano) - it's optimized for edge devices.

---

## 🎯 Recommended Workflow

### Phase 1: Quick Validation (1 hour)
1. ✅ Install dependencies
2. ✅ Download YOLOv8n pretrained
3. ✅ Test camera works: `webcam_fall_detection.py --model yolov8n.pt`

### Phase 2: Train Custom Model (1-4 hours)
1. ✅ Download fall detection dataset
2. ✅ Train YOLOv8n with 50 epochs (quick test)
3. ✅ Test on laptop camera
4. ✅ If accuracy is good, train full 300 epochs overnight

### Phase 3: Compare & Optimize (30 minutes)
1. ✅ Compare multiple models
2. ✅ Test in different scenarios (sitting, walking, bending, falling)
3. ✅ Tune confidence threshold
4. ✅ Select best model

### Phase 4: Deploy to Grove V2 (when ready)
1. ✅ Export to TFLite INT8
2. ✅ Compile with Vela
3. ✅ Upload to Grove V2 via SenseCraft
4. ✅ Verify same performance on hardware

---

## 📁 Output Files

After testing, you'll have:

```
elderly-fall-detection/
├── work_dirs/
│   └── fall_detection_swift_yolo/
│       └── weights/
│           └── best.pt                    # Trained model
├── model_comparison_*.json                 # Comparison results
├── output_test.mp4                         # Recorded test video (optional)
└── runs/
    └── detect/
        └── predict/                        # YOLO output images
```

---

## 🐛 Troubleshooting

### Camera Not Opening

```python
# Test camera directly
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera works!' if cap.isOpened() else 'Camera failed')"

# Try different camera index
python src\local_testing\webcam_fall_detection.py --model yolov8n.pt --camera 1
```

### Low FPS on Laptop

- Close other applications (especially browsers with video)
- Use smaller model (yolov8n)
- Reduce screen resolution in OpenCV (add resize in code)
- Use GPU if available (`--device cuda`)

### Model Not Detecting Falls

1. Check if model has "fall" class:
   ```python
   from ultralytics import YOLO
   model = YOLO('your_model.pt')
   print(model.names)  # Should include 'fall'
   ```

2. If using pretrained YOLOv8 (not fall-specific):
   - It won't detect falls (trained on COCO dataset)
   - You MUST train on fall detection dataset

---

## 🎓 Next Steps

After validating on laptop:

1. **If model works well**:
   - Export to TFLite: `python train_fall_detection.py export --weights best.pt`
   - Compile with Vela: `python train_fall_detection.py vela --tflite best_int8.tflite`
   - Deploy to Grove V2 via SenseCraft

2. **If model needs improvement**:
   - Train longer (300 epochs instead of 50)
   - Add more diverse training data
   - Try different model sizes
   - Adjust augmentation parameters

3. **Move to Phase 1**:
   - Build serial bridge (Grove V2 → PC)
   - Create testing dashboard
   - Automated metrics logging

---

## 📞 Getting Help

**Common issues**:
- Camera permission denied → Check Windows privacy settings
- Module not found → Activate virtual environment: `venv\Scripts\activate`
- CUDA not available → Use `--device cpu` or install CUDA toolkit

**Resources**:
- Ultralytics YOLOv8 docs: https://docs.ultralytics.com/
- OpenCV camera troubleshooting: https://docs.opencv.org/4.x/

---

**Status**: Ready for laptop camera testing
**Estimated Time**: 1-4 hours (depending on training)
**Next Phase**: Deploy to Grove V2 after validation
