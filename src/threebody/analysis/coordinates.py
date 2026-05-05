from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..utils import cross_3d, pad_to_3d


PAIR_INDICES: tuple[tuple[int, int], ...] = ((0, 1), (0, 2), (1, 2))


@dataclass(frozen=True, slots=True)
class GeneralThreeBodyFeatures:
    pair_distances: np.ndarray
    pair_speeds: np.ndarray
    nearest_pair: tuple[int, int]
    nearest_distance: float
    outer_distance: float
    hierarchy_ratio: float
    virial_ratio: float
    total_energy: float
    angular_momentum_norm: float
    escape_index: float
    normalized_area: float
    hyperradius: float
    shape_anisotropy: float
    nearest_pair_specific_energy: float
    nearest_pair_eccentricity: float
    nearest_pair_semimajor_axis: float
    outer_specific_energy: float
    hierarchy_perturbation_strength: float


@dataclass(frozen=True, slots=True)
class RestrictedThreeBodyFeatures:
    position: np.ndarray
    velocity: np.ndarray
    distances_to_primaries: np.ndarray
    nearest_primary: int
    nearest_lagrange: str
    nearest_lagrange_distance: float
    jacobi_constant: float
    speed: float
    gateway_margin: float


def general_three_body_features(system: object, state: np.ndarray) -> GeneralThreeBodyFeatures:
    positions, velocities = system.split_state(state)
    pair_distances = []
    pair_speeds = []
    for i, j in PAIR_INDICES:
        pair_distances.append(np.linalg.norm(positions[i] - positions[j]))
        pair_speeds.append(np.linalg.norm(velocities[i] - velocities[j]))
    distances = np.asarray(pair_distances, dtype=float)
    speeds = np.asarray(pair_speeds, dtype=float)

    nearest_index = int(np.argmin(distances))
    nearest_pair = PAIR_INDICES[nearest_index]
    nearest_distance = float(distances[nearest_index])
    outer_distance = float(np.max(distances))
    hierarchy_ratio = float(outer_distance / max(nearest_distance, 1.0e-12))
    energy = float(system.total_energy(state))
    angular = float(np.linalg.norm(system.angular_momentum(state)))

    kinetic = _kinetic_energy(system, velocities)
    potential = abs(_potential_energy(system, positions))
    virial_ratio = float(2.0 * kinetic / max(potential, 1.0e-12))

    masses = np.asarray(system.masses, dtype=float)
    center = np.average(positions, axis=0, weights=masses)
    radii = np.linalg.norm(positions - center, axis=1)
    speeds_from_center = np.linalg.norm(velocities, axis=1)
    escape_index = float(np.max(radii * speeds_from_center))
    side_sq_sum = float(np.sum(distances**2))
    normalized_area = float(4.0 * np.sqrt(3.0) * abs(_signed_area_2d(positions)) / max(side_sq_sum, 1.0e-12))
    hyperradius = float(np.sqrt(np.sum(masses[:, None] * (positions - center) ** 2) / np.sum(masses)))
    shape_anisotropy = float((np.max(distances) - np.min(distances)) / max(np.mean(distances), 1.0e-12))
    (
        nearest_pair_specific_energy,
        nearest_pair_eccentricity,
        nearest_pair_semimajor_axis,
        outer_specific_energy,
        hierarchy_perturbation_strength,
    ) = _nearest_pair_kepler_features(system, positions, velocities, masses, nearest_pair)

    return GeneralThreeBodyFeatures(
        pair_distances=distances,
        pair_speeds=speeds,
        nearest_pair=nearest_pair,
        nearest_distance=nearest_distance,
        outer_distance=outer_distance,
        hierarchy_ratio=hierarchy_ratio,
        virial_ratio=virial_ratio,
        total_energy=energy,
        angular_momentum_norm=angular,
        escape_index=escape_index,
        normalized_area=normalized_area,
        hyperradius=hyperradius,
        shape_anisotropy=shape_anisotropy,
        nearest_pair_specific_energy=nearest_pair_specific_energy,
        nearest_pair_eccentricity=nearest_pair_eccentricity,
        nearest_pair_semimajor_axis=nearest_pair_semimajor_axis,
        outer_specific_energy=outer_specific_energy,
        hierarchy_perturbation_strength=hierarchy_perturbation_strength,
    )


def restricted_three_body_features(system: object, state: np.ndarray) -> RestrictedThreeBodyFeatures:
    state = np.asarray(state, dtype=float)
    position = state[:2]
    velocity = state[2:]
    distances = np.asarray(system.distances(position[None, :]), dtype=float).reshape(2)
    nearest_primary = int(np.argmin(distances))
    lagrange_points = system.lagrange_points()
    lagrange_distances = {name: float(np.linalg.norm(position - point)) for name, point in lagrange_points.items()}
    nearest_lagrange = min(lagrange_distances, key=lagrange_distances.get)
    jacobi_constant = float(system.jacobi_constant(state))
    speed = float(np.linalg.norm(velocity))
    gateway_margin = float(2.0 * system.pseudo_potential(position[None, :])[0] - jacobi_constant)

    return RestrictedThreeBodyFeatures(
        position=position,
        velocity=velocity,
        distances_to_primaries=distances,
        nearest_primary=nearest_primary,
        nearest_lagrange=nearest_lagrange,
        nearest_lagrange_distance=lagrange_distances[nearest_lagrange],
        jacobi_constant=jacobi_constant,
        speed=speed,
        gateway_margin=gateway_margin,
    )


def _kinetic_energy(system: object, velocities: np.ndarray) -> float:
    masses = np.asarray(system.masses, dtype=float)
    return float(0.5 * np.sum(masses[:, None] * velocities**2))


def _potential_energy(system: object, positions: np.ndarray) -> float:
    masses = np.asarray(system.masses, dtype=float)
    potential = 0.0
    for i, j in PAIR_INDICES:
        distance = np.linalg.norm(positions[i] - positions[j])
        potential -= system.gravitational_constant * masses[i] * masses[j] / max(distance, 1.0e-12)
    return float(potential)


def _signed_area_2d(positions: np.ndarray) -> float:
    if positions.shape[1] < 2:
        return 0.0
    x = positions[:, 0]
    y = positions[:, 1]
    return float(0.5 * ((x[0] * (y[1] - y[2])) + (x[1] * (y[2] - y[0])) + (x[2] * (y[0] - y[1]))))


def _nearest_pair_kepler_features(
    system: object,
    positions: np.ndarray,
    velocities: np.ndarray,
    masses: np.ndarray,
    pair: tuple[int, int],
) -> tuple[float, float, float, float, float]:
    i, j = pair
    outer = next(index for index in range(3) if index not in pair)
    inner_position = positions[j] - positions[i]
    inner_velocity = velocities[j] - velocities[i]
    inner_radius = float(np.linalg.norm(inner_position))
    inner_speed_sq = float(np.dot(inner_velocity, inner_velocity))
    inner_mu = system.gravitational_constant * (masses[i] + masses[j])
    inner_energy = 0.5 * inner_speed_sq - inner_mu / max(inner_radius, 1.0e-12)
    inner_h = cross_3d(inner_position, inner_velocity)
    eccentricity_vector = np.cross(pad_to_3d(inner_velocity), inner_h) / inner_mu - pad_to_3d(inner_position) / max(
        inner_radius,
        1.0e-12,
    )
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
    return float(inner_energy), eccentricity, semimajor_axis, float(outer_energy), perturbation_strength
