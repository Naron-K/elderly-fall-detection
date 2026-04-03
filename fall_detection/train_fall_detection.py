#!/usr/bin/env python3
"""
=============================================================================
Fall Detection - Swift-YOLO Training Pipeline for Grove Vision AI V2
=============================================================================
Hardware Target: Grove Vision AI V2 (WiseEye2 HX6538)
  - Arm Cortex-M55 & Ethos-U55
  - Input: 192x192 or 240x240 (int8 quantized)
  - Output: xxx_int8_vela.tflite

Model: Swift-YOLO (YOLOv5-based, optimized by SSCMA)
Classes: ["fall", "standing", "sitting"]
Target: >90% detection accuracy on test videos

Author: Naron (Minh Tan Tran)
Project: Fall Detection for Elderly Care
=============================================================================
"""

import os
import sys
import json
import shutil
import argparse
import logging
from pathlib import Path
from datetime import datetime

# ─── Configuration ───────────────────────────────────────────────────────────
class Config:
    """All hyperparameters and paths in one place."""

    # ── Hardware constraints (Grove Vision AI V2) ──
    INPUT_SIZE = 192          # 192x192 recommended (max 240x240)
    QUANTIZATION = "int8"     # MUST be int8 for Ethos-U55
    MODEL_FORMAT = "tflite"   # Must end with _int8_vela.tflite

    # ── Model architecture ──
    MODEL_TYPE = "swift_yolo_tiny"
    DEEPEN_FACTOR = 0.33      # Depth multiplier
    WIDEN_FACTOR = 0.25       # Width multiplier (0.15-0.25 for tiny)
    STRIDES = [8, 16, 32]

    # ── Dataset ──
    CLASSES = ["fall", "standing", "sitting"]
    NUM_CLASSES = 3
    DATASET_NAME = "fall-detection"

    # ── Training hyperparameters (optimized for small model + edge) ──
    EPOCHS = 300
    BATCH_SIZE = 16
    LEARNING_RATE = 0.01
    WARMUP_EPOCHS = 5
    WEIGHT_DECAY = 0.0005
    MOMENTUM = 0.937
    IOU_THRESHOLD = 0.55
    CONF_THRESHOLD = 0.25

    # ── Augmentation (aggressive for small dataset) ──
    MOSAIC_PROB = 1.0
    MIXUP_PROB = 0.15
    HSV_H = 0.015
    HSV_S = 0.7
    HSV_V = 0.4
    FLIP_LR = 0.5
    SCALE = (0.5, 1.5)
    TRANSLATE = 0.1

    # ── Paths ──
    PROJECT_ROOT = Path(__file__).parent
    DATASET_DIR = PROJECT_ROOT / "datasets" / "fall_detection"
    WORK_DIR = PROJECT_ROOT / "work_dirs"
    EXPORT_DIR = PROJECT_ROOT / "exported_models"

    @classmethod
    def to_dict(cls):
        return {k: str(v) if isinstance(v, Path) else v
                for k, v in vars(cls).items()
                if not k.startswith('_') and k.isupper()}


# ─── Logging Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('training.log')
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# STEP 1: Dataset Preparation
# =============================================================================
def prepare_dataset_from_roboflow(api_key: str = None):
    """
    Download fall detection dataset from Roboflow in COCO format.
    Recommended dataset: roboflow-universe-projects/fall-detection-ca3o8

    If no API key, creates the expected directory structure for manual setup.
    """
    dataset_dir = Config.DATASET_DIR
    dataset_dir.mkdir(parents=True, exist_ok=True)

    if api_key:
        try:
            from roboflow import Roboflow
            rf = Roboflow(api_key=api_key)
            project = rf.workspace().project("fall-detection-ca3o8")
            dataset = project.version(4).download(
                "coco",
                location=str(dataset_dir)
            )
            logger.info(f"Dataset downloaded to {dataset_dir}")
            return dataset_dir
        except Exception as e:
            logger.warning(f"Roboflow download failed: {e}")

    # Create directory structure for manual dataset setup
    for split in ["train", "valid", "test"]:
        (dataset_dir / split / "images").mkdir(parents=True, exist_ok=True)
        (dataset_dir / split / "labels").mkdir(parents=True, exist_ok=True)

    # Create data.yaml for YOLO format
    data_yaml = {
        "train": str(dataset_dir / "train" / "images"),
        "val": str(dataset_dir / "valid" / "images"),
        "test": str(dataset_dir / "test" / "images"),
        "nc": Config.NUM_CLASSES,
        "names": Config.CLASSES
    }

    import yaml
    with open(dataset_dir / "data.yaml", 'w') as f:
        yaml.dump(data_yaml, f, default_flow_style=False)

    logger.info(f"Dataset structure created at {dataset_dir}")
    logger.info("Please add your images and labels, or use Roboflow API key.")
    return dataset_dir


def convert_coco_to_yolo(coco_json_path: str, output_dir: str, img_dir: str):
    """Convert COCO JSON annotations to YOLO TXT format."""
    with open(coco_json_path, 'r') as f:
        coco = json.load(f)

    # Build category mapping
    cat_map = {}
    for cat in coco['categories']:
        cat_map[cat['id']] = cat['name']

    # Map category names to our class indices
    class_map = {name: idx for idx, name in enumerate(Config.CLASSES)}

    # Build image lookup
    img_lookup = {img['id']: img for img in coco['images']}

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    converted = 0
    for ann in coco['annotations']:
        img = img_lookup[ann['image_id']]
        img_w, img_h = img['width'], img['height']

        cat_name = cat_map.get(ann['category_id'], '').lower()

        # Map to our classes
        if 'fall' in cat_name:
            cls_idx = class_map.get('fall', 0)
        elif 'stand' in cat_name or 'walk' in cat_name:
            cls_idx = class_map.get('standing', 1)
        elif 'sit' in cat_name:
            cls_idx = class_map.get('sitting', 2)
        else:
            continue

        # COCO bbox: [x, y, width, height] -> YOLO: [cx, cy, w, h] normalized
        x, y, w, h = ann['bbox']
        cx = (x + w / 2) / img_w
        cy = (y + h / 2) / img_h
        nw = w / img_w
        nh = h / img_h

        # Clamp values
        cx = max(0, min(1, cx))
        cy = max(0, min(1, cy))
        nw = max(0, min(1, nw))
        nh = max(0, min(1, nh))

        # Write label file
        label_file = output_path / (Path(img['file_name']).stem + '.txt')
        with open(label_file, 'a') as f:
            f.write(f"{cls_idx} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}\n")

        converted += 1

    logger.info(f"Converted {converted} annotations to YOLO format in {output_dir}")


# =============================================================================
# STEP 2: SSCMA Config Generation (for Swift-YOLO)
# =============================================================================
def generate_sscma_config():
    """
    Generate SSCMA-compatible config for Swift-YOLO fall detection.
    This config is used with: python3 tools/train.py <config_path>
    """
    config_content = f'''# Swift-YOLO Fall Detection Config for Grove Vision AI V2
# Optimized for 192x192 int8 quantized deployment
# Based on: swift_yolo_tiny_1xb16_300e_coco.py

_base_ = ["../_base_/default_runtime_det.py"]

# ── Anchors (optimized for human body proportions) ──
anchors = [
    [(8, 16), (14, 32), (24, 20)],      # P3/8  - small parts
    [(22, 48), (42, 36), (38, 80)],      # P4/16 - torso
    [(76, 58), (96, 128), (156, 168)]    # P5/32 - full body
]

# ── Model architecture ──
num_classes = {Config.NUM_CLASSES}
deepen_factor = {Config.DEEPEN_FACTOR}
widen_factor = {Config.WIDEN_FACTOR}
strides = {Config.STRIDES}

model = dict(
    type='mmyolo.YOLODetector',
    backbone=dict(
        type='YOLOv5CSPDarknet',
        deepen_factor=deepen_factor,
        widen_factor=widen_factor,
    ),
    neck=dict(
        type='YOLOv5PAFPN',
        deepen_factor=deepen_factor,
        widen_factor=widen_factor,
    ),
    bbox_head=dict(
        head_module=dict(
            num_classes=num_classes,
            in_channels=[256, 512, 1024],
            widen_factor=widen_factor,
        ),
    ),
)

# ── Input pipeline ──
imgsz = ({Config.INPUT_SIZE}, {Config.INPUT_SIZE})

# ── Training settings ──
max_epochs = {Config.EPOCHS}
batch_size = {Config.BATCH_SIZE}
lr = {Config.LEARNING_RATE}
weight_decay = {Config.WEIGHT_DECAY}
warmup_epochs = {Config.WARMUP_EPOCHS}

# ── Augmentation pipeline ──
train_pipeline = [
    dict(type='Mosaic', img_scale=imgsz, prob={Config.MOSAIC_PROB}),
    dict(type='YOLOv5RandomAffine',
         max_rotate_degree=15,
         max_translate_ratio={Config.TRANSLATE},
         scaling_ratio_range={Config.SCALE},
         border=(-imgsz[0] // 2, -imgsz[1] // 2)),
    dict(type='YOLOv5MixUp', prob={Config.MIXUP_PROB}),
    dict(type='mmdet.YOLOXHSVRandomAug',
         hue_delta={int(Config.HSV_H * 255)},
         saturation_delta={int(Config.HSV_S * 255)},
         value_delta={int(Config.HSV_V * 255)}),
    dict(type='RandomFlip', prob={Config.FLIP_LR}),
    dict(type='Resize', scale=imgsz, keep_ratio=False),
    dict(type='PackDetInputs'),
]

# ── Validation pipeline ──
val_pipeline = [
    dict(type='Resize', scale=imgsz, keep_ratio=False),
    dict(type='PackDetInputs'),
]

# ── Optimizer ──
optim_wrapper = dict(
    type='OptimWrapper',
    optimizer=dict(
        type='SGD',
        lr=lr,
        momentum={Config.MOMENTUM},
        weight_decay=weight_decay,
        nesterov=True,
    ),
)

# ── Learning rate schedule ──
param_scheduler = [
    dict(type='LinearLR', start_factor=0.001,
         by_epoch=True, begin=0, end=warmup_epochs),
    dict(type='CosineAnnealingLR',
         by_epoch=True, begin=warmup_epochs, end=max_epochs,
         eta_min=lr * 0.01),
]

# ── Data settings ──
data_root = 'datasets/fall_detection'
class_name = {Config.CLASSES}

train_dataloader = dict(
    batch_size=batch_size,
    num_workers=4,
    dataset=dict(
        type='YOLOv5CocoDataset',
        data_root=data_root,
        ann_file='train/_annotations.coco.json',
        data_prefix=dict(img='train/'),
        pipeline=train_pipeline,
    ),
)

val_dataloader = dict(
    batch_size=batch_size,
    num_workers=2,
    dataset=dict(
        type='YOLOv5CocoDataset',
        data_root=data_root,
        ann_file='valid/_annotations.coco.json',
        data_prefix=dict(img='valid/'),
        pipeline=val_pipeline,
    ),
)

# ── Evaluation ──
val_evaluator = dict(
    type='mmdet.CocoMetric',
    ann_file=data_root + '/valid/_annotations.coco.json',
    metric='bbox',
    proposal_nums=(100, 1, 10),
)

# ── Export settings (critical for Grove Vision AI V2) ──
# Must export as int8_vela.tflite
'''

    config_dir = Config.PROJECT_ROOT / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "swift_yolo_fall_detection_192.py"

    with open(config_path, 'w') as f:
        f.write(config_content)

    logger.info(f"SSCMA config saved to {config_path}")
    return config_path


# =============================================================================
# STEP 3: Training Script (Ultralytics YOLOv5/v8 Alternative)
# =============================================================================
def train_with_ultralytics():
    """
    Train using Ultralytics framework (simpler setup than SSCMA).
    The model will be exported and converted for Grove Vision AI V2.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("Install ultralytics: pip install ultralytics")
        return None

    # Use YOLOv8n (nano) as base - closest to Swift-YOLO
    model = YOLO('yolov8n.pt')

    data_yaml = Config.DATASET_DIR / "data.yaml"
    if not data_yaml.exists():
        logger.error(f"data.yaml not found at {data_yaml}")
        return None

    Config.WORK_DIR.mkdir(parents=True, exist_ok=True)

    # Train with optimizations for edge deployment
    results = model.train(
        data=str(data_yaml),
        epochs=Config.EPOCHS,
        imgsz=Config.INPUT_SIZE,
        batch=Config.BATCH_SIZE,
        lr0=Config.LEARNING_RATE,
        lrf=0.01,                    # Final LR = lr0 * lrf
        momentum=Config.MOMENTUM,
        weight_decay=Config.WEIGHT_DECAY,
        warmup_epochs=Config.WARMUP_EPOCHS,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,

        # Augmentation
        hsv_h=Config.HSV_H,
        hsv_s=Config.HSV_S,
        hsv_v=Config.HSV_V,
        degrees=15.0,                # Rotation (falls happen at angles)
        translate=Config.TRANSLATE,
        scale=0.5,
        shear=2.0,
        perspective=0.0001,          # Slight perspective for camera angles
        flipud=0.1,                  # Vertical flip (simulates inverted camera)
        fliplr=Config.FLIP_LR,
        mosaic=Config.MOSAIC_PROB,
        mixup=Config.MIXUP_PROB,

        # Output
        project=str(Config.WORK_DIR),
        name="fall_detection_swift_yolo",
        exist_ok=True,
        save=True,
        save_period=50,
        plots=True,
        verbose=True,

        # Performance
        patience=50,                 # Early stopping
        workers=4,
        device='0',                  # Use GPU if available
        amp=True,                    # Mixed precision training
    )

    logger.info("Training completed!")
    return results


# =============================================================================
# STEP 4: Model Export for Grove Vision AI V2
# =============================================================================
def export_to_tflite(model_path: str):
    """
    Export trained model to TFLite INT8 format for Grove Vision AI V2.

    CRITICAL: Grove Vision AI V2 ONLY accepts xxx_int8_vela.tflite format.
    Standard int8.tflite will NOT work.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("Install ultralytics: pip install ultralytics")
        return None

    model = YOLO(model_path)

    Config.EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Export to TFLite with INT8 quantization
    logger.info("Exporting to TFLite INT8...")
    export_path = model.export(
        format='tflite',
        imgsz=Config.INPUT_SIZE,
        int8=True,
        # Representative dataset for calibration
        data=str(Config.DATASET_DIR / "data.yaml"),
    )

    logger.info(f"TFLite model exported to: {export_path}")
    return export_path


def compile_with_vela(tflite_path: str):
    """
    Compile TFLite INT8 model with Vela compiler for Ethos-U55.
    This produces the xxx_int8_vela.tflite required by Grove Vision AI V2.

    Install: pip install ethos-u-vela
    """
    output_dir = Config.EXPORT_DIR / "vela"
    output_dir.mkdir(parents=True, exist_ok=True)

    vela_cmd = f"""vela \\
        --output-dir {output_dir} \\
        --accelerator-config ethos-u55-128 \\
        --config vela_config.ini \\
        --system-config Ethos_U55_High_End_Embedded \\
        --memory-mode Shared_Sram \\
        --optimise Performance \\
        {tflite_path}"""

    logger.info(f"Running Vela compiler...")
    logger.info(f"Command: {vela_cmd}")

    ret = os.system(vela_cmd)
    if ret != 0:
        logger.warning("Vela compilation failed. See manual instructions.")
        return None

    # Find output file
    vela_output = list(output_dir.glob("*_vela.tflite"))
    if vela_output:
        final_path = vela_output[0]
        logger.info(f"Vela model ready: {final_path}")
        return str(final_path)

    return None


# =============================================================================
# STEP 5: Video Test Evaluation Pipeline
# =============================================================================
def evaluate_on_video(model_path: str, video_path: str, output_path: str = None):
    """
    Evaluate fall detection model on test video.
    Calculates frame-level and event-level accuracy.
    """
    import cv2
    import numpy as np

    try:
        from ultralytics import YOLO
        model = YOLO(model_path)
    except ImportError:
        logger.error("Install ultralytics for evaluation")
        return None

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {video_path}")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Video writer for annotated output
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Tracking metrics
    results_log = []
    fall_detections = 0
    standing_detections = 0
    sitting_detections = 0
    no_detection_frames = 0
    frame_idx = 0

    # Temporal smoothing buffer (reduces false positives)
    detection_buffer = []
    BUFFER_SIZE = 5  # Number of frames for temporal smoothing

    logger.info(f"Evaluating on video: {video_path}")
    logger.info(f"Total frames: {total_frames}, FPS: {fps}")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize to model input size for inference
        results = model.predict(
            frame,
            imgsz=Config.INPUT_SIZE,
            conf=Config.CONF_THRESHOLD,
            iou=Config.IOU_THRESHOLD,
            verbose=False,
        )

        frame_detections = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                cls_name = Config.CLASSES[cls_id] if cls_id < len(Config.CLASSES) else "unknown"
                xyxy = box.xyxy[0].tolist()

                frame_detections.append({
                    'class': cls_name,
                    'confidence': conf,
                    'bbox': xyxy,
                })

                # Count detections
                if cls_name == 'fall':
                    fall_detections += 1
                elif cls_name == 'standing':
                    standing_detections += 1
                elif cls_name == 'sitting':
                    sitting_detections += 1

                # Draw on frame
                if output_path:
                    x1, y1, x2, y2 = map(int, xyxy)
                    color = (0, 0, 255) if cls_name == 'fall' else (0, 255, 0)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    label = f"{cls_name}: {conf:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        if not frame_detections:
            no_detection_frames += 1

        # Temporal smoothing
        detection_buffer.append(frame_detections)
        if len(detection_buffer) > BUFFER_SIZE:
            detection_buffer.pop(0)

        # Check for fall event (majority voting in buffer)
        fall_count_in_buffer = sum(
            1 for dets in detection_buffer
            if any(d['class'] == 'fall' for d in dets)
        )
        is_fall_event = fall_count_in_buffer >= (BUFFER_SIZE * 0.6)

        # Add FALL ALERT overlay
        if is_fall_event and output_path:
            cv2.putText(frame, "⚠ FALL DETECTED", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

        results_log.append({
            'frame': frame_idx,
            'time_sec': frame_idx / fps if fps > 0 else 0,
            'detections': frame_detections,
            'is_fall_event': is_fall_event,
        })

        if output_path:
            out.write(frame)

        frame_idx += 1

        # Progress
        if frame_idx % 100 == 0:
            logger.info(f"Processed {frame_idx}/{total_frames} frames "
                        f"({frame_idx/total_frames*100:.1f}%)")

    cap.release()
    if output_path:
        out.release()

    # ── Calculate metrics ──
    total_processed = frame_idx
    detection_rate = (total_processed - no_detection_frames) / total_processed * 100

    # Event-level analysis
    fall_events = []
    in_fall = False
    fall_start = None
    for entry in results_log:
        if entry['is_fall_event'] and not in_fall:
            in_fall = True
            fall_start = entry['time_sec']
        elif not entry['is_fall_event'] and in_fall:
            in_fall = False
            fall_events.append({
                'start_sec': fall_start,
                'end_sec': entry['time_sec'],
                'duration_sec': entry['time_sec'] - fall_start,
            })
    if in_fall:
        fall_events.append({
            'start_sec': fall_start,
            'end_sec': results_log[-1]['time_sec'],
            'duration_sec': results_log[-1]['time_sec'] - fall_start,
        })

    metrics = {
        'video_path': video_path,
        'total_frames': total_processed,
        'fps': fps,
        'detection_rate': round(detection_rate, 2),
        'fall_frame_count': fall_detections,
        'standing_frame_count': standing_detections,
        'sitting_frame_count': sitting_detections,
        'no_detection_frames': no_detection_frames,
        'fall_events': fall_events,
        'fall_event_count': len(fall_events),
        'temporal_buffer_size': BUFFER_SIZE,
    }

    logger.info("=" * 60)
    logger.info("EVALUATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total frames processed:  {total_processed}")
    logger.info(f"Detection rate:          {detection_rate:.1f}%")
    logger.info(f"Fall detections:         {fall_detections}")
    logger.info(f"Standing detections:     {standing_detections}")
    logger.info(f"Sitting detections:      {sitting_detections}")
    logger.info(f"Fall events detected:    {len(fall_events)}")
    for i, evt in enumerate(fall_events):
        logger.info(f"  Event {i+1}: {evt['start_sec']:.1f}s - "
                     f"{evt['end_sec']:.1f}s ({evt['duration_sec']:.1f}s)")
    logger.info("=" * 60)

    # Save metrics
    metrics_path = Config.WORK_DIR / "evaluation_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

    return metrics


# =============================================================================
# STEP 6: Batch Video Evaluation
# =============================================================================
def batch_evaluate(model_path: str, video_dir: str, ground_truth_path: str = None):
    """
    Evaluate model on multiple test videos and compute aggregate metrics.
    Ground truth format (JSON):
    {
        "video1.mp4": [{"start": 2.0, "end": 5.0, "label": "fall"}, ...],
        "video2.mp4": [...]
    }
    """
    import glob

    video_dir = Path(video_dir)
    videos = list(video_dir.glob("*.mp4")) + list(video_dir.glob("*.avi"))

    if not videos:
        logger.error(f"No videos found in {video_dir}")
        return None

    # Load ground truth if available
    gt = None
    if ground_truth_path and os.path.exists(ground_truth_path):
        with open(ground_truth_path, 'r') as f:
            gt = json.load(f)

    all_metrics = []
    tp, fp, fn = 0, 0, 0

    for video in videos:
        logger.info(f"\n{'='*40}\nEvaluating: {video.name}\n{'='*40}")
        output_video = Config.WORK_DIR / f"annotated_{video.name}"
        metrics = evaluate_on_video(model_path, str(video), str(output_video))

        if metrics:
            all_metrics.append(metrics)

            # Compare with ground truth
            if gt and video.name in gt:
                gt_events = gt[video.name]
                pred_events = metrics['fall_events']

                # Simple event matching (IoU > 0.3 on time axis)
                matched = set()
                for gt_evt in gt_events:
                    if gt_evt['label'] != 'fall':
                        continue
                    for j, pred_evt in enumerate(pred_events):
                        if j in matched:
                            continue
                        # Temporal IoU
                        overlap_start = max(gt_evt['start'], pred_evt['start_sec'])
                        overlap_end = min(gt_evt['end'], pred_evt['end_sec'])
                        overlap = max(0, overlap_end - overlap_start)
                        union = ((gt_evt['end'] - gt_evt['start']) +
                                 (pred_evt['end_sec'] - pred_evt['start_sec']) -
                                 overlap)
                        tiou = overlap / union if union > 0 else 0
                        if tiou > 0.3:
                            tp += 1
                            matched.add(j)
                            break
                    else:
                        fn += 1

                fp += len(pred_events) - len(matched)

    # Aggregate metrics
    if tp + fp > 0:
        precision = tp / (tp + fp) * 100
    else:
        precision = 0

    if tp + fn > 0:
        recall = tp / (tp + fn) * 100
    else:
        recall = 0

    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0

    aggregate = {
        'videos_evaluated': len(all_metrics),
        'true_positives': tp,
        'false_positives': fp,
        'false_negatives': fn,
        'precision': round(precision, 2),
        'recall': round(recall, 2),
        'f1_score': round(f1, 2),
        'per_video_metrics': all_metrics,
    }

    logger.info("\n" + "=" * 60)
    logger.info("AGGREGATE EVALUATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"Videos evaluated:  {len(all_metrics)}")
    logger.info(f"True Positives:    {tp}")
    logger.info(f"False Positives:   {fp}")
    logger.info(f"False Negatives:   {fn}")
    logger.info(f"Precision:         {precision:.1f}%")
    logger.info(f"Recall:            {recall:.1f}%")
    logger.info(f"F1 Score:          {f1:.1f}%")
    logger.info("=" * 60)

    # Save aggregate
    agg_path = Config.WORK_DIR / "aggregate_metrics.json"
    with open(agg_path, 'w') as f:
        json.dump(aggregate, f, indent=2)

    return aggregate


# =============================================================================
# MAIN CLI
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Fall Detection Pipeline for Grove Vision AI V2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Step 1: Prepare dataset
  python train_fall_detection.py prepare --api-key YOUR_ROBOFLOW_KEY

  # Step 2: Train model
  python train_fall_detection.py train

  # Step 3: Export to TFLite
  python train_fall_detection.py export --weights best.pt

  # Step 4: Compile with Vela (for Grove Vision AI V2)
  python train_fall_detection.py vela --tflite model_int8.tflite

  # Step 5: Evaluate on video
  python train_fall_detection.py eval --weights best.pt --video test.mp4

  # Step 6: Batch evaluate
  python train_fall_detection.py batch-eval --weights best.pt --video-dir ./test_videos
        """
    )

    subparsers = parser.add_subparsers(dest='command')

    # Prepare dataset
    prep = subparsers.add_parser('prepare', help='Prepare fall detection dataset')
    prep.add_argument('--api-key', type=str, default=None,
                      help='Roboflow API key')

    # Train
    train = subparsers.add_parser('train', help='Train Swift-YOLO model')
    train.add_argument('--resume', type=str, default=None,
                       help='Resume from checkpoint')

    # Export
    export = subparsers.add_parser('export', help='Export to TFLite INT8')
    export.add_argument('--weights', type=str, required=True,
                        help='Path to trained .pt weights')

    # Vela compile
    vela = subparsers.add_parser('vela', help='Compile with Vela for Ethos-U55')
    vela.add_argument('--tflite', type=str, required=True,
                      help='Path to INT8 TFLite model')

    # Evaluate
    ev = subparsers.add_parser('eval', help='Evaluate on single video')
    ev.add_argument('--weights', type=str, required=True)
    ev.add_argument('--video', type=str, required=True)
    ev.add_argument('--output', type=str, default=None)

    # Batch evaluate
    bev = subparsers.add_parser('batch-eval', help='Evaluate on video directory')
    bev.add_argument('--weights', type=str, required=True)
    bev.add_argument('--video-dir', type=str, required=True)
    bev.add_argument('--ground-truth', type=str, default=None)

    # Generate SSCMA config
    cfg = subparsers.add_parser('gen-config', help='Generate SSCMA config file')

    args = parser.parse_args()

    if args.command == 'prepare':
        prepare_dataset_from_roboflow(args.api_key)
    elif args.command == 'train':
        train_with_ultralytics()
    elif args.command == 'export':
        export_to_tflite(args.weights)
    elif args.command == 'vela':
        compile_with_vela(args.tflite)
    elif args.command == 'eval':
        evaluate_on_video(args.weights, args.video, args.output)
    elif args.command == 'batch-eval':
        batch_evaluate(args.weights, args.video_dir, args.ground_truth)
    elif args.command == 'gen-config':
        generate_sscma_config()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
