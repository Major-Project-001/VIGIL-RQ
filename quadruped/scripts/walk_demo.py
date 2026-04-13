"""
walk_demo.py - Simple trot gait demo using the Motor Control API.

Demonstrates the QuadrupedController API with a sine-wave based trot gait.
Diagonal legs move in sync (FL+RR, FR+RL) with 180-degree phase offset.

Usage:
    python quadruped/scripts/walk_demo.py
"""
import math
import time
import sys
import os

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motor_api import QuadrupedController

# ── Gait parameters ──
FREQ = 1.0           # Gait frequency (Hz)
HIP_AMP = 0.15       # Hip sideways amplitude (rad)
THIGH_AMP = 0.4      # Thigh forward/back amplitude (rad)
THIGH_OFFSET = 0.0   # Thigh neutral angle
KNEE_AMP = 0.5       # Knee bend amplitude (rad)
KNEE_OFFSET = -0.3   # Knee neutral (slight bend)
DURATION = 15.0       # Demo duration (seconds)


def trot_gait(t, freq=FREQ):
    """
    Compute joint angles for a trot gait at time t.
    
    Trot: diagonal legs (FL+RR) and (FR+RL) alternate.
    
    Returns:
        dict of {joint_name: angle_rad}
    """
    phase = 2.0 * math.pi * freq * t
    
    angles = {}
    
    # Diagonal pairs with 180-degree phase offset
    for leg, sign, phase_offset in [
        ("fl", 1.0, 0.0),        # FL: phase 0
        ("rr", 1.0, 0.0),        # RR: same phase as FL (diagonal pair)
        ("fr", -1.0, math.pi),   # FR: 180 degrees offset
        ("rl", -1.0, math.pi),   # RL: same as FR (diagonal pair)
    ]:
        ph = phase + phase_offset
        
        # Hip: gentle sideways sway
        angles[f"{leg}_hip_joint"] = HIP_AMP * math.sin(ph * 0.5) * sign
        
        # Thigh: forward/back swing
        angles[f"{leg}_thigh_joint"] = THIGH_OFFSET + THIGH_AMP * math.sin(ph)
        
        # Knee: lift during forward swing, extend during backward
        # Use a modified sine to create a "lifting" motion
        knee_phase = math.sin(ph)
        knee_lift = max(0, knee_phase)  # Only lift, don't push down
        angles[f"{leg}_knee_joint"] = KNEE_OFFSET - KNEE_AMP * knee_lift
    
    return angles


def main():
    print("=" * 50)
    print("  VIGIL-RQ Quadruped — Trot Gait Demo")
    print("=" * 50)
    
    # Initialize
    ctrl = QuadrupedController(render=True, fixed_base=False)
    
    # Warm up: stand for 2 seconds
    print("\n[PHASE 1] Stabilizing in standing pose...")
    for _ in range(480):
        ctrl.stand()
        ctrl.sleep_step()
    
    # Get initial height
    imu = ctrl.get_imu()
    print(f"  Initial height: {imu['height']:.3f}m")
    
    # Walk!
    print(f"\n[PHASE 2] Trotting for {DURATION:.0f} seconds...")
    start_time = time.time()
    sim_t = 0.0
    step_count = 0
    
    try:
        while sim_t < DURATION:
            # Compute gait angles
            angles = trot_gait(sim_t)
            ctrl.set_joint_angles(angles)
            
            # Step simulation with real time
            ctrl.sleep_step()
            sim_t += ctrl.dt
            step_count += 1
            
            # Print status every 2 seconds
            if step_count % 480 == 0:
                imu = ctrl.get_imu()
                elapsed = time.time() - start_time
                print(f"  t={sim_t:.1f}s  height={imu['height']:.3f}m  "
                      f"rpy=({math.degrees(imu['rpy'][0]):.1f}, "
                      f"{math.degrees(imu['rpy'][1]):.1f}, "
                      f"{math.degrees(imu['rpy'][2]):.1f})  "
                      f"pos=({imu['position'][0]:.3f}, {imu['position'][1]:.3f})")
    
    except KeyboardInterrupt:
        print("\n  Interrupted!")
    
    # Cool down: stand
    print("\n[PHASE 3] Returning to stand...")
    for _ in range(480):
        ctrl.stand()
        ctrl.sleep_step()
    
    # Final state
    imu = ctrl.get_imu()
    print(f"\n[FINAL] height={imu['height']:.3f}m  "
          f"position=({imu['position'][0]:.3f}, {imu['position'][1]:.3f}, {imu['position'][2]:.3f})")
    
    print("\n[DONE] Close the PyBullet window to exit.")
    
    # Keep window open
    try:
        while True:
            ctrl.sleep_step()
    except (KeyboardInterrupt, Exception):
        pass
    
    ctrl.disconnect()


if __name__ == "__main__":
    main()
