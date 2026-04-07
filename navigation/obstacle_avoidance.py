"""
Obstacle avoidance module for VIGIL-RQ.

Uses depth-annotated detections from the vision pipeline to decide
whether to continue, slow down, or maneuver around obstacles.

Decision logic
--------------
1. If any tracked obstacle is closer than ``OBSTACLE_STOP_DISTANCE`` →
   issue a *stop* command and attempt an evasive maneuver.
2. If any obstacle is within ``OBSTACLE_WARN_DISTANCE`` → reduce speed.
3. Otherwise → proceed normally.

The avoidance planner selects the evasive direction (left / right) based
on which horizontal half of the frame has fewer / farther obstacles.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import config
from utils import get_logger

log = get_logger(__name__)


class ObstacleAvoider:
    """Evaluates obstacle proximity and recommends motion commands.

    Parameters
    ----------
    stop_distance : float
        Metres – robot must stop if an obstacle is closer than this.
    warn_distance : float
        Metres – robot should slow down within this range.
    frame_width : int
        Width of the camera frame in pixels (used for lateral decisions).
    """

    # Possible avoidance recommendations
    CMD_FORWARD = "forward"
    CMD_SLOW = "slow"
    CMD_STOP = "stop"
    CMD_TURN_LEFT = "turn_left"
    CMD_TURN_RIGHT = "turn_right"

    def __init__(
        self,
        stop_distance: float = config.OBSTACLE_STOP_DISTANCE,
        warn_distance: float = config.OBSTACLE_WARN_DISTANCE,
        frame_width: int = config.FRAME_WIDTH,
    ) -> None:
        self.stop_distance = stop_distance
        self.warn_distance = warn_distance
        self.frame_width = frame_width

        self._last_command = self.CMD_FORWARD

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        obstacles: List[Tuple[Tuple[int, int], float]],
    ) -> str:
        """Return the recommended motion command.

        Parameters
        ----------
        obstacles : list of ((cx, cy), depth_m)
            Each entry is the centroid pixel coordinate and estimated depth of
            a tracked object that should be treated as an obstacle.

        Returns
        -------
        str
            One of ``CMD_FORWARD``, ``CMD_SLOW``, ``CMD_STOP``,
            ``CMD_TURN_LEFT``, ``CMD_TURN_RIGHT``.
        """
        if not obstacles:
            self._last_command = self.CMD_FORWARD
            return self.CMD_FORWARD

        min_depth = min(d for _, d in obstacles)

        if min_depth <= self.stop_distance:
            cmd = self._evasion_direction(obstacles)
            log.warning(
                "Obstacle at %.2f m (≤ stop distance %.2f m) → %s",
                min_depth,
                self.stop_distance,
                cmd,
            )
            self._last_command = cmd
            return cmd

        if min_depth <= self.warn_distance:
            log.info(
                "Obstacle at %.2f m (warn zone) → slow",
                min_depth,
            )
            self._last_command = self.CMD_SLOW
            return self.CMD_SLOW

        self._last_command = self.CMD_FORWARD
        return self.CMD_FORWARD

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _evasion_direction(
        self,
        obstacles: List[Tuple[Tuple[int, int], float]],
    ) -> str:
        """Choose turn direction that moves away from the densest obstacle cluster."""
        mid = self.frame_width / 2.0
        left_weight = sum(
            1.0 / max(d, 0.01) for (cx, _), d in obstacles if cx < mid
        )
        right_weight = sum(
            1.0 / max(d, 0.01) for (cx, _), d in obstacles if cx >= mid
        )

        # Turn away from the heavier side
        if left_weight > right_weight:
            return self.CMD_TURN_RIGHT
        return self.CMD_TURN_LEFT

    @property
    def last_command(self) -> str:
        return self._last_command
