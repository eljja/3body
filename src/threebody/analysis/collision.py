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
class LeviCivitaBinaryChart:
    """Planar Levi-Civita lift for one binary relative coordinate.

    The relative vector r=(x,y) is represented by the complex square u^2.
    Regularized time is chosen by dt/ds=|r|=|u|^2, so u_prime is du/ds.
    """

    pair: tuple[int, int]
    relative_position: np.ndarray
    relative_velocity: np.ndarray
    u: np.ndarray
    u_prime: np.ndarray
    radius: float
    regularized_radius: float
    reconstruction_error: float

    def as_dict(self) -> dict[str, float | tuple[int, int]]:
        return {
            "pair": self.pair,
            "radius": self.radius,
            "regularized_radius": self.regularized_radius,
            "u0": float(self.u[0]),
            "u1": float(self.u[1]),
            "u_prime0": float(self.u_prime[0]),
            "u_prime1": float(self.u_prime[1]),
            "reconstruction_error": self.reconstruction_error,
        }


@dataclass(frozen=True, slots=True)
class LeviCivitaChartCertificate:
    """Interval-level check that the binary collision chart is numerically well-defined."""

    sample_count: int
    pair: tuple[int, int]
    minimum_radius: float
    minimum_regularized_radius: float
    maximum_regularized_speed: float
    maximum_branch_jump: float
    maximum_reconstruction_error: float
    chart_resolved: bool

    def as_dict(self) -> dict[str, float | int | bool | tuple[int, int]]:
        return {
            "sample_count": self.sample_count,
            "pair": self.pair,
            "minimum_radius": self.minimum_radius,
            "minimum_regularized_radius": self.minimum_regularized_radius,
            "maximum_regularized_speed": self.maximum_regularized_speed,
            "maximum_branch_jump": self.maximum_branch_jump,
            "maximum_reconstruction_error": self.maximum_reconstruction_error,
            "chart_resolved": self.chart_resolved,
        }


@dataclass(frozen=True, slots=True)
class LeviCivitaRegularizedFlowState:
    """Regularized-time second-order state for one binary pair."""

    pair: tuple[int, int]
    u: np.ndarray
    u_prime: np.ndarray
    u_double_prime: np.ndarray
    radius: float
    perturbation_acceleration_norm: float
    relative_acceleration_norm: float

    def as_dict(self) -> dict[str, float | tuple[int, int]]:
        return {
            "pair": self.pair,
            "u0": float(self.u[0]),
            "u1": float(self.u[1]),
            "u_prime0": float(self.u_prime[0]),
            "u_prime1": float(self.u_prime[1]),
            "u_double_prime0": float(self.u_double_prime[0]),
            "u_double_prime1": float(self.u_double_prime[1]),
            "radius": self.radius,
            "perturbation_acceleration_norm": self.perturbation_acceleration_norm,
            "relative_acceleration_norm": self.relative_acceleration_norm,
        }


@dataclass(frozen=True, slots=True)
class LeviCivitaFlowCertificate:
    """Check that the regularized binary RHS is defined and optionally residual-tested."""

    sample_count: int
    pair: tuple[int, int]
    flow_defined: bool
    minimum_radius: float
    maximum_rhs_norm: float
    maximum_perturbation_acceleration_norm: float
    maximum_finite_difference_residual: float | None
    residual_resolved: bool

    def as_dict(self) -> dict[str, float | int | bool | tuple[int, int] | None]:
        return {
            "sample_count": self.sample_count,
            "pair": self.pair,
            "flow_defined": self.flow_defined,
            "minimum_radius": self.minimum_radius,
            "maximum_rhs_norm": self.maximum_rhs_norm,
            "maximum_perturbation_acceleration_norm": self.maximum_perturbation_acceleration_norm,
            "maximum_finite_difference_residual": self.maximum_finite_difference_residual,
            "residual_resolved": self.residual_resolved,
        }


@dataclass(frozen=True, slots=True)
class LeviCivitaEquivalenceCertificate:
    """Local equivalence check between regularized and inertial relative dynamics."""

    sample_count: int
    pair: tuple[int, int]
    maximum_position_residual: float
    maximum_velocity_residual: float
    maximum_acceleration_residual: float
    equivalence_resolved: bool

    def as_dict(self) -> dict[str, float | int | bool | tuple[int, int]]:
        return {
            "sample_count": self.sample_count,
            "pair": self.pair,
            "maximum_position_residual": self.maximum_position_residual,
            "maximum_velocity_residual": self.maximum_velocity_residual,
            "maximum_acceleration_residual": self.maximum_acceleration_residual,
            "equivalence_resolved": self.equivalence_resolved,
        }


@dataclass(frozen=True, slots=True)
class LeviCivitaTidalBoundCertificate:
    """Conservative third-body tidal bound relative to the inner Kepler core."""

    sample_count: int
    pair: tuple[int, int]
    minimum_outer_distance: float
    maximum_inner_distance: float
    tidal_constant_bound: float
    maximum_bound_ratio: float
    maximum_observed_ratio: float
    bound_satisfied: bool

    def as_dict(self) -> dict[str, float | int | bool | tuple[int, int]]:
        return {
            "sample_count": self.sample_count,
            "pair": self.pair,
            "minimum_outer_distance": self.minimum_outer_distance,
            "maximum_inner_distance": self.maximum_inner_distance,
            "tidal_constant_bound": self.tidal_constant_bound,
            "maximum_bound_ratio": self.maximum_bound_ratio,
            "maximum_observed_ratio": self.maximum_observed_ratio,
            "bound_satisfied": self.bound_satisfied,
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
    levi_civita_pair: tuple[int, int] | None
    levi_civita_chart_resolved: bool
    levi_civita_max_reconstruction_error: float | None
    levi_civita_flow_defined: bool
    levi_civita_flow_residual: float | None
    levi_civita_equivalence_resolved: bool
    levi_civita_equivalence_acceleration_residual: float | None
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | tuple[int, int] | None]:
        return {
            "sample_count": self.sample_count,
            "minimum_hyperradius": self.minimum_hyperradius,
            "minimum_pair_distance": self.minimum_pair_distance,
            "maximum_collision_depth": self.maximum_collision_depth,
            "maximum_inward_speed": self.maximum_inward_speed,
            "collision_types": ",".join(self.collision_types),
            "regularization_required": self.regularization_required,
            "levi_civita_pair": self.levi_civita_pair,
            "levi_civita_chart_resolved": self.levi_civita_chart_resolved,
            "levi_civita_max_reconstruction_error": self.levi_civita_max_reconstruction_error,
            "levi_civita_flow_defined": self.levi_civita_flow_defined,
            "levi_civita_flow_residual": self.levi_civita_flow_residual,
            "levi_civita_equivalence_resolved": self.levi_civita_equivalence_resolved,
            "levi_civita_equivalence_acceleration_residual": self.levi_civita_equivalence_acceleration_residual,
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


def levi_civita_binary_chart(system: object, state: np.ndarray, pair: tuple[int, int]) -> LeviCivitaBinaryChart:
    """Lift one planar binary relative state into a Levi-Civita collision chart."""

    if getattr(system, "dimension", None) != 2:
        raise ValueError("Levi-Civita binary chart is only implemented for planar systems.")
    positions, velocities = system.split_state(state)
    i, j = pair
    relative_position = np.asarray(positions[j] - positions[i], dtype=float)
    relative_velocity = np.asarray(velocities[j] - velocities[i], dtype=float)
    radius = float(np.linalg.norm(relative_position))
    if radius <= 0.0:
        raise ValueError("Levi-Civita chart cannot choose a square-root branch at exact collision.")
    u = _levi_civita_square_root(relative_position)
    matrix = np.array([[u[0], -u[1]], [u[1], u[0]]], dtype=float)
    u_prime = 0.5 * matrix.T @ relative_velocity
    reconstructed_position = _levi_civita_square(u)
    reconstruction_error = float(np.linalg.norm(reconstructed_position - relative_position))
    return LeviCivitaBinaryChart(
        pair=pair,
        relative_position=relative_position,
        relative_velocity=relative_velocity,
        u=u,
        u_prime=u_prime,
        radius=radius,
        regularized_radius=float(np.linalg.norm(u)),
        reconstruction_error=reconstruction_error,
    )


def levi_civita_chart_certificate(
    system: object,
    trajectory: TrajectoryResult,
    start_index: int = 0,
    end_index: int | None = None,
    pair: tuple[int, int] | None = None,
    reconstruction_tolerance: float = 1.0e-8,
) -> LeviCivitaChartCertificate:
    """Check that a consistent Levi-Civita chart exists over an interval."""

    if getattr(system, "body_count", None) != 3:
        raise TypeError("levi_civita_chart_certificate requires a general three-body system.")
    if getattr(system, "dimension", None) != 2:
        raise ValueError("levi_civita_chart_certificate is only implemented for planar systems.")
    end = len(trajectory.t) - 1 if end_index is None else min(end_index, len(trajectory.t) - 1)
    start = max(0, min(start_index, end))
    if pair is None:
        pair = _dominant_close_pair(system, trajectory, start, end)
    charts = _continuous_levi_civita_charts(
        tuple(levi_civita_binary_chart(system, state, pair) for state in trajectory.y[start : end + 1])
    )
    maximum_reconstruction_error = float(max(chart.reconstruction_error for chart in charts))
    branch_jumps = [
        float(np.linalg.norm(charts[index].u - charts[index - 1].u))
        for index in range(1, len(charts))
    ]
    chart_resolved = bool(np.isfinite(maximum_reconstruction_error) and maximum_reconstruction_error <= reconstruction_tolerance)
    return LeviCivitaChartCertificate(
        sample_count=len(charts),
        pair=pair,
        minimum_radius=float(min(chart.radius for chart in charts)),
        minimum_regularized_radius=float(min(chart.regularized_radius for chart in charts)),
        maximum_regularized_speed=float(max(np.linalg.norm(chart.u_prime) for chart in charts)),
        maximum_branch_jump=0.0 if not branch_jumps else float(max(branch_jumps)),
        maximum_reconstruction_error=maximum_reconstruction_error,
        chart_resolved=chart_resolved,
    )


def levi_civita_regularized_flow_state(
    system: object,
    state: np.ndarray,
    pair: tuple[int, int],
) -> LeviCivitaRegularizedFlowState:
    """Evaluate the perturbation-aware Levi-Civita regularized RHS.

    The inertial relative equation is split as
    r_ddot = -G(m_i+m_j) r/|r|^3 + third-body perturbation.
    With r = u^2 and dt/ds = |r|, this function returns u'' in regularized
    time s.
    """

    chart = levi_civita_binary_chart(system, state, pair)
    return _levi_civita_regularized_flow_state_from_chart(system, state, chart)


def _levi_civita_regularized_flow_state_from_chart(
    system: object,
    state: np.ndarray,
    chart: LeviCivitaBinaryChart,
) -> LeviCivitaRegularizedFlowState:
    positions, _velocities = system.split_state(state)
    i, j = chart.pair
    masses = np.asarray(system.masses, dtype=float)
    accelerations = system.acceleration_field(positions)
    relative_acceleration = np.asarray(accelerations[j] - accelerations[i], dtype=float)
    mu = float(system.gravitational_constant * (masses[i] + masses[j]))
    kepler_acceleration = -mu * chart.relative_position / max(chart.radius**3, 1.0e-18)
    perturbation = relative_acceleration - kepler_acceleration
    u_double_prime = _levi_civita_u_double_prime(
        chart.u,
        chart.u_prime,
        chart.relative_velocity,
        relative_acceleration,
    )
    return LeviCivitaRegularizedFlowState(
        pair=chart.pair,
        u=chart.u,
        u_prime=chart.u_prime,
        u_double_prime=u_double_prime,
        radius=chart.radius,
        perturbation_acceleration_norm=float(np.linalg.norm(perturbation)),
        relative_acceleration_norm=float(np.linalg.norm(relative_acceleration)),
    )


def levi_civita_flow_certificate(
    system: object,
    trajectory: TrajectoryResult,
    start_index: int = 0,
    end_index: int | None = None,
    pair: tuple[int, int] | None = None,
    residual_tolerance: float = 1.0e-4,
) -> LeviCivitaFlowCertificate:
    """Evaluate regularized RHS consistency over an interval."""

    if getattr(system, "body_count", None) != 3:
        raise TypeError("levi_civita_flow_certificate requires a general three-body system.")
    if getattr(system, "dimension", None) != 2:
        raise ValueError("levi_civita_flow_certificate is only implemented for planar systems.")
    end = len(trajectory.t) - 1 if end_index is None else min(end_index, len(trajectory.t) - 1)
    start = max(0, min(start_index, end))
    if pair is None:
        pair = _dominant_close_pair(system, trajectory, start, end)
    charts = _continuous_levi_civita_charts(
        tuple(levi_civita_binary_chart(system, state, pair) for state in trajectory.y[start : end + 1])
    )
    flow_states = tuple(
        _levi_civita_regularized_flow_state_from_chart(system, state, chart)
        for state, chart in zip(trajectory.y[start : end + 1], charts, strict=True)
    )
    flow_defined = all(
        np.all(np.isfinite(flow.u_double_prime)) and np.all(np.isfinite(flow.u_prime))
        for flow in flow_states
    )
    residual = _regularized_flow_residual(system, trajectory, start, end, pair, flow_states)
    residual_resolved = residual is not None and residual <= residual_tolerance
    return LeviCivitaFlowCertificate(
        sample_count=len(flow_states),
        pair=pair,
        flow_defined=flow_defined,
        minimum_radius=float(min(flow.radius for flow in flow_states)),
        maximum_rhs_norm=float(max(np.linalg.norm(flow.u_double_prime) for flow in flow_states)),
        maximum_perturbation_acceleration_norm=float(
            max(flow.perturbation_acceleration_norm for flow in flow_states)
        ),
        maximum_finite_difference_residual=residual,
        residual_resolved=residual_resolved,
    )


def levi_civita_equivalence_certificate(
    system: object,
    trajectory: TrajectoryResult,
    start_index: int = 0,
    end_index: int | None = None,
    pair: tuple[int, int] | None = None,
    position_tolerance: float = 1.0e-8,
    velocity_tolerance: float = 1.0e-8,
    acceleration_tolerance: float = 1.0e-7,
) -> LeviCivitaEquivalenceCertificate:
    """Check that regularized variables reconstruct inertial relative dynamics."""

    if getattr(system, "body_count", None) != 3:
        raise TypeError("levi_civita_equivalence_certificate requires a general three-body system.")
    if getattr(system, "dimension", None) != 2:
        raise ValueError("levi_civita_equivalence_certificate is only implemented for planar systems.")
    end = len(trajectory.t) - 1 if end_index is None else min(end_index, len(trajectory.t) - 1)
    start = max(0, min(start_index, end))
    if pair is None:
        pair = _dominant_close_pair(system, trajectory, start, end)
    charts = _continuous_levi_civita_charts(
        tuple(levi_civita_binary_chart(system, state, pair) for state in trajectory.y[start : end + 1])
    )
    position_residuals = []
    velocity_residuals = []
    acceleration_residuals = []
    for state, chart in zip(trajectory.y[start : end + 1], charts, strict=True):
        flow = _levi_civita_regularized_flow_state_from_chart(system, state, chart)
        positions, _velocities = system.split_state(state)
        i, j = pair
        relative_acceleration = system.acceleration_field(positions)[j] - system.acceleration_field(positions)[i]
        position_residuals.append(float(np.linalg.norm(_levi_civita_square(chart.u) - chart.relative_position)))
        velocity_residuals.append(float(np.linalg.norm(_levi_civita_velocity(chart.u, chart.u_prime) - chart.relative_velocity)))
        acceleration_residuals.append(
            float(
                np.linalg.norm(
                    _levi_civita_acceleration(chart.u, chart.u_prime, flow.u_double_prime)
                    - relative_acceleration
                )
            )
        )
    max_position = float(max(position_residuals))
    max_velocity = float(max(velocity_residuals))
    max_acceleration = float(max(acceleration_residuals))
    return LeviCivitaEquivalenceCertificate(
        sample_count=len(charts),
        pair=pair,
        maximum_position_residual=max_position,
        maximum_velocity_residual=max_velocity,
        maximum_acceleration_residual=max_acceleration,
        equivalence_resolved=(
            max_position <= position_tolerance
            and max_velocity <= velocity_tolerance
            and max_acceleration <= acceleration_tolerance
        ),
    )


def levi_civita_tidal_bound_certificate(
    system: object,
    trajectory: TrajectoryResult,
    start_index: int = 0,
    end_index: int | None = None,
    pair: tuple[int, int] | None = None,
) -> LeviCivitaTidalBoundCertificate:
    """Bound third-body forcing by a tidal Lipschitz constant on a finite interval."""

    if getattr(system, "body_count", None) != 3:
        raise TypeError("levi_civita_tidal_bound_certificate requires a general three-body system.")
    if getattr(system, "dimension", None) != 2:
        raise ValueError("levi_civita_tidal_bound_certificate is only implemented for planar systems.")
    end = len(trajectory.t) - 1 if end_index is None else min(end_index, len(trajectory.t) - 1)
    start = max(0, min(start_index, end))
    if pair is None:
        pair = _dominant_close_pair(system, trajectory, start, end)
    i, j = pair
    outer = next(index for index in range(3) if index not in pair)
    masses = np.asarray(system.masses, dtype=float)
    inner_mass = float(masses[i] + masses[j])
    outer_mass = float(masses[outer])
    minimum_outer_distance = np.inf
    maximum_inner_distance = 0.0
    maximum_observed_ratio = 0.0
    maximum_bound_ratio = 0.0
    maximum_tidal_constant = 0.0
    for state in trajectory.y[start : end + 1]:
        positions, _velocities = system.split_state(state)
        inner_distance = float(np.linalg.norm(positions[j] - positions[i]))
        outer_distance = float(
            min(
                np.linalg.norm(positions[outer] - positions[i]),
                np.linalg.norm(positions[outer] - positions[j]),
            )
        )
        minimum_outer_distance = min(minimum_outer_distance, outer_distance)
        maximum_inner_distance = max(maximum_inner_distance, inner_distance)
        tidal_constant = float((2.0 * outer_mass / inner_mass) / max(outer_distance**3, 1.0e-18))
        bound_ratio = float(tidal_constant * inner_distance**3)
        maximum_tidal_constant = max(maximum_tidal_constant, tidal_constant)
        maximum_bound_ratio = max(maximum_bound_ratio, bound_ratio)
        observed_ratio = _observed_perturbation_to_kepler_ratio(system, state, pair)
        maximum_observed_ratio = max(maximum_observed_ratio, observed_ratio)
    return LeviCivitaTidalBoundCertificate(
        sample_count=end - start + 1,
        pair=pair,
        minimum_outer_distance=float(minimum_outer_distance),
        maximum_inner_distance=maximum_inner_distance,
        tidal_constant_bound=maximum_tidal_constant,
        maximum_bound_ratio=maximum_bound_ratio,
        maximum_observed_ratio=maximum_observed_ratio,
        bound_satisfied=maximum_observed_ratio <= maximum_bound_ratio,
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
    levi_civita: LeviCivitaChartCertificate | None = None
    flow: LeviCivitaFlowCertificate | None = None
    equivalence: LeviCivitaEquivalenceCertificate | None = None
    if regularization_required and getattr(system, "dimension", None) == 2:
        levi_civita = levi_civita_chart_certificate(system, trajectory, start_index=start, end_index=end)
        flow = levi_civita_flow_certificate(
            system,
            trajectory,
            start_index=start,
            end_index=end,
            pair=levi_civita.pair,
        )
        equivalence = levi_civita_equivalence_certificate(
            system,
            trajectory,
            start_index=start,
            end_index=end,
            pair=levi_civita.pair,
        )
    warning = ""
    if regularization_required:
        if equivalence is not None and equivalence.equivalence_resolved:
            warning = "Levi-Civita local equivalence residual is resolved; near-collision analytic theorem remains unproved"
        elif flow is not None and flow.flow_defined:
            warning = "Levi-Civita regularized RHS is defined; inertial equivalence certificate remains unresolved"
        elif levi_civita is not None and levi_civita.chart_resolved:
            warning = "Levi-Civita chart is resolved; regularized time-flow construction remains incomplete"
        else:
            warning = "regularized collision coordinates are required before promoting a close-encounter law"
    return CollisionRegularizationCertificate(
        sample_count=len(diagnostics),
        minimum_hyperradius=minimum_hyperradius,
        minimum_pair_distance=minimum_pair_distance,
        maximum_collision_depth=maximum_collision_depth,
        maximum_inward_speed=maximum_inward_speed,
        collision_types=collision_types,
        regularization_required=regularization_required,
        levi_civita_pair=None if levi_civita is None else levi_civita.pair,
        levi_civita_chart_resolved=False if levi_civita is None else levi_civita.chart_resolved,
        levi_civita_max_reconstruction_error=None if levi_civita is None else levi_civita.maximum_reconstruction_error,
        levi_civita_flow_defined=False if flow is None else flow.flow_defined,
        levi_civita_flow_residual=None if flow is None else flow.maximum_finite_difference_residual,
        levi_civita_equivalence_resolved=False if equivalence is None else equivalence.equivalence_resolved,
        levi_civita_equivalence_acceleration_residual=(
            None if equivalence is None else equivalence.maximum_acceleration_residual
        ),
        warning=warning,
    )


def _levi_civita_u_double_prime(
    u: np.ndarray,
    u_prime: np.ndarray,
    relative_velocity: np.ndarray,
    relative_acceleration: np.ndarray,
) -> np.ndarray:
    radius = float(np.dot(u, u))
    radius_prime = float(2.0 * np.dot(u, u_prime))
    relative_position_double_prime_s = radius**2 * relative_acceleration + radius_prime * relative_velocity
    u_prime_square = _levi_civita_square(u_prime)
    multiplication = np.array([[u[0], -u[1]], [u[1], u[0]]], dtype=float)
    return 0.5 * multiplication.T @ (relative_position_double_prime_s - 2.0 * u_prime_square) / max(radius, 1.0e-18)


def _regularized_flow_residual(
    system: object,
    trajectory: TrajectoryResult,
    start: int,
    end: int,
    pair: tuple[int, int],
    flow_states: tuple[LeviCivitaRegularizedFlowState, ...],
) -> float | None:
    if len(flow_states) < 3:
        return None
    times = trajectory.t[start : end + 1]
    radii = np.asarray([flow.radius for flow in flow_states], dtype=float)
    s = np.zeros(len(times), dtype=float)
    for index in range(1, len(times)):
        dt = float(times[index] - times[index - 1])
        mean_radius = max(0.5 * (radii[index] + radii[index - 1]), 1.0e-18)
        s[index] = s[index - 1] + dt / mean_radius
    residuals = []
    charts = _continuous_levi_civita_charts(
        tuple(levi_civita_binary_chart(system, state, pair) for state in trajectory.y[start : end + 1])
    )
    u_primes = np.asarray([chart.u_prime for chart in charts], dtype=float)
    for index in range(1, len(flow_states) - 1):
        denominator = float(s[index + 1] - s[index - 1])
        if denominator <= 0.0:
            continue
        finite_difference = (u_primes[index + 1] - u_primes[index - 1]) / denominator
        residuals.append(float(np.linalg.norm(finite_difference - flow_states[index].u_double_prime)))
    return None if not residuals else float(max(residuals))


def _observed_perturbation_to_kepler_ratio(system: object, state: np.ndarray, pair: tuple[int, int]) -> float:
    positions, _velocities = system.split_state(state)
    i, j = pair
    masses = np.asarray(system.masses, dtype=float)
    accelerations = system.acceleration_field(positions)
    relative_acceleration = np.asarray(accelerations[j] - accelerations[i], dtype=float)
    relative_position = np.asarray(positions[j] - positions[i], dtype=float)
    radius = float(np.linalg.norm(relative_position))
    mu = float(system.gravitational_constant * (masses[i] + masses[j]))
    kepler_acceleration = -mu * relative_position / max(radius**3, 1.0e-18)
    perturbation = relative_acceleration - kepler_acceleration
    kepler_norm = mu / max(radius**2, 1.0e-18)
    return float(np.linalg.norm(perturbation) / max(kepler_norm, 1.0e-18))


def _levi_civita_velocity(u: np.ndarray, u_prime: np.ndarray) -> np.ndarray:
    radius = max(float(np.dot(u, u)), 1.0e-18)
    multiplication = np.array([[u[0], -u[1]], [u[1], u[0]]], dtype=float)
    return 2.0 * multiplication @ u_prime / radius


def _levi_civita_acceleration(u: np.ndarray, u_prime: np.ndarray, u_double_prime: np.ndarray) -> np.ndarray:
    radius = max(float(np.dot(u, u)), 1.0e-18)
    radius_prime = float(2.0 * np.dot(u, u_prime))
    multiplication = np.array([[u[0], -u[1]], [u[1], u[0]]], dtype=float)
    r_s = 2.0 * multiplication @ u_prime
    r_ss = 2.0 * (_levi_civita_square(u_prime) + multiplication @ u_double_prime)
    return (r_ss * radius - r_s * radius_prime) / max(radius**3, 1.0e-18)


def _dominant_close_pair(system: object, trajectory: TrajectoryResult, start: int, end: int) -> tuple[int, int]:
    pair_minima: dict[tuple[int, int], float] = {}
    for pair in PAIR_INDICES:
        i, j = pair
        distances = []
        for state in trajectory.y[start : end + 1]:
            positions, _velocities = system.split_state(state)
            distances.append(float(np.linalg.norm(positions[j] - positions[i])))
        pair_minima[pair] = min(distances)
    return min(pair_minima, key=pair_minima.get)


def _continuous_levi_civita_charts(charts: tuple[LeviCivitaBinaryChart, ...]) -> tuple[LeviCivitaBinaryChart, ...]:
    if not charts:
        return ()
    continuous = [charts[0]]
    for chart in charts[1:]:
        previous = continuous[-1]
        if np.linalg.norm(-chart.u - previous.u) < np.linalg.norm(chart.u - previous.u):
            chart = _flip_levi_civita_branch(chart)
        continuous.append(chart)
    return tuple(continuous)


def _flip_levi_civita_branch(chart: LeviCivitaBinaryChart) -> LeviCivitaBinaryChart:
    return LeviCivitaBinaryChart(
        pair=chart.pair,
        relative_position=chart.relative_position,
        relative_velocity=chart.relative_velocity,
        u=-chart.u,
        u_prime=-chart.u_prime,
        radius=chart.radius,
        regularized_radius=chart.regularized_radius,
        reconstruction_error=chart.reconstruction_error,
    )


def _levi_civita_square_root(position: np.ndarray) -> np.ndarray:
    x = float(position[0])
    y = float(position[1])
    radius = float(np.hypot(x, y))
    u0 = np.sqrt(max(0.5 * (radius + x), 0.0))
    if u0 > 0.0:
        u1 = y / (2.0 * u0)
    else:
        u1 = np.sign(y) * np.sqrt(max(0.5 * (radius - x), 0.0))
    return np.array([u0, u1], dtype=float)


def _levi_civita_square(u: np.ndarray) -> np.ndarray:
    return np.array([u[0] ** 2 - u[1] ** 2, 2.0 * u[0] * u[1]], dtype=float)
