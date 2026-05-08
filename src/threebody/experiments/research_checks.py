from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..analysis import (
    AnalysisAtlas,
    ChartClassifier,
    chart_validity_bound,
    gateway_transit_estimate,
    local_linearization,
    mcgehee_collision_diagnostic,
    reduced_three_body_state,
)
from ..diagnostics import InvariantMonitor, StabilityAnalyzer
from ..solvers import AdaptiveIntegrator, StructureAwareIntegrator
from ..systems import GeneralThreeBodySystem
from .orbit_library import OrbitLibrary
from .flyby_sweep import HierarchicalFlybySweep


@dataclass(frozen=True, slots=True)
class ClassifierArtifactRow:
    label: str
    stride: int
    hierarchy_perturbation_threshold: float
    close_encounter_radius: float
    transition_count: int
    primary_chart_count: int

    def as_dict(self) -> dict[str, float | int | str]:
        return {
            "label": self.label,
            "stride": self.stride,
            "hierarchy_perturbation_threshold": self.hierarchy_perturbation_threshold,
            "close_encounter_radius": self.close_encounter_radius,
            "transition_count": self.transition_count,
            "primary_chart_count": self.primary_chart_count,
        }


@dataclass(slots=True)
class ClassifierArtifactStudy:
    """Perturb chart-classifier thresholds to test whether transitions are artifacts."""

    library: OrbitLibrary = field(default_factory=OrbitLibrary)
    integrator: AdaptiveIntegrator = field(default_factory=lambda: AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11))

    def run(self, duration: float = 8.0, samples: int = 500) -> tuple[ClassifierArtifactRow, ...]:
        scenario = self.library.general_hierarchical_flyby(duration=duration, samples=samples)
        trajectory = self.integrator.integrate(
            scenario.system,
            scenario.t_span,
            scenario.initial_state,
            t_eval=scenario.t_eval,
        )
        rows = []
        for label, threshold_factor, close_factor, stride in (
            ("baseline", 1.0, 1.0, 20),
            ("loose_hierarchy", 2.0, 1.0, 20),
            ("strict_hierarchy", 0.5, 1.0, 20),
            ("wide_close", 1.0, 1.5, 20),
            ("fine_stride", 1.0, 1.0, 10),
            ("coarse_stride", 1.0, 1.0, 40),
        ):
            classifier = ChartClassifier(
                hierarchy_perturbation_threshold=4.0e-3 * threshold_factor,
                close_encounter_radius=0.08 * close_factor,
            )
            atlas = AnalysisAtlas(classifier=classifier)
            reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
            transitions = atlas.transitions(scenario.system, trajectory, stride=stride)
            rows.append(
                ClassifierArtifactRow(
                    label=label,
                    stride=stride,
                    hierarchy_perturbation_threshold=classifier.hierarchy_perturbation_threshold,
                    close_encounter_radius=classifier.close_encounter_radius,
                    transition_count=len(transitions),
                    primary_chart_count=len({report.primary_chart for report in reports}),
                )
            )
        return tuple(rows)


@dataclass(frozen=True, slots=True)
class GrammarBranchArtifactRow:
    label: str
    stride: int
    hierarchy_perturbation_threshold: float
    high_score: float | None
    hysteresis_score: float | None
    high_certified_accuracy: float | None
    hysteresis_certified_accuracy: float | None
    high_certified_fraction: float | None
    hysteresis_certified_fraction: float | None
    high_mean_margin: float | None
    hysteresis_mean_margin: float | None
    high_negative_control_gap: float | None
    hysteresis_negative_control_gap: float | None
    high_passed: bool
    hysteresis_passed: bool

    @property
    def minimum_score(self) -> float | None:
        scores = [score for score in (self.high_score, self.hysteresis_score) if score is not None]
        return None if not scores else float(min(scores))

    @property
    def passed(self) -> bool:
        return self.high_passed and self.hysteresis_passed

    @property
    def minimum_certified_accuracy(self) -> float | None:
        values = [
            value
            for value in (self.high_certified_accuracy, self.hysteresis_certified_accuracy)
            if value is not None
        ]
        return None if not values else float(min(values))

    @property
    def minimum_certified_fraction(self) -> float | None:
        values = [
            value
            for value in (self.high_certified_fraction, self.hysteresis_certified_fraction)
            if value is not None
        ]
        return None if not values else float(min(values))

    @property
    def minimum_mean_margin(self) -> float | None:
        values = [value for value in (self.high_mean_margin, self.hysteresis_mean_margin) if value is not None]
        return None if not values else float(min(values))

    @property
    def minimum_negative_control_gap(self) -> float | None:
        values = [
            value
            for value in (self.high_negative_control_gap, self.hysteresis_negative_control_gap)
            if value is not None
        ]
        return None if not values else float(min(values))

    def as_dict(self) -> dict[str, float | int | str | bool | None]:
        return {
            "label": self.label,
            "stride": self.stride,
            "hierarchy_perturbation_threshold": self.hierarchy_perturbation_threshold,
            "high_score": self.high_score,
            "hysteresis_score": self.hysteresis_score,
            "minimum_score": self.minimum_score,
            "high_certified_accuracy": self.high_certified_accuracy,
            "hysteresis_certified_accuracy": self.hysteresis_certified_accuracy,
            "minimum_certified_accuracy": self.minimum_certified_accuracy,
            "high_certified_fraction": self.high_certified_fraction,
            "hysteresis_certified_fraction": self.hysteresis_certified_fraction,
            "minimum_certified_fraction": self.minimum_certified_fraction,
            "high_mean_margin": self.high_mean_margin,
            "hysteresis_mean_margin": self.hysteresis_mean_margin,
            "minimum_mean_margin": self.minimum_mean_margin,
            "high_negative_control_gap": self.high_negative_control_gap,
            "hysteresis_negative_control_gap": self.hysteresis_negative_control_gap,
            "minimum_negative_control_gap": self.minimum_negative_control_gap,
            "high_passed": self.high_passed,
            "hysteresis_passed": self.hysteresis_passed,
            "passed": self.passed,
        }


@dataclass(slots=True)
class GrammarBranchArtifactStudy:
    """Perturb classifier/stride settings for the predeclared grammar branch laws."""

    def run(self, duration: float = 8.0, samples: int = 180) -> tuple[GrammarBranchArtifactRow, ...]:
        rows = []
        for label, threshold_factor, stride in (
            ("baseline", 1.0, 20),
            ("strict_hierarchy", 0.75, 20),
            ("loose_hierarchy", 1.5, 20),
            ("fine_stride", 1.0, 10),
        ):
            classifier = ChartClassifier(hierarchy_perturbation_threshold=4.0e-3 * threshold_factor)
            sweep = HierarchicalFlybySweep(atlas=AnalysisAtlas(classifier=classifier))
            result = sweep.run_discovery_validation(
                discovery_binary_phases=(0.0, 1.5707963267948966),
                validation_binary_phases=(
                    0.39269908169872414,
                    0.7853981633974483,
                    1.1780972450961724,
                    2.356194490192345,
                ),
                duration=duration,
                samples=samples,
                stride=stride,
            )
            validations = {row["target"]: row for row in result.as_dict()["grammar_outcome_validations"]}
            high = validations.get("high_crossing_grammar_scattering_branch", {})
            hysteresis = validations.get("hysteresis_width_grammar_phase_branch", {})
            rows.append(
                GrammarBranchArtifactRow(
                    label=label,
                    stride=stride,
                    hierarchy_perturbation_threshold=classifier.hierarchy_perturbation_threshold,
                    high_score=_optional_float(high.get("complexity_penalized_validation_score")),
                    hysteresis_score=_optional_float(hysteresis.get("complexity_penalized_validation_score")),
                    high_certified_accuracy=_optional_float(high.get("certified_validation_accuracy")),
                    hysteresis_certified_accuracy=_optional_float(hysteresis.get("certified_validation_accuracy")),
                    high_certified_fraction=_optional_float(high.get("certified_validation_fraction")),
                    hysteresis_certified_fraction=_optional_float(hysteresis.get("certified_validation_fraction")),
                    high_mean_margin=_optional_float(high.get("mean_decision_margin")),
                    hysteresis_mean_margin=_optional_float(hysteresis.get("mean_decision_margin")),
                    high_negative_control_gap=_optional_float(high.get("grammar_negative_control_score_gap")),
                    hysteresis_negative_control_gap=_optional_float(
                        hysteresis.get("grammar_negative_control_score_gap")
                    ),
                    high_passed=bool(high.get("passes_validation", False)),
                    hysteresis_passed=bool(hysteresis.get("passes_validation", False)),
                )
            )
        return tuple(rows)


@dataclass(frozen=True, slots=True)
class IntegratorComparisonResult:
    adaptive_energy_drift: float
    structure_energy_drift: float
    endpoint_separation: float
    regularized_available: bool
    warning: str

    def as_dict(self) -> dict[str, float | bool | str]:
        return {
            "adaptive_energy_drift": self.adaptive_energy_drift,
            "structure_energy_drift": self.structure_energy_drift,
            "endpoint_separation": self.endpoint_separation,
            "regularized_available": self.regularized_available,
            "warning": self.warning,
        }


@dataclass(slots=True)
class IntegratorComparisonStudy:
    """Compare adaptive DOP853 against the current structure-aware Verlet integrator."""

    library: OrbitLibrary = field(default_factory=OrbitLibrary)

    def run(self, periods: float = 0.25, step_size: float = 2.0e-3) -> IntegratorComparisonResult:
        scenario = self.library.general_figure_eight(periods=periods, samples=800)
        structure = StructureAwareIntegrator(step_size=step_size)
        structure_trajectory = structure.integrate(scenario.system, scenario.t_span, scenario.initial_state)
        adaptive = AdaptiveIntegrator(rtol=1.0e-10, atol=1.0e-12).integrate(
            scenario.system,
            scenario.t_span,
            scenario.initial_state,
            t_eval=structure_trajectory.t,
        )
        adaptive_drift = _max_abs_drift(scenario.system, adaptive)
        structure_drift = _max_abs_drift(scenario.system, structure_trajectory)
        endpoint_separation = float(np.linalg.norm(adaptive.y[-1] - structure_trajectory.y[-1]))
        return IntegratorComparisonResult(
            adaptive_energy_drift=adaptive_drift,
            structure_energy_drift=structure_drift,
            endpoint_separation=endpoint_separation,
            regularized_available=False,
            warning="No true collision-regularized integrator is implemented yet; close-encounter laws remain provisional.",
        )


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    name: str
    metric: str
    observed: float
    reference: float
    absolute_error: float
    passed: bool

    def as_dict(self) -> dict[str, float | bool | str]:
        return {
            "name": self.name,
            "metric": self.metric,
            "observed": self.observed,
            "reference": self.reference,
            "absolute_error": self.absolute_error,
            "passed": self.passed,
        }


@dataclass(slots=True)
class KnownBenchmarkSuite:
    library: OrbitLibrary = field(default_factory=OrbitLibrary)
    integrator: AdaptiveIntegrator = field(default_factory=lambda: AdaptiveIntegrator(rtol=1.0e-10, atol=1.0e-12))

    def run(self) -> tuple[BenchmarkResult, ...]:
        restricted = self.library.restricted_l4(samples=20)
        lagrange = restricted.system.lagrange_points()
        l4_reference = np.array([0.5 - restricted.system.mass_ratio, np.sqrt(3.0) / 2.0])
        l5_reference = np.array([0.5 - restricted.system.mass_ratio, -np.sqrt(3.0) / 2.0])
        figure = self.library.general_figure_eight(periods=1.0, samples=1200)
        trajectory = self.integrator.integrate(figure.system, figure.t_span, figure.initial_state, t_eval=figure.t_eval)
        return (
            _benchmark("restricted_l4", "position_error", float(np.linalg.norm(lagrange["L4"] - l4_reference)), 0.0, 1.0e-12),
            _benchmark("restricted_l5", "position_error", float(np.linalg.norm(lagrange["L5"] - l5_reference)), 0.0, 1.0e-12),
            _benchmark("figure_eight_return", "state_return_error", float(np.linalg.norm(trajectory.y[-1] - trajectory.y[0])), 0.0, 5.0e-3),
        )


@dataclass(frozen=True, slots=True)
class RegimeProbeResult:
    name: str
    primary_chart: str
    confidence: float
    validity_statement: str
    diagnostic: float | None
    extra: dict[str, float | str | bool] = field(default_factory=dict)

    def as_dict(self) -> dict[str, float | str | None]:
        row = {
            "name": self.name,
            "primary_chart": self.primary_chart,
            "confidence": self.confidence,
            "validity_statement": self.validity_statement,
            "diagnostic": self.diagnostic,
        }
        row.update(self.extra)
        return row


@dataclass(slots=True)
class RegimeProbeSuite:
    library: OrbitLibrary = field(default_factory=OrbitLibrary)

    def run(self) -> tuple[RegimeProbeResult, ...]:
        probes = []
        restricted = self.library.restricted_l4(perturbation=(0.0, 0.0, 0.0, 0.0), samples=20)
        probes.append(("restricted_lagrange", restricted.system, restricted.initial_state))

        gateway_system = self.library.restricted_l4(samples=20).system
        l1 = gateway_system.lagrange_points()["L1"]
        probes.append(("lagrange_neck", gateway_system, np.array([l1[0] + 0.01, 0.0, 0.0, 0.08], dtype=float)))

        close_system = GeneralThreeBodySystem(masses=(1.0, 1.0, 1.0), dimension=2)
        close_state = close_system.flatten_state(
            np.array([[0.0, 0.0], [0.005, 0.0], [0.02, 0.0]], dtype=float),
            np.zeros((3, 2), dtype=float),
        )
        probes.append(("shape_close_encounter", close_system, close_state))

        escape_system = GeneralThreeBodySystem(masses=(1.0, 1.0, 1.0), dimension=2)
        escape_state = escape_system.flatten_state(
            np.array([[-10.0, 0.0], [10.0, 0.0], [0.0, 10.0]], dtype=float),
            np.array([[4.0, 0.0], [-4.0, 0.0], [0.0, 4.0]], dtype=float),
        )
        probes.append(("escape_scattering", escape_system, escape_state))

        atlas = AnalysisAtlas()
        rows = []
        for name, system, state in probes:
            report = atlas.analyze_state(system, state)
            bound = chart_validity_bound(report)
            extra: dict[str, float | str | bool] = {}
            if hasattr(system, "mass_ratio") and "neck" in name:
                gateway = gateway_transit_estimate(system, state)
                extra.update({f"gateway_{key}": value for key, value in gateway.as_dict().items()})
            elif getattr(system, "body_count", None) == 3:
                reduced = reduced_three_body_state(system, state)
                collision = mcgehee_collision_diagnostic(system, state)
                extra.update(
                    {
                        "reduced_hyperradius": reduced.hyperradius,
                        "reduced_shape_area": reduced.shape_area,
                        "reduced_regime_hint": reduced.reduced_regime_hint,
                    }
                )
                extra.update({f"collision_{key}": value for key, value in collision.as_dict().items()})
            rows.append(
                RegimeProbeResult(
                    name=name,
                    primary_chart=report.primary_chart.value,
                    confidence=report.confidence,
                    validity_statement=bound.statement,
                    diagnostic=bound.observed_value,
                    extra=extra,
                )
            )
        return tuple(rows)


@dataclass(frozen=True, slots=True)
class FigureEightStabilityResult:
    finite_time_lyapunov: float
    classification: str
    spectral_radius: float

    def as_dict(self) -> dict[str, float | str]:
        return {
            "finite_time_lyapunov": self.finite_time_lyapunov,
            "classification": self.classification,
            "spectral_radius": self.spectral_radius,
        }


@dataclass(slots=True)
class FigureEightStabilityProbe:
    library: OrbitLibrary = field(default_factory=OrbitLibrary)
    integrator: AdaptiveIntegrator = field(default_factory=lambda: AdaptiveIntegrator(rtol=1.0e-10, atol=1.0e-12))

    def run(self, periods: float = 0.5, perturbation_scale: float = 1.0e-6) -> FigureEightStabilityResult:
        reference = self.library.general_figure_eight(periods=periods, samples=900)
        perturbed = self.library.general_figure_eight(
            periods=periods,
            samples=900,
            perturbation_scale=perturbation_scale,
        )
        reference_trajectory = self.integrator.integrate(
            reference.system,
            reference.t_span,
            reference.initial_state,
            t_eval=reference.t_eval,
        )
        perturbed_trajectory = self.integrator.integrate(
            perturbed.system,
            perturbed.t_span,
            perturbed.initial_state,
            t_eval=reference.t_eval,
        )
        stability = StabilityAnalyzer().finite_time_lyapunov(reference_trajectory, perturbed_trajectory)
        linearization = local_linearization(reference.system, reference.initial_state)
        return FigureEightStabilityResult(
            finite_time_lyapunov=float(stability["finite_time_lyapunov"]),
            classification=str(stability["classification"]),
            spectral_radius=linearization.spectral_radius,
        )


def _max_abs_drift(system: object, trajectory: object) -> float:
    values = InvariantMonitor(system).evaluate(trajectory)
    drift = values.get("energy_drift")
    if drift is None:
        drift = values.get("jacobi_drift")
    return float(np.max(np.abs(drift)))


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _benchmark(name: str, metric: str, observed_error: float, reference: float, tolerance: float) -> BenchmarkResult:
    return BenchmarkResult(
        name=name,
        metric=metric,
        observed=observed_error,
        reference=reference,
        absolute_error=abs(observed_error - reference),
        passed=abs(observed_error - reference) <= tolerance,
    )
