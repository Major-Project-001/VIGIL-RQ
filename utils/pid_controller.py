"""
Discrete-time PID controller with anti-windup and output clamping.

Typical use – heading/speed control for VIGIL-RQ.

Example::

    pid = PIDController(kp=0.8, ki=0.05, kd=0.1, output_limit=1.0)
    # inside the control loop:
    correction = pid.update(setpoint=0.0, measurement=heading_error)
"""

import time


class PIDController:
    """PID controller with integral anti-windup and derivative filtering.

    Parameters
    ----------
    kp, ki, kd : float
        Proportional, integral, and derivative gains.
    output_limit : float
        Symmetric clamp on the output  ( -limit … +limit ).
    derivative_filter_coeff : float
        Low-pass coefficient N for the derivative term (0 < N < 1).
        Higher values → less filtering (faster response but noisier).
    """

    def __init__(
        self,
        kp: float = 1.0,
        ki: float = 0.0,
        kd: float = 0.0,
        output_limit: float = 1.0,
        derivative_filter_coeff: float = 0.1,
    ) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limit = abs(output_limit)
        self._alpha = derivative_filter_coeff  # low-pass coefficient

        self._integral = 0.0
        self._prev_error = 0.0
        self._filtered_derivative = 0.0
        self._last_time: float | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Clear integrator and derivative memory."""
        self._integral = 0.0
        self._prev_error = 0.0
        self._filtered_derivative = 0.0
        self._last_time = None

    def update(self, setpoint: float, measurement: float, dt: float | None = None) -> float:
        """Compute the PID output.

        Parameters
        ----------
        setpoint : float
            Desired value.
        measurement : float
            Current measured value.
        dt : float | None
            Time step in seconds.  If *None* the wall-clock interval since the
            last call is used.

        Returns
        -------
        float
            Control output clamped to ``[-output_limit, +output_limit]``.
        """
        now = time.monotonic()
        if dt is None:
            dt = (now - self._last_time) if self._last_time is not None else 0.0
        self._last_time = now

        error = setpoint - measurement

        # Proportional
        proportional = self.kp * error

        # Integral with anti-windup (clamp before accumulating)
        if dt > 0:
            self._integral += error * dt
        integral_term = self.ki * self._integral

        # Clamp integral to prevent windup
        integral_term = max(-self.output_limit, min(self.output_limit, integral_term))

        # Derivative with low-pass filter
        raw_derivative = (error - self._prev_error) / dt if dt > 0 else 0.0
        self._filtered_derivative = (
            self._alpha * raw_derivative
            + (1.0 - self._alpha) * self._filtered_derivative
        )
        derivative_term = self.kd * self._filtered_derivative

        self._prev_error = error

        output = proportional + integral_term + derivative_term
        return max(-self.output_limit, min(self.output_limit, output))
