#!/usr/bin/env python3
"""
Compare multiple fall detection models
Tests on same video/webcam and generates comparison report
"""

import cv2
import time
import argparse
from pathlib import Path
import json
import numpy as np
from datetime import datetime
from ultralytics import YOLO


class ModelBenchmark:
    """Benchmark a single model"""

    def __init__(self, model_path, name=None):
        self.model_path = Path(model_path)
        self.name = name or self.model_path.stem
        self.model = YOLO(str(model_path))

        # Metrics
        self.inference_times = []
        self.detections = []
        self.model_size_mb = self.model_path.stat().st_size / (1024 * 1024)

    def run_on_frame(self, frame, conf=0.25):
        """Run detection on a single frame"""
        start = time.time()
        results = self.model(frame, conf=conf, verbose=False)
        inference_time = (time.time() - start) * 1000  # ms

        self.inference_times.append(inference_time)

        # Extract detections
        detections = []
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    detections.append({
                        'class': self.model.names[int(box.cls[0])],
                        'confidence': float(box.conf[0]),
                        'bbox': box.xyxy[0].tolist()
                    })

        self.detections.append(detections)
        return results

    def get_summary(self):
        """Get benchmark summary statistics"""
        fall_detections = sum(
            1 for frame_dets in self.detections
            for det in frame_dets
            if 'fall' in det['class'].lower()
        )

        total_detections = sum(len(dets) for dets in self.detections)

        return {
            'name': self.name,
            'model_path': str(self.model_path),
            'model_size_mb': round(self.model_size_mb, 2),
            'avg_inference_ms': round(np.mean(self.inference_times), 2) if self.inference_times else 0,
            'min_inference_ms': round(np.min(self.inference_times), 2) if self.inference_times else 0,
            'max_inference_ms': round(np.max(self.inference_times), 2) if self.inference_times else 0,
            'avg_fps': round(1000 / np.mean(self.inference_times), 2) if self.inference_times else 0,
            'total_frames': len(self.detections),
            'total_detections': total_detections,
            'fall_detections': fall_detections,
            'classes': list(self.model.names.values()),
            'num_classes': len(self.model.names),
        }


def compare_models_on_video(model_paths, video_source=0, duration=30, conf=0.25):
    """
    Compare multiple models on the same video source

    Args:
        model_paths: List of paths to model files
        video_source: Video file path or camera index
        duration: How long to test (seconds)
        conf: Confidence threshold
    """
    print("="*60)
    print("🔬 Model Comparison Tool")
    print("="*60)

    # Initialize benchmarks
    benchmarks = []
    for path in model_paths:
        model_path = Path(path)
        if not model_path.exists():
            print(f"⚠️  Skipping {path} (not found)")
            continue

        name = input(f"Enter name for {model_path.name} (or press Enter for default): ").strip()
        benchmark = ModelBenchmark(model_path, name if name else None)
        benchmarks.append(benchmark)
        print(f"✅ Loaded: {benchmark.name} ({benchmark.model_size_mb:.2f} MB)")

    if not benchmarks:
        print("❌ No valid models to compare")
        return

    # Open video source
    print(f"\n📹 Opening video source: {video_source}")
    cap = cv2.VideoCapture(video_source)

    if not cap.isOpened():
        print("❌ Failed to open video source")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"✅ Video opened: {width}x{height}")

    print(f"\n🚀 Running comparison for {duration} seconds...")
    print("Press 'q' to stop early\n")

    start_time = time.time()
    frame_count = 0

    try:
        while (time.time() - start_time) < duration:
            ret, frame = cap.read()
            if not ret:
                print("⏹️  Video ended")
                break

            frame_count += 1

            # Run all models on the same frame
            for benchmark in benchmarks:
                benchmark.run_on_frame(frame, conf=conf)

            # Display progress
            elapsed = time.time() - start_time
            if frame_count % 30 == 0:  # Every 30 frames
                print(f"⏱️  {elapsed:.1f}s / {duration}s ({frame_count} frames)")

            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    finally:
        cap.release()
        cv2.destroyAllWindows()

    # Generate comparison report
    print("\n" + "="*60)
    print("📊 Comparison Results")
    print("="*60)

    results = []
    for benchmark in benchmarks:
        summary = benchmark.get_summary()
        results.append(summary)

        print(f"\n🤖 {summary['name']}")
        print(f"  Model size: {summary['model_size_mb']} MB")
        print(f"  Classes ({summary['num_classes']}): {', '.join(summary['classes'][:5])}{'...' if summary['num_classes'] > 5 else ''}")
        print(f"  Avg inference: {summary['avg_inference_ms']} ms")
        print(f"  Avg FPS: {summary['avg_fps']}")
        print(f"  Total detections: {summary['total_detections']}")
        print(f"  Fall detections: {summary['fall_detections']}")

    # Determine winner
    print("\n" + "="*60)
    print("🏆 Rankings")
    print("="*60)

    # Rank by FPS
    by_fps = sorted(results, key=lambda x: x['avg_fps'], reverse=True)
    print("\n⚡ Fastest (FPS):")
    for i, r in enumerate(by_fps[:3], 1):
        print(f"  {i}. {r['name']}: {r['avg_fps']} FPS")

    # Rank by model size
    by_size = sorted(results, key=lambda x: x['model_size_mb'])
    print("\n💾 Smallest (Size):")
    for i, r in enumerate(by_size[:3], 1):
        print(f"  {i}. {r['name']}: {r['model_size_mb']} MB")

    # Rank by detections (more detections = better?)
    by_detections = sorted(results, key=lambda x: x['fall_detections'], reverse=True)
    print("\n🎯 Most Fall Detections:")
    for i, r in enumerate(by_detections[:3], 1):
        print(f"  {i}. {r['name']}: {r['fall_detections']} falls")

    # Save results
    output_file = f"model_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'test_duration': time.time() - start_time,
            'total_frames': frame_count,
            'models': results
        }, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")
    print("="*60)

    return results


def main():
    parser = argparse.ArgumentParser(description='Compare multiple fall detection models')
    parser.add_argument('models', nargs='+', help='Paths to model files (.pt)')
    parser.add_argument('--video', type=str, default='0', help='Video file or camera index (default: 0)')
    parser.add_argument('--duration', type=int, default=30, help='Test duration in seconds (default: 30)')
    parser.add_argument('--conf', type=float, default=0.25, help='Confidence threshold (default: 0.25)')
    args = parser.parse_args()

    # Parse video source (int or string)
    try:
        video_source = int(args.video)
    except ValueError:
        video_source = args.video

    # Run comparison
    compare_models_on_video(args.models, video_source, args.duration, args.conf)


if __name__ == "__main__":
    main()
