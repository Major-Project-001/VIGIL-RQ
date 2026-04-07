"""
Gait engine for VIGIL-RQ.

Implements forward kinematics and two gait patterns:
  * **trot** – diagonal pairs of legs move together (FL+RR, FR+RL).
  * **walk** – one leg at a time in the sequence FL → RR → FR → RL.
  * **crawl** – like walk but with a lower body height and shorter step.

Kinematics
----------
Each leg is a 3-DOF serial chain (coxa–femur–tibia).  The foot position
relative to the leg origin is computed using the standard Denavit-Hartenberg
analytic solution for a planar 2-link arm (femur + tibia) combined with a
lateral coxa rotation.

The engine produces per-servo angle commands that are forwarded to
``ServoController``.
"""

from __future__ import annotations

import math
import time
from typing import Dict, Tuple

import config
from utils import get_logger
from .servo import ServoController

log = get_logger(__name__)

# Leg indices and their nominal foot positions relative to body center (metres)
_LEG_ORIGINS: Dict[str, Tuple[float, float]] = {
    "FL": ( config.LINK_COXA, -config.LINK_COXA),
    "FR": ( config.LINK_COXA,  config.LINK_COXA),
    "RL": (-config.LINK_COXA, -config.LINK_COXA),
    "RR": (-config.LINK_COXA,  config.LINK_COXA),
}

# Trot gait: diagonal pairs
_TROT_PAIRS = [("FL", "RR"), ("FR", "RL")]

# Walk/crawl gait: one leg at a time
_WALK_SEQUENCE = ["FL", "RR", "FR", "RL"]


class GaitEngine:
    """Generates servo angles for different gait patterns.

    Parameters
    ----------
    servo : ServoController
        Low-level servo driver.
    body_height : float
        Default height of the body above the ground (metres).
    step_height : float
        How high to lift each foot during swing phase (metres).
    step_length : float
        Length of each stride in the forward direction (metres).
    cycle_period : float
        Duration of a full gait cycle in seconds.
    """

    def __init__(
        self,
        servo: ServoController,
        body_height: float = config.DEFAULT_BODY_HEIGHT,
        step_height: float = config.GAIT_STEP_HEIGHT,
        step_length: float = config.GAIT_STEP_LENGTH,
        cycle_period: float = config.GAIT_CYCLE_PERIOD,
    ) -> None:
        self._servo = servo
        self.body_height = body_height
        self.step_height = step_height
        self.step_length = step_length
        self.cycle_period = cycle_period
        self._running = False

    # ------------------------------------------------------------------
    # Inverse kinematics (2-DOF planar – femur + tibia)
    # ------------------------------------------------------------------

    @staticmethod
    def _ik_2dof(
        reach: float,
        depth: float,
        l1: float = config.LINK_FEMUR,
        l2: float = config.LINK_TIBIA,
    ) -> Tuple[float, float]:
        """Return (femur_angle, tibia_angle) in degrees.

        *reach* is the horizontal distance from the hip pivot to the foot;
        *depth* is the vertical drop (positive = downward).

        Uses the geometric (elbow-down) solution.
        Raises ``ValueError`` if the target is unreachable.
        """
        d = math.sqrt(reach ** 2 + depth ** 2)
        if d > l1 + l2 or d < abs(l1 - l2):
            raise ValueError(
                f"IK target unreachable: reach={reach:.3f}, depth={depth:.3f}, d={d:.3f}"
            )

        cos_knee = (l1 ** 2 + l2 ** 2 - d ** 2) / (2 * l1 * l2)
        cos_knee = max(-1.0, min(1.0, cos_knee))
        tibia_rad = math.acos(cos_knee)

        alpha = math.atan2(depth, reach)
        cos_beta = (l1 ** 2 + d ** 2 - l2 ** 2) / (2 * l1 * d)
        cos_beta = max(-1.0, min(1.0, cos_beta))
        beta = math.acos(cos_beta)
        femur_rad = alpha - beta

        return math.degrees(femur_rad), math.degrees(tibia_rad)

    def _set_leg(
        self,
        leg: str,
        coxa_deg: float,
        femur_deg: float,
        tibia_deg: float,
    ) -> None:
        """Send angles to one leg's three servos."""
        channels = config.SERVO_CHANNELS[leg]
        self._servo.set_angle(channels["hip"],   coxa_deg  + config.SERVO_NEUTRAL_ANGLE)
        self._servo.set_angle(channels["thigh"], femur_deg + config.SERVO_NEUTRAL_ANGLE)
        self._servo.set_angle(channels["calf"],  tibia_deg + config.SERVO_NEUTRAL_ANGLE)

    def _plant_leg(self, leg: str, x_offset: float = 0.0) -> None:
        """Put *leg* in its default stance with optional forward *x_offset*."""
        reach = config.LINK_COXA + x_offset
        depth = self.body_height
        try:
            femur, tibia = self._ik_2dof(reach, depth)
        except ValueError as exc:
            log.warning("IK plant: %s", exc)
            femur, tibia = 30.0, -60.0  # safe fallback
        self._set_leg(leg, 0.0, femur, tibia)

    def _lift_leg(self, leg: str, x_offset: float = 0.0) -> None:
        """Swing *leg* forward by *x_offset* and lift by ``step_height``."""
        reach = config.LINK_COXA + x_offset
        depth = self.body_height - self.step_height
        try:
            femur, tibia = self._ik_2dof(reach, depth)
        except ValueError as exc:
            log.warning("IK lift: %s", exc)
            femur, tibia = 20.0, -50.0
        self._set_leg(leg, 0.0, femur, tibia)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def stand(self) -> None:
        """Place the robot in its default standing pose."""
        for leg in config.SERVO_CHANNELS:
            self._plant_leg(leg)
        log.info("GaitEngine: standing pose.")

    def step_trot(self, forward_speed: float = 1.0) -> None:
        """Execute one trot cycle (two half-cycles)."""
        half = self.cycle_period / 2.0
        stride = self.step_length * forward_speed

        for swing_pair, stance_pair in [
            (_TROT_PAIRS[0], _TROT_PAIRS[1]),
            (_TROT_PAIRS[1], _TROT_PAIRS[0]),
        ]:
            # Lift swing pair
            for leg in swing_pair:
                self._lift_leg(leg, stride)
            # Keep stance pair planted
            for leg in stance_pair:
                self._plant_leg(leg)
            time.sleep(half)

    def step_walk(self, forward_speed: float = 1.0) -> None:
        """Execute one walk cycle (four steps, one per leg)."""
        quarter = self.cycle_period / 4.0
        stride = self.step_length * forward_speed

        for i, leg in enumerate(_WALK_SEQUENCE):
            self._lift_leg(leg, stride)
            for other in _WALK_SEQUENCE:
                if other != leg:
                    self._plant_leg(other)
            time.sleep(quarter)

    def step_crawl(self, forward_speed: float = 0.5) -> None:
        """Slow, stable crawl gait – like walk but lower body height."""
        saved = self.body_height
        self.body_height = max(0.05, self.body_height * 0.75)
        self.step_walk(forward_speed)
        self.body_height = saved

    def run_gait(
        self,
        gait: str = config.GAIT_DEFAULT,
        forward_speed: float = 1.0,
        steps: int = 1,
    ) -> None:
        """Execute *steps* gait cycles.

        Parameters
        ----------
        gait : str
            ``"trot"``, ``"walk"``, or ``"crawl"``.
        forward_speed : float
            Normalised speed [0, 1].
        steps : int
            Number of gait cycles to execute.
        """
        stepper = {
            "trot":  self.step_trot,
            "walk":  self.step_walk,
            "crawl": self.step_crawl,
        }.get(gait)

        if stepper is None:
            log.warning("Unknown gait '%s' – defaulting to trot.", gait)
            stepper = self.step_trot

        for _ in range(steps):
            stepper(forward_speed)
