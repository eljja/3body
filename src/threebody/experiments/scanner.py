from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..solvers import AdaptiveIntegrator


@dataclass(slots=True)
class InitialConditionScanner:
    """Grid scanning utilities for bounded, collision, and escape classification."""

    integrator: AdaptiveIntegrator
    collision_radius: float = 0.02
    escape_radius: float = 3.0

    def classify_restricted(self, system: object, state: np.ndarray, t_final: float = 20.0 * np.pi) -> str:
        t_eval = np.linspace(0.0, t_final, 2000)
        trajectory = self.integrator.integrate(system, (0.0, t_final), state, t_eval=t_eval)
        positions = trajectory.y[:, :2]
        distances = np.linalg.norm(positions, axis=1)
        r1, r2 = system.distances(positions)
        if np.min(r1) < self.collision_radius or np.min(r2) < self.collision_radius:
            return "collision"
        if np.max(distances) > self.escape_radius:
            return "escape"
        return "bounded"

    def scan_restricted_grid(
        self,
        system: object,
        jacobi_constant: float,
        x_values: np.ndarray,
        y_values: np.ndarray,
    ) -> np.ndarray:
        classes = np.empty((y_values.size, x_values.size), dtype=object)
        for row, y_value in enumerate(y_values):
            for column, x_value in enumerate(x_values):
                omega = system.pseudo_potential([[x_value, y_value]])[0]
                velocity_sq = 2.0 * omega - jacobi_constant
                if velocity_sq <= 0.0:
                    classes[row, column] = "forbidden"
                    continue
                state = np.array([x_value, y_value, 0.0, np.sqrt(velocity_sq)], dtype=float)
                classes[row, column] = self.classify_restricted(system, state)
        return classes

    def classify_general(self, system: object, state: np.ndarray, t_final: float = 10.0) -> str:
        t_eval = np.linspace(0.0, t_final, 2000)
        trajectory = self.integrator.integrate(system, (0.0, t_final), state, t_eval=t_eval)
        positions, _velocities = system.split_state(trajectory.y[-1])
        max_distance = float(np.max(np.linalg.norm(positions, axis=1)))
        min_pairwise = np.inf
        for snapshot in trajectory.y:
            position_snapshot, _velocity_snapshot = system.split_state(snapshot)
            for i in range(system.body_count):
                for j in range(i + 1, system.body_count):
                    min_pairwise = min(min_pairwise, np.linalg.norm(position_snapshot[i] - position_snapshot[j]))
        if min_pairwise < self.collision_radius:
            return "collision"
        if max_distance > self.escape_radius:
            return "escape"
        return "bounded"
