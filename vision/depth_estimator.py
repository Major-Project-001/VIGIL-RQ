"""
Monocular depth estimator for VIGIL-RQ.

Uses similar-triangles (known-width) method:

    distance = (focal_length * known_width) / perceived_pixel_width

This is the classical approach for a calibrated camera when a reference
object of known real width is visible.  Results are smoothed with a
per-object exponential moving average to reduce frame-to-frame jitter.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import config
from utils import get_logger

log = get_logger(__name__)


class DepthEstimator:
    """Estimates metric depth from bounding-box width.

    Parameters
    ----------
    focal_length_px : float
        Camera focal length in pixels (obtained during calibration).
    known_object_width_m : float
        Real-world width of the reference object class (metres).
    smoothing_alpha : float
        EMA coefficient for depth smoothing.
        0 = no update (ignore measurements), 1 = no smoothing.
    """

    def __init__(
        self,
        focal_length_px: float = config.DEPTH_FOCAL_LENGTH_PX,
        known_object_width_m: float = config.DEPTH_KNOWN_OBJECT_WIDTH_M,
        smoothing_alpha: float = 0.3,
    ) -> None:
        self.focal_length_px = focal_length_px
        self.known_object_width_m = known_object_width_m
        self.alpha = smoothing_alpha

        self._smoothed: Dict[int, float] = {}   # track_id → smoothed depth

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def estimate(self, track_id: int, bbox_width_px: int) -> Optional[float]:
        """Return the estimated depth in metres for a tracked object.

        Parameters
        ----------
        track_id : int
            ID of the track (used for per-track EMA smoothing).
        bbox_width_px : int
            Pixel width of the bounding box.

        Returns
        -------
        float | None
            Estimated depth in metres, or *None* if ``bbox_width_px`` is zero.
        """
        if bbox_width_px <= 0:
            return None

        raw_depth = (self.focal_length_px * self.known_object_width_m) / bbox_width_px

        if track_id in self._smoothed:
            smoothed = (
                self.alpha * raw_depth
                + (1.0 - self.alpha) * self._smoothed[track_id]
            )
        else:
            smoothed = raw_depth

        self._smoothed[track_id] = smoothed
        return smoothed

    def estimate_from_bbox(
        self, track_id: int, bbox: Tuple[int, int, int, int]
    ) -> Optional[float]:
        """Convenience wrapper; accepts a full ``(x, y, w, h)`` bbox tuple."""
        _, _, w, _ = bbox
        return self.estimate(track_id, w)

    def remove_track(self, track_id: int) -> None:
        """Clear smoothing history for a track that has been deregistered."""
        self._smoothed.pop(track_id, None)

    def clear(self) -> None:
        """Clear all smoothing history."""
        self._smoothed.clear()
