from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import TrajectoryResult
from .coordinates import PAIR_INDICES, general_three_body_features
from .shape import shape_space_coordinates


@dataclass(frozen=True, slots=True)
class CenterOfMassReductionCertificate:
    """Certificate that a trajectory is already in the center-of-mass quotient frame."""

    sample_count: int
    maximum_center_norm: float
    maximum_center_velocity_norm: float
    maximum_linear_momentum_norm: float
    tolerance: float
    reduction_resolved: bool

    def as_dict(self) -> dict[str, float | int | bool]:
        return {
            "sample_count": self.sample_count,
            "maximum_center_norm": self.maximum_center_norm,
            "maximum_center_velocity_norm": self.maximum_center_velocity_norm,
            "maximum_linear_momentum_norm": self.maximum_linear_momentum_norm,
            "tolerance": self.tolerance,
            "reduction_resolved": self.reduction_resolved,
        }


@dataclass(frozen=True, slots=True)
class LagrangeJacobiIdentityCertificate:
    """Certificate for the Newtonian homogeneous-potential identity I'' = 4E + 2U."""

    sample_count: int
    maximum_absolute_residual: float
    maximum_relative_residual: float
    rms_relative_residual: float
    tolerance: float
    identity_resolved: bool

    def as_dict(self) -> dict[str, float | int | bool]:
        return {
            "sample_count": self.sample_count,
            "maximum_absolute_residual": self.maximum_absolute_residual,
            "maximum_relative_residual": self.maximum_relative_residual,
            "rms_relative_residual": self.rms_relative_residual,
            "tolerance": self.tolerance,
            "identity_resolved": self.identity_resolved,
        }


@dataclass(frozen=True, slots=True)
class SundmanInequalityCertificate:
    """Certificate for the Newtonian three-body inequality |L|^2 <= 2 I T."""

    sample_count: int
    maximum_ratio: float
    minimum_margin: float
    maximum_violation: float
    tolerance: float
    inequality_resolved: bool

    def as_dict(self) -> dict[str, float | int | bool]:
        return {
            "sample_count": self.sample_count,
            "maximum_ratio": self.maximum_ratio,
            "minimum_margin": self.minimum_margin,
            "maximum_violation": self.maximum_violation,
            "tolerance": self.tolerance,
            "inequality_resolved": self.inequality_resolved,
        }


@dataclass(frozen=True, slots=True)
class ReducedThreeBodyState:
    """Symmetry-reduced scale/shape/invariant state for a Newtonian three-body configuration."""

    time: float
    total_energy: float
    angular_momentum_norm: float
    virial_ratio: float
    hyperradius: float
    radial_velocity: float
    normalized_radial_velocity: float
    shape_area: float
    shape_anisotropy: float
    shape_orientation: float
    nearest_pair: tuple[int, int]
    nearest_distance: float
    hierarchy_ratio: float
    hierarchy_perturbation_strength: float
    escape_index: float
    collision_depth: float
    escape_depth: float
    reduced_regime_hint: str

    def as_dict(self) -> dict[str, float | int | str]:
        return {
            "time": self.time,
            "total_energy": self.total_energy,
            "angular_momentum_norm": self.angular_momentum_norm,
            "virial_ratio": self.virial_ratio,
            "hyperradius": self.hyperradius,
            "radial_velocity": self.radial_velocity,
            "normalized_radial_velocity": self.normalized_radial_velocity,
            "shape_area": self.shape_area,
            "shape_anisotropy": self.shape_anisotropy,
            "shape_orientation": self.shape_orientation,
            "nearest_pair_i": self.nearest_pair[0],
            "nearest_pair_j": self.nearest_pair[1],
            "nearest_distance": self.nearest_distance,
            "hierarchy_ratio": self.hierarchy_ratio,
            "hierarchy_perturbation_strength": self.hierarchy_perturbation_strength,
            "escape_index": self.escape_index,
            "collision_depth": self.collision_depth,
            "escape_depth": self.escape_depth,
            "reduced_regime_hint": self.reduced_regime_hint,
        }


def reduced_three_body_state(system: object, state: np.ndarray, time: float = 0.0) -> ReducedThreeBodyState:
    """Compute the shared reduced coordinates used by atlas-level diagnostics."""

    positions, velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    center = np.average(positions, axis=0, weights=masses)
    center_velocity = np.average(velocities, axis=0, weights=masses)
    centered_positions = positions - center
    centered_velocities = velocities - center_velocity
    features = general_three_body_features(system, state)
    shape = shape_space_coordinates(system, state)
    hyperradius = max(shape.hyperradius, 1.0e-12)
    radial_velocity = float(np.sum(masses[:, None] * centered_positions * centered_velocities) / (np.sum(masses) * hyperradius))
    normalized_radial_velocity = float(radial_velocity / np.sqrt(1.0 + radial_velocity**2))
    minimum_pair_distance = float(min(np.linalg.norm(positions[i] - positions[j]) for i, j in PAIR_INDICES))
    collision_depth = float(min(1.0 / max(minimum_pair_distance, 1.0e-12), 1.0 / hyperradius))
    escape_depth = float(features.escape_index / (1.0 + features.escape_index))
    regime_hint = _reduced_regime_hint(features.hierarchy_ratio, collision_depth, escape_depth, shape.anisotropy)
    return ReducedThreeBodyState(
        time=float(time),
        total_energy=features.total_energy,
        angular_momentum_norm=features.angular_momentum_norm,
        virial_ratio=features.virial_ratio,
        hyperradius=float(shape.hyperradius),
        radial_velocity=radial_velocity,
        normalized_radial_velocity=normalized_radial_velocity,
        shape_area=shape.normalized_area,
        shape_anisotropy=shape.anisotropy,
        shape_orientation=shape.orientation,
        nearest_pair=features.nearest_pair,
        nearest_distance=features.nearest_distance,
        hierarchy_ratio=features.hierarchy_ratio,
        hierarchy_perturbation_strength=features.hierarchy_perturbation_strength,
        escape_index=features.escape_index,
        collision_depth=collision_depth,
        escape_depth=escape_depth,
        reduced_regime_hint=regime_hint,
    )


def center_of_mass_reduction_certificate(
    system: object,
    trajectory: TrajectoryResult,
    *,
    stride: int = 1,
    tolerance: float = 1.0e-8,
) -> CenterOfMassReductionCertificate:
    """Check whether sampled states stay in the center-of-mass inertial frame."""

    if stride < 1:
        raise ValueError("stride must be >= 1.")
    if not hasattr(system, "split_state") or not hasattr(system, "masses"):
        raise TypeError("center_of_mass_reduction_certificate requires a massive body system.")

    masses = np.asarray(system.masses, dtype=float)
    total_mass = float(np.sum(masses))
    centers = []
    center_velocities = []
    momenta = []
    for state in trajectory.y[::stride]:
        positions, velocities = system.split_state(state)
        center = np.sum(masses[:, None] * positions, axis=0) / total_mass
        center_velocity = np.sum(masses[:, None] * velocities, axis=0) / total_mass
        momentum = np.sum(masses[:, None] * velocities, axis=0)
        centers.append(float(np.linalg.norm(center)))
        center_velocities.append(float(np.linalg.norm(center_velocity)))
        momenta.append(float(np.linalg.norm(momentum)))

    if not centers:
        return CenterOfMassReductionCertificate(
            sample_count=0,
            maximum_center_norm=np.inf,
            maximum_center_velocity_norm=np.inf,
            maximum_linear_momentum_norm=np.inf,
            tolerance=tolerance,
            reduction_resolved=False,
        )

    maximum_center_norm = float(max(centers))
    maximum_center_velocity_norm = float(max(center_velocities))
    maximum_linear_momentum_norm = float(max(momenta))
    return CenterOfMassReductionCertificate(
        sample_count=len(centers),
        maximum_center_norm=maximum_center_norm,
        maximum_center_velocity_norm=maximum_center_velocity_norm,
        maximum_linear_momentum_norm=maximum_linear_momentum_norm,
        tolerance=tolerance,
        reduction_resolved=bool(
            maximum_center_norm <= tolerance
            and maximum_center_velocity_norm <= tolerance
            and maximum_linear_momentum_norm <= tolerance
        ),
    )


def lagrange_jacobi_identity_certificate(
    system: object,
    trajectory: TrajectoryResult,
    *,
    stride: int = 1,
    tolerance: float = 1.0e-9,
) -> LagrangeJacobiIdentityCertificate:
    """Check the Lagrange-Jacobi identity along sampled Newtonian states."""

    if stride < 1:
        raise ValueError("stride must be >= 1.")
    if not hasattr(system, "split_state") or not hasattr(system, "masses") or not hasattr(system, "acceleration_field"):
        raise TypeError("lagrange_jacobi_identity_certificate requires a Newtonian massive-body system.")

    absolute_residuals = []
    relative_residuals = []
    for state in trajectory.y[::stride]:
        lhs, rhs = _lagrange_jacobi_terms(system, state)
        residual = float(lhs - rhs)
        scale = max(abs(lhs), abs(rhs), 1.0)
        absolute_residuals.append(abs(residual))
        relative_residuals.append(abs(residual) / scale)

    if not absolute_residuals:
        return LagrangeJacobiIdentityCertificate(
            sample_count=0,
            maximum_absolute_residual=np.inf,
            maximum_relative_residual=np.inf,
            rms_relative_residual=np.inf,
            tolerance=tolerance,
            identity_resolved=False,
        )

    absolute = np.asarray(absolute_residuals, dtype=float)
    relative = np.asarray(relative_residuals, dtype=float)
    maximum_relative = float(np.max(relative))
    return LagrangeJacobiIdentityCertificate(
        sample_count=int(relative.size),
        maximum_absolute_residual=float(np.max(absolute)),
        maximum_relative_residual=maximum_relative,
        rms_relative_residual=float(np.sqrt(np.mean(relative**2))),
        tolerance=tolerance,
        identity_resolved=bool(np.all(np.isfinite(relative)) and maximum_relative <= tolerance),
    )


def sundman_inequality_certificate(
    system: object,
    trajectory: TrajectoryResult,
    *,
    stride: int = 1,
    tolerance: float = 1.0e-12,
) -> SundmanInequalityCertificate:
    """Check |L|^2 <= 2 I T over sampled center-of-mass states."""

    if stride < 1:
        raise ValueError("stride must be >= 1.")
    if not hasattr(system, "split_state") or not hasattr(system, "masses"):
        raise TypeError("sundman_inequality_certificate requires a massive body system.")

    ratios = []
    for state in trajectory.y[::stride]:
        ratio = _sundman_ratio(system, state)
        ratios.append(ratio)

    if not ratios:
        return SundmanInequalityCertificate(
            sample_count=0,
            maximum_ratio=np.inf,
            minimum_margin=-np.inf,
            maximum_violation=np.inf,
            tolerance=tolerance,
            inequality_resolved=False,
        )

    ratio_array = np.asarray(ratios, dtype=float)
    maximum_ratio = float(np.max(ratio_array))
    minimum_margin = float(np.min(1.0 - ratio_array))
    maximum_violation = float(max(0.0, maximum_ratio - 1.0))
    return SundmanInequalityCertificate(
        sample_count=int(ratio_array.size),
        maximum_ratio=maximum_ratio,
        minimum_margin=minimum_margin,
        maximum_violation=maximum_violation,
        tolerance=tolerance,
        inequality_resolved=bool(np.all(np.isfinite(ratio_array)) and maximum_violation <= tolerance),
    )


def reduced_state_series(
    system: object,
    trajectory: TrajectoryResult,
    stride: int = 1,
) -> tuple[ReducedThreeBodyState, ...]:
    if stride < 1:
        raise ValueError("stride must be >= 1.")
    return tuple(
        reduced_three_body_state(system, state, time=float(time))
        for time, state in zip(trajectory.t[::stride], trajectory.y[::stride], strict=True)
    )


def _reduced_regime_hint(
    hierarchy_ratio: float,
    collision_depth: float,
    escape_depth: float,
    shape_anisotropy: float,
) -> str:
    if collision_depth > 20.0:
        return "collision_boundary"
    if escape_depth > 0.9:
        return "escape_boundary"
    if hierarchy_ratio > 5.0:
        return "hierarchy_chart"
    if shape_anisotropy < 0.5:
        return "democratic_shape"
    return "transition_region"


def _lagrange_jacobi_terms(system: object, state: np.ndarray) -> tuple[float, float]:
    positions, velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    total_mass = float(np.sum(masses))
    center = np.sum(masses[:, None] * positions, axis=0) / total_mass
    center_velocity = np.sum(masses[:, None] * velocities, axis=0) / total_mass
    centered_positions = positions - center
    centered_velocities = velocities - center_velocity
    accelerations = system.acceleration_field(positions)
    internal_kinetic = float(0.5 * np.sum(masses[:, None] * centered_velocities**2))
    potential_magnitude = _newtonian_potential_magnitude(system, positions, masses)
    internal_energy = internal_kinetic - potential_magnitude
    inertia_second_derivative = float(
        2.0 * np.sum(masses[:, None] * (centered_velocities**2 + centered_positions * accelerations))
    )
    return inertia_second_derivative, float(4.0 * internal_energy + 2.0 * potential_magnitude)


def _sundman_ratio(system: object, state: np.ndarray) -> float:
    positions, velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    total_mass = float(np.sum(masses))
    center = np.sum(masses[:, None] * positions, axis=0) / total_mass
    center_velocity = np.sum(masses[:, None] * velocities, axis=0) / total_mass
    centered_positions = positions - center
    centered_velocities = velocities - center_velocity
    inertia = float(np.sum(masses[:, None] * centered_positions**2))
    kinetic = float(0.5 * np.sum(masses[:, None] * centered_velocities**2))
    angular_momentum_norm = _centered_angular_momentum_norm(masses, centered_positions, centered_velocities)
    denominator = 2.0 * inertia * kinetic
    if denominator <= 0.0:
        return 0.0 if angular_momentum_norm <= 1.0e-15 else np.inf
    return float(angular_momentum_norm**2 / denominator)


def _centered_angular_momentum_norm(masses: np.ndarray, positions: np.ndarray, velocities: np.ndarray) -> float:
    if positions.shape[1] == 2:
        angular = np.sum(masses * (positions[:, 0] * velocities[:, 1] - positions[:, 1] * velocities[:, 0]))
        return float(abs(angular))
    angular_vector = np.sum(masses[:, None] * np.cross(positions, velocities), axis=0)
    return float(np.linalg.norm(angular_vector))


def _newtonian_potential_magnitude(system: object, positions: np.ndarray, masses: np.ndarray) -> float:
    gravitational_constant = float(getattr(system, "gravitational_constant", 1.0))
    total = 0.0
    for first, second in PAIR_INDICES:
        distance = float(np.linalg.norm(positions[second] - positions[first]))
        total += gravitational_constant * masses[first] * masses[second] / max(distance, 1.0e-18)
    return float(total)
