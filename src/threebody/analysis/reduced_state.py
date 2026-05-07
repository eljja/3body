from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import TrajectoryResult
from .coordinates import PAIR_INDICES, general_three_body_features
from .shape import shape_space_coordinates


@dataclass(frozen=True, slots=True)
class ReducedThreeBodyState:
    """Symmetry-reduced scale/shape/invariant state for a Newtonian three-body configuration."""

    time: float
    total_energy: float
    angular_momentum_norm: float
    virial_ratio: float
    hyperradius: float
    radial_velocity: float
    normalized_radial_velocity: float
    shape_area: float
    shape_anisotropy: float
    shape_orientation: float
    nearest_pair: tuple[int, int]
    nearest_distance: float
    hierarchy_ratio: float
    hierarchy_perturbation_strength: float
    escape_index: float
    collision_depth: float
    escape_depth: float
    reduced_regime_hint: str

    def as_dict(self) -> dict[str, float | int | str]:
        return {
            "time": self.time,
            "total_energy": self.total_energy,
            "angular_momentum_norm": self.angular_momentum_norm,
            "virial_ratio": self.virial_ratio,
            "hyperradius": self.hyperradius,
            "radial_velocity": self.radial_velocity,
            "normalized_radial_velocity": self.normalized_radial_velocity,
            "shape_area": self.shape_area,
            "shape_anisotropy": self.shape_anisotropy,
            "shape_orientation": self.shape_orientation,
            "nearest_pair_i": self.nearest_pair[0],
            "nearest_pair_j": self.nearest_pair[1],
            "nearest_distance": self.nearest_distance,
            "hierarchy_ratio": self.hierarchy_ratio,
            "hierarchy_perturbation_strength": self.hierarchy_perturbation_strength,
            "escape_index": self.escape_index,
            "collision_depth": self.collision_depth,
            "escape_depth": self.escape_depth,
            "reduced_regime_hint": self.reduced_regime_hint,
        }


def reduced_three_body_state(system: object, state: np.ndarray, time: float = 0.0) -> ReducedThreeBodyState:
    """Compute the shared reduced coordinates used by atlas-level diagnostics."""

    positions, velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    center = np.average(positions, axis=0, weights=masses)
    center_velocity = np.average(velocities, axis=0, weights=masses)
    centered_positions = positions - center
    centered_velocities = velocities - center_velocity
    features = general_three_body_features(system, state)
    shape = shape_space_coordinates(system, state)
    hyperradius = max(shape.hyperradius, 1.0e-12)
    radial_velocity = float(np.sum(masses[:, None] * centered_positions * centered_velocities) / (np.sum(masses) * hyperradius))
    normalized_radial_velocity = float(radial_velocity / np.sqrt(1.0 + radial_velocity**2))
    minimum_pair_distance = float(min(np.linalg.norm(positions[i] - positions[j]) for i, j in PAIR_INDICES))
    collision_depth = float(min(1.0 / max(minimum_pair_distance, 1.0e-12), 1.0 / hyperradius))
    escape_depth = float(features.escape_index / (1.0 + features.escape_index))
    regime_hint = _reduced_regime_hint(features.hierarchy_ratio, collision_depth, escape_depth, shape.anisotropy)
    return ReducedThreeBodyState(
        time=float(time),
        total_energy=features.total_energy,
        angular_momentum_norm=features.angular_momentum_norm,
        virial_ratio=features.virial_ratio,
        hyperradius=float(shape.hyperradius),
        radial_velocity=radial_velocity,
        normalized_radial_velocity=normalized_radial_velocity,
        shape_area=shape.normalized_area,
        shape_anisotropy=shape.anisotropy,
        shape_orientation=shape.orientation,
        nearest_pair=features.nearest_pair,
        nearest_distance=features.nearest_distance,
        hierarchy_ratio=features.hierarchy_ratio,
        hierarchy_perturbation_strength=features.hierarchy_perturbation_strength,
        escape_index=features.escape_index,
        collision_depth=collision_depth,
        escape_depth=escape_depth,
        reduced_regime_hint=regime_hint,
    )


def reduced_state_series(
    system: object,
    trajectory: TrajectoryResult,
    stride: int = 1,
) -> tuple[ReducedThreeBodyState, ...]:
    if stride < 1:
        raise ValueError("stride must be >= 1.")
    return tuple(
        reduced_three_body_state(system, state, time=float(time))
        for time, state in zip(trajectory.t[::stride], trajectory.y[::stride], strict=True)
    )


def _reduced_regime_hint(
    hierarchy_ratio: float,
    collision_depth: float,
    escape_depth: float,
    shape_anisotropy: float,
) -> str:
    if collision_depth > 20.0:
        return "collision_boundary"
    if escape_depth > 0.9:
        return "escape_boundary"
    if hierarchy_ratio > 5.0:
        return "hierarchy_chart"
    if shape_anisotropy < 0.5:
        return "democratic_shape"
    return "transition_region"
