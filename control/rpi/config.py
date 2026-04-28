"""
config.py — Central configuration for the VIGIL-RQ remote control system.

All constants, tuning parameters, pin mappings, and servo definitions
live here. Adjust these values to match your physical robot.
"""

# ══════════════════════════════════════════════════════════════════════════════
# NETWORK
# ══════════════════════════════════════════════════════════════════════════════

WIFI_SSID = "VIGIL-RQ"
WIFI_PASSWORD = "vigilrq2026"       # Change for production
WIFI_CHANNEL = 6

WEBSOCKET_HOST = "0.0.0.0"
WEBSOCKET_PORT = 8765
WEB_APP_PORT = 80
WEB_APP_DIR = "../app"              # Relative to rpi/ directory

TELEMETRY_RATE_HZ = 20              # How often to broadcast telemetry (Hz)


# ══════════════════════════════════════════════════════════════════════════════
# SPI — Raspberry Pi 4B → Tang Nano 9K FPGA
# ══════════════════════════════════════════════════════════════════════════════

SPI_BUS = 0
SPI_DEVICE = 0                      # CE0 (GPIO 8)
SPI_SPEED_HZ = 1_000_000            # 1 MHz
SPI_MODE = 0b00                     # CPOL=0, CPHA=0


# ══════════════════════════════════════════════════════════════════════════════
# I2C — Sensors
# ══════════════════════════════════════════════════════════════════════════════

I2C_BUS = 1                         # RPi 4B default I2C bus

# MPU9250 IMU
IMU_ADDRESS = 0x68                   # Default; use 0x69 if AD0 is HIGH
IMU_SAMPLE_RATE_HZ = 50

# INA219 Power Monitor
INA219_ADDRESS = 0x40                # Default; adjust if A0/A1 jumpers changed
INA219_SHUNT_OHMS = 0.1             # Shunt resistor value (Ω)


# ══════════════════════════════════════════════════════════════════════════════
# SERVO CHANNEL MAPPING — FPGA PWM channel ID → Joint name
# ══════════════════════════════════════════════════════════════════════════════
# Maps the FPGA PWM channel index (0–11) to the robot joint name.
# This must match the pin mapping in tangnano9k.cst.

SERVO_CHANNELS = {
    "fl_hip":   0,
    "fl_thigh": 1,
    "fl_knee":  2,
    "fr_hip":   3,
    "fr_thigh": 4,
    "fr_knee":  5,
    "rl_hip":   6,
    "rl_thigh": 7,
    "rl_knee":  8,
    "rr_hip":   9,
    "rr_thigh": 10,
    "rr_knee":  11,
}

# Reverse mapping: channel ID → joint name
CHANNEL_NAMES = {v: k for k, v in SERVO_CHANNELS.items()}


# ══════════════════════════════════════════════════════════════════════════════
# DS3218 SERVO SPECIFICATIONS
# ══════════════════════════════════════════════════════════════════════════════

SERVO_PULSE_MIN_US = 500             # Minimum pulse width (µs)
SERVO_PULSE_MAX_US = 2500            # Maximum pulse width (µs)
SERVO_PULSE_NEUTRAL_US = 1500        # Neutral / center (µs)
SERVO_FREQ_HZ = 50                   # PWM frequency (Hz)

# Angle range: the DS3218 covers 180° over 500–2500 µs
SERVO_ANGLE_RANGE_DEG = 180.0        # Total rotation range in degrees
SERVO_ANGLE_MIN_RAD = -1.5708        # -90° in radians
SERVO_ANGLE_MAX_RAD = 1.5708         # +90° in radians


# ══════════════════════════════════════════════════════════════════════════════
# JOINT LIMITS (radians) — Physical constraints per joint type
# ══════════════════════════════════════════════════════════════════════════════
# These must match the URDF joint limits from robot.urdf

JOINT_LIMITS = {
    "hip":   (-0.78, 0.78),          # ±45°
    "thigh": (-1.57, 1.57),          # ±90°
    "knee":  (-1.57, 0.50),          # -90° to +28.6° (within ±90° servo range)
}

# Per-servo neutral offset (µs) — calibrate each servo individually
# Add/subtract from 1500 µs to correct for mechanical misalignment
SERVO_OFFSETS = {name: 0 for name in SERVO_CHANNELS}


# ══════════════════════════════════════════════════════════════════════════════
# GAIT PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════

import math

GAIT_UPDATE_RATE_HZ = 50             # How often gait engine ticks

# Walk gait
WALK_FREQ_HZ = 1.0                   # Step frequency
WALK_HIP_AMP = 0.15                  # Hip sway amplitude (rad)
WALK_THIGH_AMP = 0.2                 # Thigh swing amplitude (rad)
WALK_THIGH_OFFSET = 0.0              # Thigh neutral angle (rad)
WALK_KNEE_AMP = 0.3                  # Knee lift amplitude (rad)
WALK_KNEE_OFFSET = -0.3              # Knee neutral angle (rad)

# Run gait (faster, larger amplitudes)
RUN_FREQ_HZ = 2.0
RUN_HIP_AMP = 0.20
RUN_THIGH_AMP = 0.52
RUN_THIGH_OFFSET = 0.0
RUN_KNEE_AMP = 0.65
RUN_KNEE_OFFSET = -0.35

# Static pose presets (radians)
LEGS = ["fl", "fr", "rl", "rr"]
JOINTS = ["hip", "thigh", "knee"]

POSE_STAND = {f"{leg}_{jt}": 0.0 for leg in LEGS for jt in JOINTS}

POSE_SIT = {
    **{f"{l}_hip": 0.0 for l in LEGS},
    **{f"{l}_thigh": 0.5 for l in LEGS},
    **{f"{l}_knee": -1.2 for l in LEGS},
}

POSE_REST = {f"{leg}_{jt}": 0.0 for leg in LEGS for jt in JOINTS}


# ══════════════════════════════════════════════════════════════════════════════
# SAFETY
# ══════════════════════════════════════════════════════════════════════════════

WATCHDOG_TIMEOUT_S = 10.0            # Seconds with no command → auto-rest
BATTERY_WARN_V = 9.6                 # Low battery warning (3.2V/cell)
BATTERY_CUTOFF_V = 9.0               # Critical: disable servos (3.0V/cell)
BATTERY_FULL_V = 12.6                # Fully charged (4.2V/cell)
MAX_CURRENT_A = 15.0                 # Over-current alert threshold


# ══════════════════════════════════════════════════════════════════════════════
# ALERT GPIO PINS (BCM numbering)
# ══════════════════════════════════════════════════════════════════════════════

BUZZER_PIN = 18                      # GPIO 18 (PWM capable)
RGB_RED_PIN = 17                     # GPIO 17
RGB_GREEN_PIN = 27                   # GPIO 27
RGB_BLUE_PIN = 22                    # GPIO 22
