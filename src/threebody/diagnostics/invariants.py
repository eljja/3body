from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import TrajectoryResult


@dataclass(slots=True)
class InvariantMonitor:
    """Evaluate conserved quantities and drift diagnostics for each system type."""

    system: object

    def evaluate(self, trajectory: TrajectoryResult) -> dict[str, np.ndarray]:
        if hasattr(self.system, "jacobi_constant"):
            jacobi = np.array([self.system.jacobi_constant(state) for state in trajectory.y], dtype=float)
            return {
                "jacobi_constant": jacobi,
                "jacobi_drift": jacobi - jacobi[0],
            }

        if hasattr(self.system, "laplace_runge_lenz"):
            energy = np.array([self.system.total_energy(state) for state in trajectory.y], dtype=float)
            angular = np.array([np.linalg.norm(self.system.angular_momentum(state)) for state in trajectory.y], dtype=float)
            lrl = np.array([np.linalg.norm(self.system.laplace_runge_lenz(state)) for state in trajectory.y], dtype=float)
            return {
                "energy": energy,
                "energy_drift": energy - energy[0],
                "angular_momentum_norm": angular,
                "angular_momentum_drift": angular - angular[0],
                "lrl_norm": lrl,
            }

        energy = np.array([self.system.total_energy(state) for state in trajectory.y], dtype=float)
        momentum = np.array([np.linalg.norm(self.system.linear_momentum(state)) for state in trajectory.y], dtype=float)
        angular = np.array([np.linalg.norm(self.system.angular_momentum(state)) for state in trajectory.y], dtype=float)
        return {
            "energy": energy,
            "energy_drift": energy - energy[0],
            "linear_momentum_norm": momentum,
            "linear_momentum_drift": momentum - momentum[0],
            "angular_momentum_norm": angular,
            "angular_momentum_drift": angular - angular[0],
        }

    @staticmethod
    def drift_summary(values: np.ndarray) -> dict[str, float]:
        values = np.asarray(values, dtype=float)
        drift = values - values[0]
        return {
            "initial": float(values[0]),
            "final": float(values[-1]),
            "max_abs_drift": float(np.max(np.abs(drift))),
            "rms_drift": float(np.sqrt(np.mean(drift**2))),
        }
