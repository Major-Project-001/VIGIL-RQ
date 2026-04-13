"""
joint_control.py - Interactive slider control for the quadruped robot.

12 sliders (3 per leg: hip, thigh, knee) for real-time joint control.
Meshes are from Blender export (world-space), so default joint angles = 0.
"""
import pybullet as p
import pybullet_data
import time
import os
import sys
import math

# ── Config ──
SPAWN_HEIGHT = 0.45
SIM_TIMESTEP = 1.0 / 240.0

script_dir = os.path.dirname(os.path.abspath(__file__))
urdf_path = os.path.normpath(os.path.join(script_dir, "..", "urdf", "robot.urdf"))

if not os.path.isfile(urdf_path):
    print(f"[ERROR] URDF not found: {urdf_path}")
    sys.exit(1)

# ── Connect ──
cid = p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.81)
p.setTimeStep(SIM_TIMESTEP)
p.loadURDF("plane.urdf")

# ── Load robot ──
robot = p.loadURDF(
    urdf_path,
    basePosition=[0, 0, SPAWN_HEIGHT],
    useFixedBase=False,
)

# ── Clean up debug visuals (hide red collision shapes) ──
p.configureDebugVisualizer(p.COV_ENABLE_WIREFRAME, 0)
p.configureDebugVisualizer(p.COV_ENABLE_RGB_BUFFER_PREVIEW, 0)
p.configureDebugVisualizer(p.COV_ENABLE_DEPTH_BUFFER_PREVIEW, 0)
p.configureDebugVisualizer(p.COV_ENABLE_SEGMENTATION_MARK_PREVIEW, 0)

# ── Discover joints ──
joint_info = []
for i in range(p.getNumJoints(robot)):
    info = p.getJointInfo(robot, i)
    if info[2] != p.JOINT_FIXED:
        joint_info.append({
            "idx": i,
            "name": info[1].decode(),
            "lower": info[8],
            "upper": info[9],
        })

print(f"[INFO] {len(joint_info)} actuated joints")

# ── Set initial pose (all zeros - matches Blender export) ──
for j in joint_info:
    p.resetJointState(robot, j["idx"], 0.0)

# ── Create sliders ──
sliders = []
for j in joint_info:
    sid = p.addUserDebugParameter(
        j["name"],
        j["lower"],
        j["upper"],
        0.0,  # default = 0 (Blender standing pose)
    )
    sliders.append(sid)

# ── Preset buttons ──
btn_stand = p.addUserDebugParameter("STAND (reset to 0)", 1, 0, 0)
btn_sit = p.addUserDebugParameter("SIT (knees bent)", 1, 0, 0)

last_stand = 0
last_sit = 0

# Preset poses
STAND_POSE = {j["name"]: 0.0 for j in joint_info}
SIT_POSE = {}
for j in joint_info:
    if "knee" in j["name"]:
        SIT_POSE[j["name"]] = -1.5
    elif "thigh" in j["name"]:
        SIT_POSE[j["name"]] = 0.8
    else:
        SIT_POSE[j["name"]] = 0.0

# ── Camera ──
p.resetDebugVisualizerCamera(
    cameraDistance=0.8,
    cameraYaw=45,
    cameraPitch=-30,
    cameraTargetPosition=[0, 0, 0.15],
)

print("[INFO] Sliders ready. Adjust joints or use STAND/SIT buttons.")
print("[INFO] Close window or Ctrl+C to exit.\n")

# ── Main loop ──
step = 0
try:
    while True:
        # Check preset buttons
        stand_val = p.readUserDebugParameter(btn_stand)
        sit_val = p.readUserDebugParameter(btn_sit)

        if stand_val > last_stand:
            last_stand = stand_val
            for idx, j in enumerate(joint_info):
                p.resetJointState(robot, j["idx"], STAND_POSE[j["name"]])
            print("[POSE] Stand")

        if sit_val > last_sit:
            last_sit = sit_val
            for idx, j in enumerate(joint_info):
                p.resetJointState(robot, j["idx"], SIT_POSE[j["name"]])
            print("[POSE] Sit")

        # Read sliders and apply
        for idx, j in enumerate(joint_info):
            target = p.readUserDebugParameter(sliders[idx])
            p.setJointMotorControl2(
                robot, j["idx"],
                controlMode=p.POSITION_CONTROL,
                targetPosition=target,
                force=20.0,
                positionGain=0.3,
                velocityGain=1.0,
            )

        p.stepSimulation()
        step += 1

        # Print status every 5 seconds
        if step % 1200 == 0:
            pos, orn = p.getBasePositionAndOrientation(robot)
            euler = p.getEulerFromQuaternion(orn)
            print(f"  height={pos[2]:.3f}m  rpy=({math.degrees(euler[0]):.1f}, "
                  f"{math.degrees(euler[1]):.1f}, {math.degrees(euler[2]):.1f})")

        time.sleep(SIM_TIMESTEP)

except KeyboardInterrupt:
    print("\n[INFO] Stopped.")
except p.error as e:
    print(f"\n[ERROR] {e}")
finally:
    try:
        p.disconnect()
    except:
        pass
