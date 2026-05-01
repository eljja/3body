from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..utils import cross_3d, pad_to_3d
from .coordinates import general_three_body_features


@dataclass(frozen=True, slots=True)
class HierarchicalElements:
    """Kepler-style elements for a tight inner pair and an outer perturber."""

    inner_pair: tuple[int, int]
    outer_body: int
    inner_semimajor_axis: float
    inner_eccentricity: float
    inner_specific_energy: float
    inner_angular_momentum_norm: float
    outer_radius: float
    outer_specific_energy: float
    perturbation_strength: float
    hierarchy_ratio: float
    is_inner_bound: bool


def hierarchical_elements(system: object, state: np.ndarray) -> HierarchicalElements:
    """Extract the leading two-body hierarchy from a general three-body state."""

    positions, velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    features = general_three_body_features(system, state)
    i, j = features.nearest_pair
    outer = next(index for index in range(3) if index not in features.nearest_pair)

    inner_position = positions[j] - positions[i]
    inner_velocity = velocities[j] - velocities[i]
    inner_mu = system.gravitational_constant * (masses[i] + masses[j])
    inner_radius = float(np.linalg.norm(inner_position))
    inner_speed_sq = float(np.dot(inner_velocity, inner_velocity))
    inner_energy = 0.5 * inner_speed_sq - inner_mu / max(inner_radius, 1.0e-12)
    inner_h = cross_3d(inner_position, inner_velocity)
    inner_h_norm = float(np.linalg.norm(inner_h))
    eccentricity_vector = np.cross(pad_to_3d(inner_velocity), inner_h) / inner_mu - pad_to_3d(inner_position) / inner_radius
    eccentricity = float(np.linalg.norm(eccentricity_vector))
    semimajor_axis = float(-inner_mu / (2.0 * inner_energy)) if inner_energy < 0.0 else np.inf

    pair_mass = masses[i] + masses[j]
    pair_center = (masses[i] * positions[i] + masses[j] * positions[j]) / pair_mass
    pair_velocity = (masses[i] * velocities[i] + masses[j] * velocities[j]) / pair_mass
    outer_position = positions[outer] - pair_center
    outer_velocity = velocities[outer] - pair_velocity
    outer_radius = float(np.linalg.norm(outer_position))
    outer_mu = system.gravitational_constant * (pair_mass + masses[outer])
    outer_energy = 0.5 * float(np.dot(outer_velocity, outer_velocity)) - outer_mu / max(outer_radius, 1.0e-12)

    perturbation_strength = float((masses[outer] / pair_mass) * (inner_radius / max(outer_radius, 1.0e-12)) ** 3)

    return HierarchicalElements(
        inner_pair=(i, j),
        outer_body=outer,
        inner_semimajor_axis=semimajor_axis,
        inner_eccentricity=eccentricity,
        inner_specific_energy=float(inner_energy),
        inner_angular_momentum_norm=inner_h_norm,
        outer_radius=outer_radius,
        outer_specific_energy=float(outer_energy),
        perturbation_strength=perturbation_strength,
        hierarchy_ratio=features.hierarchy_ratio,
        is_inner_bound=bool(inner_energy < 0.0 and eccentricity < 1.0),
    )
