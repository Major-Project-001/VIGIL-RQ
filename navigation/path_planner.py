"""
Simple waypoint path planner for VIGIL-RQ.

Manages a list of waypoints (pixel or metric coordinates) and returns the
next target for the robot to navigate toward.

The planner does **not** compute full trajectories – that complexity is
deferred to future work.  It currently provides:

  * A FIFO waypoint queue.
  * Distance-to-waypoint check to advance to the next waypoint.
  * An idle/done state when all waypoints are consumed.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from utils import get_logger

log = get_logger(__name__)

Waypoint = Tuple[float, float]   # (x, y) in any consistent coordinate system


class PathPlanner:
    """FIFO waypoint planner.

    Parameters
    ----------
    arrival_radius : float
        Distance at which the robot is considered to have reached a waypoint.
    """

    def __init__(self, arrival_radius: float = 0.1) -> None:
        self.arrival_radius = arrival_radius
        self._waypoints: List[Waypoint] = []
        self._current_index: int = 0

    # ------------------------------------------------------------------
    # Waypoint management
    # ------------------------------------------------------------------

    def load(self, waypoints: List[Waypoint]) -> None:
        """Replace the current plan with a new list of waypoints."""
        self._waypoints = list(waypoints)
        self._current_index = 0
        log.info("PathPlanner: loaded %d waypoints.", len(self._waypoints))

    def append(self, waypoint: Waypoint) -> None:
        """Append a single waypoint to the end of the plan."""
        self._waypoints.append(waypoint)

    def clear(self) -> None:
        """Remove all waypoints and reset the plan."""
        self._waypoints.clear()
        self._current_index = 0

    # ------------------------------------------------------------------
    # Navigation queries
    # ------------------------------------------------------------------

    @property
    def current_waypoint(self) -> Optional[Waypoint]:
        """Return the active waypoint, or *None* if the plan is complete."""
        if self._current_index < len(self._waypoints):
            return self._waypoints[self._current_index]
        return None

    @property
    def is_done(self) -> bool:
        """True when all waypoints have been reached."""
        return self._current_index >= len(self._waypoints)

    def update(self, position: Waypoint) -> Optional[Waypoint]:
        """Advance the plan if *position* is close enough to the current waypoint.

        Parameters
        ----------
        position : (x, y)
            Current robot position in the same coordinate system as the
            waypoints.

        Returns
        -------
        (x, y) | None
            The next (or current) waypoint to head toward, or *None* if done.
        """
        if self.is_done:
            return None

        wp = self._waypoints[self._current_index]
        dist = math.sqrt((position[0] - wp[0]) ** 2 + (position[1] - wp[1]) ** 2)

        if dist <= self.arrival_radius:
            log.info(
                "PathPlanner: reached waypoint %d/%d (%.2f m from target).",
                self._current_index + 1,
                len(self._waypoints),
                dist,
            )
            self._current_index += 1

        return self.current_waypoint

    def bearing_to_current(self, position: Waypoint) -> Optional[float]:
        """Return the bearing (radians, 0 = east, CCW positive) to the current waypoint."""
        wp = self.current_waypoint
        if wp is None:
            return None
        dx = wp[0] - position[0]
        dy = wp[1] - position[1]
        return math.atan2(dy, dx)
