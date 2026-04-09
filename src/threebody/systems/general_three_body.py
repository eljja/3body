from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..utils import cross_3d


@dataclass(slots=True)
class GeneralThreeBodySystem:
    """General Newtonian three-body problem in inertial coordinates."""

    masses: tuple[float, float, float] = (1.0, 1.0, 1.0)
    gravitational_constant: float = 1.0
    dimension: int = 2
    softening: float = 0.0

    def __post_init__(self) -> None:
        if self.dimension not in (2, 3):
            raise ValueError("GeneralThreeBodySystem only supports 2D or 3D.")

    @property
    def body_count(self) -> int:
        return 3

    @property
    def state_dim(self) -> int:
        return self.body_count * self.dimension * 2

    def split_state(self, state: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        state = np.asarray(state, dtype=float)
        offset = self.body_count * self.dimension
        positions = state[:offset].reshape(self.body_count, self.dimension)
        velocities = state[offset:].reshape(self.body_count, self.dimension)
        return positions, velocities

    def flatten_state(self, positions: np.ndarray, velocities: np.ndarray) -> np.ndarray:
        return np.concatenate([positions.reshape(-1), velocities.reshape(-1)])

    def rhs(self, _t: float, state: np.ndarray) -> np.ndarray:
        positions, velocities = self.split_state(state)
        accelerations = self.acceleration_field(positions)
        return self.flatten_state(velocities, accelerations)

    def acceleration_field(self, positions: np.ndarray) -> np.ndarray:
        positions = np.asarray(positions, dtype=float).reshape(self.body_count, self.dimension)
        accelerations = np.zeros_like(positions)
        masses = np.asarray(self.masses, dtype=float)
        for i in range(self.body_count):
            displacement = positions - positions[i]
            distance_sq = np.sum(displacement**2, axis=1) + self.softening**2
            distance_sq[i] = np.inf
            inverse_distance_cubed = distance_sq ** (-1.5)
            weighted = self.gravitational_constant * masses[:, None] * displacement * inverse_distance_cubed[:, None]
            accelerations[i] = np.sum(weighted, axis=0)
        return accelerations

    def total_energy(self, state: np.ndarray) -> float:
        positions, velocities = self.split_state(state)
        masses = np.asarray(self.masses, dtype=float)
        kinetic = 0.5 * np.sum(masses[:, None] * velocities**2)
        potential = 0.0
        for i in range(self.body_count):
            for j in range(i + 1, self.body_count):
                distance = np.linalg.norm(positions[j] - positions[i])
                potential -= self.gravitational_constant * masses[i] * masses[j] / distance
        return float(kinetic + potential)

    def linear_momentum(self, state: np.ndarray) -> np.ndarray:
        _positions, velocities = self.split_state(state)
        masses = np.asarray(self.masses, dtype=float)
        return np.sum(masses[:, None] * velocities, axis=0)

    def angular_momentum(self, state: np.ndarray) -> np.ndarray:
        positions, velocities = self.split_state(state)
        masses = np.asarray(self.masses, dtype=float)
        total = np.zeros(3, dtype=float)
        for mass, position, velocity in zip(masses, positions, velocities, strict=True):
            total += mass * cross_3d(position, velocity)
        return total
