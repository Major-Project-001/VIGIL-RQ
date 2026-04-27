"""
__init__.py — Gait module for VIGIL-RQ quadruped.

Provides:
    - IKSolver: Analytical 3-DOF inverse kinematics
    - TrotGaitIK: Diagonal trot gait (fast, dynamic)
    - CreepGaitIK: Wave gait (slow, stable, 1 leg at a time)
    - forward_kinematics: FK for visualization/verification
"""

from .ik_solver import IKSolver, forward_kinematics, LEG_ORIGINS, LEG_SIDE
from .trot import TrotGaitIK
from .creep import CreepGaitIK

__all__ = [
    "IKSolver", "forward_kinematics", "LEG_ORIGINS", "LEG_SIDE",
    "TrotGaitIK", "CreepGaitIK",
]
