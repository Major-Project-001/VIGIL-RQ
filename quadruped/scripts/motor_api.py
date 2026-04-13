"""
motor_api.py - Programmatic control API for the VIGIL-RQ quadruped robot.

Provides a clean interface for controlling the 12-DOF quadruped in PyBullet.
Designed for future RL integration.

Usage:
    from motor_api import QuadrupedController
    ctrl = QuadrupedController()
    ctrl.stand()
    ctrl.set_leg_pose("fl", hip=0.0, thigh=-0.3, knee=-0.5)
    states = ctrl.get_joint_states()
    ctrl.disconnect()
"""
import pybullet as p
import pybullet_data
import time
import os
import sys
import math
import numpy as np

# ── Leg & joint naming ──
LEGS = ["fl", "fr", "rl", "rr"]
JOINTS_PER_LEG = ["hip", "thigh", "knee"]
ALL_JOINT_NAMES = [f"{leg}_{jt}_joint" for leg in LEGS for jt in JOINTS_PER_LEG]

# ── Preset poses ──
PRESETS = {
    "stand": {j: 0.0 for j in ALL_JOINT_NAMES},
    "sit": {
        **{f"{l}_hip_joint": 0.0 for l in LEGS},
        **{f"{l}_thigh_joint": 0.5 for l in LEGS},
        **{f"{l}_knee_joint": -1.2 for l in LEGS},
    },
    "rest": {
        **{f"{l}_hip_joint": 0.0 for l in LEGS},
        **{f"{l}_thigh_joint": 0.8 for l in LEGS},
        **{f"{l}_knee_joint": -1.8 for l in LEGS},
    },
}


class QuadrupedController:
    """High-level controller for the VIGIL-RQ quadruped robot."""

    def __init__(self, render=True, fixed_base=False, spawn_height=0.45):
        """
        Initialize the simulation and load the robot.
        
        Args:
            render: True for GUI, False for headless (DIRECT) mode
            fixed_base: Pin the body in the air (useful for joint testing)
            spawn_height: Initial Z height of the base link
        """
        self.spawn_height = spawn_height
        self.dt = 1.0 / 240.0

        # Connect
        mode = p.GUI if render else p.DIRECT
        self.cid = p.connect(mode)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)
        p.setTimeStep(self.dt)

        # Clean visuals
        if render:
            p.configureDebugVisualizer(p.COV_ENABLE_WIREFRAME, 0)
            p.configureDebugVisualizer(p.COV_ENABLE_RGB_BUFFER_PREVIEW, 0)
            p.configureDebugVisualizer(p.COV_ENABLE_DEPTH_BUFFER_PREVIEW, 0)
            p.configureDebugVisualizer(p.COV_ENABLE_SEGMENTATION_MARK_PREVIEW, 0)
            p.resetDebugVisualizerCamera(
                cameraDistance=0.8, cameraYaw=45, cameraPitch=-30,
                cameraTargetPosition=[0, 0, 0.15],
            )

        # Ground
        self.plane = p.loadURDF("plane.urdf")

        # Robot
        script_dir = os.path.dirname(os.path.abspath(__file__))
        urdf_path = os.path.normpath(os.path.join(script_dir, "..", "urdf", "robot.urdf"))
        if not os.path.isfile(urdf_path):
            raise FileNotFoundError(f"URDF not found: {urdf_path}")

        self.robot = p.loadURDF(
            urdf_path,
            basePosition=[0, 0, spawn_height],
            useFixedBase=fixed_base,
        )

        # Build joint map: name -> index
        self.joint_map = {}
        self.joint_limits = {}
        for i in range(p.getNumJoints(self.robot)):
            info = p.getJointInfo(self.robot, i)
            name = info[1].decode()
            if info[2] != p.JOINT_FIXED:
                self.joint_map[name] = i
                self.joint_limits[name] = (info[8], info[9])  # (lower, upper)

        assert len(self.joint_map) == 12, f"Expected 12 joints, got {len(self.joint_map)}"

        # Initialize to standing pose
        self.reset_pose("stand")
        print(f"[QuadrupedController] Ready. {len(self.joint_map)} joints loaded.")

    # ── Core control ──

    def set_joint_angles(self, angles: dict, force=20.0, kp=0.3, kd=1.0):
        """
        Set target angles for multiple joints.

        Args:
            angles: dict of {joint_name: target_angle_rad}
            force: max motor force (Nm)
            kp: position gain
            kd: velocity gain
        """
        for name, angle in angles.items():
            if name not in self.joint_map:
                continue
            lo, hi = self.joint_limits[name]
            angle = np.clip(angle, lo, hi)
            p.setJointMotorControl2(
                self.robot, self.joint_map[name],
                controlMode=p.POSITION_CONTROL,
                targetPosition=angle,
                force=force,
                positionGain=kp,
                velocityGain=kd,
            )

    def set_leg_pose(self, leg: str, hip=0.0, thigh=0.0, knee=0.0, **kwargs):
        """
        Set all 3 joint angles for one leg.

        Args:
            leg: "fl", "fr", "rl", or "rr"
            hip, thigh, knee: target angles in radians
        """
        self.set_joint_angles({
            f"{leg}_hip_joint": hip,
            f"{leg}_thigh_joint": thigh,
            f"{leg}_knee_joint": knee,
        }, **kwargs)

    def set_all_legs(self, hip=0.0, thigh=0.0, knee=0.0, **kwargs):
        """Set the same pose on all 4 legs."""
        for leg in LEGS:
            self.set_leg_pose(leg, hip, thigh, knee, **kwargs)

    # ── Presets ──

    def reset_pose(self, preset="stand"):
        """Instantly reset joints (no physics, teleport)."""
        angles = PRESETS.get(preset, PRESETS["stand"])
        for name, angle in angles.items():
            if name in self.joint_map:
                p.resetJointState(self.robot, self.joint_map[name], angle)

    def stand(self):
        """Smoothly move to standing pose via motor control."""
        self.set_joint_angles(PRESETS["stand"])

    def sit(self):
        """Smoothly move to sitting pose."""
        self.set_joint_angles(PRESETS["sit"])

    def rest(self):
        """Smoothly move to rest (flat) pose."""
        self.set_joint_angles(PRESETS["rest"])

    # ── State queries ──

    def get_joint_states(self) -> dict:
        """
        Get current joint positions, velocities, and torques.

        Returns:
            dict of {joint_name: {"pos": float, "vel": float, "torque": float}}
        """
        states = {}
        for name, idx in self.joint_map.items():
            js = p.getJointState(self.robot, idx)
            states[name] = {
                "pos": js[0],
                "vel": js[1],
                "torque": js[3],
            }
        return states

    def get_joint_positions(self) -> dict:
        """Get just the joint angles as {name: radians}."""
        return {n: p.getJointState(self.robot, i)[0]
                for n, i in self.joint_map.items()}

    def get_base_pose(self):
        """
        Get base link position and orientation.

        Returns:
            pos: (x, y, z) in meters
            orn: (roll, pitch, yaw) in radians
        """
        pos, quat = p.getBasePositionAndOrientation(self.robot)
        euler = p.getEulerFromQuaternion(quat)
        return np.array(pos), np.array(euler)

    def get_base_velocity(self):
        """
        Get base linear and angular velocity.

        Returns:
            lin_vel: (vx, vy, vz) m/s
            ang_vel: (wx, wy, wz) rad/s
        """
        lin, ang = p.getBaseVelocity(self.robot)
        return np.array(lin), np.array(ang)

    def get_imu(self) -> dict:
        """
        Simulated IMU reading (orientation + angular velocity).

        Returns:
            dict with "rpy", "angular_vel", "linear_vel", "height"
        """
        pos, rpy = self.get_base_pose()
        lin_vel, ang_vel = self.get_base_velocity()
        return {
            "rpy": rpy,
            "angular_vel": ang_vel,
            "linear_vel": lin_vel,
            "height": pos[2],
            "position": pos,
        }

    # ── Simulation ──

    def step(self, n=1):
        """Advance simulation by n timesteps."""
        for _ in range(n):
            p.stepSimulation()

    def step_seconds(self, seconds: float):
        """Advance simulation by a given number of seconds."""
        steps = int(seconds / self.dt)
        for _ in range(steps):
            p.stepSimulation()

    def sleep_step(self, n=1):
        """Step simulation with real-time delay (for GUI)."""
        for _ in range(n):
            p.stepSimulation()
            time.sleep(self.dt)

    def disconnect(self):
        """Disconnect from physics server."""
        try:
            p.disconnect(self.cid)
        except:
            pass


# ── Quick test ──
if __name__ == "__main__":
    ctrl = QuadrupedController(render=True, fixed_base=False)

    print("\n[TEST] Standing for 2 seconds...")
    for _ in range(480):
        ctrl.stand()
        ctrl.sleep_step()

    print("[TEST] Sitting...")
    for _ in range(480):
        ctrl.sit()
        ctrl.sleep_step()

    print("[TEST] Standing again...")
    for _ in range(480):
        ctrl.stand()
        ctrl.sleep_step()

    imu = ctrl.get_imu()
    print(f"\n[IMU] height={imu['height']:.3f}m  "
          f"rpy=({math.degrees(imu['rpy'][0]):.1f}, "
          f"{math.degrees(imu['rpy'][1]):.1f}, "
          f"{math.degrees(imu['rpy'][2]):.1f})")

    joints = ctrl.get_joint_positions()
    print(f"[JOINTS] {', '.join(f'{k}={v:.2f}' for k,v in joints.items())}")

    ctrl.disconnect()
    print("\n[DONE]")
