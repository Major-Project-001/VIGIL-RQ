"""
spi_driver.py — SPI master driver for RPi 4B → Tang Nano 9K FPGA communication.

Sends servo pulse-width commands to the FPGA over SPI. Each command is a
3-byte frame: [channel_id (8-bit)] [pulse_us_hi] [pulse_us_lo].

The FPGA's spi_slave.sv decodes these frames and routes them to the
corresponding PWM channel.

Usage:
    from spi_driver import SpiServoDriver
    driver = SpiServoDriver()
    driver.set_servo(0, 1500)           # Channel 0 → 1500 µs (neutral)
    driver.set_all_servos([1500]*12)    # All channels → neutral
    driver.close()
"""

import threading
import math
import time
from config import (
    SPI_BUS, SPI_DEVICE, SPI_SPEED_HZ, SPI_MODE,
    SERVO_CHANNELS, SERVO_PULSE_MIN_US, SERVO_PULSE_MAX_US,
    SERVO_PULSE_NEUTRAL_US, SERVO_ANGLE_RANGE_DEG,
    SERVO_ANGLE_MIN_RAD, SERVO_ANGLE_MAX_RAD, SERVO_OFFSETS,
    SERVO_DIRECTION, JOINT_LIMITS,
)

# Try to import spidev (only available on RPi)
try:
    import spidev
    SPI_AVAILABLE = True
except ImportError:
    SPI_AVAILABLE = False
    print("[SPI] spidev not available — running in simulation mode")


class SpiServoDriver:
    """
    SPI master driver for sending servo commands to the FPGA.

    Thread-safe: all SPI transactions are protected by a lock.
    Falls back to print-only simulation mode if spidev is not installed.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._spi = None

        if SPI_AVAILABLE:
            self._spi = spidev.SpiDev()
            self._spi.open(SPI_BUS, SPI_DEVICE)
            self._spi.max_speed_hz = SPI_SPEED_HZ
            self._spi.mode = SPI_MODE
            print(f"[SPI] Opened SPI{SPI_BUS}.{SPI_DEVICE} @ {SPI_SPEED_HZ/1e6:.1f} MHz")
        else:
            print("[SPI] Running in simulation mode (no hardware)")

    def set_servo(self, channel_id: int, pulse_us: int):
        """
        Send a single servo command to the FPGA.

        Args:
            channel_id: PWM channel (0–11)
            pulse_us:   Pulse width in microseconds (500–2500)
        """
        # Clamp
        pulse_us = max(SERVO_PULSE_MIN_US, min(SERVO_PULSE_MAX_US, pulse_us))
        channel_id = max(0, min(11, channel_id))

        # Build 3-byte frame: [channel_id, pulse_hi, pulse_lo]
        frame = [
            channel_id & 0xFF,
            (pulse_us >> 8) & 0xFF,
            pulse_us & 0xFF,
        ]

        with self._lock:
            if self._spi:
                self._spi.xfer2(frame)
                # Inter-frame gap: give FPGA time to process CS rising edge
                # before the next frame. Without this, rapid slider updates
                # can cause garbled frames → jitter on other channels.
                time.sleep(0.0001)  # 100 µs


    def set_all_servos(self, pulse_widths: list):
        """
        Update all 12 servo channels.

        Args:
            pulse_widths: List of 12 pulse widths in µs (index = channel)
        """
        assert len(pulse_widths) == 12, f"Expected 12 values, got {len(pulse_widths)}"
        for ch, pw in enumerate(pulse_widths):
            self.set_servo(ch, pw)

    def set_joint_angles(self, angles: dict):
        """
        Set servo positions from joint angles (radians).

        Args:
            angles: dict of {joint_name: angle_rad}
                    e.g. {"fl_hip": 0.0, "fl_thigh": -0.3, ...}
        """
        for name, angle in angles.items():
            if name not in SERVO_CHANNELS:
                continue

            # SAFETY: hip servos locked at neutral — do not move
            joint_type = name.split("_")[-1]
            if joint_type == "hip":
                continue

            channel = SERVO_CHANNELS[name]

            # Limit clamping
            lo, hi = JOINT_LIMITS.get(joint_type, (-math.pi, math.pi))
            angle = max(lo, min(hi, angle))

            # Convert angle to pulse width
            pulse_us = self.angle_to_pulse(angle, name)
            self.set_servo(channel, pulse_us)

    def set_all_neutral(self):
        """Set all servos to neutral position (1500 µs)."""
        self.set_all_servos([SERVO_PULSE_NEUTRAL_US] * 12)

    @staticmethod
    def angle_to_pulse(angle_rad: float, joint_name: str = "") -> int:
        """
        Convert a joint angle (radians) to a servo pulse width (µs).

        The DS3218 maps 500–2500 µs to its full angle range.
        0 rad → 1500 µs (neutral)

        Args:
            angle_rad:  Target angle in radians
            joint_name: Joint name (for per-servo offset lookup)

        Returns:
            Pulse width in microseconds (500–2500)
        """
        # Linear mapping: angle → pulse
        # angle_range = SERVO_ANGLE_MAX_RAD - SERVO_ANGLE_MIN_RAD
        # pulse_range = SERVO_PULSE_MAX_US - SERVO_PULSE_MIN_US
        # normalised = (angle - SERVO_ANGLE_MIN_RAD) / angle_range
        # pulse = SERVO_PULSE_MIN_US + normalised * pulse_range

        # Simplified: 0 rad = 1500 µs, scale = pulse_range / angle_range
        angle_range = SERVO_ANGLE_MAX_RAD - SERVO_ANGLE_MIN_RAD
        pulse_range = SERVO_PULSE_MAX_US - SERVO_PULSE_MIN_US
        scale = pulse_range / angle_range  # µs per radian

        # Apply servo direction (mirror-mounted servos)
        direction = SERVO_DIRECTION.get(joint_name, 1)
        angle_rad = angle_rad * direction

        pulse_us = int(SERVO_PULSE_NEUTRAL_US + angle_rad * scale)

        # Apply per-servo calibration offset
        offset = SERVO_OFFSETS.get(joint_name, 0)
        pulse_us += offset

        # Clamp to valid range
        pulse_us = max(SERVO_PULSE_MIN_US, min(SERVO_PULSE_MAX_US, pulse_us))

        return pulse_us

    def close(self):
        """Close the SPI connection."""
        with self._lock:
            if self._spi:
                self.set_all_neutral()
                self._spi.close()
                self._spi = None
                print("[SPI] Connection closed")
