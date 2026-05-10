from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..analysis import (
    AnalysisAtlas,
    ChartClassifier,
    ThreeBodyInterpreter,
    chart_validity_bound,
    gateway_transit_estimate,
    levi_civita_equivalence_certificate,
    levi_civita_flow_certificate,
    local_linearization,
    mcgehee_collision_diagnostic,
    reduced_three_body_state,
)
from ..diagnostics import InvariantMonitor, StabilityAnalyzer
from ..solvers import AdaptiveIntegrator, StructureAwareIntegrator
from ..systems import GeneralThreeBodySystem
from ..types import TrajectoryResult
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
class InterpretationSuiteRow:
    name: str
    segment_count: int
    transition_count: int
    regime_status: str
    local_interpretation_available: bool
    theorem_ready: bool
    chart_types: tuple[str, ...]
    resolved_obligation_count: int
    blocker_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "segment_count": self.segment_count,
            "transition_count": self.transition_count,
            "regime_status": self.regime_status,
            "local_interpretation_available": self.local_interpretation_available,
            "theorem_ready": self.theorem_ready,
            "chart_types": list(self.chart_types),
            "resolved_obligation_count": self.resolved_obligation_count,
            "blocker_count": self.blocker_count,
        }


@dataclass(frozen=True, slots=True)
class InterpretationSuiteResult:
    rows: tuple[InterpretationSuiteRow, ...]
    covered_chart_types: tuple[str, ...]
    unresolved_blockers: tuple[str, ...]
    resolved_obligations: tuple[str, ...]

    @property
    def local_interpretation_rate(self) -> float:
        if not self.rows:
            return 0.0
        return float(sum(row.local_interpretation_available for row in self.rows) / len(self.rows))

    def as_dict(self) -> dict[str, object]:
        return {
            "rows": [row.as_dict() for row in self.rows],
            "covered_chart_types": list(self.covered_chart_types),
            "unresolved_blockers": list(self.unresolved_blockers),
            "resolved_obligations": list(self.resolved_obligations),
            "local_interpretation_rate": self.local_interpretation_rate,
        }


@dataclass(slots=True)
class InterpretationSuite:
    """Run representative regimes through the chart-local interpretation certificate pipeline."""

    library: OrbitLibrary = field(default_factory=OrbitLibrary)
    integrator: AdaptiveIntegrator = field(default_factory=lambda: AdaptiveIntegrator(rtol=1.0e-8, atol=1.0e-10))
    interpreter: ThreeBodyInterpreter = field(default_factory=ThreeBodyInterpreter)

    def run(self) -> InterpretationSuiteResult:
        scenarios = (
            ("hierarchical_flyby", *self._hierarchical_flyby()),
            ("restricted_l4", *self._restricted_l4()),
            ("escape_scattering", *self._escape_scattering()),
            ("close_encounter", *self._close_encounter()),
        )
        rows = []
        covered: list[str] = []
        blockers: list[str] = []
        resolved: list[str] = []
        for name, system, trajectory, stride in scenarios:
            interpretation = self.interpreter.interpret(system, trajectory, stride=stride)
            chart_types = tuple(dict.fromkeys(segment.chart.value for segment in interpretation.segments))
            covered.extend(chart_types)
            blockers.extend(interpretation.unresolved_obligations)
            resolved.extend(interpretation.resolved_obligations)
            rows.append(
                InterpretationSuiteRow(
                    name=name,
                    segment_count=len(interpretation.segments),
                    transition_count=len(interpretation.transitions),
                    regime_status=interpretation.certificate.regime_status,
                    local_interpretation_available=interpretation.certificate.local_interpretation_available,
                    theorem_ready=interpretation.certificate.theorem_ready,
                    chart_types=chart_types,
                    resolved_obligation_count=len(interpretation.resolved_obligations),
                    blocker_count=len(interpretation.unresolved_obligations),
                )
            )
        return InterpretationSuiteResult(
            rows=tuple(rows),
            covered_chart_types=tuple(sorted(set(covered))),
            unresolved_blockers=tuple(dict.fromkeys(blockers)),
            resolved_obligations=tuple(dict.fromkeys(resolved)),
        )

    def _hierarchical_flyby(self) -> tuple[object, TrajectoryResult, int]:
        scenario = self.library.general_hierarchical_flyby(duration=2.0, samples=120)
        trajectory = self.integrator.integrate(
            scenario.system,
            scenario.t_span,
            scenario.initial_state,
            t_eval=scenario.t_eval,
        )
        return scenario.system, trajectory, 10

    def _restricted_l4(self) -> tuple[object, TrajectoryResult, int]:
        scenario = self.library.restricted_l4(periods=0.2, samples=160)
        trajectory = self.integrator.integrate(
            scenario.system,
            scenario.t_span,
            scenario.initial_state,
            t_eval=scenario.t_eval,
        )
        return scenario.system, trajectory, 10

    def _escape_scattering(self) -> tuple[object, TrajectoryResult, int]:
        system = GeneralThreeBodySystem(masses=(1.0, 1.0, 0.1), dimension=2)
        times = np.linspace(0.0, 1.0, 40)
        states = []
        for time in times:
            positions = np.array([[-0.1, 0.0], [0.1, 0.0], [8.0 + 4.0 * time, 0.0]], dtype=float)
            velocities = np.array([[0.0, 0.4], [0.0, -0.4], [4.0, 0.0]], dtype=float)
            states.append(system.flatten_state(positions, velocities))
        return system, TrajectoryResult(t=times, y=np.asarray(states), success=True, message="synthetic escape"), 5

    def _close_encounter(self) -> tuple[object, TrajectoryResult, int]:
        system = GeneralThreeBodySystem(masses=(1.0, 1.0, 1.0), dimension=2)
        state = system.flatten_state(
            np.array([[0.0, 0.0], [0.005, 0.0], [1.0, 0.0]], dtype=float),
            np.zeros((3, 2), dtype=float),
        )
        return (
            system,
            TrajectoryResult(t=np.array([0.0, 1.0]), y=np.vstack([state, state]), success=True, message="synthetic close"),
            1,
        )


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
class CloseEncounterResidualResult:
    sample_count: int
    minimum_pair_distance: float
    maximum_finite_difference_residual: float | None
    residual_threshold: float
    residual_resolved: bool
    flow_defined: bool
    maximum_equivalence_acceleration_residual: float
    equivalence_resolved: bool

    def as_dict(self) -> dict[str, float | int | bool | None]:
        return {
            "sample_count": self.sample_count,
            "minimum_pair_distance": self.minimum_pair_distance,
            "maximum_finite_difference_residual": self.maximum_finite_difference_residual,
            "residual_threshold": self.residual_threshold,
            "residual_resolved": self.residual_resolved,
            "flow_defined": self.flow_defined,
            "maximum_equivalence_acceleration_residual": self.maximum_equivalence_acceleration_residual,
            "equivalence_resolved": self.equivalence_resolved,
        }


@dataclass(slots=True)
class CloseEncounterResidualStudy:
    """Validate Levi-Civita regularized RHS residual on an integrated close encounter."""

    library: OrbitLibrary = field(default_factory=OrbitLibrary)
    integrator: AdaptiveIntegrator = field(
        default_factory=lambda: AdaptiveIntegrator(rtol=1.0e-11, atol=1.0e-13, max_step=1.0e-4)
    )
    residual_threshold: float = 1.0e-4

    def run(self) -> CloseEncounterResidualResult:
        scenario = self.library.general_close_encounter_probe()
        trajectory = self.integrator.integrate(
            scenario.system,
            scenario.t_span,
            scenario.initial_state,
            t_eval=scenario.t_eval,
        )
        certificate = levi_civita_flow_certificate(
            scenario.system,
            trajectory,
            pair=(0, 1),
            residual_tolerance=self.residual_threshold,
        )
        equivalence = levi_civita_equivalence_certificate(scenario.system, trajectory, pair=(0, 1))
        return CloseEncounterResidualResult(
            sample_count=certificate.sample_count,
            minimum_pair_distance=certificate.minimum_radius,
            maximum_finite_difference_residual=certificate.maximum_finite_difference_residual,
            residual_threshold=self.residual_threshold,
            residual_resolved=certificate.residual_resolved,
            flow_defined=certificate.flow_defined,
            maximum_equivalence_acceleration_residual=equivalence.maximum_acceleration_residual,
            equivalence_resolved=equivalence.equivalence_resolved,
        )


@dataclass(frozen=True, slots=True)
class CloseEncounterResidualGridRow:
    label: str
    binary_separation: float
    intruder_mass: float
    sample_count: int
    minimum_pair_distance: float
    maximum_finite_difference_residual: float | None
    residual_resolved: bool
    flow_defined: bool
    maximum_equivalence_acceleration_residual: float
    equivalence_resolved: bool

    def as_dict(self) -> dict[str, float | int | bool | str | None]:
        return {
            "label": self.label,
            "binary_separation": self.binary_separation,
            "intruder_mass": self.intruder_mass,
            "sample_count": self.sample_count,
            "minimum_pair_distance": self.minimum_pair_distance,
            "maximum_finite_difference_residual": self.maximum_finite_difference_residual,
            "residual_resolved": self.residual_resolved,
            "flow_defined": self.flow_defined,
            "maximum_equivalence_acceleration_residual": self.maximum_equivalence_acceleration_residual,
            "equivalence_resolved": self.equivalence_resolved,
        }


@dataclass(frozen=True, slots=True)
class CloseEncounterResidualGridResult:
    rows: tuple[CloseEncounterResidualGridRow, ...]
    residual_threshold: float

    @property
    def pass_rate(self) -> float:
        if not self.rows:
            return 0.0
        return float(sum(row.residual_resolved for row in self.rows) / len(self.rows))

    @property
    def equivalence_pass_rate(self) -> float:
        if not self.rows:
            return 0.0
        return float(sum(row.equivalence_resolved for row in self.rows) / len(self.rows))

    @property
    def maximum_residual(self) -> float | None:
        residuals = [
            row.maximum_finite_difference_residual
            for row in self.rows
            if row.maximum_finite_difference_residual is not None
        ]
        return None if not residuals else float(max(residuals))

    @property
    def maximum_equivalence_acceleration_residual(self) -> float | None:
        if not self.rows:
            return None
        return float(max(row.maximum_equivalence_acceleration_residual for row in self.rows))

    def as_dict(self) -> dict[str, object]:
        return {
            "rows": [row.as_dict() for row in self.rows],
            "residual_threshold": self.residual_threshold,
            "pass_rate": self.pass_rate,
            "equivalence_pass_rate": self.equivalence_pass_rate,
            "maximum_residual": self.maximum_residual,
            "maximum_equivalence_acceleration_residual": self.maximum_equivalence_acceleration_residual,
        }


@dataclass(slots=True)
class CloseEncounterResidualGridStudy:
    """Validate Levi-Civita regularized RHS over a small integrated close-encounter grid."""

    library: OrbitLibrary = field(default_factory=OrbitLibrary)
    integrator: AdaptiveIntegrator = field(
        default_factory=lambda: AdaptiveIntegrator(rtol=1.0e-11, atol=1.0e-13, max_step=1.0e-4)
    )
    residual_threshold: float = 2.0e-4

    def run(self) -> CloseEncounterResidualGridResult:
        rows = []
        for label, parameters in self._cases():
            scenario = self.library.general_close_encounter_probe(**parameters)
            trajectory = self.integrator.integrate(
                scenario.system,
                scenario.t_span,
                scenario.initial_state,
                t_eval=scenario.t_eval,
            )
            certificate = levi_civita_flow_certificate(
                scenario.system,
                trajectory,
                pair=(0, 1),
                residual_tolerance=self.residual_threshold,
            )
            equivalence = levi_civita_equivalence_certificate(scenario.system, trajectory, pair=(0, 1))
            rows.append(
                CloseEncounterResidualGridRow(
                    label=label,
                    binary_separation=float(parameters["binary_separation"]),
                    intruder_mass=float(parameters["intruder_mass"]),
                    sample_count=certificate.sample_count,
                    minimum_pair_distance=certificate.minimum_radius,
                    maximum_finite_difference_residual=certificate.maximum_finite_difference_residual,
                    residual_resolved=certificate.residual_resolved,
                    flow_defined=certificate.flow_defined,
                    maximum_equivalence_acceleration_residual=equivalence.maximum_acceleration_residual,
                    equivalence_resolved=equivalence.equivalence_resolved,
                )
            )
        return CloseEncounterResidualGridResult(rows=tuple(rows), residual_threshold=self.residual_threshold)

    def _cases(self) -> tuple[tuple[str, dict[str, object]], ...]:
        return (
            (
                "baseline_close_binary",
                {
                    "binary_separation": 0.02,
                    "intruder_mass": 0.05,
                    "intruder_position": (1.0, 0.2),
                    "intruder_velocity": (0.0, -0.1),
                    "duration": 0.02,
                    "samples": 401,
                },
            ),
            (
                "light_offaxis_intruder",
                {
                    "binary_separation": 0.022,
                    "intruder_mass": 0.03,
                    "intruder_position": (1.2, -0.1),
                    "intruder_velocity": (-0.05, 0.08),
                    "duration": 0.02,
                    "samples": 401,
                },
            ),
            (
                "strong_oblique_intruder",
                {
                    "binary_separation": 0.024,
                    "intruder_mass": 0.08,
                    "intruder_position": (0.9, 0.35),
                    "intruder_velocity": (0.03, -0.06),
                    "duration": 0.018,
                    "samples": 361,
                },
            ),
            (
                "heavy_collinear_intruder",
                {
                    "binary_separation": 0.026,
                    "intruder_mass": 0.1,
                    "intruder_position": (1.1, 0.0),
                    "intruder_velocity": (0.0, 0.05),
                    "duration": 0.018,
                    "samples": 361,
                },
            ),
        )


@dataclass(frozen=True, slots=True)
class NearCollisionScalingRow:
    binary_separation: float
    duration: float
    sample_count: int
    minimum_pair_distance: float
    maximum_rhs_norm: float
    maximum_perturbation_acceleration_norm: float
    maximum_perturbation_to_kepler_ratio: float
    tidal_constant_estimate: float
    maximum_finite_difference_residual: float | None
    normalized_residual: float | None
    maximum_equivalence_acceleration_residual: float
    residual_resolved: bool
    equivalence_resolved: bool

    def as_dict(self) -> dict[str, float | int | bool | None]:
        return {
            "binary_separation": self.binary_separation,
            "duration": self.duration,
            "sample_count": self.sample_count,
            "minimum_pair_distance": self.minimum_pair_distance,
            "maximum_rhs_norm": self.maximum_rhs_norm,
            "maximum_perturbation_acceleration_norm": self.maximum_perturbation_acceleration_norm,
            "maximum_perturbation_to_kepler_ratio": self.maximum_perturbation_to_kepler_ratio,
            "tidal_constant_estimate": self.tidal_constant_estimate,
            "maximum_finite_difference_residual": self.maximum_finite_difference_residual,
            "normalized_residual": self.normalized_residual,
            "maximum_equivalence_acceleration_residual": self.maximum_equivalence_acceleration_residual,
            "residual_resolved": self.residual_resolved,
            "equivalence_resolved": self.equivalence_resolved,
        }


@dataclass(frozen=True, slots=True)
class NearCollisionScalingResult:
    rows: tuple[NearCollisionScalingRow, ...]
    residual_threshold: float
    normalized_residual_threshold: float
    minimum_allowed_normalized_slope: float = -0.25
    maximum_allowed_perturbation_ratio: float = 5.0e-7
    minimum_allowed_perturbation_ratio_slope: float = 2.5
    maximum_allowed_tidal_constant: float = 6.0e-2

    @property
    def minimum_pair_distance(self) -> float | None:
        return None if not self.rows else float(min(row.minimum_pair_distance for row in self.rows))

    @property
    def maximum_residual(self) -> float | None:
        residuals = [
            row.maximum_finite_difference_residual
            for row in self.rows
            if row.maximum_finite_difference_residual is not None
        ]
        return None if not residuals else float(max(residuals))

    @property
    def maximum_normalized_residual(self) -> float | None:
        residuals = [row.normalized_residual for row in self.rows if row.normalized_residual is not None]
        return None if not residuals else float(max(residuals))

    @property
    def maximum_equivalence_acceleration_residual(self) -> float | None:
        return None if not self.rows else float(max(row.maximum_equivalence_acceleration_residual for row in self.rows))

    @property
    def normalized_residual_scaling_exponent(self) -> float | None:
        return _loglog_slope(
            tuple(row.minimum_pair_distance for row in self.rows),
            tuple(row.normalized_residual for row in self.rows),
        )

    @property
    def absolute_residual_scaling_exponent(self) -> float | None:
        return _loglog_slope(
            tuple(row.minimum_pair_distance for row in self.rows),
            tuple(row.maximum_finite_difference_residual for row in self.rows),
        )

    @property
    def maximum_perturbation_to_kepler_ratio(self) -> float | None:
        return None if not self.rows else float(max(row.maximum_perturbation_to_kepler_ratio for row in self.rows))

    @property
    def perturbation_ratio_scaling_exponent(self) -> float | None:
        return _loglog_slope(
            tuple(row.minimum_pair_distance for row in self.rows),
            tuple(row.maximum_perturbation_to_kepler_ratio for row in self.rows),
        )

    @property
    def tidal_constant_bound(self) -> float | None:
        return None if not self.rows else float(max(row.tidal_constant_estimate for row in self.rows))

    @property
    def tidal_bound_resolved(self) -> bool:
        return self.tidal_constant_bound is not None and self.tidal_constant_bound <= self.maximum_allowed_tidal_constant

    @property
    def pass_rate(self) -> float:
        if not self.rows:
            return 0.0
        return float(sum(row.residual_resolved and row.equivalence_resolved for row in self.rows) / len(self.rows))

    @property
    def scaling_resolved(self) -> bool:
        slope = self.normalized_residual_scaling_exponent
        perturbation_slope = self.perturbation_ratio_scaling_exponent
        return (
            self.pass_rate == 1.0
            and self.maximum_residual is not None
            and self.maximum_residual <= self.residual_threshold
            and self.maximum_normalized_residual is not None
            and self.maximum_normalized_residual <= self.normalized_residual_threshold
            and slope is not None
            and slope >= self.minimum_allowed_normalized_slope
            and self.maximum_perturbation_to_kepler_ratio is not None
            and self.maximum_perturbation_to_kepler_ratio <= self.maximum_allowed_perturbation_ratio
            and perturbation_slope is not None
            and perturbation_slope >= self.minimum_allowed_perturbation_ratio_slope
            and self.tidal_bound_resolved
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "rows": [row.as_dict() for row in self.rows],
            "residual_threshold": self.residual_threshold,
            "normalized_residual_threshold": self.normalized_residual_threshold,
            "minimum_allowed_normalized_slope": self.minimum_allowed_normalized_slope,
            "maximum_allowed_perturbation_ratio": self.maximum_allowed_perturbation_ratio,
            "minimum_allowed_perturbation_ratio_slope": self.minimum_allowed_perturbation_ratio_slope,
            "maximum_allowed_tidal_constant": self.maximum_allowed_tidal_constant,
            "minimum_pair_distance": self.minimum_pair_distance,
            "maximum_residual": self.maximum_residual,
            "maximum_normalized_residual": self.maximum_normalized_residual,
            "maximum_equivalence_acceleration_residual": self.maximum_equivalence_acceleration_residual,
            "normalized_residual_scaling_exponent": self.normalized_residual_scaling_exponent,
            "absolute_residual_scaling_exponent": self.absolute_residual_scaling_exponent,
            "maximum_perturbation_to_kepler_ratio": self.maximum_perturbation_to_kepler_ratio,
            "perturbation_ratio_scaling_exponent": self.perturbation_ratio_scaling_exponent,
            "tidal_constant_bound": self.tidal_constant_bound,
            "tidal_bound_resolved": self.tidal_bound_resolved,
            "pass_rate": self.pass_rate,
            "scaling_resolved": self.scaling_resolved,
        }


@dataclass(slots=True)
class NearCollisionScalingStudy:
    """Push the Levi-Civita residual certificate toward smaller binary separations."""

    library: OrbitLibrary = field(default_factory=OrbitLibrary)
    integrator: AdaptiveIntegrator = field(
        default_factory=lambda: AdaptiveIntegrator(rtol=1.0e-11, atol=1.0e-13, max_step=5.0e-5)
    )
    residual_threshold: float = 5.0e-4
    normalized_residual_threshold: float = 5.0e-5

    def run(self) -> NearCollisionScalingResult:
        rows = []
        for separation, duration, samples in (
            (0.020, 0.020, 401),
            (0.016, 0.016, 401),
            (0.012, 0.012, 481),
            (0.010, 0.010, 501),
            (0.008, 0.008, 641),
        ):
            scenario = self.library.general_close_encounter_probe(
                binary_separation=separation,
                intruder_mass=0.05,
                intruder_position=(1.0, 0.2),
                intruder_velocity=(0.0, -0.1),
                duration=duration,
                samples=samples,
            )
            trajectory = self.integrator.integrate(
                scenario.system,
                scenario.t_span,
                scenario.initial_state,
                t_eval=scenario.t_eval,
            )
            certificate = levi_civita_flow_certificate(
                scenario.system,
                trajectory,
                pair=(0, 1),
                residual_tolerance=self.residual_threshold,
            )
            equivalence = levi_civita_equivalence_certificate(scenario.system, trajectory, pair=(0, 1))
            normalized = (
                None
                if certificate.maximum_finite_difference_residual is None
                else float(certificate.maximum_finite_difference_residual / max(certificate.maximum_rhs_norm, 1.0e-18))
            )
            masses = np.asarray(scenario.system.masses, dtype=float)
            kepler_acceleration = float(
                scenario.system.gravitational_constant
                * (masses[0] + masses[1])
                / max(certificate.minimum_radius**2, 1.0e-18)
            )
            perturbation_ratio = float(
                certificate.maximum_perturbation_acceleration_norm / max(kepler_acceleration, 1.0e-18)
            )
            tidal_constant = float(perturbation_ratio / max(certificate.minimum_radius**3, 1.0e-18))
            rows.append(
                NearCollisionScalingRow(
                    binary_separation=separation,
                    duration=duration,
                    sample_count=certificate.sample_count,
                    minimum_pair_distance=certificate.minimum_radius,
                    maximum_rhs_norm=certificate.maximum_rhs_norm,
                    maximum_perturbation_acceleration_norm=certificate.maximum_perturbation_acceleration_norm,
                    maximum_perturbation_to_kepler_ratio=perturbation_ratio,
                    tidal_constant_estimate=tidal_constant,
                    maximum_finite_difference_residual=certificate.maximum_finite_difference_residual,
                    normalized_residual=normalized,
                    maximum_equivalence_acceleration_residual=equivalence.maximum_acceleration_residual,
                    residual_resolved=certificate.residual_resolved,
                    equivalence_resolved=equivalence.equivalence_resolved,
                )
            )
        return NearCollisionScalingResult(
            rows=tuple(rows),
            residual_threshold=self.residual_threshold,
            normalized_residual_threshold=self.normalized_residual_threshold,
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


def _loglog_slope(xs: tuple[float, ...], ys: tuple[float | None, ...]) -> float | None:
    pairs = [(float(x), float(y)) for x, y in zip(xs, ys, strict=True) if y is not None and x > 0.0 and y > 0.0]
    if len(pairs) < 2:
        return None
    log_x = np.log([pair[0] for pair in pairs])
    log_y = np.log([pair[1] for pair in pairs])
    slope, _intercept = np.polyfit(log_x, log_y, 1)
    return float(slope)


def _benchmark(name: str, metric: str, observed_error: float, reference: float, tolerance: float) -> BenchmarkResult:
    return BenchmarkResult(
        name=name,
        metric=metric,
        observed=observed_error,
        reference=reference,
        absolute_error=abs(observed_error - reference),
        passed=abs(observed_error - reference) <= tolerance,
    )
