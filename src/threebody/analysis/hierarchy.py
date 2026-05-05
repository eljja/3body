from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..utils import cross_3d
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
    inner_energy = features.nearest_pair_specific_energy
    inner_h = cross_3d(inner_position, inner_velocity)
    inner_h_norm = float(np.linalg.norm(inner_h))
    eccentricity = features.nearest_pair_eccentricity
    semimajor_axis = features.nearest_pair_semimajor_axis

    pair_mass = masses[i] + masses[j]
    pair_center = (masses[i] * positions[i] + masses[j] * positions[j]) / pair_mass
    outer_position = positions[outer] - pair_center
    outer_radius = float(np.linalg.norm(outer_position))

    return HierarchicalElements(
        inner_pair=(i, j),
        outer_body=outer,
        inner_semimajor_axis=semimajor_axis,
        inner_eccentricity=eccentricity,
        inner_specific_energy=float(inner_energy),
        inner_angular_momentum_norm=inner_h_norm,
        outer_radius=outer_radius,
        outer_specific_energy=features.outer_specific_energy,
        perturbation_strength=features.hierarchy_perturbation_strength,
        hierarchy_ratio=features.hierarchy_ratio,
        is_inner_bound=bool(inner_energy < 0.0 and eccentricity < 1.0),
    )
