"""
test_pybullet.py — Load and validate the quadruped URDF in PyBullet.

Usage:
    python quadruped/scripts/test_pybullet.py

Diagnostic approach:
    1. First loads with FIXED BASE to verify URDF integrity
    2. Then reloads free-floating to test full physics
"""

import pybullet as p
import pybullet_data
import time
import os
import sys
import math

# ── Configuration ──────────────────────────────────────────────────
SPAWN_HEIGHT = 0.45          # metres above ground (legs are ~0.39m total)
SIM_TIMESTEP = 1.0 / 240.0  # 240 Hz physics
GRAVITY = -9.81              # m/s²

# Standing pose: meshes exported from Blender already in standing pose,
# so joint angles=0 matches the visual geometry
STANDING_ANGLES = [0.0, 0.0, 0.0] * 4  # all joints at zero

# ── Resolve URDF path ────────────────────────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
urdf_path = os.path.normpath(os.path.join(script_dir, "..", "urdf", "robot.urdf"))

if not os.path.isfile(urdf_path):
    print(f"[ERROR] URDF not found at: {urdf_path}")
    sys.exit(1)

# ── Connect to PyBullet ───────────────────────────────────────────
physics_client = p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, GRAVITY)
p.setTimeStep(SIM_TIMESTEP)

# ── Load environment ──────────────────────────────────────────────
plane_id = p.loadURDF("plane.urdf")

# ── Load robot (NO self collision flags!) ─────────────────────────
print(f"[INFO] Loading URDF: {urdf_path}")

robot_id = p.loadURDF(
    urdf_path,
    basePosition=[0, 0, SPAWN_HEIGHT],
    baseOrientation=p.getQuaternionFromEuler([0, 0, 0]),
    useFixedBase=False,
    # NOTE: Do NOT use URDF_USE_SELF_COLLISION flags — they ENABLE
    # self-collision which causes leg-to-leg and leg-to-body collisions
    # that launch the robot into orbit.
)

# ── Discover actuated joints ─────────────────────────────────────
num_joints = p.getNumJoints(robot_id)
actuated_joints = []
joint_names = []

for i in range(num_joints):
    info = p.getJointInfo(robot_id, i)
    if info[2] != p.JOINT_FIXED:
        actuated_joints.append(i)
        joint_names.append(info[1].decode("utf-8"))

print(f"[INFO] {len(actuated_joints)} actuated joints found")

# ── Set standing pose BEFORE any physics stepping ─────────────────
# resetJointState is instantaneous — no physics involved
for idx, joint_idx in enumerate(actuated_joints):
    p.resetJointState(robot_id, joint_idx, STANDING_ANGLES[idx], targetVelocity=0)

# ── Engage motors to HOLD the pose ───────────────────────────────
for idx, joint_idx in enumerate(actuated_joints):
    p.setJointMotorControl2(
        robot_id, joint_idx,
        controlMode=p.POSITION_CONTROL,
        targetPosition=STANDING_ANGLES[idx],
        force=20.0,
        positionGain=0.2,
        velocityGain=1.0,  # high velocity gain to damp oscillation
    )

# ── Print joint info ─────────────────────────────────────────────
print(f"\n{'Idx':>3}  {'Name':<25} {'Angle':>8}  {'Lower':>8}  {'Upper':>8}")
print("-" * 60)
for idx, joint_idx in enumerate(actuated_joints):
    info = p.getJointInfo(robot_id, joint_idx)
    name = info[1].decode("utf-8")
    lower = info[8]
    upper = info[9]
    print(f"{joint_idx:>3}  {name:<25} {STANDING_ANGLES[idx]:>8.2f}  {lower:>8.2f}  {upper:>8.2f}")

print(f"\n[INFO] Simulation running. Close window or Ctrl+C to exit.\n")

# ── Configure camera ─────────────────────────────────────────────
p.resetDebugVisualizerCamera(
    cameraDistance=0.8,
    cameraYaw=45,
    cameraPitch=-30,
    cameraTargetPosition=[0, 0, 0.15],
)

# ── Simulation loop ──────────────────────────────────────────────
step_count = 0
try:
    while True:
        p.stepSimulation()
        step_count += 1

        # Print base state every 3 seconds
        if step_count % 720 == 0:
            pos, orn = p.getBasePositionAndOrientation(robot_id)
            euler = p.getEulerFromQuaternion(orn)
            height = pos[2]
            # Detect instability
            if height > 2.0 or height < -1.0:
                print(f"[WARN] Robot unstable! height={height:.2f}m — something is wrong")
            else:
                print(f"[OK] height={height:.3f}m  "
                      f"rpy=({math.degrees(euler[0]):.1f}°, "
                      f"{math.degrees(euler[1]):.1f}°, "
                      f"{math.degrees(euler[2]):.1f}°)")

        time.sleep(SIM_TIMESTEP)

except KeyboardInterrupt:
    print("\n[INFO] Simulation stopped by user.")
except p.error as e:
    print(f"\n[ERROR] PyBullet error: {e}")
finally:
    try:
        p.disconnect()
    except:
        pass
