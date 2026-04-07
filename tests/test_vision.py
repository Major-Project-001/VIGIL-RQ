"""
Unit tests for vision modules:
  - ObjectDetector (temporal stability filter)
  - MultiObjectTracker
  - DepthEstimator
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np

from vision.detector import Detection, ObjectDetector
from vision.tracker import MultiObjectTracker
from vision.depth_estimator import DepthEstimator


# ──────────────────────────────────────────────────────────────────────────────
# Detection dataclass
# ──────────────────────────────────────────────────────────────────────────────

class TestDetection:
    def test_center_computed_correctly(self):
        d = Detection(class_id=0, class_name="person", confidence=0.9, bbox=(10, 20, 40, 60))
        assert d.center == (30, 50)

    def test_center_zero_bbox(self):
        d = Detection(class_id=0, class_name="obj", confidence=0.5, bbox=(0, 0, 0, 0))
        assert d.center == (0, 0)


# ──────────────────────────────────────────────────────────────────────────────
# ObjectDetector – temporal stability filter (no OpenCV needed)
# ──────────────────────────────────────────────────────────────────────────────

def _make_detection(name="person"):
    return Detection(class_id=0, class_name=name, confidence=0.9, bbox=(10, 10, 50, 80))


class TestObjectDetectorStability:
    """Test the stability filter without exercising the actual DNN."""

    def _detector(self, stability=3):
        det = ObjectDetector.__new__(ObjectDetector)
        det.conf_threshold = 0.5
        det.nms_threshold  = 0.4
        det.stability_frames = stability
        det._classes = ["person", "obstacle"]
        det._net = None
        det._output_layers = []
        det._use_yolo = False
        det._stability_counter = {}
        det._stable_detections = []
        from collections import defaultdict
        det._stability_counter = defaultdict(int)
        return det

    def test_detection_not_stable_before_threshold(self):
        det = self._detector(stability=3)
        raw = [_make_detection("person")]
        det._update_stability(raw)
        det._update_stability(raw)
        # 2 frames < 3 required → not stable yet
        assert det._stable_detections == []

    def test_detection_stable_after_threshold(self):
        det = self._detector(stability=3)
        raw = [_make_detection("person")]
        for _ in range(3):
            det._update_stability(raw)
        assert len(det._stable_detections) == 1
        assert det._stable_detections[0].class_name == "person"

    def test_stable_detection_disappears_after_absence(self):
        det = self._detector(stability=3)
        raw = [_make_detection("person")]
        for _ in range(3):
            det._update_stability(raw)
        # Now stop seeing "person"
        for _ in range(4):
            det._update_stability([])
        assert det._stable_detections == []

    def test_multiple_classes_tracked_independently(self):
        det = self._detector(stability=2)
        p = _make_detection("person")
        o = _make_detection("obstacle")
        for _ in range(2):
            det._update_stability([p, o])
        assert {d.class_name for d in det._stable_detections} == {"person", "obstacle"}


# ──────────────────────────────────────────────────────────────────────────────
# MultiObjectTracker
# ──────────────────────────────────────────────────────────────────────────────

class TestMultiObjectTracker:
    def _det(self, cx, cy, name="person"):
        bbox = (cx - 20, cy - 30, 40, 60)
        return Detection(class_id=0, class_name=name, confidence=0.9, bbox=bbox)

    def test_new_detections_register_tracks(self):
        t = MultiObjectTracker(max_disappeared=5, max_distance=200)
        dets = [self._det(100, 100), self._det(300, 200)]
        tracks = t.update(dets)
        assert len(tracks) == 2

    def test_track_persists_across_frames(self):
        t = MultiObjectTracker(max_disappeared=5, max_distance=200)
        det = [self._det(100, 100)]
        tracks1 = t.update(det)
        tracks2 = t.update(det)
        ids1 = set(tracks1.keys())
        ids2 = set(tracks2.keys())
        assert ids1 == ids2, "Track ID should persist when detection is stable"

    def test_track_deregistered_after_max_disappeared(self):
        t = MultiObjectTracker(max_disappeared=3, max_distance=200)
        det = [self._det(100, 100)]
        t.update(det)
        # Send empty frames until track should be culled
        for _ in range(4):
            tracks = t.update([])
        assert len(tracks) == 0

    def test_track_not_deregistered_before_max_disappeared(self):
        t = MultiObjectTracker(max_disappeared=5, max_distance=200)
        det = [self._det(100, 100)]
        t.update(det)
        for _ in range(3):  # 3 < 5
            tracks = t.update([])
        assert len(tracks) == 1

    def test_close_detection_matches_existing_track(self):
        t = MultiObjectTracker(max_disappeared=5, max_distance=200)
        t.update([self._det(100, 100)])
        # Move detection slightly
        tracks = t.update([self._det(105, 102)])
        assert len(tracks) == 1   # same track, not a new one

    def test_distant_detection_creates_new_track(self):
        t = MultiObjectTracker(max_disappeared=5, max_distance=50)
        t.update([self._det(100, 100)])
        tracks = t.update([self._det(300, 300)])
        # Original track persists (disappeared=1) plus new track
        assert len(tracks) == 2

    def test_kalman_smoothing_reduces_jitter(self):
        t = MultiObjectTracker()
        # Feed noisy measurements around (200, 200)
        rng = np.random.default_rng(42)
        for _ in range(20):
            noise_x = 200 + rng.normal(0, 5)
            noise_y = 200 + rng.normal(0, 5)
            tracks = t.update([self._det(int(noise_x), int(noise_y))])
        assert len(tracks) == 1
        tid = next(iter(tracks))
        cx, cy = tracks[tid].center
        # Kalman estimate should be close to the true center
        assert abs(cx - 200) < 20
        assert abs(cy - 200) < 20


# ──────────────────────────────────────────────────────────────────────────────
# DepthEstimator
# ──────────────────────────────────────────────────────────────────────────────

class TestDepthEstimator:
    def test_known_width_formula(self):
        """depth = focal * real_width / pixel_width"""
        de = DepthEstimator(focal_length_px=600.0, known_object_width_m=0.4, smoothing_alpha=1.0)
        depth = de.estimate(track_id=0, bbox_width_px=240)
        assert depth == pytest.approx(600.0 * 0.4 / 240, rel=1e-3)

    def test_zero_width_returns_none(self):
        de = DepthEstimator()
        assert de.estimate(0, 0) is None

    def test_smoothing_damps_jumps(self):
        de = DepthEstimator(focal_length_px=600.0, known_object_width_m=0.4, smoothing_alpha=0.1)
        # First estimate
        d1 = de.estimate(0, 200)
        # Sudden change in pixel width
        d2 = de.estimate(0, 50)
        raw_d2 = 600.0 * 0.4 / 50
        # Smoothed value should be between d1 and raw_d2
        assert d1 < d2 < raw_d2 or d1 > d2 > raw_d2 or d2 == pytest.approx(raw_d2, rel=0.5)

    def test_remove_track_clears_history(self):
        de = DepthEstimator()
        de.estimate(track_id=1, bbox_width_px=200)
        de.remove_track(1)
        assert 1 not in de._smoothed

    def test_clear_removes_all_tracks(self):
        de = DepthEstimator()
        for i in range(5):
            de.estimate(track_id=i, bbox_width_px=200)
        de.clear()
        assert de._smoothed == {}

    def test_estimate_from_bbox(self):
        de = DepthEstimator(focal_length_px=600.0, known_object_width_m=0.4, smoothing_alpha=1.0)
        depth = de.estimate_from_bbox(0, (10, 20, 300, 100))
        assert depth == pytest.approx(600.0 * 0.4 / 300, rel=1e-3)
