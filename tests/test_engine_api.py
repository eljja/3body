from __future__ import annotations

from threebody_engine import (
    audit_public_static_artifact_bytes,
    audit_public_static_artifacts,
    audit_public_static_artifacts_from_url,
    build_hysteresis_markov_chain,
    compare_hysteresis_markov_to_baseline,
    compare_hysteresis_markov_to_baseline_with_uncertainty,
    certify_jacobi_escape,
    certify_jacobi_escape_report,
    integrate_reference_scenario,
    predict_three_body_distribution_ephemeris,
    predict_three_body_ephemeris,
    predict_three_body_forecast_horizon,
    predict_three_body_interpretation_report,
    predict_three_body_linearized_distribution,
    predict_three_body_position_distribution,
    predict_three_body_positions,
    public_static_artifact_audit_report_payload_sha256,
    public_static_artifact_claim_contract,
    run_verification_report,
    select_hysteresis_markov_order,
    solve_three_body_prediction_problem,
    tune_jacobi_picard,
    validate_hysteresis_markov_chain,
    validate_public_static_artifact_receipt_contract,
    verify_public_static_artifact_bytes,
    verify_public_static_artifacts,
    verify_public_static_artifacts_from_url,
)


def test_engine_api_integrates_reference_scenario() -> None:
    assert callable(audit_public_static_artifacts)
    assert callable(audit_public_static_artifacts_from_url)
    assert callable(audit_public_static_artifact_bytes)
    assert callable(verify_public_static_artifacts)
    assert callable(verify_public_static_artifacts_from_url)
    assert callable(verify_public_static_artifact_bytes)
    assert callable(public_static_artifact_audit_report_payload_sha256)

    scenario, trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=30)

    assert scenario.name == "general-figure-eight"
    assert trajectory.success is True
    assert len(trajectory.t) == 30


def test_engine_api_predicts_three_body_positions_from_initial_state() -> None:
    scenario, _trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=8)
    positions, velocities = scenario.system.split_state(scenario.initial_state)

    prediction = predict_three_body_positions(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        samples=16,
    )

    assert prediction["prediction_type"] == "deterministic-position"
    assert prediction["success"] is True
    assert prediction["dimension"] == 2
    assert len(prediction["positions"]) == 3
    assert len(prediction["positions"][0]) == 2
    assert prediction["invariant_certificate"]["maximum_relative_energy_drift"] < 1.0e-8


def test_engine_api_builds_three_body_ephemeris() -> None:
    scenario, _trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=8)
    positions, velocities = scenario.system.split_state(scenario.initial_state)

    ephemeris = predict_three_body_ephemeris(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        samples=9,
        include_invariant_series=True,
    )
    point_prediction = predict_three_body_positions(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        samples=9,
    )

    assert ephemeris["prediction_type"] == "deterministic-ephemeris"
    assert ephemeris["success"] is True
    assert ephemeris["sample_count"] == 9
    assert len(ephemeris["times"]) == 9
    assert len(ephemeris["positions"]) == 9
    assert len(ephemeris["positions"][0]) == 3
    assert len(ephemeris["positions"][0][0]) == 2
    assert ephemeris["positions"][-1] == point_prediction["positions"]
    assert ephemeris["velocities"][-1] == point_prediction["velocities"]
    assert len(ephemeris["invariant_series"]["energy"]) == 9
    assert ephemeris["invariant_certificate"]["maximum_relative_energy_drift"] < 1.0e-8


def test_engine_api_builds_three_body_position_distribution() -> None:
    scenario, _trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=8)
    positions, velocities = scenario.system.split_state(scenario.initial_state)

    distribution = predict_three_body_position_distribution(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        count=7,
        position_scale=1.0e-7,
        velocity_scale=1.0e-7,
        seed=4,
        samples=16,
        include_sample_positions=True,
    )

    assert distribution["prediction_type"] == "empirical-position-distribution"
    assert distribution["success_count"] == 7
    assert distribution["failure_count"] == 0
    assert distribution["uncertainty_model"]["preserve_center_of_mass"] is True
    assert len(distribution["position_distribution"]["mean_positions"]) == 3
    assert len(distribution["position_distribution"]["flat_covariance"]) == 6
    assert len(distribution["sample_predictions"]) == 7


def test_engine_api_builds_three_body_distribution_ephemeris() -> None:
    scenario, _trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=8)
    positions, velocities = scenario.system.split_state(scenario.initial_state)

    distribution = predict_three_body_distribution_ephemeris(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        count=7,
        position_scale=1.0e-7,
        velocity_scale=1.0e-7,
        seed=4,
        samples=9,
        include_sample_ephemerides=True,
    )

    assert distribution["prediction_type"] == "empirical-position-distribution-ephemeris"
    assert distribution["success_count"] == 7
    assert distribution["failure_count"] == 0
    assert len(distribution["times"]) == 9
    assert len(distribution["position_distribution_ephemeris"]["mean_positions"]) == 9
    assert len(distribution["position_distribution_ephemeris"]["mean_positions"][0]) == 3
    assert len(distribution["position_distribution_ephemeris"]["flat_covariances"]) == 9
    assert len(distribution["position_distribution_ephemeris"]["flat_covariances"][0]) == 6
    assert len(distribution["sample_ephemerides"]) == 7
    assert len(distribution["sample_ephemerides"][0]["positions"]) == 9


def test_engine_api_solves_three_body_prediction_problem() -> None:
    scenario, _trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=8)
    positions, velocities = scenario.system.split_state(scenario.initial_state)

    solution = solve_three_body_prediction_problem(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        count=5,
        position_scale=1.0e-7,
        velocity_scale=1.0e-7,
        samples=9,
        horizon_samples=6,
    )

    assert solution["prediction_type"] == "three-body-prediction-solution"
    assert solution["answer"]["recommended_mode"] in {"linearized-gaussian", "empirical-ensemble"}
    assert solution["answer"]["target_time_inside_forecast_horizon"] is True
    assert len(solution["answer"]["final_positions"]) == 3
    assert len(solution["answer"]["final_position_distribution"]["mean_positions"]) == 3
    assert solution["deterministic_ephemeris"]["prediction_type"] == "deterministic-ephemeris"
    assert solution["distribution_ephemeris"]["prediction_type"] == "empirical-position-distribution-ephemeris"
    assert solution["interpretation_report"]["prediction_type"] == "three-body-interpretation-report"


def test_engine_api_builds_linearized_three_body_position_distribution() -> None:
    scenario, _trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=8)
    positions, velocities = scenario.system.split_state(scenario.initial_state)

    distribution = predict_three_body_linearized_distribution(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        position_scale=1.0e-7,
        velocity_scale=1.0e-7,
    )

    assert distribution["prediction_type"] == "linearized-gaussian-position-distribution"
    assert distribution["success"] is True
    assert len(distribution["mean_positions"]) == 3
    assert len(distribution["position_covariance"]) == 6
    assert len(distribution["state_transition_matrix"]) == 12
    assert distribution["linearized_diagnostics"]["minimum_covariance_eigenvalue"] > -1.0e-18
    assert distribution["linearized_diagnostics"]["maximum_position_std"] > 0.0


def test_engine_api_builds_interpretation_prediction_report() -> None:
    scenario, _trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=8)
    positions, velocities = scenario.system.split_state(scenario.initial_state)

    report = predict_three_body_interpretation_report(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        count=7,
        position_scale=1.0e-7,
        velocity_scale=1.0e-7,
        samples=16,
    )

    assert report["prediction_type"] == "three-body-interpretation-report"
    assert report["deterministic"]["prediction_type"] == "deterministic-position"
    assert report["linearized_gaussian"]["prediction_type"] == "linearized-gaussian-position-distribution"
    assert report["forecast_horizon"]["prediction_type"] == "linearized-forecast-horizon"
    assert report["forecast_horizon"]["target_time_resolved"] is True
    assert report["empirical_distribution"]["prediction_type"] == "empirical-position-distribution"
    assert report["comparison"]["mean_gap_in_sigma_units"] >= 0.0
    assert report["verdict"]["deterministic_resolved"] is True
    assert report["verdict"]["empirical_distribution_resolved"] is True
    assert report["verdict"]["target_time_inside_forecast_horizon"] is True
    assert report["verdict"]["recommended_mode"] in {"linearized-gaussian", "empirical-ensemble"}


def test_engine_api_estimates_three_body_forecast_horizon() -> None:
    scenario, _trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=8)
    positions, velocities = scenario.system.split_state(scenario.initial_state)

    horizon = predict_three_body_forecast_horizon(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        position_tolerance=1.0e-3,
        position_scale=1.0e-7,
        velocity_scale=1.0e-7,
        horizon_samples=6,
    )

    assert horizon["prediction_type"] == "linearized-forecast-horizon"
    assert horizon["success"] is True
    assert horizon["target_time_resolved"] is True
    assert horizon["reliable_until"] == horizon["rows"][-1]["time"]
    assert horizon["final_uncertainty_to_tolerance_ratio"] < 1.0
    assert len(horizon["rows"]) == 6


def test_engine_api_exposes_public_static_claim_contract() -> None:
    contract = public_static_artifact_claim_contract()

    assert contract["contract_schema_version"] == 1
    assert contract["profile"] == "public-claims-v1"
    assert isinstance(contract["profile_sha256"], str)
    assert len(contract["profile_sha256"]) == 64
    assert contract["profile_descriptor"]["profile"] == "public-claims-v1"
    assert "artifact-availability" in contract["profile_descriptor"]["requirements"]["require_features"]
    assert "certificate-verifier-capability-digest" in contract["verification_schema_features"]
    assert isinstance(contract["verification_schema_features_sha256"], str)
    assert len(contract["verification_schema_features_sha256"]) == 64


def test_engine_api_receipt_contract_validator_reports_missing_fields() -> None:
    result = validate_public_static_artifact_receipt_contract({})

    assert result["verified"] is False
    assert result["checks"]["receipt_verified"] is False
    assert result["checks"]["receipt_payload_sha256_present"] is False
    assert result["checks"]["receipt_payload_sha256_matches"] is False
    assert result["checks"]["required_profile_declared"] is False
    assert result["checks"]["required_profile_hash_matches"] is False
    assert result["checks"]["required_feature_set_sha256_matches"] is False


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


def test_engine_api_compares_hysteresis_markov_with_uncertainty() -> None:
    _chain, bootstrap = compare_hysteresis_markov_to_baseline_with_uncertainty(
        ("hierarchical-flyby",),
        ("hierarchical-flyby",),
        periods=2.0,
        samples=80,
        stride=10,
        resamples=32,
        random_seed=3,
    )

    assert bootstrap.resample_count == 32
    assert bootstrap.comparison.baseline_perplexity >= 1.0
    assert bootstrap.log_likelihood_gain_ci[0] <= bootstrap.log_likelihood_gain_ci[1]


def test_engine_api_selects_hysteresis_markov_order() -> None:
    selection = select_hysteresis_markov_order(
        ("hierarchical-flyby",),
        ("hierarchical-flyby",),
        periods=2.0,
        samples=80,
        stride=10,
        max_order=2,
    )

    assert selection.selected_order in {0, 1, 2}
    assert selection.scores
    assert selection.criterion == "bic"


def test_engine_api_supports_poincare_hysteresis_words() -> None:
    chain, bootstrap = compare_hysteresis_markov_to_baseline_with_uncertainty(
        ("hierarchical-flyby",),
        ("hierarchical-flyby",),
        periods=2.0,
        samples=80,
        stride=10,
        word_mode="poincare",
        resamples=16,
    )
    selection = select_hysteresis_markov_order(
        ("hierarchical-flyby",),
        ("hierarchical-flyby",),
        periods=2.0,
        samples=80,
        stride=10,
        word_mode="poincare",
    )

    assert chain.states
    assert bootstrap.comparison.markov_validation.transition_count >= 0
    assert selection.selected_order in {0, 1, 2}


def test_engine_api_runs_integrated_verification_report() -> None:
    report = run_verification_report(
        scenario="hierarchical-flyby",
        periods=8.0,
        samples=500,
        stride=20,
    )

    assert report["metadata"]["engine"] == "threebody-engine"
    assert report["metadata"]["report_schema_version"] == 2
    assert report["metadata"]["word_mode"] == "refined"
    assert report["metadata"]["random_seeds"]["symbolic_stride_robustness"] == 43
    assert report["promotion_gates"]["picard_certified"] is True
    assert report["promotion_gates"]["picard_contraction_reserve"] > 0.0
    assert "baseline_comparison" in report["hysteresis_markov"]
    assert "bootstrap_comparison" in report["hysteresis_markov"]
    assert "order_selection" in report["hysteresis_markov"]
    assert report["hysteresis_markov"]["validation_mode"] == "heldout_binary_phase"
    assert "poincare_section_sweep" in report["hysteresis_markov"]
    assert "poincare_coordinate_sweep" in report["hysteresis_markov"]
    assert "poincare_markov" in report["hysteresis_markov"]
    assert "permutation_control" in report["hysteresis_markov"]["poincare_markov"]
    assert "section_robustness" in report["hysteresis_markov"]["poincare_markov"]
    assert "stride_robustness" in report["hysteresis_markov"]["poincare_markov"]
    assert "hysteresis_log_likelihood_gain_ci" in report["promotion_gates"]
    assert "hysteresis_selected_markov_order" in report["promotion_gates"]
    assert "poincare_best_crossing_count" in report["promotion_gates"]
    assert "poincare_best_coordinate" in report["promotion_gates"]
    assert "poincare_best_coordinate_crossing_count" in report["promotion_gates"]
    assert "poincare_markov_significant_baseline_win" in report["promotion_gates"]
    assert "poincare_selected_markov_order" in report["promotion_gates"]
    assert "poincare_passes_permutation_control" in report["promotion_gates"]
    assert "poincare_permutation_control_gap" in report["promotion_gates"]
    assert report["promotion_gates"]["poincare_heldout_phase_validation"] is True
    assert "poincare_section_robust_pass_count" in report["promotion_gates"]
    assert "poincare_passes_section_robustness" in report["promotion_gates"]
    assert "symbolic_stride_robust_pass_count" in report["promotion_gates"]
    assert "symbolic_passes_stride_robustness" in report["promotion_gates"]
