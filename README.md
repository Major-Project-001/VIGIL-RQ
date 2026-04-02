# 🦾 VIGIL-RQ — Vision Module

> **Real-time human pose perception for quadruped robot navigation**

VIGIL-RQ (**Vi**sion-**G**uided **I**ntelligent **L**ocomotion for **R**obotic **Q**uadrupeds) is the perception layer of a quadruped robotics platform. It uses a webcam and [MediaPipe Pose](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker) to track a human operator's body in real time and convert their position into high-level directional commands (`LEFT`, `RIGHT`, `CENTER`) that will ultimately drive FPGA-based motor control.

---

## 📸 What It Does

1. **Captures** live video from a webcam via OpenCV.
2. **Detects** 33 human pose landmarks using MediaPipe's Pose Landmarker (Tasks API).
3. **Extracts** the nose keypoint's normalized x-coordinate (0.0 – 1.0).
4. **Decides** a movement command based on configurable thresholds:
   | Nose X Position | Command |
   |---|---|
   | `< 0.4` | `LEFT` |
   | `> 0.6` | `RIGHT` |
   | `0.4 – 0.6` | `CENTER` |
5. **Displays** an annotated video feed with skeleton overlay and command text.
6. **Logs** every decision to the console for debugging.

---

## 🏗️ Architecture

```
Camera → Vision (MediaPipe) → Decision Logic → Display / Console
                                    ↓
                          (future) FPGA → Motors
```

The codebase follows a strict **separation-of-concerns** pattern to keep each layer independently testable and swappable:

```
VIGIL-RQ/
│
├── main.py                    # Pipeline orchestrator
│
├── vision/
│   ├── pose_detector.py       # MediaPipe Pose Landmarker wrapper
│   └── hand_detector.py       # Hand tracking (placeholder for future use)
│
├── logic/
│   └── decision.py            # Landmark coordinates → directional commands
│
├── utils/
│   └── display.py             # Skeleton drawing, text overlay, window management
│
├── config/
│   └── settings.py            # Thresholds, camera params, UI constants
│
├── pose_landmarker_lite.task   # MediaPipe model binary
├── basic.py                    # Minimal single-file prototype (reference)
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Start

### Prerequisites

- Python 3.10+
- A webcam connected to your machine

### Installation

```bash
# Clone the repository
git clone https://github.com/Major-Project-001/VIGIL-RQ.git
cd VIGIL-RQ

# (Recommended) Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

- A window titled **"Quadruped Vision Module"** will open showing the annotated camera feed.
- Directional commands are printed to the console in real time.
- Press **`q`** to quit.

> **Note:** By default the camera index is set to `1`. If your webcam is not detected, change `CAMERA_INDEX` in `config/settings.py` to `0`.

---

## 🔧 Configuration

All tunable parameters live in [`config/settings.py`](config/settings.py):

| Parameter | Default | Description |
|---|---|---|
| `LEFT_THRESHOLD` | `0.4` | Nose x below this → `LEFT` |
| `RIGHT_THRESHOLD` | `0.6` | Nose x above this → `RIGHT` |
| `CAMERA_INDEX` | `1` | OpenCV camera device index |
| `FRAME_WIDTH` | `640` | Capture width in pixels |
| `FRAME_HEIGHT` | `480` | Capture height in pixels |
| `FONT_SCALE` | `1.0` | Overlay text size |
| `FONT_THICKNESS` | `2` | Overlay text thickness |
| `TEXT_COLOR` | `(0, 255, 0)` | Overlay text color (BGR green) |

---

## 🧩 Module Details

### `vision/pose_detector.py` — PoseDetector

Wraps the **MediaPipe Tasks API** (not the legacy `mp.solutions` interface) for pose detection.

- **`__init__(model_path)`** — Loads the `.task` model and creates a `PoseLandmarker` in `IMAGE` running mode.
- **`process_frame(frame)`** — Accepts a BGR OpenCV frame, converts to RGB, and returns a `PoseLandmarkerResult`.
- **`get_keypoint(detection_result, index)`** — Returns `(x, y)` normalized coordinates for a given landmark index, or `None` if not detected.

### `logic/decision.py` — get_direction

Pure function. Takes a normalized nose x-coordinate and returns `"LEFT"`, `"RIGHT"`, or `"CENTER"` based on the configured thresholds.

### `utils/display.py` — Drawing Utilities

- **`draw_landmarks(frame, results)`** — Renders a skeleton overlay (keypoints + connections) using raw OpenCV drawing, independent of MediaPipe's drawing utils.
- **`overlay_direction(frame, direction)`** — Stamps the current command (`CMD: LEFT`, etc.) onto the frame.
- **`show_frame(frame)`** — Displays the frame in the named OpenCV window.

### `main.py` — Pipeline

The main loop ties everything together:

```
Capture Frame → Detect Pose → Extract Nose → Decide Direction → Draw & Display
```

---

## 🔜 Roadmap

This vision module is the first stage of a full robotics pipeline:

- [ ] **YOLO Integration** — Object detection alongside (or replacing) pose tracking
- [ ] **Hand Gesture Control** — Activate the `hand_detector.py` stub for gesture-based commands
- [ ] **Serial / Socket Output** — Send commands to FPGA motor controller in real time
- [ ] **Reinforcement Learning Bridge** — Feed perception data into a PPO locomotion policy
- [ ] **Multi-person Tracking** — Track and follow a specific operator in crowded scenes

---

## 🧠 System Context

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Webcam     │────▶│  Vision      │────▶│  Decision    │────▶│  FPGA        │
│   (Laptop)   │     │  (MediaPipe) │     │  (Logic)     │     │  (Motors)    │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

- **Vision** runs on a laptop/PC for compute.
- **Decision logic** is lightweight and CPU-efficient by design.
- **FPGA** receives commands and drives the quadruped's servos.

---

## 📄 License

This project is part of an academic major project. Refer to your institution's guidelines for usage and distribution.
