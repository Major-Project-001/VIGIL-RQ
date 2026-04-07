"""
Servo controller for VIGIL-RQ.

Provides a hardware-agnostic interface for commanding 12 servo channels
(3 per leg × 4 legs).  When the serial port is unavailable (development /
simulation mode) all commands are silently logged instead.

Each servo is driven by an angle in degrees [SERVO_MIN_ANGLE … SERVO_MAX_ANGLE].
The driver board expects a simple ASCII protocol::

    "S<channel>:<angle>\\n"

e.g.  "S3:95\\n" sets servo channel 3 to 95 °.
"""

from __future__ import annotations

import time
from typing import Dict, Optional

import config
from utils import get_logger

log = get_logger(__name__)

try:
    import serial  # type: ignore
    _SERIAL_AVAILABLE = True
except ImportError:
    _SERIAL_AVAILABLE = False
    log.warning("pyserial not installed – ServoController running in simulation mode.")


class ServoController:
    """Low-level servo driver.

    Parameters
    ----------
    port : str
        Serial port path (e.g. ``/dev/ttyUSB0``).
    baud : int
        Baud rate.
    simulation : bool
        If *True*, no serial port is opened regardless of availability.
    """

    def __init__(
        self,
        port: str = config.SERVO_PORT,
        baud: int = config.SERVO_BAUD,
        simulation: bool = False,
    ) -> None:
        self._simulation = simulation or not _SERIAL_AVAILABLE
        self._port = port
        self._baud = baud
        self._ser: Optional[object] = None

        # Cache of last commanded angles (channel → degrees)
        self._angles: Dict[int, float] = {}

        if not self._simulation:
            self._open()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _open(self) -> None:
        try:
            self._ser = serial.Serial(self._port, self._baud, timeout=1)
            log.info("Servo serial port opened: %s @ %d", self._port, self._baud)
        except Exception as exc:  # noqa: BLE001
            log.warning("Cannot open servo port %s: %s – switching to simulation.", self._port, exc)
            self._simulation = True

    def close(self) -> None:
        """Release the serial port."""
        if self._ser is not None:
            try:
                self._ser.close()  # type: ignore[union-attr]
            except Exception:  # noqa: BLE001
                pass
        log.info("ServoController closed.")

    def __enter__(self) -> "ServoController":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_angle(self, channel: int, angle: float) -> None:
        """Set servo *channel* to *angle* degrees.

        Angle is clamped to [SERVO_MIN_ANGLE, SERVO_MAX_ANGLE].
        """
        angle = max(config.SERVO_MIN_ANGLE, min(config.SERVO_MAX_ANGLE, angle))
        self._angles[channel] = angle

        if self._simulation:
            log.debug("SIM  servo ch%02d → %.1f °", channel, angle)
            return

        cmd = f"S{channel}:{int(angle)}\n"
        try:
            self._ser.write(cmd.encode())  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            log.error("Servo write error: %s", exc)

    def set_all_neutral(self) -> None:
        """Return all servos to their neutral (90 °) position."""
        for leg, joints in config.SERVO_CHANNELS.items():
            for joint, ch in joints.items():
                self.set_angle(ch, config.SERVO_NEUTRAL_ANGLE)
        log.info("All servos set to neutral.")

    def sweep_to(
        self,
        channel: int,
        target_angle: float,
        step_deg: float = 2.0,
    ) -> None:
        """Move servo *channel* smoothly from its current angle to *target_angle*.

        Parameters
        ----------
        step_deg : float
            Maximum degrees to move per step.
        """
        current = self._angles.get(channel, config.SERVO_NEUTRAL_ANGLE)
        target = max(config.SERVO_MIN_ANGLE, min(config.SERVO_MAX_ANGLE, target_angle))
        direction = 1 if target > current else -1

        while abs(current - target) > step_deg:
            current += direction * step_deg
            self.set_angle(channel, current)
            time.sleep(config.SERVO_STEP_DELAY)

        self.set_angle(channel, target)

    def get_angle(self, channel: int) -> float:
        """Return the last commanded angle for *channel*."""
        return self._angles.get(channel, config.SERVO_NEUTRAL_ANGLE)
