from __future__ import annotations

from dataclasses import dataclass

import numpy as np


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

    center = np.average(positions, axis=0, weights=np.asarray(system.masses, dtype=float))
    radii = np.linalg.norm(positions - center, axis=1)
    speeds_from_center = np.linalg.norm(velocities, axis=1)
    escape_index = float(np.max(radii * speeds_from_center))

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
