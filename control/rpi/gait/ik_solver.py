"""
ik_solver.py — Inverse Kinematics for VIGIL-RQ Quadruped

Computes joint angles (hip, thigh, knee) from desired foot position
relative to the hip joint origin. Uses analytical geometric IK for
a 3-DOF leg with hip offset, thigh, and shin links.

Leg Geometry (from URDF):
    Hip offset (L1):  ~68.9 mm  (lateral from body to thigh pivot)
    Thigh (L2):      ~114.4 mm  (hip pivot to knee pivot)
    Shin (L3):       ~139.8 mm  (knee pivot to foot)

Coordinate Frame (per leg, hip-centered):
    X = forward (+front of robot)
    Y = lateral (+left for left legs, +right for right legs)
    Z = vertical (+up)

Usage:
    from ik_solver import IKSolver
    ik = IKSolver()
    angles = ik.solve(x=0.0, y=0.055, z=-0.20)
    # Returns (hip_rad, thigh_rad, knee_rad)
"""

import math
import numpy as np
from typing import Tuple, Optional, Dict

# ══════════════════════════════════════════════════════════════════════════════
# LEG DIMENSIONS (meters, extracted from URDF joint origins)
# ══════════════════════════════════════════════════════════════════════════════

# Hip offset: distance from hip rotation axis to thigh pivot (lateral)
# From URDF: fl_thigh_joint origin xyz="0.0689 -0.0165 -0.0014"
L_HIP = 0.0689       # ~68.9 mm

# Thigh length: distance from thigh pivot to knee pivot
# From URDF: fl_knee_joint origin xyz="0.0172 0.0075 -0.1144"
L_THIGH = 0.1144     # ~114.4 mm

# Shin length: distance from knee pivot to foot
# From URDF: fl_foot_joint origin xyz="0.0162 -0.0557 -0.1398"
L_SHIN = 0.1398      # ~139.8 mm

# Body half-dimensions (for computing foot positions in body frame)
# From URDF: fl_hip_joint origin xyz="0.0412 0.1660 -0.1168"
BODY_HALF_LENGTH = 0.0412    # X: front/back from body center to hip
BODY_HALF_WIDTH = 0.1660     # Y: left/right from body center to hip
BODY_HIP_Z_OFFSET = 0.1168  # Z: body center to hip joint (downward)

# Leg positions relative to body center
LEG_ORIGINS = {
    "fl": np.array([ BODY_HALF_LENGTH,  BODY_HALF_WIDTH, -BODY_HIP_Z_OFFSET]),
    "fr": np.array([ BODY_HALF_LENGTH, -BODY_HALF_WIDTH, -BODY_HIP_Z_OFFSET]),
    "rl": np.array([-BODY_HALF_LENGTH,  BODY_HALF_WIDTH, -BODY_HIP_Z_OFFSET]),
    "rr": np.array([-BODY_HALF_LENGTH, -BODY_HALF_WIDTH, -BODY_HIP_Z_OFFSET]),
}

# Side sign: +1 for left legs (Y+), -1 for right legs (Y-)
LEG_SIDE = {"fl": 1, "fr": -1, "rl": 1, "rr": -1}


class IKSolver:
    """
    Analytical inverse kinematics for a single 3-DOF quadruped leg.

    Given a desired foot position (x, y, z) relative to the hip joint,
    computes the three joint angles: hip, thigh, knee.
    """

    def __init__(self, l_hip: float = L_HIP, l_thigh: float = L_THIGH,
                 l_shin: float = L_SHIN):
        self.l_hip = l_hip
        self.l_thigh = l_thigh
        self.l_shin = l_shin

    def solve(self, x: float, y: float, z: float,
              side: int = 1) -> Optional[Tuple[float, float, float]]:
        """
        Solve IK for a single leg.

        Args:
            x: Forward/backward position (m), + = forward
            y: Lateral position (m), + = outward from body
            z: Vertical position (m), + = up (foot is negative)
            side: +1 for left legs, -1 for right legs

        Returns:
            Tuple of (hip_angle, thigh_angle, knee_angle) in radians
            or None if the position is unreachable.
        """
        # ── Step 1: Hip angle ──
        # The hip rotates in the Y-Z plane to swing the leg laterally
        # Foot position projected onto the lateral plane
        y_eff = y * side  # Normalize direction
        d_yz = math.sqrt(y_eff ** 2 + z ** 2)

        # Check reachability for hip
        if d_yz < self.l_hip:
            return None  # Too close to body

        hip_angle = math.atan2(y_eff, -z) - math.atan2(
            self.l_hip, math.sqrt(d_yz ** 2 - self.l_hip ** 2)
        )

        # ── Step 2: Project to the thigh-knee plane ──
        # After removing the hip offset, work in the sagittal plane
        d_foot = math.sqrt(d_yz ** 2 - self.l_hip ** 2)  # Distance in knee plane
        r = math.sqrt(x ** 2 + d_foot ** 2)               # Total reach

        # Check reachability for thigh-knee
        max_reach = self.l_thigh + self.l_shin
        min_reach = abs(self.l_thigh - self.l_shin)
        if r > max_reach or r < min_reach:
            # Clamp to nearest reachable point
            r = max(min_reach + 0.001, min(max_reach - 0.001, r))

        # ── Step 3: Knee angle (law of cosines) ──
        cos_knee = (self.l_thigh ** 2 + self.l_shin ** 2 - r ** 2) / \
                   (2 * self.l_thigh * self.l_shin)
        cos_knee = max(-1.0, min(1.0, cos_knee))  # Numerical safety
        knee_angle = -(math.pi - math.acos(cos_knee))  # Negative = bent backward

        # ── Step 4: Thigh angle ──
        alpha = math.atan2(x, d_foot)  # Angle from vertical to foot
        cos_beta = (self.l_thigh ** 2 + r ** 2 - self.l_shin ** 2) / \
                   (2 * self.l_thigh * r)
        cos_beta = max(-1.0, min(1.0, cos_beta))
        beta = math.acos(cos_beta)
        thigh_angle = alpha + beta  # Combine angles

        return (hip_angle, thigh_angle, knee_angle)

    def solve_leg(self, leg: str, foot_pos: np.ndarray) -> Optional[Dict[str, float]]:
        """
        Solve IK for a named leg given foot position in body frame.

        Args:
            leg: One of "fl", "fr", "rl", "rr"
            foot_pos: np.array([x, y, z]) in body frame (meters)

        Returns:
            Dict of {joint_name: angle_rad} or None if unreachable
        """
        origin = LEG_ORIGINS[leg]
        side = LEG_SIDE[leg]

        # Convert foot position to hip-relative coordinates
        local = foot_pos - origin

        result = self.solve(local[0], local[1] * side, local[2], side=1)
        if result is None:
            return None

        hip_rad, thigh_rad, knee_rad = result
        return {
            f"{leg}_hip": hip_rad * side,
            f"{leg}_thigh": thigh_rad,
            f"{leg}_knee": knee_rad,
        }

    def solve_all_legs(self, foot_positions: Dict[str, np.ndarray]) -> Dict[str, float]:
        """
        Solve IK for all four legs.

        Args:
            foot_positions: Dict of {"fl": [x,y,z], "fr": [x,y,z], ...}
                           in body frame (meters)

        Returns:
            Dict of all 12 joint angles {joint_name: angle_rad}
        """
        all_angles = {}
        for leg, pos in foot_positions.items():
            angles = self.solve_leg(leg, np.array(pos))
            if angles:
                all_angles.update(angles)
            else:
                # Fallback to zero if unreachable
                for joint in ["hip", "thigh", "knee"]:
                    all_angles[f"{leg}_{joint}"] = 0.0
        return all_angles

    def get_default_stance(self, height: float = 0.20) -> Dict[str, np.ndarray]:
        """
        Compute default standing foot positions at a given body height.

        Args:
            height: Body height above ground (meters)

        Returns:
            Dict of {leg_name: foot_position_in_body_frame}
        """
        stance = {}
        for leg in ["fl", "fr", "rl", "rr"]:
            origin = LEG_ORIGINS[leg]
            side = LEG_SIDE[leg]
            stance[leg] = np.array([
                origin[0],                                  # X: directly under hip
                origin[1] + side * self.l_hip,              # Y: hip offset outward
                -(height - BODY_HIP_Z_OFFSET + origin[2])   # Z: foot on ground
            ])
        return stance


# ══════════════════════════════════════════════════════════════════════════════
# FORWARD KINEMATICS (for verification / visualization)
# ══════════════════════════════════════════════════════════════════════════════

def forward_kinematics(hip_angle: float, thigh_angle: float, knee_angle: float,
                       l_hip: float = L_HIP, l_thigh: float = L_THIGH,
                       l_shin: float = L_SHIN, side: int = 1
                       ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute joint positions from angles (for plotting).

    Returns:
        (hip_pos, knee_pos, foot_pos) as 3D numpy arrays
        relative to the hip joint origin.
    """
    origin = np.array([0.0, 0.0, 0.0])

    # Hip joint → thigh pivot (lateral offset)
    hip_end = np.array([
        0.0,
        side * l_hip * math.cos(hip_angle),
        -l_hip * math.sin(hip_angle)
    ])

    # Thigh pivot → knee
    thigh_z = -l_thigh * math.cos(thigh_angle)
    thigh_x = l_thigh * math.sin(thigh_angle)
    knee_pos = hip_end + np.array([thigh_x, 0.0, thigh_z])

    # Knee → foot
    total_angle = thigh_angle + knee_angle
    shin_z = -l_shin * math.cos(total_angle)
    shin_x = l_shin * math.sin(total_angle)
    foot_pos = knee_pos + np.array([shin_x, 0.0, shin_z])

    return origin, hip_end, knee_pos, foot_pos


# ══════════════════════════════════════════════════════════════════════════════
# STANDALONE TESTING + VISUALIZATION
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

    ik = IKSolver()

    print("=" * 60)
    print("  VIGIL-RQ — Inverse Kinematics Test")
    print("=" * 60)
    print(f"  Hip offset (L1):  {L_HIP * 1000:.1f} mm")
    print(f"  Thigh (L2):       {L_THIGH * 1000:.1f} mm")
    print(f"  Shin (L3):        {L_SHIN * 1000:.1f} mm")
    print(f"  Max reach:        {(L_THIGH + L_SHIN) * 1000:.1f} mm")
    print()

    # ── Test Cases ──
    test_cases = [
        ("Standing neutral",   0.000,  L_HIP,  -0.200),
        ("Foot forward",       0.050,  L_HIP,  -0.200),
        ("Foot back",         -0.050,  L_HIP,  -0.200),
        ("Crouched",           0.000,  L_HIP,  -0.120),
        ("Extended",           0.000,  L_HIP,  -0.240),
        ("Foot outward",       0.000,  0.120,  -0.200),
    ]

    fig = plt.figure(figsize=(16, 10))
    fig.suptitle("VIGIL-RQ — IK Solver Verification", fontsize=14, fontweight='bold')

    for i, (name, x, y, z) in enumerate(test_cases):
        result = ik.solve(x, y, z, side=1)
        if result is None:
            print(f"  ✗ {name}: UNREACHABLE  (x={x:.3f}, y={y:.3f}, z={z:.3f})")
            continue

        hip_deg = math.degrees(result[0])
        thigh_deg = math.degrees(result[1])
        knee_deg = math.degrees(result[2])

        print(f"  ✓ {name:20s}  →  Hip: {hip_deg:+6.1f}°  Thigh: {thigh_deg:+6.1f}°  Knee: {knee_deg:+6.1f}°")

        # Verify with forward kinematics
        origin, hip_end, knee_pos, foot_pos = forward_kinematics(*result, side=1)

        # Plot
        ax = fig.add_subplot(2, 3, i + 1, projection='3d')
        ax.set_title(f"{name}\nH:{hip_deg:+.1f}° T:{thigh_deg:+.1f}° K:{knee_deg:+.1f}°",
                     fontsize=9)

        # Draw leg segments
        points = np.array([origin, hip_end, knee_pos, foot_pos])
        ax.plot(points[:, 0] * 1000, points[:, 1] * 1000, points[:, 2] * 1000,
                'o-', linewidth=3, markersize=8, color='#3b82f6')
        ax.scatter(*foot_pos * 1000, s=100, c='red', marker='v', zorder=5,
                   label=f'Foot ({x*1000:.0f},{y*1000:.0f},{z*1000:.0f})')

        # Draw target
        ax.scatter(x * 1000, y * 1000, z * 1000, s=80, c='lime', marker='x',
                   linewidths=3, zorder=5, label='Target')

        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_zlabel('Z (mm)')
        ax.set_xlim(-100, 100)
        ax.set_ylim(-20, 150)
        ax.set_zlim(-280, 20)
        ax.legend(fontsize=7, loc='upper right')

    print()
    print("  ── Full body stance test ──")
    stance = ik.get_default_stance(height=0.20)
    all_angles = ik.solve_all_legs(stance)
    for joint, angle in sorted(all_angles.items()):
        print(f"    {joint:12s}: {math.degrees(angle):+6.1f}°")

    plt.tight_layout()
    plt.savefig("ik_test_results.png", dpi=150, bbox_inches='tight')
    print(f"\n  Plot saved: ik_test_results.png")
    plt.show()
