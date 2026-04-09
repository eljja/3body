from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..utils import cross_3d, pad_to_3d


@dataclass(slots=True)
class TwoBodySystem:
    """Relative-coordinate two-body problem in nondimensional Newtonian gravity."""

    primary_mass: float = 1.0
    secondary_mass: float = 1.0e-3
    gravitational_constant: float = 1.0
    dimension: int = 2

    def __post_init__(self) -> None:
        if self.dimension not in (2, 3):
            raise ValueError("TwoBodySystem only supports 2D or 3D.")

    @property
    def body_count(self) -> int:
        return 1

    @property
    def gravitational_parameter(self) -> float:
        return self.gravitational_constant * (self.primary_mass + self.secondary_mass)

    @property
    def reduced_mass(self) -> float:
        return (self.primary_mass * self.secondary_mass) / (self.primary_mass + self.secondary_mass)

    def split_state(self, state: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        state = np.asarray(state, dtype=float)
        position = state[: self.dimension]
        velocity = state[self.dimension :]
        return position, velocity

    def rhs(self, _t: float, state: np.ndarray) -> np.ndarray:
        position, velocity = self.split_state(state)
        acceleration = self.acceleration_field(position[None, :])[0]
        return np.concatenate([velocity, acceleration])

    def acceleration_field(self, positions: np.ndarray) -> np.ndarray:
        positions = np.asarray(positions, dtype=float)
        radius = np.linalg.norm(positions, axis=1)[:, None]
        return -self.gravitational_parameter * positions / radius**3

    def specific_energy(self, state: np.ndarray) -> float:
        position, velocity = self.split_state(state)
        radius = np.linalg.norm(position)
        return 0.5 * float(np.dot(velocity, velocity)) - self.gravitational_parameter / radius

    def total_energy(self, state: np.ndarray) -> float:
        return self.reduced_mass * self.specific_energy(state)

    def specific_angular_momentum(self, state: np.ndarray) -> np.ndarray:
        position, velocity = self.split_state(state)
        return cross_3d(position, velocity)

    def angular_momentum(self, state: np.ndarray) -> np.ndarray:
        return self.reduced_mass * self.specific_angular_momentum(state)

    def laplace_runge_lenz(self, state: np.ndarray) -> np.ndarray:
        position, velocity = self.split_state(state)
        h = self.specific_angular_momentum(state)
        return np.cross(pad_to_3d(velocity), h) - self.gravitational_parameter * pad_to_3d(position) / np.linalg.norm(position)

    def barycentric_positions(self, state: np.ndarray) -> np.ndarray:
        position, _velocity = self.split_state(state)
        total_mass = self.primary_mass + self.secondary_mass
        primary = -(self.secondary_mass / total_mass) * position
        secondary = (self.primary_mass / total_mass) * position
        return np.vstack([primary, secondary])
