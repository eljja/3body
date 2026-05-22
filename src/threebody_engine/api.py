from __future__ import annotations

from typing import Literal

from threebody.analysis import (
    AnalysisAtlas,
    ChartWordMarkovChain,
    ChartWordMarkovBaselineComparison,
    ChartWordMarkovBootstrapComparison,
    ChartWordMarkovValidation,
    bootstrap_markov_baseline_comparison,
    JacobiIntervalPicardFlowCertificate,
    JacobiPicardTuningCertificate,
    compare_markov_chain_to_independent_baseline,
    hysteresis_markov_chain_from_reports,
    jacobi_interval_picard_flow_certificate,
    jacobi_picard_tuning_certificate,
    return_map_word_from_reports,
    validate_markov_chain,
)
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator
from threebody.types import Scenario, TrajectoryResult

ReferenceScenario = Literal["figure-eight", "hierarchical-flyby", "restricted-l4", "restricted-l5"]


def integrate_reference_scenario(
    scenario: ReferenceScenario = "hierarchical-flyby",
    *,
    periods: float = 0.25,
    samples: int = 240,
    rtol: float = 1.0e-9,
    atol: float = 1.0e-11,
) -> tuple[Scenario, TrajectoryResult]:
    """Integrate a built-in benchmark scenario through the engine API."""

    library = OrbitLibrary()
    reference = _reference_scenario(library, scenario, periods=periods, samples=samples)
    trajectory = AdaptiveIntegrator(rtol=rtol, atol=atol).integrate(
        reference.system,
        reference.t_span,
        reference.initial_state,
        t_eval=reference.t_eval,
    )
    return reference, trajectory


def certify_jacobi_escape(
    trajectory: TrajectoryResult,
    scenario: Scenario,
    *,
    inner_pair: tuple[int, int] = (0, 1),
    target_contraction: float = 0.35,
) -> JacobiIntervalPicardFlowCertificate:
    """Run the Picard-certified Jacobi escape certificate for a solved trajectory."""

    return jacobi_interval_picard_flow_certificate(
        scenario.system,
        trajectory,
        inner_pair=inner_pair,
        target_contraction=target_contraction,
    )


def tune_jacobi_picard(
    trajectory: TrajectoryResult,
    scenario: Scenario,
    *,
    inner_pair: tuple[int, int] = (0, 1),
    target_contraction: float = 0.35,
) -> JacobiPicardTuningCertificate:
    """Auto-select Picard settings for a solved trajectory."""

    return jacobi_picard_tuning_certificate(
        scenario.system,
        trajectory,
        inner_pair=inner_pair,
        target_contraction=target_contraction,
    )


def certify_jacobi_escape_report(
    trajectory: TrajectoryResult,
    scenario: Scenario,
    *,
    inner_pair: tuple[int, int] = (0, 1),
    target_contraction: float = 0.35,
) -> dict[str, object]:
    """Return a JSON-ready Picard tuning and escape certificate report."""

    tuning = tune_jacobi_picard(
        trajectory,
        scenario,
        inner_pair=inner_pair,
        target_contraction=target_contraction,
    )
    certificate = certify_jacobi_escape(
        trajectory,
        scenario,
        inner_pair=inner_pair,
        target_contraction=target_contraction,
    )
    return {
        "scenario": scenario.name,
        "picard_tuning": tuning.as_dict(),
        "jacobi_escape_certificate": certificate.as_dict(),
    }


def build_hysteresis_markov_chain(
    scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    *,
    periods: float = 8.0,
    samples: int = 240,
    stride: int = 20,
    coordinate: str = "hierarchy_perturbation_strength",
) -> ChartWordMarkovChain:
    """Build a symbolic Markov model from return-map chart words."""

    atlas = AnalysisAtlas()
    reports_by_name = {}
    for scenario_name in scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports_by_name[scenario.name] = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
    return hysteresis_markov_chain_from_reports(reports_by_name, coordinate=coordinate)


def validate_hysteresis_markov_chain(
    train_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    validation_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    *,
    periods: float = 8.0,
    samples: int = 240,
    stride: int = 20,
    coordinate: str = "hierarchy_perturbation_strength",
) -> tuple[ChartWordMarkovChain, ChartWordMarkovValidation]:
    """Fit and validate a hysteresis symbolic Markov model."""

    chain = build_hysteresis_markov_chain(
        train_scenarios,
        periods=periods,
        samples=samples,
        stride=stride,
        coordinate=coordinate,
    )
    atlas = AnalysisAtlas()
    heldout_words = []
    for scenario_name in validation_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        heldout_words.append(return_map_word_from_reports(reports, coordinate=coordinate))
    return chain, validate_markov_chain(chain, tuple(heldout_words))


def compare_hysteresis_markov_to_baseline(
    train_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    validation_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    *,
    periods: float = 8.0,
    samples: int = 240,
    stride: int = 20,
    coordinate: str = "hierarchy_perturbation_strength",
) -> tuple[ChartWordMarkovChain, ChartWordMarkovBaselineComparison]:
    """Fit hysteresis Markov dynamics and compare against an independent baseline."""

    atlas = AnalysisAtlas()
    training_words = []
    reports_by_name = {}
    for scenario_name in train_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        reports_by_name[scenario.name] = reports
        training_words.append(return_map_word_from_reports(reports, coordinate=coordinate))
    chain = hysteresis_markov_chain_from_reports(reports_by_name, coordinate=coordinate)
    validation_words = []
    for scenario_name in validation_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        validation_words.append(return_map_word_from_reports(reports, coordinate=coordinate))
    return chain, compare_markov_chain_to_independent_baseline(
        chain,
        tuple(training_words),
        tuple(validation_words),
    )


def compare_hysteresis_markov_to_baseline_with_uncertainty(
    train_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    validation_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    *,
    periods: float = 8.0,
    samples: int = 240,
    stride: int = 20,
    coordinate: str = "hierarchy_perturbation_strength",
    resamples: int = 512,
    confidence_level: float = 0.95,
    random_seed: int = 0,
) -> tuple[ChartWordMarkovChain, ChartWordMarkovBootstrapComparison]:
    """Fit hysteresis Markov dynamics and bootstrap its baseline gain."""

    atlas = AnalysisAtlas()
    training_words = []
    reports_by_name = {}
    for scenario_name in train_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        reports_by_name[scenario.name] = reports
        training_words.append(return_map_word_from_reports(reports, coordinate=coordinate))
    chain = hysteresis_markov_chain_from_reports(reports_by_name, coordinate=coordinate)
    validation_words = []
    for scenario_name in validation_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        validation_words.append(return_map_word_from_reports(reports, coordinate=coordinate))
    return chain, bootstrap_markov_baseline_comparison(
        chain,
        tuple(training_words),
        tuple(validation_words),
        resamples=resamples,
        confidence_level=confidence_level,
        random_seed=random_seed,
    )


def run_verification_report(
    *,
    scenario: ReferenceScenario = "hierarchical-flyby",
    periods: float = 8.0,
    samples: int = 500,
    stride: int = 20,
    inner_pair: tuple[int, int] = (0, 1),
    target_contraction: float = 0.35,
) -> dict[str, object]:
    """Return a JSON-ready end-to-end engine verification report."""

    reference, trajectory = integrate_reference_scenario(
        scenario,
        periods=periods,
        samples=samples,
    )
    jacobi_report = certify_jacobi_escape_report(
        trajectory,
        reference,
        inner_pair=inner_pair,
        target_contraction=target_contraction,
    )
    chain, bootstrap_comparison = compare_hysteresis_markov_to_baseline_with_uncertainty(
        (scenario,),
        (scenario,),
        periods=periods,
        samples=samples,
        stride=stride,
    )
    comparison = bootstrap_comparison.comparison
    return {
        "metadata": {
            "engine": "threebody-engine",
            "scenario": reference.name,
            "source_scenario": scenario,
            "periods": periods,
            "samples": samples,
            "stride": stride,
            "target_contraction": target_contraction,
        },
        "jacobi": jacobi_report,
        "hysteresis_markov": {
            "chain": chain.as_dict(),
            "baseline_comparison": comparison.as_dict(),
            "bootstrap_comparison": bootstrap_comparison.as_dict(),
        },
        "promotion_gates": {
            "picard_certified": bool(jacobi_report["picard_tuning"]["certified"]),
            "picard_contraction_reserve": jacobi_report["picard_tuning"]["contraction_reserve"],
            "hysteresis_beats_independent_baseline": comparison.beats_baseline,
            "hysteresis_significant_baseline_win": bootstrap_comparison.significant_baseline_win,
            "hysteresis_log_likelihood_gain": comparison.log_likelihood_gain,
            "hysteresis_log_likelihood_gain_ci": list(bootstrap_comparison.log_likelihood_gain_ci),
        },
    }


def _reference_scenario(
    library: OrbitLibrary,
    scenario: ReferenceScenario,
    *,
    periods: float,
    samples: int,
) -> Scenario:
    if scenario == "figure-eight":
        return library.general_figure_eight(periods=periods, samples=samples)
    if scenario == "hierarchical-flyby":
        return library.general_hierarchical_flyby(
            intruder_velocity=(0.8, 1.6),
            duration=periods,
            samples=samples,
        )
    if scenario == "restricted-l4":
        return library.restricted_l4(periods=periods, samples=samples)
    if scenario == "restricted-l5":
        return library.restricted_l5(periods=periods, samples=samples)
    raise ValueError(f"Unknown reference scenario: {scenario}")
