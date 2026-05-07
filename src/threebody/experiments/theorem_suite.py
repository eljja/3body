from __future__ import annotations

from dataclasses import dataclass

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
            validation_binary_phases=(0.7853981633974483, 2.356194490192345),
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
    low_scattering = next(
        (
            row
            for row in best_models
            if str(row["target"]).startswith("low_") and "scattering_map" in str(row["target"])
        ),
        None,
    )
    low_score = None if low_scattering is None else float(low_scattering["complexity_penalized_validation_score"])
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
            name="low_crossing_scattering_map_validation",
            passed=low_score is not None and low_score > 0.25,
            metric="complexity_penalized_validation_score",
            observed=low_score,
            threshold=0.25,
            interpretation="The only current breakthrough candidate: trajectory-measured scattering coordinates improve low hierarchy-exit prediction.",
        ),
    )


def _theorem_candidates(benchmarks: tuple[PaperBenchmarkResult, ...]) -> tuple[TheoremCandidate, ...]:
    benchmark_by_name = {benchmark.name: benchmark for benchmark in benchmarks}
    scattering_passed = benchmark_by_name["low_crossing_scattering_map_validation"].passed
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
                    "partial" if scattering_passed else "failing",
                    "The smoke theorem suite requires positive complexity-penalized held-out score for low_crossing_scattering_map.",
                    None if scattering_passed else "Current scattering map does not survive held-out validation.",
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
    )
