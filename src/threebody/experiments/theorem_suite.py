from __future__ import annotations

from dataclasses import dataclass

from ..analysis import word_distance
from .flyby_sweep import HierarchicalFlybySweep
from .research_checks import ClassifierArtifactStudy, IntegratorComparisonStudy, KnownBenchmarkSuite, RegimeProbeSuite


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
    theorem_candidates: tuple[TheoremCandidate, ...]
    benchmarks: tuple[PaperBenchmarkResult, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "theorem_candidates": [candidate.as_dict() for candidate in self.theorem_candidates],
            "benchmarks": [benchmark.as_dict() for benchmark in self.benchmarks],
        }


@dataclass(slots=True)
class TheoremSuite:
    """Reproducible theorem/proof-obligation/benchmark harness."""

    def run(self) -> TheoremSuiteResult:
        artifact_rows = ClassifierArtifactStudy().run(duration=8.0, samples=500)
        integrator = IntegratorComparisonStudy().run()
        benchmarks = KnownBenchmarkSuite().run()
        regimes = RegimeProbeSuite().run()
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
        benchmark_rows = _paper_benchmarks(artifact_rows, integrator, benchmarks, regimes, flyby_summary)
        candidates = _theorem_candidates(benchmark_rows)
        return TheoremSuiteResult(theorem_candidates=candidates, benchmarks=benchmark_rows)


def _paper_benchmarks(
    artifact_rows: object,
    integrator: object,
    known_benchmarks: object,
    regimes: object,
    flyby_summary: dict[str, object],
) -> tuple[PaperBenchmarkResult, ...]:
    transition_counts = [row.transition_count for row in artifact_rows]
    baseline_count = transition_counts[0]
    artifact_spread = max(abs(count - baseline_count) for count in transition_counts)
    known_pass_rate = sum(1 for row in known_benchmarks if row.passed) / len(known_benchmarks)
    regime_names = {row.name for row in regimes}
    reduced_regime_hints = {
        str(row.extra.get("reduced_regime_hint"))
        for row in regimes
        if "reduced_regime_hint" in row.extra
    }
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
    min_grammar_training_gain = None if not grammar_training_gains else float(min(grammar_training_gains))
    min_grammar_validation_support = None if not grammar_validation_supports else float(min(grammar_validation_supports))
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
            passed=high_grammar_score is not None and high_grammar_score > 0.2,
            metric="complexity_penalized_accuracy_gain",
            observed=high_grammar_score,
            threshold=0.2,
            interpretation="High re-entry should be predictable as a grammar/scattering branch even when scalar boundary collapse fails.",
        ),
        PaperBenchmarkResult(
            name="hysteresis_width_grammar_outcome_validation",
            passed=hysteresis_grammar_score is not None and hysteresis_grammar_score > 0.2,
            metric="complexity_penalized_accuracy_gain",
            observed=hysteresis_grammar_score,
            threshold=0.2,
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
    )


def _theorem_candidates(benchmarks: tuple[PaperBenchmarkResult, ...]) -> tuple[TheoremCandidate, ...]:
    benchmark_by_name = {benchmark.name: benchmark for benchmark in benchmarks}
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
    coverage_passed = benchmark_by_name["regime_coverage_smoke"].passed
    artifact_passed = benchmark_by_name["classifier_artifact_bound"].passed
    return (
        TheoremCandidate(
            name="Reduced Shape-Scattering Atlas Conjecture",
            claim=(
                "On noncollision intervals of the planar Newtonian three-body problem, a finite atlas built from "
                "shape-scale coordinates, hierarchy charts, collision blow-up diagnostics, gateway linearization, "
                "and scattering maps can assign each sampled state a local explanatory regime with explicit validity controls."
            ),
            scope="Planar Newtonian three-body trajectories away from unresolved collision singularities; currently empirical.",
            novelty_target="Unify local analytic charts and transition/scattering validation around one reduced state object.",
            proven=False,
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
                    "open",
                    "McGehee-style diagnostics exist, but no regularized flow or collision manifold theorem is implemented.",
                    "Implement Levi-Civita/McGehee regularized dynamics and prove coordinate equivalence.",
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
                    "partial" if high_grammar_passed and grammar_training_signal_passed else "failing",
                    benchmark_by_name["high_crossing_grammar_outcome_validation"].interpretation,
                    None
                    if high_grammar_passed and grammar_training_signal_passed
                    else "High re-entry branch lacks held-out validation or discovery training signal.",
                ),
                ProofObligation(
                    "hysteresis_branch_prediction",
                    "partial" if hysteresis_grammar_passed and grammar_training_signal_passed else "failing",
                    benchmark_by_name["hysteresis_width_grammar_outcome_validation"].interpretation,
                    None
                    if hysteresis_grammar_passed and grammar_training_signal_passed
                    else "Hysteresis branch lacks held-out validation or discovery training signal.",
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
