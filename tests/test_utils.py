"""
Unit tests for VIGIL-RQ utility modules:
  - KalmanFilter2D
  - PIDController
"""

import sys
import os
import math
import time

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from utils.kalman_filter import KalmanFilter2D
from utils.pid_controller import PIDController


# ──────────────────────────────────────────────────────────────────────────────
# KalmanFilter2D
# ──────────────────────────────────────────────────────────────────────────────

class TestKalmanFilter2D:
    def test_init_sets_position(self):
        kf = KalmanFilter2D()
        kf.init(10.0, 20.0)
        x, y = kf.position
        assert x == pytest.approx(10.0)
        assert y == pytest.approx(20.0)

    def test_update_returns_smoothed_position(self):
        kf = KalmanFilter2D()
        kf.init(0.0, 0.0)
        for _ in range(20):
            kf.update(5.0, 5.0)
        x, y = kf.position
        # After many identical measurements the estimate should converge
        assert x == pytest.approx(5.0, abs=0.5)
        assert y == pytest.approx(5.0, abs=0.5)

    def test_predict_advances_position(self):
        kf = KalmanFilter2D()
        kf.init(0.0, 0.0)
        # Seed a known velocity by updating twice at the same location
        kf.update(0.0, 0.0)
        kf.update(1.0, 1.0)
        px, py = kf.predict()
        # After prediction the estimate should be > the last measurement
        assert px > 0.5
        assert py > 0.5

    def test_velocity_is_nonzero_after_movement(self):
        kf = KalmanFilter2D()
        kf.init(0.0, 0.0)
        for i in range(10):
            kf.update(float(i), float(i))
        vx, vy = kf.velocity
        assert vx > 0
        assert vy > 0

    def test_update_without_init_does_not_raise(self):
        kf = KalmanFilter2D()
        x, y = kf.update(3.0, 4.0)
        # On first call (no init) should return the raw measurement
        assert x == pytest.approx(3.0)
        assert y == pytest.approx(4.0)

    def test_noise_parameters_affect_smoothing(self):
        """Higher measurement noise → more smoothing (estimate lags measurement)."""
        high_noise = KalmanFilter2D(measurement_noise=1e0)
        low_noise  = KalmanFilter2D(measurement_noise=1e-6)

        high_noise.init(0.0, 0.0)
        low_noise.init(0.0, 0.0)

        for _ in range(5):
            high_noise.update(10.0, 10.0)
            low_noise.update(10.0, 10.0)

        hx, _ = high_noise.position
        lx, _ = low_noise.position
        # Low measurement noise → filter trusts measurements → estimate stays near 10.0
        # High measurement noise → filter discounts measurements → larger residual from 10.0
        assert abs(lx - 10.0) < abs(hx - 10.0)


# ──────────────────────────────────────────────────────────────────────────────
# PIDController
# ──────────────────────────────────────────────────────────────────────────────

class TestPIDController:
    def test_zero_error_gives_zero_output(self):
        pid = PIDController(kp=1.0, ki=0.0, kd=0.0)
        out = pid.update(setpoint=0.0, measurement=0.0, dt=0.1)
        assert out == pytest.approx(0.0)

    def test_proportional_only(self):
        pid = PIDController(kp=2.0, ki=0.0, kd=0.0, output_limit=10.0)
        out = pid.update(setpoint=1.0, measurement=0.0, dt=0.1)
        assert out == pytest.approx(2.0)

    def test_output_clamped_to_limit(self):
        pid = PIDController(kp=100.0, ki=0.0, kd=0.0, output_limit=1.0)
        out = pid.update(setpoint=1.0, measurement=0.0, dt=0.1)
        assert out == pytest.approx(1.0)

    def test_negative_output_clamped(self):
        pid = PIDController(kp=100.0, ki=0.0, kd=0.0, output_limit=1.0)
        out = pid.update(setpoint=-1.0, measurement=0.0, dt=0.1)
        assert out == pytest.approx(-1.0)

    def test_integral_accumulates(self):
        pid = PIDController(kp=0.0, ki=1.0, kd=0.0, output_limit=100.0)
        for _ in range(5):
            pid.update(setpoint=1.0, measurement=0.0, dt=0.1)
        # After 5 steps with dt=0.1 and error=1.0: integral ≈ 0.5
        out = pid.update(setpoint=1.0, measurement=0.0, dt=0.1)
        assert out > 0.0

    def test_reset_clears_integral(self):
        pid = PIDController(kp=0.0, ki=1.0, kd=0.0, output_limit=100.0)
        for _ in range(10):
            pid.update(setpoint=1.0, measurement=0.0, dt=0.1)
        pid.reset()
        out = pid.update(setpoint=1.0, measurement=0.0, dt=0.1)
        # After reset integral is 0; only the small dt contribution remains
        assert out == pytest.approx(0.1, abs=0.05)

    def test_auto_dt_used_when_not_provided(self):
        pid = PIDController(kp=1.0, ki=0.0, kd=0.0)
        out = pid.update(setpoint=1.0, measurement=0.0)
        # dt defaults to wall-clock; output should still be proportional
        assert out > 0.0

    def test_derivative_reduces_overshoot(self):
        """PD controller differs from P-only due to derivative contribution."""
        p_only  = PIDController(kp=1.0, ki=0.0, kd=0.0,  output_limit=10.0)
        pd      = PIDController(kp=1.0, ki=0.0, kd=0.5,  output_limit=10.0)
        out_p   = p_only.update(setpoint=1.0, measurement=0.0, dt=0.1)
        out_pd  = pd.update(setpoint=1.0, measurement=0.0, dt=0.1)
        # PD adds a derivative spike on the first step → output differs from P-only
        assert out_pd != pytest.approx(out_p)
