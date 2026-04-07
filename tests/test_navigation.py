"""
Unit tests for navigation modules:
  - ObstacleAvoider
  - PathPlanner
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from navigation.obstacle_avoidance import ObstacleAvoider
from navigation.path_planner import PathPlanner


# ──────────────────────────────────────────────────────────────────────────────
# ObstacleAvoider
# ──────────────────────────────────────────────────────────────────────────────

class TestObstacleAvoider:
    def _avoider(self):
        return ObstacleAvoider(stop_distance=0.3, warn_distance=0.6, frame_width=640)

    def test_no_obstacles_gives_forward(self):
        av = self._avoider()
        assert av.evaluate([]) == ObstacleAvoider.CMD_FORWARD

    def test_obstacle_in_warn_zone_gives_slow(self):
        av = self._avoider()
        cmd = av.evaluate([((320, 240), 0.5)])
        assert cmd == ObstacleAvoider.CMD_SLOW

    def test_obstacle_beyond_warn_zone_gives_forward(self):
        av = self._avoider()
        cmd = av.evaluate([((320, 240), 1.0)])
        assert cmd == ObstacleAvoider.CMD_FORWARD

    def test_obstacle_in_stop_zone_gives_turn(self):
        av = self._avoider()
        cmd = av.evaluate([((320, 240), 0.2)])
        assert cmd in (ObstacleAvoider.CMD_TURN_LEFT, ObstacleAvoider.CMD_TURN_RIGHT)

    def test_evasion_turns_away_from_obstacle_on_left(self):
        """Obstacle on left side → turn right."""
        av = self._avoider()
        # cx=100 is on the left half of a 640-wide frame
        cmd = av.evaluate([((100, 240), 0.1)])
        assert cmd == ObstacleAvoider.CMD_TURN_RIGHT

    def test_evasion_turns_away_from_obstacle_on_right(self):
        """Obstacle on right side → turn left."""
        av = self._avoider()
        # cx=540 is on the right half of a 640-wide frame
        cmd = av.evaluate([((540, 240), 0.1)])
        assert cmd == ObstacleAvoider.CMD_TURN_LEFT

    def test_last_command_updated(self):
        av = self._avoider()
        av.evaluate([((320, 240), 0.5)])
        assert av.last_command == ObstacleAvoider.CMD_SLOW

    def test_multiple_obstacles_closest_determines_zone(self):
        av = self._avoider()
        # One far, one close
        cmd = av.evaluate([((320, 240), 1.5), ((100, 240), 0.15)])
        assert cmd in (ObstacleAvoider.CMD_TURN_LEFT, ObstacleAvoider.CMD_TURN_RIGHT)


# ──────────────────────────────────────────────────────────────────────────────
# PathPlanner
# ──────────────────────────────────────────────────────────────────────────────

class TestPathPlanner:
    def test_empty_plan_is_done(self):
        pp = PathPlanner()
        assert pp.is_done

    def test_load_waypoints(self):
        pp = PathPlanner()
        pp.load([(1.0, 0.0), (2.0, 0.0)])
        assert not pp.is_done
        assert pp.current_waypoint == (1.0, 0.0)

    def test_advance_to_next_waypoint_on_arrival(self):
        pp = PathPlanner(arrival_radius=0.1)
        pp.load([(1.0, 0.0), (2.0, 0.0)])
        pp.update((1.0, 0.0))   # exactly at first waypoint
        assert pp.current_waypoint == (2.0, 0.0)

    def test_no_advance_when_far_from_waypoint(self):
        pp = PathPlanner(arrival_radius=0.1)
        pp.load([(1.0, 0.0)])
        pp.update((0.0, 0.0))
        assert pp.current_waypoint == (1.0, 0.0)

    def test_plan_done_after_last_waypoint(self):
        pp = PathPlanner(arrival_radius=0.1)
        pp.load([(1.0, 0.0)])
        pp.update((1.0, 0.0))
        assert pp.is_done
        assert pp.current_waypoint is None

    def test_append_waypoint(self):
        pp = PathPlanner()
        pp.append((3.0, 4.0))
        assert not pp.is_done
        assert pp.current_waypoint == (3.0, 4.0)

    def test_clear_resets_plan(self):
        pp = PathPlanner()
        pp.load([(1.0, 0.0), (2.0, 0.0)])
        pp.clear()
        assert pp.is_done

    def test_bearing_to_current_east(self):
        pp = PathPlanner()
        pp.load([(1.0, 0.0)])
        bearing = pp.bearing_to_current((0.0, 0.0))
        assert bearing == pytest.approx(0.0, abs=1e-9)

    def test_bearing_to_current_north(self):
        pp = PathPlanner()
        pp.load([(0.0, 1.0)])
        bearing = pp.bearing_to_current((0.0, 0.0))
        assert bearing == pytest.approx(math.pi / 2, abs=1e-9)

    def test_bearing_returns_none_when_done(self):
        pp = PathPlanner()
        assert pp.bearing_to_current((0.0, 0.0)) is None

    def test_update_returns_none_when_done(self):
        pp = PathPlanner(arrival_radius=0.1)
        pp.load([(0.0, 0.0)])
        pp.update((0.0, 0.0))  # advance past it
        result = pp.update((0.0, 0.0))
        assert result is None
