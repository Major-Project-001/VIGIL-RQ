"""
power_monitor.py — INA219 I2C power monitor driver for VIGIL-RQ.

Reads battery voltage, current draw, and power consumption from the
INA219 sensor on the main power rail. Provides low-voltage alerts.

Usage:
    from power_monitor import PowerMonitor
    pm = PowerMonitor()
    data = pm.read()  # {"voltage": 11.4, "current": 3.2, "power": 36.5}
    pm.close()
"""

import time
from config import (
    I2C_BUS, INA219_ADDRESS, INA219_SHUNT_OHMS,
    BATTERY_WARN_V, BATTERY_CUTOFF_V, BATTERY_FULL_V, MAX_CURRENT_A,
)

# Try to import smbus2
try:
    import smbus2
    I2C_AVAILABLE = True
except ImportError:
    I2C_AVAILABLE = False
    print("[POWER] smbus2 not available — running in simulation mode")


# ── INA219 Register addresses ──
REG_CONFIG = 0x00
REG_SHUNT_VOLTAGE = 0x01
REG_BUS_VOLTAGE = 0x02
REG_POWER = 0x03
REG_CURRENT = 0x04
REG_CALIBRATION = 0x05

# Default config: 32V range, ±320mV shunt range, 12-bit, continuous
DEFAULT_CONFIG = 0x399F


class PowerMonitor:
    """
    Reads voltage, current, and power from the INA219 sensor.

    Provides alert states for battery monitoring.
    """

    def __init__(self):
        self._bus = None
        self._address = INA219_ADDRESS
        self._shunt_ohms = INA219_SHUNT_OHMS

        # Alert state
        self._alert = "none"

        if I2C_AVAILABLE:
            try:
                self._bus = smbus2.SMBus(I2C_BUS)
                self._init_sensor()
                print(f"[POWER] INA219 initialised at 0x{self._address:02X}")
            except Exception as e:
                print(f"[POWER] INA219 init failed ({e}) — running without power monitor")
                self._bus = None
                self._current_lsb = 0
                self._power_lsb = 0
        else:
            print("[POWER] Running in simulation mode (no hardware)")

    def _init_sensor(self):
        """Configure the INA219 with default settings."""
        # Write config register
        self._write_register(REG_CONFIG, DEFAULT_CONFIG)
        time.sleep(0.01)

        # Calculate and write calibration register
        # Cal = trunc(0.04096 / (current_lsb * shunt_ohms))
        # current_lsb = max_expected_current / 2^15
        max_current = 20.0  # 20A max expected
        current_lsb = max_current / 32768.0
        cal = int(0.04096 / (current_lsb * self._shunt_ohms))
        self._write_register(REG_CALIBRATION, cal)

        self._current_lsb = current_lsb
        self._power_lsb = current_lsb * 20  # Power LSB = 20 × current_lsb

    def _write_register(self, reg: int, value: int):
        """Write a 16-bit value to an INA219 register."""
        if self._bus:
            high = (value >> 8) & 0xFF
            low = value & 0xFF
            self._bus.write_i2c_block_data(self._address, reg, [high, low])

    def _read_register(self, reg: int) -> int:
        """Read a 16-bit value from an INA219 register."""
        if not self._bus:
            return 0
        try:
            data = self._bus.read_i2c_block_data(self._address, reg, 2)
            value = (data[0] << 8) | data[1]
            return value
        except OSError:
            self._bus = None
            print("[POWER] I2C error — disabling power monitor")
            return 0

    def read(self) -> dict:
        """
        Read voltage, current, and power.

        Returns:
            dict with:
                "voltage":  Bus voltage in volts
                "current":  Current in amps
                "power":    Power in watts
                "alert":    "none", "low_battery", "critical_battery", "overcurrent"
                "percent":  Estimated battery percentage (0–100)
        """
        if not self._bus:
            # Simulation: return fake healthy battery
            return {
                "voltage": 11.4,
                "current": 2.5,
                "power": 28.5,
                "alert": "none",
                "percent": 75,
            }

        # Read bus voltage (register value needs shifting)
        raw_voltage = self._read_register(REG_BUS_VOLTAGE)
        # Bits [15:3] contain voltage, bit 1 = conversion ready, bit 0 = overflow
        voltage = (raw_voltage >> 3) * 0.004  # 4 mV per LSB

        # Read current
        raw_current = self._read_register(REG_CURRENT)
        if raw_current >= 0x8000:
            raw_current -= 0x10000
        current = abs(raw_current * self._current_lsb)

        # Read power
        raw_power = self._read_register(REG_POWER)
        power = raw_power * self._power_lsb

        # Determine alert state
        if voltage <= BATTERY_CUTOFF_V:
            self._alert = "critical_battery"
        elif voltage <= BATTERY_WARN_V:
            self._alert = "low_battery"
        elif current >= MAX_CURRENT_A:
            self._alert = "overcurrent"
        else:
            self._alert = "none"

        # Estimate battery percentage (linear approximation for 3S LiPo)
        # 9.0V = 0%, 12.6V = 100%
        percent = max(0, min(100, int(
            (voltage - BATTERY_CUTOFF_V) / (BATTERY_FULL_V - BATTERY_CUTOFF_V) * 100
        )))

        return {
            "voltage": round(voltage, 2),
            "current": round(current, 2),
            "power": round(power, 2),
            "alert": self._alert,
            "percent": percent,
        }

    @property
    def alert(self) -> str:
        """Current alert state."""
        return self._alert

    def close(self):
        """Close the I2C bus."""
        if self._bus:
            self._bus.close()
            self._bus = None
            print("[POWER] Connection closed")
