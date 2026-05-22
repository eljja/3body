from __future__ import annotations

from threebody_engine import (
    build_hysteresis_markov_chain,
    compare_hysteresis_markov_to_baseline,
    certify_jacobi_escape,
    certify_jacobi_escape_report,
    integrate_reference_scenario,
    run_verification_report,
    tune_jacobi_picard,
    validate_hysteresis_markov_chain,
)


def test_engine_api_integrates_reference_scenario() -> None:
    scenario, trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=30)

    assert scenario.name == "general-figure-eight"
    assert trajectory.success is True
    assert len(trajectory.t) == 30


def test_engine_api_exposes_picard_jacobi_certificate() -> None:
    scenario, trajectory = integrate_reference_scenario(
        "hierarchical-flyby",
        periods=8.0,
        samples=500,
    )

    certificate = certify_jacobi_escape(trajectory, scenario)

    assert certificate.picard_flow_certified is True
    assert certificate.maximum_observed_contraction < certificate.target_contraction

    tuning = tune_jacobi_picard(trajectory, scenario)
    report = certify_jacobi_escape_report(trajectory, scenario)

    assert tuning.certified is True
    assert tuning.best_observed_contraction < tuning.target_contraction
    assert report["picard_tuning"]["certified"] is True


def test_engine_api_builds_hysteresis_markov_chain() -> None:
    chain = build_hysteresis_markov_chain(
        ("hierarchical-flyby",),
        periods=2.0,
        samples=80,
        stride=10,
    )

    assert chain.states
    assert chain.transition_entropy_rate >= 0.0
    assert abs(sum(chain.stationary_distribution) - 1.0) < 1.0e-12


def test_engine_api_validates_hysteresis_markov_chain() -> None:
    _chain, validation = validate_hysteresis_markov_chain(
        ("hierarchical-flyby",),
        ("hierarchical-flyby",),
        periods=2.0,
        samples=80,
        stride=10,
    )

    assert validation.transition_count >= 0
    assert validation.perplexity >= 1.0


def test_engine_api_compares_hysteresis_markov_to_baseline() -> None:
    _chain, comparison = compare_hysteresis_markov_to_baseline(
        ("hierarchical-flyby",),
        ("hierarchical-flyby",),
        periods=2.0,
        samples=80,
        stride=10,
    )

    assert comparison.markov_validation.transition_count >= 0
    assert comparison.baseline_perplexity >= 1.0


def test_engine_api_runs_integrated_verification_report() -> None:
    report = run_verification_report(
        scenario="hierarchical-flyby",
        periods=8.0,
        samples=500,
        stride=20,
    )

    assert report["metadata"]["engine"] == "threebody-engine"
    assert report["promotion_gates"]["picard_certified"] is True
    assert report["promotion_gates"]["picard_contraction_reserve"] > 0.0
    assert "baseline_comparison" in report["hysteresis_markov"]
