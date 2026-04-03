# Fall Detection System for Grove Vision AI V2

## Overview

End-to-end fall detection pipeline optimized for **Grove Vision AI V2** (WiseEye2 HX6538, Arm Cortex-M55 & Ethos-U55). Trains a Swift-YOLO model to detect falls in real-time at 20-30 FPS while consuming only 0.35W.

**Target**: >90% detection accuracy on test videos.

## Hardware Specifications

| Component | Detail |
|-----------|--------|
| Processor | WiseEye2 HX6538 (Dual Cortex-M55) |
| NPU | Arm Ethos-U55 (128 MAC units) |
| Camera | Raspberry Pi OV5647 (CSI) |
| Input Size | 192×192 pixels (square, max 240×240) |
| Model Format | `*_int8_vela.tflite` (INT8 only) |
| Power | ~0.35W during inference |
| FPS | 20-30 FPS |
| Interface | I2C/UART via XIAO |

## Model Architecture

**Swift-YOLO Tiny** — YOLOv5-based model optimized by Seeed Studio for microcontrollers.

| Parameter | Value |
|-----------|-------|
| Backbone | YOLOv5 CSPDarknet |
| Neck | YOLOv5 PAFPN |
| Input | 192×192×3 |
| Deepen Factor | 0.33 |
| Widen Factor | 0.25 |
| Classes | 3 (fall, standing, sitting) |
| Quantization | INT8 (Ethos-U55) |
| Est. Size | ~200-400 KB |

## Quick Start

### Step 1: Prepare Dataset

```bash
pip install roboflow ultralytics

# Download fall detection dataset from Roboflow
python train_fall_detection.py prepare --api-key YOUR_ROBOFLOW_API_KEY
```

Recommended dataset: [Roboflow Fall Detection](https://universe.roboflow.com/roboflow-universe-projects/fall-detection-ca3o8) (~10K labeled images, 3 classes).

### Step 2: Train Model

```bash
# Train locally (GPU recommended)
python train_fall_detection.py train

# Or use Google Colab (free GPU)
# Upload Fall_Detection_Grove_Vision_AI_V2.ipynb to Colab
```

Key training parameters:
- 300 epochs with early stopping (patience=50)
- 192×192 input resolution
- Heavy augmentation: mosaic, mixup, rotation (15°), perspective
- SGD optimizer with cosine annealing LR

### Step 3: Export to TFLite INT8

```bash
python train_fall_detection.py export --weights work_dirs/fall_detection_swift_yolo/weights/best.pt
```

### Step 4: Compile with Vela

```bash
pip install ethos-u-vela

python train_fall_detection.py vela --tflite path/to/model_int8.tflite
```

Output: `model_int8_vela.tflite` — this is the ONLY format accepted by Grove Vision AI V2.

### Step 5: Deploy to Device

**Option A — SenseCraft Web Toolkit (easiest)**:
1. Open https://seeed-studio.github.io/SenseCraft-Web-Toolkit/ in Chrome
2. Connect Grove Vision AI V2 via USB-C
3. Upload `*_int8_vela.tflite`
4. Press Send

**Option B — Command line (xmodem)**:
```bash
python3 xmodem/xmodem_send.py \
    --port=/dev/ttyACM0 \
    --baudrate=921600 \
    --protocol=xmodem \
    --file=we2_image_gen_local/output_case1_sec_wlcsp/output.img \
    --model="fall_detection_int8_vela.tflite 0xB7B000 0x00000"
```

### Step 6: Test on Videos

```bash
# Single video
python train_fall_detection.py eval --weights best.pt --video test_video.mp4 --output annotated.mp4

# Batch evaluation with ground truth
python train_fall_detection.py batch-eval --weights best.pt --video-dir ./test_videos --ground-truth gt.json
```

## Achieving >90% Accuracy

### Data Quality
- Use diverse fall scenarios: forward falls, backward falls, side falls, falls from chair
- Include negative examples: bending down, sitting, lying on couch
- Balance classes (aim for roughly equal representation)
- Use Grove Vision AI V2 camera to capture training data when possible (best domain match)

### Training Optimization
- Start from YOLOv8n pretrained weights (COCO transfer learning)
- Aggressive augmentation compensates for small datasets
- 15° rotation augmentation is critical (falls happen at angles)
- Perspective augmentation simulates different camera mounting positions

### Temporal Smoothing (Critical for >90%)
Single-frame detection alone won't achieve 90%. The temporal smoothing buffer (5 frames, 60% threshold) dramatically reduces false positives by requiring consistent detection across multiple frames before triggering an alert.

### Post-Processing
- Confidence threshold: 0.25 (deliberately low to catch all falls)
- Temporal buffer reduces false positives from the low threshold
- NMS IoU threshold: 0.55

## Project Structure

```
fall-detection-grove-v2/
├── train_fall_detection.py          # Main training pipeline
├── Fall_Detection_Grove_Vision_AI_V2.ipynb  # Colab notebook
├── vela_config.ini                  # Vela compiler config
├── requirements.txt                 # Python dependencies
├── configs/
│   └── swift_yolo_fall_detection_192.py  # SSCMA config
├── arduino/
│   └── fall_detection_alert/
│       └── fall_detection_alert.ino # XIAO alert system
├── datasets/
│   └── fall_detection/
│       ├── data.yaml
│       ├── train/
│       ├── valid/
│       └── test/
├── work_dirs/                       # Training outputs
└── exported_models/
    └── vela/                        # Final deployable models
```

## Ground Truth Format

For batch evaluation, provide a JSON file:

```json
{
  "video1.mp4": [
    {"start": 2.0, "end": 5.5, "label": "fall"},
    {"start": 12.0, "end": 15.0, "label": "fall"}
  ],
  "video2.mp4": [
    {"start": 8.0, "end": 11.0, "label": "fall"}
  ]
}
```

## Alert System (Arduino/XIAO)

The `fall_detection_alert.ino` sketch connects XIAO to Grove Vision AI V2 via I2C and:
- Reads detection results in real-time
- Applies temporal smoothing (5-frame buffer)
- Triggers buzzer + LED alert on fall detection
- Logs events via Serial

Install the `Seeed_Arduino_SSCMA` library via Arduino Library Manager.

## References

- [SSCMA (Seeed SenseCraft Model Assistant)](https://github.com/Seeed-Studio/ModelAssistant)
- [SSCMA-Micro Firmware](https://github.com/Seeed-Studio/SSCMA-Micro)
- [Grove Vision AI V2 Wiki](https://wiki.seeedstudio.com/grove_vision_ai_v2/)
- [Deploying Custom Models Guide](https://wiki.seeedstudio.com/grove_vision_ai_v2_sscma/)
- [HimaxWiseEyePlus GitHub](https://github.com/HimaxWiseEyePlus/Seeed_Grove_Vision_AI_Module_V2)
