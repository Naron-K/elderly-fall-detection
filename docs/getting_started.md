# Getting Started: Phase 0 - Model Training

**Status**: ✅ Hardware ready | 🔄 Model training required | 🎯 Timeline: ASAP (2-3 weeks)

This guide will walk you through **Phase 0** to get your Grove Vision AI V2 detecting falls.

---

## 🎯 Phase 0 Quick Start (Days 1-3)

### Prerequisites Checklist

- [x] **Hardware**: Grove Vision AI V2 + XIAO setup
- [ ] **Software**: Python environment with dependencies
- [ ] **Dataset**: Fall detection dataset downloaded
- [ ] **GPU**: Recommended for training (or use Google Colab)

---

## 📋 Step-by-Step Instructions

### Step 1: Setup Python Environment (15 minutes)

```bash
# Navigate to project directory
cd c:\Users\User\OneDrive\Documents\GitHub\elderly-fall-detection

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r fall_detection/requirements.txt

# Verify installation
python -c "from ultralytics import YOLO; print('✅ Ultralytics installed')"
```

**Expected Output**: `✅ Ultralytics installed`

---

### Step 2: Prepare Dataset (30 minutes)

#### Option A: Use Roboflow API (Recommended)

1. **Get API Key**:
   - Go to https://app.roboflow.com/settings/api
   - Copy your API key

2. **Download Dataset**:
```bash
cd fall_detection

# Replace YOUR_API_KEY with your actual key
python train_fall_detection.py prepare --api-key YOUR_API_KEY
```

**Expected Output**:
```
✅ Dataset downloaded: ./datasets/fall_detection
Dataset config:
  Classes: ['fall', 'standing', 'sitting']
  NC: 3
  train: 7,234 images
  valid: 1,808 images
  test: 904 images
```

#### Option B: Manual Dataset Setup

If you don't have Roboflow:

1. Download a fall detection dataset (e.g., from Kaggle, UR Fall Detection)
2. Convert to YOLO format (see existing `convert_coco_to_yolo()` in training script)
3. Place in `fall_detection/datasets/fall_detection/` following the structure:
   ```
   fall_detection/
   ├── train/
   │   ├── images/
   │   └── labels/
   ├── valid/
   │   ├── images/
   │   └── labels/
   └── data.yaml
   ```

---

### Step 3: Train Model (8-12 hours on GPU)

#### Option A: Train Locally (if you have GPU)

```bash
cd fall_detection

# Start training
python train_fall_detection.py train
```

**Monitor Progress**:
- Training logs will appear in console
- Results saved to: `work_dirs/fall_detection_swift_yolo/`
- Training will take ~8-12 hours for 300 epochs
- Early stopping will trigger if no improvement after 50 epochs

**What to Watch For**:
- mAP@50 should increase over epochs (target: >0.85)
- Loss should decrease
- Training will auto-save best weights

#### Option B: Train on Google Colab (Free GPU)

1. Upload `Fall_Detection_Grove_Vision_AI_V2.ipynb` to Google Colab
2. Follow the notebook step-by-step
3. Download the trained model when complete

**Colab Advantages**:
- Free Tesla T4 GPU
- Faster than CPU (~4-6 hours)
- No local setup required

---

### Step 4: Export Model for Grove V2 (15 minutes)

After training completes:

```bash
# Find your best weights
# Location: work_dirs/fall_detection_swift_yolo/weights/best.pt

# Export to TFLite INT8
python train_fall_detection.py export --weights work_dirs/fall_detection_swift_yolo/weights/best.pt
```

**Expected Output**:
```
Exporting to TFLite INT8...
✅ TFLite model exported to: work_dirs/.../best_int8.tflite
   File size: 1.2 MB
```

---

### Step 5: Compile with Vela (5 minutes)

```bash
# Install Vela compiler (if not already installed)
pip install ethos-u-vela

# Compile for Ethos-U55
python train_fall_detection.py vela --tflite work_dirs/fall_detection_swift_yolo/weights/best_saved_model/best_int8.tflite
```

**Expected Output**:
```
Running Vela compiler...
✅ Vela model ready: exported_models/vela/best_int8_vela.tflite
   File size: 1.1 MB
📦 This file is ready for deployment to Grove Vision AI V2!
```

---

### Step 6: Deploy to Grove Vision AI V2 (10 minutes)

#### Method 1: SenseCraft Web Toolkit (Easiest)

1. **Open Browser**: https://seeed-studio.github.io/SenseCraft-Web-Toolkit/ (Chrome only)

2. **Connect Hardware**:
   - Connect Grove Vision AI V2 to PC via USB-C
   - Allow browser permissions for serial port

3. **Upload Model**:
   - Click "Upload Custom Model"
   - Select: `exported_models/vela/best_int8_vela.tflite`
   - Click "Send"
   - Wait for upload confirmation (should take ~30 seconds)

4. **Verify Deployment**:
   - Open Serial Monitor in SenseCraft
   - Point camera at yourself
   - You should see detection boxes appearing

**Expected Output** (in Serial Monitor):
```
Model loaded: best_int8_vela.tflite
Inference FPS: 28.3
Detection: standing (conf: 0.92)
```

---

### Step 7: Test Basic Detection (15 minutes)

1. **Upload Arduino Sketch**:
   - Open `fall_detection/fall_detection_alert.ino` in Arduino IDE
   - Select board: "Seeed XIAO ESP32C3" or your XIAO model
   - Upload to XIAO

2. **Connect Hardware**:
   ```
   Grove Vision AI V2 → XIAO (via I2C Grove connector)
   XIAO → PC (via USB)
   ```

3. **Open Serial Monitor**:
   - Baud rate: 115200
   - You should see detection messages

4. **Test Detection**:
   - Stand in front of camera → should detect "standing"
   - Sit down → should detect "sitting"
   - Simulate fall motion (carefully!) → should trigger buzzer/LED

**Expected Serial Output**:
```
========================================
  Fall Detection Alert System v1.0
  Grove Vision AI V2 + XIAO
========================================
System ready. Monitoring for falls...

[Frame] Class: 1, Conf: 0.92, Box: (100,80,120,160)
[Perf] Pre: 2ms, Inf: 25ms, Post: 3ms

⚠️  ========================
⚠️  FALL DETECTED!
⚠️  Event #1 at 12345 ms
⚠️  ========================
```

---

## ✅ Phase 0 Completion Checklist

Before moving to Phase 1, verify:

- [ ] Dataset downloaded and prepared
- [ ] Model trained successfully (mAP@50 > 0.80)
- [ ] Model exported to `*_int8_vela.tflite` format
- [ ] Model deployed to Grove Vision AI V2
- [ ] Grove V2 runs at 20-30 FPS
- [ ] Basic fall detection works (buzzer triggers on fall motion)
- [ ] XIAO can communicate with PC via serial

**If all checked**: ✅ **Ready for Phase 1 - Serial Bridge & Testing Infrastructure**

---

## 🐛 Troubleshooting

### "CUDA not available" during training
**Solution**: Either install CUDA or use Google Colab

### "Vela compilation failed"
**Solution**:
```bash
pip install --upgrade ethos-u-vela
# Try again with verbose output
vela --verbose exported_models/vela/best_int8.tflite
```

### Grove V2 not responding in SenseCraft
**Solution**:
1. Disconnect and reconnect USB
2. Try different USB port
3. Ensure Chrome browser (Firefox/Edge not supported)
4. Check if device shows up in Device Manager (Windows)

### "No detections" in serial monitor
**Solution**:
1. Verify model was uploaded successfully
2. Check camera is not obstructed
3. Ensure good lighting (bright room recommended)
4. Try moving closer to camera (2-3 meters ideal)

### Low FPS (< 20)
**Solution**:
1. Model might be too large - check file size (should be ~1 MB)
2. Re-run Vela compilation with correct config
3. Verify using 192×192 input size (not 240×240)

---

## 📊 Training Tips for Best Results

### Monitor These Metrics During Training

| Metric | Target | What it means |
|--------|--------|---------------|
| mAP@50 | >0.85 | Detection accuracy |
| Precision | >0.80 | % of detections that are correct |
| Recall | >0.90 | % of actual falls detected |
| Loss | Decreasing | Model is learning |

### If mAP is Low (< 0.70)

1. **More epochs**: Increase from 300 to 500
2. **Better data**: Add more diverse fall examples
3. **Data augmentation**: Already enabled in config
4. **Check labels**: Verify dataset annotations are correct

### If Training is Too Slow

- Use batch size 8 instead of 16 (less memory, slower but works on weaker GPUs)
- Use Google Colab with GPU runtime
- Reduce epochs to 150 for faster iteration

---

## 🎯 Next Steps After Phase 0

Once Phase 0 is complete:

1. **Create issue/branch** for Phase 1 implementation
2. **Review** [local_testing_plan.md](local_testing_plan.md) Phase 1 details
3. **Begin** building serial bridge infrastructure
4. **Write tests** alongside each component (TDD approach)

**Estimated Time to Phase 1**: Immediate (can start next day)

---

## 📞 Getting Help

If you encounter issues:

1. **Check logs**: Look for error messages in terminal
2. **Verify hardware**: Test Grove V2 with SenseCraft first
3. **Model issues**: Try with smaller dataset first (100 images for quick test)
4. **Documentation**: See Grove Vision AI V2 Wiki at https://wiki.seeedstudio.com/

---

**Status**: Ready to begin Phase 0
**Next Action**: Install dependencies and prepare dataset
**Estimated Completion**: Day 3
