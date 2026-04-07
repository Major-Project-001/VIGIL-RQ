"""
Multi-object tracker for VIGIL-RQ.

Implements a centroid-based tracker with per-track Kalman filtering for
smooth, temporally consistent trajectories.

Algorithm:
1. For every new frame, receive a list of Detection centroids.
2. Compute the distance matrix between existing tracks and new detections.
3. Use the Hungarian-like greedy assignment (Hungarian assignment is
   approximated via ``scipy.optimize.linear_sum_assignment`` when available,
   with a greedy fallback).
4. Update matched tracks via their Kalman filters; advance unmatched tracks
   using only the Kalman prediction; register new tracks for unmatched
   detections; deregister tracks that have been missing for too long.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

import config
from utils import get_logger, KalmanFilter2D

log = get_logger(__name__)

try:
    from scipy.optimize import linear_sum_assignment  # type: ignore
    _SCIPY = True
except ImportError:
    _SCIPY = False

try:
    import cv2  # type: ignore
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False


@dataclass
class Track:
    """State for a single tracked object."""
    track_id: int
    class_name: str
    kalman: KalmanFilter2D = field(default_factory=KalmanFilter2D)
    bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)   # last known bbox
    disappeared: int = 0

    @property
    def center(self) -> Tuple[float, float]:
        return self.kalman.position


class MultiObjectTracker:
    """Centroid-based multi-object tracker with Kalman-filter smoothing.

    Parameters
    ----------
    max_disappeared : int
        Frames a track may go unmatched before being deregistered.
    max_distance : float
        Maximum centroid distance (pixels) for a valid match.
    process_noise : float
        Kalman process noise.
    measurement_noise : float
        Kalman measurement noise.
    """

    def __init__(
        self,
        max_disappeared: int = config.TRACKER_MAX_DISAPPEARED,
        max_distance: float = config.TRACKER_MAX_DISTANCE,
        process_noise: float = config.KALMAN_PROCESS_NOISE,
        measurement_noise: float = config.KALMAN_MEASUREMENT_NOISE,
    ) -> None:
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        self._process_noise = process_noise
        self._measurement_noise = measurement_noise

        self._tracks: Dict[int, Track] = {}
        self._next_id = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, detections: list) -> Dict[int, Track]:
        """Update tracker with new detections.

        Parameters
        ----------
        detections : list[Detection]
            Output of ``ObjectDetector.detect()``.

        Returns
        -------
        dict[int, Track]
            Active tracks keyed by track ID.
        """
        if len(detections) == 0:
            for track in self._tracks.values():
                track.disappeared += 1
                track.kalman.predict()
            self._cull_tracks()
            return dict(self._tracks)

        det_centers = np.array([d.center for d in detections], dtype=np.float64)

        if len(self._tracks) == 0:
            for det in detections:
                self._register(det)
            return dict(self._tracks)

        track_ids = list(self._tracks.keys())
        track_centers = np.array(
            [self._tracks[tid].center for tid in track_ids], dtype=np.float64
        )

        # Distance matrix  (tracks × detections)
        dist_matrix = self._euclidean_distance_matrix(track_centers, det_centers)

        matched_tracks, matched_dets = self._assign(dist_matrix)

        # Update matched
        used_det_indices = set()
        for tidx, didx in zip(matched_tracks, matched_dets):
            if dist_matrix[tidx, didx] > self.max_distance:
                continue
            tid = track_ids[tidx]
            det = detections[didx]
            track = self._tracks[tid]
            cx, cy = float(det.center[0]), float(det.center[1])
            track.kalman.update(cx, cy)
            track.bbox = det.bbox
            track.disappeared = 0
            used_det_indices.add(didx)

        # Mark unmatched tracks as disappeared
        matched_track_indices = set(matched_tracks)
        for tidx, tid in enumerate(track_ids):
            if tidx not in matched_track_indices:
                self._tracks[tid].disappeared += 1
                self._tracks[tid].kalman.predict()

        # Register new detections
        for didx, det in enumerate(detections):
            if didx not in used_det_indices:
                self._register(det)

        self._cull_tracks()
        return dict(self._tracks)

    @property
    def tracks(self) -> Dict[int, Track]:
        return dict(self._tracks)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _register(self, det) -> None:
        kf = KalmanFilter2D(
            process_noise=self._process_noise,
            measurement_noise=self._measurement_noise,
        )
        cx, cy = float(det.center[0]), float(det.center[1])
        kf.init(cx, cy)
        track = Track(
            track_id=self._next_id,
            class_name=det.class_name,
            kalman=kf,
            bbox=det.bbox,
        )
        self._tracks[self._next_id] = track
        log.debug("Registered new track #%d (%s)", self._next_id, det.class_name)
        self._next_id += 1

    def _cull_tracks(self) -> None:
        to_delete = [
            tid
            for tid, track in self._tracks.items()
            if track.disappeared > self.max_disappeared
        ]
        for tid in to_delete:
            log.debug("Deregistered track #%d", tid)
            del self._tracks[tid]

    @staticmethod
    def _euclidean_distance_matrix(
        a: np.ndarray, b: np.ndarray
    ) -> np.ndarray:
        """Return (len(a) × len(b)) pairwise Euclidean distance matrix."""
        diff = a[:, np.newaxis, :] - b[np.newaxis, :, :]  # (A, B, 2)
        return np.sqrt((diff ** 2).sum(axis=2))

    def _assign(
        self, dist_matrix: np.ndarray
    ) -> Tuple[List[int], List[int]]:
        """Assign tracks to detections using the Hungarian algorithm."""
        if _SCIPY:
            row_ind, col_ind = linear_sum_assignment(dist_matrix)
            return list(row_ind), list(col_ind)
        # Greedy fallback
        row_ind, col_ind = [], []
        used_cols: set = set()
        for r in range(dist_matrix.shape[0]):
            best_c, best_d = -1, float("inf")
            for c in range(dist_matrix.shape[1]):
                if c not in used_cols and dist_matrix[r, c] < best_d:
                    best_d = dist_matrix[r, c]
                    best_c = c
            if best_c >= 0:
                row_ind.append(r)
                col_ind.append(best_c)
                used_cols.add(best_c)
        return row_ind, col_ind
