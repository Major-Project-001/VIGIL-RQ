# 🦾 VIGIL-RQ
### **V**ision-**G**uided **I**ntelligent **L**ocomotion for **R**obotic **Q**uadrupeds

<p align="center">
  <img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge" alt="Status Active">
  <img src="https://img.shields.io/badge/Hardware-Quadruped-blue?style=for-the-badge" alt="Hardware Quadruped">
  <img src="https://img.shields.io/badge/Phase-2--Rigging-orange?style=for-the-badge" alt="Phase 2">
</p>

---

## 📖 Overview

VIGIL-RQ is an advanced robotics research project aimed at creating a fully autonomous, vision-aware quadruped robot. The project integrates state-of-the-art **Computer Vision** for operator tracking with a high-fidelity **PyBullet Simulation** environment. 

This repository serves as the central hub for the vision modules, simulation rigging, and locomotion control APIs.

---

## 🗺️ Project Roadmap

```mermaid
graph TD
    subgraph "Phase 1: The Eyes (Complete)"
        P1_1["MediaPipe Pose Integration"] --> P1_2["33-Keypoint skeleton tracking"]
        P1_2 --> P1_3["Directional Logic (L/C/R)"]
    end

    subgraph "Phase 2: The Body (Current)"
        P2_1["Blender 3D Rigging"] --> P2_2["URDF Generation Engine"]
        P2_2 --> P2_3["Link-Local Mesh Optimization"]
        P2_3 --> P2_4["Modular Motor API"]
        P2_4 --> P2_5["Sine-wave Trot Gait"]
    end

    subgraph "Phase 3: The Brain (Future)"
        P3_1["Gymnasium RL Wrapper"] --> P3_2["PPO/SAC Policy Training"]
        P3_2 --> P3_3["Sim-to-Real Bridge"]
        P3_3 --> P3_4["FPGA Hardware Integration"]
    end

    Phase 1 --> Phase 2
    Phase 2 --> Phase 3
```

---

## 🛠️ Technical Deep-Dive

### 1. 👁️ Vision Module (`vision/`)
Built on Google's **MediaPipe Pose Landmarker**, the vision system provides low-latency human tracking. 
*   **Keypoint Extraction**: Uses the Nose landmark (Index 0) to determine operator position.
*   **Threshold Logic**:
    *   **X < 0.4**: `LEFT` command
    *   **X > 0.6**: `RIGHT` command
    *   **0.4 < X < 0.6**: `CENTER` command
*   **Safety**: Designed to ignore background noise and prioritize the primary human operator.

### 2. 🐕 Simulation Engine & Rigging
The simulation is powered by **PyBullet** and features a highly optimized URDF assembly.
*   **Link-Local Transformation**: Unlike standard exports, our pipeline uses a custom algorithm to re-center STL vertices relative to their parent link origins. This eliminates "visual orbit" bugs and ensures physics and visuals are perfectly aligned at the joint pivot.
*   **Mesh-to-Link Mapping**:
    *   **Base**: Main chassis + Hip Servo housings.
    *   **Hip**: Servo gear + Joint pivots (Sideways rotation, Y-axis).
    *   **Thigh**: Upper leg assembly (Forward/Back rotation, X-axis).
    *   **Calf**: Lower leg + Foot assembly (Knee lift, X-axis).

### 3. ⚙️ Locomotion & Motor API (`motor_api.py`)
Our modular API provides an industrial-grade interface for robot control:
*   `set_joint_angles(dict)`: Direct motor index control.
*   `set_leg_pose(leg, hip, thigh, knee)`: Per-leg geometric control.
*   `get_imu()`: Returns 6-DOF data including Roll, Pitch, Yaw, and Linear/Angular Velocities.
*   **Presets**: Built-in `stand()`, `sit()`, and `rest()` poses.

---

## 🔌 System Architecture

```mermaid
flowchart LR
    A["📷 Camera Stream"] ==> B["🧠 MediaPipe Pose"]
    B ==> C["⚙️ Decision Logic"]

    subgraph "Locomotion Layer"
        C -.->|"CMD: LEFT/RIGHT"| D["🐕 Motor API"]
        D ==> E["🌍 PyBullet Physics"]
        E ==> F["📊 IMU / State Feedback"]
        F ==> D
    end

    style A fill:#1e3a5f,stroke:#4a90d9,color:#fff
    style B fill:#2d1b4e,stroke:#8b5cf6,color:#fff
    style C fill:#1b3d2f,stroke:#34d399,color:#fff
    style D fill:#e65100,stroke:#ffb74d,color:#fff
    style E fill:#4a1e1e,stroke:#f87171,color:#fff
    style F fill:#0d47a1,stroke:#42a5f5,color:#fff
```

---

## 🚀 Future Vision: Reinforcement Learning

The project is currently transitioning to **Deep Reinforcement Learning (DRL)**.
*   **Environment**: We are wrapping the simulation in a `gymnasium.Env` interface.
*   **Algorithm**: Utilizing **Proximal Policy Optimization (PPO)** to train gait stability.
*   **Observation Space**: IMU data (Roll, Pitch, Accelerometer) + Joint Positions.
*   **Action Space**: target joint angles for 12 servos.

---

## ⚡ Setup & Usage

### ⚙️ Quick Installation
```bash
git clone https://github.com/Major-Project-001/VIGIL-RQ.git
pip install pybullet mediapipe opencv-python numpy
```

### 🏃 Running the Demos
1.  **Manual Control**: `python quadruped/scripts/joint_control.py`
2.  **Autonomous Trot**: `python quadruped/scripts/walk_demo.py`
3.  **Vision Tracking**: `python main.py`

---
> **Project VIGIL-RQ** | Major Project | Robotics & AI 🦾
