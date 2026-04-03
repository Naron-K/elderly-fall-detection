#!/usr/bin/env python3
"""
=============================================================================
Laptop Fall Detection: Train -> Test -> Webcam
=============================================================================
A self-contained pipeline optimised for laptop (no edge hardware required).
Uses YOLOv8n at 640px — faster to train and more accurate than the 192px
edge model.

Quick Start (recommended):
  1. Get a FREE Roboflow API key at https://app.roboflow.com (takes ~2 min)
  2. python train_laptop.py download --api-key YOUR_KEY
  3. python train_laptop.py train
  4. python train_laptop.py test
  5. python train_laptop.py webcam

All-in-one (download + train + test):
  python train_laptop.py all --api-key YOUR_KEY

No API key? Provide a YOLO-format zip from the internet:
  python train_laptop.py download --url https://example.com/fall_dataset.zip

Or use a local zip you already have:
  python train_laptop.py download --zip-path /path/to/dataset.zip

Dataset used (Roboflow): https://universe.roboflow.com/roboflow-universe-projects/fall-detection-ca3o8
=============================================================================
"""

import os
import sys
import json
import shutil
import zipfile
import argparse
import logging
import urllib.request
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent.parent  # project root
DATA_DIR = ROOT / "datasets" / "fall_detection_laptop"
MODELS_DIR = ROOT / "models" / "laptop"
RESULTS_DIR = ROOT / "results" / "laptop"

for d in [DATA_DIR, MODELS_DIR, RESULTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(ROOT / "training_laptop.log"),
    ],
)
log = logging.getLogger(__name__)


# =============================================================================
# 1. DOWNLOAD DATASET
# =============================================================================
def cmd_download(args):
    """
    Download a fall detection dataset.

    Priority:
      1. --api-key  ->  Roboflow Universe (fall-detection-ca3o8, version 4)
      2. --url      ->  any direct zip URL
      3. --zip-path ->  local zip file
    """
    if args.api_key:
        _download_roboflow(args.api_key)
    elif args.url:
        _download_url(args.url)
    elif args.zip_path:
        _extract_zip(args.zip_path)
    else:
        log.error(
            "No dataset source provided.\n"
            "Options:\n"
            "  --api-key  YOUR_ROBOFLOW_KEY   (free at https://app.roboflow.com)\n"
            "  --url      https://...zip\n"
            "  --zip-path /local/dataset.zip"
        )
        sys.exit(1)

    # Search recursively in case Roboflow created a subdirectory
    yamls = list(DATA_DIR.rglob("data.yaml"))
    if yamls:
        log.info(f"Dataset ready. data.yaml: {yamls[0]}")
    else:
        log.warning(f"data.yaml not found under {DATA_DIR} — check dataset structure.")


def _download_roboflow(api_key: str):
    """Download fall-detection-ca3o8 v4 from Roboflow in YOLOv8 format."""
    try:
        from roboflow import Roboflow
    except ImportError:
        log.error("Install roboflow: pip install roboflow")
        sys.exit(1)

    log.info("Connecting to Roboflow...")
    rf = Roboflow(api_key=api_key)

    # Public dataset: https://universe.roboflow.com/roboflow-universe-projects/fall-detection-ca3o8
    project = rf.workspace("roboflow-universe-projects").project("fall-detection-ca3o8")
    dataset = project.version(4).download("yolov8", location=str(DATA_DIR), overwrite=True)

    # Roboflow returns a Dataset object whose .location attribute is the real
    # download path (often a subdirectory like DATA_DIR/fall-detection-4/).
    actual_location = Path(dataset.location) if hasattr(dataset, "location") else DATA_DIR
    log.info(f"Roboflow actual location: {actual_location}")

    # If Roboflow put files in a subdirectory, flatten them into DATA_DIR
    if actual_location != DATA_DIR and actual_location.exists():
        log.info(f"Moving files from {actual_location} -> {DATA_DIR}")
        for item in actual_location.iterdir():
            dest = DATA_DIR / item.name
            if dest.exists():
                shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
            shutil.move(str(item), str(DATA_DIR))
        try:
            actual_location.rmdir()
        except OSError:
            pass  # not empty, leave it

    # Also search recursively in case it's nested further
    yamls = list(DATA_DIR.rglob("data.yaml"))
    if yamls and yamls[0].parent != DATA_DIR:
        nested = yamls[0].parent
        log.info(f"Found nested data.yaml in {nested}, flattening...")
        for item in nested.iterdir():
            dest = DATA_DIR / item.name
            if dest.exists():
                shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
            shutil.move(str(item), str(DATA_DIR))

    log.info(f"Dataset ready at: {DATA_DIR}")
    _fix_data_yaml(DATA_DIR / "data.yaml")


def _download_url(url: str):
    """Download a zip from a direct URL and extract it."""
    zip_path = DATA_DIR / "dataset.zip"
    log.info(f"Downloading from: {url}")

    def _progress(count, block_size, total):
        if total > 0:
            pct = count * block_size / total * 100
            print(f"\r  {min(pct, 100):.1f}%", end="", flush=True)

    urllib.request.urlretrieve(url, zip_path, reporthook=_progress)
    print()
    _extract_zip(str(zip_path))


def _extract_zip(zip_path: str):
    """Extract a YOLO-format dataset zip into DATA_DIR."""
    zip_path = Path(zip_path)
    if not zip_path.exists():
        log.error(f"File not found: {zip_path}")
        sys.exit(1)

    log.info(f"Extracting: {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(DATA_DIR)

    # If there's a nested folder, flatten it
    subdirs = [p for p in DATA_DIR.iterdir() if p.is_dir()]
    yamls = list(DATA_DIR.rglob("data.yaml"))
    if yamls:
        top_yaml = yamls[0]
        if top_yaml.parent != DATA_DIR:
            # Flatten: move contents of the subdirectory up
            nested = top_yaml.parent
            log.info(f"Flattening nested directory: {nested.name}/")
            for item in nested.iterdir():
                dest = DATA_DIR / item.name
                if dest.exists():
                    shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
                shutil.move(str(item), str(DATA_DIR))
            nested.rmdir()

    _fix_data_yaml(DATA_DIR / "data.yaml")


def _fix_data_yaml(yaml_path: Path):
    """Ensure train/val/test paths in data.yaml point to the correct absolute location."""
    if not yaml_path.exists():
        log.warning(f"data.yaml not found at {yaml_path}")
        return

    try:
        import yaml
    except ImportError:
        log.warning("PyYAML not installed - skipping data.yaml path fix")
        return

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    # Map split key -> candidate folder names inside DATA_DIR
    folder_candidates = {
        "train": ["train"],
        "val":   ["valid", "val"],
        "valid": ["valid", "val"],
        "test":  ["test"],
    }

    changed = False
    for split, folders in folder_candidates.items():
        if split not in data:
            continue
        raw = str(data[split])
        p = Path(raw)

        if p.is_absolute() and p.exists():
            continue  # already a valid absolute path

        # Try known folder names first (most reliable for Roboflow datasets)
        resolved = None
        for folder in folders:
            candidate = DATA_DIR / folder / "images"
            if candidate.exists():
                resolved = candidate
                break

        if resolved is None:
            # Fall back: resolve relative path against DATA_DIR
            candidate = (DATA_DIR / p).resolve()
            if candidate.exists():
                resolved = candidate
            else:
                candidate = (yaml_path.parent / p).resolve()
                if candidate.exists():
                    resolved = candidate

        if resolved is not None:
            data[split] = str(resolved)
            changed = True
        else:
            log.warning(f"  split '{split}': could not resolve '{raw}' - leaving as-is")

    # Normalise "valid" -> "val" (ultralytics expects "val")
    if "valid" in data and "val" not in data:
        data["val"] = data.pop("valid")
        changed = True

    if changed:
        with open(yaml_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        log.info(f"Updated data.yaml paths -> {yaml_path}")


# =============================================================================
# 2. TRAIN
# =============================================================================
def cmd_train(args):
    """Train YOLOv8n on the downloaded dataset."""
    try:
        from ultralytics import YOLO
    except ImportError:
        log.error("Install ultralytics: pip install ultralytics")
        sys.exit(1)

    # Find data.yaml — Roboflow may leave it in a subdirectory
    yamls = list(DATA_DIR.rglob("data.yaml"))
    if not yamls:
        log.error(f"data.yaml not found under {DATA_DIR}. Run `download` first.")
        sys.exit(1)
    yaml_path = yamls[0]
    log.info(f"Using dataset: {yaml_path}")

    # Pick device
    import torch
    if args.device == "auto":
        device = "0" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device

    log.info(f"Training on device: {device}")
    log.info(f"Model: {args.model}  |  imgsz: {args.imgsz}  |  epochs: {args.epochs}")

    model = YOLO(args.model)

    run_name = f"fall_laptop_{datetime.now().strftime('%Y%m%d_%H%M')}"

    results = model.train(
        data=str(yaml_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,

        # Optimiser
        lr0=0.01,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,

        # Augmentation (aggressive — fall datasets are small)
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=15.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,

        # Output
        project=str(MODELS_DIR),
        name=run_name,
        exist_ok=False,
        save=True,
        plots=True,
        verbose=True,
        patience=30,
        amp=True,
    )

    best = MODELS_DIR / run_name / "weights" / "best.pt"
    if best.exists():
        # Copy to a stable path for easy reference
        stable = MODELS_DIR / "best.pt"
        shutil.copy(best, stable)
        log.info(f"\nBest model saved to: {stable}")
        log.info(f"Full run at: {MODELS_DIR / run_name}")
    else:
        log.warning("best.pt not found — check training output directory")

    return results


# =============================================================================
# 3. TEST (evaluate on test split)
# =============================================================================
def cmd_test(args):
    """
    Evaluate the trained model on the test split.
    Prints Precision, Recall, mAP50, mAP50-95.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        log.error("Install ultralytics: pip install ultralytics")
        sys.exit(1)

    weights = Path(args.weights)
    if not weights.exists():
        log.error(f"Weights not found: {weights}")
        log.info("Run `train` first, or specify --weights path/to/best.pt")
        sys.exit(1)

    yamls = list(DATA_DIR.rglob("data.yaml"))
    if not yamls:
        log.error(f"data.yaml not found under {DATA_DIR}")
        sys.exit(1)
    yaml_path = yamls[0]

    import torch
    if args.device == "auto":
        device = "0" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device

    log.info(f"Evaluating: {weights}")
    model = YOLO(str(weights))

    # Validate on test split
    metrics = model.val(
        data=str(yaml_path),
        split="test",
        imgsz=args.imgsz,
        conf=args.conf,
        iou=0.5,
        device=device,
        plots=True,
        save_json=True,
        project=str(RESULTS_DIR),
        name=f"test_{datetime.now().strftime('%Y%m%d_%H%M')}",
        verbose=True,
    )

    # Print clean summary
    print("\n" + "=" * 55)
    print("TEST RESULTS")
    print("=" * 55)

    try:
        box = metrics.box
        class_names = model.names

        # Per-class metrics
        print(f"{'Class':<15} {'Precision':>10} {'Recall':>8} {'mAP50':>8} {'mAP50-95':>10}")
        print("-" * 55)
        for i, name in class_names.items():
            p = box.p[i] if i < len(box.p) else 0
            r = box.r[i] if i < len(box.r) else 0
            m50 = box.ap50[i] if i < len(box.ap50) else 0
            m = box.ap[i] if i < len(box.ap) else 0
            print(f"{name:<15} {p:>10.3f} {r:>8.3f} {m50:>8.3f} {m:>10.3f}")

        print("-" * 55)
        print(f"{'all (mean)':<15} {box.mp:>10.3f} {box.mr:>8.3f} {box.map50:>8.3f} {box.map:>10.3f}")
        print("=" * 55)

        # Target check
        print("\nTarget Metrics:")
        recall_ok = box.mr >= 0.90
        prec_ok = box.mp >= 0.70
        print(f"  Recall  >= 90%:    {'PASS' if recall_ok else 'FAIL'}  ({box.mr*100:.1f}%)")
        print(f"  Precision >= 70%:  {'PASS' if prec_ok else 'FAIL'}  ({box.mp*100:.1f}%)")

    except Exception as e:
        log.warning(f"Could not parse detailed metrics: {e}")
        log.info(f"Raw metrics: {metrics}")

    # Save JSON summary
    summary = {
        "weights": str(weights),
        "timestamp": datetime.now().isoformat(),
        "precision": float(metrics.box.mp),
        "recall": float(metrics.box.mr),
        "map50": float(metrics.box.map50),
        "map50_95": float(metrics.box.map),
    }
    out = RESULTS_DIR / "test_summary.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    log.info(f"\nSummary saved to: {out}")

    return metrics


# =============================================================================
# 4. WEBCAM (real-time demo)
# =============================================================================
def cmd_webcam(args):
    """Run real-time fall detection on the laptop webcam."""
    try:
        import cv2
        import numpy as np
        from ultralytics import YOLO
    except ImportError as e:
        log.error(f"Missing dependency: {e}")
        sys.exit(1)

    weights = Path(args.weights)
    if not weights.exists():
        log.error(f"Weights not found: {weights}")
        log.info("Run `train` first, or specify --weights")
        sys.exit(1)

    import torch
    if args.device == "auto":
        device = "0" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device

    log.info(f"Loading model: {weights}")
    model = YOLO(str(weights))
    model.to(device)

    # Temporal smoothing
    buffer = []
    BUFFER_SIZE = 5
    FALL_THRESHOLD = 0.6

    # Stats
    frame_times = []
    fall_count = 0
    in_fall = False

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        log.error("Cannot open webcam")
        sys.exit(1)

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    log.info(f"Camera: {w}x{h}  |  Press 'q' to quit, 'r' to reset stats")

    writer = None
    if args.save:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(args.save, fourcc, 20.0, (w, h))
        log.info(f"Saving to: {args.save}")

    import time

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            t0 = time.time()
            results = model(frame, conf=args.conf, verbose=False)
            inference_ms = (time.time() - t0) * 1000
            frame_times.append(inference_ms)

            # Check for fall in this frame
            fall_now = any(
                "fall" in model.names[int(box.cls[0])].lower()
                for r in results
                for box in (r.boxes or [])
            )

            # Temporal buffer
            buffer.append(fall_now)
            if len(buffer) > BUFFER_SIZE:
                buffer.pop(0)
            is_fall = sum(buffer) / len(buffer) >= FALL_THRESHOLD

            # Count unique fall events
            if is_fall and not in_fall:
                fall_count += 1
            in_fall = is_fall

            # Draw bounding boxes
            annotated = frame.copy()
            for r in results:
                for box in (r.boxes or []):
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls_name = model.names[int(box.cls[0])]
                    conf = float(box.conf[0])
                    color = (0, 0, 255) if "fall" in cls_name.lower() else (0, 255, 0)
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                    lbl = f"{cls_name} {conf:.2f}"
                    (lw, lh), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    cv2.rectangle(annotated, (x1, y1 - lh - 8), (x1 + lw, y1), color, -1)
                    cv2.putText(annotated, lbl, (x1, y1 - 4),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Fall alert banner
            if is_fall:
                cv2.rectangle(annotated, (0, 0), (w, 70), (0, 0, 200), -1)
                cv2.putText(annotated, "!! FALL DETECTED !!", (w // 2 - 160, 48),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 255, 255), 3)

            # Stats overlay
            avg_ms = np.mean(frame_times[-30:]) if frame_times else 0
            fps = 1000 / avg_ms if avg_ms > 0 else 0
            y0 = 90 if is_fall else 25
            cv2.putText(annotated, f"FPS: {fps:.1f}", (10, y0),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
            cv2.putText(annotated, f"Latency: {avg_ms:.0f}ms", (10, y0 + 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
            cv2.putText(annotated, f"Falls: {fall_count}", (10, y0 + 56),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

            cv2.imshow("Fall Detection (laptop)", annotated)

            if writer:
                writer.write(annotated)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("r"):
                frame_times.clear()
                fall_count = 0
                buffer.clear()
                in_fall = False
                print("Stats reset")

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()

    avg_ms = float(np.mean(frame_times)) if frame_times else 0
    print(f"\nSession stats — frames: {len(frame_times)}  avg latency: {avg_ms:.0f}ms  "
          f"avg FPS: {1000/avg_ms:.1f if avg_ms else 0:.1f}  falls detected: {fall_count}")


# =============================================================================
# 5. ALL (download + train + test in one go)
# =============================================================================
def cmd_all(args):
    """Download dataset, train, then test — end-to-end."""
    log.info("=== Step 1/3: Download ===")
    cmd_download(args)

    log.info("\n=== Step 2/3: Train ===")
    cmd_train(args)

    # Point test at freshly trained model
    args.weights = str(MODELS_DIR / "best.pt")

    log.info("\n=== Step 3/3: Test on test split ===")
    cmd_test(args)

    log.info("\n=== All done! ===")
    log.info(f"Model: {MODELS_DIR / 'best.pt'}")
    log.info("Now run: python train_laptop.py webcam")


# =============================================================================
# CLI
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Laptop Fall Detection: train -> test -> webcam",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline (recommended — free Roboflow key from https://app.roboflow.com):
  python train_laptop.py all --api-key YOUR_KEY

  # Step by step:
  python train_laptop.py download --api-key YOUR_KEY
  python train_laptop.py train --epochs 50
  python train_laptop.py test
  python train_laptop.py webcam

  # No API key? Provide a zip URL:
  python train_laptop.py download --url https://example.com/fall_dataset.zip
  python train_laptop.py train

  # Webcam with custom model:
  python train_laptop.py webcam --weights /path/to/best.pt
""",
    )

    # Shared args (device, imgsz)
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"],
                        help="Device (default: auto-detect)")
    shared.add_argument("--imgsz", type=int, default=320,
                        help="Image size for training/inference (default: 320 for CPU speed)")

    sub = parser.add_subparsers(dest="command", required=True)

    # --- download ---
    dl = sub.add_parser("download", help="Download fall detection dataset",
                        parents=[shared])
    dl_src = dl.add_mutually_exclusive_group()
    dl_src.add_argument("--api-key", help="Roboflow API key (free at https://app.roboflow.com)")
    dl_src.add_argument("--url", help="Direct download URL of a YOLO-format zip")
    dl_src.add_argument("--zip-path", help="Path to local YOLO-format zip file")

    # --- train ---
    tr = sub.add_parser("train", help="Train YOLOv8n on the dataset", parents=[shared])
    tr.add_argument("--model", default="yolov8n.pt",
                    help="Base YOLO model (default: yolov8n.pt)")
    tr.add_argument("--epochs", type=int, default=25,
                    help="Training epochs (default: 25)")
    tr.add_argument("--batch", type=int, default=16,
                    help="Batch size (default: 16)")

    # --- test ---
    ts = sub.add_parser("test", help="Evaluate model on the test split", parents=[shared])
    ts.add_argument("--weights", default=str(MODELS_DIR / "best.pt"),
                    help="Path to model weights")
    ts.add_argument("--conf", type=float, default=0.25,
                    help="Confidence threshold (default: 0.25)")

    # --- webcam ---
    wc = sub.add_parser("webcam", help="Real-time webcam fall detection", parents=[shared])
    wc.add_argument("--weights", default=str(MODELS_DIR / "best.pt"),
                    help="Path to model weights")
    wc.add_argument("--conf", type=float, default=0.25,
                    help="Confidence threshold (default: 0.25)")
    wc.add_argument("--camera", type=int, default=0,
                    help="Camera index (default: 0)")
    wc.add_argument("--save", default=None,
                    help="Save output video to this path")

    # --- all ---
    al = sub.add_parser("all", help="Download + train + test in one go", parents=[shared])
    al_src = al.add_mutually_exclusive_group(required=True)
    al_src.add_argument("--api-key", help="Roboflow API key")
    al_src.add_argument("--url", help="Direct zip URL")
    al_src.add_argument("--zip-path", help="Local zip path")
    al.add_argument("--model", default="yolov8n.pt")
    al.add_argument("--epochs", type=int, default=25)
    al.add_argument("--batch", type=int, default=16)
    al.add_argument("--conf", type=float, default=0.25)

    args = parser.parse_args()

    dispatch = {
        "download": cmd_download,
        "train": cmd_train,
        "test": cmd_test,
        "webcam": cmd_webcam,
        "all": cmd_all,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
