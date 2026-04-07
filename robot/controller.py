"""
High-level robot controller for VIGIL-RQ.

Bridges the vision pipeline with the gait engine and obstacle avoidance,
providing simple action commands:

  * ``move_forward()``
  * ``turn_left()`` / ``turn_right()``
  * ``stop()``
  * ``track_target(track_id)`` – visual servoing toward a tracked object

The controller owns the PID controller used for heading correction.
"""

from __future__ import annotations

import time
from typing import Optional

import config
from utils import get_logger, PIDController
from .servo import ServoController
from .gait import GaitEngine

log = get_logger(__name__)


class RobotController:
    """Coordinates the servo driver, gait engine, and heading PID.

    Parameters
    ----------
    simulation : bool
        When *True* the servo driver operates in simulation mode.
    """

    def __init__(self, simulation: bool = False) -> None:
        self._servo = ServoController(simulation=simulation)
        self._gait = GaitEngine(servo=self._servo)

        self._heading_pid = PIDController(
            kp=config.PID_KP,
            ki=config.PID_KI,
            kd=config.PID_KD,
            output_limit=config.PID_OUTPUT_LIMIT,
        )

        self._last_action: str = "idle"
        self._forward_speed: float = config.ROBOT_FORWARD_SPEED
        self._turn_speed: float = config.ROBOT_TURN_SPEED

        # Stand up on init
        self._gait.stand()
        log.info("RobotController initialised (simulation=%s).", simulation)

    # ------------------------------------------------------------------
    # Basic motion commands
    # ------------------------------------------------------------------

    def move_forward(self, steps: int = 1, gait: Optional[str] = None) -> None:
        """Walk forward for *steps* gait cycles."""
        g = gait or config.GAIT_DEFAULT
        log.info("Moving forward – gait=%s, steps=%d", g, steps)
        self._last_action = "forward"
        self._gait.run_gait(g, forward_speed=self._forward_speed, steps=steps)

    def turn_left(self, steps: int = 1) -> None:
        """Turn the robot left."""
        log.info("Turning left – steps=%d", steps)
        self._last_action = "turn_left"
        # Reduce right-side stride and increase left-side to pivot
        saved = self._gait.step_length
        self._gait.step_length = saved * self._turn_speed
        self._gait.run_gait("walk", forward_speed=self._turn_speed, steps=steps)
        self._gait.step_length = saved

    def turn_right(self, steps: int = 1) -> None:
        """Turn the robot right."""
        log.info("Turning right – steps=%d", steps)
        self._last_action = "turn_right"
        saved = self._gait.step_length
        self._gait.step_length = saved * self._turn_speed
        self._gait.run_gait("walk", forward_speed=self._turn_speed, steps=steps)
        self._gait.step_length = saved

    def stop(self) -> None:
        """Halt motion and return all legs to the standing pose."""
        log.info("Stopping.")
        self._last_action = "stop"
        self._gait.stand()

    # ------------------------------------------------------------------
    # Visual servoing
    # ------------------------------------------------------------------

    def track_target(
        self,
        cx: float,
        frame_width: int,
        depth_m: Optional[float] = None,
    ) -> None:
        """Steer toward a detected target centerd at horizontal pixel *cx*.

        Parameters
        ----------
        cx : float
            Horizontal pixel position of the target center.
        frame_width : int
            Full width of the camera frame in pixels.
        depth_m : float | None
            Estimated distance to the target in metres.
            If the target is closer than ``OBSTACLE_STOP_DISTANCE`` the
            robot stops rather than advancing.
        """
        # Normalise horizontal error to [-1, +1]
        error = (cx - frame_width / 2.0) / (frame_width / 2.0)
        correction = self._heading_pid.update(setpoint=0.0, measurement=error)

        if depth_m is not None and depth_m < config.OBSTACLE_STOP_DISTANCE:
            log.info("Target within stop distance (%.2f m) – holding position.", depth_m)
            self.stop()
            return

        if abs(correction) > 0.15:
            if correction > 0:
                self.turn_right(steps=1)
            else:
                self.turn_left(steps=1)
        else:
            speed = self._forward_speed
            if depth_m is not None and depth_m < config.OBSTACLE_WARN_DISTANCE:
                speed *= 0.5
            self._gait.run_gait(config.GAIT_DEFAULT, forward_speed=speed, steps=1)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def shutdown(self) -> None:
        """Safely park all servos and close the serial port."""
        self.stop()
        self._servo.set_all_neutral()
        self._servo.close()
        log.info("RobotController shut down.")

    def __enter__(self) -> "RobotController":
        return self

    def __exit__(self, *_) -> None:
        self.shutdown()
