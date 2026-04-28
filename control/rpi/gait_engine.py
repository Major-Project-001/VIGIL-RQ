"""
gait_engine.py — Gait presets and dynamic gait generator for VIGIL-RQ.

Converts high-level commands (walk, run, sit, stand, rest) into per-joint
angle values. Dynamic gaits (walk/run) compute angles based on elapsed time
using sine-wave interpolation with diagonal leg pairing (trot gait).

The output is a dict of {joint_name: angle_rad} ready to be sent to
spi_driver.set_joint_angles().

Usage:
    from gait_engine import GaitEngine
    engine = GaitEngine()
    engine.set_mode("walk", speed=1.0, direction=0.0)
    angles = engine.tick(dt=0.02)  # Call at 50 Hz
"""

import math
import time
from config import (
    LEGS, JOINTS,
    POSE_STAND, POSE_SIT, POSE_REST,
    WALK_FREQ_HZ, WALK_HIP_AMP, WALK_THIGH_AMP,
    WALK_THIGH_OFFSET, WALK_KNEE_AMP, WALK_KNEE_OFFSET,
    RUN_FREQ_HZ, RUN_HIP_AMP, RUN_THIGH_AMP,
    RUN_THIGH_OFFSET, RUN_KNEE_AMP, RUN_KNEE_OFFSET,
)


# ── Gait modes ──
MODE_STAND = "stand"
MODE_SIT = "sit"
MODE_REST = "rest"
MODE_WALK = "walk"
MODE_RUN = "run"
MODE_STOP = "stop"   # Emergency stop → neutral

STATIC_MODES = {MODE_STAND, MODE_SIT, MODE_REST, MODE_STOP}
DYNAMIC_MODES = {MODE_WALK, MODE_RUN}


class GaitEngine:
    """
    Manages robot gaits and computes joint angles over time.

    Call tick(dt) at a regular interval (e.g. 50 Hz) to get the current
    target joint angles. For static poses, tick() always returns the same
    angles. For dynamic gaits (walk/run), angles evolve over time.
    """

    def __init__(self):
        self._mode = MODE_STAND
        self._speed = 1.0          # Speed multiplier (0.0–2.0)
        self._direction = 0.0      # Turn direction: -1.0 (left) to +1.0 (right)
        self._gait_time = 0.0      # Accumulated time for dynamic gaits
        self._last_angles = dict(POSE_STAND)

        # Smooth transition tracking
        self._transitioning = False
        self._transition_start_angles = dict(POSE_STAND)
        self._transition_target_angles = dict(POSE_STAND)
        self._transition_elapsed = 0.0
        self._transition_duration = 0.5  # seconds

    @property
    def mode(self) -> str:
        """Current gait mode."""
        return self._mode

    @property
    def is_dynamic(self) -> bool:
        """Whether the current mode produces time-varying angles."""
        return self._mode in DYNAMIC_MODES

    def set_mode(self, mode: str, speed: float = 1.0, direction: float = 0.0):
        """
        Change the gait mode.

        Args:
            mode:      One of: "stand", "sit", "rest", "walk", "run", "stop"
            speed:     Speed multiplier for dynamic gaits (0.0–2.0)
            direction: Turn direction (-1.0 = hard left, +1.0 = hard right)
        """
        mode = mode.lower()
        if mode == self._mode and mode in STATIC_MODES:
            return  # Already in this static pose

        # Start smooth transition for static mode changes
        if mode in STATIC_MODES:
            self._transition_start_angles = dict(self._last_angles)
            self._transition_target_angles = self._get_static_pose(mode)
            self._transition_elapsed = 0.0
            self._transitioning = True

        self._mode = mode
        self._speed = max(0.0, min(2.0, speed))
        self._direction = max(-1.0, min(1.0, direction))

        if mode in DYNAMIC_MODES:
            self._gait_time = 0.0  # Reset gait phase
            self._transitioning = False

    def update_joystick(self, x: float, y: float, yaw: float = 0.0):
        """
        Update direction and speed from joystick input.

        Args:
            x: Left/right (-1.0 to +1.0)
            y: Forward/backward (-1.0 to +1.0, positive = forward)
            yaw: Turn rate from right stick (-1.0 to +1.0)
        """
        self._direction = max(-1.0, min(1.0, x + yaw))
        magnitude = math.sqrt(x * x + y * y)
        self._speed = max(0.0, min(2.0, magnitude))

    def tick(self, dt: float) -> dict:
        """
        Compute joint angles for the current time step.

        Args:
            dt: Time step in seconds (e.g. 0.02 for 50 Hz)

        Returns:
            dict of {joint_name: angle_rad} for all 12 joints
        """
        if self._transitioning:
            self._transition_elapsed += dt
            progress = min(1.0, self._transition_elapsed / self._transition_duration)
            # Smooth ease-in-out
            t = 0.5 * (1.0 - math.cos(math.pi * progress))
            angles = {}
            for joint in self._transition_target_angles:
                start = self._transition_start_angles.get(joint, 0.0)
                end = self._transition_target_angles[joint]
                angles[joint] = start + (end - start) * t
            if progress >= 1.0:
                self._transitioning = False
            self._last_angles = angles
            return angles

        if self._mode == MODE_WALK:
            angles = self._compute_trot(
                dt, WALK_FREQ_HZ, WALK_HIP_AMP, WALK_THIGH_AMP,
                WALK_THIGH_OFFSET, WALK_KNEE_AMP, WALK_KNEE_OFFSET
            )
        elif self._mode == MODE_RUN:
            angles = self._compute_trot(
                dt, RUN_FREQ_HZ, RUN_HIP_AMP, RUN_THIGH_AMP,
                RUN_THIGH_OFFSET, RUN_KNEE_AMP, RUN_KNEE_OFFSET
            )
        elif self._mode == MODE_SIT:
            angles = dict(POSE_SIT)
        elif self._mode == MODE_REST:
            angles = dict(POSE_REST)
        elif self._mode == MODE_STOP:
            angles = dict(POSE_STAND)  # Stop = go to neutral
        else:
            angles = dict(POSE_STAND)

        self._last_angles = angles
        return angles

    def _compute_trot(self, dt, freq, hip_amp, thigh_amp,
                      thigh_offset, knee_amp, knee_offset) -> dict:
        """
        Compute trot gait angles for the current time step.

        Trot gait: diagonal legs (FL+RR and FR+RL) move in sync,
        with 180° phase offset between the two pairs.

        Speed modulates frequency, direction modulates hip amplitude
        asymmetry between left and right sides.
        """
        self._gait_time += dt
        t = self._gait_time

        # Apply speed multiplier to frequency
        effective_freq = freq * self._speed
        phase = 2.0 * math.pi * effective_freq * t

        angles = {}

        # Diagonal pairs with phase offset
        leg_configs = [
            ("fl", 1.0, 0.0),           # FL: phase 0
            ("rr", 1.0, 0.0),           # RR: same phase (diagonal pair)
            ("fr", -1.0, math.pi),      # FR: 180° offset
            ("rl", -1.0, math.pi),      # RL: same as FR (diagonal pair)
        ]

        for leg, sign, phase_offset in leg_configs:
            ph = phase + phase_offset

            # Direction modulation: asymmetric hip for turning
            # direction > 0 → turn right → left legs push more
            dir_mod = 1.0
            if "l" in leg:  # Left leg
                dir_mod = 1.0 + self._direction * 0.3
            else:           # Right leg
                dir_mod = 1.0 - self._direction * 0.3

            # Hip: gentle sideways sway
            angles[f"{leg}_hip"] = hip_amp * math.sin(ph * 0.5) * sign

            # Thigh: forward/back swing (modulated by direction for turning)
            angles[f"{leg}_thigh"] = (
                thigh_offset + thigh_amp * math.sin(ph) * dir_mod
            )

            # Knee: lift during forward swing, extend during backward
            knee_phase = math.sin(ph)
            knee_lift = max(0.0, knee_phase)  # Only lift, don't push down
            angles[f"{leg}_knee"] = knee_offset - knee_amp * knee_lift

        return angles

    def _get_static_pose(self, mode: str) -> dict:
        """Get the target angles for a static pose mode."""
        if mode == MODE_SIT:
            return dict(POSE_SIT)
        elif mode == MODE_REST:
            return dict(POSE_REST)
        elif mode == MODE_STOP:
            return dict(POSE_STAND)
        else:
            return dict(POSE_STAND)

    def emergency_stop(self):
        """Immediately set all joints to neutral (stand)."""
        self._mode = MODE_STOP
        self._transitioning = False
        self._gait_time = 0.0
        self._last_angles = dict(POSE_STAND)
        return dict(POSE_STAND)
