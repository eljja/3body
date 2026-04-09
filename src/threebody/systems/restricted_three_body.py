from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import root_scalar


@dataclass(slots=True)
class RestrictedThreeBodySystem:
    """Planar circular restricted three-body problem in the rotating frame."""

    mass_ratio: float = 0.0121505856

    @property
    def primary_positions(self) -> np.ndarray:
        return np.array(
            [
                [-self.mass_ratio, 0.0],
                [1.0 - self.mass_ratio, 0.0],
            ],
            dtype=float,
        )

    def distances(self, positions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        positions = np.atleast_2d(np.asarray(positions, dtype=float))
        primary, secondary = self.primary_positions
        r1 = np.linalg.norm(positions - primary, axis=1)
        r2 = np.linalg.norm(positions - secondary, axis=1)
        return r1, r2

    def pseudo_potential(self, positions: np.ndarray) -> np.ndarray:
        positions = np.atleast_2d(np.asarray(positions, dtype=float))
        x = positions[:, 0]
        y = positions[:, 1]
        r1, r2 = self.distances(positions)
        return 0.5 * (x**2 + y**2) + (1.0 - self.mass_ratio) / r1 + self.mass_ratio / r2

    def potential_gradient(self, positions: np.ndarray) -> np.ndarray:
        positions = np.atleast_2d(np.asarray(positions, dtype=float))
        x = positions[:, 0]
        y = positions[:, 1]
        mu = self.mass_ratio
        r1, r2 = self.distances(positions)
        grad_x = x - (1.0 - mu) * (x + mu) / r1**3 - mu * (x - (1.0 - mu)) / r2**3
        grad_y = y - (1.0 - mu) * y / r1**3 - mu * y / r2**3
        return np.column_stack([grad_x, grad_y])

    def rhs(self, _t: float, state: np.ndarray) -> np.ndarray:
        x, y, vx, vy = np.asarray(state, dtype=float)
        grad_x, grad_y = self.potential_gradient([[x, y]])[0]
        ax = 2.0 * vy + grad_x
        ay = -2.0 * vx + grad_y
        return np.array([vx, vy, ax, ay], dtype=float)

    def jacobi_constant(self, state: np.ndarray) -> float:
        position = np.asarray(state[:2], dtype=float)
        velocity = np.asarray(state[2:], dtype=float)
        return float(2.0 * self.pseudo_potential(position[None, :])[0] - np.dot(velocity, velocity))

    def lagrange_points(self) -> dict[str, np.ndarray]:
        mu = self.mass_ratio
        x_secondary = 1.0 - mu

        def collinear_equation(x_value: float) -> float:
            return self.potential_gradient([[x_value, 0.0]])[0, 0]

        def bracketed_root(bounds: tuple[float, float]) -> float:
            left, right = bounds
            grid = np.linspace(left, right, 512)
            values = np.array([collinear_equation(point) for point in grid])
            for idx in range(grid.size - 1):
                if np.sign(values[idx]) == 0:
                    return float(grid[idx])
                if np.sign(values[idx]) != np.sign(values[idx + 1]):
                    result = root_scalar(collinear_equation, bracket=(grid[idx], grid[idx + 1]), method="brentq")
                    return float(result.root)
            raise RuntimeError(f"Could not bracket collinear Lagrange point in interval {bounds}.")

        return {
            "L1": np.array([bracketed_root((0.2 - mu, x_secondary - 1.0e-5)), 0.0]),
            "L2": np.array([bracketed_root((x_secondary + 1.0e-5, 2.0)), 0.0]),
            "L3": np.array([bracketed_root((-2.0, -mu - 1.0e-5)), 0.0]),
            "L4": np.array([0.5 - mu, np.sqrt(3.0) / 2.0]),
            "L5": np.array([0.5 - mu, -np.sqrt(3.0) / 2.0]),
        }

    def zero_velocity_curve(self, x_grid: np.ndarray, y_grid: np.ndarray, jacobi_constant: float) -> np.ndarray:
        grid = np.column_stack([x_grid.ravel(), y_grid.ravel()])
        values = 2.0 * self.pseudo_potential(grid) - jacobi_constant
        return values.reshape(x_grid.shape)
