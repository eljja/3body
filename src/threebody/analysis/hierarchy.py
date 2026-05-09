from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import TrajectoryResult
from ..utils import cross_3d
from .coordinates import general_three_body_features


@dataclass(frozen=True, slots=True)
class HierarchicalElements:
    """Kepler-style elements for a tight inner pair and an outer perturber."""

    inner_pair: tuple[int, int]
    outer_body: int
    inner_semimajor_axis: float
    inner_eccentricity: float
    inner_specific_energy: float
    inner_angular_momentum_norm: float
    outer_radius: float
    outer_specific_energy: float
    perturbation_strength: float
    hierarchy_ratio: float
    is_inner_bound: bool


@dataclass(frozen=True, slots=True)
class HierarchyActionDriftBound:
    """Numerical drift certificate for an osculating inner binary over one trajectory interval."""

    inner_pair: tuple[int, int]
    outer_body: int
    sample_count: int
    relative_action_drift: float
    relative_angular_momentum_drift: float
    max_perturbation_strength: float
    perturbation_budget: float
    bound_multiplier: float
    bound_satisfied: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "sample_count": self.sample_count,
            "relative_action_drift": self.relative_action_drift,
            "relative_angular_momentum_drift": self.relative_angular_momentum_drift,
            "max_perturbation_strength": self.max_perturbation_strength,
            "perturbation_budget": self.perturbation_budget,
            "bound_multiplier": self.bound_multiplier,
            "bound_satisfied": self.bound_satisfied,
            "warning": self.warning,
        }


def hierarchical_elements(system: object, state: np.ndarray) -> HierarchicalElements:
    """Extract the leading two-body hierarchy from a general three-body state."""

    positions, velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    features = general_three_body_features(system, state)
    i, j = features.nearest_pair
    outer = next(index for index in range(3) if index not in features.nearest_pair)

    inner_position = positions[j] - positions[i]
    inner_velocity = velocities[j] - velocities[i]
    inner_energy = features.nearest_pair_specific_energy
    inner_h = cross_3d(inner_position, inner_velocity)
    inner_h_norm = float(np.linalg.norm(inner_h))
    eccentricity = features.nearest_pair_eccentricity
    semimajor_axis = features.nearest_pair_semimajor_axis

    pair_mass = masses[i] + masses[j]
    pair_center = (masses[i] * positions[i] + masses[j] * positions[j]) / pair_mass
    outer_position = positions[outer] - pair_center
    outer_radius = float(np.linalg.norm(outer_position))

    return HierarchicalElements(
        inner_pair=(i, j),
        outer_body=outer,
        inner_semimajor_axis=semimajor_axis,
        inner_eccentricity=eccentricity,
        inner_specific_energy=float(inner_energy),
        inner_angular_momentum_norm=inner_h_norm,
        outer_radius=outer_radius,
        outer_specific_energy=features.outer_specific_energy,
        perturbation_strength=features.hierarchy_perturbation_strength,
        hierarchy_ratio=features.hierarchy_ratio,
        is_inner_bound=bool(inner_energy < 0.0 and eccentricity < 1.0),
    )


def hierarchy_action_drift_bound(
    system: object,
    trajectory: TrajectoryResult,
    start_index: int = 0,
    end_index: int | None = None,
    bound_multiplier: float = 25.0,
) -> HierarchyActionDriftBound:
    """Estimate whether inner-binary action drift is controlled by the tidal perturbation budget.

    This is a numerical certificate, not a theorem. It is meant to identify hierarchy intervals where
    a perturbative Kepler chart is plausible enough to promote to analytic proof work.
    """

    if getattr(system, "body_count", None) != 3:
        raise TypeError("hierarchy_action_drift_bound requires a general three-body system.")
    end = len(trajectory.t) - 1 if end_index is None else min(end_index, len(trajectory.t) - 1)
    start = max(0, min(start_index, end))
    states = trajectory.y[start : end + 1]
    times = trajectory.t[start : end + 1]
    if len(states) < 2:
        element = hierarchical_elements(system, states[0])
        return HierarchyActionDriftBound(
            inner_pair=element.inner_pair,
            outer_body=element.outer_body,
            sample_count=len(states),
            relative_action_drift=0.0,
            relative_angular_momentum_drift=0.0,
            max_perturbation_strength=element.perturbation_strength,
            perturbation_budget=0.0,
            bound_multiplier=bound_multiplier,
            bound_satisfied=True,
            warning="single-sample interval; drift is not resolved",
        )

    elements = tuple(hierarchical_elements(system, state) for state in states)
    pair = elements[0].inner_pair
    outer = elements[0].outer_body
    pair_changed = any(element.inner_pair != pair or element.outer_body != outer for element in elements)
    masses = np.asarray(system.masses, dtype=float)
    mu = float(system.gravitational_constant * (masses[pair[0]] + masses[pair[1]]))
    actions = np.asarray([_inner_kepler_action(mu, element.inner_semimajor_axis) for element in elements], dtype=float)
    angular_momenta = np.asarray([element.inner_angular_momentum_norm for element in elements], dtype=float)
    perturbations = np.asarray([element.perturbation_strength for element in elements], dtype=float)
    periods = np.asarray(
        [_inner_period(mu, element.inner_semimajor_axis) for element in elements if np.isfinite(element.inner_semimajor_axis)],
        dtype=float,
    )
    reference_period = float(np.median(periods)) if periods.size else max(float(times[-1] - times[0]), 1.0e-12)
    perturbation_budget = float(np.trapezoid(perturbations, times) / max(reference_period, 1.0e-12))
    relative_action_drift = _relative_span(actions)
    relative_angular_momentum_drift = _relative_span(angular_momenta)
    tolerated = bound_multiplier * perturbation_budget + 1.0e-10
    bound_satisfied = (
        bool(not pair_changed)
        and bool(np.all(np.isfinite(actions)))
        and relative_action_drift <= tolerated
        and relative_angular_momentum_drift <= tolerated
    )
    warning = ""
    if pair_changed:
        warning = "nearest inner pair changed inside interval; hierarchy chart is not a single Kepler chart"
    elif not np.all(np.isfinite(actions)):
        warning = "inner binary became unbound or semimajor axis was not finite"
    elif not bound_satisfied:
        warning = "measured action drift exceeded perturbation-budget tolerance"
    return HierarchyActionDriftBound(
        inner_pair=pair,
        outer_body=outer,
        sample_count=len(states),
        relative_action_drift=relative_action_drift,
        relative_angular_momentum_drift=relative_angular_momentum_drift,
        max_perturbation_strength=float(np.max(perturbations)),
        perturbation_budget=perturbation_budget,
        bound_multiplier=bound_multiplier,
        bound_satisfied=bound_satisfied,
        warning=warning,
    )


def _inner_kepler_action(mu: float, semimajor_axis: float) -> float:
    if not np.isfinite(semimajor_axis) or semimajor_axis <= 0.0:
        return np.inf
    return float(np.sqrt(mu * semimajor_axis))


def _inner_period(mu: float, semimajor_axis: float) -> float:
    if not np.isfinite(semimajor_axis) or semimajor_axis <= 0.0:
        return np.inf
    return float(2.0 * np.pi * np.sqrt(semimajor_axis**3 / max(mu, 1.0e-12)))


def _relative_span(values: np.ndarray) -> float:
    finite = np.asarray(values[np.isfinite(values)], dtype=float)
    if finite.size == 0:
        return np.inf
    scale = max(abs(float(finite[0])), 1.0e-12)
    return float((np.max(finite) - np.min(finite)) / scale)
