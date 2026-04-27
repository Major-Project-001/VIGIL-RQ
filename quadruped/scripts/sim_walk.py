"""
sim_walk.py — PyBullet Simulation for VIGIL-RQ Quadruped

Loads the robot URDF, applies IK-based standing pose, then runs a
trot gait demonstration. Renders in real-time with PyBullet GUI.

Requirements:
    pip install pybullet numpy

Usage:
    python sim_walk.py                 # Interactive GUI
    python sim_walk.py --record        # Record video frames
    python sim_walk.py --headless      # No GUI, print angles only
"""

import pybullet as p
import pybullet_data
import numpy as np
import time
import math
import argparse
import os
import sys

# ── Add parent paths for imports ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, os.path.join(REPO_ROOT, "control", "rpi"))

try:
    from gait.ik_solver import IKSolver, LEG_ORIGINS, LEG_SIDE, L_HIP
    from config import JOINT_LIMITS
    IK_AVAILABLE = True
except ImportError:
    print("[WARN] IK solver or config not found, using basic sine gait")
    IK_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

URDF_PATH = os.path.join(REPO_ROOT, "quadruped", "urdf", "robot.urdf")
TIME_STEP = 1.0 / 240.0    # PyBullet default timestep
GAIT_DT = 1.0 / 50.0       # Gait update rate (50 Hz)

# Standing height
STAND_HEIGHT = 0.20         # meters

# Trot gait parameters
TROT_FREQ = 1.5             # Hz
STEP_HEIGHT = 0.03          # meters (foot lift)
STRIDE_LENGTH = 0.06        # meters (forward stride)

# Joint name mapping from URDF to our convention
JOINT_MAP = {
    "fl_hip_joint":   "fl_hip",
    "fl_thigh_joint": "fl_thigh",
    "fl_knee_joint":  "fl_knee",
    "fr_hip_joint":   "fr_hip",
    "fr_thigh_joint": "fr_thigh",
    "fr_knee_joint":  "fr_knee",
    "rl_hip_joint":   "rl_hip",
    "rl_thigh_joint": "rl_thigh",
    "rl_knee_joint":  "rl_knee",
    "rr_hip_joint":   "rr_hip",
    "rr_thigh_joint": "rr_thigh",
    "rr_knee_joint":  "rr_knee",
}


# ══════════════════════════════════════════════════════════════════════════════
# TROT GAIT GENERATOR (IK-based)
# ══════════════════════════════════════════════════════════════════════════════

class TrotGait:
    """
    Generates trot gait foot trajectories using Bezier-curve swing phases
    and straight-line stance phases.

    Diagonal pairs: (FL, RR) and (FR, RL) move in anti-phase.
    """

    def __init__(self, ik_solver: 'IKSolver', height: float = STAND_HEIGHT):
        self.ik = ik_solver
        self.height = height
        self.phase = 0.0

        # Default stance positions (foot targets in body frame)
        self.default_stance = {}
        for leg in ["fl", "fr", "rl", "rr"]:
            origin = LEG_ORIGINS[leg]
            side = LEG_SIDE[leg]
            self.default_stance[leg] = np.array([
                origin[0],
                origin[1] + side * L_HIP,
                origin[2] - self.height
            ])

    def get_foot_positions(self, t: float, vx: float = 0.0,
                           vy: float = 0.0, yaw_rate: float = 0.0):
        """
        Compute foot positions for all 4 legs at time t.

        Args:
            t: Time in seconds
            vx: Forward velocity command (m/s)
            vy: Lateral velocity command (m/s)
            yaw_rate: Turn rate (rad/s)

        Returns:
            Dict of {leg_name: np.array([x, y, z])} in body frame
        """
        phase = (t * TROT_FREQ) % 1.0  # Normalized phase [0, 1)

        # Diagonal pairing: FL+RR phase 0, FR+RL phase 0.5
        leg_phases = {
            "fl": phase,
            "rr": phase,
            "fr": (phase + 0.5) % 1.0,
            "rl": (phase + 0.5) % 1.0,
        }

        positions = {}
        for leg, leg_phase in leg_phases.items():
            base = self.default_stance[leg].copy()

            if vx == 0.0 and vy == 0.0 and yaw_rate == 0.0:
                # Standing still — just return default stance
                positions[leg] = base
                continue

            # Swing phase: first half of cycle (0.0 to 0.5)
            # Stance phase: second half (0.5 to 1.0)
            if leg_phase < 0.5:
                # ── Swing ── lift foot and move forward
                swing_progress = leg_phase / 0.5  # 0→1 through swing

                # Forward/back offset
                x_offset = STRIDE_LENGTH * (swing_progress - 0.5) * vx
                y_offset = STRIDE_LENGTH * (swing_progress - 0.5) * vy

                # Foot lift: parabolic arc
                z_lift = STEP_HEIGHT * 4.0 * swing_progress * (1.0 - swing_progress)

                base[0] += x_offset
                base[1] += y_offset
                base[2] += z_lift  # Lift foot up

            else:
                # ── Stance ── foot on ground, push backward
                stance_progress = (leg_phase - 0.5) / 0.5  # 0→1 through stance

                x_offset = STRIDE_LENGTH * (0.5 - stance_progress) * vx
                y_offset = STRIDE_LENGTH * (0.5 - stance_progress) * vy

                base[0] += x_offset
                base[1] += y_offset

            positions[leg] = base

        return positions

    def compute_angles(self, t: float, vx: float = 0.0,
                       vy: float = 0.0, yaw_rate: float = 0.0):
        """Compute all 12 joint angles for the given time."""
        positions = self.get_foot_positions(t, vx, vy, yaw_rate)
        return self.ik.solve_all_legs(positions)


# ══════════════════════════════════════════════════════════════════════════════
# SIMPLE SINE GAIT (fallback if IK not available)
# ══════════════════════════════════════════════════════════════════════════════

def compute_sine_gait(t: float):
    """Simple sinusoidal trot gait (no IK needed)."""
    freq = 1.5
    phase = 2.0 * math.pi * freq * t

    angles = {}
    for leg, sign, ph_offset in [("fl", 1, 0), ("rr", 1, 0),
                                  ("fr", -1, math.pi), ("rl", -1, math.pi)]:
        ph = phase + ph_offset
        angles[f"{leg}_hip"] = 0.0
        angles[f"{leg}_thigh"] = 0.3 * math.sin(ph)
        knee_lift = max(0.0, math.sin(ph))
        angles[f"{leg}_knee"] = -0.3 - 0.4 * knee_lift
    return angles


# ══════════════════════════════════════════════════════════════════════════════
# SIMULATION
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="VIGIL-RQ PyBullet Simulation")
    parser.add_argument("--headless", action="store_true", help="No GUI")
    parser.add_argument("--record", action="store_true", help="Record video frames")
    parser.add_argument("--duration", type=float, default=30.0, help="Sim duration (s)")
    args = parser.parse_args()

    # ── Initialize PyBullet ──
    if args.headless:
        physics_client = p.connect(p.DIRECT)
    else:
        physics_client = p.connect(p.GUI)
        p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
        p.configureDebugVisualizer(p.COV_ENABLE_SHADOWS, 1)

    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.setTimeStep(TIME_STEP)

    # ── Load ground plane ──
    plane_id = p.loadURDF("plane.urdf")

    # ── Load robot ──
    if not os.path.exists(URDF_PATH):
        print(f"[ERROR] URDF not found: {URDF_PATH}")
        return

    # Spawn robot above ground
    start_pos = [0, 0, 0.35]
    start_orn = p.getQuaternionFromEuler([0, 0, 0])
    robot_id = p.loadURDF(URDF_PATH, start_pos, start_orn,
                          useFixedBase=False,
                          flags=p.URDF_USE_SELF_COLLISION_EXCLUDE_PARENT)

    print(f"[SIM] Robot loaded: {URDF_PATH}")

    # ── Map joint names to indices ──
    joint_indices = {}
    num_joints = p.getNumJoints(robot_id)
    print(f"[SIM] Total joints: {num_joints}")

    for i in range(num_joints):
        info = p.getJointInfo(robot_id, i)
        name = info[1].decode('utf-8')
        joint_type = info[2]
        if name in JOINT_MAP and joint_type == p.JOINT_REVOLUTE:
            joint_indices[JOINT_MAP[name]] = i
            print(f"  [{i}] {name} → {JOINT_MAP[name]}")

    if len(joint_indices) < 12:
        print(f"[WARN] Only found {len(joint_indices)}/12 joints. Check URDF joint names.")
        # Print all joints for debugging
        for i in range(num_joints):
            info = p.getJointInfo(robot_id, i)
            print(f"  [{i}] {info[1].decode('utf-8')} type={info[2]}")

    # ── Setup IK-based gait ──
    if IK_AVAILABLE:
        ik = IKSolver()
        gait = TrotGait(ik)
        print("[SIM] Using IK-based trot gait")
    else:
        gait = None
        print("[SIM] Using simple sine gait (IK not available)")

    # ── Camera setup ──
    if not args.headless:
        p.resetDebugVisualizerCamera(
            cameraDistance=0.6,
            cameraYaw=45,
            cameraPitch=-30,
            cameraTargetPosition=[0, 0, 0.15]
        )

    # ── GUI controls ──
    if not args.headless:
        vx_slider = p.addUserDebugParameter("Forward Speed", -1.0, 1.0, 0.0)
        vy_slider = p.addUserDebugParameter("Lateral Speed", -1.0, 1.0, 0.0)
        yaw_slider = p.addUserDebugParameter("Yaw Rate", -1.0, 1.0, 0.0)
        height_slider = p.addUserDebugParameter("Body Height", 0.10, 0.28, 0.20)
        mode_slider = p.addUserDebugParameter("Mode (0=stand,1=walk)", 0, 1, 0)

    # ── Simulation loop ──
    print(f"\n[SIM] Running for {args.duration}s...")
    print("[SIM] Use GUI sliders to control the robot")
    print("[SIM] Press Ctrl+C to stop\n")

    sim_time = 0.0
    gait_timer = 0.0
    frame = 0

    try:
        while sim_time < args.duration:
            # Read GUI controls
            if not args.headless:
                vx = p.readUserDebugParameter(vx_slider)
                vy = p.readUserDebugParameter(vy_slider)
                yaw = p.readUserDebugParameter(yaw_slider)
                height = p.readUserDebugParameter(height_slider)
                mode = int(round(p.readUserDebugParameter(mode_slider)))
            else:
                # Auto walk in headless mode
                vx = 0.5 if sim_time > 2.0 else 0.0
                vy = 0.0
                yaw = 0.0
                height = 0.20
                mode = 1 if sim_time > 2.0 else 0

            # Update gait at 50 Hz
            gait_timer += TIME_STEP
            if gait_timer >= GAIT_DT:
                gait_timer = 0.0

                if mode == 1 and (vx != 0 or vy != 0 or yaw != 0):
                    # Walking
                    if gait is not None:
                        gait.height = height
                        angles = gait.compute_angles(sim_time, vx, vy, yaw)
                    else:
                        angles = compute_sine_gait(sim_time)
                else:
                    # Standing
                    if gait is not None:
                        gait.height = height
                        positions = gait.get_foot_positions(sim_time, 0, 0, 0)
                        angles = gait.ik.solve_all_legs(positions)
                    else:
                        angles = {f"{l}_{j}": 0.0
                                  for l in ["fl","fr","rl","rr"]
                                  for j in ["hip","thigh","knee"]}

                # Apply joint angles
                for joint_name, angle in angles.items():
                    if joint_name in joint_indices:
                        idx = joint_indices[joint_name]
                        p.setJointMotorControl2(
                            robot_id, idx,
                            controlMode=p.POSITION_CONTROL,
                            targetPosition=angle,
                            force=20.0,
                            maxVelocity=5.0
                        )

            # Step simulation
            p.stepSimulation()
            sim_time += TIME_STEP
            frame += 1

            # Real-time sync (GUI only)
            if not args.headless:
                time.sleep(TIME_STEP)

            # Record frames
            if args.record and frame % 4 == 0:
                os.makedirs("sim_frames", exist_ok=True)
                p.saveBullet(f"sim_frames/state_{frame:06d}.bullet")

            # Track robot position for camera
            if not args.headless and frame % 48 == 0:
                pos, _ = p.getBasePositionAndOrientation(robot_id)
                p.resetDebugVisualizerCamera(
                    cameraDistance=0.6, cameraYaw=45, cameraPitch=-30,
                    cameraTargetPosition=pos
                )

    except KeyboardInterrupt:
        print("\n[SIM] Stopped by user")

    # ── Cleanup ──
    p.disconnect()
    print(f"[SIM] Completed. {frame} frames, {sim_time:.1f}s simulated.")


if __name__ == "__main__":
    main()
