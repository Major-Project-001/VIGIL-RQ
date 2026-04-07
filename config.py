"""
VIGIL-RQ Configuration
Central configuration for the quadruped robot, vision pipeline, and navigation.
"""

import os

# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------
PROJECT_NAME = "VIGIL-RQ"
VERSION = "1.0.0"
DEBUG = os.environ.get("VIGIL_DEBUG", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Camera / Vision
# ---------------------------------------------------------------------------
CAMERA_INDEX = int(os.environ.get("VIGIL_CAMERA_INDEX", "0"))
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_RATE = 30  # target FPS

# Detection model – set VIGIL_MODEL_PATH to override
DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "yolo_vigil.weights")
MODEL_PATH = os.environ.get("VIGIL_MODEL_PATH", DEFAULT_MODEL_PATH)
MODEL_CONFIG_PATH = os.environ.get(
    "VIGIL_MODEL_CONFIG", os.path.join(os.path.dirname(__file__), "models", "yolo_vigil.cfg")
)
MODEL_CLASSES_PATH = os.environ.get(
    "VIGIL_CLASSES_PATH", os.path.join(os.path.dirname(__file__), "models", "classes.txt")
)

# Confidence / NMS thresholds
DETECTION_CONFIDENCE_THRESHOLD = 0.5
DETECTION_NMS_THRESHOLD = 0.4

# Temporal consistency filter – detections must persist this many frames
DETECTION_STABILITY_FRAMES = 3

# Depth estimation
DEPTH_FOCAL_LENGTH_PX = 600.0       # camera focal length in pixels
DEPTH_KNOWN_OBJECT_WIDTH_M = 0.4    # reference object real width (metres)

# ---------------------------------------------------------------------------
# Tracking
# ---------------------------------------------------------------------------
TRACKER_MAX_DISAPPEARED = 10   # frames before a tracked object is dropped
TRACKER_MAX_DISTANCE = 150     # max pixel distance to associate detections

# Kalman filter process / measurement noise
KALMAN_PROCESS_NOISE = 1e-4
KALMAN_MEASUREMENT_NOISE = 1e-2

# ---------------------------------------------------------------------------
# Robot Hardware
# ---------------------------------------------------------------------------
# I²C / serial port for the servo driver board
SERVO_PORT = os.environ.get("VIGIL_SERVO_PORT", "/dev/ttyUSB0")
SERVO_BAUD = int(os.environ.get("VIGIL_SERVO_BAUD", "115200"))

# Servo channel layout (leg order: FL, FR, RL, RR)
# Each leg uses 3 servos: hip, thigh, calf
SERVO_CHANNELS = {
    "FL": {"hip": 0, "thigh": 1,  "calf": 2},
    "FR": {"hip": 3, "thigh": 4,  "calf": 5},
    "RL": {"hip": 6, "thigh": 7,  "calf": 8},
    "RR": {"hip": 9, "thigh": 10, "calf": 11},
}

SERVO_NEUTRAL_ANGLE = 90    # degrees
SERVO_MIN_ANGLE = 0
SERVO_MAX_ANGLE = 180
SERVO_STEP_DELAY = 0.01     # seconds between incremental moves

# ---------------------------------------------------------------------------
# Kinematics
# ---------------------------------------------------------------------------
# Link lengths in metres
LINK_COXA = 0.055
LINK_FEMUR = 0.105
LINK_TIBIA = 0.120

# Default body height above ground (metres)
DEFAULT_BODY_HEIGHT = 0.12

# ---------------------------------------------------------------------------
# Gait
# ---------------------------------------------------------------------------
GAIT_STEP_HEIGHT = 0.04      # metres – how high to lift each foot
GAIT_STEP_LENGTH = 0.06      # metres – forward stride length
GAIT_CYCLE_PERIOD = 0.8      # seconds per full gait cycle
GAIT_DEFAULT = "trot"        # "trot" | "walk" | "crawl"

# ---------------------------------------------------------------------------
# Navigation / Obstacle Avoidance
# ---------------------------------------------------------------------------
OBSTACLE_STOP_DISTANCE = 0.30     # metres – stop if obstacle closer than this
OBSTACLE_WARN_DISTANCE = 0.60     # metres – slow-down zone
ROBOT_TURN_SPEED = 0.5            # normalised [0, 1]
ROBOT_FORWARD_SPEED = 1.0         # normalised [0, 1]

# ---------------------------------------------------------------------------
# PID – heading control
# ---------------------------------------------------------------------------
PID_KP = 0.8
PID_KI = 0.05
PID_KD = 0.1
PID_OUTPUT_LIMIT = 1.0

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = os.environ.get("VIGIL_LOG_LEVEL", "INFO")
LOG_FILE = os.environ.get("VIGIL_LOG_FILE", "vigil_rq.log")
LOG_MAX_BYTES = 5 * 1024 * 1024   # 5 MB
LOG_BACKUP_COUNT = 3
