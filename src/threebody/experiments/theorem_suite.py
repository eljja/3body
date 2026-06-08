from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..analysis import (
    JacobiEscapeCertificate,
    JacobiFutureTailBound,
    JacobiInflatedMarginCertificate,
    JacobiIntervalFlowTubeCertificate,
    JacobiIntervalPicardFlowCertificate,
    JacobiIntervalTailCertificate,
    JacobiOpenConeCertificate,
    JacobiQuadrupoleAccelerationCertificate,
    JacobiSelfConsistentConeCertificate,
    JacobiTailIntervalReserveCertificate,
    jacobi_escape_sufficient_condition,
    jacobi_future_tail_bound,
    jacobi_inflated_margin_certificate,
    jacobi_interval_flow_tube_certificate,
    jacobi_interval_picard_flow_certificate,
    jacobi_interval_escape_certificate,
    jacobi_open_escape_cone_certificate,
    jacobi_quadrupole_acceleration_certificate,
    jacobi_self_consistent_escape_cone,
    jacobi_tail_interval_reserve_certificate,
    word_distance,
)
from ..solvers import AdaptiveIntegrator
from .flyby_sweep import GRAMMAR_BRANCH_SCORE_THRESHOLD, HierarchicalFlybySweep
from .orbit_library import OrbitLibrary
from .research_checks import (
    ClassifierArtifactStudy,
    CloseEncounterResidualGridStudy,
    CloseEncounterResidualStudy,
    GrammarBranchArtifactStudy,
    IntegratorComparisonStudy,
    InterpretationSuite,
    KnownBenchmarkSuite,
    NearCollisionScalingStudy,
    RegimeProbeSuite,
)


@dataclass(frozen=True, slots=True)
class ProofObligation:
    name: str
    status: str
    evidence: str
    blocker: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "name": self.name,
            "status": self.status,
            "evidence": self.evidence,
            "blocker": self.blocker,
        }


@dataclass(frozen=True, slots=True)
class TheoremCandidate:
    name: str
    claim: str
    scope: str
    novelty_target: str
    proven: bool
    obligations: tuple[ProofObligation, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "claim": self.claim,
            "scope": self.scope,
            "novelty_target": self.novelty_target,
            "proven": self.proven,
            "obligations": [obligation.as_dict() for obligation in self.obligations],
        }


@dataclass(frozen=True, slots=True)
class PaperBenchmarkResult:
    name: str
    passed: bool
    metric: str
    observed: float | None
    threshold: float | None
    interpretation: str

    def as_dict(self) -> dict[str, float | str | bool | None]:
        return {
            "name": self.name,
            "passed": self.passed,
            "metric": self.metric,
            "observed": self.observed,
            "threshold": self.threshold,
            "interpretation": self.interpretation,
        }


@dataclass(frozen=True, slots=True)
class TheoremSuiteResult:
    mode: str
    theorem_candidates: tuple[TheoremCandidate, ...]
    benchmarks: tuple[PaperBenchmarkResult, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "theorem_candidates": [candidate.as_dict() for candidate in self.theorem_candidates],
            "benchmarks": [benchmark.as_dict() for benchmark in self.benchmarks],
        }


@dataclass(frozen=True, slots=True)
class JacobiParameterBoxResult:
    case_count: int
    pass_rate: float
    minimum_relative_open_radius: float
    minimum_grid_margin_lower: float
    finite_difference_lipschitz_bound: float
    normalized_cell_radius: float
    interval_box_margin_lower: float
    maximum_quadrupole_bound_ratio: float
    interval_tail_pass_rate: float
    minimum_interval_tail_margin_lower: float
    flow_tube_pass_rate: float
    minimum_flow_tube_margin_lower: float
    maximum_flow_tube_radius: float
    picard_flow_pass_rate: float
    minimum_picard_flow_margin_lower: float
    maximum_picard_contraction: float
    picard_finite_difference_lipschitz_bound: float
    picard_interval_box_margin_lower: float
    picard_cell_center_count: int
    picard_cell_center_pass_rate: float
    minimum_picard_cell_center_margin_lower: float
    picard_cell_center_variation_bound: float
    picard_cell_center_reserve_margin_lower: float
    picard_face_center_count: int
    picard_face_center_pass_rate: float
    minimum_picard_face_center_margin_lower: float
    picard_face_center_variation_bound: float
    picard_face_center_reserve_margin_lower: float
    picard_edge_center_count: int
    picard_edge_center_pass_rate: float
    minimum_picard_edge_center_margin_lower: float
    picard_edge_center_variation_bound: float
    picard_edge_center_reserve_margin_lower: float
    picard_half_grid_count: int
    picard_half_grid_lipschitz_bound: float
    picard_half_grid_interval_margin_lower: float
    picard_half_grid_subcell_count: int
    picard_half_grid_subcell_margin_lower: float
    box_certified: bool
    grid_margin_certified: bool
    interval_box_certified: bool
    parameter_interval_tail_certified: bool
    parameter_flow_tube_certified: bool
    parameter_picard_flow_certified: bool
    parameter_picard_interval_box_certified: bool
    parameter_picard_cell_centers_certified: bool
    parameter_picard_face_centers_certified: bool
    parameter_picard_edge_centers_certified: bool
    parameter_picard_half_grid_certified: bool
    parameter_picard_half_grid_subcells_certified: bool


@dataclass(frozen=True, slots=True)
class JacobiResolutionCrosscheckResult:
    case_count: int
    pass_rate: float
    minimum_picard_margin_lower: float
    maximum_margin_spread: float
    maximum_tube_radius: float
    maximum_propagated_endpoint_radius: float
    maximum_observed_contraction: float
    minimum_sample_count: int
    maximum_sample_count: int
    certified: bool


@dataclass(slots=True)
class TheoremSuite:
    """Reproducible theorem/proof-obligation/benchmark harness."""

    mode: str = "quick"

    def run(self) -> TheoremSuiteResult:
        if self.mode not in {"quick", "paper"}:
            raise ValueError("TheoremSuite mode must be 'quick' or 'paper'.")
        artifact_rows = ClassifierArtifactStudy().run(duration=8.0, samples=500)
        grammar_artifact_rows = GrammarBranchArtifactStudy().run(duration=8.0, samples=180)
        integrator = IntegratorComparisonStudy().run()
        benchmarks = KnownBenchmarkSuite().run()
        regimes = RegimeProbeSuite().run()
        interpretation = InterpretationSuite().run()
        close_residual = CloseEncounterResidualStudy().run()
        close_residual_grid = CloseEncounterResidualGridStudy().run()
        near_collision = NearCollisionScalingStudy().run()
        jacobi_escape = _jacobi_escape_benchmark()
        jacobi_future_tail = _jacobi_future_tail_benchmark()
        jacobi_inflated_margin = _jacobi_inflated_margin_benchmark()
        jacobi_self_consistent = _jacobi_self_consistent_benchmark()
        jacobi_open_cone = _jacobi_open_cone_benchmark()
        jacobi_tail_interval = _jacobi_tail_interval_benchmark()
        jacobi_interval_tail = _jacobi_interval_tail_benchmark()
        jacobi_flow_tube = _jacobi_flow_tube_benchmark()
        jacobi_picard_flow = _jacobi_picard_flow_benchmark()
        jacobi_resolution_crosscheck = _jacobi_resolution_crosscheck_benchmark()
        jacobi_quadrupole = _jacobi_quadrupole_benchmark()
        jacobi_parameter_box = _jacobi_parameter_box_benchmark(paper=self.mode == "paper")
        flyby = HierarchicalFlybySweep().run_discovery_validation(
            discovery_binary_phases=(0.0, 1.5707963267948966),
            validation_binary_phases=(
                0.39269908169872414,
                0.7853981633974483,
                1.1780972450961724,
                2.356194490192345,
            ),
            duration=8.0,
            samples=240,
            stride=20,
        )
        flyby_summary = flyby.as_dict()
        benchmark_rows = _paper_benchmarks(
            artifact_rows,
            grammar_artifact_rows,
            integrator,
            benchmarks,
            regimes,
            interpretation,
            close_residual,
            close_residual_grid,
            near_collision,
            jacobi_escape,
            jacobi_future_tail,
            jacobi_inflated_margin,
            jacobi_self_consistent,
            jacobi_open_cone,
            jacobi_tail_interval,
            jacobi_interval_tail,
            jacobi_flow_tube,
            jacobi_picard_flow,
            jacobi_resolution_crosscheck,
            jacobi_quadrupole,
            jacobi_parameter_box,
            flyby_summary,
        )
        candidates = _theorem_candidates(benchmark_rows)
        return TheoremSuiteResult(mode=self.mode, theorem_candidates=candidates, benchmarks=benchmark_rows)


def _paper_benchmarks(
    artifact_rows: object,
    grammar_artifact_rows: object,
    integrator: object,
    known_benchmarks: object,
    regimes: object,
    interpretation: object,
    close_residual: object,
    close_residual_grid: object,
    near_collision: object,
    jacobi_escape: JacobiEscapeCertificate,
    jacobi_future_tail: JacobiFutureTailBound,
    jacobi_inflated_margin: JacobiInflatedMarginCertificate,
    jacobi_self_consistent: JacobiSelfConsistentConeCertificate,
    jacobi_open_cone: JacobiOpenConeCertificate,
    jacobi_tail_interval: JacobiTailIntervalReserveCertificate,
    jacobi_interval_tail: JacobiIntervalTailCertificate,
    jacobi_flow_tube: JacobiIntervalFlowTubeCertificate,
    jacobi_picard_flow: JacobiIntervalPicardFlowCertificate,
    jacobi_resolution_crosscheck: JacobiResolutionCrosscheckResult,
    jacobi_quadrupole: JacobiQuadrupoleAccelerationCertificate,
    jacobi_parameter_box: JacobiParameterBoxResult,
    flyby_summary: dict[str, object],
) -> tuple[PaperBenchmarkResult, ...]:
    transition_counts = [row.transition_count for row in artifact_rows]
    baseline_count = transition_counts[0]
    artifact_spread = max(abs(count - baseline_count) for count in transition_counts)
    grammar_artifact_scores = [
        row.minimum_score for row in grammar_artifact_rows if row.minimum_score is not None
    ]
    grammar_artifact_certified_accuracies = [
        row.minimum_certified_accuracy
        for row in grammar_artifact_rows
        if row.minimum_certified_accuracy is not None
    ]
    grammar_artifact_certified_fractions = [
        row.minimum_certified_fraction
        for row in grammar_artifact_rows
        if row.minimum_certified_fraction is not None
    ]
    grammar_artifact_mean_margins = [
        row.minimum_mean_margin for row in grammar_artifact_rows if row.minimum_mean_margin is not None
    ]
    grammar_artifact_negative_control_gaps = [
        row.minimum_negative_control_gap
        for row in grammar_artifact_rows
        if row.minimum_negative_control_gap is not None
    ]
    grammar_artifact_high_negative_control_gaps = [
        row.high_negative_control_gap for row in grammar_artifact_rows if row.high_negative_control_gap is not None
    ]
    grammar_artifact_hysteresis_negative_control_gaps = [
        row.hysteresis_negative_control_gap
        for row in grammar_artifact_rows
        if row.hysteresis_negative_control_gap is not None
    ]
    grammar_artifact_pass_rate = sum(1 for row in grammar_artifact_rows if row.passed) / len(grammar_artifact_rows)
    minimum_grammar_artifact_score = None if not grammar_artifact_scores else float(min(grammar_artifact_scores))
    minimum_grammar_artifact_certified_accuracy = (
        None if not grammar_artifact_certified_accuracies else float(min(grammar_artifact_certified_accuracies))
    )
    minimum_grammar_artifact_certified_fraction = (
        None if not grammar_artifact_certified_fractions else float(min(grammar_artifact_certified_fractions))
    )
    minimum_grammar_artifact_mean_margin = (
        None if not grammar_artifact_mean_margins else float(min(grammar_artifact_mean_margins))
    )
    minimum_grammar_artifact_negative_control_gap = (
        None if not grammar_artifact_negative_control_gaps else float(min(grammar_artifact_negative_control_gaps))
    )
    minimum_grammar_artifact_high_negative_control_gap = (
        None
        if not grammar_artifact_high_negative_control_gaps
        else float(min(grammar_artifact_high_negative_control_gaps))
    )
    minimum_grammar_artifact_hysteresis_negative_control_gap = (
        None
        if not grammar_artifact_hysteresis_negative_control_gaps
        else float(min(grammar_artifact_hysteresis_negative_control_gaps))
    )
    known_pass_rate = sum(1 for row in known_benchmarks if row.passed) / len(known_benchmarks)
    known_by_name = {row.name: row for row in known_benchmarks}
    figure_eight_noether_energy = known_by_name["figure_eight_noether_energy_drift"]
    figure_eight_noether_linear = known_by_name["figure_eight_noether_linear_momentum"]
    figure_eight_noether_angular = known_by_name["figure_eight_noether_angular_momentum"]
    figure_eight_com_position = known_by_name["figure_eight_center_of_mass_position"]
    figure_eight_com_momentum = known_by_name["figure_eight_center_of_mass_momentum"]
    figure_eight_lagrange_jacobi = known_by_name["figure_eight_lagrange_jacobi_identity"]
    figure_eight_sundman = known_by_name["figure_eight_sundman_inequality"]
    figure_eight_variational = known_by_name["figure_eight_variational_linear_stability"]
    figure_eight_symplectic = known_by_name["figure_eight_variational_symplectic_residual"]
    figure_eight_hamiltonian = known_by_name["figure_eight_hamiltonian_jacobian_structure"]
    figure_eight_choreography_position = known_by_name["figure_eight_choreography_position"]
    figure_eight_choreography_velocity = known_by_name["figure_eight_choreography_velocity"]
    figure_eight_variational_convergence = known_by_name["figure_eight_variational_step_convergence"]
    regime_names = {row.name for row in regimes}
    reduced_regime_hints = {
        str(row.extra.get("reduced_regime_hint"))
        for row in regimes
        if "reduced_regime_hint" in row.extra
    }
    levi_civita_chart_resolved = "numerically construct Levi-Civita binary collision chart" in set(
        interpretation.resolved_obligations
    )
    levi_civita_flow_defined = "construct perturbation-aware Levi-Civita regularized RHS" in set(
        interpretation.resolved_obligations
    )
    levi_civita_equivalence_resolved = "numerically certify Levi-Civita inertial equivalence residual" in set(
        interpretation.resolved_obligations
    )
    best_models = flyby_summary["best_validation_models"]
    grammar_outcomes = flyby_summary["grammar_outcome_validations"]
    low_best = next((row for row in best_models if str(row["target"]).startswith("low_")), None)
    low_best_is_scattering = low_best is not None and "scattering_map" in str(low_best["target"])
    low_scattering_validation = next(
        (
            row
            for row in flyby_summary["collapse_validations"]
            if str(row["target"]) == "low_crossing_scattering_map"
        ),
        None,
    )
    low_scattering_score = (
        None
        if low_scattering_validation is None
        else float(low_scattering_validation["complexity_penalized_validation_score"])
    )
    low_scattering_selection_score = 1.0 if low_best_is_scattering else 0.0
    low_scattering_selection = next(
        (
            row
            for row in best_models
            if str(row["target"]).startswith("low_") and "scattering_map" in str(row["target"])
        ),
        None,
    )
    low_selection_score = (
        None if low_scattering_selection is None else float(low_scattering_selection["complexity_penalized_validation_score"])
    )
    discovery_words = _word_rows_by_name(flyby_summary["discovery"])
    validation_words = _word_rows_by_name(flyby_summary["validation"])
    word_stability = _word_stability_score(discovery_words, validation_words)
    combined_word_rows = tuple(discovery_words.values()) + tuple(validation_words.values())
    distinct_word_count = _distinct_word_count(combined_word_rows)
    validation_distinct_word_count = _distinct_word_count(tuple(validation_words.values()))
    refined_discovery_words = _word_rows_by_name(flyby_summary["discovery"], field="refined_chart_word")
    refined_validation_words = _word_rows_by_name(flyby_summary["validation"], field="refined_chart_word")
    refined_word_stability = _word_stability_score(
        refined_discovery_words,
        refined_validation_words,
        field="refined_chart_word",
    )
    refined_combined_word_rows = tuple(refined_discovery_words.values()) + tuple(refined_validation_words.values())
    refined_distinct_word_count = _distinct_word_count(refined_combined_word_rows, field="refined_chart_word")
    refined_validation_distinct_word_count = _distinct_word_count(
        tuple(refined_validation_words.values()),
        field="refined_chart_word",
    )
    return_discovery_words = _word_rows_by_name(flyby_summary["discovery"], field="return_chart_word")
    return_validation_words = _word_rows_by_name(flyby_summary["validation"], field="return_chart_word")
    return_word_stability = _word_stability_score(
        return_discovery_words,
        return_validation_words,
        field="return_chart_word",
    )
    return_validation_distinct_word_count = _distinct_word_count(
        tuple(return_validation_words.values()),
        field="return_chart_word",
    )
    high_best = next((row for row in best_models if str(row["target"]).startswith("high_")), None)
    hysteresis_best = next((row for row in best_models if str(row["target"]).startswith("hysteresis_")), None)
    low_best_score = None if low_best is None else float(low_best["complexity_penalized_validation_score"])
    high_best_score = None if high_best is None else float(high_best["complexity_penalized_validation_score"])
    hysteresis_best_score = (
        None if hysteresis_best is None else float(hysteresis_best["complexity_penalized_validation_score"])
    )
    low_best_target = "none" if low_best is None else str(low_best["target"])
    high_best_target = "none" if high_best is None else str(high_best["target"])
    hysteresis_best_target = "none" if hysteresis_best is None else str(hysteresis_best["target"])
    high_grammar = next(
        (row for row in grammar_outcomes if str(row["target"]) == "high_crossing_grammar_scattering_branch"),
        None,
    )
    hysteresis_grammar = next(
        (row for row in grammar_outcomes if str(row["target"]) == "hysteresis_width_grammar_phase_branch"),
        None,
    )
    high_grammar_score = (
        None if high_grammar is None else float(high_grammar["complexity_penalized_validation_score"])
    )
    hysteresis_grammar_score = (
        None if hysteresis_grammar is None else float(hysteresis_grammar["complexity_penalized_validation_score"])
    )
    high_grammar_negative_control_gap = (
        None if high_grammar is None else float(high_grammar["grammar_negative_control_score_gap"])
    )
    hysteresis_grammar_negative_control_gap = (
        None if hysteresis_grammar is None else float(hysteresis_grammar["grammar_negative_control_score_gap"])
    )
    high_selected_model, high_selected_score, high_selected_gap = _branch_explanation_selection(high_grammar)
    hysteresis_selected_model, hysteresis_selected_score, hysteresis_selected_gap = _branch_explanation_selection(
        hysteresis_grammar
    )
    grammar_training_gains = [
        float(row["training_accuracy_gain"])
        for row in (high_grammar, hysteresis_grammar)
        if row is not None and row.get("training_accuracy_gain") is not None
    ]
    grammar_validation_supports = [
        float(row["validation_support"])
        for row in (high_grammar, hysteresis_grammar)
        if row is not None and row.get("validation_support") is not None
    ]
    grammar_certified_accuracies = [
        float(row["certified_validation_accuracy"])
        for row in (high_grammar, hysteresis_grammar)
        if row is not None and row.get("certified_validation_accuracy") is not None
    ]
    grammar_certified_fractions = [
        float(row["certified_validation_fraction"])
        for row in (high_grammar, hysteresis_grammar)
        if row is not None and row.get("certified_validation_fraction") is not None
    ]
    grammar_mean_margins = [
        float(row["mean_decision_margin"])
        for row in (high_grammar, hysteresis_grammar)
        if row is not None and row.get("mean_decision_margin") is not None
    ]
    grammar_negative_control_gaps = [
        float(row["grammar_negative_control_score_gap"])
        for row in (high_grammar, hysteresis_grammar)
        if row is not None and row.get("grammar_negative_control_score_gap") is not None
    ]
    min_grammar_training_gain = None if not grammar_training_gains else float(min(grammar_training_gains))
    min_grammar_validation_support = None if not grammar_validation_supports else float(min(grammar_validation_supports))
    min_grammar_certified_accuracy = (
        None if not grammar_certified_accuracies else float(min(grammar_certified_accuracies))
    )
    min_grammar_certified_fraction = (
        None if not grammar_certified_fractions else float(min(grammar_certified_fractions))
    )
    min_grammar_mean_margin = None if not grammar_mean_margins else float(min(grammar_mean_margins))
    min_grammar_negative_control_gap = (
        None if not grammar_negative_control_gaps else float(min(grammar_negative_control_gaps))
    )
    return (
        PaperBenchmarkResult(
            name="known_reference_benchmarks",
            passed=known_pass_rate == 1.0,
            metric="pass_rate",
            observed=known_pass_rate,
            threshold=1.0,
            interpretation="L4/L5 geometry and figure-eight return must match known reference cases.",
        ),
        PaperBenchmarkResult(
            name="figure_eight_noether_invariants",
            passed=figure_eight_noether_energy.passed
            and figure_eight_noether_linear.passed
            and figure_eight_noether_angular.passed,
            metric="max_noether_guardrail_error",
            observed=max(
                figure_eight_noether_energy.observed,
                figure_eight_noether_linear.observed,
                figure_eight_noether_angular.observed,
            ),
            threshold=1.0e-9,
            interpretation=(
                "The figure-eight benchmark must conserve Noether invariants before periodic, "
                "symmetry, or reduced-state certificates are promoted."
            ),
        ),
        PaperBenchmarkResult(
            name="figure_eight_center_of_mass_reduction",
            passed=figure_eight_com_position.passed and figure_eight_com_momentum.passed,
            metric="max_center_or_momentum_norm",
            observed=max(figure_eight_com_position.observed, figure_eight_com_momentum.observed),
            threshold=1.0e-8,
            interpretation=(
                "The figure-eight benchmark must be in the center-of-mass quotient frame before "
                "periodic, Floquet, or choreography certificates are interpreted."
            ),
        ),
        PaperBenchmarkResult(
            name="figure_eight_lagrange_jacobi_identity",
            passed=figure_eight_lagrange_jacobi.passed,
            metric=figure_eight_lagrange_jacobi.metric,
            observed=figure_eight_lagrange_jacobi.observed,
            threshold=1.0e-9,
            interpretation=(
                "The sampled figure-eight trajectory must satisfy the Newtonian Lagrange-Jacobi "
                "identity I'' = 4E + 2U in the center-of-mass frame."
            ),
        ),
        PaperBenchmarkResult(
            name="figure_eight_sundman_inequality",
            passed=figure_eight_sundman.passed,
            metric=figure_eight_sundman.metric,
            observed=figure_eight_sundman.observed,
            threshold=1.0e-12,
            interpretation=(
                "The sampled figure-eight trajectory must satisfy Sundman's inequality |L|^2 <= 2 I T "
                "in the center-of-mass frame, constraining the admissible scale-angular-momentum state."
            ),
        ),
        PaperBenchmarkResult(
            name="figure_eight_variational_linear_stability",
            passed=figure_eight_variational.passed,
            metric=figure_eight_variational.metric,
            observed=figure_eight_variational.observed,
            threshold=1.002,
            interpretation=(
                "Figure-eight periodic-chart promotion now requires a variational monodromy certificate: "
                "orbit closure, volume preservation, reciprocal Floquet-multiplier pairing, and bounded "
                "nontrivial multiplier radius."
            ),
        ),
        PaperBenchmarkResult(
            name="figure_eight_variational_symplectic_residual",
            passed=figure_eight_symplectic.passed,
            metric=figure_eight_symplectic.metric,
            observed=figure_eight_symplectic.observed,
            threshold=1.0e-4,
            interpretation=(
                "The figure-eight variational state-transition matrix must preserve the mass-weighted "
                "symplectic form in q,v coordinates before Floquet multipliers are promoted."
            ),
        ),
        PaperBenchmarkResult(
            name="figure_eight_hamiltonian_jacobian_structure",
            passed=figure_eight_hamiltonian.passed,
            metric=figure_eight_hamiltonian.metric,
            observed=figure_eight_hamiltonian.observed,
            threshold=1.0e-5,
            interpretation=(
                "The sampled figure-eight Jacobians must satisfy A^T Omega + Omega A ~= 0, "
                "so the variational equation is tied to Hamiltonian structure rather than only fitted multipliers."
            ),
        ),
        PaperBenchmarkResult(
            name="figure_eight_choreography_symmetry",
            passed=figure_eight_choreography_position.passed and figure_eight_choreography_velocity.passed,
            metric="max_position_velocity_error",
            observed=max(figure_eight_choreography_position.observed, figure_eight_choreography_velocity.observed),
            threshold=1.0e-4,
            interpretation=(
                "The figure-eight benchmark must satisfy the T/3 choreography body-permutation symmetry, "
                "not only return close to its initial state."
            ),
        ),
        PaperBenchmarkResult(
            name="figure_eight_variational_step_convergence",
            passed=figure_eight_variational_convergence.passed,
            metric=figure_eight_variational_convergence.metric,
            observed=figure_eight_variational_convergence.observed,
            threshold=2.0e-3,
            interpretation=(
                "The figure-eight Floquet proxy must remain stable under a predeclared finite-difference "
                "Jacobian step sweep before it is treated as a periodic-chart certificate."
            ),
        ),
        PaperBenchmarkResult(
            name="classifier_artifact_bound",
            passed=artifact_spread <= 1,
            metric="max_transition_count_change",
            observed=float(artifact_spread),
            threshold=1.0,
            interpretation="Small threshold/stride perturbations should not completely rewrite the transition story.",
        ),
        PaperBenchmarkResult(
            name="integrator_drift_guardrail",
            passed=integrator.adaptive_energy_drift < 1.0e-7 and integrator.endpoint_separation < 1.0e-3,
            metric="adaptive_energy_drift",
            observed=integrator.adaptive_energy_drift,
            threshold=1.0e-7,
            interpretation="Reference integration must be stable enough before promoting transition laws.",
        ),
        PaperBenchmarkResult(
            name="regime_coverage_smoke",
            passed={"lagrange_neck", "shape_close_encounter", "escape_scattering"}.issubset(regime_names)
            and {"collision_boundary", "escape_boundary"}.issubset(reduced_regime_hints),
            metric="covered_required_regimes",
            observed=float(len(regime_names)),
            threshold=4.0,
            interpretation="The atlas must exercise non-flyby regimes before making broad claims.",
        ),
        PaperBenchmarkResult(
            name="jacobi_energy_split_residual",
            passed=jacobi_escape.decomposition_resolved,
            metric="maximum_closure_residual",
            observed=jacobi_escape.maximum_closure_residual,
            threshold=1.0e-9,
            interpretation=(
                "The hierarchy escape claim must first pass the exact Jacobi Hamiltonian split "
                "H - T_cm = E_inner + E_outer + W on the outgoing tail."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_escape_sufficient_condition",
            passed=jacobi_escape.sufficient_escape,
            metric="escape_margin",
            observed=jacobi_escape.escape_margin,
            threshold=0.0,
            interpretation=(
                "A hierarchy escape chart is promoted only when the minimum outer Kepler energy "
                "exceeds the interaction-remainder bound and numerical closure residual on an outward tail."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_future_tail_exchange_bound",
            passed=jacobi_future_tail.conditional_asymptotic_escape,
            metric="asymptotic_escape_margin",
            observed=jacobi_future_tail.asymptotic_escape_margin,
            threshold=0.0,
            interpretation=(
                "The finite hierarchy escape margin must dominate the declared future-tail quadrupole exchange "
                "integral before the escape cone is promoted to a conditional asymptotic theorem candidate."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_quadrupole_tail_assumptions",
            passed=jacobi_future_tail.assumptions_satisfied,
            metric="minimum_radial_velocity",
            observed=jacobi_future_tail.minimum_radial_velocity,
            threshold=0.0,
            interpretation=(
                "The future-tail theorem domain requires outward radial motion, sufficient hierarchy ratio, "
                "and resolved Jacobi splitting on the certified tail."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_inflated_margin_lower_bound",
            passed=jacobi_inflated_margin.validated_positive,
            metric="validated_margin_lower",
            observed=jacobi_inflated_margin.validated_margin_lower,
            threshold=0.0,
            interpretation=(
                "The conditional escape theorem candidate must keep a positive lower margin after "
                "predeclared scalar roundoff and state-scale inflation."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_self_consistent_radial_floor",
            passed=jacobi_self_consistent.self_consistent,
            metric="certified_radial_floor",
            observed=jacobi_self_consistent.certified_radial_floor,
            threshold=0.0,
            interpretation=(
                "The escape cone must not rely on an arbitrary outward-speed assumption: the observed radial "
                "floor must be compatible with the post-exchange energy lower bound."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_open_cone_radius",
            passed=jacobi_open_cone.open_cone_certified,
            metric="relative_state_radius",
            observed=jacobi_open_cone.relative_state_radius,
            threshold=1.0e-8,
            interpretation=(
                "The Jacobi escape result must certify a nonzero open tail-data neighborhood, "
                "not only a single sampled trajectory."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_terminal_tail_interval_reserve",
            passed=jacobi_tail_interval.interval_reserve_certified,
            metric="interval_margin_lower",
            observed=jacobi_tail_interval.interval_margin_lower,
            threshold=0.0,
            interpretation=(
                "The Jacobi escape cone must keep a positive margin after a finite-difference reserve over "
                "terminal tail-state perturbations; this is a bridge toward interval-enclosed trajectories."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_interval_tail_escape_margin",
            passed=jacobi_interval_tail.interval_escape_certified,
            metric="asymptotic_margin_lower",
            observed=jacobi_interval_tail.asymptotic_margin_lower,
            threshold=0.0,
            interpretation=(
                "The Jacobi escape cone must keep a positive asymptotic margin when outer energy, "
                "interaction remainder, radial floor, hierarchy ratio, and future exchange are evaluated "
                "by interval arithmetic on a nonzero tail-state box."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_interval_flow_tube",
            passed=jacobi_flow_tube.flow_tube_certified,
            metric="interval_escape_margin_lower",
            observed=jacobi_flow_tube.interval_escape_margin_lower,
            threshold=0.0,
            interpretation=(
                "The interval tail-state escape margin must survive an a posteriori flow tube whose radius "
                "is chosen from the sampled tail's trapezoid defect, and every sampled segment slope must "
                "lie inside the interval-evaluated Newtonian RHS on its expanded segment hull."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_interval_picard_flow",
            passed=jacobi_picard_flow.picard_flow_certified,
            metric="interval_escape_margin_lower",
            observed=jacobi_picard_flow.interval_escape_margin_lower,
            threshold=0.0,
            interpretation=(
                "The Jacobi tail must pass segment-wise interval Picard propagation: each propagated "
                "interval start box must map into an expanded substep tube with contraction factor below one, "
                "the propagated box must remain compatible with sampled endpoints, and the final Jacobi "
                "margin must survive the propagated endpoint enclosure radius."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_picard_interval_jacobian_contraction",
            passed=jacobi_picard_flow.maximum_observed_contraction < jacobi_picard_flow.target_contraction,
            metric="maximum_observed_contraction",
            observed=jacobi_picard_flow.maximum_observed_contraction,
            threshold=jacobi_picard_flow.target_contraction,
            interpretation=(
                "The segment-wise Picard validator must compute its contraction reserve from an interval "
                "Newtonian RHS Jacobian row-sum bound, not from a purely empirical segment-slope estimate."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_picard_resolution_crosscheck",
            passed=jacobi_resolution_crosscheck.certified,
            metric="minimum_picard_margin_lower",
            observed=jacobi_resolution_crosscheck.minimum_picard_margin_lower,
            threshold=0.0,
            interpretation=(
                "The representative Jacobi tail must remain Picard-certified after re-integrating it with "
                "predeclared sample counts and adaptive-integrator tolerances, reducing dependence on a "
                "single sampled trajectory."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_picard_resolution_margin_spread",
            passed=jacobi_resolution_crosscheck.maximum_margin_spread <= 2.0e-2,
            metric="maximum_margin_spread",
            observed=jacobi_resolution_crosscheck.maximum_margin_spread,
            threshold=2.0e-2,
            interpretation=(
                "Picard-certified Jacobi margins should not move enough under the resolution/tolerance sweep "
                "to suggest that the accepted cone is a solver-setting artifact."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_quadrupole_acceleration_envelope",
            passed=jacobi_quadrupole.quadrupole_bound_resolved,
            metric="maximum_bound_ratio",
            observed=jacobi_quadrupole.maximum_bound_ratio,
            threshold=1.0,
            interpretation=(
                "The declared quadrupole acceleration envelope must dominate the actual Jacobi perturbing "
                "acceleration on the certified tail."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_parameter_box_open_regime",
            passed=jacobi_parameter_box.box_certified,
            metric="minimum_relative_open_radius",
            observed=jacobi_parameter_box.minimum_relative_open_radius,
            threshold=1.0e-8,
            interpretation=(
                "The Jacobi escape theorem candidate must certify a nonzero open cone over a small "
                "predeclared parameter box, not only one representative trajectory."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_parameter_box_quadrupole_ratio",
            passed=jacobi_parameter_box.maximum_quadrupole_bound_ratio <= 1.0,
            metric="maximum_quadrupole_bound_ratio",
            observed=jacobi_parameter_box.maximum_quadrupole_bound_ratio,
            threshold=1.0,
            interpretation=(
                "The parameter-box Jacobi escape regime must keep the quadrupole perturbation envelope valid "
                "on every sampled case."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_parameter_grid_margin",
            passed=jacobi_parameter_box.grid_margin_certified,
            metric="minimum_grid_margin_lower",
            observed=jacobi_parameter_box.minimum_grid_margin_lower,
            threshold=0.0,
            interpretation=(
                "A refined 3x3x3 grid inside the declared parameter box must keep a positive inflated "
                "Jacobi escape margin."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_parameter_interval_box_margin",
            passed=jacobi_parameter_box.interval_box_certified,
            metric="interval_box_margin_lower",
            observed=jacobi_parameter_box.interval_box_margin_lower,
            threshold=0.0,
            interpretation=(
                "A finite-difference Lipschitz reserve over normalized parameter cells must leave a positive "
                "lower margin, moving the claim from grid points toward a continuum box certificate."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_parameter_interval_tail_margin",
            passed=jacobi_parameter_box.parameter_interval_tail_certified,
            metric="minimum_interval_tail_margin_lower",
            observed=jacobi_parameter_box.minimum_interval_tail_margin_lower,
            threshold=0.0,
            interpretation=(
                "Every sampled point in the predeclared parameter box must keep a positive interval-arithmetic "
                "tail escape margin, not only a floating or scalar-inflated margin."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_parameter_flow_tube_margin",
            passed=jacobi_parameter_box.parameter_flow_tube_certified,
            metric="minimum_flow_tube_margin_lower",
            observed=jacobi_parameter_box.minimum_flow_tube_margin_lower,
            threshold=0.0,
            interpretation=(
                "Every sampled point in the predeclared parameter box must keep a positive flow-level "
                "Jacobi tail margin under the a posteriori tube check or the stronger Picard propagation "
                "certificate."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_parameter_picard_flow_margin",
            passed=jacobi_parameter_box.parameter_picard_flow_certified,
            metric="minimum_picard_flow_margin_lower",
            observed=jacobi_parameter_box.minimum_picard_flow_margin_lower,
            threshold=0.0,
            interpretation=(
                "Every sampled point in the predeclared parameter box must pass segment-wise interval Picard "
                "propagation for the outgoing Jacobi tail."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_parameter_picard_interval_box_margin",
            passed=jacobi_parameter_box.parameter_picard_interval_box_certified,
            metric="picard_interval_box_margin_lower",
            observed=jacobi_parameter_box.picard_interval_box_margin_lower,
            threshold=0.0,
            interpretation=(
                "The continuum-style finite-difference parameter-cell reserve must remain positive after "
                "using the Picard-certified Jacobi tail margin, not only the scalar-inflated margin."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_parameter_picard_cell_centers",
            passed=jacobi_parameter_box.parameter_picard_cell_centers_certified,
            metric="picard_cell_center_reserve_margin_lower",
            observed=jacobi_parameter_box.picard_cell_center_reserve_margin_lower,
            threshold=0.0,
            interpretation=(
                "Every midpoint of the parameter cells must pass Picard-certified Jacobi escape, and "
                "the center margin must remain positive after subtracting the observed center-to-corner "
                "variation inside each cell."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_parameter_picard_face_centers",
            passed=jacobi_parameter_box.parameter_picard_face_centers_certified,
            metric="picard_face_center_reserve_margin_lower",
            observed=jacobi_parameter_box.picard_face_center_reserve_margin_lower,
            threshold=0.0,
            interpretation=(
                "Every face-center of the parameter cells must pass Picard-certified Jacobi escape, and "
                "the face-center margin must remain positive after subtracting the observed face-center-to-corner "
                "variation on that face."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_parameter_picard_edge_centers",
            passed=jacobi_parameter_box.parameter_picard_edge_centers_certified,
            metric="picard_edge_center_reserve_margin_lower",
            observed=jacobi_parameter_box.picard_edge_center_reserve_margin_lower,
            threshold=0.0,
            interpretation=(
                "Every edge-center of the parameter cells must pass Picard-certified Jacobi escape, and "
                "the edge-center margin must remain positive after subtracting the observed edge-center-to-corner "
                "variation on that edge."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_parameter_picard_half_grid_margin",
            passed=jacobi_parameter_box.parameter_picard_half_grid_certified,
            metric="picard_half_grid_interval_margin_lower",
            observed=jacobi_parameter_box.picard_half_grid_interval_margin_lower,
            threshold=0.0,
            interpretation=(
                "The full 5x5x5 Picard-certified half-grid must leave a positive continuum-style "
                "finite-difference reserve over its smaller subcells."
            ),
        ),
        PaperBenchmarkResult(
            name="jacobi_parameter_picard_half_grid_subcells",
            passed=jacobi_parameter_box.parameter_picard_half_grid_subcells_certified,
            metric="picard_half_grid_subcell_margin_lower",
            observed=jacobi_parameter_box.picard_half_grid_subcell_margin_lower,
            threshold=0.0,
            interpretation=(
                "Each of the 64 subcells in the Picard-certified 5x5x5 half-grid must keep a positive "
                "local finite-difference reserve from its own eight corners."
            ),
        ),
        PaperBenchmarkResult(
            name="levi_civita_collision_chart_certificate",
            passed=levi_civita_chart_resolved,
            metric="resolved_certificate_indicator",
            observed=1.0 if levi_civita_chart_resolved else 0.0,
            threshold=1.0,
            interpretation=(
                "Close-encounter promotion now requires a Levi-Civita binary chart that reconstructs the inertial "
                "relative state over the certified interval."
            ),
        ),
        PaperBenchmarkResult(
            name="levi_civita_regularized_rhs_certificate",
            passed=levi_civita_flow_defined,
            metric="resolved_certificate_indicator",
            observed=1.0 if levi_civita_flow_defined else 0.0,
            threshold=1.0,
            interpretation=(
                "The close-encounter chart must expose a perturbation-aware regularized-time RHS before "
                "finite residual and equivalence proofs can be attempted."
            ),
        ),
        PaperBenchmarkResult(
            name="levi_civita_non_synthetic_residual",
            passed=close_residual.residual_resolved,
            metric="maximum_finite_difference_residual",
            observed=close_residual.maximum_finite_difference_residual,
            threshold=close_residual.residual_threshold,
            interpretation=(
                "The regularized RHS must match finite-difference du'/ds on an integrated close-encounter "
                "trajectory, not only on synthetic static states."
            ),
        ),
        PaperBenchmarkResult(
            name="levi_civita_residual_grid",
            passed=close_residual_grid.pass_rate == 1.0,
            metric="maximum_grid_residual",
            observed=close_residual_grid.maximum_residual,
            threshold=close_residual_grid.residual_threshold,
            interpretation=(
                "The regularized RHS residual must remain below threshold over a predeclared grid of "
                "integrated close-encounter probes."
            ),
        ),
        PaperBenchmarkResult(
            name="levi_civita_local_equivalence",
            passed=levi_civita_equivalence_resolved and close_residual_grid.equivalence_pass_rate == 1.0,
            metric="maximum_equivalence_acceleration_residual",
            observed=close_residual_grid.maximum_equivalence_acceleration_residual,
            threshold=1.0e-7,
            interpretation=(
                "The regularized chart must reconstruct inertial position, velocity, and acceleration over the "
                "current close-encounter grid before an analytic equivalence theorem is attempted."
            ),
        ),
        PaperBenchmarkResult(
            name="levi_civita_near_collision_scaling",
            passed=near_collision.scaling_resolved,
            metric="maximum_normalized_residual",
            observed=near_collision.maximum_normalized_residual,
            threshold=near_collision.normalized_residual_threshold,
            interpretation=(
                "The regularized RHS residual should remain controlled as the certified binary separation "
                "is pushed toward smaller near-collision values."
            ),
        ),
        PaperBenchmarkResult(
            name="levi_civita_normalized_residual_slope",
            passed=near_collision.normalized_residual_scaling_exponent is not None
            and near_collision.normalized_residual_scaling_exponent >= near_collision.minimum_allowed_normalized_slope,
            metric="normalized_residual_loglog_slope",
            observed=near_collision.normalized_residual_scaling_exponent,
            threshold=near_collision.minimum_allowed_normalized_slope,
            interpretation=(
                "The normalized regularized RHS residual should not show a negative blow-up exponent over the "
                "near-collision scaling grid."
            ),
        ),
        PaperBenchmarkResult(
            name="levi_civita_tidal_perturbation_scaling",
            passed=near_collision.perturbation_ratio_scaling_exponent is not None
            and near_collision.perturbation_ratio_scaling_exponent
            >= near_collision.minimum_allowed_perturbation_ratio_slope
            and near_collision.maximum_perturbation_to_kepler_ratio is not None
            and near_collision.maximum_perturbation_to_kepler_ratio
            <= near_collision.maximum_allowed_perturbation_ratio,
            metric="perturbation_ratio_loglog_slope",
            observed=near_collision.perturbation_ratio_scaling_exponent,
            threshold=near_collision.minimum_allowed_perturbation_ratio_slope,
            interpretation=(
                "The third-body perturbation should shrink relative to the inner Kepler acceleration with "
                "approximately tidal scaling as binary separation decreases."
            ),
        ),
        PaperBenchmarkResult(
            name="levi_civita_tidal_constant_bound",
            passed=near_collision.tidal_bound_resolved,
            metric="tidal_constant_bound",
            observed=near_collision.tidal_constant_bound,
            threshold=near_collision.maximum_allowed_tidal_constant,
            interpretation=(
                "The finite near-collision grid should satisfy perturbation/Kepler <= C r^3 with an explicit "
                "declared constant C."
            ),
        ),
        PaperBenchmarkResult(
            name="levi_civita_tidal_lipschitz_bound",
            passed=near_collision.tidal_bound_resolved,
            metric="tidal_lipschitz_constant_bound",
            observed=near_collision.tidal_lipschitz_constant_bound,
            threshold=near_collision.maximum_allowed_tidal_lipschitz_constant,
            interpretation=(
                "A conservative Lipschitz tidal bound should dominate the observed third-body perturbation "
                "over the near-collision scaling grid."
            ),
        ),
        PaperBenchmarkResult(
            name="low_crossing_scattering_map_score",
            passed=low_scattering_score is not None and low_scattering_score > 0.25,
            metric="complexity_penalized_validation_score",
            observed=low_scattering_score,
            threshold=0.25,
            interpretation="The scattering-map model must retain positive held-out score before it can be considered physically relevant.",
        ),
        PaperBenchmarkResult(
            name="low_crossing_scattering_map_selection",
            passed=low_best_is_scattering,
            metric="selection_indicator",
            observed=low_scattering_selection_score if low_selection_score is None else low_selection_score,
            threshold=1.0,
            interpretation="The stronger breakthrough requirement: scattering-map must beat simpler competing low-crossing models.",
        ),
        PaperBenchmarkResult(
            name="best_low_crossing_model_validation",
            passed=low_best_score is not None and low_best_score > 0.25,
            metric="complexity_penalized_validation_score",
            observed=low_best_score,
            threshold=0.25,
            interpretation=f"Best low-crossing model in theorem suite: {low_best_target}.",
        ),
        PaperBenchmarkResult(
            name="best_high_crossing_model_validation",
            passed=high_best_score is not None and high_best_score > 0.25,
            metric="complexity_penalized_validation_score",
            observed=high_best_score,
            threshold=0.25,
            interpretation=f"Best high-crossing model in theorem suite: {high_best_target}.",
        ),
        PaperBenchmarkResult(
            name="best_hysteresis_width_model_validation",
            passed=hysteresis_best_score is not None and hysteresis_best_score > 0.25,
            metric="complexity_penalized_validation_score",
            observed=hysteresis_best_score,
            threshold=0.25,
            interpretation=f"Best hysteresis-width model in theorem suite: {hysteresis_best_target}.",
        ),
        PaperBenchmarkResult(
            name="transition_word_stability",
            passed=word_stability is not None and word_stability >= 0.5,
            metric="mean_normalized_word_similarity",
            observed=word_stability,
            threshold=0.5,
            interpretation="New-math candidate: chart words should remain grammar-stable across held-out flyby grids.",
        ),
        PaperBenchmarkResult(
            name="transition_word_nontriviality",
            passed=distinct_word_count >= 2,
            metric="distinct_chart_words",
            observed=float(distinct_word_count),
            threshold=2.0,
            interpretation="Chart-word stability is not meaningful if the whole sweep collapses to one trivial word.",
        ),
        PaperBenchmarkResult(
            name="transition_word_validation_diversity",
            passed=validation_distinct_word_count >= 2,
            metric="heldout_distinct_chart_words",
            observed=float(validation_distinct_word_count),
            threshold=2.0,
            interpretation="Held-out chart words must retain diversity before claiming a robust grammar law.",
        ),
        PaperBenchmarkResult(
            name="refined_transition_word_stability",
            passed=refined_word_stability is not None and refined_word_stability >= 0.5,
            metric="mean_normalized_refined_word_similarity",
            observed=refined_word_stability,
            threshold=0.5,
            interpretation="Refined physical chart words should remain grammar-stable across held-out flyby grids.",
        ),
        PaperBenchmarkResult(
            name="refined_transition_word_nontriviality",
            passed=refined_distinct_word_count >= 6,
            metric="distinct_refined_chart_words",
            observed=float(refined_distinct_word_count),
            threshold=6.0,
            interpretation="The refined chart alphabet must separate multiple physical word classes.",
        ),
        PaperBenchmarkResult(
            name="refined_transition_word_validation_diversity",
            passed=refined_validation_distinct_word_count >= 6,
            metric="heldout_distinct_refined_chart_words",
            observed=float(refined_validation_distinct_word_count),
            threshold=6.0,
            interpretation="Held-out refined chart words must remain diverse after physical binning.",
        ),
        PaperBenchmarkResult(
            name="return_word_stability",
            passed=return_word_stability is not None and return_word_stability >= 0.35,
            metric="mean_normalized_return_word_similarity",
            observed=return_word_stability,
            threshold=0.35,
            interpretation="Extremum-based return words should retain partial stability across held-out flyby grids.",
        ),
        PaperBenchmarkResult(
            name="return_word_validation_diversity",
            passed=return_validation_distinct_word_count >= 4,
            metric="heldout_distinct_return_words",
            observed=float(return_validation_distinct_word_count),
            threshold=4.0,
            interpretation="The return-word proxy must produce multiple held-out symbolic return classes.",
        ),
        PaperBenchmarkResult(
            name="high_crossing_grammar_outcome_validation",
            passed=high_grammar_score is not None and high_grammar_score > GRAMMAR_BRANCH_SCORE_THRESHOLD,
            metric="complexity_penalized_accuracy_gain",
            observed=high_grammar_score,
            threshold=GRAMMAR_BRANCH_SCORE_THRESHOLD,
            interpretation="High re-entry should be predictable as a grammar/scattering branch even when scalar boundary collapse fails.",
        ),
        PaperBenchmarkResult(
            name="hysteresis_width_grammar_outcome_validation",
            passed=hysteresis_grammar_score is not None and hysteresis_grammar_score > GRAMMAR_BRANCH_SCORE_THRESHOLD,
            metric="complexity_penalized_accuracy_gain",
            observed=hysteresis_grammar_score,
            threshold=GRAMMAR_BRANCH_SCORE_THRESHOLD,
            interpretation="Hysteresis width should be predictable as a grammar/phase branch rather than a scalar threshold.",
        ),
        PaperBenchmarkResult(
            name="grammar_branch_training_signal",
            passed=min_grammar_training_gain is not None and min_grammar_training_gain > 0.05,
            metric="minimum_discovery_loo_accuracy_gain",
            observed=min_grammar_training_gain,
            threshold=0.05,
            interpretation="Predeclared grammar branch laws must improve discovery leave-one-out accuracy before held-out promotion.",
        ),
        PaperBenchmarkResult(
            name="grammar_branch_validation_support",
            passed=min_grammar_validation_support is not None and min_grammar_validation_support >= 48.0,
            metric="minimum_heldout_branch_cases",
            observed=min_grammar_validation_support,
            threshold=48.0,
            interpretation="Grammar branch validation must use the wider held-out phase sweep.",
        ),
        PaperBenchmarkResult(
            name="grammar_branch_artifact_pass_rate",
            passed=grammar_artifact_pass_rate >= 0.75,
            metric="pass_rate_under_classifier_and_stride_perturbations",
            observed=grammar_artifact_pass_rate,
            threshold=0.75,
            interpretation="Predeclared branch laws should survive classifier-threshold and stride perturbations.",
        ),
        PaperBenchmarkResult(
            name="grammar_branch_artifact_min_score",
            passed=minimum_grammar_artifact_score is not None and minimum_grammar_artifact_score > 0.05,
            metric="minimum_complexity_penalized_score_under_perturbation",
            observed=minimum_grammar_artifact_score,
            threshold=0.05,
            interpretation="Branch-law scores should not collapse to zero under classifier-threshold and stride perturbations.",
        ),
        PaperBenchmarkResult(
            name="grammar_branch_artifact_certified_accuracy",
            passed=minimum_grammar_artifact_certified_accuracy is not None
            and minimum_grammar_artifact_certified_accuracy >= 0.95,
            metric="minimum_certified_accuracy_under_perturbation",
            observed=minimum_grammar_artifact_certified_accuracy,
            threshold=0.95,
            interpretation="Positive-margin branch predictions should remain nearly error-free under classifier and stride perturbations.",
        ),
        PaperBenchmarkResult(
            name="grammar_branch_artifact_certified_fraction",
            passed=minimum_grammar_artifact_certified_fraction is not None
            and minimum_grammar_artifact_certified_fraction >= 0.5,
            metric="minimum_certified_fraction_under_perturbation",
            observed=minimum_grammar_artifact_certified_fraction,
            threshold=0.5,
            interpretation="Classifier and stride perturbations should not collapse the certified branch region.",
        ),
        PaperBenchmarkResult(
            name="grammar_branch_artifact_mean_margin",
            passed=minimum_grammar_artifact_mean_margin is not None and minimum_grammar_artifact_mean_margin > 0.05,
            metric="minimum_mean_margin_under_perturbation",
            observed=minimum_grammar_artifact_mean_margin,
            threshold=0.05,
            interpretation="Classifier and stride perturbations should preserve a positive branch decision margin.",
        ),
        PaperBenchmarkResult(
            name="grammar_branch_artifact_negative_control_gap",
            passed=minimum_grammar_artifact_negative_control_gap is not None
            and minimum_grammar_artifact_negative_control_gap > 0.0,
            metric="minimum_score_gap_over_feature_only_or_permuted_word_controls",
            observed=minimum_grammar_artifact_negative_control_gap,
            threshold=0.0,
            interpretation="Branch grammar should beat feature-only and permuted-word controls under perturbation.",
        ),
        PaperBenchmarkResult(
            name="high_crossing_grammar_artifact_negative_control_gap",
            passed=minimum_grammar_artifact_high_negative_control_gap is not None
            and minimum_grammar_artifact_high_negative_control_gap > 0.0,
            metric="minimum_high_score_gap_over_negative_controls",
            observed=minimum_grammar_artifact_high_negative_control_gap,
            threshold=0.0,
            interpretation="High re-entry grammar should beat negative controls under classifier and stride perturbations.",
        ),
        PaperBenchmarkResult(
            name="hysteresis_width_grammar_artifact_negative_control_gap",
            passed=minimum_grammar_artifact_hysteresis_negative_control_gap is not None
            and minimum_grammar_artifact_hysteresis_negative_control_gap > 0.0,
            metric="minimum_hysteresis_score_gap_over_negative_controls",
            observed=minimum_grammar_artifact_hysteresis_negative_control_gap,
            threshold=0.0,
            interpretation="Hysteresis grammar should beat negative controls under classifier and stride perturbations.",
        ),
        PaperBenchmarkResult(
            name="grammar_branch_certified_accuracy",
            passed=min_grammar_certified_accuracy is not None and min_grammar_certified_accuracy >= 0.95,
            metric="minimum_margin_certified_validation_accuracy",
            observed=min_grammar_certified_accuracy,
            threshold=0.95,
            interpretation="Predictions with positive nearest-neighbor branch margin should be nearly error-free.",
        ),
        PaperBenchmarkResult(
            name="grammar_branch_certified_fraction",
            passed=min_grammar_certified_fraction is not None and min_grammar_certified_fraction >= 0.5,
            metric="minimum_positive_margin_fraction",
            observed=min_grammar_certified_fraction,
            threshold=0.5,
            interpretation="A branch law is weak if only a tiny fraction of held-out cases have positive decision margin.",
        ),
        PaperBenchmarkResult(
            name="grammar_branch_mean_margin",
            passed=min_grammar_mean_margin is not None and min_grammar_mean_margin > 0.05,
            metric="minimum_mean_decision_margin",
            observed=min_grammar_mean_margin,
            threshold=0.05,
            interpretation="Held-out branch decisions should have positive margin, not only tie-breaking accuracy.",
        ),
        PaperBenchmarkResult(
            name="grammar_branch_negative_control_gap",
            passed=min_grammar_negative_control_gap is not None and min_grammar_negative_control_gap > 0.0,
            metric="minimum_score_gap_over_feature_only_or_permuted_word_controls",
            observed=min_grammar_negative_control_gap,
            threshold=0.0,
            interpretation="Predeclared grammar branch laws must beat feature-only and permuted-word negative controls.",
        ),
        PaperBenchmarkResult(
            name="high_crossing_grammar_negative_control_gap",
            passed=high_grammar_negative_control_gap is not None and high_grammar_negative_control_gap > 0.0,
            metric="score_gap_over_feature_only_or_permuted_word_controls",
            observed=high_grammar_negative_control_gap,
            threshold=0.0,
            interpretation=(
                "High re-entry grammar must add information beyond smooth scattering features and permuted words."
            ),
        ),
        PaperBenchmarkResult(
            name="high_crossing_selected_branch_score",
            passed=high_selected_model != "permuted_word" and high_selected_score is not None and high_selected_score > 0.25,
            metric="best_branch_explanation_score",
            observed=high_selected_score,
            threshold=0.25,
            interpretation=(
                f"Selected high-crossing branch explanation: {high_selected_model}; "
                f"gap over next competitor: {high_selected_gap}."
            ),
        ),
        PaperBenchmarkResult(
            name="high_crossing_selected_branch_is_feature",
            passed=high_selected_model == "feature_only",
            metric="feature_selection_indicator",
            observed=1.0 if high_selected_model == "feature_only" else 0.0,
            threshold=1.0,
            interpretation="High re-entry currently selects smooth scattering features over chart grammar.",
        ),
        PaperBenchmarkResult(
            name="hysteresis_width_grammar_negative_control_gap",
            passed=hysteresis_grammar_negative_control_gap is not None
            and hysteresis_grammar_negative_control_gap > 0.0,
            metric="score_gap_over_feature_only_or_permuted_word_controls",
            observed=hysteresis_grammar_negative_control_gap,
            threshold=0.0,
            interpretation="Hysteresis grammar must add information beyond adiabaticity features and permuted words.",
        ),
        PaperBenchmarkResult(
            name="hysteresis_width_selected_branch_score",
            passed=hysteresis_selected_model == "grammar"
            and hysteresis_selected_score is not None
            and hysteresis_selected_score > GRAMMAR_BRANCH_SCORE_THRESHOLD,
            metric="best_branch_explanation_score",
            observed=hysteresis_selected_score,
            threshold=GRAMMAR_BRANCH_SCORE_THRESHOLD,
            interpretation=(
                f"Selected hysteresis branch explanation: {hysteresis_selected_model}; "
                f"gap over next competitor: {hysteresis_selected_gap}."
            ),
        ),
        PaperBenchmarkResult(
            name="hysteresis_width_selected_branch_is_grammar",
            passed=hysteresis_selected_model == "grammar",
            metric="grammar_selection_indicator",
            observed=1.0 if hysteresis_selected_model == "grammar" else 0.0,
            threshold=1.0,
            interpretation="Hysteresis currently selects chart grammar over feature-only and permuted-word controls.",
        ),
    )


def _branch_explanation_selection(row: dict[str, object] | None) -> tuple[str, float | None, float | None]:
    if row is None:
        return "none", None, None
    scores = {
        "grammar": _optional_float(row.get("complexity_penalized_validation_score")),
        "feature_only": _optional_float(row.get("feature_only_complexity_penalized_score")),
        "permuted_word": _optional_float(row.get("permuted_word_complexity_penalized_score")),
    }
    finite_scores = {name: score for name, score in scores.items() if score is not None}
    if not finite_scores:
        return "none", None, None
    selected_model, selected_score = max(finite_scores.items(), key=lambda item: item[1])
    competitors = [score for name, score in finite_scores.items() if name != selected_model]
    gap = None if not competitors else float(selected_score - max(competitors))
    return selected_model, float(selected_score), gap


def _jacobi_escape_benchmark() -> JacobiEscapeCertificate:
    library = OrbitLibrary()
    scenario = library.general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=360,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )
    return jacobi_escape_sufficient_condition(scenario.system, trajectory, inner_pair=(0, 1))


def _jacobi_future_tail_benchmark() -> JacobiFutureTailBound:
    library = OrbitLibrary()
    scenario = library.general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=360,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )
    return jacobi_future_tail_bound(scenario.system, trajectory, inner_pair=(0, 1))


def _jacobi_inflated_margin_benchmark() -> JacobiInflatedMarginCertificate:
    library = OrbitLibrary()
    scenario = library.general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=360,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )
    return jacobi_inflated_margin_certificate(scenario.system, trajectory, inner_pair=(0, 1))


def _jacobi_self_consistent_benchmark() -> JacobiSelfConsistentConeCertificate:
    library = OrbitLibrary()
    scenario = library.general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=360,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )
    return jacobi_self_consistent_escape_cone(scenario.system, trajectory, inner_pair=(0, 1))


def _jacobi_open_cone_benchmark() -> JacobiOpenConeCertificate:
    library = OrbitLibrary()
    scenario = library.general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=360,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )
    return jacobi_open_escape_cone_certificate(scenario.system, trajectory, inner_pair=(0, 1))


def _jacobi_tail_interval_benchmark() -> JacobiTailIntervalReserveCertificate:
    library = OrbitLibrary()
    scenario = library.general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=360,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )
    return jacobi_tail_interval_reserve_certificate(scenario.system, trajectory, inner_pair=(0, 1))


def _jacobi_interval_tail_benchmark() -> JacobiIntervalTailCertificate:
    library = OrbitLibrary()
    scenario = library.general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=360,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )
    return jacobi_interval_escape_certificate(scenario.system, trajectory, inner_pair=(0, 1))


def _jacobi_flow_tube_benchmark() -> JacobiIntervalFlowTubeCertificate:
    library = OrbitLibrary()
    scenario = library.general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=360,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )
    return jacobi_interval_flow_tube_certificate(scenario.system, trajectory, inner_pair=(0, 1))


def _jacobi_picard_flow_benchmark() -> JacobiIntervalPicardFlowCertificate:
    library = OrbitLibrary()
    scenario = library.general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=360,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )
    return jacobi_interval_picard_flow_certificate(scenario.system, trajectory, inner_pair=(0, 1))


def _jacobi_resolution_crosscheck_benchmark() -> JacobiResolutionCrosscheckResult:
    library = OrbitLibrary()
    cases = (
        (500, 1.0e-9, 1.0e-11),
        (520, 1.0e-9, 1.0e-11),
        (500, 1.0e-10, 1.0e-12),
        (500, 1.0e-8, 1.0e-10),
    )
    certificates = []
    sample_counts = []
    for samples, rtol, atol in cases:
        scenario = library.general_hierarchical_flyby(
            intruder_velocity=(0.8, 1.6),
            duration=8.0,
            samples=samples,
        )
        trajectory = AdaptiveIntegrator(rtol=rtol, atol=atol).integrate(
            scenario.system,
            scenario.t_span,
            scenario.initial_state,
            t_eval=scenario.t_eval,
        )
        certificates.append(jacobi_interval_picard_flow_certificate(scenario.system, trajectory, inner_pair=(0, 1)))
        sample_counts.append(samples)
    margins = [certificate.interval_escape_margin_lower for certificate in certificates]
    pass_count = sum(1 for certificate in certificates if certificate.picard_flow_certified)
    maximum_margin_spread = float(max(margins) - min(margins))
    certified = bool(pass_count == len(certificates) and min(margins) > 0.0 and maximum_margin_spread <= 2.0e-2)
    return JacobiResolutionCrosscheckResult(
        case_count=len(certificates),
        pass_rate=float(pass_count / len(certificates)),
        minimum_picard_margin_lower=float(min(margins)),
        maximum_margin_spread=maximum_margin_spread,
        maximum_tube_radius=float(max(certificate.tube_radius for certificate in certificates)),
        maximum_propagated_endpoint_radius=float(
            max(certificate.maximum_propagated_endpoint_radius for certificate in certificates)
        ),
        maximum_observed_contraction=float(
            max(certificate.maximum_observed_contraction for certificate in certificates)
        ),
        minimum_sample_count=min(sample_counts),
        maximum_sample_count=max(sample_counts),
        certified=certified,
    )


def _jacobi_quadrupole_benchmark() -> JacobiQuadrupoleAccelerationCertificate:
    library = OrbitLibrary()
    scenario = library.general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=360,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )
    return jacobi_quadrupole_acceleration_certificate(scenario.system, trajectory, inner_pair=(0, 1))


def _jacobi_parameter_box_benchmark(paper: bool = False) -> JacobiParameterBoxResult:
    library = OrbitLibrary()
    integrator = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11)
    rows = []
    margins_by_index = {}
    picard_margins_by_index = {}
    picard_half_grid_margins = {}
    masses = (0.18, 0.20, 0.22)
    speeds = (1.60, 1.625, 1.65)
    phases = (0.0, 0.1, 0.2)
    samples = 520
    for mass_index, intruder_mass in enumerate(masses):
        for speed_index, intruder_speed_y in enumerate(speeds):
            for phase_index, binary_phase in enumerate(phases):
                scenario = library.general_hierarchical_flyby(
                    intruder_mass=intruder_mass,
                    intruder_velocity=(0.8, intruder_speed_y),
                    binary_phase=binary_phase,
                    duration=8.0,
                    samples=samples,
                )
                trajectory = integrator.integrate(
                    scenario.system,
                    scenario.t_span,
                    scenario.initial_state,
                    t_eval=scenario.t_eval,
                )
                open_cone = jacobi_open_escape_cone_certificate(scenario.system, trajectory, inner_pair=(0, 1))
                quadrupole = jacobi_quadrupole_acceleration_certificate(scenario.system, trajectory, inner_pair=(0, 1))
                inflated = jacobi_inflated_margin_certificate(scenario.system, trajectory, inner_pair=(0, 1))
                interval_tail = jacobi_interval_escape_certificate(scenario.system, trajectory, inner_pair=(0, 1))
                flow_tube = jacobi_interval_flow_tube_certificate(scenario.system, trajectory, inner_pair=(0, 1))
                picard_flow = jacobi_interval_picard_flow_certificate(scenario.system, trajectory, inner_pair=(0, 1))
                rows.append((open_cone, quadrupole, inflated, interval_tail, flow_tube, picard_flow))
                margins_by_index[(mass_index, speed_index, phase_index)] = inflated.validated_margin_lower
                picard_margins_by_index[(mass_index, speed_index, phase_index)] = picard_flow.interval_escape_margin_lower
                picard_half_grid_margins[(2 * mass_index, 2 * speed_index, 2 * phase_index)] = (
                    picard_flow.interval_escape_margin_lower
                )
    cell_center_margins: list[float] = []
    cell_center_pass_count = 0
    cell_center_variations: list[float] = []
    if paper:
        for mass_index in range(len(masses) - 1):
            for speed_index in range(len(speeds) - 1):
                for phase_index in range(len(phases) - 1):
                    intruder_mass = 0.5 * (masses[mass_index] + masses[mass_index + 1])
                    intruder_speed_y = 0.5 * (speeds[speed_index] + speeds[speed_index + 1])
                    binary_phase = 0.5 * (phases[phase_index] + phases[phase_index + 1])
                    scenario = library.general_hierarchical_flyby(
                        intruder_mass=intruder_mass,
                        intruder_velocity=(0.8, intruder_speed_y),
                        binary_phase=binary_phase,
                        duration=8.0,
                        samples=samples,
                    )
                    trajectory = integrator.integrate(
                        scenario.system,
                        scenario.t_span,
                        scenario.initial_state,
                        t_eval=scenario.t_eval,
                    )
                    picard_flow = jacobi_interval_picard_flow_certificate(scenario.system, trajectory, inner_pair=(0, 1))
                    cell_center_margins.append(picard_flow.interval_escape_margin_lower)
                    picard_half_grid_margins[(2 * mass_index + 1, 2 * speed_index + 1, 2 * phase_index + 1)] = (
                        picard_flow.interval_escape_margin_lower
                    )
                    if picard_flow.picard_flow_certified:
                        cell_center_pass_count += 1
                    corner_margins = [
                        picard_margins_by_index[(mass_index + dm, speed_index + dv, phase_index + dp)]
                        for dm in (0, 1)
                        for dv in (0, 1)
                        for dp in (0, 1)
                    ]
                    cell_center_variations.append(
                        max(abs(picard_flow.interval_escape_margin_lower - corner) for corner in corner_margins)
                    )
    face_center_margins: list[float] = []
    face_center_pass_count = 0
    face_center_variations: list[float] = []
    face_center_keys = [
        key
        for key in np.ndindex(5, 5, 5)
        if sum(component % 2 == 1 for component in key) == 2
    ]
    for key in (face_center_keys if paper else []):
        mass_position, speed_position, phase_position = key
        intruder_mass = _half_grid_value(masses, mass_position)
        intruder_speed_y = _half_grid_value(speeds, speed_position)
        binary_phase = _half_grid_value(phases, phase_position)
        scenario = library.general_hierarchical_flyby(
            intruder_mass=intruder_mass,
            intruder_velocity=(0.8, intruder_speed_y),
            binary_phase=binary_phase,
            duration=8.0,
            samples=samples,
        )
        trajectory = integrator.integrate(
            scenario.system,
            scenario.t_span,
            scenario.initial_state,
            t_eval=scenario.t_eval,
        )
        picard_flow = jacobi_interval_picard_flow_certificate(scenario.system, trajectory, inner_pair=(0, 1))
        face_center_margins.append(picard_flow.interval_escape_margin_lower)
        picard_half_grid_margins[key] = picard_flow.interval_escape_margin_lower
        if picard_flow.picard_flow_certified:
            face_center_pass_count += 1
        face_corner_margins = [
            picard_margins_by_index[corner]
            for corner in _face_center_corner_indices(key)
        ]
        face_center_variations.append(
            max(abs(picard_flow.interval_escape_margin_lower - corner) for corner in face_corner_margins)
        )
    edge_center_margins: list[float] = []
    edge_center_pass_count = 0
    edge_center_variations: list[float] = []
    edge_center_keys = [
        key
        for key in np.ndindex(5, 5, 5)
        if sum(component % 2 == 1 for component in key) == 1
    ]
    for key in (edge_center_keys if paper else []):
        mass_position, speed_position, phase_position = key
        intruder_mass = _half_grid_value(masses, mass_position)
        intruder_speed_y = _half_grid_value(speeds, speed_position)
        binary_phase = _half_grid_value(phases, phase_position)
        scenario = library.general_hierarchical_flyby(
            intruder_mass=intruder_mass,
            intruder_velocity=(0.8, intruder_speed_y),
            binary_phase=binary_phase,
            duration=8.0,
            samples=samples,
        )
        trajectory = integrator.integrate(
            scenario.system,
            scenario.t_span,
            scenario.initial_state,
            t_eval=scenario.t_eval,
        )
        picard_flow = jacobi_interval_picard_flow_certificate(scenario.system, trajectory, inner_pair=(0, 1))
        edge_center_margins.append(picard_flow.interval_escape_margin_lower)
        picard_half_grid_margins[key] = picard_flow.interval_escape_margin_lower
        if picard_flow.picard_flow_certified:
            edge_center_pass_count += 1
        edge_corner_margins = [
            picard_margins_by_index[corner]
            for corner in _edge_center_corner_indices(key)
        ]
        edge_center_variations.append(
            max(abs(picard_flow.interval_escape_margin_lower - corner) for corner in edge_corner_margins)
        )
    pass_count = sum(
        1
        for open_cone, quadrupole, inflated, _interval_tail, _flow_tube, _picard_flow in rows
        if open_cone.open_cone_certified and quadrupole.quadrupole_bound_resolved and inflated.validated_positive
    )
    interval_tail_pass_count = sum(
        1
        for _open_cone, _quadrupole, _inflated, interval_tail, _flow_tube, _picard_flow in rows
        if interval_tail.interval_escape_certified
    )
    flow_tube_pass_count = sum(
        1
        for _open_cone, _quadrupole, _inflated, _interval_tail, flow_tube, _picard_flow in rows
        if flow_tube.flow_tube_certified
    )
    picard_flow_pass_count = sum(
        1
        for _open_cone, _quadrupole, _inflated, _interval_tail, _flow_tube, picard_flow in rows
        if picard_flow.picard_flow_certified
    )
    minimum_radius = min(
        open_cone.relative_state_radius
        for open_cone, _quadrupole, _inflated, _interval_tail, _flow_tube, _picard_flow in rows
    )
    minimum_margin = min(
        inflated.validated_margin_lower
        for _open_cone, _quadrupole, inflated, _interval_tail, _flow_tube, _picard_flow in rows
    )
    minimum_interval_tail_margin = min(
        interval_tail.asymptotic_margin_lower
        for _open_cone, _quadrupole, _inflated, interval_tail, _flow_tube, _picard_flow in rows
    )
    minimum_flow_tube_margin = min(
        flow_tube.interval_escape_margin_lower
        for _open_cone, _quadrupole, _inflated, _interval_tail, flow_tube, _picard_flow in rows
    )
    minimum_picard_flow_margin = min(
        picard_flow.interval_escape_margin_lower
        for _open_cone, _quadrupole, _inflated, _interval_tail, _flow_tube, picard_flow in rows
    )
    maximum_flow_tube_radius = max(
        flow_tube.tube_radius
        for _open_cone, _quadrupole, _inflated, _interval_tail, flow_tube, _picard_flow in rows
    )
    maximum_picard_contraction = max(
        picard_flow.maximum_observed_contraction
        for _open_cone, _quadrupole, _inflated, _interval_tail, _flow_tube, picard_flow in rows
    )
    maximum_ratio = max(
        quadrupole.maximum_bound_ratio
        for _open_cone, quadrupole, _inflated, _interval_tail, _flow_tube, _picard_flow in rows
    )
    lipschitz_bound = _normalized_parameter_lipschitz_bound(margins_by_index)
    picard_lipschitz_bound = _normalized_parameter_lipschitz_bound(picard_margins_by_index)
    normalized_cell_radius = float(np.sqrt(3.0) * 0.5)
    interval_box_margin = float(minimum_margin - lipschitz_bound * normalized_cell_radius)
    picard_interval_box_margin = float(minimum_picard_flow_margin - picard_lipschitz_bound * normalized_cell_radius)
    minimum_cell_center_margin = float(min(cell_center_margins)) if cell_center_margins else float("inf")
    cell_center_variation_bound = float(max(cell_center_variations)) if cell_center_variations else float("inf")
    cell_center_reserve_margin = float(minimum_cell_center_margin - cell_center_variation_bound)
    minimum_face_center_margin = float(min(face_center_margins)) if face_center_margins else float("inf")
    face_center_variation_bound = float(max(face_center_variations)) if face_center_variations else float("inf")
    face_center_reserve_margin = float(minimum_face_center_margin - face_center_variation_bound)
    minimum_edge_center_margin = float(min(edge_center_margins)) if edge_center_margins else float("inf")
    edge_center_variation_bound = float(max(edge_center_variations)) if edge_center_variations else float("inf")
    edge_center_reserve_margin = float(minimum_edge_center_margin - edge_center_variation_bound)
    minimum_half_grid_margin = float(min(picard_half_grid_margins.values())) if picard_half_grid_margins else float("inf")
    half_grid_lipschitz_bound = _normalized_half_grid_lipschitz_bound(picard_half_grid_margins) if paper else 0.0
    half_grid_cell_radius = float(np.sqrt(3.0) * 0.25)
    half_grid_interval_margin = float(minimum_half_grid_margin - half_grid_lipschitz_bound * half_grid_cell_radius)
    half_grid_subcell_margins = (
        _half_grid_subcell_margin_lowers(picard_half_grid_margins) if paper else ()
    )
    minimum_half_grid_subcell_margin = (
        float(min(half_grid_subcell_margins)) if half_grid_subcell_margins else float("-inf")
    )
    return JacobiParameterBoxResult(
        case_count=len(rows),
        pass_rate=float(pass_count / len(rows)),
        minimum_relative_open_radius=float(minimum_radius),
        minimum_grid_margin_lower=float(minimum_margin),
        finite_difference_lipschitz_bound=float(lipschitz_bound),
        normalized_cell_radius=normalized_cell_radius,
        interval_box_margin_lower=interval_box_margin,
        maximum_quadrupole_bound_ratio=float(maximum_ratio),
        interval_tail_pass_rate=float(interval_tail_pass_count / len(rows)),
        minimum_interval_tail_margin_lower=float(minimum_interval_tail_margin),
        flow_tube_pass_rate=float(flow_tube_pass_count / len(rows)),
        minimum_flow_tube_margin_lower=float(minimum_flow_tube_margin),
        maximum_flow_tube_radius=float(maximum_flow_tube_radius),
        picard_flow_pass_rate=float(picard_flow_pass_count / len(rows)),
        minimum_picard_flow_margin_lower=float(minimum_picard_flow_margin),
        maximum_picard_contraction=float(maximum_picard_contraction),
        picard_finite_difference_lipschitz_bound=float(picard_lipschitz_bound),
        picard_interval_box_margin_lower=picard_interval_box_margin,
        picard_cell_center_count=len(cell_center_margins),
        picard_cell_center_pass_rate=float(cell_center_pass_count / len(cell_center_margins)) if cell_center_margins else 0.0,
        minimum_picard_cell_center_margin_lower=minimum_cell_center_margin,
        picard_cell_center_variation_bound=cell_center_variation_bound,
        picard_cell_center_reserve_margin_lower=cell_center_reserve_margin,
        picard_face_center_count=len(face_center_margins),
        picard_face_center_pass_rate=float(face_center_pass_count / len(face_center_margins)) if face_center_margins else 0.0,
        minimum_picard_face_center_margin_lower=minimum_face_center_margin,
        picard_face_center_variation_bound=face_center_variation_bound,
        picard_face_center_reserve_margin_lower=face_center_reserve_margin,
        picard_edge_center_count=len(edge_center_margins),
        picard_edge_center_pass_rate=float(edge_center_pass_count / len(edge_center_margins)) if edge_center_margins else 0.0,
        minimum_picard_edge_center_margin_lower=minimum_edge_center_margin,
        picard_edge_center_variation_bound=edge_center_variation_bound,
        picard_edge_center_reserve_margin_lower=edge_center_reserve_margin,
        picard_half_grid_count=len(picard_half_grid_margins),
        picard_half_grid_lipschitz_bound=float(half_grid_lipschitz_bound),
        picard_half_grid_interval_margin_lower=half_grid_interval_margin,
        picard_half_grid_subcell_count=len(half_grid_subcell_margins),
        picard_half_grid_subcell_margin_lower=minimum_half_grid_subcell_margin,
        box_certified=pass_count == len(rows) and minimum_radius >= 1.0e-8 and maximum_ratio <= 1.0,
        grid_margin_certified=minimum_margin > 0.0,
        interval_box_certified=interval_box_margin > 0.0,
        parameter_interval_tail_certified=interval_tail_pass_count == len(rows) and minimum_interval_tail_margin > 0.0,
        parameter_flow_tube_certified=(
            minimum_flow_tube_margin > 0.0
            and (flow_tube_pass_count == len(rows) or picard_flow_pass_count == len(rows))
        ),
        parameter_picard_flow_certified=picard_flow_pass_count == len(rows) and minimum_picard_flow_margin > 0.0,
        parameter_picard_interval_box_certified=picard_interval_box_margin > 0.0,
        parameter_picard_cell_centers_certified=(
            paper
            and
            cell_center_pass_count == len(cell_center_margins)
            and minimum_cell_center_margin > 0.0
            and cell_center_reserve_margin > 0.0
        ),
        parameter_picard_face_centers_certified=(
            paper
            and
            face_center_pass_count == len(face_center_margins)
            and minimum_face_center_margin > 0.0
            and face_center_reserve_margin > 0.0
        ),
        parameter_picard_edge_centers_certified=(
            paper
            and
            edge_center_pass_count == len(edge_center_margins)
            and minimum_edge_center_margin > 0.0
            and edge_center_reserve_margin > 0.0
        ),
        parameter_picard_half_grid_certified=(
            paper
            and
            len(picard_half_grid_margins) == 125
            and half_grid_interval_margin > 0.0
        ),
        parameter_picard_half_grid_subcells_certified=(
            paper
            and
            len(half_grid_subcell_margins) == 64
            and minimum_half_grid_subcell_margin > 0.0
        ),
    )


def _normalized_parameter_lipschitz_bound(margins_by_index: dict[tuple[int, int, int], float]) -> float:
    axis_slopes = []
    for axis in range(3):
        maximum_axis_slope = 0.0
        for index, margin in margins_by_index.items():
            neighbor = list(index)
            neighbor[axis] += 1
            neighbor_key = tuple(neighbor)
            if neighbor_key in margins_by_index:
                maximum_axis_slope = max(maximum_axis_slope, abs(margins_by_index[neighbor_key] - margin))
        axis_slopes.append(maximum_axis_slope)
    return float(1.25 * np.linalg.norm(axis_slopes))


def _normalized_half_grid_lipschitz_bound(margins_by_index: dict[tuple[int, int, int], float]) -> float:
    axis_slopes = []
    half_step = 0.5
    for axis in range(3):
        maximum_axis_slope = 0.0
        for index, margin in margins_by_index.items():
            neighbor = list(index)
            neighbor[axis] += 1
            neighbor_key = tuple(neighbor)
            if neighbor_key in margins_by_index:
                maximum_axis_slope = max(
                    maximum_axis_slope,
                    abs(margins_by_index[neighbor_key] - margin) / half_step,
                )
        axis_slopes.append(maximum_axis_slope)
    return float(1.25 * np.linalg.norm(axis_slopes))


def _half_grid_subcell_margin_lowers(margins_by_index: dict[tuple[int, int, int], float]) -> tuple[float, ...]:
    radius = float(np.sqrt(3.0) * 0.25)
    margin_lowers = []
    for base in np.ndindex(4, 4, 4):
        corner_indices = tuple(
            (base[0] + dx, base[1] + dy, base[2] + dz)
            for dx in (0, 1)
            for dy in (0, 1)
            for dz in (0, 1)
        )
        if not all(index in margins_by_index for index in corner_indices):
            continue
        corner_margins = {index: margins_by_index[index] for index in corner_indices}
        minimum_corner_margin = min(corner_margins.values())
        local_lipschitz = _local_half_grid_lipschitz_bound(corner_margins)
        margin_lowers.append(float(minimum_corner_margin - local_lipschitz * radius))
    return tuple(margin_lowers)


def _local_half_grid_lipschitz_bound(corner_margins: dict[tuple[int, int, int], float]) -> float:
    axis_slopes = []
    half_step = 0.5
    for axis in range(3):
        maximum_axis_slope = 0.0
        for index, margin in corner_margins.items():
            neighbor = list(index)
            neighbor[axis] += 1
            neighbor_key = tuple(neighbor)
            if neighbor_key in corner_margins:
                maximum_axis_slope = max(
                    maximum_axis_slope,
                    abs(corner_margins[neighbor_key] - margin) / half_step,
                )
        axis_slopes.append(maximum_axis_slope)
    return float(1.25 * np.linalg.norm(axis_slopes))


def _half_grid_value(values: tuple[float, ...], position: int) -> float:
    if position % 2 == 0:
        return float(values[position // 2])
    lower = position // 2
    return float(0.5 * (values[lower] + values[lower + 1]))


def _face_center_corner_indices(key: tuple[int, int, int]) -> tuple[tuple[int, int, int], ...]:
    odd_axes = [axis for axis, component in enumerate(key) if component % 2 == 1]
    if len(odd_axes) != 2:
        raise ValueError("face-center key must have exactly two half-grid coordinates")
    corner_indices = []
    for first_offset in (0, 1):
        for second_offset in (0, 1):
            corner = []
            offsets = {odd_axes[0]: first_offset, odd_axes[1]: second_offset}
            for axis, component in enumerate(key):
                if component % 2 == 0:
                    corner.append(component // 2)
                else:
                    corner.append(component // 2 + offsets[axis])
            corner_indices.append(tuple(corner))
    return tuple(corner_indices)


def _edge_center_corner_indices(key: tuple[int, int, int]) -> tuple[tuple[int, int, int], ...]:
    odd_axes = [axis for axis, component in enumerate(key) if component % 2 == 1]
    if len(odd_axes) != 1:
        raise ValueError("edge-center key must have exactly one half-grid coordinate")
    odd_axis = odd_axes[0]
    corners = []
    for offset in (0, 1):
        corner = []
        for axis, component in enumerate(key):
            if component % 2 == 0:
                corner.append(component // 2)
            elif axis == odd_axis:
                corner.append(component // 2 + offset)
            else:
                raise ValueError("unexpected half-grid coordinate")
        corners.append(tuple(corner))
    return tuple(corners)


def _theorem_candidates(benchmarks: tuple[PaperBenchmarkResult, ...]) -> tuple[TheoremCandidate, ...]:
    benchmark_by_name = {benchmark.name: benchmark for benchmark in benchmarks}
    jacobi_split_passed = benchmark_by_name["jacobi_energy_split_residual"].passed
    jacobi_escape_passed = benchmark_by_name["jacobi_escape_sufficient_condition"].passed
    jacobi_future_tail_passed = benchmark_by_name["jacobi_future_tail_exchange_bound"].passed
    jacobi_tail_assumptions_passed = benchmark_by_name["jacobi_quadrupole_tail_assumptions"].passed
    jacobi_inflated_margin_passed = benchmark_by_name["jacobi_inflated_margin_lower_bound"].passed
    jacobi_self_consistent_passed = benchmark_by_name["jacobi_self_consistent_radial_floor"].passed
    jacobi_open_cone_passed = benchmark_by_name["jacobi_open_cone_radius"].passed
    jacobi_interval_tail_passed = benchmark_by_name["jacobi_interval_tail_escape_margin"].passed
    jacobi_flow_tube_passed = benchmark_by_name["jacobi_interval_flow_tube"].passed
    jacobi_picard_flow_passed = benchmark_by_name["jacobi_interval_picard_flow"].passed
    jacobi_interval_jacobian_passed = benchmark_by_name["jacobi_picard_interval_jacobian_contraction"].passed
    jacobi_resolution_crosscheck_passed = (
        benchmark_by_name["jacobi_picard_resolution_crosscheck"].passed
        and benchmark_by_name["jacobi_picard_resolution_margin_spread"].passed
    )
    jacobi_quadrupole_passed = benchmark_by_name["jacobi_quadrupole_acceleration_envelope"].passed
    jacobi_parameter_box_passed = (
        benchmark_by_name["jacobi_parameter_box_open_regime"].passed
        and benchmark_by_name["jacobi_parameter_box_quadrupole_ratio"].passed
        and benchmark_by_name["jacobi_parameter_grid_margin"].passed
        and benchmark_by_name["jacobi_parameter_interval_box_margin"].passed
        and benchmark_by_name["jacobi_parameter_interval_tail_margin"].passed
        and benchmark_by_name["jacobi_parameter_flow_tube_margin"].passed
        and benchmark_by_name["jacobi_parameter_picard_flow_margin"].passed
        and benchmark_by_name["jacobi_parameter_picard_interval_box_margin"].passed
        and benchmark_by_name["jacobi_parameter_picard_cell_centers"].passed
        and benchmark_by_name["jacobi_parameter_picard_face_centers"].passed
        and benchmark_by_name["jacobi_parameter_picard_edge_centers"].passed
        and benchmark_by_name["jacobi_parameter_picard_half_grid_margin"].passed
        and benchmark_by_name["jacobi_parameter_picard_half_grid_subcells"].passed
    )
    scattering_score_passed = benchmark_by_name["low_crossing_scattering_map_score"].passed
    scattering_selection_passed = benchmark_by_name["low_crossing_scattering_map_selection"].passed
    low_best_passed = benchmark_by_name["best_low_crossing_model_validation"].passed
    high_best_passed = benchmark_by_name["best_high_crossing_model_validation"].passed
    hysteresis_best_passed = benchmark_by_name["best_hysteresis_width_model_validation"].passed
    refined_word_stability_passed = benchmark_by_name["refined_transition_word_stability"].passed
    refined_word_nontriviality_passed = benchmark_by_name["refined_transition_word_nontriviality"].passed
    refined_word_validation_diversity_passed = benchmark_by_name["refined_transition_word_validation_diversity"].passed
    return_word_passed = benchmark_by_name["return_word_stability"].passed
    return_word_diversity_passed = benchmark_by_name["return_word_validation_diversity"].passed
    high_grammar_passed = benchmark_by_name["high_crossing_grammar_outcome_validation"].passed
    hysteresis_grammar_passed = benchmark_by_name["hysteresis_width_grammar_outcome_validation"].passed
    grammar_training_signal_passed = benchmark_by_name["grammar_branch_training_signal"].passed
    grammar_artifact_passed = benchmark_by_name["grammar_branch_artifact_pass_rate"].passed
    grammar_margin_passed = (
        benchmark_by_name["grammar_branch_certified_accuracy"].passed
        and benchmark_by_name["grammar_branch_mean_margin"].passed
        and benchmark_by_name["grammar_branch_artifact_certified_accuracy"].passed
        and benchmark_by_name["grammar_branch_artifact_mean_margin"].passed
    )
    high_grammar_negative_control_passed = (
        benchmark_by_name["high_crossing_grammar_negative_control_gap"].passed
        and benchmark_by_name["high_crossing_grammar_artifact_negative_control_gap"].passed
    )
    hysteresis_grammar_negative_control_passed = (
        benchmark_by_name["hysteresis_width_grammar_negative_control_gap"].passed
        and benchmark_by_name["hysteresis_width_grammar_artifact_negative_control_gap"].passed
    )
    high_selected_feature_passed = (
        benchmark_by_name["high_crossing_selected_branch_score"].passed
        and benchmark_by_name["high_crossing_selected_branch_is_feature"].passed
    )
    hysteresis_selected_grammar_passed = (
        benchmark_by_name["hysteresis_width_selected_branch_score"].passed
        and benchmark_by_name["hysteresis_width_selected_branch_is_grammar"].passed
    )
    coverage_passed = benchmark_by_name["regime_coverage_smoke"].passed
    levi_civita_passed = benchmark_by_name["levi_civita_collision_chart_certificate"].passed
    levi_civita_flow_passed = benchmark_by_name["levi_civita_regularized_rhs_certificate"].passed
    levi_civita_residual_passed = benchmark_by_name["levi_civita_non_synthetic_residual"].passed
    levi_civita_grid_passed = benchmark_by_name["levi_civita_residual_grid"].passed
    levi_civita_equivalence_passed = benchmark_by_name["levi_civita_local_equivalence"].passed
    levi_civita_near_collision_passed = benchmark_by_name["levi_civita_near_collision_scaling"].passed
    levi_civita_slope_passed = benchmark_by_name["levi_civita_normalized_residual_slope"].passed
    levi_civita_tidal_passed = benchmark_by_name["levi_civita_tidal_perturbation_scaling"].passed
    levi_civita_tidal_bound_passed = benchmark_by_name["levi_civita_tidal_constant_bound"].passed
    levi_civita_lipschitz_bound_passed = benchmark_by_name["levi_civita_tidal_lipschitz_bound"].passed
    artifact_passed = benchmark_by_name["classifier_artifact_bound"].passed
    return (
        TheoremCandidate(
            name="Jacobi Escape Cone Theorem Candidate",
            claim=(
                "For a declared hierarchical three-body tail, if the exact Jacobi energy split is resolved, "
                "the outer Kepler energy has a positive margin over a rigorous interaction-remainder bound, "
                "and the outer radius is moving outward throughout the certified tail, then the trajectory lies "
                "inside a one-sided escape/scattering cone for that hierarchy."
            ),
            scope=(
                "Newtonian three-body states with one chosen inner binary, no collision on the certified tail, "
                "and outer separation larger than the binary scale; currently a finite-time certificate."
            ),
            novelty_target=(
                "Replace visual escape labels and fitted escape classifiers with a Hamiltonian split plus "
                "explicit remainder margin that can be upgraded into an interval or asymptotic proof."
            ),
            proven=bool(
                jacobi_split_passed
                and jacobi_escape_passed
                and jacobi_future_tail_passed
                and jacobi_tail_assumptions_passed
                and jacobi_self_consistent_passed
                and jacobi_open_cone_passed
                and jacobi_interval_tail_passed
                and jacobi_flow_tube_passed
                and jacobi_picard_flow_passed
                and jacobi_interval_jacobian_passed
                and jacobi_resolution_crosscheck_passed
                and jacobi_quadrupole_passed
                and jacobi_parameter_box_passed
            ),
            obligations=(
                ProofObligation(
                    "exact_jacobi_hamiltonian_split",
                    "partial" if jacobi_split_passed else "failing",
                    benchmark_by_name["jacobi_energy_split_residual"].interpretation,
                    None if jacobi_split_passed else "Energy split residual blocks the claimed coordinate chart.",
                ),
                ProofObligation(
                    "finite_tail_escape_margin",
                    "partial" if jacobi_escape_passed else "failing",
                    benchmark_by_name["jacobi_escape_sufficient_condition"].interpretation,
                    None if jacobi_escape_passed else "The tested escape tail lacks a positive certified margin.",
                ),
                ProofObligation(
                    "asymptotic_escape_extension",
                    "partial" if jacobi_future_tail_passed and jacobi_tail_assumptions_passed else "failing",
                    (
                        "A quadrupole-cancelled future-tail exchange integral is now bounded under explicit "
                        "tail hypotheses, and the benchmark requires the asymptotic margin to remain positive."
                    ),
                    None
                    if jacobi_future_tail_passed and jacobi_tail_assumptions_passed
                    else "The future-tail bound or its declared assumptions do not yet pass the benchmark.",
                ),
                ProofObligation(
                    "self_consistent_radial_floor",
                    "partial" if jacobi_self_consistent_passed else "failing",
                    benchmark_by_name["jacobi_self_consistent_radial_floor"].interpretation,
                    None
                    if jacobi_self_consistent_passed
                    else "The escape cone still relies on an unsupported radial-speed floor.",
                ),
                ProofObligation(
                    "open_escape_cone_radius",
                    "partial" if jacobi_open_cone_passed else "failing",
                    benchmark_by_name["jacobi_open_cone_radius"].interpretation,
                    None
                    if jacobi_open_cone_passed
                    else "The certificate is still zero-measure and does not define an open regime.",
                ),
                ProofObligation(
                    "interval_tail_escape_margin",
                    "partial" if jacobi_interval_tail_passed else "failing",
                    benchmark_by_name["jacobi_interval_tail_escape_margin"].interpretation,
                    None
                    if jacobi_interval_tail_passed
                    else "The local tail-data box does not keep a positive interval-enclosed asymptotic margin.",
                ),
                ProofObligation(
                    "a_posteriori_flow_tube",
                    "partial" if jacobi_flow_tube_passed else "failing",
                    benchmark_by_name["jacobi_interval_flow_tube"].interpretation,
                    None
                    if jacobi_flow_tube_passed
                    else "The expanded tail-state tube does not yet enclose the sampled segment slopes in the interval RHS.",
                ),
                ProofObligation(
                    "interval_picard_flow_propagation",
                    "partial" if jacobi_picard_flow_passed and jacobi_interval_jacobian_passed else "failing",
                    benchmark_by_name["jacobi_interval_picard_flow"].interpretation,
                    None
                    if jacobi_picard_flow_passed and jacobi_interval_jacobian_passed
                    else "The tail does not yet pass segment-wise interval Picard propagation.",
                ),
                ProofObligation(
                    "interval_jacobian_contraction_bound",
                    "partial" if jacobi_interval_jacobian_passed else "failing",
                    benchmark_by_name["jacobi_picard_interval_jacobian_contraction"].interpretation,
                    None
                    if jacobi_interval_jacobian_passed
                    else "The Picard contraction reserve is not below the declared target under the interval Jacobian bound.",
                ),
                ProofObligation(
                    "resolution_tolerance_crosscheck",
                    "partial" if jacobi_resolution_crosscheck_passed else "failing",
                    (
                        benchmark_by_name["jacobi_picard_resolution_crosscheck"].interpretation
                        + " "
                        + benchmark_by_name["jacobi_picard_resolution_margin_spread"].interpretation
                    ),
                    None
                    if jacobi_resolution_crosscheck_passed
                    else "The Picard-certified margin is not yet stable across the declared resolution/tolerance sweep.",
                ),
                ProofObligation(
                    "quadrupole_acceleration_envelope",
                    "partial" if jacobi_quadrupole_passed else "failing",
                    benchmark_by_name["jacobi_quadrupole_acceleration_envelope"].interpretation,
                    None
                    if jacobi_quadrupole_passed
                    else "The declared C_Q envelope does not dominate the sampled perturbing acceleration.",
                ),
                ProofObligation(
                    "parameter_box_open_regime",
                    "partial" if jacobi_parameter_box_passed else "failing",
                    benchmark_by_name["jacobi_parameter_box_open_regime"].interpretation,
                    None
                    if jacobi_parameter_box_passed
                    else "The certified escape cone has not survived the predeclared parameter box.",
                ),
                ProofObligation(
                    "interval_arithmetic_remainder",
                    "partial"
                    if (
                        jacobi_interval_tail_passed
                        and jacobi_flow_tube_passed
                        and jacobi_picard_flow_passed
                        and jacobi_interval_jacobian_passed
                        and jacobi_resolution_crosscheck_passed
                    )
                    else "failing",
                    (
                        "The interaction, outer-energy, radial-floor, hierarchy, and future-tail margins are "
                        "now interval-enclosed on a nonzero tail-state box, and the tail box is tied to an "
                        "a posteriori interval RHS flow tube plus segment-wise Picard propagation. The "
                        "representative Picard margin also survives a predeclared resolution/tolerance sweep. "
                        "This is still not a CAPD-grade validated integrator over arbitrary initial boxes."
                    ),
                    None
                    if (
                        jacobi_interval_tail_passed
                        and jacobi_flow_tube_passed
                        and jacobi_picard_flow_passed
                        and jacobi_interval_jacobian_passed
                        and jacobi_resolution_crosscheck_passed
                    )
                    else "The positive margin, interval flow-tube certificate, or Picard propagation certificate fails.",
                ),
            ),
        ),
        TheoremCandidate(
            name="Reduced Shape-Scattering Atlas Conjecture",
            claim=(
                "On noncollision intervals of the planar Newtonian three-body problem, a finite atlas built from "
                "shape-scale coordinates, hierarchy charts, collision blow-up diagnostics, gateway linearization, "
                "and scattering maps can assign each sampled state a local explanatory regime with explicit validity controls."
            ),
            scope="Planar Newtonian three-body trajectories away from unresolved collision singularities; currently empirical.",
            novelty_target="Unify local analytic charts and transition/scattering validation around one reduced state object.",
            proven=bool(
                coverage_passed
                and artifact_passed
                and levi_civita_passed
                and levi_civita_flow_passed
                and levi_civita_residual_passed
                and levi_civita_grid_passed
                and levi_civita_equivalence_passed
                and levi_civita_near_collision_passed
                and levi_civita_slope_passed
                and levi_civita_tidal_passed
                and levi_civita_tidal_bound_passed
                and levi_civita_lipschitz_bound_passed
            ),
            obligations=(
                ProofObligation(
                    "reduced_state_coverage",
                    "partial" if coverage_passed else "failing",
                    "Regime smoke suite covers hierarchy, Lagrange neck, collision boundary, and escape boundary.",
                    None if coverage_passed else "Add missing chart probes and classifier migration.",
                ),
                ProofObligation(
                    "classifier_stability",
                    "partial" if artifact_passed else "failing",
                    "Classifier threshold/stride perturbation changes transition count by at most one in the flyby smoke benchmark.",
                    None if artifact_passed else "Transition labels may be classifier artifacts.",
                ),
                ProofObligation(
                    "regularized_collision_flow",
                    (
                        "partial"
                        if (
                            levi_civita_passed
                            and levi_civita_flow_passed
                            and levi_civita_residual_passed
                            and levi_civita_grid_passed
                            and levi_civita_equivalence_passed
                            and levi_civita_near_collision_passed
                            and levi_civita_slope_passed
                            and levi_civita_tidal_passed
                            and levi_civita_tidal_bound_passed
                            and levi_civita_lipschitz_bound_passed
                        )
                        else "open"
                    ),
                    (
                        "Levi-Civita binary chart reconstruction and perturbation-aware regularized RHS are "
                        "certified, the current integrated residual grid passes, and local inertial equivalence "
                        "residuals are controlled through the current near-collision scaling grid. The third-body "
                        "perturbation also satisfies explicit finite and Lipschitz tidal bounds relative to the "
                        "inner Kepler core. A collision manifold theorem remains open."
                    ),
                    "Turn the finite near-collision scaling certificate into an analytic limiting bound.",
                ),
            ),
        ),
        TheoremCandidate(
            name="Hierarchy Exit Scattering Coordinate Conjecture",
            claim=(
                "For the declared hierarchical flyby family, the low hierarchy-exit boundary is better collapsed by "
                "trajectory-measured periapsis phase, periapsis distance, and deflection angle than by instantaneous geometry alone."
            ),
            scope="Declared hierarchical flyby grid with held-out masses, impact parameters, speeds, and binary phases.",
            novelty_target="Replace phase proxy thresholds with measured scattering coordinates in a transition law.",
            proven=False,
            obligations=(
                ProofObligation(
                    "heldout_scattering_validation",
                    "partial" if scattering_score_passed else "failing",
                    "The theorem suite requires positive complexity-penalized held-out score for low_crossing_scattering_map.",
                    None if scattering_score_passed else "Current scattering map does not survive held-out validation.",
                ),
                ProofObligation(
                    "competitive_model_selection",
                    "partial" if scattering_selection_passed else "failing",
                    "The theorem suite also requires the scattering-map model to beat simpler low-crossing competitors.",
                    None if scattering_selection_passed else "Scattering coordinates may be useful but are not yet the selected explanation.",
                ),
                ProofObligation(
                    "large_sweep_bootstrap",
                    "open",
                    "Current sample count is too small for a theorem-level claim.",
                    "Run wider sweeps with bootstrap confidence intervals and publish raw artifacts.",
                ),
                ProofObligation(
                    "analytic_bound",
                    "open",
                    "No perturbation-theoretic error bound links tidal impulse and scattering coordinates yet.",
                    "Derive a local bound in a restricted mass/impact/energy regime.",
                ),
            ),
        ),
        TheoremCandidate(
            name="Impulse-Exchange Hierarchy Boundary Conjecture",
            claim=(
                "For the declared hierarchical flyby family, hierarchy exit and re-entry boundaries are better treated as "
                "accumulated encounter effects than as instantaneous geometric thresholds."
            ),
            scope="Declared hierarchical flyby grid with held-out masses, impact parameters, speeds, and binary phases.",
            novelty_target="Promote the robust negative result against instantaneous thresholds into a positive impulse/exchange boundary law.",
            proven=False,
            obligations=(
                ProofObligation(
                    "low_boundary_best_model_validation",
                    "partial" if low_best_passed else "failing",
                    benchmark_by_name["best_low_crossing_model_validation"].interpretation,
                    None if low_best_passed else "No low-boundary model survives theorem-suite validation.",
                ),
                ProofObligation(
                    "high_boundary_best_model_validation",
                    "partial" if high_best_passed else "failing",
                    benchmark_by_name["best_high_crossing_model_validation"].interpretation,
                    None if high_best_passed else "No high-boundary model survives theorem-suite validation.",
                ),
                ProofObligation(
                    "hysteresis_width_model_validation",
                    "partial" if hysteresis_best_passed else "failing",
                    benchmark_by_name["best_hysteresis_width_model_validation"].interpretation,
                    None if hysteresis_best_passed else "Width/memory model does not yet survive theorem-suite validation.",
                ),
                ProofObligation(
                    "instantaneous_threshold_rejection",
                    "open",
                    "The theorem suite should explicitly compare against instantaneous-only thresholds over wider grids.",
                    "Add a formal likelihood-ratio or bootstrap dominance test against instantaneous models.",
                ),
                ProofObligation(
                    "analytic_impulse_bound",
                    "open",
                    "No analytic perturbation bound has been derived for the observed impulse/exchange scaling.",
                    "Derive a restricted-regime bound from tidal forcing and inner-binary action variation.",
                ),
            ),
        ),
        TheoremCandidate(
            name="Chart-Word Grammar Conjecture",
            claim=(
                "When scalar boundary collapse fails, the re-entry structure of a three-body trajectory may still be "
                "described by stable words over the chart alphabet and their transition grammar."
            ),
            scope=(
                "Current implementation tests coarse words, refined physical words, and extremum-based return words "
                "over the hierarchical flyby theorem-suite grids."
            ),
            novelty_target="Move from scalar thresholds to an algebra of chart words, reversal defects, primitive periods, and grammar rank.",
            proven=False,
            obligations=(
                ProofObligation(
                    "heldout_word_stability",
                    "partial" if refined_word_stability_passed and refined_word_nontriviality_passed else "failing",
                    benchmark_by_name["refined_transition_word_stability"].interpretation,
                    None
                    if refined_word_stability_passed and refined_word_nontriviality_passed
                    else "Chart words are not stable or are trivial across the current held-out grids.",
                ),
                ProofObligation(
                    "coarse_alphabet_artifact_check",
                    "partial" if refined_word_validation_diversity_passed else "failing",
                    benchmark_by_name["refined_transition_word_validation_diversity"].interpretation,
                    None
                    if refined_word_validation_diversity_passed
                    else "Current held-out flyby words collapse to too few symbols; refine the alphabet before promoting this.",
                ),
                ProofObligation(
                    "grammar_invariant_bound",
                    "open",
                    "No analytic invariant or symbolic-dynamics bound has been derived for chart words.",
                    "Define admissible grammar transformations and prove stability in a restricted regime.",
                ),
                ProofObligation(
                    "return_map_connection",
                    "partial" if return_word_passed and return_word_diversity_passed else "failing",
                    benchmark_by_name["return_word_stability"].interpretation,
                    None
                    if return_word_passed and return_word_diversity_passed
                    else "The current return-word proxy is not stable or diverse enough.",
                ),
                ProofObligation(
                    "reentry_branch_prediction",
                    "partial"
                    if high_grammar_passed and grammar_training_signal_passed and grammar_artifact_passed and grammar_margin_passed
                    and high_grammar_negative_control_passed
                    else "failing",
                    benchmark_by_name["high_crossing_grammar_outcome_validation"].interpretation,
                    None
                    if high_grammar_passed
                    and grammar_training_signal_passed
                    and grammar_artifact_passed
                    and grammar_margin_passed
                    and high_grammar_negative_control_passed
                    else (
                        "High re-entry branch lacks held-out validation, discovery training signal, artifact robustness, "
                        "decision margin, or negative-control separation."
                    ),
                ),
                ProofObligation(
                    "hysteresis_branch_prediction",
                    "partial"
                    if hysteresis_grammar_passed
                    and grammar_training_signal_passed
                    and grammar_artifact_passed
                    and grammar_margin_passed
                    and hysteresis_grammar_negative_control_passed
                    else "failing",
                    benchmark_by_name["hysteresis_width_grammar_outcome_validation"].interpretation,
                    None
                    if hysteresis_grammar_passed
                    and grammar_training_signal_passed
                    and grammar_artifact_passed
                    and grammar_margin_passed
                    and hysteresis_grammar_negative_control_passed
                    else (
                        "Hysteresis branch lacks held-out validation, discovery training signal, artifact robustness, "
                        "decision margin, or negative-control separation."
                    ),
                ),
            ),
        ),
        TheoremCandidate(
            name="Split Branch Explanation Conjecture",
            claim=(
                "In a hierarchical three-body flyby, different transition branches may require different explanatory "
                "coordinates: high re-entry is currently best explained by smooth scattering features, while "
                "hysteresis is currently best explained by chart-word memory."
            ),
            scope="Declared hierarchical flyby theorem-suite grid with held-out masses, impact parameters, speeds, and phases.",
            novelty_target=(
                "Replace a single universal transition law with a falsifiable branch-wise selector over feature, "
                "grammar, and randomized-control explanations."
            ),
            proven=False,
            obligations=(
                ProofObligation(
                    "high_reentry_feature_selection",
                    "partial" if high_selected_feature_passed else "failing",
                    benchmark_by_name["high_crossing_selected_branch_score"].interpretation,
                    None
                    if high_selected_feature_passed
                    else "High re-entry does not yet select a non-control feature explanation with sufficient score.",
                ),
                ProofObligation(
                    "hysteresis_grammar_selection",
                    "partial" if hysteresis_selected_grammar_passed else "failing",
                    benchmark_by_name["hysteresis_width_selected_branch_score"].interpretation,
                    None
                    if hysteresis_selected_grammar_passed
                    else "Hysteresis does not yet select grammar over feature-only and permuted-word controls.",
                ),
                ProofObligation(
                    "selector_generalization",
                    "open",
                    "The selector is tested only on the current flyby family.",
                    "Extend branch selection to Lagrange-neck, close-encounter, and escape-scattering regimes.",
                ),
                ProofObligation(
                    "selector_error_bound",
                    "open",
                    "No theorem-level error bound exists for the branch-wise selector.",
                    "Derive branch-local perturbation bounds and finite-sample confidence intervals.",
                ),
            ),
        ),
    )


def _word_rows_by_name(summary: object, *, field: str = "chart_word") -> dict[str, dict[str, object]]:
    return {
        f"{row['intruder_mass']}:{row['impact_parameter']}:{row['intruder_speed_y']}:{row['binary_phase']}": row
        for row in summary.get("rows", [])
        if field in row
    }


def _word_stability_score(
    discovery_words: dict[str, dict[str, object]],
    validation_words: dict[str, dict[str, object]],
    *,
    field: str = "chart_word",
) -> float | None:
    if not discovery_words or not validation_words:
        return None
    discovery_strings = [str(row[field]) for row in discovery_words.values()]
    validation_strings = [str(row[field]) for row in validation_words.values()]
    scores = []
    for validation in validation_strings:
        validation_symbols = tuple(part.strip() for part in validation.split("->") if part.strip())
        best = 0.0
        for discovery in discovery_strings:
            discovery_symbols = tuple(part.strip() for part in discovery.split("->") if part.strip())
            distance = _string_word_distance(discovery_symbols, validation_symbols)
            denominator = max(len(discovery_symbols), len(validation_symbols), 1)
            best = max(best, 1.0 - distance / denominator)
        scores.append(best)
    return float(sum(scores) / len(scores))


def _distinct_word_count(rows: tuple[dict[str, object], ...], *, field: str = "chart_word") -> int:
    return len({str(row[field]) for row in rows if field in row})


def _string_word_distance(first: tuple[str, ...], second: tuple[str, ...]) -> int:
    class _Word:
        def __init__(self, symbols: tuple[str, ...]) -> None:
            self.symbols = symbols

        @property
        def length(self) -> int:
            return len(self.symbols)

    return word_distance(_Word(first), _Word(second))


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
