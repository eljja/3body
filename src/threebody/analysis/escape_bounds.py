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


def _relative_span(values: np.ndarray) -> float:
    finite = np.asarray(values[np.isfinite(values)], dtype=float)
    if finite.size == 0:
        return float("inf")
    scale = max(abs(float(np.mean(finite))), 1.0e-12)
    return float((np.max(finite) - np.min(finite)) / scale)
