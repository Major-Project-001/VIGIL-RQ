"""
2-D Kalman filter for smooth position/velocity estimation.

Used to reduce jitter in tracked bounding-box centroids and sensor readings.

State vector:  [x, y, vx, vy]
Measurement:   [x, y]
"""

import numpy as np


class KalmanFilter2D:
    """Constant-velocity Kalman filter for a 2-D point.

    Parameters
    ----------
    process_noise : float
        Variance of the process (motion) noise.
    measurement_noise : float
        Variance of the measurement noise.
    """

    def __init__(
        self,
        process_noise: float = 1e-4,
        measurement_noise: float = 1e-2,
    ) -> None:
        # State transition matrix  (x, y, vx, vy)
        self.F = np.eye(4, dtype=np.float64)
        self.F[0, 2] = 1.0  # x  += vx * dt  (dt = 1 frame)
        self.F[1, 3] = 1.0  # y  += vy * dt

        # Measurement matrix  – we observe x, y only
        self.H = np.zeros((2, 4), dtype=np.float64)
        self.H[0, 0] = 1.0
        self.H[1, 1] = 1.0

        # Process noise covariance
        self.Q = np.eye(4, dtype=np.float64) * process_noise

        # Measurement noise covariance
        self.R = np.eye(2, dtype=np.float64) * measurement_noise

        # State estimate and covariance
        self.x = np.zeros((4, 1), dtype=np.float64)
        self.P = np.eye(4, dtype=np.float64)

        self._initialised = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def init(self, x: float, y: float) -> None:
        """Seed the filter with an initial measurement."""
        self.x = np.array([[x], [y], [0.0], [0.0]], dtype=np.float64)
        self.P = np.eye(4, dtype=np.float64)
        self._initialised = True

    def predict(self) -> tuple[float, float]:
        """Predict the next state and return (x, y)."""
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return float(self.x[0, 0]), float(self.x[1, 0])

    def update(self, x: float, y: float) -> tuple[float, float]:
        """Correct the prediction with a new measurement; return smoothed (x, y)."""
        if not self._initialised:
            self.init(x, y)
            return x, y

        self.predict()

        z = np.array([[x], [y]], dtype=np.float64)
        y_tilde = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y_tilde
        self.P = (np.eye(4, dtype=np.float64) - K @ self.H) @ self.P
        return float(self.x[0, 0]), float(self.x[1, 0])

    @property
    def position(self) -> tuple[float, float]:
        """Current estimated position (x, y)."""
        return float(self.x[0, 0]), float(self.x[1, 0])

    @property
    def velocity(self) -> tuple[float, float]:
        """Current estimated velocity (vx, vy)."""
        return float(self.x[2, 0]), float(self.x[3, 0])
