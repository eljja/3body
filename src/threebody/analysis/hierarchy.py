from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

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


@dataclass(frozen=True, slots=True)
class HierarchyResonanceDiagnostic:
    """Numerical resonance classifier for a hierarchical inner/outer split."""

    inner_pair: tuple[int, int]
    outer_body: int
    sample_count: int
    median_frequency_ratio: float
    nearest_resonance_numerator: int
    nearest_resonance_denominator: int
    relative_detuning: float
    resonance_tolerance: float
    classification: str
    warning: str

    def as_dict(self) -> dict[str, float | int | str | tuple[int, int]]:
        return {
            "inner_pair": self.inner_pair,
            "outer_body": self.outer_body,
            "sample_count": self.sample_count,
            "median_frequency_ratio": self.median_frequency_ratio,
            "nearest_resonance_numerator": self.nearest_resonance_numerator,
            "nearest_resonance_denominator": self.nearest_resonance_denominator,
            "relative_detuning": self.relative_detuning,
            "resonance_tolerance": self.resonance_tolerance,
            "classification": self.classification,
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


def hierarchy_resonance_diagnostic(
    system: object,
    trajectory: TrajectoryResult,
    start_index: int = 0,
    end_index: int | None = None,
    max_denominator: int = 8,
    resonance_tolerance: float = 0.02,
) -> HierarchyResonanceDiagnostic:
    """Classify a hierarchy interval as resonant or nonresonant by frequency detuning."""

    if getattr(system, "body_count", None) != 3:
        raise TypeError("hierarchy_resonance_diagnostic requires a general three-body system.")
    end = len(trajectory.t) - 1 if end_index is None else min(end_index, len(trajectory.t) - 1)
    start = max(0, min(start_index, end))
    states = trajectory.y[start : end + 1]
    elements = tuple(hierarchical_elements(system, state) for state in states)
    pair = elements[0].inner_pair
    outer = elements[0].outer_body
    pair_changed = any(element.inner_pair != pair or element.outer_body != outer for element in elements)
    ratios = []
    for state, element in zip(states, elements, strict=True):
        inner_frequency = _inner_mean_motion(system, pair, element.inner_semimajor_axis)
        outer_frequency = _outer_angular_frequency(system, state, pair, outer)
        if np.isfinite(inner_frequency) and np.isfinite(outer_frequency) and abs(outer_frequency) > 1.0e-12:
            ratios.append(abs(inner_frequency / outer_frequency))
    if not ratios:
        return HierarchyResonanceDiagnostic(
            inner_pair=pair,
            outer_body=outer,
            sample_count=len(states),
            median_frequency_ratio=np.inf,
            nearest_resonance_numerator=0,
            nearest_resonance_denominator=1,
            relative_detuning=np.inf,
            resonance_tolerance=resonance_tolerance,
            classification="unresolved",
            warning="no finite inner/outer frequency ratio could be computed",
        )
    median_ratio = float(np.median(np.asarray(ratios, dtype=float)))
    resonance = Fraction(median_ratio).limit_denominator(max_denominator)
    resonance_value = float(resonance.numerator / resonance.denominator)
    detuning = float(abs(median_ratio - resonance_value) / max(abs(median_ratio), 1.0e-12))
    if pair_changed:
        classification = "unresolved"
        warning = "nearest inner pair changed inside interval; resonance class is not stable"
    elif detuning <= resonance_tolerance:
        classification = "near_resonant"
        warning = ""
    else:
        classification = "nonresonant"
        warning = ""
    return HierarchyResonanceDiagnostic(
        inner_pair=pair,
        outer_body=outer,
        sample_count=len(states),
        median_frequency_ratio=median_ratio,
        nearest_resonance_numerator=int(resonance.numerator),
        nearest_resonance_denominator=int(resonance.denominator),
        relative_detuning=detuning,
        resonance_tolerance=resonance_tolerance,
        classification=classification,
        warning=warning,
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


def _inner_mean_motion(system: object, pair: tuple[int, int], semimajor_axis: float) -> float:
    if not np.isfinite(semimajor_axis) or semimajor_axis <= 0.0:
        return np.inf
    masses = np.asarray(system.masses, dtype=float)
    mu = float(system.gravitational_constant * (masses[pair[0]] + masses[pair[1]]))
    return float(np.sqrt(mu / semimajor_axis**3))


def _outer_angular_frequency(system: object, state: np.ndarray, pair: tuple[int, int], outer: int) -> float:
    positions, velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    pair_mass = masses[pair[0]] + masses[pair[1]]
    pair_center = (masses[pair[0]] * positions[pair[0]] + masses[pair[1]] * positions[pair[1]]) / pair_mass
    pair_velocity = (masses[pair[0]] * velocities[pair[0]] + masses[pair[1]] * velocities[pair[1]]) / pair_mass
    radius = positions[outer] - pair_center
    velocity = velocities[outer] - pair_velocity
    radius_norm = float(np.linalg.norm(radius))
    if radius_norm <= 1.0e-12:
        return np.inf
    angular = cross_3d(radius, velocity)
    return float(np.linalg.norm(angular) / radius_norm**2)


def _relative_span(values: np.ndarray) -> float:
    finite = np.asarray(values[np.isfinite(values)], dtype=float)
    if finite.size == 0:
        return np.inf
    scale = max(abs(float(finite[0])), 1.0e-12)
    return float((np.max(finite) - np.min(finite)) / scale)
