"""
imu_reader.py — MPU6050 / MPU9250 I2C driver for the VIGIL-RQ quadruped.

Reads accelerometer and gyroscope data from the IMU and computes
roll, pitch, yaw using a complementary filter.

Usage:
    from imu_reader import ImuReader
    imu = ImuReader()
    data = imu.read()  # {"roll": float, "pitch": float, "yaw": float}
    imu.close()
"""

import time
import math
from config import I2C_BUS, IMU_ADDRESS

# Try to import smbus2 (only available on RPi)
try:
    import smbus2
    I2C_AVAILABLE = True
except ImportError:
    I2C_AVAILABLE = False
    print("[IMU] smbus2 not available — running in simulation mode")


# ── MPU6050/9250 Register addresses ──
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43
WHO_AM_I = 0x75

# Scale factors
ACCEL_SCALE = 16384.0       # ±2g mode (default)
GYRO_SCALE = 131.0          # ±250°/s mode (default)


class ImuReader:
    """
    Reads orientation data from MPU6050/MPU9250 over I2C.

    Uses a complementary filter to fuse accelerometer and gyroscope
    data into stable roll, pitch, yaw estimates.
    """

    def __init__(self, alpha: float = 0.98):
        """
        Args:
            alpha: Complementary filter weight (0.0–1.0).
                   Higher = trust gyro more (less drift correction).
        """
        self._bus = None
        self._address = IMU_ADDRESS
        self._alpha = alpha
        self._last_time = None

        # Orientation state (degrees)
        self._roll = 0.0
        self._pitch = 0.0
        self._yaw = 0.0

        if I2C_AVAILABLE:
            self._bus = smbus2.SMBus(I2C_BUS)
            self._init_sensor()
            print(f"[IMU] Initialised at address 0x{self._address:02X}")
        else:
            print("[IMU] Running in simulation mode (no hardware)")

    def _init_sensor(self):
        """Wake up the MPU6050/9250 and configure default settings."""
        # Wake up (clear sleep bit)
        self._bus.write_byte_data(self._address, PWR_MGMT_1, 0x00)
        time.sleep(0.1)

        # Read WHO_AM_I for identification
        who = self._bus.read_byte_data(self._address, WHO_AM_I)
        if who == 0x68:
            print("[IMU] Detected MPU6050")
        elif who == 0x71:
            print("[IMU] Detected MPU9250")
        else:
            print(f"[IMU] Unknown device: WHO_AM_I = 0x{who:02X}")

    def _read_raw(self, reg: int) -> int:
        """Read a 16-bit signed value from two consecutive registers."""
        if not self._bus:
            return 0
        high = self._bus.read_byte_data(self._address, reg)
        low = self._bus.read_byte_data(self._address, reg + 1)
        value = (high << 8) | low
        if value >= 0x8000:
            value -= 0x10000
        return value

    def read(self) -> dict:
        """
        Read and compute orientation.

        Returns:
            dict with "roll", "pitch", "yaw" in degrees
        """
        now = time.time()
        if self._last_time is None:
            self._last_time = now
            dt = 0.02  # Assume 50 Hz first call
        else:
            dt = now - self._last_time
            self._last_time = now

        if not self._bus:
            # Simulation: return zeros
            return {"roll": 0.0, "pitch": 0.0, "yaw": 0.0}

        # Read raw accelerometer (3 axes)
        ax = self._read_raw(ACCEL_XOUT_H) / ACCEL_SCALE
        ay = self._read_raw(ACCEL_XOUT_H + 2) / ACCEL_SCALE
        az = self._read_raw(ACCEL_XOUT_H + 4) / ACCEL_SCALE

        # Read raw gyroscope (3 axes)
        gx = self._read_raw(GYRO_XOUT_H) / GYRO_SCALE
        gy = self._read_raw(GYRO_XOUT_H + 2) / GYRO_SCALE
        gz = self._read_raw(GYRO_XOUT_H + 4) / GYRO_SCALE

        # Accelerometer-based angles (only roll and pitch are reliable)
        accel_roll = math.degrees(math.atan2(ay, az))
        accel_pitch = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))

        # Complementary filter: fuse gyro rate with accel angle
        self._roll = self._alpha * (self._roll + gx * dt) + (1 - self._alpha) * accel_roll
        self._pitch = self._alpha * (self._pitch + gy * dt) + (1 - self._alpha) * accel_pitch
        self._yaw += gz * dt  # Yaw drifts (no magnetometer correction)

        return {
            "roll": round(self._roll, 2),
            "pitch": round(self._pitch, 2),
            "yaw": round(self._yaw, 2),
        }

    def close(self):
        """Close the I2C bus."""
        if self._bus:
            self._bus.close()
            self._bus = None
            print("[IMU] Connection closed")
