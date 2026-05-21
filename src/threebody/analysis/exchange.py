from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import TrajectoryResult
from ..utils import cross_3d, trapezoid_integral


@dataclass(frozen=True, slots=True)
class EncounterExchangeMetrics:
    """Accumulated exchange diagnostics for a selected inner binary during an encounter."""

    inner_pair: tuple[int, int]
    outer_body: int
    initial_inner_energy: float
    final_inner_energy: float
    signed_inner_energy_delta: float
    relative_inner_energy_exchange: float
    initial_angular_momentum_norm: float
    final_angular_momentum_norm: float
    signed_angular_momentum_delta: float
    relative_angular_momentum_exchange: float
    tidal_impulse: float


def encounter_exchange_metrics(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
) -> EncounterExchangeMetrics:
    """Measure cumulative energy, angular momentum, and tidal forcing over a flyby."""

    outer = next(index for index in range(3) if index not in inner_pair)
    energies = []
    angular_momentum_norms = []
    perturbation_strengths = []
    for state in trajectory.y:
        energy, angular_momentum_norm, perturbation_strength = _state_exchange_features(
            system,
            state,
            inner_pair=inner_pair,
            outer=outer,
        )
        energies.append(energy)
        angular_momentum_norms.append(angular_momentum_norm)
        perturbation_strengths.append(perturbation_strength)

    energy_array = np.asarray(energies, dtype=float)
    angular_array = np.asarray(angular_momentum_norms, dtype=float)
    perturbation_array = np.asarray(perturbation_strengths, dtype=float)
    energy_delta = float(energy_array[-1] - energy_array[0])
    angular_delta = float(angular_array[-1] - angular_array[0])
    tidal_impulse = trapezoid_integral(perturbation_array, trajectory.t)
    return EncounterExchangeMetrics(
        inner_pair=inner_pair,
        outer_body=outer,
        initial_inner_energy=float(energy_array[0]),
        final_inner_energy=float(energy_array[-1]),
        signed_inner_energy_delta=energy_delta,
        relative_inner_energy_exchange=float(abs(energy_delta) / max(abs(energy_array[0]), 1.0e-12)),
        initial_angular_momentum_norm=float(angular_array[0]),
        final_angular_momentum_norm=float(angular_array[-1]),
        signed_angular_momentum_delta=angular_delta,
        relative_angular_momentum_exchange=float(abs(angular_delta) / max(abs(angular_array[0]), 1.0e-12)),
        tidal_impulse=tidal_impulse,
    )


def _state_exchange_features(
    system: object,
    state: np.ndarray,
    inner_pair: tuple[int, int],
    outer: int,
) -> tuple[float, float, float]:
    positions, velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    i, j = inner_pair
    inner_position = positions[j] - positions[i]
    inner_velocity = velocities[j] - velocities[i]
    inner_radius = float(np.linalg.norm(inner_position))
    inner_mu = system.gravitational_constant * (masses[i] + masses[j])
    inner_energy = 0.5 * float(np.dot(inner_velocity, inner_velocity)) - inner_mu / max(inner_radius, 1.0e-12)
    angular_momentum_norm = float(np.linalg.norm(cross_3d(inner_position, inner_velocity)))

    pair_mass = masses[i] + masses[j]
    pair_center = (masses[i] * positions[i] + masses[j] * positions[j]) / pair_mass
    outer_radius = float(np.linalg.norm(positions[outer] - pair_center))
    perturbation_strength = float((masses[outer] / pair_mass) * (inner_radius / max(outer_radius, 1.0e-12)) ** 3)
    return float(inner_energy), angular_momentum_norm, perturbation_strength
