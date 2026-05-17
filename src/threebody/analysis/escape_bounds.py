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


def _safe_norm(vector: np.ndarray) -> float:
    return max(float(np.linalg.norm(vector)), 1.0e-12)


def _relative_span(values: np.ndarray) -> float:
    finite = np.asarray(values[np.isfinite(values)], dtype=float)
    if finite.size == 0:
        return float("inf")
    scale = max(abs(float(np.mean(finite))), 1.0e-12)
    return float((np.max(finite) - np.min(finite)) / scale)
