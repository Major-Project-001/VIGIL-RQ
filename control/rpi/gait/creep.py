"""
creep.py — IK-based creep (wave) gait for VIGIL-RQ.

A statically-stable gait where only one leg lifts at a time,
keeping the center of gravity within the support triangle.

Leg sequence: RL → FL → RR → FR (or configurable)
Each leg spends 75% of the cycle on the ground.

Usage:
    from gait.creep import CreepGaitIK
    creep = CreepGaitIK()
    angles = creep.tick(dt=0.02, vx=0.3, vy=0.0, yaw=0.0)
"""

import math
import numpy as np
from typing import Dict

from .ik_solver import IKSolver, LEG_ORIGINS, LEG_SIDE, L_HIP


# ══════════════════════════════════════════════════════════════════════════════
# CREEP CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_STAND_HEIGHT = 0.18      # Slightly lower for stability
CREEP_FREQUENCY = 0.5            # Full cycle frequency (Hz) — slow and stable
STEP_HEIGHT = 0.04               # Foot lift height (m) — higher for clearance
STRIDE_LENGTH = 0.04             # Max stride per step (m) — conservative
DUTY_FACTOR = 0.75               # 75% stance — only 1 leg off ground at a time

# Leg lift order: one at a time, maximizing support polygon
# Standard wave gait: RL → FL → RR → FR
LEG_ORDER = ["rl", "fl", "rr", "fr"]
LEG_PHASE_OFFSETS = {
    "rl": 0.00,     # Phase 0.00 – 0.25: RL swings
    "fl": 0.25,     # Phase 0.25 – 0.50: FL swings
    "rr": 0.50,     # Phase 0.50 – 0.75: RR swings
    "fr": 0.75,     # Phase 0.75 – 1.00: FR swings
}


class CreepGaitIK:
    """
    IK-based creep (wave) gait generator.

    Only one leg lifts at a time → always 3-point support.
    Very stable but slow. Ideal for rough terrain or heavy payloads.
    """

    def __init__(self, stand_height: float = DEFAULT_STAND_HEIGHT):
        self.ik = IKSolver()
        self.stand_height = stand_height
        self.time = 0.0

        # Default foot positions (standing)
        self.default_feet = {}
        for leg in ["fl", "fr", "rl", "rr"]:
            origin = LEG_ORIGINS[leg]
            side = LEG_SIDE[leg]
            self.default_feet[leg] = np.array([
                origin[0],
                origin[1] + side * L_HIP,
                origin[2] - self.stand_height
            ])

    def _swing_trajectory(self, progress: float, stride_vec: np.ndarray) -> np.ndarray:
        """
        Swing foot trajectory with trapezoidal lift profile.

        Lifts quickly, holds height during forward motion, then lands.
        """
        # Forward: linear progression
        x_offset = stride_vec[0] * (progress - 0.5)
        y_offset = stride_vec[1] * (progress - 0.5)

        # Vertical: trapezoidal (flat top for clearance)
        if progress < 0.2:
            z_lift = STEP_HEIGHT * (progress / 0.2)
        elif progress > 0.8:
            z_lift = STEP_HEIGHT * ((1.0 - progress) / 0.2)
        else:
            z_lift = STEP_HEIGHT

        return np.array([x_offset, y_offset, z_lift])

    def _stance_offset(self, progress: float, stride_vec: np.ndarray) -> np.ndarray:
        """
        Stance phase: foot pushes backward slowly (3× longer than swing).
        """
        # Foot moves backward during stance (pushing body forward)
        x_offset = stride_vec[0] * (0.5 - progress) * (1.0 - DUTY_FACTOR) / DUTY_FACTOR
        y_offset = stride_vec[1] * (0.5 - progress) * (1.0 - DUTY_FACTOR) / DUTY_FACTOR
        return np.array([x_offset, y_offset, 0.0])

    def tick(self, dt: float, vx: float = 0.0, vy: float = 0.0,
             yaw: float = 0.0, speed: float = 1.0) -> Dict[str, float]:
        """
        Compute all 12 joint angles for one timestep.

        Args:
            dt: Time step (seconds)
            vx: Forward velocity command (-1.0 to 1.0)
            vy: Lateral velocity command (-1.0 to 1.0)
            yaw: Yaw rate command (-1.0 to 1.0)
            speed: Speed multiplier (0.0 to 2.0)

        Returns:
            Dict of {joint_name: angle_rad} for all 12 joints
        """
        self.time += dt

        freq = CREEP_FREQUENCY * max(0.2, speed)
        global_phase = (self.time * freq) % 1.0

        stride = np.array([
            STRIDE_LENGTH * vx * speed,
            STRIDE_LENGTH * vy * speed,
            0.0
        ])

        swing_duration = 1.0 - DUTY_FACTOR  # 0.25 of cycle per leg

        foot_positions = {}
        for leg in ["fl", "fr", "rl", "rr"]:
            base = self.default_feet[leg].copy()

            if abs(vx) < 0.01 and abs(vy) < 0.01 and abs(yaw) < 0.01:
                foot_positions[leg] = base
                continue

            # Compute this leg's phase relative to its offset
            leg_phase = (global_phase - LEG_PHASE_OFFSETS[leg]) % 1.0

            # Yaw differential
            side = LEG_SIDE[leg]
            if yaw != 0.0:
                yaw_factor = 1.0 + side * yaw * 0.3
                stride_local = stride * yaw_factor
            else:
                stride_local = stride

            if leg_phase < swing_duration:
                # This leg is swinging
                progress = leg_phase / swing_duration
                offset = self._swing_trajectory(progress, stride_local)
                foot_positions[leg] = base + offset
            else:
                # This leg is in stance
                stance_phase = (leg_phase - swing_duration) / DUTY_FACTOR
                offset = self._stance_offset(stance_phase, stride_local)
                foot_positions[leg] = base + offset

        return self.ik.solve_all_legs(foot_positions)

    def reset(self):
        """Reset gait phase to zero."""
        self.time = 0.0
