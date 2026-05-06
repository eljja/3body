from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import TrajectoryResult
from ..utils import cross_3d


@dataclass(frozen=True, slots=True)
class PeriapsisScatteringMap:
    """Trajectory-measured flyby scattering coordinates for one inner binary."""

    inner_pair: tuple[int, int]
    outer_body: int
    periapsis_index: int
    periapsis_time: float
    periapsis_distance: float
    binary_phase_at_periapsis: float
    binary_phase_cos_positive: float
    binary_phase_sin_positive: float
    incoming_outer_energy: float
    outgoing_outer_energy: float
    outer_energy_delta: float
    incoming_outer_angular_momentum: float
    outgoing_outer_angular_momentum: float
    outer_angular_momentum_delta: float
    deflection_angle: float

    def as_dict(self) -> dict[str, float | int]:
        return {
            "periapsis_index": self.periapsis_index,
            "periapsis_time": self.periapsis_time,
            "periapsis_distance": self.periapsis_distance,
            "binary_phase_at_periapsis": self.binary_phase_at_periapsis,
            "binary_phase_cos_positive": self.binary_phase_cos_positive,
            "binary_phase_sin_positive": self.binary_phase_sin_positive,
            "incoming_outer_energy": self.incoming_outer_energy,
            "outgoing_outer_energy": self.outgoing_outer_energy,
            "outer_energy_delta": self.outer_energy_delta,
            "incoming_outer_angular_momentum": self.incoming_outer_angular_momentum,
            "outgoing_outer_angular_momentum": self.outgoing_outer_angular_momentum,
            "outer_angular_momentum_delta": self.outer_angular_momentum_delta,
            "deflection_angle": self.deflection_angle,
        }


def periapsis_scattering_map(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
) -> PeriapsisScatteringMap:
    """Measure scattering variables at the actual closest approach in the trajectory."""

    outer = next(index for index in range(3) if index not in inner_pair)
    masses = np.asarray(system.masses, dtype=float)
    i, j = inner_pair

    distances = []
    binary_phases = []
    outer_energies = []
    outer_angular = []
    outer_velocities = []
    for state in trajectory.y:
        positions, velocities = system.split_state(state)
        pair_mass = masses[i] + masses[j]
        pair_center = (masses[i] * positions[i] + masses[j] * positions[j]) / pair_mass
        pair_velocity = (masses[i] * velocities[i] + masses[j] * velocities[j]) / pair_mass
        binary_vector = positions[j] - positions[i]
        outer_vector = positions[outer] - pair_center
        outer_velocity = velocities[outer] - pair_velocity

        distance = float(np.linalg.norm(outer_vector))
        phase = float(np.mod(np.arctan2(binary_vector[1], binary_vector[0]), 2.0 * np.pi))
        mu_outer = system.gravitational_constant * (pair_mass + masses[outer])
        energy = 0.5 * float(np.dot(outer_velocity, outer_velocity)) - mu_outer / max(distance, 1.0e-12)
        angular = float(np.linalg.norm(cross_3d(outer_vector, outer_velocity)))

        distances.append(distance)
        binary_phases.append(phase)
        outer_energies.append(energy)
        outer_angular.append(angular)
        outer_velocities.append(outer_velocity)

    distance_array = np.asarray(distances, dtype=float)
    periapsis_index = int(np.argmin(distance_array))
    phase = float(binary_phases[periapsis_index])
    incoming_velocity = np.asarray(outer_velocities[0], dtype=float)
    outgoing_velocity = np.asarray(outer_velocities[-1], dtype=float)
    deflection_angle = _angle_between(incoming_velocity, outgoing_velocity)
    return PeriapsisScatteringMap(
        inner_pair=inner_pair,
        outer_body=outer,
        periapsis_index=periapsis_index,
        periapsis_time=float(trajectory.t[periapsis_index]),
        periapsis_distance=float(distance_array[periapsis_index]),
        binary_phase_at_periapsis=phase,
        binary_phase_cos_positive=float(1.01 + np.cos(phase)),
        binary_phase_sin_positive=float(1.01 + np.sin(phase)),
        incoming_outer_energy=float(outer_energies[0]),
        outgoing_outer_energy=float(outer_energies[-1]),
        outer_energy_delta=float(outer_energies[-1] - outer_energies[0]),
        incoming_outer_angular_momentum=float(outer_angular[0]),
        outgoing_outer_angular_momentum=float(outer_angular[-1]),
        outer_angular_momentum_delta=float(outer_angular[-1] - outer_angular[0]),
        deflection_angle=deflection_angle,
    )


def _angle_between(first: np.ndarray, second: np.ndarray) -> float:
    first_norm = float(np.linalg.norm(first))
    second_norm = float(np.linalg.norm(second))
    if first_norm < 1.0e-12 or second_norm < 1.0e-12:
        return 0.0
    cosine = float(np.dot(first, second) / (first_norm * second_norm))
    return float(np.arccos(np.clip(cosine, -1.0, 1.0)))
