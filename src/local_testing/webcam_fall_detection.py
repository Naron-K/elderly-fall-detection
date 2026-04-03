#!/usr/bin/env python3
"""
Real-time fall detection using laptop webcam
Supports multiple YOLO models for comparison
"""

import cv2
import time
import argparse
from pathlib import Path
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    print("❌ Ultralytics not installed. Run: pip install ultralytics")
    exit(1)



class FallDetector:
    """Real-time fall detection with temporal smoothing"""

    def __init__(self, model_path, confidence=0.25, device='cpu'):
        """
        Args:
            model_path: Path to YOLO model (.pt file)
            confidence: Detection confidence threshold
            device: 'cpu' or 'cuda'
        """
        print(f"Loading model: {model_path}")
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.device = device

        # Temporal smoothing buffer (reduces false positives)
        self.detection_buffer = []
        self.buffer_size = 5  # 5 frames
        self.fall_threshold = 0.6  # 60% of frames must detect fall


        # Performance metrics
        self.frame_times = []
        self.fall_count = 0
        self.total_frames = 0

    def detect_frame(self, frame):
        """
        Run detection on a single frame

        Returns:
            results: YOLO detection results
            is_fall: Boolean indicating if fall detected (after temporal smoothing)
        """
        self.total_frames += 1

        # Run inference
        start_time = time.time()
        results = self.model(frame, conf=self.confidence, device=self.device, verbose=False)
        inference_time = (time.time() - start_time) * 1000  # ms

        self.frame_times.append(inference_time)

        # Check for fall detections — collect bounding boxes for pose verification
        fall_detected = False
        fall_boxes = []
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id].lower()
                    if 'fall' in class_name:
                        fall_boxes.append(box.xyxy[0].tolist())

        if fall_boxes:
            fall_detected = True

        # Temporal smoothing
        self.detection_buffer.append(fall_detected)
        if len(self.detection_buffer) > self.buffer_size:
            self.detection_buffer.pop(0)

        # Trigger fall only if threshold met
        fall_ratio = sum(self.detection_buffer) / len(self.detection_buffer)
        is_fall = fall_ratio >= self.fall_threshold

        if is_fall and not hasattr(self, '_last_fall_triggered'):
            self.fall_count += 1
            self._last_fall_triggered = True
        elif not is_fall:
            self._last_fall_triggered = False

        return results, is_fall, inference_time

    def get_stats(self):
        """Get performance statistics"""
        if not self.frame_times:
            return {}

        avg_time = np.mean(self.frame_times[-30:])  # Last 30 frames
        fps = 1000 / avg_time if avg_time > 0 else 0

        return {
            'avg_inference_ms': avg_time,
            'fps': fps,
            'total_frames': self.total_frames,
            'fall_detections': self.fall_count,
        }


def draw_results(frame, results, is_fall, stats):
    """Draw detection boxes and stats on frame"""
    annotated_frame = frame.copy()

    # Draw bounding boxes
    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                # Get box coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = result.names[class_id]

                # Color based on class
                if 'fall' in class_name.lower():
                    color = (0, 0, 255)  # Red for fall
                elif 'sit' in class_name.lower() or 'stand' in class_name.lower():
                    color = (0, 255, 0)  # Green for normal activities
                else:
                    color = (255, 0, 0)  # Blue for others

                # Draw box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)

                # Draw label
                label = f"{class_name} {confidence:.2f}"
                (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(annotated_frame, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1)
                cv2.putText(annotated_frame, label, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Draw fall alert banner
    if is_fall:
        h, w = annotated_frame.shape[:2]
        cv2.rectangle(annotated_frame, (0, 0), (w, 80), (0, 0, 255), -1)
        cv2.putText(annotated_frame, "⚠️ FALL DETECTED ⚠️", (w//2 - 150, 50),
                   cv2.FONT_HERSHEY_BOLD, 1.2, (255, 255, 255), 3)

    # Draw stats overlay
    y_offset = 30 if not is_fall else 100
    cv2.putText(annotated_frame, f"FPS: {stats['fps']:.1f}", (10, y_offset),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(annotated_frame, f"Latency: {stats['avg_inference_ms']:.1f}ms", (10, y_offset + 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(annotated_frame, f"Falls: {stats['fall_detections']}", (10, y_offset + 60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    return annotated_frame


def open_source(source):
    """
    Open a video source: webcam index, RTSP URL, or video file.
    Returns (cap, source_label) or (None, error_msg).
    """
    # Determine source type
    if isinstance(source, str) and (source.startswith("rtsp://") or source.startswith("rtsps://")):
        print(f"\nConnecting to RTSP stream: {source}")
        cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        # Minimise buffering to reduce latency on RTSP
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        label = f"RTSP: {source}"
    elif isinstance(source, str) and not source.lstrip("-").isdigit():
        print(f"\nOpening video file: {source}")
        cap = cv2.VideoCapture(source)
        label = f"File: {source}"
    else:
        cam_idx = int(source)
        print(f"\nOpening camera index {cam_idx}...")
        cap = cv2.VideoCapture(cam_idx)
        label = f"Camera {cam_idx}"

    if not cap.isOpened():
        return None, label
    return cap, label


def main():
    parser = argparse.ArgumentParser(description='Real-time fall detection on webcam or RTSP stream')
    parser.add_argument('--model', type=str, required=True, help='Path to YOLO model (.pt file)')
    parser.add_argument('--conf', type=float, default=0.25, help='Confidence threshold (default: 0.25)')
    parser.add_argument('--device', type=str, default='cpu', choices=['cpu', 'cuda'], help='Device to run on')
    parser.add_argument('--source', type=str, default='0',
                        help='Video source: camera index (0), RTSP URL (rtsp://...), or video file path')
    parser.add_argument('--camera', type=int, default=None, help='Camera index — deprecated, use --source instead')
    parser.add_argument('--save', type=str, help='Save output video to file')
    args = parser.parse_args()

    # Backward-compat: --camera overrides --source if provided
    if args.camera is not None:
        args.source = str(args.camera)

    # Validate model path
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"Model not found: {model_path}")
        print("\nOptions:")
        print("  1. Train a model first (see fall_detection/train_fall_detection.py)")
        print("  2. Download YOLOv8 pretrained: yolov8n.pt, yolov8s.pt")
        return

    # Initialize detector
    detector = FallDetector(args.model, confidence=args.conf, device=args.device)

    # Open video source (with retry for RTSP)
    max_retries = 3
    cap = None
    for attempt in range(1, max_retries + 1):
        cap, label = open_source(args.source)
        if cap is not None:
            break
        print(f"Failed to open source (attempt {attempt}/{max_retries}): {label}")
        if attempt < max_retries:
            time.sleep(2)

    if cap is None:
        print("Could not open video source. Check the URL/index and try again.")
        return

    # Get source properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
    print(f"Source opened ({label}): {width}x{height} @ {fps}fps")

    # Video writer (optional)
    writer = None
    if args.save:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(args.save, fourcc, 20.0, (width, height))
        print(f"💾 Saving to: {args.save}")

    print("\n🚀 Starting fall detection...")
    print("Press 'q' to quit, 'r' to reset stats\n")

    consecutive_failures = 0
    max_failures = 30  # ~1 second at 30fps before reconnect attempt

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    print("Stream lost — attempting reconnect...")
                    cap.release()
                    cap, label = open_source(args.source)
                    if cap is None:
                        print("Reconnect failed. Exiting.")
                        break
                    consecutive_failures = 0
                    print("Reconnected.")
                continue
            consecutive_failures = 0

            # Run detection
            results, is_fall, inference_time = detector.detect_frame(frame)
            stats = detector.get_stats()

            # Draw results
            annotated_frame = draw_results(frame, results, is_fall, stats)

            # Display
            cv2.imshow('Fall Detection', annotated_frame)

            # Save video
            if writer:
                writer.write(annotated_frame)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                detector.fall_count = 0
                detector.total_frames = 0
                detector.frame_times = []
                print("📊 Stats reset")

    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    finally:
        # Cleanup
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()

        # Print final stats
        stats = detector.get_stats()
        print("\n" + "="*50)
        print("📊 Final Statistics:")
        print(f"  Total frames: {stats['total_frames']}")
        print(f"  Average FPS: {stats['fps']:.1f}")
        print(f"  Average latency: {stats['avg_inference_ms']:.1f}ms")
        print(f"  Fall detections: {stats['fall_detections']}")
        print("="*50)


if __name__ == "__main__":
    main()
