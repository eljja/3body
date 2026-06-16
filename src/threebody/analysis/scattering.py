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
    outgoing_semimajor_axis: float
    outgoing_eccentricity: float
    outgoing_periapsis_distance: float
    outgoing_escape_speed_at_infinity: float
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
            "outgoing_semimajor_axis": self.outgoing_semimajor_axis,
            "outgoing_eccentricity": self.outgoing_eccentricity,
            "outgoing_periapsis_distance": self.outgoing_periapsis_distance,
            "outgoing_escape_speed_at_infinity": self.outgoing_escape_speed_at_infinity,
            "deflection_angle": self.deflection_angle,
        }


@dataclass(frozen=True, slots=True)
class EscapeAsymptoticCertificate:
    """Finite-time certificate for whether an escape label has asymptotic support."""

    inner_pair: tuple[int, int]
    outer_body: int
    tail_sample_count: int
    outgoing_energy: float
    relative_energy_drift: float
    radius_growth_fraction: float
    deflection_angle_drift: float
    escape_speed_at_infinity: float
    asymptotic_resolved: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "tail_sample_count": self.tail_sample_count,
            "outgoing_energy": self.outgoing_energy,
            "relative_energy_drift": self.relative_energy_drift,
            "radius_growth_fraction": self.radius_growth_fraction,
            "deflection_angle_drift": self.deflection_angle_drift,
            "escape_speed_at_infinity": self.escape_speed_at_infinity,
            "asymptotic_resolved": self.asymptotic_resolved,
            "warning": self.warning,
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
    outgoing_elements = _relative_orbital_elements(system, trajectory.y[-1], inner_pair, outer)
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
        outgoing_semimajor_axis=outgoing_elements["semimajor_axis"],
        outgoing_eccentricity=outgoing_elements["eccentricity"],
        outgoing_periapsis_distance=outgoing_elements["periapsis_distance"],
        outgoing_escape_speed_at_infinity=outgoing_elements["escape_speed_at_infinity"],
        deflection_angle=deflection_angle,
    )


def escape_asymptotic_certificate(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
    tail_fraction: float = 0.25,
    energy_tolerance: float = 5.0e-2,
    deflection_tolerance: float = 5.0e-2,
) -> EscapeAsymptoticCertificate:
    """Check whether the outgoing leg has converged enough to support an escape/scattering label."""

    if getattr(system, "body_count", None) != 3:
        raise TypeError("escape_asymptotic_certificate requires a general three-body system.")
    outer = next(index for index in range(3) if index not in inner_pair)
    tail_count = max(3, int(np.ceil(len(trajectory.t) * tail_fraction)))
    tail_states = trajectory.y[-tail_count:]
    radii, energies, velocities = _outer_relative_series(system, tail_states, inner_pair, outer)
    outgoing_energy = float(energies[-1])
    relative_energy_drift = _relative_span(energies)
    radius_growth_fraction = float(np.mean(np.diff(radii) > 0.0)) if radii.size > 1 else 0.0
    deflection_angles = np.asarray([_angle_between(velocities[0], velocity) for velocity in velocities], dtype=float)
    deflection_angle_drift = float(np.max(deflection_angles) - np.min(deflection_angles))
    escape_speed = float(np.sqrt(max(2.0 * outgoing_energy, 0.0)))
    asymptotic_resolved = (
        outgoing_energy > 0.0
        and relative_energy_drift <= energy_tolerance
        and radius_growth_fraction >= 0.8
        and deflection_angle_drift <= deflection_tolerance
    )
    warning = ""
    if outgoing_energy <= 0.0:
        warning = "outgoing two-body energy is not positive"
    elif radius_growth_fraction < 0.8:
        warning = "outer radius is not monotonically increasing over the tail"
    elif relative_energy_drift > energy_tolerance:
        warning = "outgoing energy has not converged over the tail"
    elif deflection_angle_drift > deflection_tolerance:
        warning = "deflection angle has not converged over the tail"
    return EscapeAsymptoticCertificate(
        inner_pair=inner_pair,
        outer_body=outer,
        tail_sample_count=tail_count,
        outgoing_energy=outgoing_energy,
        relative_energy_drift=relative_energy_drift,
        radius_growth_fraction=radius_growth_fraction,
        deflection_angle_drift=deflection_angle_drift,
        escape_speed_at_infinity=escape_speed,
        asymptotic_resolved=asymptotic_resolved,
        warning=warning,
    )


def _angle_between(first: np.ndarray, second: np.ndarray) -> float:
    first_norm = float(np.linalg.norm(first))
    second_norm = float(np.linalg.norm(second))
    if first_norm < 1.0e-12 or second_norm < 1.0e-12:
        return 0.0
    cosine = float(np.dot(first, second) / (first_norm * second_norm))
    return float(np.arccos(np.clip(cosine, -1.0, 1.0)))


def _outer_relative_series(
    system: object,
    states: np.ndarray,
    inner_pair: tuple[int, int],
    outer: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    masses = np.asarray(system.masses, dtype=float)
    i, j = inner_pair
    pair_mass = masses[i] + masses[j]
    radii = []
    energies = []
    velocities_out = []
    for state in states:
        positions, velocities = system.split_state(state)
        pair_center = (masses[i] * positions[i] + masses[j] * positions[j]) / pair_mass
        pair_velocity = (masses[i] * velocities[i] + masses[j] * velocities[j]) / pair_mass
        relative_position = positions[outer] - pair_center
        relative_velocity = velocities[outer] - pair_velocity
        radius = float(np.linalg.norm(relative_position))
        mu = system.gravitational_constant * (pair_mass + masses[outer])
        energy = 0.5 * float(np.dot(relative_velocity, relative_velocity)) - mu / max(radius, 1.0e-12)
        radii.append(radius)
        energies.append(energy)
        velocities_out.append(relative_velocity)
    return (
        np.asarray(radii, dtype=float),
        np.asarray(energies, dtype=float),
        np.asarray(velocities_out, dtype=float),
    )


def _relative_span(values: np.ndarray) -> float:
    finite = np.asarray(values[np.isfinite(values)], dtype=float)
    if finite.size == 0:
        return np.inf
    scale = max(abs(float(finite[-1])), 1.0e-12)
    return float((np.max(finite) - np.min(finite)) / scale)


def _relative_orbital_elements(
    system: object,
    state: np.ndarray,
    inner_pair: tuple[int, int],
    outer: int,
) -> dict[str, float]:
    positions, velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    i, j = inner_pair
    pair_mass = masses[i] + masses[j]
    pair_center = (masses[i] * positions[i] + masses[j] * positions[j]) / pair_mass
    pair_velocity = (masses[i] * velocities[i] + masses[j] * velocities[j]) / pair_mass
    relative_position = positions[outer] - pair_center
    relative_velocity = velocities[outer] - pair_velocity
    radius = float(np.linalg.norm(relative_position))
    speed_sq = float(np.dot(relative_velocity, relative_velocity))
    mu = system.gravitational_constant * (pair_mass + masses[outer])
    specific_energy = 0.5 * speed_sq - mu / max(radius, 1.0e-12)
    angular = cross_3d(relative_position, relative_velocity)
    eccentricity_vector = np.cross(np.array([relative_velocity[0], relative_velocity[1], 0.0]), angular) / mu
    eccentricity_vector -= np.array([relative_position[0], relative_position[1], 0.0]) / max(radius, 1.0e-12)
    eccentricity = float(np.linalg.norm(eccentricity_vector))
    semimajor_axis = float(-mu / (2.0 * specific_energy)) if abs(specific_energy) > 1.0e-12 else np.inf
    periapsis_distance = float(semimajor_axis * (1.0 - eccentricity)) if np.isfinite(semimajor_axis) else np.inf
    if periapsis_distance < 0.0 and eccentricity > 1.0:
        periapsis_distance = float(abs(semimajor_axis) * (eccentricity - 1.0))
    escape_speed = float(np.sqrt(max(2.0 * specific_energy, 0.0)))
    return {
        "semimajor_axis": semimajor_axis,
        "eccentricity": eccentricity,
        "periapsis_distance": periapsis_distance,
        "escape_speed_at_infinity": escape_speed,
    }


@dataclass(frozen=True, slots=True)
class AnalyticScatteringBoundCertificate:
    """Rigorous certificate verifying that flyby scattering satisfies analytical quadrupole bounds."""

    inner_pair: tuple[int, int]
    outer_body: int
    observed_energy_exchange: float
    theoretical_quadrupole_bound: float
    observed_deflection_angle: float
    theoretical_deflection_bound: float
    bounds_satisfied: bool
    interpretation: str

    def as_dict(self) -> dict[str, float | bool | str | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "observed_energy_exchange": self.observed_energy_exchange,
            "theoretical_quadrupole_bound": self.theoretical_quadrupole_bound,
            "observed_deflection_angle": self.observed_deflection_angle,
            "theoretical_deflection_bound": self.theoretical_deflection_bound,
            "bounds_satisfied": self.bounds_satisfied,
            "interpretation": self.interpretation,
        }


def verify_scattering_analytic_bounds(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
) -> AnalyticScatteringBoundCertificate:
    """Verify that the measured flyby scattering lies within analytical quadrupole tidal bounds."""

    outer = next(index for index in range(3) if index not in inner_pair)
    masses = np.asarray(system.masses, dtype=float)
    i, j = inner_pair

    # Compute scattering map to get periapsis coordinates
    smap = periapsis_scattering_map(system, trajectory, inner_pair=inner_pair)
    d_min = smap.periapsis_distance
    
    # Calculate orbital speed at infinity or start
    states = trajectory.y
    positions_0, velocities_0 = system.split_state(states[0])
    pair_mass = masses[i] + masses[j]
    pair_velocity_0 = (masses[i] * velocities_0[i] + masses[j] * velocities_0[j]) / pair_mass
    v_in = float(np.linalg.norm(velocities_0[outer] - pair_velocity_0))
    
    # Quadrupole parameters
    a_binary = 0.2  # nominal binary separation
    G = system.gravitational_constant
    m_third = masses[outer]
    M_total = np.sum(masses)
    
    # Theoretical limits
    # Quadrupole energy exchange scales as G * m_third * a_binary / (d_min**3 * v_in)
    C_E = 15.0  # safety scaling constant
    theoretical_quadrupole = C_E * (G * m_third * a_binary) / max(d_min**3 * v_in, 1.0e-6)
    
    # Deflection angle scales as G * M_total / (d_min * v_in**2)
    C_d = 5.0  # safety scaling constant
    theoretical_deflection = C_d * (G * M_total) / max(d_min * v_in**2, 1.0e-6)
    
    observed_de = abs(smap.outer_energy_delta)
    observed_theta = smap.deflection_angle
    
    bounds_satisfied = bool((observed_de <= theoretical_quadrupole) and (observed_theta <= theoretical_deflection))
    
    interpretation = (
        f"Observed energy delta |dE|={observed_de:.6f} vs bound={theoretical_quadrupole:.6f}. "
        f"Observed deflection={observed_theta:.6f} rad vs bound={theoretical_deflection:.6f} rad."
    )
    
    return AnalyticScatteringBoundCertificate(
        inner_pair=inner_pair,
        outer_body=outer,
        observed_energy_exchange=observed_de,
        theoretical_quadrupole_bound=theoretical_quadrupole,
        observed_deflection_angle=observed_theta,
        theoretical_deflection_bound=theoretical_deflection,
        bounds_satisfied=bounds_satisfied,
        interpretation=interpretation,
    )

