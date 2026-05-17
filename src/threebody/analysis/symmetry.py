from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations

import numpy as np

from ..types import TrajectoryResult


@dataclass(frozen=True, slots=True)
class ChoreographySymmetryCertificate:
    """Certificate for equal-mass choreography symmetry over a periodic orbit."""

    sample_count: int
    time_shift_fraction: float
    best_permutation: tuple[int, ...]
    maximum_position_error: float
    maximum_velocity_error: float
    tolerance: float
    symmetry_resolved: bool

    def as_dict(self) -> dict[str, float | int | bool | list[int]]:
        return {
            "sample_count": self.sample_count,
            "time_shift_fraction": self.time_shift_fraction,
            "best_permutation": list(self.best_permutation),
            "maximum_position_error": self.maximum_position_error,
            "maximum_velocity_error": self.maximum_velocity_error,
            "tolerance": self.tolerance,
            "symmetry_resolved": self.symmetry_resolved,
        }


def choreography_symmetry_certificate(
    system: object,
    trajectory: TrajectoryResult,
    *,
    period: float | None = None,
    time_shift_fraction: float = 1.0 / 3.0,
    tolerance: float = 1.0e-4,
    candidate_permutations: tuple[tuple[int, ...], ...] | None = None,
) -> ChoreographySymmetryCertificate:
    """Find the best body permutation for x_i(t + T/3) = x_perm(i)(t)."""

    if not hasattr(system, "split_state") or not hasattr(system, "body_count") or not hasattr(system, "dimension"):
        raise TypeError("choreography_symmetry_certificate requires a general-body system with split_state.")
    body_count = int(getattr(system, "body_count"))
    dimension = int(getattr(system, "dimension"))
    if body_count < 2:
        raise ValueError("at least two bodies are required for choreography symmetry.")

    times = np.asarray(trajectory.t, dtype=float)
    if len(times) < 2:
        return _empty_choreography_certificate(time_shift_fraction, tolerance, body_count)
    period_value = float(times[-1] - times[0]) if period is None else float(period)
    shift = period_value * time_shift_fraction
    if period_value <= 0.0 or shift <= 0.0:
        return _empty_choreography_certificate(time_shift_fraction, tolerance, body_count)

    positions = []
    velocities = []
    for state in trajectory.y:
        position, velocity = system.split_state(state)
        positions.append(position)
        velocities.append(velocity)
    position_array = np.asarray(positions, dtype=float).reshape(len(times), body_count, dimension)
    velocity_array = np.asarray(velocities, dtype=float).reshape(len(times), body_count, dimension)

    usable = times + shift <= times[0] + period_value + 1.0e-12
    base_times = times[usable]
    if len(base_times) == 0:
        return _empty_choreography_certificate(time_shift_fraction, tolerance, body_count)
    shifted_times = base_times + shift
    base_positions = position_array[usable]
    base_velocities = velocity_array[usable]
    shifted_positions = _interpolate_body_series(times, position_array, shifted_times)
    shifted_velocities = _interpolate_body_series(times, velocity_array, shifted_times)

    if candidate_permutations is None:
        candidate_permutations = tuple(permutations(range(body_count)))
    best_permutation = candidate_permutations[0]
    best_position_error = np.inf
    best_velocity_error = np.inf
    best_score = np.inf
    for candidate in candidate_permutations:
        permutation = tuple(int(index) for index in candidate)
        position_error = float(np.max(np.linalg.norm(base_positions[:, permutation, :] - shifted_positions, axis=2)))
        velocity_error = float(np.max(np.linalg.norm(base_velocities[:, permutation, :] - shifted_velocities, axis=2)))
        score = max(position_error, velocity_error)
        if score < best_score:
            best_permutation = permutation
            best_position_error = position_error
            best_velocity_error = velocity_error
            best_score = score

    return ChoreographySymmetryCertificate(
        sample_count=int(len(base_times)),
        time_shift_fraction=float(time_shift_fraction),
        best_permutation=best_permutation,
        maximum_position_error=best_position_error,
        maximum_velocity_error=best_velocity_error,
        tolerance=tolerance,
        symmetry_resolved=bool(best_position_error <= tolerance and best_velocity_error <= tolerance),
    )


def _interpolate_body_series(times: np.ndarray, values: np.ndarray, target_times: np.ndarray) -> np.ndarray:
    body_count = values.shape[1]
    dimension = values.shape[2]
    interpolated = np.empty((len(target_times), body_count, dimension), dtype=float)
    for body in range(body_count):
        for axis in range(dimension):
            interpolated[:, body, axis] = np.interp(target_times, times, values[:, body, axis])
    return interpolated


def _empty_choreography_certificate(
    time_shift_fraction: float,
    tolerance: float,
    body_count: int,
) -> ChoreographySymmetryCertificate:
    return ChoreographySymmetryCertificate(
        sample_count=0,
        time_shift_fraction=time_shift_fraction,
        best_permutation=tuple(range(body_count)),
        maximum_position_error=np.inf,
        maximum_velocity_error=np.inf,
        tolerance=tolerance,
        symmetry_resolved=False,
    )
