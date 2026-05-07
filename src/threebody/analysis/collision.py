from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .coordinates import PAIR_INDICES
from .reduced_state import reduced_three_body_state
from .shape import shape_space_coordinates


@dataclass(frozen=True, slots=True)
class McGeheeCollisionDiagnostic:
    """Scale/shape collision diagnostic inspired by McGehee blow-up coordinates."""

    hyperradius: float
    radial_velocity: float
    normalized_radial_velocity: float
    shape_area: float
    shape_anisotropy: float
    minimum_pair_distance: float
    collision_depth: float
    collision_type: str
    regularization_required: bool

    def as_dict(self) -> dict[str, float | str | bool]:
        return {
            "hyperradius": self.hyperradius,
            "radial_velocity": self.radial_velocity,
            "normalized_radial_velocity": self.normalized_radial_velocity,
            "shape_area": self.shape_area,
            "shape_anisotropy": self.shape_anisotropy,
            "minimum_pair_distance": self.minimum_pair_distance,
            "collision_depth": self.collision_depth,
            "collision_type": self.collision_type,
            "regularization_required": self.regularization_required,
        }


def mcgehee_collision_diagnostic(
    system: object,
    state: np.ndarray,
    binary_collision_radius: float = 0.02,
    triple_collision_hyperradius: float = 0.05,
) -> McGeheeCollisionDiagnostic:
    """Separate scale from shape near binary or triple collision candidates."""

    positions, velocities = system.split_state(state)
    reduced = reduced_three_body_state(system, state)
    masses = np.asarray(system.masses, dtype=float)
    center = np.average(positions, axis=0, weights=masses)
    center_velocity = np.average(velocities, axis=0, weights=masses)
    centered_positions = positions - center
    centered_velocities = velocities - center_velocity
    shape = shape_space_coordinates(system, state)
    hyperradius = max(shape.hyperradius, 1.0e-12)
    radial_velocity = float(np.sum(masses[:, None] * centered_positions * centered_velocities) / (np.sum(masses) * hyperradius))
    normalized_radial_velocity = float(radial_velocity / np.sqrt(1.0 + radial_velocity**2))
    pair_distances = np.array([np.linalg.norm(positions[i] - positions[j]) for i, j in PAIR_INDICES], dtype=float)
    minimum_pair_distance = float(np.min(pair_distances))
    collision_depth = float(min(binary_collision_radius / max(minimum_pair_distance, 1.0e-12), triple_collision_hyperradius / hyperradius))

    if shape.hyperradius < triple_collision_hyperradius:
        collision_type = "triple_collision_candidate"
    elif minimum_pair_distance < binary_collision_radius:
        collision_type = "binary_collision_candidate"
    else:
        collision_type = "regular_shape"

    return McGeheeCollisionDiagnostic(
        hyperradius=reduced.hyperradius,
        radial_velocity=radial_velocity,
        normalized_radial_velocity=normalized_radial_velocity,
        shape_area=reduced.shape_area,
        shape_anisotropy=reduced.shape_anisotropy,
        minimum_pair_distance=minimum_pair_distance,
        collision_depth=collision_depth,
        collision_type=collision_type,
        regularization_required=collision_type != "regular_shape",
    )
