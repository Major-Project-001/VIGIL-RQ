# 🦾 VIGIL-RQ — Quadruped Simulation & Rigging

> **Physics-based simulation and programmatic motor control for the VIGIL-RQ quadruped robot.**

This branch (`urdf`) contains the complete rigging and physics simulation environment for the VIGIL-RQ quadruped robot, built using PyBullet. It provides a reliable URDF transformation pipeline from Blender, an interactive joint control interface, a programmatic Python API for driving motors, and a working trot gait demonstration.

---

## 🚀 Key Features

1. **Robust URDF Pipeline (`build_urdf.py`)**
   - Dynamically builds the `robot.urdf` from a Blender `full.blend` export.
   - Automatically transforms world-space STL vertices into **link-local** coordinate space. This guarantees stable, precise joint rotations without the visual mesh components "orbiting" out of bounds.
   - Computes exact joint axis configurations (e.g. Y axis for Hip sideways splay, X axis for Thigh/Knee forward swing) and assigns accurate physical collision primitives/inertia.

2. **Interactive Simulation (`joint_control.py`)**
   - Loads the assembled URDF into PyBullet.
   - Exposes 12 real-time GUI sliders mapping directly to physical servos (3 per leg).
   - Quick one-click UI presets for STAND and SIT poses.

3. **Motor API (`motor_api.py`)**
   - High-level, modular control wrapper class (`QuadrupedController`) designed specifically for future integration with Reinforcement Learning (RL) frameworks.
   - Handles batch joint assignments (`set_joint_angles`), leg-specific overrides (`set_leg_pose`), posture presets, and returns exact simulated states (simulated IMU readings, base velocities).

4. **Trot Demo (`walk_demo.py`)**
   - A demonstration of the Motor API driving a sine-wave based trot gait.
   - Integrates phases for stabilizing into gravity, trotting, and returning to a standing stance.

---

## ⚡ Quick Start

### Prerequisites

- Python 3.10+
- `pybullet` and `numpy` installed

### Installation

```bash
# Clone the repository and checkout the urdf branch
git clone https://github.com/Major-Project-001/VIGIL-RQ.git
cd VIGIL-RQ
git checkout urdf

# Run standard dependencies
pip install requirements.txt
# Alternatively, ensure pybullet and numpy are installed:
pip install pybullet numpy
```

### Try the Interactive Sliders

To run the interactive UI for testing joints manually:
```bash
python quadruped/scripts/joint_control.py
```
*(You can use the sliders on the right-hand panel to test individual linkages.)*

### Try the Walking Demo

To witness the API orchestrating an alternating diagonal trot gait:
```bash
python quadruped/scripts/walk_demo.py
```

---

## 🏗️ Architecture & Scripts

```text
quadruped/
├── 3D file/
│   └── full.blend              ← Original 3D design source
├── config/
│   ├── scene_info.json         ← Exported hierarchy details
│   └── export_manifest.json    ← File lists from Blender
├── urdf/
│   ├── robot.urdf              ← Final compiled simulation asset
│   ├── meshes_export/          ← Raw, world-space STLs
│   └── meshes_local/           ← Re-centered, link-local STLs
└── scripts/
    ├── blender_full_export.py  ← Script for Blender UI to output details
    ├── build_urdf.py           ← Engine: Maps STLs -> link-local -> creates URDF
    ├── joint_control.py        ← Sliders + PyBullet test GUI
    ├── motor_api.py            ← Programmatic control bindings
    └── walk_demo.py            ← Walking implementation 
```

---

## 🔜 Next Steps

The next stages of the simulation track involve moving towards autonomous walking patterns:
- Wrap the `QuadrupedController` into an **OpenAI Gym (Gymnasium) Environment**.
- Train robust locomotion policies using **Reinforcement Learning** (e.g., PPO/SAC).
- Finalize the bridge for Sim-to-Real hardware transfer.

---
> **Note:** For the Vision/Pose tracking component of VIGIL-RQ, please refer to the `vision` or related branches.
