from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from math import pi

import numpy as np

from ..analysis import (
    AnalysisAtlas,
    detect_hysteresis_loops,
    encounter_exchange_metrics,
    estimate_transition_boundaries,
    fit_power_law_boundary_collapse,
    periapsis_scattering_map,
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
    binary_phase: float = 0.0


@dataclass(frozen=True, slots=True)
class FlybySweepRow:
    case: FlybySweepCase
    incoming_speed: float
    encounter_adiabaticity: float
    relative_inner_energy_exchange: float
    relative_angular_momentum_exchange: float
    tidal_impulse: float
    phase_alignment: float
    phase_quadrature: float
    nonlinear_tidal_exposure: float
    periapsis_time: float
    periapsis_distance: float
    binary_phase_at_periapsis: float
    binary_phase_cos_positive: float
    binary_phase_sin_positive: float
    outer_energy_delta: float
    outer_angular_momentum_delta: float
    outgoing_semimajor_axis: float
    outgoing_eccentricity: float
    outgoing_periapsis_distance: float
    outgoing_escape_speed_at_infinity: float
    deflection_angle: float
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
            "binary_phase": self.case.binary_phase,
            "incoming_speed": self.incoming_speed,
            "encounter_adiabaticity": self.encounter_adiabaticity,
            "relative_inner_energy_exchange": self.relative_inner_energy_exchange,
            "relative_angular_momentum_exchange": self.relative_angular_momentum_exchange,
            "tidal_impulse": self.tidal_impulse,
            "phase_alignment": self.phase_alignment,
            "phase_quadrature": self.phase_quadrature,
            "nonlinear_tidal_exposure": self.nonlinear_tidal_exposure,
            "periapsis_time": self.periapsis_time,
            "periapsis_distance": self.periapsis_distance,
            "binary_phase_at_periapsis": self.binary_phase_at_periapsis,
            "binary_phase_cos_positive": self.binary_phase_cos_positive,
            "binary_phase_sin_positive": self.binary_phase_sin_positive,
            "outer_energy_delta": self.outer_energy_delta,
            "outer_angular_momentum_delta": self.outer_angular_momentum_delta,
            "outgoing_semimajor_axis": self.outgoing_semimajor_axis,
            "outgoing_eccentricity": self.outgoing_eccentricity,
            "outgoing_periapsis_distance": self.outgoing_periapsis_distance,
            "outgoing_escape_speed_at_infinity": self.outgoing_escape_speed_at_infinity,
            "deflection_angle": self.deflection_angle,
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
            "model_selection": _model_selection_rows(self.rows),
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
            "worst_validation_residuals": _collapse_residual_rows(self.discovery.rows, self.validation.rows),
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
        binary_phases: tuple[float, ...] = (0.0,),
        duration: float = 8.0,
        samples: int = 600,
        stride: int = 20,
        binary_separation: float = 0.2,
    ) -> FlybySweepResult:
        rows: list[FlybySweepRow] = []
        for intruder_mass, impact_parameter, speed_y, binary_phase in product(
            intruder_masses,
            impact_parameters,
            intruder_speed_y_values,
            binary_phases,
        ):
            case = FlybySweepCase(intruder_mass, impact_parameter, speed_y, binary_phase)
            incoming_speed = float(np.hypot(0.8, speed_y))
            encounter_time = float(np.hypot(impact_parameter, 2.0) / incoming_speed)
            inner_period = orbit_period(2.0, binary_separation)
            encounter_adiabaticity = float(encounter_time / inner_period)
            phase_alignment, phase_quadrature = _phase_features(binary_phase, encounter_adiabaticity)
            scenario = self.library.general_hierarchical_flyby(
                binary_separation=binary_separation,
                binary_phase=binary_phase,
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
            scattering = periapsis_scattering_map(scenario.system, trajectory, inner_pair=(0, 1))
            nonlinear_tidal_exposure = float(exchange.tidal_impulse * encounter_adiabaticity)
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
                        phase_alignment=phase_alignment,
                        phase_quadrature=phase_quadrature,
                        nonlinear_tidal_exposure=nonlinear_tidal_exposure,
                        periapsis_time=scattering.periapsis_time,
                        periapsis_distance=scattering.periapsis_distance,
                        binary_phase_at_periapsis=scattering.binary_phase_at_periapsis,
                        binary_phase_cos_positive=scattering.binary_phase_cos_positive,
                        binary_phase_sin_positive=scattering.binary_phase_sin_positive,
                        outer_energy_delta=scattering.outer_energy_delta,
                        outer_angular_momentum_delta=scattering.outer_angular_momentum_delta,
                        outgoing_semimajor_axis=scattering.outgoing_semimajor_axis,
                        outgoing_eccentricity=scattering.outgoing_eccentricity,
                        outgoing_periapsis_distance=scattering.outgoing_periapsis_distance,
                        outgoing_escape_speed_at_infinity=scattering.outgoing_escape_speed_at_infinity,
                        deflection_angle=scattering.deflection_angle,
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
                        phase_alignment=phase_alignment,
                        phase_quadrature=phase_quadrature,
                        nonlinear_tidal_exposure=nonlinear_tidal_exposure,
                        periapsis_time=scattering.periapsis_time,
                        periapsis_distance=scattering.periapsis_distance,
                        binary_phase_at_periapsis=scattering.binary_phase_at_periapsis,
                        binary_phase_cos_positive=scattering.binary_phase_cos_positive,
                        binary_phase_sin_positive=scattering.binary_phase_sin_positive,
                        outer_energy_delta=scattering.outer_energy_delta,
                        outer_angular_momentum_delta=scattering.outer_angular_momentum_delta,
                        outgoing_semimajor_axis=scattering.outgoing_semimajor_axis,
                        outgoing_eccentricity=scattering.outgoing_eccentricity,
                        outgoing_periapsis_distance=scattering.outgoing_periapsis_distance,
                        outgoing_escape_speed_at_infinity=scattering.outgoing_escape_speed_at_infinity,
                        deflection_angle=scattering.deflection_angle,
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
        discovery_binary_phases: tuple[float, ...] = (0.0,),
        validation_binary_phases: tuple[float, ...] = (0.0,),
        duration: float = 8.0,
        samples: int = 600,
        stride: int = 20,
        binary_separation: float = 0.2,
    ) -> FlybySweepValidationResult:
        discovery = self.run(
            intruder_masses=discovery_intruder_masses,
            impact_parameters=discovery_impact_parameters,
            intruder_speed_y_values=discovery_intruder_speed_y_values,
            binary_phases=discovery_binary_phases,
            duration=duration,
            samples=samples,
            stride=stride,
            binary_separation=binary_separation,
        )
        validation = self.run(
            intruder_masses=validation_intruder_masses,
            impact_parameters=validation_impact_parameters,
            intruder_speed_y_values=validation_intruder_speed_y_values,
            binary_phases=validation_binary_phases,
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


def _model_selection_rows(
    rows: tuple[FlybySweepRow, ...],
    bootstrap_replicates: int = 32,
) -> list[dict[str, float | int | str | None]]:
    diagnostics = []
    for spec in _collapse_specs(rows):
        target, features = _target_and_features(rows, spec)
        fit = fit_power_law_boundary_collapse(
            target,
            features,
            feature_names=spec["feature_names"],
            target_name=spec["target_name"],
        )
        diagnostics.append(
            {
                "target": str(spec["target_name"]),
                "feature_count": len(spec["feature_names"]),
                "support": fit.support,
                "aic": fit.aic,
                "bic": fit.bic,
                "log_feature_condition_number": _log_feature_condition_number(features),
                "max_abs_log_feature_correlation": _max_abs_log_feature_correlation(features),
                "loo_log_rmse": _leave_one_out_log_rmse(target, features, spec),
                "bootstrap_oob_log_rmse_mean": _bootstrap_oob_log_rmse(target, features, spec, bootstrap_replicates),
            }
        )
    return diagnostics


def _log_feature_condition_number(features: np.ndarray) -> float | None:
    features = np.atleast_2d(np.asarray(features, dtype=float))
    if features.size == 0 or features.shape[0] < 2:
        return None
    log_features = np.log(np.maximum(features, 1.0e-300))
    centered = log_features - np.mean(log_features, axis=0)
    if np.allclose(centered, 0.0):
        return None
    return float(np.linalg.cond(centered))


def _max_abs_log_feature_correlation(features: np.ndarray) -> float | None:
    features = np.atleast_2d(np.asarray(features, dtype=float))
    if features.size == 0 or features.shape[1] < 2 or features.shape[0] < 3:
        return None
    log_features = np.log(np.maximum(features, 1.0e-300))
    correlation = np.corrcoef(log_features, rowvar=False)
    if not np.all(np.isfinite(correlation)):
        return None
    mask = ~np.eye(correlation.shape[0], dtype=bool)
    return float(np.max(np.abs(correlation[mask])))


def _leave_one_out_log_rmse(target: np.ndarray, features: np.ndarray, spec: dict[str, object]) -> float | None:
    target = np.asarray(target, dtype=float)
    features = np.atleast_2d(np.asarray(features, dtype=float))
    if target.size < len(spec["feature_names"]) + 3:
        return None
    residuals = []
    for holdout in range(target.size):
        train_mask = np.ones(target.size, dtype=bool)
        train_mask[holdout] = False
        fit = fit_power_law_boundary_collapse(
            target[train_mask],
            features[train_mask],
            feature_names=spec["feature_names"],
            target_name=str(spec["target_name"]),
        )
        if fit.support < len(spec["feature_names"]) + 1:
            continue
        prediction = float(fit.predict(features[holdout])[0])
        residuals.append(np.log(target[holdout]) - np.log(max(prediction, 1.0e-300)))
    if not residuals:
        return None
    return float(np.sqrt(np.mean(np.asarray(residuals, dtype=float) ** 2)))


def _bootstrap_oob_log_rmse(
    target: np.ndarray,
    features: np.ndarray,
    spec: dict[str, object],
    replicates: int,
) -> float | None:
    target = np.asarray(target, dtype=float)
    features = np.atleast_2d(np.asarray(features, dtype=float))
    if target.size < len(spec["feature_names"]) + 3:
        return None
    rng = np.random.default_rng(20260507)
    rmses = []
    for _replicate in range(replicates):
        sample = rng.integers(0, target.size, size=target.size)
        oob_mask = np.ones(target.size, dtype=bool)
        oob_mask[np.unique(sample)] = False
        if not np.any(oob_mask):
            continue
        fit = fit_power_law_boundary_collapse(
            target[sample],
            features[sample],
            feature_names=spec["feature_names"],
            target_name=str(spec["target_name"]),
        )
        if fit.support < len(spec["feature_names"]) + 1:
            continue
        predictions = fit.predict(features[oob_mask])
        residuals = np.log(target[oob_mask]) - np.log(np.maximum(predictions, 1.0e-300))
        rmses.append(float(np.sqrt(np.mean(residuals**2))))
    return None if not rmses else float(np.mean(rmses))


def _collapse_fits(rows: tuple[FlybySweepRow, ...]):
    fits = []
    for spec in _collapse_specs(rows):
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
    specs = _collapse_specs(discovery_rows)
    for spec, fit in zip(specs, _collapse_fits(discovery_rows), strict=True):
        target, features = _target_and_features(validation_rows, spec)
        validation = validate_power_law_boundary_collapse(fit, target, features)
        rows.append(validation.rows())
    return rows


def _collapse_residual_rows(
    discovery_rows: tuple[FlybySweepRow, ...],
    validation_rows: tuple[FlybySweepRow, ...],
    max_per_model: int = 3,
) -> list[dict[str, float | int | str]]:
    rows = []
    specs = _collapse_specs(discovery_rows)
    for spec, fit in zip(specs, _collapse_fits(discovery_rows), strict=True):
        target, features, source_rows = _target_features_and_rows(validation_rows, spec)
        if target.size == 0 or features.size == 0:
            continue
        predictions = fit.predict(features)
        for observed, predicted, source in zip(target, predictions, source_rows, strict=True):
            ratio = float(observed / max(float(predicted), 1.0e-300))
            rows.append(
                {
                    "target": str(spec["target_name"]),
                    "intruder_mass": source.case.intruder_mass,
                    "impact_parameter": source.case.impact_parameter,
                    "intruder_speed_y": source.case.intruder_speed_y,
                    "binary_phase": source.case.binary_phase,
                    "observed": float(observed),
                    "predicted": float(predicted),
                    "ratio": ratio,
                    "abs_log_error": float(abs(np.log(max(ratio, 1.0e-300)))),
                }
            )
    selected = []
    for target in sorted({row["target"] for row in rows}):
        target_rows = [row for row in rows if row["target"] == target]
        selected.extend(sorted(target_rows, key=lambda row: float(row["abs_log_error"]), reverse=True)[:max_per_model])
    return selected


def _best_validation_rows(
    rows: tuple[dict[str, float | int | str | bool | None], ...],
) -> list[dict[str, float | int | str | bool | None]]:
    best_by_family: dict[str, dict[str, float | int | str | bool | None]] = {}
    for row in rows:
        target = str(row["target"])
        family = _target_family(target)
        score = row.get("complexity_penalized_validation_score")
        if score is None:
            continue
        current = best_by_family.get(family)
        current_score = None if current is None else current.get("complexity_penalized_validation_score")
        if current is None or float(score) > float(current_score or -np.inf):
            best_by_family[family] = row
    return [best_by_family[key] for key in sorted(best_by_family)]


def _target_family(target: str) -> str:
    if target.startswith("low_"):
        return "low"
    if target.startswith("high_"):
        return "high"
    if target.startswith("hysteresis_"):
        return "hysteresis"
    return target.split("_", maxsplit=1)[0]


def _collapse_specs(rows: tuple[FlybySweepRow, ...] | None = None) -> tuple[dict[str, object], ...]:
    specs = []
    include_phase = _has_phase_diversity(rows)
    for prefix, crossing_attr, hierarchy_attr in (
        ("low_crossing", "low_crossing", "low_hierarchy_ratio"),
        ("high_crossing", "high_crossing", "high_hierarchy_ratio"),
        ("hysteresis_width", "hysteresis_width", "high_hierarchy_ratio"),
    ):
        base_specs = [
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
            {
                "target_name": f"{prefix}_nonlinear_cumulative",
                "crossing_attr": crossing_attr,
                "hierarchy_attr": hierarchy_attr,
                "feature_names": (
                    "encounter_adiabaticity",
                    "hierarchy_ratio",
                    "relative_inner_energy_exchange",
                    "relative_angular_momentum_exchange",
                    "tidal_impulse",
                    "nonlinear_tidal_exposure",
                ),
            },
        ]
        if include_phase:
            base_specs.extend(
                [
                    {
                        "target_name": f"{prefix}_phase_cumulative",
                        "crossing_attr": crossing_attr,
                        "hierarchy_attr": hierarchy_attr,
                        "feature_names": (
                            "encounter_adiabaticity",
                            "hierarchy_ratio",
                            "relative_inner_energy_exchange",
                            "relative_angular_momentum_exchange",
                            "tidal_impulse",
                            "binary_phase_cos_positive",
                            "binary_phase_sin_positive",
                        ),
                    },
                    {
                        "target_name": f"{prefix}_phase_nonlinear",
                        "crossing_attr": crossing_attr,
                        "hierarchy_attr": hierarchy_attr,
                        "feature_names": (
                            "encounter_adiabaticity",
                            "hierarchy_ratio",
                            "relative_inner_energy_exchange",
                            "relative_angular_momentum_exchange",
                            "tidal_impulse",
                            "binary_phase_cos_positive",
                            "binary_phase_sin_positive",
                            "nonlinear_tidal_exposure",
                        ),
                    },
                    {
                        "target_name": f"{prefix}_scattering_map",
                        "crossing_attr": crossing_attr,
                        "hierarchy_attr": hierarchy_attr,
                        "feature_names": (
                            "encounter_adiabaticity",
                            "hierarchy_ratio",
                            "tidal_impulse",
                            "binary_phase_cos_positive",
                            "binary_phase_sin_positive",
                            "periapsis_distance",
                            "deflection_angle",
                        ),
                    },
                ]
            )
        specs.extend(base_specs)
    return tuple(specs)


def _target_and_features(rows: tuple[FlybySweepRow, ...], spec: dict[str, object]) -> tuple[np.ndarray, np.ndarray]:
    target, features, _source_rows = _target_features_and_rows(rows, spec)
    return target, features


def _target_features_and_rows(
    rows: tuple[FlybySweepRow, ...],
    spec: dict[str, object],
) -> tuple[np.ndarray, np.ndarray, tuple[FlybySweepRow, ...]]:
    target = []
    features = []
    source_rows = []
    for row in rows:
        crossing = getattr(row, str(spec["crossing_attr"]))
        hierarchy_ratio = getattr(row, str(spec["hierarchy_attr"]))
        if crossing is None or hierarchy_ratio is None:
            continue
        target.append(crossing)
        vector = [_feature_value(row, hierarchy_ratio, name) for name in spec["feature_names"]]
        features.append(vector)
        source_rows.append(row)
    return np.asarray(target, dtype=float), np.asarray(features, dtype=float), tuple(source_rows)


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
    if name == "phase_alignment":
        return max(row.phase_alignment, 1.0e-12)
    if name == "phase_quadrature":
        return max(row.phase_quadrature, 1.0e-12)
    if name == "nonlinear_tidal_exposure":
        return max(row.nonlinear_tidal_exposure, 1.0e-12)
    if name == "periapsis_distance":
        return max(row.periapsis_distance, 1.0e-12)
    if name == "binary_phase_cos_positive":
        return max(row.binary_phase_cos_positive, 1.0e-12)
    if name == "binary_phase_sin_positive":
        return max(row.binary_phase_sin_positive, 1.0e-12)
    if name == "outer_energy_delta":
        return max(abs(row.outer_energy_delta), 1.0e-12)
    if name == "outer_angular_momentum_delta":
        return max(abs(row.outer_angular_momentum_delta), 1.0e-12)
    if name == "deflection_angle":
        return max(row.deflection_angle, 1.0e-12)
    raise ValueError(f"Unknown collapse feature: {name}")


def _phase_features(binary_phase: float, encounter_adiabaticity: float) -> tuple[float, float]:
    encounter_phase = binary_phase + 2.0 * pi * encounter_adiabaticity
    return 1.0 + abs(float(np.cos(encounter_phase))), 1.0 + abs(float(np.sin(encounter_phase)))


def _has_phase_diversity(rows: tuple[FlybySweepRow, ...] | None) -> bool:
    if rows is None:
        return False
    phases = np.asarray([row.case.binary_phase for row in rows], dtype=float)
    return bool(phases.size > 1 and np.ptp(phases) > 1.0e-12)
