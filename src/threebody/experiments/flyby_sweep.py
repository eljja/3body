from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

import numpy as np

from ..analysis import (
    AnalysisAtlas,
    detect_hysteresis_loops,
    estimate_transition_boundaries,
    fit_power_law_boundary_collapse,
)
from ..solvers import AdaptiveIntegrator
from ..utils import orbit_period
from .orbit_library import OrbitLibrary


@dataclass(frozen=True, slots=True)
class FlybySweepCase:
    intruder_mass: float
    impact_parameter: float
    intruder_speed_y: float


@dataclass(frozen=True, slots=True)
class FlybySweepRow:
    case: FlybySweepCase
    incoming_speed: float
    encounter_adiabaticity: float
    transition_count: int
    low_crossing: float | None
    high_crossing: float | None
    low_hierarchy_ratio: float | None
    high_hierarchy_ratio: float | None
    hysteresis_width: float | None
    support: int

    def as_dict(self) -> dict[str, float | int | None]:
        return {
            "intruder_mass": self.case.intruder_mass,
            "impact_parameter": self.case.impact_parameter,
            "intruder_speed_y": self.case.intruder_speed_y,
            "incoming_speed": self.incoming_speed,
            "encounter_adiabaticity": self.encounter_adiabaticity,
            "transition_count": self.transition_count,
            "low_crossing": self.low_crossing,
            "high_crossing": self.high_crossing,
            "low_hierarchy_ratio": self.low_hierarchy_ratio,
            "high_hierarchy_ratio": self.high_hierarchy_ratio,
            "hysteresis_width": self.hysteresis_width,
            "support": self.support,
        }


@dataclass(frozen=True, slots=True)
class FlybySweepResult:
    rows: tuple[FlybySweepRow, ...]

    def as_dict(self) -> dict[str, object]:
        valid_widths = [row.hysteresis_width for row in self.rows if row.hysteresis_width is not None]
        low_crossings = [row.low_crossing for row in self.rows if row.low_crossing is not None]
        high_crossings = [row.high_crossing for row in self.rows if row.high_crossing is not None]
        return {
            "rows": [row.as_dict() for row in self.rows],
            "case_count": len(self.rows),
            "transitioning_case_count": sum(1 for row in self.rows if row.transition_count > 0),
            "mean_hysteresis_width": None if not valid_widths else float(np.mean(valid_widths)),
            "low_crossing_mean": _mean_or_none(low_crossings),
            "low_crossing_cv": _coefficient_of_variation_or_none(low_crossings),
            "high_crossing_mean": _mean_or_none(high_crossings),
            "high_crossing_cv": _coefficient_of_variation_or_none(high_crossings),
            "collapse_fits": _collapse_fit_rows(self.rows),
        }


@dataclass(slots=True)
class HierarchicalFlybySweep:
    """Parameter sweep for testing whether the hierarchy boundary scales across flybys."""

    integrator: AdaptiveIntegrator = field(default_factory=lambda: AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11))
    atlas: AnalysisAtlas = field(default_factory=AnalysisAtlas)
    library: OrbitLibrary = field(default_factory=OrbitLibrary)

    def run(
        self,
        intruder_masses: tuple[float, ...] = (0.1, 0.2, 0.4),
        impact_parameters: tuple[float, ...] = (0.0, 0.2),
        intruder_speed_y_values: tuple[float, ...] = (1.0, 1.2),
        duration: float = 8.0,
        samples: int = 600,
        stride: int = 20,
        binary_separation: float = 0.2,
    ) -> FlybySweepResult:
        rows: list[FlybySweepRow] = []
        for intruder_mass, impact_parameter, speed_y in product(
            intruder_masses,
            impact_parameters,
            intruder_speed_y_values,
        ):
            case = FlybySweepCase(intruder_mass, impact_parameter, speed_y)
            incoming_speed = float(np.hypot(0.8, speed_y))
            encounter_time = float(np.hypot(impact_parameter, 2.0) / incoming_speed)
            inner_period = orbit_period(2.0, binary_separation)
            encounter_adiabaticity = float(encounter_time / inner_period)
            scenario = self.library.general_hierarchical_flyby(
                binary_separation=binary_separation,
                intruder_mass=intruder_mass,
                intruder_position=(impact_parameter, -2.0),
                intruder_velocity=(0.8, speed_y),
                duration=duration,
                samples=samples,
            )
            trajectory = self.integrator.integrate(
                scenario.system,
                scenario.t_span,
                scenario.initial_state,
                t_eval=scenario.t_eval,
            )
            reports = self.atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
            transitions = self.atlas.transitions(scenario.system, trajectory, stride=stride)
            perturbation_boundaries = estimate_transition_boundaries(
                {"flyby": reports},
                coordinate="hierarchy_perturbation_strength",
            )
            hierarchy_boundaries = estimate_transition_boundaries({"flyby": reports}, coordinate="hierarchy_ratio")
            perturbation_loops = detect_hysteresis_loops(perturbation_boundaries)
            hierarchy_loops = detect_hysteresis_loops(hierarchy_boundaries)
            if perturbation_loops:
                perturbation_loop = perturbation_loops[0]
                hierarchy_loop = hierarchy_loops[0] if hierarchy_loops else None
                rows.append(
                    FlybySweepRow(
                        case=case,
                        incoming_speed=incoming_speed,
                        encounter_adiabaticity=encounter_adiabaticity,
                        transition_count=len(transitions),
                        low_crossing=perturbation_loop.low_crossing,
                        high_crossing=perturbation_loop.high_crossing,
                        low_hierarchy_ratio=None if hierarchy_loop is None else hierarchy_loop.low_crossing,
                        high_hierarchy_ratio=None if hierarchy_loop is None else hierarchy_loop.high_crossing,
                        hysteresis_width=perturbation_loop.width,
                        support=perturbation_loop.support,
                    )
                )
            else:
                rows.append(
                    FlybySweepRow(
                        case=case,
                        incoming_speed=incoming_speed,
                        encounter_adiabaticity=encounter_adiabaticity,
                        transition_count=len(transitions),
                        low_crossing=None,
                        high_crossing=None,
                        low_hierarchy_ratio=None,
                        high_hierarchy_ratio=None,
                        hysteresis_width=None,
                        support=0,
                    )
                )
        return FlybySweepResult(rows=tuple(rows))


def _mean_or_none(values: list[float]) -> float | None:
    return None if not values else float(np.mean(values))


def _coefficient_of_variation_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    mean = float(np.mean(values))
    if abs(mean) < 1.0e-12:
        return None
    return float(np.std(values) / abs(mean))


def _collapse_fit_rows(rows: tuple[FlybySweepRow, ...]) -> list[dict[str, float | int | str | None]]:
    fits = []
    for target_name, crossing_attr, hierarchy_attr in (
        ("low_crossing", "low_crossing", "low_hierarchy_ratio"),
        ("high_crossing", "high_crossing", "high_hierarchy_ratio"),
    ):
        target = []
        features = []
        for row in rows:
            crossing = getattr(row, crossing_attr)
            hierarchy_ratio = getattr(row, hierarchy_attr)
            if crossing is None or hierarchy_ratio is None:
                continue
            target.append(crossing)
            features.append([row.encounter_adiabaticity, hierarchy_ratio])
        fit = fit_power_law_boundary_collapse(
            np.asarray(target, dtype=float),
            np.asarray(features, dtype=float),
            feature_names=("encounter_adiabaticity", "hierarchy_ratio"),
            target_name=target_name,
        )
        fits.append(fit.rows())
    return fits
