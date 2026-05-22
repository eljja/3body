from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import TrajectoryResult


@dataclass(frozen=True, slots=True)
class JacobiEnergyDecomposition:
    """Exact Jacobi-coordinate energy split for one binary plus one outer body."""

    inner_pair: tuple[int, int]
    outer_body: int
    total_energy: float
    center_of_mass_kinetic: float
    reduced_total_energy: float
    inner_kepler_energy: float
    outer_kepler_energy: float
    interaction_remainder: float
    interaction_bound: float
    quadrupole_interaction_bound: float
    closure_residual: float
    inner_radius: float
    outer_radius: float
    hierarchy_ratio: float
    radial_velocity: float

    def as_dict(self) -> dict[str, float | int | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "total_energy": self.total_energy,
            "center_of_mass_kinetic": self.center_of_mass_kinetic,
            "reduced_total_energy": self.reduced_total_energy,
            "inner_kepler_energy": self.inner_kepler_energy,
            "outer_kepler_energy": self.outer_kepler_energy,
            "interaction_remainder": self.interaction_remainder,
            "interaction_bound": self.interaction_bound,
            "quadrupole_interaction_bound": self.quadrupole_interaction_bound,
            "closure_residual": self.closure_residual,
            "inner_radius": self.inner_radius,
            "outer_radius": self.outer_radius,
            "hierarchy_ratio": self.hierarchy_ratio,
            "radial_velocity": self.radial_velocity,
        }


@dataclass(frozen=True, slots=True)
class JacobiEscapeCertificate:
    """One-sided sufficient escape certificate on a hierarchical outer tail."""

    inner_pair: tuple[int, int]
    outer_body: int
    tail_sample_count: int
    minimum_outer_kepler_energy: float
    maximum_interaction_bound: float
    maximum_closure_residual: float
    reduced_energy_drift: float
    radius_growth_fraction: float
    minimum_radial_velocity: float
    minimum_hierarchy_ratio: float
    escape_margin: float
    decomposition_resolved: bool
    sufficient_escape: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "tail_sample_count": self.tail_sample_count,
            "minimum_outer_kepler_energy": self.minimum_outer_kepler_energy,
            "maximum_interaction_bound": self.maximum_interaction_bound,
            "maximum_closure_residual": self.maximum_closure_residual,
            "reduced_energy_drift": self.reduced_energy_drift,
            "radius_growth_fraction": self.radius_growth_fraction,
            "minimum_radial_velocity": self.minimum_radial_velocity,
            "minimum_hierarchy_ratio": self.minimum_hierarchy_ratio,
            "escape_margin": self.escape_margin,
            "decomposition_resolved": self.decomposition_resolved,
            "sufficient_escape": self.sufficient_escape,
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class JacobiFutureTailBound:
    """Conditional asymptotic bound for energy exchange after a certified tail."""

    inner_pair: tuple[int, int]
    outer_body: int
    tail_sample_count: int
    terminal_outer_radius: float
    maximum_inner_radius: float
    maximum_outer_speed: float
    minimum_radial_velocity: float
    maximum_quadrupole_acceleration_constant: float
    finite_tail_escape_margin: float
    future_energy_exchange_bound: float
    asymptotic_escape_margin: float
    assumptions_satisfied: bool
    conditional_asymptotic_escape: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "tail_sample_count": self.tail_sample_count,
            "terminal_outer_radius": self.terminal_outer_radius,
            "maximum_inner_radius": self.maximum_inner_radius,
            "maximum_outer_speed": self.maximum_outer_speed,
            "minimum_radial_velocity": self.minimum_radial_velocity,
            "maximum_quadrupole_acceleration_constant": self.maximum_quadrupole_acceleration_constant,
            "finite_tail_escape_margin": self.finite_tail_escape_margin,
            "future_energy_exchange_bound": self.future_energy_exchange_bound,
            "asymptotic_escape_margin": self.asymptotic_escape_margin,
            "assumptions_satisfied": self.assumptions_satisfied,
            "conditional_asymptotic_escape": self.conditional_asymptotic_escape,
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class JacobiInflatedMarginCertificate:
    """Outward-inflated scalar certificate for the conditional escape margin."""

    inner_pair: tuple[int, int]
    outer_body: int
    nominal_asymptotic_margin: float
    roundoff_inflation: float
    state_inflation: float
    validated_margin_lower: float
    validated_positive: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "nominal_asymptotic_margin": self.nominal_asymptotic_margin,
            "roundoff_inflation": self.roundoff_inflation,
            "state_inflation": self.state_inflation,
            "validated_margin_lower": self.validated_margin_lower,
            "validated_positive": self.validated_positive,
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class JacobiSelfConsistentConeCertificate:
    """Self-consistency check tying the future-tail radial floor to the energy margin."""

    inner_pair: tuple[int, int]
    outer_body: int
    outer_reduced_mass: float
    observed_radial_floor: float
    energy_radial_floor: float
    certified_radial_floor: float
    asymptotic_margin_lower: float
    future_exchange_bound: float
    self_consistent: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "outer_reduced_mass": self.outer_reduced_mass,
            "observed_radial_floor": self.observed_radial_floor,
            "energy_radial_floor": self.energy_radial_floor,
            "certified_radial_floor": self.certified_radial_floor,
            "asymptotic_margin_lower": self.asymptotic_margin_lower,
            "future_exchange_bound": self.future_exchange_bound,
            "self_consistent": self.self_consistent,
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class JacobiOpenConeCertificate:
    """Open-neighborhood certificate for the conditional Jacobi escape cone."""

    inner_pair: tuple[int, int]
    outer_body: int
    validated_margin_lower: float
    margin_sensitivity_scale: float
    state_scale: float
    absolute_state_radius: float
    relative_state_radius: float
    open_cone_certified: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "validated_margin_lower": self.validated_margin_lower,
            "margin_sensitivity_scale": self.margin_sensitivity_scale,
            "state_scale": self.state_scale,
            "absolute_state_radius": self.absolute_state_radius,
            "relative_state_radius": self.relative_state_radius,
            "open_cone_certified": self.open_cone_certified,
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class JacobiQuadrupoleAccelerationCertificate:
    """Certificate that the declared quadrupole acceleration envelope dominates the tail."""

    inner_pair: tuple[int, int]
    outer_body: int
    tail_sample_count: int
    maximum_observed_perturbing_acceleration: float
    minimum_declared_bound: float
    maximum_bound_ratio: float
    quadrupole_bound_resolved: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "tail_sample_count": self.tail_sample_count,
            "maximum_observed_perturbing_acceleration": self.maximum_observed_perturbing_acceleration,
            "minimum_declared_bound": self.minimum_declared_bound,
            "maximum_bound_ratio": self.maximum_bound_ratio,
            "quadrupole_bound_resolved": self.quadrupole_bound_resolved,
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class JacobiTailIntervalReserveCertificate:
    """Finite-difference reserve for terminal tail-state perturbations.

    This is a bridge certificate, not interval arithmetic. It asks whether the
    inflated Jacobi escape margin stays positive after subtracting a local
    finite-difference Lipschitz reserve over the terminal tail state.
    """

    inner_pair: tuple[int, int]
    outer_body: int
    nominal_margin_lower: float
    perturbation_radius: float
    finite_difference_step: float
    finite_difference_lipschitz: float
    interval_margin_lower: float
    sampled_axis_count: int
    interval_reserve_certified: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "nominal_margin_lower": self.nominal_margin_lower,
            "perturbation_radius": self.perturbation_radius,
            "finite_difference_step": self.finite_difference_step,
            "finite_difference_lipschitz": self.finite_difference_lipschitz,
            "interval_margin_lower": self.interval_margin_lower,
            "sampled_axis_count": self.sampled_axis_count,
            "interval_reserve_certified": self.interval_reserve_certified,
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class JacobiIntervalTailCertificate:
    """Interval-arithmetic certificate over a nonzero tail-state box.

    This is stronger than scalar inflation or finite-difference reserve because
    the Jacobi quantities entering the escape margin are evaluated on interval
    boxes around the sampled tail states. It is still local to the certified
    tail data; it does not yet enclose the ODE flow that produced that tail.
    """

    inner_pair: tuple[int, int]
    outer_body: int
    tail_sample_count: int
    absolute_state_radius: float
    relative_state_radius: float
    state_box_radius: float
    minimum_outer_kepler_energy_lower: float
    maximum_interaction_abs_upper: float
    finite_tail_margin_lower: float
    future_exchange_bound_upper: float
    asymptotic_margin_lower: float
    minimum_radial_velocity_lower: float
    minimum_hierarchy_ratio_lower: float
    terminal_outer_radius_lower: float
    maximum_inner_radius_upper: float
    maximum_outer_speed_upper: float
    maximum_quadrupole_acceleration_constant_upper: float
    maximum_split_identity_width: float
    split_identity_enclosed: bool
    interval_tail_assumptions_satisfied: bool
    interval_escape_certified: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "tail_sample_count": self.tail_sample_count,
            "absolute_state_radius": self.absolute_state_radius,
            "relative_state_radius": self.relative_state_radius,
            "state_box_radius": self.state_box_radius,
            "minimum_outer_kepler_energy_lower": self.minimum_outer_kepler_energy_lower,
            "maximum_interaction_abs_upper": self.maximum_interaction_abs_upper,
            "finite_tail_margin_lower": self.finite_tail_margin_lower,
            "future_exchange_bound_upper": self.future_exchange_bound_upper,
            "asymptotic_margin_lower": self.asymptotic_margin_lower,
            "minimum_radial_velocity_lower": self.minimum_radial_velocity_lower,
            "minimum_hierarchy_ratio_lower": self.minimum_hierarchy_ratio_lower,
            "terminal_outer_radius_lower": self.terminal_outer_radius_lower,
            "maximum_inner_radius_upper": self.maximum_inner_radius_upper,
            "maximum_outer_speed_upper": self.maximum_outer_speed_upper,
            "maximum_quadrupole_acceleration_constant_upper": self.maximum_quadrupole_acceleration_constant_upper,
            "maximum_split_identity_width": self.maximum_split_identity_width,
            "split_identity_enclosed": self.split_identity_enclosed,
            "interval_tail_assumptions_satisfied": self.interval_tail_assumptions_satisfied,
            "interval_escape_certified": self.interval_escape_certified,
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class JacobiIntervalFlowTubeCertificate:
    """A posteriori interval flow-tube check for the certified Jacobi tail.

    The tube radius is chosen from the sampled trajectory's trapezoid defect,
    then the Newtonian RHS is interval-evaluated on each expanded segment hull.
    This is not a full validated integrator, but it ties the local interval
    escape margin to an interval enclosure of the sampled tail's vector field.
    """

    inner_pair: tuple[int, int]
    outer_body: int
    tail_sample_count: int
    segment_count: int
    tube_radius: float
    defect_safety_factor: float
    maximum_trapezoid_defect: float
    maximum_position_defect: float
    maximum_velocity_defect: float
    maximum_step: float
    maximum_rhs_width: float
    rhs_inclusion_fraction: float
    rhs_inclusion_passed: bool
    interval_escape_margin_lower: float
    interval_escape_certified: bool
    flow_tube_certified: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "tail_sample_count": self.tail_sample_count,
            "segment_count": self.segment_count,
            "tube_radius": self.tube_radius,
            "defect_safety_factor": self.defect_safety_factor,
            "maximum_trapezoid_defect": self.maximum_trapezoid_defect,
            "maximum_position_defect": self.maximum_position_defect,
            "maximum_velocity_defect": self.maximum_velocity_defect,
            "maximum_step": self.maximum_step,
            "maximum_rhs_width": self.maximum_rhs_width,
            "rhs_inclusion_fraction": self.rhs_inclusion_fraction,
            "rhs_inclusion_passed": self.rhs_inclusion_passed,
            "interval_escape_margin_lower": self.interval_escape_margin_lower,
            "interval_escape_certified": self.interval_escape_certified,
            "flow_tube_certified": self.flow_tube_certified,
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class JacobiIntervalPicardFlowCertificate:
    """Segment-wise interval Picard propagation certificate for the Jacobi tail."""

    inner_pair: tuple[int, int]
    outer_body: int
    tail_sample_count: int
    segment_count: int
    substep_count: int
    tube_radius: float
    initial_state_radius: float
    maximum_propagated_endpoint_radius: float
    maximum_lipschitz_bound: float
    lipschitz_bound_method: str
    maximum_observed_contraction: float
    target_contraction: float
    picard_inclusion_fraction: float
    endpoint_inclusion_fraction: float
    endpoint_subset_fraction: float
    picard_inclusion_passed: bool
    endpoint_inclusion_passed: bool
    interval_escape_margin_lower: float
    interval_escape_certified: bool
    picard_flow_certified: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "tail_sample_count": self.tail_sample_count,
            "segment_count": self.segment_count,
            "substep_count": self.substep_count,
            "tube_radius": self.tube_radius,
            "initial_state_radius": self.initial_state_radius,
            "maximum_propagated_endpoint_radius": self.maximum_propagated_endpoint_radius,
            "maximum_lipschitz_bound": self.maximum_lipschitz_bound,
            "lipschitz_bound_method": self.lipschitz_bound_method,
            "maximum_observed_contraction": self.maximum_observed_contraction,
            "target_contraction": self.target_contraction,
            "picard_inclusion_fraction": self.picard_inclusion_fraction,
            "endpoint_inclusion_fraction": self.endpoint_inclusion_fraction,
            "endpoint_subset_fraction": self.endpoint_subset_fraction,
            "picard_inclusion_passed": self.picard_inclusion_passed,
            "endpoint_inclusion_passed": self.endpoint_inclusion_passed,
            "interval_escape_margin_lower": self.interval_escape_margin_lower,
            "interval_escape_certified": self.interval_escape_certified,
            "picard_flow_certified": self.picard_flow_certified,
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class JacobiPicardTuningCertificate:
    """Automatic Picard tuning result across contraction-bound settings."""

    inner_pair: tuple[int, int]
    outer_body: int
    attempted_count: int
    selected_maximum_substeps_per_segment: int
    selected_scaled_phase_norm: bool
    selected_lipschitz_bound_method: str
    best_observed_contraction: float
    contraction_reserve: float
    best_interval_escape_margin_lower: float
    best_substep_count: int
    mean_substeps_per_segment: float
    certification_efficiency: float
    target_contraction: float
    certified: bool
    attempts: tuple[dict[str, float | int | bool | str], ...]
    warning: str

    def as_dict(self) -> dict[str, object]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "attempted_count": self.attempted_count,
            "selected_maximum_substeps_per_segment": self.selected_maximum_substeps_per_segment,
            "selected_scaled_phase_norm": self.selected_scaled_phase_norm,
            "selected_lipschitz_bound_method": self.selected_lipschitz_bound_method,
            "best_observed_contraction": self.best_observed_contraction,
            "contraction_reserve": self.contraction_reserve,
            "best_interval_escape_margin_lower": self.best_interval_escape_margin_lower,
            "best_substep_count": self.best_substep_count,
            "mean_substeps_per_segment": self.mean_substeps_per_segment,
            "certification_efficiency": self.certification_efficiency,
            "target_contraction": self.target_contraction,
            "certified": self.certified,
            "attempts": list(self.attempts),
            "warning": self.warning,
        }


def jacobi_energy_decomposition(
    system: object,
    state: np.ndarray,
    inner_pair: tuple[int, int] = (0, 1),
) -> JacobiEnergyDecomposition:
    """Split the Newtonian three-body Hamiltonian into inner, outer, and interaction terms.

    The identity is exact in the center-of-mass quotient:

        H - T_cm = E_inner(r, rdot) + E_outer(R, Rdot) + W(r, R)

    where `R` is the outer body relative to the selected binary center of mass.
    """

    if getattr(system, "body_count", None) != 3:
        raise TypeError("jacobi_energy_decomposition requires a three-body Newtonian system.")
    positions, velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    gravitational_constant = float(system.gravitational_constant)
    i, j = inner_pair
    outer = next(index for index in range(3) if index not in inner_pair)
    pair_mass = float(masses[i] + masses[j])
    total_mass = float(pair_mass + masses[outer])
    inner_reduced_mass = float(masses[i] * masses[j] / pair_mass)
    outer_reduced_mass = float(pair_mass * masses[outer] / total_mass)

    pair_center = (masses[i] * positions[i] + masses[j] * positions[j]) / pair_mass
    pair_velocity = (masses[i] * velocities[i] + masses[j] * velocities[j]) / pair_mass
    total_velocity = np.sum(masses[:, None] * velocities, axis=0) / total_mass

    inner_position = positions[j] - positions[i]
    inner_velocity = velocities[j] - velocities[i]
    outer_position = positions[outer] - pair_center
    outer_velocity = velocities[outer] - pair_velocity
    inner_radius = _safe_norm(inner_position)
    outer_radius = _safe_norm(outer_position)

    inner_kepler = (
        0.5 * inner_reduced_mass * float(np.dot(inner_velocity, inner_velocity))
        - gravitational_constant * masses[i] * masses[j] / inner_radius
    )
    outer_kepler = (
        0.5 * outer_reduced_mass * float(np.dot(outer_velocity, outer_velocity))
        - gravitational_constant * pair_mass * masses[outer] / outer_radius
    )
    actual_outer_potential = -gravitational_constant * masses[outer] * (
        masses[i] / _safe_norm(positions[outer] - positions[i])
        + masses[j] / _safe_norm(positions[outer] - positions[j])
    )
    monopole_outer_potential = -gravitational_constant * pair_mass * masses[outer] / outer_radius
    interaction = float(actual_outer_potential - monopole_outer_potential)

    total_energy = float(system.total_energy(state))
    center_kinetic = 0.5 * total_mass * float(np.dot(total_velocity, total_velocity))
    reduced_total = total_energy - center_kinetic
    closure_residual = abs(reduced_total - (inner_kepler + outer_kepler + interaction))
    radial_velocity = float(np.dot(outer_position, outer_velocity) / outer_radius)
    return JacobiEnergyDecomposition(
        inner_pair=inner_pair,
        outer_body=outer,
        total_energy=total_energy,
        center_of_mass_kinetic=float(center_kinetic),
        reduced_total_energy=float(reduced_total),
        inner_kepler_energy=float(inner_kepler),
        outer_kepler_energy=float(outer_kepler),
        interaction_remainder=interaction,
        interaction_bound=_interaction_remainder_bound(
            gravitational_constant,
            masses,
            positions,
            pair_center,
            outer_position,
            inner_pair,
            outer,
        ),
        quadrupole_interaction_bound=_quadrupole_interaction_remainder_bound(
            gravitational_constant,
            masses,
            positions,
            pair_center,
            outer_position,
            inner_pair,
            outer,
        ),
        closure_residual=float(closure_residual),
        inner_radius=inner_radius,
        outer_radius=outer_radius,
        hierarchy_ratio=float(outer_radius / inner_radius),
        radial_velocity=radial_velocity,
    )


def jacobi_escape_sufficient_condition(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
    tail_fraction: float = 0.25,
    closure_tolerance: float = 1.0e-9,
    radius_growth_threshold: float = 0.8,
) -> JacobiEscapeCertificate:
    """Certify a finite-time sufficient escape condition on the outgoing tail.

    This is intentionally one-sided. A failing certificate does not mean the body is
    bound; it only means the current finite tail does not yet prove escape.
    """

    tail_count = max(3, int(np.ceil(len(trajectory.t) * tail_fraction)))
    decompositions = tuple(
        jacobi_energy_decomposition(system, state, inner_pair=inner_pair) for state in trajectory.y[-tail_count:]
    )
    outer_energies = np.asarray([row.outer_kepler_energy for row in decompositions], dtype=float)
    interaction_bounds = np.asarray([row.interaction_bound for row in decompositions], dtype=float)
    closure_residuals = np.asarray([row.closure_residual for row in decompositions], dtype=float)
    reduced_energies = np.asarray([row.reduced_total_energy for row in decompositions], dtype=float)
    outer_radii = np.asarray([row.outer_radius for row in decompositions], dtype=float)
    radial_velocities = np.asarray([row.radial_velocity for row in decompositions], dtype=float)
    hierarchy_ratios = np.asarray([row.hierarchy_ratio for row in decompositions], dtype=float)

    minimum_outer_energy = float(np.min(outer_energies))
    maximum_interaction_bound = float(np.max(interaction_bounds))
    maximum_closure_residual = float(np.max(closure_residuals))
    reduced_energy_drift = _relative_span(reduced_energies)
    radius_growth_fraction = float(np.mean(np.diff(outer_radii) > 0.0)) if outer_radii.size > 1 else 0.0
    minimum_radial_velocity = float(np.min(radial_velocities))
    minimum_hierarchy_ratio = float(np.min(hierarchy_ratios))
    escape_margin = minimum_outer_energy - maximum_interaction_bound - maximum_closure_residual
    decomposition_resolved = maximum_closure_residual <= closure_tolerance
    sufficient_escape = (
        decomposition_resolved
        and escape_margin > 0.0
        and radius_growth_fraction >= radius_growth_threshold
        and minimum_radial_velocity > 0.0
    )
    warning = ""
    if not decomposition_resolved:
        warning = "Jacobi energy decomposition residual exceeds tolerance"
    elif escape_margin <= 0.0:
        warning = "outer Kepler energy is not separated from interaction remainder by a positive margin"
    elif radius_growth_fraction < radius_growth_threshold:
        warning = "outer radius is not monotonically increasing enough on the certified tail"
    elif minimum_radial_velocity <= 0.0:
        warning = "outer radial velocity is not outward on the full certified tail"

    return JacobiEscapeCertificate(
        inner_pair=inner_pair,
        outer_body=decompositions[-1].outer_body,
        tail_sample_count=tail_count,
        minimum_outer_kepler_energy=minimum_outer_energy,
        maximum_interaction_bound=maximum_interaction_bound,
        maximum_closure_residual=maximum_closure_residual,
        reduced_energy_drift=reduced_energy_drift,
        radius_growth_fraction=radius_growth_fraction,
        minimum_radial_velocity=minimum_radial_velocity,
        minimum_hierarchy_ratio=minimum_hierarchy_ratio,
        escape_margin=float(escape_margin),
        decomposition_resolved=decomposition_resolved,
        sufficient_escape=sufficient_escape,
        warning=warning,
    )


def jacobi_future_tail_bound(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
    tail_fraction: float = 0.25,
    closure_tolerance: float = 1.0e-9,
    minimum_hierarchy_ratio: float = 4.0,
) -> JacobiFutureTailBound:
    """Bound future outer-energy exchange under explicit hierarchy-tail assumptions.

    The bound is conditional: after the sampled tail it assumes the inner binary
    radius, outer relative speed, and outward radial velocity remain within the
    certified tail extrema. Under those hypotheses, the quadrupole-cancelled
    perturbing acceleration is integrable as `O(R^-4)`.
    """

    escape = jacobi_escape_sufficient_condition(
        system,
        trajectory,
        inner_pair=inner_pair,
        tail_fraction=tail_fraction,
        closure_tolerance=closure_tolerance,
    )
    tail_count = escape.tail_sample_count
    states = trajectory.y[-tail_count:]
    decompositions = tuple(jacobi_energy_decomposition(system, state, inner_pair=inner_pair) for state in states)
    masses = np.asarray(system.masses, dtype=float)
    i, j = inner_pair
    outer = decompositions[-1].outer_body
    pair_mass = float(masses[i] + masses[j])
    total_mass = float(pair_mass + masses[outer])
    outer_reduced_mass = float(pair_mass * masses[outer] / total_mass)

    maximum_inner_radius = float(max(row.inner_radius for row in decompositions))
    terminal_outer_radius = float(decompositions[-1].outer_radius)
    minimum_radial_velocity = float(min(row.radial_velocity for row in decompositions))
    maximum_outer_speed = _maximum_outer_relative_speed(system, states, inner_pair, outer)
    maximum_acceleration_constant = max(
        _quadrupole_acceleration_constant(system, state, inner_pair, outer) for state in states
    )
    denominator_radius = terminal_outer_radius - 0.5 * maximum_inner_radius
    if denominator_radius <= 0.0 or minimum_radial_velocity <= 0.0:
        future_exchange = float("inf")
    else:
        future_exchange = float(
            outer_reduced_mass
            * maximum_outer_speed
            * maximum_acceleration_constant
            / (3.0 * minimum_radial_velocity * denominator_radius**3)
        )
    assumptions_satisfied = (
        escape.decomposition_resolved
        and np.isfinite(future_exchange)
        and escape.minimum_hierarchy_ratio >= minimum_hierarchy_ratio
        and minimum_radial_velocity > 0.0
    )
    asymptotic_margin = float(escape.escape_margin - future_exchange)
    conditional_escape = bool(assumptions_satisfied and asymptotic_margin > 0.0)
    warning = ""
    if not escape.decomposition_resolved:
        warning = "Jacobi split is not resolved on the certified tail"
    elif escape.minimum_hierarchy_ratio < minimum_hierarchy_ratio:
        warning = "tail hierarchy ratio is below the declared theorem domain"
    elif minimum_radial_velocity <= 0.0:
        warning = "outer radial velocity is not outward on the certified tail"
    elif asymptotic_margin <= 0.0:
        warning = "future exchange bound consumes the finite escape margin"

    return JacobiFutureTailBound(
        inner_pair=inner_pair,
        outer_body=outer,
        tail_sample_count=tail_count,
        terminal_outer_radius=terminal_outer_radius,
        maximum_inner_radius=maximum_inner_radius,
        maximum_outer_speed=maximum_outer_speed,
        minimum_radial_velocity=minimum_radial_velocity,
        maximum_quadrupole_acceleration_constant=float(maximum_acceleration_constant),
        finite_tail_escape_margin=escape.escape_margin,
        future_energy_exchange_bound=future_exchange,
        asymptotic_escape_margin=asymptotic_margin,
        assumptions_satisfied=assumptions_satisfied,
        conditional_asymptotic_escape=conditional_escape,
        warning=warning,
    )


def jacobi_inflated_margin_certificate(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
    tail_fraction: float = 0.25,
    relative_inflation: float = 1.0e-10,
    absolute_inflation: float = 1.0e-12,
) -> JacobiInflatedMarginCertificate:
    """Check that the asymptotic escape margin survives conservative scalar inflation.

    This is not a replacement for machine-checked interval integration. It is a
    reproducible guardrail: theorem candidates fail if the positive margin is
    comparable to roundoff or state-measurement scale.
    """

    future = jacobi_future_tail_bound(
        system,
        trajectory,
        inner_pair=inner_pair,
        tail_fraction=tail_fraction,
    )
    tail_count = future.tail_sample_count
    states = trajectory.y[-tail_count:]
    state_scale = float(max(np.max(np.abs(states)), 1.0))
    scalar_scale = max(
        abs(future.finite_tail_escape_margin),
        abs(future.future_energy_exchange_bound),
        abs(future.maximum_quadrupole_acceleration_constant),
        abs(future.maximum_outer_speed),
        abs(future.terminal_outer_radius),
        1.0,
    )
    roundoff_inflation = float(32.0 * np.finfo(float).eps * scalar_scale + absolute_inflation)
    state_inflation = float(relative_inflation * state_scale * scalar_scale)
    validated_margin = float(future.asymptotic_escape_margin - roundoff_inflation - state_inflation)
    validated = bool(future.conditional_asymptotic_escape and validated_margin > 0.0)
    warning = ""
    if not future.conditional_asymptotic_escape:
        warning = "nominal conditional asymptotic escape certificate failed"
    elif validated_margin <= 0.0:
        warning = "positive nominal margin is not separated from inflated numerical uncertainty"
    return JacobiInflatedMarginCertificate(
        inner_pair=inner_pair,
        outer_body=future.outer_body,
        nominal_asymptotic_margin=future.asymptotic_escape_margin,
        roundoff_inflation=roundoff_inflation,
        state_inflation=state_inflation,
        validated_margin_lower=validated_margin,
        validated_positive=validated,
        warning=warning,
    )


def jacobi_self_consistent_escape_cone(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
    tail_fraction: float = 0.25,
    minimum_radial_floor: float = 1.0e-6,
) -> JacobiSelfConsistentConeCertificate:
    """Certify that the tail's outward-speed floor is compatible with the energy margin.

    This promotes the escape cone from "assume an outward radial floor" to
    "the observed outward floor is supported by the post-exchange energy lower
    bound." It is still conditional on the hierarchy and perturbation bounds
    used by `jacobi_future_tail_bound`.
    """

    future = jacobi_future_tail_bound(
        system,
        trajectory,
        inner_pair=inner_pair,
        tail_fraction=tail_fraction,
    )
    inflated = jacobi_inflated_margin_certificate(
        system,
        trajectory,
        inner_pair=inner_pair,
        tail_fraction=tail_fraction,
    )
    masses = np.asarray(system.masses, dtype=float)
    outer = future.outer_body
    pair_mass = float(sum(masses[index] for index in inner_pair))
    total_mass = float(pair_mass + masses[outer])
    outer_reduced_mass = float(pair_mass * masses[outer] / total_mass)
    energy_radial_floor = float(np.sqrt(max(2.0 * inflated.validated_margin_lower / outer_reduced_mass, 0.0)))
    certified_radial_floor = float(min(future.minimum_radial_velocity, energy_radial_floor))
    self_consistent = bool(
        inflated.validated_positive
        and future.assumptions_satisfied
        and certified_radial_floor > minimum_radial_floor
        and future.future_energy_exchange_bound < future.finite_tail_escape_margin
    )
    warning = ""
    if not inflated.validated_positive:
        warning = "inflated asymptotic margin is not positive"
    elif not future.assumptions_satisfied:
        warning = "future-tail assumptions are not satisfied"
    elif certified_radial_floor <= minimum_radial_floor:
        warning = "energy-supported radial floor is too small"
    elif future.future_energy_exchange_bound >= future.finite_tail_escape_margin:
        warning = "future exchange bound does not fit inside finite escape margin"
    return JacobiSelfConsistentConeCertificate(
        inner_pair=inner_pair,
        outer_body=outer,
        outer_reduced_mass=outer_reduced_mass,
        observed_radial_floor=future.minimum_radial_velocity,
        energy_radial_floor=energy_radial_floor,
        certified_radial_floor=certified_radial_floor,
        asymptotic_margin_lower=inflated.validated_margin_lower,
        future_exchange_bound=future.future_energy_exchange_bound,
        self_consistent=self_consistent,
        warning=warning,
    )


def jacobi_open_escape_cone_certificate(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
    tail_fraction: float = 0.25,
    minimum_relative_radius: float = 1.0e-8,
) -> JacobiOpenConeCertificate:
    """Certify an open tail-data neighborhood that preserves the escape margin.

    The returned radius is conservative and scalar: it treats the margin as a
    Lipschitz-like scalar with sensitivity equal to the largest certified scale
    entering the margin calculation. This is a proof obligation placeholder for
    a future interval derivative bound, but it already prevents a zero-measure
    single-trajectory claim.
    """

    self_consistent = jacobi_self_consistent_escape_cone(
        system,
        trajectory,
        inner_pair=inner_pair,
        tail_fraction=tail_fraction,
    )
    future = jacobi_future_tail_bound(
        system,
        trajectory,
        inner_pair=inner_pair,
        tail_fraction=tail_fraction,
    )
    tail_count = future.tail_sample_count
    states = trajectory.y[-tail_count:]
    state_scale = float(max(np.max(np.abs(states)), 1.0))
    margin_sensitivity = max(
        abs(future.finite_tail_escape_margin),
        abs(future.future_energy_exchange_bound),
        abs(future.maximum_quadrupole_acceleration_constant),
        abs(future.maximum_outer_speed),
        abs(future.terminal_outer_radius),
        abs(self_consistent.certified_radial_floor),
        1.0,
    )
    absolute_radius = float(0.5 * self_consistent.asymptotic_margin_lower / margin_sensitivity)
    relative_radius = float(absolute_radius / state_scale)
    certified = bool(
        self_consistent.self_consistent
        and absolute_radius > 0.0
        and relative_radius >= minimum_relative_radius
    )
    warning = ""
    if not self_consistent.self_consistent:
        warning = "self-consistent escape cone certificate failed"
    elif relative_radius < minimum_relative_radius:
        warning = "open cone radius is below the declared minimum relative radius"
    return JacobiOpenConeCertificate(
        inner_pair=inner_pair,
        outer_body=future.outer_body,
        validated_margin_lower=self_consistent.asymptotic_margin_lower,
        margin_sensitivity_scale=margin_sensitivity,
        state_scale=state_scale,
        absolute_state_radius=absolute_radius,
        relative_state_radius=relative_radius,
        open_cone_certified=certified,
        warning=warning,
    )


def jacobi_quadrupole_acceleration_certificate(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
    tail_fraction: float = 0.25,
    safety_factor: float = 4.0,
) -> JacobiQuadrupoleAccelerationCertificate:
    """Check that the quadrupole perturbing-acceleration envelope dominates the sampled tail."""

    if getattr(system, "body_count", None) != 3:
        raise TypeError("jacobi_quadrupole_acceleration_certificate requires a three-body Newtonian system.")
    tail_count = max(3, int(np.ceil(len(trajectory.t) * tail_fraction)))
    states = trajectory.y[-tail_count:]
    outer = next(index for index in range(3) if index not in inner_pair)
    observed = []
    bounds = []
    for state in states:
        perturbation = _outer_jacobi_perturbing_acceleration(system, state, inner_pair, outer)
        decomposition = jacobi_energy_decomposition(system, state, inner_pair=inner_pair)
        constant = safety_factor * _quadrupole_acceleration_constant(system, state, inner_pair, outer)
        denominator = max(decomposition.outer_radius - 0.5 * decomposition.inner_radius, 1.0e-12)
        observed.append(float(np.linalg.norm(perturbation)))
        bounds.append(float(constant / denominator**4))
    observed_array = np.asarray(observed, dtype=float)
    bound_array = np.asarray(bounds, dtype=float)
    ratios = observed_array / np.maximum(bound_array, 1.0e-18)
    maximum_ratio = float(np.max(ratios))
    resolved = bool(np.all(observed_array <= bound_array) and np.isfinite(maximum_ratio))
    warning = "" if resolved else "observed Jacobi perturbing acceleration exceeds declared quadrupole envelope"
    return JacobiQuadrupoleAccelerationCertificate(
        inner_pair=inner_pair,
        outer_body=outer,
        tail_sample_count=tail_count,
        maximum_observed_perturbing_acceleration=float(np.max(observed_array)),
        minimum_declared_bound=float(np.min(bound_array)),
        maximum_bound_ratio=maximum_ratio,
        quadrupole_bound_resolved=resolved,
        warning=warning,
    )


def jacobi_tail_interval_reserve_certificate(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
    tail_fraction: float = 0.25,
    perturbation_radius: float | None = None,
    finite_difference_step: float | None = None,
) -> JacobiTailIntervalReserveCertificate:
    """Subtract a finite-difference terminal-state reserve from the escape margin.

    The certificate perturbs each coordinate of the terminal sampled tail state
    and recomputes the inflated asymptotic margin. It is intentionally local and
    conservative; a future interval integrator should replace this finite-
    difference Lipschitz estimate.
    """

    inflated = jacobi_inflated_margin_certificate(
        system,
        trajectory,
        inner_pair=inner_pair,
        tail_fraction=tail_fraction,
    )
    state_scale = float(max(np.linalg.norm(trajectory.y[-1]), 1.0))
    radius = float(perturbation_radius if perturbation_radius is not None else 1.0e-8 * state_scale)
    step = float(finite_difference_step if finite_difference_step is not None else 1.0e-6 * state_scale)
    if step <= 0.0:
        step = 1.0e-8
    slopes = []
    for axis in range(trajectory.state_dim):
        plus = _terminal_state_perturbed_trajectory(trajectory, axis, step)
        minus = _terminal_state_perturbed_trajectory(trajectory, axis, -step)
        plus_margin = jacobi_inflated_margin_certificate(
            system,
            plus,
            inner_pair=inner_pair,
            tail_fraction=tail_fraction,
        ).validated_margin_lower
        minus_margin = jacobi_inflated_margin_certificate(
            system,
            minus,
            inner_pair=inner_pair,
            tail_fraction=tail_fraction,
        ).validated_margin_lower
        if np.isfinite(plus_margin) and np.isfinite(minus_margin):
            slopes.append(abs(plus_margin - minus_margin) / (2.0 * step))
    lipschitz = float(np.linalg.norm(np.asarray(slopes, dtype=float))) if slopes else float("inf")
    interval_margin = float(inflated.validated_margin_lower - lipschitz * radius)
    certified = bool(inflated.validated_positive and np.isfinite(interval_margin) and interval_margin > 0.0)
    warning = ""
    if not inflated.validated_positive:
        warning = "nominal inflated Jacobi escape margin is not positive"
    elif not np.isfinite(lipschitz):
        warning = "finite-difference terminal-state sensitivity is unresolved"
    elif interval_margin <= 0.0:
        warning = "terminal-state finite-difference reserve consumes the escape margin"
    return JacobiTailIntervalReserveCertificate(
        inner_pair=inner_pair,
        outer_body=inflated.outer_body,
        nominal_margin_lower=inflated.validated_margin_lower,
        perturbation_radius=radius,
        finite_difference_step=step,
        finite_difference_lipschitz=lipschitz,
        interval_margin_lower=interval_margin,
        sampled_axis_count=len(slopes),
        interval_reserve_certified=certified,
        warning=warning,
    )


def jacobi_interval_escape_certificate(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
    tail_fraction: float = 0.25,
    relative_state_radius: float = 1.0e-11,
    absolute_state_radius: float = 1.0e-13,
    minimum_hierarchy_ratio: float = 4.0,
) -> JacobiIntervalTailCertificate:
    """Certify the Jacobi escape margin on interval boxes around the tail.

    The box radius is `absolute_state_radius + relative_state_radius * ||y||_inf`
    over the sampled tail. The certificate interval-encloses the one-sided
    escape inequality

        E_outer > |W| + future_exchange_bound

    using interval arithmetic for `E_outer`, `W`, the radial velocity floor,
    hierarchy ratio, binary scale, outer speed, and quadrupole acceleration
    constant. This is a local tail-data certificate, not an interval ODE
    integration proof.
    """

    if getattr(system, "body_count", None) != 3:
        raise TypeError("jacobi_interval_escape_certificate requires a three-body Newtonian system.")
    tail_count = max(3, int(np.ceil(len(trajectory.t) * tail_fraction)))
    states = np.asarray(trajectory.y[-tail_count:], dtype=float)
    state_scale = float(max(np.max(np.abs(states)), 1.0))
    state_radius = float(absolute_state_radius + relative_state_radius * state_scale)
    rows = tuple(
        _interval_jacobi_tail_row(system, state, inner_pair, state_radius)
        for state in states
    )
    outer_body = int(rows[-1]["outer_body"])
    minimum_outer_energy = float(min(row["outer_kepler_energy"].lo for row in rows))
    maximum_interaction = float(max(row["interaction_abs_upper"] for row in rows))
    finite_margin = float(minimum_outer_energy - maximum_interaction)
    minimum_radial_velocity = float(min(row["radial_velocity"].lo for row in rows))
    minimum_hierarchy = float(min(row["hierarchy_ratio_lower"] for row in rows))
    terminal_outer_radius = float(rows[-1]["outer_radius"].lo)
    maximum_inner_radius = float(max(row["inner_radius"].hi for row in rows))
    maximum_outer_speed = float(max(row["outer_speed"].hi for row in rows))
    maximum_acceleration_constant = float(max(row["quadrupole_acceleration_constant_upper"] for row in rows))
    denominator_radius = terminal_outer_radius - 0.5 * maximum_inner_radius
    masses = np.asarray(system.masses, dtype=float)
    pair_mass = float(sum(masses[index] for index in inner_pair))
    total_mass = float(pair_mass + masses[outer_body])
    outer_reduced_mass = float(pair_mass * masses[outer_body] / total_mass)
    if denominator_radius <= 0.0 or minimum_radial_velocity <= 0.0:
        future_exchange = float("inf")
    else:
        future_exchange = float(
            outer_reduced_mass
            * maximum_outer_speed
            * maximum_acceleration_constant
            / (3.0 * minimum_radial_velocity * denominator_radius**3)
        )
    asymptotic_margin = float(finite_margin - future_exchange)
    split_identity_enclosed = all(row["split_identity"].contains(0.0) for row in rows)
    maximum_split_width = float(max(row["split_identity"].width for row in rows))
    assumptions = bool(
        split_identity_enclosed
        and np.isfinite(future_exchange)
        and minimum_radial_velocity > 0.0
        and minimum_hierarchy >= minimum_hierarchy_ratio
        and denominator_radius > 0.0
    )
    certified = bool(assumptions and asymptotic_margin > 0.0)
    warning = ""
    if not split_identity_enclosed:
        warning = "interval Jacobi split does not enclose the exact identity on the tail box"
    elif minimum_hierarchy < minimum_hierarchy_ratio:
        warning = "interval hierarchy ratio lower bound is below the declared theorem domain"
    elif minimum_radial_velocity <= 0.0:
        warning = "interval radial velocity lower bound is not outward on the tail box"
    elif denominator_radius <= 0.0:
        warning = "interval terminal outer radius does not dominate the binary scale"
    elif asymptotic_margin <= 0.0:
        warning = "interval future exchange bound consumes the interval escape margin"
    return JacobiIntervalTailCertificate(
        inner_pair=inner_pair,
        outer_body=outer_body,
        tail_sample_count=tail_count,
        absolute_state_radius=float(absolute_state_radius),
        relative_state_radius=float(relative_state_radius),
        state_box_radius=state_radius,
        minimum_outer_kepler_energy_lower=minimum_outer_energy,
        maximum_interaction_abs_upper=maximum_interaction,
        finite_tail_margin_lower=finite_margin,
        future_exchange_bound_upper=future_exchange,
        asymptotic_margin_lower=asymptotic_margin,
        minimum_radial_velocity_lower=minimum_radial_velocity,
        minimum_hierarchy_ratio_lower=minimum_hierarchy,
        terminal_outer_radius_lower=terminal_outer_radius,
        maximum_inner_radius_upper=maximum_inner_radius,
        maximum_outer_speed_upper=maximum_outer_speed,
        maximum_quadrupole_acceleration_constant_upper=maximum_acceleration_constant,
        maximum_split_identity_width=maximum_split_width,
        split_identity_enclosed=split_identity_enclosed,
        interval_tail_assumptions_satisfied=assumptions,
        interval_escape_certified=certified,
        warning=warning,
    )


def jacobi_interval_flow_tube_certificate(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
    tail_fraction: float = 0.25,
    defect_safety_factor: float = 3.0,
    minimum_tube_radius: float = 1.0e-12,
) -> JacobiIntervalFlowTubeCertificate:
    """Check that the certified tail sits inside an interval RHS flow tube.

    For each tail segment, this function forms the componentwise hull of the
    two endpoint states, expands it by a radius chosen from the trajectory's
    trapezoid defect, interval-evaluates the Newtonian RHS on that hull, and
    checks that the observed segment slope lies inside the interval RHS.

    The same tube radius is then used for `jacobi_interval_escape_certificate`.
    Passing this certificate means the escape margin survives a tube large
    enough to contain the measured local integration defect and the sampled
    segment slopes are compatible with the interval vector field.
    """

    if getattr(system, "body_count", None) != 3:
        raise TypeError("jacobi_interval_flow_tube_certificate requires a three-body Newtonian system.")
    tail_count = max(3, int(np.ceil(len(trajectory.t) * tail_fraction)))
    times = np.asarray(trajectory.t[-tail_count:], dtype=float)
    states = np.asarray(trajectory.y[-tail_count:], dtype=float)
    dimension = int(system.body_count * system.dimension)
    defects = []
    position_defects = []
    velocity_defects = []
    steps = []
    for index in range(len(times) - 1):
        dt = float(times[index + 1] - times[index])
        if dt <= 0.0:
            continue
        rhs_start = np.asarray(system.rhs(times[index], states[index]), dtype=float)
        rhs_end = np.asarray(system.rhs(times[index + 1], states[index + 1]), dtype=float)
        defect = states[index + 1] - states[index] - 0.5 * dt * (rhs_start + rhs_end)
        defects.append(float(np.linalg.norm(defect, ord=np.inf)))
        position_defects.append(float(np.linalg.norm(defect[:dimension], ord=np.inf)))
        velocity_defects.append(float(np.linalg.norm(defect[dimension:], ord=np.inf)))
        steps.append(dt)
    maximum_defect = 0.0 if not defects else float(max(defects))
    tube_radius = float(max(minimum_tube_radius, defect_safety_factor * maximum_defect))
    inclusion_count = 0
    segment_count = 0
    maximum_rhs_width = 0.0
    for index in range(len(times) - 1):
        dt = float(times[index + 1] - times[index])
        if dt <= 0.0:
            continue
        slope = (states[index + 1] - states[index]) / dt
        state_lower = np.minimum(states[index], states[index + 1]) - tube_radius
        state_upper = np.maximum(states[index], states[index + 1]) + tube_radius
        rhs_box = _interval_rhs_from_state_bounds(system, state_lower, state_upper)
        maximum_rhs_width = max(maximum_rhs_width, max(interval.width for interval in rhs_box))
        segment_count += 1
        if all(interval.contains(float(value)) for interval, value in zip(rhs_box, slope, strict=True)):
            inclusion_count += 1
    inclusion_fraction = 0.0 if segment_count == 0 else float(inclusion_count / segment_count)
    rhs_inclusion_passed = inclusion_count == segment_count and segment_count > 0
    interval_escape = jacobi_interval_escape_certificate(
        system,
        trajectory,
        inner_pair=inner_pair,
        tail_fraction=tail_fraction,
        absolute_state_radius=tube_radius,
        relative_state_radius=0.0,
    )
    certified = bool(rhs_inclusion_passed and interval_escape.interval_escape_certified)
    warning = ""
    if not rhs_inclusion_passed:
        warning = "sampled tail segment slopes are not contained in the expanded interval RHS tube"
    elif not interval_escape.interval_escape_certified:
        warning = "Jacobi interval escape margin fails on the expanded flow tube"
    return JacobiIntervalFlowTubeCertificate(
        inner_pair=inner_pair,
        outer_body=interval_escape.outer_body,
        tail_sample_count=tail_count,
        segment_count=segment_count,
        tube_radius=tube_radius,
        defect_safety_factor=float(defect_safety_factor),
        maximum_trapezoid_defect=maximum_defect,
        maximum_position_defect=0.0 if not position_defects else float(max(position_defects)),
        maximum_velocity_defect=0.0 if not velocity_defects else float(max(velocity_defects)),
        maximum_step=0.0 if not steps else float(max(steps)),
        maximum_rhs_width=float(maximum_rhs_width),
        rhs_inclusion_fraction=inclusion_fraction,
        rhs_inclusion_passed=rhs_inclusion_passed,
        interval_escape_margin_lower=interval_escape.asymptotic_margin_lower,
        interval_escape_certified=interval_escape.interval_escape_certified,
        flow_tube_certified=certified,
        warning=warning,
    )


def jacobi_interval_picard_flow_certificate(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
    tail_fraction: float = 0.25,
    defect_safety_factor: float = 3.0,
    target_contraction: float = 0.35,
    initial_state_radius: float = 1.0e-12,
    maximum_substeps_per_segment: int = 256,
    use_scaled_phase_norm: bool = True,
) -> JacobiIntervalPicardFlowCertificate:
    """Propagate tail interval boxes by a segment-wise Picard inclusion test.

    For each sampled tail segment, the method subdivides until the interval
    Jacobian row-sum bound for the Newtonian RHS satisfies `h_sub * L <= target_contraction`
    whenever the cap allows it. On each substep it checks Picard self-inclusion:

        X_start + h_sub * f(Z) subset Z

    where `Z` is the expanded hull around the sampled subsegment and the
    propagated start box. The final interval endpoint radius produced by these
    Picard images is then fed back into the Jacobi interval escape margin,
    instead of reusing only the sampled trapezoid-defect tube radius. This is
    the first in-repo substitute for a validated interval ODE step. It remains
    segment-local and conservative, but it does propagate interval initial
    boxes rather than only checking sampled slopes.
    """

    if getattr(system, "body_count", None) != 3:
        raise TypeError("jacobi_interval_picard_flow_certificate requires a three-body Newtonian system.")
    flow_tube = jacobi_interval_flow_tube_certificate(
        system,
        trajectory,
        inner_pair=inner_pair,
        tail_fraction=tail_fraction,
        defect_safety_factor=defect_safety_factor,
    )
    tail_count = flow_tube.tail_sample_count
    times = np.asarray(trajectory.t[-tail_count:], dtype=float)
    states = np.asarray(trajectory.y[-tail_count:], dtype=float)
    tube_radius = flow_tube.tube_radius
    picard_passes = 0
    endpoint_passes = 0
    endpoint_subset_passes = 0
    total_substeps = 0
    total_segments = 0
    maximum_lipschitz = 0.0
    maximum_contraction = 0.0
    maximum_propagated_endpoint_radius = tube_radius
    for index in range(len(times) - 1):
        dt = float(times[index + 1] - times[index])
        if dt <= 0.0:
            continue
        segment_lower = np.minimum(states[index], states[index + 1]) - tube_radius
        segment_upper = np.maximum(states[index], states[index + 1]) + tube_radius
        segment_subdivision_lipschitz = _rhs_interval_jacobian_inf_bound(system, segment_lower, segment_upper)
        if not np.isfinite(segment_subdivision_lipschitz) or segment_subdivision_lipschitz <= 0.0:
            substeps = maximum_substeps_per_segment
        else:
            substeps = max(1, int(np.ceil(dt * segment_subdivision_lipschitz / (0.75 * target_contraction))))
            substeps = min(substeps, maximum_substeps_per_segment)
        current_lower = states[index] - initial_state_radius
        current_upper = states[index] + initial_state_radius
        segment_inclusion_ok = True
        for substep in range(substeps):
            alpha0 = substep / substeps
            alpha1 = (substep + 1) / substeps
            center0 = states[index] + alpha0 * (states[index + 1] - states[index])
            center1 = states[index] + alpha1 * (states[index + 1] - states[index])
            z_lower = np.minimum.reduce((center0, center1, current_lower)) - tube_radius
            z_upper = np.maximum.reduce((center0, center1, current_upper)) + tube_radius
            rhs_box = _interval_rhs_from_state_bounds(system, z_lower, z_upper)
            sub_dt = dt / substeps
            image_lower, image_upper = _interval_euler_image(current_lower, current_upper, rhs_box, sub_dt)
            inclusion = _interval_box_subset(image_lower, image_upper, z_lower, z_upper)
            if inclusion:
                picard_passes += 1
            else:
                segment_inclusion_ok = False
            lipschitz = _rhs_lipschitz_bound(
                system,
                z_lower,
                z_upper,
                use_scaled_phase_norm=use_scaled_phase_norm,
            )
            maximum_lipschitz = max(maximum_lipschitz, lipschitz)
            maximum_contraction = max(maximum_contraction, sub_dt * lipschitz)
            current_lower, current_upper = image_lower, image_upper
            total_substeps += 1
        endpoint_box_lower = states[index + 1] - tube_radius
        endpoint_box_upper = states[index + 1] + tube_radius
        endpoint_radius = _interval_box_radius_about_point(current_lower, current_upper, states[index + 1])
        maximum_propagated_endpoint_radius = max(maximum_propagated_endpoint_radius, endpoint_radius)
        if segment_inclusion_ok and _interval_box_subset(current_lower, current_upper, endpoint_box_lower, endpoint_box_upper):
            endpoint_subset_passes += 1
        if segment_inclusion_ok and _interval_boxes_intersect(current_lower, current_upper, endpoint_box_lower, endpoint_box_upper):
            endpoint_passes += 1
        total_segments += 1
    picard_fraction = 0.0 if total_substeps == 0 else float(picard_passes / total_substeps)
    endpoint_fraction = 0.0 if total_segments == 0 else float(endpoint_passes / total_segments)
    endpoint_subset_fraction = 0.0 if total_segments == 0 else float(endpoint_subset_passes / total_segments)
    picard_passed = bool(total_substeps > 0 and picard_passes == total_substeps and maximum_contraction < 1.0)
    endpoint_passed = bool(total_segments > 0 and endpoint_passes == total_segments)
    interval_escape = jacobi_interval_escape_certificate(
        system,
        trajectory,
        inner_pair=inner_pair,
        tail_fraction=tail_fraction,
        absolute_state_radius=maximum_propagated_endpoint_radius,
        relative_state_radius=0.0,
    )
    certified = bool(picard_passed and endpoint_passed and interval_escape.interval_escape_certified)
    warning = ""
    if not picard_passed:
        warning = "Picard self-inclusion or contraction bound fails on at least one tail substep"
    elif not endpoint_passed:
        warning = "propagated interval boxes do not intersect every sampled endpoint tube"
    elif not interval_escape.interval_escape_certified:
        warning = "Jacobi interval escape margin fails on the Picard flow tube"
    return JacobiIntervalPicardFlowCertificate(
        inner_pair=inner_pair,
        outer_body=interval_escape.outer_body,
        tail_sample_count=tail_count,
        segment_count=total_segments,
        substep_count=total_substeps,
        tube_radius=tube_radius,
        initial_state_radius=float(initial_state_radius),
        maximum_propagated_endpoint_radius=float(maximum_propagated_endpoint_radius),
        maximum_lipschitz_bound=float(maximum_lipschitz),
        lipschitz_bound_method=(
            "scaled_phase_space_interval_newtonian_rhs_jacobian"
            if use_scaled_phase_norm
            else "interval_newtonian_rhs_jacobian_inf_row_sum"
        ),
        maximum_observed_contraction=float(maximum_contraction),
        target_contraction=float(target_contraction),
        picard_inclusion_fraction=picard_fraction,
        endpoint_inclusion_fraction=endpoint_fraction,
        endpoint_subset_fraction=endpoint_subset_fraction,
        picard_inclusion_passed=picard_passed,
        endpoint_inclusion_passed=endpoint_passed,
        interval_escape_margin_lower=interval_escape.asymptotic_margin_lower,
        interval_escape_certified=interval_escape.interval_escape_certified,
        picard_flow_certified=certified,
        warning=warning,
    )


def jacobi_picard_tuning_certificate(
    system: object,
    trajectory: TrajectoryResult,
    inner_pair: tuple[int, int] = (0, 1),
    tail_fraction: float = 0.25,
    target_contraction: float = 0.35,
    maximum_substep_candidates: tuple[int, ...] = (64, 128, 256),
    norm_candidates: tuple[bool, ...] = (True, False),
) -> JacobiPicardTuningCertificate:
    """Try Picard contraction settings and select the cheapest certified one."""

    attempts: list[dict[str, float | int | bool | str]] = []
    best: JacobiIntervalPicardFlowCertificate | None = None
    best_cap = 0
    best_scaled = False
    selected: JacobiIntervalPicardFlowCertificate | None = None
    selected_cap = 0
    selected_scaled = False
    for scaled in norm_candidates:
        for cap in maximum_substep_candidates:
            certificate = jacobi_interval_picard_flow_certificate(
                system,
                trajectory,
                inner_pair=inner_pair,
                tail_fraction=tail_fraction,
                target_contraction=target_contraction,
                maximum_substeps_per_segment=cap,
                use_scaled_phase_norm=scaled,
            )
            attempts.append(
                {
                    "maximum_substeps_per_segment": int(cap),
                    "use_scaled_phase_norm": bool(scaled),
                    "lipschitz_bound_method": certificate.lipschitz_bound_method,
                    "observed_contraction": certificate.maximum_observed_contraction,
                    "substep_count": certificate.substep_count,
                    "interval_escape_margin_lower": certificate.interval_escape_margin_lower,
                    "certified": certificate.picard_flow_certified,
                    "warning": certificate.warning,
                }
            )
            if best is None or (
                certificate.picard_flow_certified,
                certificate.interval_escape_margin_lower,
                -certificate.maximum_observed_contraction,
            ) > (
                best.picard_flow_certified,
                best.interval_escape_margin_lower,
                -best.maximum_observed_contraction,
            ):
                best = certificate
                best_cap = cap
                best_scaled = scaled
            if certificate.picard_flow_certified and selected is None:
                selected = certificate
                selected_cap = cap
                selected_scaled = scaled
                break
        if selected is not None:
            break
    chosen = selected or best
    if chosen is None:
        raise RuntimeError("Picard tuning produced no attempts.")
    certified = bool(chosen.picard_flow_certified)
    warning = "" if certified else "no Picard tuning candidate certified the interval flow"
    mean_substeps = float(chosen.substep_count / max(chosen.segment_count, 1))
    reserve = float(target_contraction - chosen.maximum_observed_contraction)
    return JacobiPicardTuningCertificate(
        inner_pair=inner_pair,
        outer_body=chosen.outer_body,
        attempted_count=len(attempts),
        selected_maximum_substeps_per_segment=int(selected_cap if selected is not None else best_cap),
        selected_scaled_phase_norm=bool(selected_scaled if selected is not None else best_scaled),
        selected_lipschitz_bound_method=chosen.lipschitz_bound_method,
        best_observed_contraction=chosen.maximum_observed_contraction,
        contraction_reserve=reserve,
        best_interval_escape_margin_lower=chosen.interval_escape_margin_lower,
        best_substep_count=chosen.substep_count,
        mean_substeps_per_segment=mean_substeps,
        certification_efficiency=float(max(reserve, 0.0) / max(mean_substeps, 1.0e-12)),
        target_contraction=target_contraction,
        certified=certified,
        attempts=tuple(attempts),
        warning=warning,
    )


def _interaction_remainder_bound(
    gravitational_constant: float,
    masses: np.ndarray,
    positions: np.ndarray,
    pair_center: np.ndarray,
    outer_position: np.ndarray,
    inner_pair: tuple[int, int],
    outer: int,
) -> float:
    outer_radius = _safe_norm(outer_position)
    offsets = [positions[index] - pair_center for index in inner_pair]
    maximum_offset = max(_safe_norm(offset) for offset in offsets)
    if maximum_offset >= outer_radius:
        return float("inf")
    denominator = outer_radius * max(outer_radius - maximum_offset, 1.0e-12)
    total = 0.0
    for index, offset in zip(inner_pair, offsets, strict=True):
        total += float(masses[index] * _safe_norm(offset))
    return float(gravitational_constant * masses[outer] * total / denominator)


def _quadrupole_interaction_remainder_bound(
    gravitational_constant: float,
    masses: np.ndarray,
    positions: np.ndarray,
    pair_center: np.ndarray,
    outer_position: np.ndarray,
    inner_pair: tuple[int, int],
    outer: int,
) -> float:
    outer_radius = _safe_norm(outer_position)
    offsets = [positions[index] - pair_center for index in inner_pair]
    maximum_offset = max(_safe_norm(offset) for offset in offsets)
    if maximum_offset >= outer_radius:
        return float("inf")
    second_moment = sum(float(masses[index] * np.dot(offset, offset)) for index, offset in zip(inner_pair, offsets, strict=True))
    return float(gravitational_constant * masses[outer] * second_moment / max(outer_radius - maximum_offset, 1.0e-12) ** 3)


@dataclass(frozen=True, slots=True)
class _Interval:
    lo: float
    hi: float

    def __post_init__(self) -> None:
        if self.lo > self.hi:
            raise ValueError("interval lower endpoint exceeds upper endpoint")

    @property
    def width(self) -> float:
        return float(self.hi - self.lo)

    @property
    def abs_upper(self) -> float:
        return float(max(abs(self.lo), abs(self.hi)))

    def contains(self, value: float) -> bool:
        return self.lo <= value <= self.hi


def _interval_jacobi_tail_row(
    system: object,
    state: np.ndarray,
    inner_pair: tuple[int, int],
    state_radius: float,
) -> dict[str, object]:
    positions, velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    gravitational_constant = float(system.gravitational_constant)
    i, j = inner_pair
    outer = next(index for index in range(3) if index not in inner_pair)
    pair_mass = float(masses[i] + masses[j])
    total_mass = float(pair_mass + masses[outer])
    inner_reduced_mass = float(masses[i] * masses[j] / pair_mass)
    outer_reduced_mass = float(pair_mass * masses[outer] / total_mass)

    position_boxes = _interval_matrix_from_points(positions, state_radius)
    velocity_boxes = _interval_matrix_from_points(velocities, state_radius)
    pair_center = _interval_vector_linear_combination(
        (
            (float(masses[i] / pair_mass), position_boxes[i]),
            (float(masses[j] / pair_mass), position_boxes[j]),
        )
    )
    pair_velocity = _interval_vector_linear_combination(
        (
            (float(masses[i] / pair_mass), velocity_boxes[i]),
            (float(masses[j] / pair_mass), velocity_boxes[j]),
        )
    )
    total_velocity = _interval_vector_linear_combination(
        tuple((float(masses[index] / total_mass), velocity_boxes[index]) for index in range(3))
    )
    inner_position = _interval_vector_sub(position_boxes[j], position_boxes[i])
    inner_velocity = _interval_vector_sub(velocity_boxes[j], velocity_boxes[i])
    outer_position = _interval_vector_sub(position_boxes[outer], pair_center)
    outer_velocity = _interval_vector_sub(velocity_boxes[outer], pair_velocity)
    inner_radius = _interval_norm(inner_position)
    outer_radius = _interval_norm(outer_position)
    inner_speed_squared = _interval_norm_squared(inner_velocity)
    outer_speed_squared = _interval_norm_squared(outer_velocity)
    outer_speed = _interval_sqrt(outer_speed_squared)

    inner_kepler = _interval_add(
        _interval_mul_scalar(0.5 * inner_reduced_mass, inner_speed_squared),
        _interval_negative_reciprocal_scaled(gravitational_constant * masses[i] * masses[j], inner_radius),
    )
    outer_kepler = _interval_add(
        _interval_mul_scalar(0.5 * outer_reduced_mass, outer_speed_squared),
        _interval_negative_reciprocal_scaled(gravitational_constant * pair_mass * masses[outer], outer_radius),
    )
    actual_outer_potential = _interval_add(
        _interval_negative_reciprocal_scaled(
            gravitational_constant * masses[outer] * masses[i],
            _interval_norm(_interval_vector_sub(position_boxes[outer], position_boxes[i])),
        ),
        _interval_negative_reciprocal_scaled(
            gravitational_constant * masses[outer] * masses[j],
            _interval_norm(_interval_vector_sub(position_boxes[outer], position_boxes[j])),
        ),
    )
    monopole_outer_potential = _interval_negative_reciprocal_scaled(
        gravitational_constant * pair_mass * masses[outer],
        outer_radius,
    )
    interaction = _interval_sub(actual_outer_potential, monopole_outer_potential)

    total_energy = _interval_total_energy(
        gravitational_constant,
        masses,
        position_boxes,
        velocity_boxes,
    )
    center_kinetic = _interval_mul_scalar(0.5 * total_mass, _interval_norm_squared(total_velocity))
    reduced_total = _interval_sub(total_energy, center_kinetic)
    split_sum = _interval_add(_interval_add(inner_kepler, outer_kepler), interaction)
    split_identity = _interval_sub(reduced_total, split_sum)
    radial_velocity = _interval_div_positive(_interval_dot(outer_position, outer_velocity), outer_radius)
    hierarchy_ratio_lower = float(outer_radius.lo / max(inner_radius.hi, 1.0e-18))
    return {
        "outer_body": outer,
        "inner_radius": inner_radius,
        "outer_radius": outer_radius,
        "outer_speed": outer_speed,
        "outer_kepler_energy": outer_kepler,
        "interaction": interaction,
        "interaction_abs_upper": interaction.abs_upper,
        "radial_velocity": radial_velocity,
        "hierarchy_ratio_lower": hierarchy_ratio_lower,
        "quadrupole_acceleration_constant_upper": _interval_quadrupole_acceleration_constant_upper(
            system,
            position_boxes,
            inner_pair,
            outer,
        ),
        "split_identity": split_identity,
    }


def _interval_matrix_from_points(values: np.ndarray, radius: float) -> tuple[tuple[_Interval, ...], ...]:
    return tuple(
        tuple(_Interval(float(component - radius), float(component + radius)) for component in row)
        for row in np.asarray(values, dtype=float)
    )


def _interval_matrix_from_bounds(
    lower: np.ndarray,
    upper: np.ndarray,
) -> tuple[tuple[_Interval, ...], ...]:
    return tuple(
        tuple(_Interval(float(lo), float(hi)) for lo, hi in zip(lower_row, upper_row, strict=True))
        for lower_row, upper_row in zip(np.asarray(lower, dtype=float), np.asarray(upper, dtype=float), strict=True)
    )


def _interval_rhs_from_state_bounds(
    system: object,
    state_lower: np.ndarray,
    state_upper: np.ndarray,
) -> tuple[_Interval, ...]:
    dimension = int(system.body_count * system.dimension)
    position_lower = np.asarray(state_lower[:dimension], dtype=float).reshape(system.body_count, system.dimension)
    position_upper = np.asarray(state_upper[:dimension], dtype=float).reshape(system.body_count, system.dimension)
    velocity_lower = np.asarray(state_lower[dimension:], dtype=float).reshape(system.body_count, system.dimension)
    velocity_upper = np.asarray(state_upper[dimension:], dtype=float).reshape(system.body_count, system.dimension)
    position_boxes = _interval_matrix_from_bounds(position_lower, position_upper)
    velocity_boxes = _interval_matrix_from_bounds(velocity_lower, velocity_upper)
    acceleration_boxes = _interval_acceleration_field(system, position_boxes)
    return tuple(component for row in velocity_boxes for component in row) + tuple(
        component for row in acceleration_boxes for component in row
    )


def _interval_acceleration_field(
    system: object,
    position_boxes: tuple[tuple[_Interval, ...], ...],
) -> tuple[tuple[_Interval, ...], ...]:
    masses = np.asarray(system.masses, dtype=float)
    accelerations = []
    for i in range(system.body_count):
        components = []
        for axis in range(system.dimension):
            component = _Interval(0.0, 0.0)
            for j in range(system.body_count):
                if i == j:
                    continue
                displacement = _interval_vector_sub(position_boxes[j], position_boxes[i])
                distance = _interval_norm(displacement)
                if distance.lo <= 0.0:
                    contribution = _Interval(float("-inf"), float("inf"))
                else:
                    reciprocal_distance_cubed = _Interval(
                        float(1.0 / distance.hi**3),
                        float(1.0 / distance.lo**3),
                    )
                    contribution = _interval_mul_scalar(
                        float(system.gravitational_constant * masses[j]),
                        _interval_mul(displacement[axis], reciprocal_distance_cubed),
                    )
                component = _interval_add(component, contribution)
            components.append(component)
        accelerations.append(tuple(components))
    return tuple(accelerations)


def _interval_euler_image(
    current_lower: np.ndarray,
    current_upper: np.ndarray,
    rhs_box: tuple[_Interval, ...],
    step: float,
) -> tuple[np.ndarray, np.ndarray]:
    lower = []
    upper = []
    for lo, hi, rhs in zip(current_lower, current_upper, rhs_box, strict=True):
        image = _interval_add(_Interval(float(lo), float(hi)), _interval_mul_scalar(step, rhs))
        lower.append(image.lo)
        upper.append(image.hi)
    return np.asarray(lower, dtype=float), np.asarray(upper, dtype=float)


def _interval_box_subset(
    lower: np.ndarray,
    upper: np.ndarray,
    container_lower: np.ndarray,
    container_upper: np.ndarray,
) -> bool:
    return bool(np.all(lower >= container_lower) and np.all(upper <= container_upper))


def _interval_boxes_intersect(
    first_lower: np.ndarray,
    first_upper: np.ndarray,
    second_lower: np.ndarray,
    second_upper: np.ndarray,
) -> bool:
    return bool(np.all(first_upper >= second_lower) and np.all(second_upper >= first_lower))


def _interval_box_radius_about_point(lower: np.ndarray, upper: np.ndarray, center: np.ndarray) -> float:
    lower_radius = np.max(np.abs(np.asarray(center, dtype=float) - np.asarray(lower, dtype=float)))
    upper_radius = np.max(np.abs(np.asarray(upper, dtype=float) - np.asarray(center, dtype=float)))
    return float(max(lower_radius, upper_radius))


def _rhs_lipschitz_inf_bound(system: object, state_lower: np.ndarray, state_upper: np.ndarray) -> float:
    return _rhs_interval_jacobian_inf_bound(system, state_lower, state_upper)


def _rhs_lipschitz_bound(
    system: object,
    state_lower: np.ndarray,
    state_upper: np.ndarray,
    *,
    use_scaled_phase_norm: bool,
) -> float:
    if use_scaled_phase_norm:
        return _rhs_interval_jacobian_scaled_phase_bound(system, state_lower, state_upper)
    return _rhs_interval_jacobian_inf_bound(system, state_lower, state_upper)


def _rhs_interval_jacobian_inf_bound(system: object, state_lower: np.ndarray, state_upper: np.ndarray) -> float:
    maximum_acceleration_row_sum = _maximum_acceleration_jacobian_row_sum(system, state_lower, state_upper)
    if not np.isfinite(maximum_acceleration_row_sum):
        return float("inf")
    return float(max(1.0, maximum_acceleration_row_sum))


def _rhs_interval_jacobian_scaled_phase_bound(
    system: object,
    state_lower: np.ndarray,
    state_upper: np.ndarray,
) -> float:
    """Scaled phase-space bound for `q'=v, v'=a(q)`.

    In coordinates with different position and velocity scales, the Jacobian
    block bound becomes `max(s, A/s)`, where `A` bounds the acceleration
    Jacobian row sum. Choosing `s=sqrt(A)` gives a tighter local normal-form-like
    contraction proxy while preserving an explicit coordinate transform.
    """

    maximum_acceleration_row_sum = _maximum_acceleration_jacobian_row_sum(system, state_lower, state_upper)
    if not np.isfinite(maximum_acceleration_row_sum):
        return float("inf")
    return float(max(1.0e-12, np.sqrt(max(maximum_acceleration_row_sum, 1.0e-24))))


def _maximum_acceleration_jacobian_row_sum(system: object, state_lower: np.ndarray, state_upper: np.ndarray) -> float:
    dimension = int(system.body_count * system.dimension)
    position_lower = np.asarray(state_lower[:dimension], dtype=float).reshape(system.body_count, system.dimension)
    position_upper = np.asarray(state_upper[:dimension], dtype=float).reshape(system.body_count, system.dimension)
    position_boxes = _interval_matrix_from_bounds(position_lower, position_upper)
    masses = np.asarray(system.masses, dtype=float)
    maximum_acceleration_row_sum = 0.0
    for i in range(system.body_count):
        for axis in range(system.dimension):
            row_sum = 0.0
            for j in range(system.body_count):
                if i == j:
                    continue
                displacement = _interval_vector_sub(position_boxes[j], position_boxes[i])
                distance = _interval_norm(displacement)
                if distance.lo <= 0.0:
                    return float("inf")
                row_sum += 2.0 * float(system.gravitational_constant * masses[j]) * _pair_force_jacobian_row_sum_bound(
                    displacement,
                    axis,
                    distance.lo,
                )
            maximum_acceleration_row_sum = max(maximum_acceleration_row_sum, row_sum)
    return float(max(1.0, maximum_acceleration_row_sum))


def _pair_force_jacobian_row_sum_bound(
    displacement: tuple[_Interval, ...],
    axis: int,
    distance_lower: float,
) -> float:
    reciprocal_radius_cubed = 1.0 / distance_lower**3
    reciprocal_radius_fifth = 1.0 / distance_lower**5
    axis_abs = _interval_abs_upper(displacement[axis])
    row_sum = 0.0
    for column, component in enumerate(displacement):
        delta_term = reciprocal_radius_cubed if axis == column else 0.0
        tidal_term = 3.0 * axis_abs * _interval_abs_upper(component) * reciprocal_radius_fifth
        row_sum += delta_term + tidal_term
    return float(row_sum)


def _interval_abs_upper(interval: _Interval) -> float:
    return float(max(abs(interval.lo), abs(interval.hi)))


def _interval_total_energy(
    gravitational_constant: float,
    masses: np.ndarray,
    positions: tuple[tuple[_Interval, ...], ...],
    velocities: tuple[tuple[_Interval, ...], ...],
) -> _Interval:
    total = _Interval(0.0, 0.0)
    for index, velocity in enumerate(velocities):
        total = _interval_add(total, _interval_mul_scalar(0.5 * masses[index], _interval_norm_squared(velocity)))
    for first in range(3):
        for second in range(first + 1, 3):
            distance = _interval_norm(_interval_vector_sub(positions[second], positions[first]))
            total = _interval_add(
                total,
                _interval_negative_reciprocal_scaled(
                    gravitational_constant * masses[first] * masses[second],
                    distance,
                ),
            )
    return total


def _interval_quadrupole_acceleration_constant_upper(
    system: object,
    positions: tuple[tuple[_Interval, ...], ...],
    inner_pair: tuple[int, int],
    outer: int,
) -> float:
    masses = np.asarray(system.masses, dtype=float)
    pair_mass = float(sum(masses[index] for index in inner_pair))
    total_mass = float(pair_mass + masses[outer])
    pair_center = _interval_vector_linear_combination(
        tuple((float(masses[index] / pair_mass), positions[index]) for index in inner_pair)
    )
    second_moment_upper = 0.0
    for index in inner_pair:
        offset = _interval_vector_sub(positions[index], pair_center)
        second_moment_upper += float(masses[index] * _interval_norm_squared(offset).hi)
    return float(6.0 * system.gravitational_constant * total_mass * second_moment_upper / pair_mass)


def _interval_vector_sub(
    first: tuple[_Interval, ...],
    second: tuple[_Interval, ...],
) -> tuple[_Interval, ...]:
    return tuple(_interval_sub(a, b) for a, b in zip(first, second, strict=True))


def _interval_vector_linear_combination(
    terms: tuple[tuple[float, tuple[_Interval, ...]], ...],
) -> tuple[_Interval, ...]:
    dimension = len(terms[0][1])
    components = []
    for axis in range(dimension):
        component = _Interval(0.0, 0.0)
        for scalar, vector in terms:
            component = _interval_add(component, _interval_mul_scalar(scalar, vector[axis]))
        components.append(component)
    return tuple(components)


def _interval_norm(vector: tuple[_Interval, ...]) -> _Interval:
    return _interval_sqrt(_interval_norm_squared(vector))


def _interval_norm_squared(vector: tuple[_Interval, ...]) -> _Interval:
    total = _Interval(0.0, 0.0)
    for component in vector:
        total = _interval_add(total, _interval_square(component))
    return total


def _interval_dot(first: tuple[_Interval, ...], second: tuple[_Interval, ...]) -> _Interval:
    total = _Interval(0.0, 0.0)
    for a, b in zip(first, second, strict=True):
        total = _interval_add(total, _interval_mul(a, b))
    return total


def _interval_add(first: _Interval, second: _Interval) -> _Interval:
    return _Interval(float(first.lo + second.lo), float(first.hi + second.hi))


def _interval_sub(first: _Interval, second: _Interval) -> _Interval:
    return _Interval(float(first.lo - second.hi), float(first.hi - second.lo))


def _interval_mul(first: _Interval, second: _Interval) -> _Interval:
    candidates = (
        first.lo * second.lo,
        first.lo * second.hi,
        first.hi * second.lo,
        first.hi * second.hi,
    )
    return _Interval(float(min(candidates)), float(max(candidates)))


def _interval_mul_scalar(scalar: float, interval: _Interval) -> _Interval:
    if scalar >= 0.0:
        return _Interval(float(scalar * interval.lo), float(scalar * interval.hi))
    return _Interval(float(scalar * interval.hi), float(scalar * interval.lo))


def _interval_square(interval: _Interval) -> _Interval:
    if interval.lo <= 0.0 <= interval.hi:
        return _Interval(0.0, float(max(interval.lo * interval.lo, interval.hi * interval.hi)))
    return _Interval(
        float(min(interval.lo * interval.lo, interval.hi * interval.hi)),
        float(max(interval.lo * interval.lo, interval.hi * interval.hi)),
    )


def _interval_sqrt(interval: _Interval) -> _Interval:
    return _Interval(float(np.sqrt(max(interval.lo, 0.0))), float(np.sqrt(max(interval.hi, 0.0))))


def _interval_div_positive(numerator: _Interval, denominator: _Interval) -> _Interval:
    if denominator.lo <= 0.0:
        return _Interval(float("-inf"), float("inf"))
    reciprocal = _Interval(float(1.0 / denominator.hi), float(1.0 / denominator.lo))
    return _interval_mul(numerator, reciprocal)


def _interval_negative_reciprocal_scaled(scale: float, radius: _Interval) -> _Interval:
    if radius.lo <= 0.0:
        return _Interval(float("-inf"), float("inf"))
    return _Interval(float(-scale / radius.lo), float(-scale / radius.hi))


def _quadrupole_acceleration_constant(
    system: object,
    state: np.ndarray,
    inner_pair: tuple[int, int],
    outer: int,
) -> float:
    positions, _velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    pair_mass = float(sum(masses[index] for index in inner_pair))
    total_mass = float(pair_mass + masses[outer])
    pair_center = sum(masses[index] * positions[index] for index in inner_pair) / pair_mass
    offsets = [positions[index] - pair_center for index in inner_pair]
    second_moment = sum(float(masses[index] * np.dot(offset, offset)) for index, offset in zip(inner_pair, offsets, strict=True))
    return float(6.0 * system.gravitational_constant * total_mass * second_moment / pair_mass)


def _outer_jacobi_perturbing_acceleration(
    system: object,
    state: np.ndarray,
    inner_pair: tuple[int, int],
    outer: int,
) -> np.ndarray:
    positions, _velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    pair_mass = float(sum(masses[index] for index in inner_pair))
    total_mass = float(pair_mass + masses[outer])
    accelerations = system.acceleration_field(positions)
    pair_center = sum(masses[index] * positions[index] for index in inner_pair) / pair_mass
    pair_acceleration = sum(masses[index] * accelerations[index] for index in inner_pair) / pair_mass
    outer_position = positions[outer] - pair_center
    outer_radius = _safe_norm(outer_position)
    actual_relative_acceleration = accelerations[outer] - pair_acceleration
    monopole_acceleration = -system.gravitational_constant * total_mass * outer_position / outer_radius**3
    return actual_relative_acceleration - monopole_acceleration


def _maximum_outer_relative_speed(
    system: object,
    states: np.ndarray,
    inner_pair: tuple[int, int],
    outer: int,
) -> float:
    masses = np.asarray(system.masses, dtype=float)
    pair_mass = float(sum(masses[index] for index in inner_pair))
    speeds = []
    for state in states:
        _positions, velocities = system.split_state(state)
        pair_velocity = sum(masses[index] * velocities[index] for index in inner_pair) / pair_mass
        speeds.append(float(np.linalg.norm(velocities[outer] - pair_velocity)))
    return float(max(speeds))


def _safe_norm(vector: np.ndarray) -> float:
    return max(float(np.linalg.norm(vector)), 1.0e-12)


def _terminal_state_perturbed_trajectory(
    trajectory: TrajectoryResult,
    axis: int,
    delta: float,
) -> TrajectoryResult:
    perturbed = np.array(trajectory.y, dtype=float, copy=True)
    perturbed[-1, axis] += delta
    return TrajectoryResult(
        t=trajectory.t,
        y=perturbed,
        success=trajectory.success,
        message=trajectory.message,
        metadata=dict(trajectory.metadata),
    )


def _relative_span(values: np.ndarray) -> float:
    finite = np.asarray(values[np.isfinite(values)], dtype=float)
    if finite.size == 0:
        return float("inf")
    scale = max(abs(float(np.mean(finite))), 1.0e-12)
    return float((np.max(finite) - np.min(finite)) / scale)
