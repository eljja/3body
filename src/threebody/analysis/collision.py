from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import TrajectoryResult
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


@dataclass(frozen=True, slots=True)
class CollisionRegularizationCertificate:
    """Interval-level certificate that raw coordinates should be replaced near collision."""

    sample_count: int
    minimum_hyperradius: float
    minimum_pair_distance: float
    maximum_collision_depth: float
    maximum_inward_speed: float
    collision_types: tuple[str, ...]
    regularization_required: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str]:
        return {
            "sample_count": self.sample_count,
            "minimum_hyperradius": self.minimum_hyperradius,
            "minimum_pair_distance": self.minimum_pair_distance,
            "maximum_collision_depth": self.maximum_collision_depth,
            "maximum_inward_speed": self.maximum_inward_speed,
            "collision_types": ",".join(self.collision_types),
            "regularization_required": self.regularization_required,
            "warning": self.warning,
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


def collision_regularization_certificate(
    system: object,
    trajectory: TrajectoryResult,
    start_index: int = 0,
    end_index: int | None = None,
    binary_collision_radius: float = 0.02,
    triple_collision_hyperradius: float = 0.05,
) -> CollisionRegularizationCertificate:
    """Aggregate McGehee-style diagnostics over a close-encounter interval."""

    if getattr(system, "body_count", None) != 3:
        raise TypeError("collision_regularization_certificate requires a general three-body system.")
    end = len(trajectory.t) - 1 if end_index is None else min(end_index, len(trajectory.t) - 1)
    start = max(0, min(start_index, end))
    diagnostics = tuple(
        mcgehee_collision_diagnostic(
            system,
            state,
            binary_collision_radius=binary_collision_radius,
            triple_collision_hyperradius=triple_collision_hyperradius,
        )
        for state in trajectory.y[start : end + 1]
    )
    minimum_hyperradius = float(min(diagnostic.hyperradius for diagnostic in diagnostics))
    minimum_pair_distance = float(min(diagnostic.minimum_pair_distance for diagnostic in diagnostics))
    maximum_collision_depth = float(max(diagnostic.collision_depth for diagnostic in diagnostics))
    maximum_inward_speed = float(max(max(-diagnostic.radial_velocity, 0.0) for diagnostic in diagnostics))
    collision_types = tuple(dict.fromkeys(diagnostic.collision_type for diagnostic in diagnostics))
    regularization_required = any(diagnostic.regularization_required for diagnostic in diagnostics)
    warning = ""
    if regularization_required:
        warning = "regularized collision coordinates are required before promoting a close-encounter law"
    return CollisionRegularizationCertificate(
        sample_count=len(diagnostics),
        minimum_hyperradius=minimum_hyperradius,
        minimum_pair_distance=minimum_pair_distance,
        maximum_collision_depth=maximum_collision_depth,
        maximum_inward_speed=maximum_inward_speed,
        collision_types=collision_types,
        regularization_required=regularization_required,
        warning=warning,
    )
