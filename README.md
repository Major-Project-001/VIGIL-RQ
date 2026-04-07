# VIGIL-RQ – Quadruped Robot Vision & Navigation System

VIGIL-RQ is a Python-based control stack for a 12-DOF quadruped robot
that navigates its environment using a monocular camera, Kalman-filtered
object tracking, and an obstacle-aware path planner.

---

## Project Structure

```
VIGIL-RQ/
├── main.py                  # Entry point
├── config.py                # Central configuration
├── requirements.txt
│
├── vision/
│   ├── detector.py          # YOLO / HOG object detection with stability filter
│   ├── tracker.py           # Centroid + Kalman multi-object tracker
│   └── depth_estimator.py   # Monocular depth from bounding-box width
│
├── robot/
│   ├── servo.py             # Servo driver (serial / simulation)
│   ├── gait.py              # Trot / walk / crawl gait engine + IK
│   └── controller.py        # High-level motion commands + visual servoing
│
├── navigation/
│   ├── obstacle_avoidance.py  # Proximity-based evasion decisions
│   └── path_planner.py        # FIFO waypoint planner
│
├── utils/
│   ├── logger.py            # Rotating-file + console logger
│   ├── kalman_filter.py     # 2-D constant-velocity Kalman filter
│   └── pid_controller.py    # Discrete PID with anti-windup
│
└── tests/
    ├── test_utils.py
    ├── test_vision.py
    └── test_navigation.py
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
# For live camera support also install one of:
pip install opencv-python           # includes GUI
pip install opencv-python-headless  # for headless/server use
```

### 2. Run in simulation mode (no hardware required)

```bash
python main.py --simulation
```

### 3. Run on real hardware

```bash
python main.py --gait trot
```

### Available flags

| Flag | Default | Description |
|------|---------|-------------|
| `--simulation` | `False` | Disable real servo communication |
| `--camera INT` | `0` | Camera device index |
| `--gait STR` | `trot` | Gait pattern: `trot`, `walk`, `crawl` |
| `--debug` | `False` | Enable DEBUG-level log output |

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VIGIL_CAMERA_INDEX` | `0` | Camera index |
| `VIGIL_SERVO_PORT` | `/dev/ttyUSB0` | Serial port for servo board |
| `VIGIL_SERVO_BAUD` | `115200` | Baud rate |
| `VIGIL_MODEL_PATH` | `models/yolo_vigil.weights` | YOLO weights file |
| `VIGIL_MODEL_CONFIG` | `models/yolo_vigil.cfg` | YOLO config file |
| `VIGIL_CLASSES_PATH` | `models/classes.txt` | Class-name list |
| `VIGIL_LOG_LEVEL` | `INFO` | Logging level |
| `VIGIL_LOG_FILE` | `vigil_rq.log` | Log file path |
| `VIGIL_DEBUG` | `false` | Set `true` to enable debug mode |

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Accuracy & Robustness Improvements

| Feature | Location | Description |
|---------|----------|-------------|
| Temporal stability filter | `vision/detector.py` | Detection must appear in N consecutive frames |
| Kalman-filtered tracking | `vision/tracker.py` | Smooths bounding-box jitter |
| EMA depth smoothing | `vision/depth_estimator.py` | Reduces depth estimate noise |
| Hungarian assignment | `vision/tracker.py` | Optimal detection-to-track matching |
| PID heading control | `robot/controller.py` | Smooth visual servoing |
| PID anti-windup | `utils/pid_controller.py` | Prevents integral saturation |
| NMS post-processing | `vision/detector.py` | Removes duplicate YOLO boxes |
| Evasion direction choice | `navigation/obstacle_avoidance.py` | Turns away from densest obstacle cluster |

---

## Hardware Notes

- **Servos**: 12-channel PWM driver connected via UART (`/dev/ttyUSB0` by default).
  Protocol: `S<channel>:<angle>\n`  (angle in degrees, 0–180).
- **Camera**: Any OpenCV-compatible USB or CSI camera.
- **YOLO model**: Place weights, cfg, and classes files in `models/` and set
  the `VIGIL_MODEL_PATH`, `VIGIL_MODEL_CONFIG`, `VIGIL_CLASSES_PATH`
  environment variables (or edit `config.py`).  Without the model files the
  system falls back to HOG-based pedestrian detection.
