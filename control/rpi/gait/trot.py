"""
trot.py — IK-based trot gait for VIGIL-RQ.

Generates foot trajectories using Bezier-curve swing phases and
straight-line stance phases, then converts to joint angles via IK.

Diagonal pairs (FL+RR and FR+RL) move in anti-phase.

Usage:
    from gait.trot import TrotGaitIK
    trot = TrotGaitIK()
    angles = trot.tick(dt=0.02, vx=0.5, vy=0.0, yaw=0.0)
"""

import math
import numpy as np
from typing import Dict

from .ik_solver import IKSolver, LEG_ORIGINS, LEG_SIDE, L_HIP, L_THIGH, L_SHIN


# ══════════════════════════════════════════════════════════════════════════════
# TROT CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_STAND_HEIGHT = 0.20      # Body height (m)
TROT_FREQUENCY = 1.5             # Step frequency (Hz)
STEP_HEIGHT = 0.035              # Foot lift height during swing (m)
STRIDE_LENGTH = 0.06             # Max stride length per step (m)
DUTY_FACTOR = 0.5                # Fraction of cycle in stance (0.5 = symmetric trot)


class TrotGaitIK:
    """
    IK-based trot gait generator.

    Produces smooth foot trajectories for a diagonal trot gait:
    - FL & RR lift together (phase A)
    - FR & RL lift together (phase B, 180° offset)
    """

    def __init__(self, stand_height: float = DEFAULT_STAND_HEIGHT):
        self.ik = IKSolver()
        self.stand_height = stand_height
        self.time = 0.0

        # Compute default foot positions (standing)
        self.default_feet = {}
        for leg in ["fl", "fr", "rl", "rr"]:
            origin = LEG_ORIGINS[leg]
            side = LEG_SIDE[leg]
            self.default_feet[leg] = np.array([
                origin[0],                              # X: directly under hip
                origin[1] + side * L_HIP,               # Y: hip offset outward
                origin[2] - self.stand_height            # Z: foot on ground
            ])

    def _swing_trajectory(self, progress: float, stride_vec: np.ndarray) -> np.ndarray:
        """
        Compute swing foot offset using a parabolic arc.

        Args:
            progress: 0.0 (liftoff) to 1.0 (touchdown)
            stride_vec: [dx, dy, 0] total stride displacement

        Returns:
            np.array([x_offset, y_offset, z_lift])
        """
        # Forward/lateral: sinusoidal ramp
        forward_factor = math.sin(math.pi * progress)  # Smooth 0→1→0
        x_offset = stride_vec[0] * (progress - 0.5)
        y_offset = stride_vec[1] * (progress - 0.5)

        # Vertical: parabolic arc
        z_lift = STEP_HEIGHT * 4.0 * progress * (1.0 - progress)

        return np.array([x_offset, y_offset, z_lift])

    def _stance_offset(self, progress: float, stride_vec: np.ndarray) -> np.ndarray:
        """
        Compute stance foot offset (foot pushes backward on ground).

        Args:
            progress: 0.0 (touchdown) to 1.0 (liftoff)
            stride_vec: [dx, dy, 0] total stride displacement

        Returns:
            np.array([x_offset, y_offset, 0])
        """
        x_offset = stride_vec[0] * (0.5 - progress)
        y_offset = stride_vec[1] * (0.5 - progress)
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

        freq = TROT_FREQUENCY * max(0.3, speed)
        phase = (self.time * freq) % 1.0

        # Stride vector based on velocity commands
        stride = np.array([
            STRIDE_LENGTH * vx * speed,
            STRIDE_LENGTH * vy * speed,
            0.0
        ])

        # Diagonal pairing
        leg_phases = {
            "fl": phase,
            "rr": phase,
            "fr": (phase + 0.5) % 1.0,
            "rl": (phase + 0.5) % 1.0,
        }

        # Compute foot positions
        foot_positions = {}
        for leg, leg_phase in leg_phases.items():
            base = self.default_feet[leg].copy()

            # Yaw: differential stride for turning
            side = LEG_SIDE[leg]
            yaw_offset = np.array([0.0, 0.0, 0.0])
            if yaw != 0.0:
                # Outer legs stride more, inner legs less
                yaw_factor = 1.0 + side * yaw * 0.4
                stride_local = stride * yaw_factor
            else:
                stride_local = stride

            if abs(vx) < 0.01 and abs(vy) < 0.01 and abs(yaw) < 0.01:
                # Standing still — no trajectory offset
                foot_positions[leg] = base
            elif leg_phase < DUTY_FACTOR:
                # Swing phase
                progress = leg_phase / DUTY_FACTOR
                offset = self._swing_trajectory(progress, stride_local)
                foot_positions[leg] = base + offset
            else:
                # Stance phase
                progress = (leg_phase - DUTY_FACTOR) / (1.0 - DUTY_FACTOR)
                offset = self._stance_offset(progress, stride_local)
                foot_positions[leg] = base + offset

        # Solve IK for all legs
        return self.ik.solve_all_legs(foot_positions)

    def reset(self):
        """Reset gait phase to zero."""
        self.time = 0.0
