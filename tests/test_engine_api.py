from __future__ import annotations

import numpy as np

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
    predict_three_body_linearized_ephemeris,
    predict_three_body_position_distribution,
    predict_three_body_positions,
    public_static_artifact_audit_report_payload_sha256,
    public_static_artifact_claim_contract,
    run_verification_report,
    select_hysteresis_markov_order,
    solve_three_body_prediction_problem,
    solve_three_body_target_positions,
    score_three_body_position_hypothesis,
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
    assert prediction["close_approach_diagnostics"]["minimum_pair_distance"] > 0.0
    assert prediction["close_approach_diagnostics"]["warning_level"] in {
        "nominal",
        "close-approach",
        "softening-scale",
        "collision-scale",
    }


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
    assert ephemeris["close_approach_diagnostics"]["minimum_pair_distance"] > 0.0
    assert len(ephemeris["close_approach_diagnostics"]["minimum_pair"]) == 2


def test_engine_api_builds_ephemeris_at_requested_times() -> None:
    scenario, _trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=8)
    positions, velocities = scenario.system.split_state(scenario.initial_state)
    target_times = [0.0, 0.01, 0.035, 0.05]

    ephemeris = predict_three_body_ephemeris(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        samples=9,
        target_times=target_times,
    )
    linearized = predict_three_body_linearized_ephemeris(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        position_scale=1.0e-7,
        velocity_scale=1.0e-7,
        samples=9,
        target_times=target_times,
        preserve_center_of_mass=True,
    )
    distribution = predict_three_body_distribution_ephemeris(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        count=5,
        position_scale=1.0e-7,
        velocity_scale=1.0e-7,
        seed=4,
        samples=9,
        target_times=target_times,
    )

    assert ephemeris["times"] == target_times
    assert len(ephemeris["positions"]) == len(target_times)
    assert linearized["times"] == target_times
    assert len(linearized["rows"]) == len(target_times)
    assert distribution["times"] == target_times
    assert len(distribution["position_distribution_ephemeris"]["mean_positions"]) == len(target_times)


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
    assert len(distribution["position_distribution"]["position_confidence_regions"]) == 3
    assert distribution["position_distribution"]["position_confidence_regions"][0]["levels"][2]["probability"] == 0.95
    assert len(distribution["sample_predictions"]) == 7


def test_engine_api_pushes_explicit_initial_covariance_through_distribution_modes() -> None:
    scenario, _trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=8)
    positions, velocities = scenario.system.split_state(scenario.initial_state)
    covariance = np.eye(scenario.initial_state.size, dtype=float) * 1.0e-14
    covariance[0, 2] = covariance[2, 0] = 2.0e-15

    distribution = predict_three_body_position_distribution(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        count=7,
        initial_state_covariance=covariance,
        seed=4,
        samples=16,
    )
    solution = solve_three_body_prediction_problem(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        count=7,
        initial_state_covariance=covariance,
        samples=9,
        horizon_samples=6,
    )

    assert distribution["uncertainty_model"]["initial_state_covariance_supplied"] is True
    assert distribution["uncertainty_model"]["preserve_center_of_mass"] is False
    assert np.allclose(np.asarray(distribution["initial_state_covariance"], dtype=float), covariance)
    assert solution["linearized_gaussian_ephemeris"]["uncertainty_model"]["initial_state_covariance_supplied"] is True
    assert solution["distribution_ephemeris"]["uncertainty_model"]["initial_state_covariance_supplied"] is True
    assert np.allclose(
        np.asarray(solution["distribution_ephemeris"]["initial_state_covariance"], dtype=float),
        covariance,
    )


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
    assert len(distribution["position_distribution_ephemeris"]["position_confidence_regions"]) == 9
    assert len(distribution["position_distribution_ephemeris"]["position_confidence_regions"][0]) == 3
    assert distribution["ensemble_close_approach_diagnostics"]["sample_count"] == 7
    assert distribution["ensemble_close_approach_diagnostics"]["minimum_pair_distance"] > 0.0
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
    assert solution["prediction_input_contract"]["contract_schema_version"] == 1
    assert solution["prediction_input_contract"]["uncertainty_parameters"]["count"] == 5
    assert solution["prediction_input_contract"]["solver_parameters"]["samples"] == 9
    assert isinstance(solution["prediction_input_sha256"], str)
    assert len(solution["prediction_input_sha256"]) == 64
    assert solution["prediction_summary"]["summary_schema_version"] == 1
    assert solution["prediction_summary"]["claim"] in {
        "target-position-and-distribution",
        "distributional-target-position",
        "deterministic-target-position",
        "unresolved-target-position",
    }
    assert solution["prediction_summary"]["recommended_mode"] == solution["answer"]["recommended_mode"]
    assert "Target-time positions" in solution["prediction_summary"]["headline"]
    assert "target-time Newtonian flow-map" in solution["prediction_summary"]["position_statement"]
    assert len(solution["prediction_summary"]["deterministic_final_positions"]) == 3
    assert len(solution["prediction_summary"]["confidence_regions_95"]) == 3
    assert len(solution["prediction_summary"]["body_95_confidence_regions"]) == 3
    assert solution["prediction_summary"]["key_metrics"]["minimum_pair_distance"] > 0.0
    assert (
        solution["prediction_summary"]["key_metrics"]["minimum_pair_distance"]
        == solution["answer"]["minimum_pair_distance"]
    )
    statement = solution["mathematical_statement"]
    assert statement["statement_schema_version"] == 1
    assert statement["problem_type"] == "general-newtonian-three-body-initial-value-problem"
    assert statement["target_time"] == solution["target_time"]
    assert statement["deterministic_problem"]["flow_map"] == "x(t) = Phi_t(x(0))"
    assert "d r_i / dt = v_i" in statement["deterministic_problem"]["equations"]
    assert statement["probability_problem"]["linearized_gaussian"] == "P_t = D Phi_t(x0) P_0 D Phi_t(x0)^T."
    assert statement["claim_contract"]["promoted_claim"] == solution["prediction_summary"]["claim"]
    assert len(statement["body_position_claims"]) == 3
    assert statement["body_position_claims"][0]["deterministic_position"] == solution["answer"]["final_positions"][0]
    assert statement["body_position_claims"][0]["confidence_region_95"]["probability"] == 0.95
    assert solution["answer"]["recommended_mode"] in {"linearized-gaussian", "empirical-ensemble"}
    assert solution["answer"]["target_time_inside_forecast_horizon"] is True
    assert len(solution["answer"]["final_positions"]) == 3
    assert len(solution["answer"]["final_position_distribution"]["mean_positions"]) == 3
    assert len(solution["answer"]["final_position_distribution"]["position_confidence_regions"]) == 3
    assert solution["deterministic_ephemeris"]["prediction_type"] == "deterministic-ephemeris"
    assert solution["linearized_gaussian_ephemeris"]["prediction_type"] == "linearized-gaussian-ephemeris"
    assert solution["linearized_gaussian_ephemeris"]["uncertainty_model"]["preserve_center_of_mass"] is True
    assert solution["distribution_ephemeris"]["prediction_type"] == "empirical-position-distribution-ephemeris"
    assert solution["ephemeris_distribution_comparison"]["row_count"] == 9
    assert solution["ephemeris_distribution_comparison"]["final_covariance_relative_gap"] >= 0.0
    assert solution["answer"]["uncertainty_amplification_factor"] >= 1.0
    assert np.isfinite(solution["answer"]["finite_time_lyapunov_exponent"])
    assert solution["answer"]["minimum_pair_distance"] > 0.0
    assert solution["answer"]["close_approach_warning_level"] in {
        "nominal",
        "close-approach",
        "softening-scale",
        "collision-scale",
    }
    assert solution["answer"]["regularization_recommended"] in {True, False}
    assert "linearized_ephemeris_consistent_until" in solution["answer"]
    assert "first_linearized_ephemeris_break_time" in solution["answer"]
    assert solution["interpretation_report"]["prediction_type"] == "three-body-interpretation-report"


def test_engine_api_returns_compact_target_position_solution() -> None:
    scenario, _trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=8)
    positions, velocities = scenario.system.split_state(scenario.initial_state)

    solution = solve_three_body_target_positions(
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

    assert solution["prediction_type"] == "three-body-target-position-solution"
    assert solution["claim"] in {
        "target-position-and-distribution",
        "distributional-target-position",
        "deterministic-target-position",
        "unresolved-target-position",
    }
    assert len(solution["target_positions"]) == 3
    assert len(solution["target_position_distribution"]["mean_positions"]) == 3
    assert len(solution["target_position_table"]) == 3
    assert solution["target_position_table"][0]["body_index"] == 0
    assert solution["target_position_table"][0]["deterministic_position"] == solution["target_positions"][0]
    assert len(solution["target_position_table"][0]["central_90_interval"]["lower"]) == 2
    assert len(solution["target_position_table"][0]["central_90_interval"]["upper"]) == 2
    assert solution["target_position_table"][0]["confidence_region_95"]["max_semi_axis"] >= 0.0
    assert solution["target_position_table"][0]["confidence_region_95"]["relative_95_radius"] >= 0.0
    assert solution["target_position_table"][0]["characteristic_position_scale"] > 0.0
    assert solution["target_position_table"][0]["position_claim_strength"] in {
        "point-resolved",
        "localized-distribution",
        "broad-distribution",
    }
    assert solution["target_position_table"][0]["recommended_readout"] in {
        "point-position-with-confidence-region",
        "probability-region",
        "distribution-summary-only",
    }
    assert solution["target_position_table"][0]["deterministic_to_mean_distance"] >= 0.0
    assert solution["target_position_table"][0]["deterministic_to_mean_distance_relative"] >= 0.0
    center_frame = solution["center_of_mass_frame"]
    assert center_frame["frame"] == "mass-weighted-center-of-mass"
    assert center_frame["total_mass"] == sum(scenario.system.masses)
    assert len(center_frame["target_center_position"]) == 2
    assert len(center_frame["target_positions_relative_to_center"]) == 3
    assert len(center_frame["distribution_mean_relative_to_center"]) == 3
    assert center_frame["target_center_speed"] >= 0.0
    assert (
        solution["deterministic_flow_answer"]["positions_relative_to_center_of_mass"]
        == center_frame["target_positions_relative_to_center"]
    )
    assert (
        solution["probability_answer"]["mean_positions_relative_to_center_of_mass"]
        == center_frame["distribution_mean_relative_to_center"]
    )
    pair_geometry = solution["target_pair_geometry"]
    assert pair_geometry["geometry_schema_version"] == 1
    assert pair_geometry["pair_order"] == [[0, 1], [0, 2], [1, 2]]
    assert len(pair_geometry["pair_distances"]) == 3
    assert pair_geometry["pair_distances"][0]["body_pair"] == [0, 1]
    assert pair_geometry["pair_distances"][0]["deterministic_distance"] > 0.0
    assert pair_geometry["pair_distances"][0]["probability_mean_distance"] > 0.0
    assert pair_geometry["pair_distances"][0]["central_90_distance_interval_from_coordinate_box"]["upper"] > 0.0
    assert pair_geometry["deterministic"]["perimeter"] > 0.0
    assert pair_geometry["deterministic"]["triangle_area"] >= 0.0
    assert pair_geometry["probability"]["mean_perimeter"] > 0.0
    assert solution["deterministic_flow_answer"]["pair_geometry"] == pair_geometry["deterministic"]
    assert solution["probability_answer"]["pair_geometry"] == pair_geometry["probability"]
    distribution_quality = solution["target_distribution_quality"]
    assert distribution_quality["quality_schema_version"] == 1
    assert distribution_quality["sample_count"] == 5
    assert len(distribution_quality["body_mean_standard_errors"]) == 3
    assert distribution_quality["body_mean_standard_errors"][0]["max_mean_standard_error"] >= 0.0
    assert distribution_quality["relative_max_mean_standard_error"] >= 0.0
    assert distribution_quality["sampling_error_strength"] in {
        "well-sampled",
        "usable",
        "sampling-noisy",
    }
    assert solution["probability_answer"]["distribution_quality"] == distribution_quality
    certificate = solution["target_prediction_certificate"]
    assert certificate["certificate_schema_version"] == 1
    assert certificate["certificate_type"] == "three-body-target-prediction-reproducibility"
    assert certificate["input_contract"]["uncertainty_parameters"]["count"] == 5
    assert certificate["input_contract"]["solver_parameters"]["samples"] == 9
    assert isinstance(certificate["input_contract_sha256"], str)
    assert len(certificate["input_contract_sha256"]) == 64
    assert isinstance(certificate["result_payload_sha256"], str)
    assert len(certificate["result_payload_sha256"]) == 64
    assert "target_prediction_certificate" not in certificate["result_payload_keys"]
    assert "target_positions" in certificate["result_payload_keys"]
    assert len(solution["body_answers"]) == 3
    assert solution["body_answers"][0]["deterministic_position"] == solution["target_positions"][0]
    assert solution["deterministic_flow_answer"]["definition"] == "r_i(t) = Pi_{r_i} Phi_t(x(0))"
    assert solution["probability_answer"]["definition"] == "Law(X_t) = (Phi_t)_# Law(X_0)"
    assert solution["probability_answer"]["target_position_table"] == solution["target_position_table"]
    assert len(solution["probability_answer"]["confidence_regions_95"]) == 3
    assert solution["diagnostics"]["minimum_pair_distance"] > 0.0
    assert solution["mathematical_statement"]["statement_schema_version"] == 1
    assert "solution_bundle" not in solution


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
        preserve_center_of_mass=True,
    )

    assert distribution["prediction_type"] == "linearized-gaussian-position-distribution"
    assert distribution["success"] is True
    assert distribution["uncertainty_model"]["preserve_center_of_mass"] is True
    assert len(distribution["mean_positions"]) == 3
    assert len(distribution["position_covariance"]) == 6
    assert len(distribution["state_transition_matrix"]) == 12
    assert len(distribution["position_confidence_regions"]) == 3
    assert distribution["position_confidence_regions"][0]["method"] == "linearized-gaussian"
    assert distribution["linearized_diagnostics"]["minimum_covariance_eigenvalue"] > -1.0e-18
    assert distribution["linearized_diagnostics"]["maximum_position_std"] > 0.0
    assert distribution["linearized_diagnostics"]["uncertainty_amplification_factor"] >= 1.0
    assert np.isfinite(distribution["linearized_diagnostics"]["finite_time_lyapunov_exponent"])
    covariance0 = np.asarray(distribution["initial_state_covariance"], dtype=float)
    weights = np.asarray(scenario.system.masses, dtype=float)
    weights = weights / np.sum(weights)
    for offset in (0, 3 * scenario.system.dimension):
        for axis in range(scenario.system.dimension):
            indices = [offset + body_index * scenario.system.dimension + axis for body_index in range(3)]
            axis_covariance = covariance0[np.ix_(indices, indices)]
            assert abs(float(weights @ axis_covariance @ weights)) < 1.0e-30


def test_engine_api_scores_three_body_position_hypothesis() -> None:
    scenario, _trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=8)
    positions, velocities = scenario.system.split_state(scenario.initial_state)
    prediction = predict_three_body_positions(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        samples=16,
    )

    score = score_three_body_position_hypothesis(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        prediction["positions"],
        position_scale=1.0e-7,
        velocity_scale=1.0e-7,
        preserve_center_of_mass=True,
    )

    assert score["prediction_type"] == "three-body-position-hypothesis-score"
    assert score["joint_score"]["mahalanobis_distance"] < 1.0e-6
    assert score["joint_score"]["inside_confidence_levels"]["0.95"] is True
    assert len(score["body_scores"]) == 3
    assert score["body_scores"][0]["inside_confidence_levels"]["0.95"] is True


def test_engine_api_builds_linearized_three_body_ephemeris() -> None:
    scenario, _trajectory = integrate_reference_scenario("figure-eight", periods=0.02, samples=8)
    positions, velocities = scenario.system.split_state(scenario.initial_state)

    ephemeris = predict_three_body_linearized_ephemeris(
        scenario.system.masses,
        positions,
        velocities,
        0.05,
        position_scale=1.0e-7,
        velocity_scale=1.0e-7,
        samples=9,
        preserve_center_of_mass=True,
    )

    assert ephemeris["prediction_type"] == "linearized-gaussian-ephemeris"
    assert ephemeris["success"] is True
    assert ephemeris["uncertainty_model"]["preserve_center_of_mass"] is True
    assert len(ephemeris["times"]) == 9
    assert len(ephemeris["rows"]) == 9
    assert len(ephemeris["rows"][0]["mean_positions"]) == 3
    assert len(ephemeris["rows"][0]["position_covariance"]) == 6
    assert len(ephemeris["rows"][0]["position_confidence_regions"]) == 3
    assert ephemeris["rows"][-1]["linearized_sensitivity"]["uncertainty_amplification_factor"] >= 1.0
    assert np.isfinite(
        ephemeris["linearized_diagnostics"]["final_linearized_sensitivity"]["finite_time_lyapunov_exponent"]
    )
    assert ephemeris["rows"][-1]["maximum_position_std"] > 0.0
    assert ephemeris["linearized_diagnostics"]["maximum_position_std"] >= ephemeris["rows"][-1]["maximum_position_std"]


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
    assert report["uncertainty_model"]["preserve_center_of_mass"] is True
    assert report["linearized_gaussian"]["uncertainty_model"]["preserve_center_of_mass"] is True
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
        preserve_center_of_mass=True,
    )

    assert horizon["prediction_type"] == "linearized-forecast-horizon"
    assert horizon["success"] is True
    assert horizon["uncertainty_model"]["preserve_center_of_mass"] is True
    assert horizon["target_time_resolved"] is True
    assert horizon["reliable_until"] == horizon["rows"][-1]["time"]
    assert horizon["final_uncertainty_to_tolerance_ratio"] < 1.0
    assert len(horizon["rows"]) == 6
    assert horizon["rows"][-1]["linearized_sensitivity"]["uncertainty_amplification_factor"] >= 1.0


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
