from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

import numpy as np

from ..analysis import (
    AnalysisAtlas,
    detect_hysteresis_loops,
    encounter_exchange_metrics,
    estimate_transition_boundaries,
    fit_power_law_boundary_collapse,
    validate_power_law_boundary_collapse,
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
    relative_inner_energy_exchange: float
    relative_angular_momentum_exchange: float
    tidal_impulse: float
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
            "relative_inner_energy_exchange": self.relative_inner_energy_exchange,
            "relative_angular_momentum_exchange": self.relative_angular_momentum_exchange,
            "tidal_impulse": self.tidal_impulse,
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


@dataclass(frozen=True, slots=True)
class FlybySweepValidationResult:
    discovery: FlybySweepResult
    validation: FlybySweepResult
    collapse_validations: tuple[dict[str, float | int | str | bool | None], ...]

    def as_dict(self) -> dict[str, object]:
        best = _best_validation_rows(self.collapse_validations)
        return {
            "discovery": self.discovery.as_dict(),
            "validation": self.validation.as_dict(),
            "collapse_validations": list(self.collapse_validations),
            "best_validation_models": best,
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
            exchange = encounter_exchange_metrics(scenario.system, trajectory, inner_pair=(0, 1))
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
                        relative_inner_energy_exchange=exchange.relative_inner_energy_exchange,
                        relative_angular_momentum_exchange=exchange.relative_angular_momentum_exchange,
                        tidal_impulse=exchange.tidal_impulse,
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
                        relative_inner_energy_exchange=exchange.relative_inner_energy_exchange,
                        relative_angular_momentum_exchange=exchange.relative_angular_momentum_exchange,
                        tidal_impulse=exchange.tidal_impulse,
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

    def run_discovery_validation(
        self,
        discovery_intruder_masses: tuple[float, ...] = (0.1, 0.2, 0.4),
        discovery_impact_parameters: tuple[float, ...] = (0.0, 0.2),
        discovery_intruder_speed_y_values: tuple[float, ...] = (1.0, 1.2),
        validation_intruder_masses: tuple[float, ...] = (0.15, 0.3, 0.5),
        validation_impact_parameters: tuple[float, ...] = (0.1, 0.3),
        validation_intruder_speed_y_values: tuple[float, ...] = (1.1, 1.3),
        duration: float = 8.0,
        samples: int = 600,
        stride: int = 20,
        binary_separation: float = 0.2,
    ) -> FlybySweepValidationResult:
        discovery = self.run(
            intruder_masses=discovery_intruder_masses,
            impact_parameters=discovery_impact_parameters,
            intruder_speed_y_values=discovery_intruder_speed_y_values,
            duration=duration,
            samples=samples,
            stride=stride,
            binary_separation=binary_separation,
        )
        validation = self.run(
            intruder_masses=validation_intruder_masses,
            impact_parameters=validation_impact_parameters,
            intruder_speed_y_values=validation_intruder_speed_y_values,
            duration=duration,
            samples=samples,
            stride=stride,
            binary_separation=binary_separation,
        )
        collapse_validations = _collapse_validation_rows(discovery.rows, validation.rows)
        return FlybySweepValidationResult(
            discovery=discovery,
            validation=validation,
            collapse_validations=tuple(collapse_validations),
        )


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
    return [fit.rows() for fit in _collapse_fits(rows)]


def _collapse_fits(rows: tuple[FlybySweepRow, ...]):
    fits = []
    for spec in _collapse_specs():
        target, features = _target_and_features(rows, spec)
        fit = fit_power_law_boundary_collapse(
            target,
            features,
            feature_names=spec["feature_names"],
            target_name=spec["target_name"],
        )
        fits.append(fit)
    return fits


def _collapse_validation_rows(
    discovery_rows: tuple[FlybySweepRow, ...],
    validation_rows: tuple[FlybySweepRow, ...],
) -> list[dict[str, float | int | str | bool | None]]:
    rows = []
    for spec, fit in zip(_collapse_specs(), _collapse_fits(discovery_rows), strict=True):
        target, features = _target_and_features(validation_rows, spec)
        validation = validate_power_law_boundary_collapse(fit, target, features)
        rows.append(validation.rows())
    return rows


def _best_validation_rows(
    rows: tuple[dict[str, float | int | str | bool | None], ...],
) -> list[dict[str, float | int | str | bool | None]]:
    best_by_direction: dict[str, dict[str, float | int | str | bool | None]] = {}
    for row in rows:
        target = str(row["target"])
        direction = "low" if target.startswith("low_") else "high"
        improvement = row.get("validation_improvement")
        if improvement is None:
            continue
        current = best_by_direction.get(direction)
        if current is None or float(improvement) > float(current.get("validation_improvement") or -np.inf):
            best_by_direction[direction] = row
    return [best_by_direction[key] for key in sorted(best_by_direction)]


def _collapse_specs() -> tuple[dict[str, object], ...]:
    specs = []
    for prefix, crossing_attr, hierarchy_attr in (
        ("low_crossing", "low_crossing", "low_hierarchy_ratio"),
        ("high_crossing", "high_crossing", "high_hierarchy_ratio"),
    ):
        specs.extend(
            [
                {
                    "target_name": f"{prefix}_instantaneous",
                    "crossing_attr": crossing_attr,
                    "hierarchy_attr": hierarchy_attr,
                    "feature_names": ("encounter_adiabaticity", "hierarchy_ratio"),
                },
                {
                    "target_name": f"{prefix}_impulse",
                    "crossing_attr": crossing_attr,
                    "hierarchy_attr": hierarchy_attr,
                    "feature_names": ("encounter_adiabaticity", "hierarchy_ratio", "tidal_impulse"),
                },
                {
                    "target_name": f"{prefix}_exchange",
                    "crossing_attr": crossing_attr,
                    "hierarchy_attr": hierarchy_attr,
                    "feature_names": (
                        "encounter_adiabaticity",
                        "hierarchy_ratio",
                        "relative_inner_energy_exchange",
                        "relative_angular_momentum_exchange",
                    ),
                },
                {
                    "target_name": f"{prefix}_cumulative",
                    "crossing_attr": crossing_attr,
                    "hierarchy_attr": hierarchy_attr,
                    "feature_names": (
                        "encounter_adiabaticity",
                        "hierarchy_ratio",
                        "relative_inner_energy_exchange",
                        "relative_angular_momentum_exchange",
                        "tidal_impulse",
                    ),
                },
            ]
        )
    return tuple(specs)


def _target_and_features(rows: tuple[FlybySweepRow, ...], spec: dict[str, object]) -> tuple[np.ndarray, np.ndarray]:
    target = []
    features = []
    for row in rows:
        crossing = getattr(row, str(spec["crossing_attr"]))
        hierarchy_ratio = getattr(row, str(spec["hierarchy_attr"]))
        if crossing is None or hierarchy_ratio is None:
            continue
        target.append(crossing)
        vector = [_feature_value(row, hierarchy_ratio, name) for name in spec["feature_names"]]
        features.append(vector)
    return np.asarray(target, dtype=float), np.asarray(features, dtype=float)


def _feature_value(row: FlybySweepRow, hierarchy_ratio: float, name: str) -> float:
    if name == "encounter_adiabaticity":
        return row.encounter_adiabaticity
    if name == "hierarchy_ratio":
        return hierarchy_ratio
    if name == "relative_inner_energy_exchange":
        return max(row.relative_inner_energy_exchange, 1.0e-12)
    if name == "relative_angular_momentum_exchange":
        return max(row.relative_angular_momentum_exchange, 1.0e-12)
    if name == "tidal_impulse":
        return max(row.tidal_impulse, 1.0e-12)
    raise ValueError(f"Unknown collapse feature: {name}")
