from __future__ import annotations

import hashlib
import json

import threebody.cli as cli_module
from threebody.cli import main


def test_survey_cli_writes_research_artifact(tmp_path) -> None:
    output = tmp_path / "survey.json"

    exit_code = main(
        [
            "survey",
            "--scenario",
            "figure-eight",
            "--count",
            "1",
            "--periods",
            "0.02",
            "--samples",
            "30",
            "--stride",
            "10",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["metadata"]["scenario"] == "general-figure-eight"
    assert payload["summary"]["trajectory_count"] == 1
    assert "chart_distribution" in payload["summary"]


def test_interpret_cli_writes_chart_local_segments(tmp_path) -> None:
    output = tmp_path / "interpret.json"

    exit_code = main(
        [
            "interpret",
            "--scenario",
            "hierarchical-flyby",
            "--periods",
            "1.0",
            "--samples",
            "80",
            "--stride",
            "10",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["metadata"]["kind"] == "trajectory-interpretation"
    assert payload["summary"]["certificate"]["local_interpretation_available"] is True
    assert payload["summary"]["certificate"]["theorem_ready"] is False
    assert payload["summary"]["segments"]
    assert payload["summary"]["unresolved_obligations"]


def test_interpretation_suite_cli_writes_certificate_coverage(tmp_path) -> None:
    output = tmp_path / "interpretation-suite.json"

    exit_code = main(["interpretation-suite", "--output", str(output)])

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["metadata"]["kind"] == "interpretation-suite"
    assert payload["summary"]["local_interpretation_rate"] == 1.0
    assert "close_encounter" in payload["summary"]["covered_chart_types"]
    assert payload["summary"]["unresolved_blockers"]


def test_atlas_benchmark_cli_writes_reproducible_cases(tmp_path) -> None:
    output = tmp_path / "atlas-benchmark.json"

    exit_code = main(
        [
            "atlas-benchmark",
            "--scenario",
            "figure-eight",
            "--periods",
            "0.02",
            "--samples",
            "30",
            "--stride",
            "10",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["metadata"]["kind"] == "atlas-benchmark"
    assert payload["metadata"]["schema_version"] == 1
    assert payload["cases"][0]["source_name"] == "figure-eight"
    assert payload["cases"][0]["initial_state"]
    assert payload["cases"][0]["chart_distribution"]
    assert "threebody interpret" in payload["cases"][0]["reproduce"]


def test_predict_cli_writes_deterministic_three_body_forecast(tmp_path) -> None:
    input_path = tmp_path / "initial-state.json"
    output_path = tmp_path / "prediction.json"
    _write_prediction_input(input_path)

    exit_code = main(
        [
            "predict",
            "--input",
            str(input_path),
            "--target-time",
            "0.05",
            "--samples",
            "16",
            "--output",
            str(output_path),
        ]
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["prediction_type"] == "deterministic-position"
    assert payload["success"] is True
    assert payload["dimension"] == 2
    assert len(payload["positions"]) == 3
    assert payload["invariant_certificate"]["maximum_relative_energy_drift"] < 1.0e-8
    assert payload["close_approach_diagnostics"]["minimum_pair_distance"] > 0.0


def test_predict_cli_writes_ephemeris(tmp_path) -> None:
    input_path = tmp_path / "initial-state.json"
    output_path = tmp_path / "ephemeris.json"
    _write_prediction_input(input_path)

    exit_code = main(
        [
            "predict",
            "--input",
            str(input_path),
            "--ephemeris",
            "--samples",
            "9",
            "--include-invariant-series",
            "--output",
            str(output_path),
        ]
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["prediction_type"] == "deterministic-ephemeris"
    assert payload["success"] is True
    assert payload["sample_count"] == 9
    assert len(payload["times"]) == 9
    assert len(payload["positions"]) == 9
    assert len(payload["positions"][0]) == 3
    assert len(payload["invariant_series"]["energy"]) == 9
    assert payload["invariant_certificate"]["maximum_relative_energy_drift"] < 1.0e-8
    assert payload["close_approach_diagnostics"]["minimum_pair_distance"] > 0.0


def test_predict_cli_writes_ephemeris_at_requested_times(tmp_path) -> None:
    input_path = tmp_path / "initial-state.json"
    output_path = tmp_path / "ephemeris.json"
    _write_prediction_input(input_path)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    payload["target_times"] = [0.0, 0.01, 0.035, 0.05]
    input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    exit_code = main(
        [
            "predict",
            "--input",
            str(input_path),
            "--ephemeris",
            "--samples",
            "9",
            "--output",
            str(output_path),
        ]
    )
    result = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert result["prediction_type"] == "deterministic-ephemeris"
    assert result["times"] == payload["target_times"]
    assert len(result["positions"]) == len(payload["target_times"])


def test_predict_cli_writes_position_distribution(tmp_path) -> None:
    input_path = tmp_path / "initial-state.json"
    output_path = tmp_path / "distribution.json"
    _write_prediction_input(input_path)

    exit_code = main(
        [
            "predict",
            "--input",
            str(input_path),
            "--distribution",
            "--count",
            "5",
            "--position-scale",
            "1e-7",
            "--velocity-scale",
            "1e-7",
            "--samples",
            "16",
            "--include-sample-positions",
            "--output",
            str(output_path),
        ]
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["prediction_type"] == "empirical-position-distribution"
    assert payload["success_count"] == 5
    assert payload["failure_count"] == 0
    assert len(payload["position_distribution"]["mean_positions"]) == 3
    assert len(payload["sample_predictions"]) == 5


def test_predict_cli_writes_distribution_ephemeris(tmp_path) -> None:
    input_path = tmp_path / "initial-state.json"
    output_path = tmp_path / "distribution-ephemeris.json"
    _write_prediction_input(input_path)

    exit_code = main(
        [
            "predict",
            "--input",
            str(input_path),
            "--distribution-ephemeris",
            "--count",
            "5",
            "--position-scale",
            "1e-7",
            "--velocity-scale",
            "1e-7",
            "--samples",
            "9",
            "--include-sample-ephemerides",
            "--output",
            str(output_path),
        ]
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["prediction_type"] == "empirical-position-distribution-ephemeris"
    assert payload["success_count"] == 5
    assert payload["failure_count"] == 0
    assert len(payload["times"]) == 9
    assert len(payload["position_distribution_ephemeris"]["mean_positions"]) == 9
    assert len(payload["position_distribution_ephemeris"]["mean_positions"][0]) == 3
    assert len(payload["position_distribution_ephemeris"]["flat_covariances"][0]) == 6
    assert len(payload["position_distribution_ephemeris"]["position_confidence_regions"]) == 9
    assert payload["ensemble_close_approach_diagnostics"]["sample_count"] == 5
    assert len(payload["sample_ephemerides"]) == 5


def test_predict_cli_writes_solution_bundle(tmp_path) -> None:
    input_path = tmp_path / "initial-state.json"
    output_path = tmp_path / "solution.json"
    _write_prediction_input(input_path)

    exit_code = main(
        [
            "predict",
            "--input",
            str(input_path),
            "--solution",
            "--count",
            "5",
            "--position-scale",
            "1e-7",
            "--velocity-scale",
            "1e-7",
            "--samples",
            "9",
            "--horizon-samples",
            "6",
            "--output",
            str(output_path),
        ]
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["prediction_type"] == "three-body-prediction-solution"
    assert payload["prediction_summary"]["summary_schema_version"] == 1
    assert payload["prediction_summary"]["claim"] in {
        "target-position-and-distribution",
        "distributional-target-position",
        "deterministic-target-position",
        "unresolved-target-position",
    }
    assert payload["prediction_summary"]["recommended_mode"] == payload["answer"]["recommended_mode"]
    assert "position_statement" in payload["prediction_summary"]
    assert len(payload["prediction_summary"]["confidence_regions_95"]) == 3
    assert len(payload["prediction_summary"]["body_95_confidence_regions"]) == 3
    assert payload["prediction_summary"]["key_metrics"]["minimum_pair_distance"] > 0.0
    assert (
        payload["prediction_summary"]["key_metrics"]["minimum_pair_distance"]
        == payload["answer"]["minimum_pair_distance"]
    )
    statement = payload["mathematical_statement"]
    assert statement["statement_schema_version"] == 1
    assert statement["problem_type"] == "general-newtonian-three-body-initial-value-problem"
    assert statement["deterministic_problem"]["position_readout"] == "r_i(t) = Pi_{r_i} Phi_t(x(0))"
    assert statement["probability_problem"]["exact_pushforward"] == "Law(X_t) = (Phi_t)_# Law(X_0)."
    assert statement["claim_contract"]["promoted_claim"] == payload["prediction_summary"]["claim"]
    assert len(statement["body_position_claims"]) == 3
    assert statement["body_position_claims"][0]["deterministic_position"] == payload["answer"]["final_positions"][0]
    assert statement["body_position_claims"][0]["confidence_region_95"]["probability"] == 0.95
    assert payload["answer"]["recommended_mode"] in {"linearized-gaussian", "empirical-ensemble"}
    assert payload["answer"]["target_time_inside_forecast_horizon"] is True
    assert len(payload["answer"]["final_positions"]) == 3
    assert len(payload["answer"]["final_position_distribution"]["mean_positions"]) == 3
    assert len(payload["answer"]["final_position_distribution"]["position_confidence_regions"]) == 3
    assert payload["deterministic_ephemeris"]["prediction_type"] == "deterministic-ephemeris"
    assert payload["distribution_ephemeris"]["prediction_type"] == "empirical-position-distribution-ephemeris"
    assert payload["linearized_gaussian_ephemeris"]["prediction_type"] == "linearized-gaussian-ephemeris"
    assert payload["ephemeris_distribution_comparison"]["row_count"] == 9
    assert payload["ephemeris_distribution_comparison"]["final_covariance_relative_gap"] >= 0.0
    assert payload["answer"]["uncertainty_amplification_factor"] >= 1.0
    assert payload["answer"]["minimum_pair_distance"] > 0.0
    assert payload["interpretation_report"]["prediction_type"] == "three-body-interpretation-report"


def test_predict_cli_writes_compact_target_solution(tmp_path) -> None:
    input_path = tmp_path / "initial-state.json"
    output_path = tmp_path / "target-solution.json"
    _write_prediction_input(input_path)

    exit_code = main(
        [
            "predict",
            "--input",
            str(input_path),
            "--target-solution",
            "--count",
            "5",
            "--position-scale",
            "1e-7",
            "--velocity-scale",
            "1e-7",
            "--samples",
            "9",
            "--horizon-samples",
            "6",
            "--output",
            str(output_path),
        ]
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["prediction_type"] == "three-body-target-position-solution"
    assert payload["claim"] in {
        "target-position-and-distribution",
        "distributional-target-position",
        "deterministic-target-position",
        "unresolved-target-position",
    }
    assert payload["recommended_mode"] in {"linearized-gaussian", "empirical-ensemble"}
    assert len(payload["target_positions"]) == 3
    assert len(payload["target_position_distribution"]["mean_positions"]) == 3
    assert len(payload["target_position_table"]) == 3
    assert payload["target_position_table"][0]["body_index"] == 0
    assert payload["target_position_table"][0]["deterministic_position"] == payload["target_positions"][0]
    assert len(payload["target_position_table"][0]["central_90_interval"]["lower"]) == 2
    assert len(payload["target_position_table"][0]["central_90_interval"]["upper"]) == 2
    assert payload["target_position_table"][0]["confidence_region_95"]["max_semi_axis"] >= 0.0
    assert payload["target_position_table"][0]["confidence_region_95"]["relative_95_radius"] >= 0.0
    assert payload["target_position_table"][0]["characteristic_position_scale"] > 0.0
    assert payload["target_position_table"][0]["position_claim_strength"] in {
        "point-resolved",
        "localized-distribution",
        "broad-distribution",
    }
    assert payload["target_position_table"][0]["recommended_readout"] in {
        "point-position-with-confidence-region",
        "probability-region",
        "distribution-summary-only",
    }
    assert payload["target_position_table"][0]["deterministic_to_mean_distance"] >= 0.0
    assert payload["target_position_table"][0]["deterministic_to_mean_distance_relative"] >= 0.0
    center_frame = payload["center_of_mass_frame"]
    assert center_frame["frame"] == "mass-weighted-center-of-mass"
    assert center_frame["total_mass"] == 3.0
    assert len(center_frame["target_center_position"]) == 2
    assert len(center_frame["target_positions_relative_to_center"]) == 3
    assert len(center_frame["distribution_mean_relative_to_center"]) == 3
    assert center_frame["target_center_speed"] >= 0.0
    assert (
        payload["deterministic_flow_answer"]["positions_relative_to_center_of_mass"]
        == center_frame["target_positions_relative_to_center"]
    )
    assert (
        payload["probability_answer"]["mean_positions_relative_to_center_of_mass"]
        == center_frame["distribution_mean_relative_to_center"]
    )
    pair_geometry = payload["target_pair_geometry"]
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
    assert payload["deterministic_flow_answer"]["pair_geometry"] == pair_geometry["deterministic"]
    assert payload["probability_answer"]["pair_geometry"] == pair_geometry["probability"]
    assert len(payload["body_answers"]) == 3
    assert payload["body_answers"][0]["deterministic_position"] == payload["target_positions"][0]
    assert payload["deterministic_flow_answer"]["definition"] == "r_i(t) = Pi_{r_i} Phi_t(x(0))"
    assert payload["probability_answer"]["definition"] == "Law(X_t) = (Phi_t)_# Law(X_0)"
    assert payload["probability_answer"]["target_position_table"] == payload["target_position_table"]
    assert len(payload["probability_answer"]["confidence_regions_95"]) == 3
    assert payload["diagnostics"]["minimum_pair_distance"] > 0.0
    assert payload["mathematical_statement"]["statement_schema_version"] == 1
    assert "solution_bundle" not in payload


def test_predict_cli_writes_linearized_position_distribution(tmp_path) -> None:
    input_path = tmp_path / "initial-state.json"
    output_path = tmp_path / "linearized-distribution.json"
    _write_prediction_input(input_path)

    exit_code = main(
        [
            "predict",
            "--input",
            str(input_path),
            "--linearized-distribution",
            "--position-scale",
            "1e-7",
            "--velocity-scale",
            "1e-7",
            "--preserve-center-of-mass",
            "--output",
            str(output_path),
        ]
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["prediction_type"] == "linearized-gaussian-position-distribution"
    assert payload["success"] is True
    assert payload["uncertainty_model"]["preserve_center_of_mass"] is True
    assert len(payload["mean_positions"]) == 3
    assert len(payload["position_covariance"]) == 6
    assert len(payload["position_confidence_regions"]) == 3
    assert payload["linearized_diagnostics"]["maximum_position_std"] > 0.0
    assert payload["linearized_diagnostics"]["uncertainty_amplification_factor"] >= 1.0


def test_predict_cli_uses_explicit_initial_covariance_for_distribution(tmp_path) -> None:
    input_path = tmp_path / "initial-state.json"
    output_path = tmp_path / "distribution.json"
    _write_prediction_input(input_path)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    covariance = [[0.0 for _column in range(12)] for _row in range(12)]
    for index in range(12):
        covariance[index][index] = 1.0e-14
    covariance[0][2] = covariance[2][0] = 2.0e-15
    payload["initial_state_covariance"] = covariance
    input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    exit_code = main(
        [
            "predict",
            "--input",
            str(input_path),
            "--distribution",
            "--count",
            "7",
            "--output",
            str(output_path),
        ]
    )
    result = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert result["prediction_type"] == "empirical-position-distribution"
    assert result["uncertainty_model"]["initial_state_covariance_supplied"] is True
    assert result["uncertainty_model"]["preserve_center_of_mass"] is False
    assert result["initial_state_covariance"] == covariance


def test_predict_cli_scores_candidate_positions(tmp_path) -> None:
    input_path = tmp_path / "initial-state.json"
    output_path = tmp_path / "position-score.json"
    _write_prediction_input(input_path)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    payload["candidate_positions"] = payload["positions"]
    input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    exit_code = main(
        [
            "predict",
            "--input",
            str(input_path),
            "--score-positions",
            "--position-scale",
            "1e-7",
            "--velocity-scale",
            "1e-7",
            "--output",
            str(output_path),
        ]
    )
    result = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert result["prediction_type"] == "three-body-position-hypothesis-score"
    assert len(result["body_scores"]) == 3
    assert result["joint_score"]["mahalanobis_distance"] >= 0.0
    assert "0.95" in result["joint_score"]["inside_confidence_levels"]


def test_predict_cli_writes_linearized_ephemeris(tmp_path) -> None:
    input_path = tmp_path / "initial-state.json"
    output_path = tmp_path / "linearized-ephemeris.json"
    _write_prediction_input(input_path)

    exit_code = main(
        [
            "predict",
            "--input",
            str(input_path),
            "--linearized-ephemeris",
            "--position-scale",
            "1e-7",
            "--velocity-scale",
            "1e-7",
            "--preserve-center-of-mass",
            "--samples",
            "9",
            "--output",
            str(output_path),
        ]
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["prediction_type"] == "linearized-gaussian-ephemeris"
    assert payload["success"] is True
    assert payload["uncertainty_model"]["preserve_center_of_mass"] is True
    assert len(payload["times"]) == 9
    assert len(payload["rows"]) == 9
    assert len(payload["rows"][0]["mean_positions"]) == 3
    assert len(payload["rows"][0]["position_covariance"]) == 6
    assert len(payload["rows"][0]["position_confidence_regions"]) == 3
    assert payload["rows"][-1]["linearized_sensitivity"]["uncertainty_amplification_factor"] >= 1.0


def test_predict_cli_writes_interpretation_report(tmp_path) -> None:
    input_path = tmp_path / "initial-state.json"
    output_path = tmp_path / "prediction-report.json"
    _write_prediction_input(input_path)

    exit_code = main(
        [
            "predict",
            "--input",
            str(input_path),
            "--report",
            "--count",
            "5",
            "--position-scale",
            "1e-7",
            "--velocity-scale",
            "1e-7",
            "--samples",
            "16",
            "--output",
            str(output_path),
        ]
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["prediction_type"] == "three-body-interpretation-report"
    assert payload["uncertainty_model"]["preserve_center_of_mass"] is True
    assert payload["forecast_horizon"]["prediction_type"] == "linearized-forecast-horizon"
    assert payload["forecast_horizon"]["target_time_resolved"] is True
    assert payload["verdict"]["recommended_mode"] in {"linearized-gaussian", "empirical-ensemble"}
    assert payload["comparison"]["covariance_relative_gap"] >= 0.0


def test_predict_cli_writes_forecast_horizon(tmp_path) -> None:
    input_path = tmp_path / "initial-state.json"
    output_path = tmp_path / "forecast-horizon.json"
    _write_prediction_input(input_path)

    exit_code = main(
        [
            "predict",
            "--input",
            str(input_path),
            "--horizon",
            "--position-scale",
            "1e-7",
            "--velocity-scale",
            "1e-7",
            "--position-tolerance",
            "1e-3",
            "--preserve-center-of-mass",
            "--horizon-samples",
            "6",
            "--output",
            str(output_path),
        ]
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["prediction_type"] == "linearized-forecast-horizon"
    assert payload["target_time_resolved"] is True
    assert payload["uncertainty_model"]["preserve_center_of_mass"] is True
    assert payload["final_uncertainty_to_tolerance_ratio"] < 1.0
    assert len(payload["rows"]) == 6


def test_verify_static_artifacts_cli_checks_manifest_hashes(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    receipt_path = tmp_path / "verification-receipt.json"

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc",
            "--require-gate",
            "symbolic_passes_stride_robustness",
            "--require-min",
            "promotion_gates.picard_contraction_reserve=0.1",
            "--require-min",
            "publication_pipeline.promotion_gate_pass_count=7",
            "--require-max",
            "metrics.picard_max_contraction=0.35",
            "--require-feature",
            "index-artifact-discoverability",
            "--require-feature",
            "active-profile-descriptor",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert receipt["verification_schema_version"] == 1
    assert receipt["verification_schema_features"] == [
        "artifact-availability",
        "json-parse-errors",
        "artifact-identity",
        "manifest-hash-algorithm",
        "index-artifact-discoverability",
        "publication-pipeline-links",
        "published-branch-line-ending-policy",
        "commit-provenance",
        "active-profile-descriptor",
        "profile-gates",
        "numeric-minimums",
        "numeric-maximums",
        "certificate-verifier-capability-digest",
    ]
    assert receipt["verification_schema_features_sha256"] == cli_module.static_artifact_verification_features_sha256(
        receipt["verification_schema_features"]
    )
    assert receipt["receipt_payload_sha256"] == cli_module.static_artifact_receipt_payload_sha256(receipt)
    retimestamped_receipt = {**receipt, "verified_at_utc": "2099-01-01T00:00:00Z"}
    assert cli_module.static_artifact_receipt_payload_sha256(retimestamped_receipt) == receipt["receipt_payload_sha256"]
    tampered_receipt = {**receipt, "verified": False}
    assert cli_module.static_artifact_receipt_payload_sha256(tampered_receipt) != receipt["receipt_payload_sha256"]
    assert receipt["certificate_verification_schema_features"] == receipt["verification_schema_features"]
    assert (
        receipt["certificate_verification_schema_features_sha256"] == receipt["verification_schema_features_sha256"]
    )
    assert receipt["required_feature_set_sha256"] is None
    assert receipt["checks"]["required_feature_set_sha256"] is True
    assert receipt["verifier"] == "threebody.cli verify-static-artifacts"
    assert receipt["verified_at_utc"].endswith("Z")
    assert receipt["verified"] is True
    assert receipt["checks"]["manifest_json"] is True
    assert receipt["checks"]["manifest_hash_algorithm"] is True
    assert receipt["checks"]["certificate_json"] is True
    assert receipt["checks"]["certificate_verification_schema_features"] is True
    assert receipt["checks"]["certificate_verification_schema_features_sha256"] is True
    assert receipt["parse_errors"] == {"certificate.json": None, "manifest.json": None}
    assert receipt["artifact_errors"] == {
        "certificate.json": None,
        "favicon.svg": None,
        ".gitattributes": None,
        "index.html": None,
        "manifest.json": None,
    }
    assert receipt["checks"]["index_available"] is True
    assert receipt["checks"]["certificate_available"] is True
    assert receipt["checks"]["favicon_available"] is True
    assert receipt["checks"]["gitattributes_available"] is True
    assert receipt["checks"]["manifest_available"] is True
    assert receipt["checks"]["required_commit"] is True
    assert receipt["checks"]["required_gates"] is True
    assert receipt["checks"]["required_minimums"] is True
    assert receipt["checks"]["required_maximums"] is True
    assert receipt["checks"]["required_features"] is True
    assert receipt["required_features"] == ["index-artifact-discoverability", "active-profile-descriptor"]
    assert receipt["required_feature_results"] == [
        {"feature": "index-artifact-discoverability", "passed": True},
        {"feature": "active-profile-descriptor", "passed": True},
    ]
    assert receipt["checks"]["index_certificate_link"] is True
    assert receipt["checks"]["index_manifest_link"] is True
    assert receipt["checks"]["index_favicon_link"] is True
    assert receipt["checks"]["favicon_hash"] is True
    assert receipt["checks"]["favicon_size"] is True
    assert receipt["checks"]["gitattributes_hash"] is True
    assert receipt["checks"]["gitattributes_size"] is True
    assert receipt["checks"]["gitattributes_policy"] is True
    assert receipt["required_gates"] == ["symbolic_passes_stride_robustness"]
    assert receipt["required_gate_results"]["symbolic_passes_stride_robustness"] is True
    assert receipt["required_minimum_results"][0]["path"] == "promotion_gates.picard_contraction_reserve"
    assert receipt["required_minimum_results"][0]["passed"] is True
    assert receipt["required_maximum_results"][0]["path"] == "metrics.picard_max_contraction"
    assert receipt["required_maximum_results"][0]["passed"] is True


def test_verify_static_artifacts_cli_rejects_unexpected_commit(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)

    exit_code = main(["verify-static-artifacts", "--site-dir", str(tmp_path), "--require-commit", "wrong"])

    assert exit_code == 1


def test_verify_static_artifacts_cli_rejects_manifest_hash_algorithm_mismatch(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    receipt_path = tmp_path / "hash-algorithm-receipt.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["hash_algorithm"] = "sha1"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["manifest_hash_algorithm"] is False
    assert receipt["checks"]["index_hash"] is True
    assert receipt["checks"]["certificate_hash"] is True
    assert receipt["checks"]["favicon_hash"] is True


def test_verify_static_artifacts_cli_rejects_wrong_gitattributes_policy(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    receipt_path = tmp_path / "gitattributes-policy-receipt.json"
    (tmp_path / ".gitattributes").write_text("* text=auto\n", encoding="utf-8", newline="\n")
    _refresh_manifest_hashes(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-public-claim",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["gitattributes_available"] is True
    assert receipt["checks"]["gitattributes_hash"] is True
    assert receipt["checks"]["gitattributes_size"] is True
    assert receipt["checks"]["gitattributes_policy"] is False
    assert "published-branch-line-ending-policy" in receipt["verification_schema_features"]


def test_verify_static_artifacts_cli_rejects_missing_required_feature(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    receipt_path = tmp_path / "missing-feature-receipt.json"

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-feature",
            "not-a-real-feature",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["required_features"] is False
    assert receipt["required_features"] == ["not-a-real-feature"]
    assert receipt["required_feature_results"] == [{"feature": "not-a-real-feature", "passed": False}]
    assert receipt["checks"]["index_hash"] is True


def test_verify_static_artifacts_cli_can_pin_current_feature_set_digest(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    receipt_path = tmp_path / "current-feature-set-digest-receipt.json"

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-current-feature-set",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    expected_digest = cli_module.static_artifact_verification_features_sha256(
        cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
    )

    assert exit_code == 0
    assert receipt["verified"] is True
    assert receipt["required_feature_set_sha256"] == expected_digest
    assert receipt["checks"]["required_feature_set_sha256"] is True
    assert receipt["checks"]["certificate_verification_schema_features_sha256"] is True


def test_verify_static_artifacts_cli_can_require_public_claim(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    receipt_path = tmp_path / "public-claim-receipt.json"

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-public-claim",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    expected_digest = cli_module.static_artifact_verification_features_sha256(
        cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
    )

    assert exit_code == 0
    assert receipt["verified"] is True
    assert receipt["required_profiles"] == ["public-claims-v1"]
    assert receipt["required_feature_set_sha256"] == expected_digest
    assert receipt["checks"]["required_profile_hashes"] is True
    assert receipt["checks"]["required_feature_set_sha256"] is True
    assert receipt["checks"]["required_gates"] is True
    assert receipt["checks"]["required_minimums"] is True
    assert receipt["checks"]["required_maximums"] is True


def test_verify_static_artifacts_api_can_require_public_claim(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    result = cli_module.verify_static_artifacts(
        tmp_path,
        require_commit="abc123",
        require_public_claim=True,
    )
    expected_digest = cli_module.static_artifact_verification_features_sha256(
        cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
    )

    assert result["verified"] is True
    assert result["required_profiles"] == ["public-claims-v1"]
    assert result["required_feature_set_sha256"] == expected_digest
    assert result["checks"]["required_profile_hashes"] is True
    assert result["checks"]["required_feature_set_sha256"] is True
    assert result["checks"]["required_gates"] is True
    assert result["checks"]["required_minimums"] is True
    assert result["checks"]["required_maximums"] is True


def test_verify_static_artifact_bytes_api_can_require_public_claim(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        "favicon.svg": (tmp_path / "favicon.svg").read_bytes(),
        ".gitattributes": (tmp_path / ".gitattributes").read_bytes(),
        "manifest.json": (tmp_path / "manifest.json").read_bytes(),
    }

    result = cli_module.verify_static_artifact_bytes(
        artifacts,
        source="direct-bytes",
        require_commit="abc123",
        require_public_claim=True,
    )
    expected_digest = cli_module.static_artifact_verification_features_sha256(
        cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
    )

    assert result["verified"] is True
    assert result["required_profiles"] == ["public-claims-v1"]
    assert result["required_feature_set_sha256"] == expected_digest
    assert result["checks"]["required_profile_hashes"] is True
    assert result["checks"]["required_feature_set_sha256"] is True


def test_verify_static_artifacts_cli_rejects_feature_set_digest_mismatch(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    receipt_path = tmp_path / "feature-set-digest-receipt.json"
    wrong_digest = "0" * 64

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-feature-set-sha256",
            wrong_digest,
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["required_feature_set_sha256"] == wrong_digest
    assert receipt["checks"]["required_feature_set_sha256"] is False
    assert receipt["checks"]["index_hash"] is True


def test_verify_static_artifacts_cli_rejects_certificate_verifier_feature_digest_mismatch(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    certificate_path = tmp_path / "certificate.json"
    receipt_path = tmp_path / "certificate-feature-digest-receipt.json"
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    certificate["verification_schema_features"] = ["artifact-availability"]
    certificate["verification_schema_features_sha256"] = "0" * 64
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    _refresh_manifest_hashes(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["certificate_hash"] is True
    assert receipt["certificate_verification_schema_features"] == ["artifact-availability"]
    assert receipt["certificate_verification_schema_features_sha256"] == "0" * 64
    assert receipt["checks"]["certificate_verification_schema_features"] is False
    assert receipt["checks"]["certificate_verification_schema_features_sha256"] is False
    assert receipt["checks"]["required_profile_hashes"] is True


def test_verify_static_artifacts_cli_rejects_index_without_manifest_link(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    index_path = tmp_path / "index.html"
    receipt_path = tmp_path / "index-link-receipt.json"
    index_path.write_text(
        (
            '<html><head><link rel="icon" href="favicon.svg" type="image/svg+xml"></head>'
            '<body>ThreeBody Dynamics Lab <a href="certificate.json">certificate</a></body></html>'
        ),
        encoding="utf-8",
    )
    _refresh_manifest_hashes(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["index_certificate_link"] is True
    assert receipt["checks"]["index_manifest_link"] is False
    assert receipt["checks"]["index_favicon_link"] is True
    assert receipt["checks"]["index_hash"] is True


def test_verify_static_artifacts_cli_rejects_missing_required_gate(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)

    exit_code = main(["verify-static-artifacts", "--site-dir", str(tmp_path), "--require-gate", "missing_gate"])

    assert exit_code == 1


def test_verify_static_artifacts_cli_rejects_failed_minimum(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-min",
            "promotion_gates.picard_contraction_reserve=1.0",
        ]
    )

    assert exit_code == 1


def test_verify_static_artifacts_cli_rejects_failed_maximum(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-max",
            "metrics.picard_max_contraction=0.001",
        ]
    )

    assert exit_code == 1


def test_verify_static_artifacts_cli_applies_public_claim_profile(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    receipt_path = tmp_path / "profile-receipt.json"

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert receipt["verified"] is True
    assert receipt["checks"]["manifest_artifact"] is True
    assert receipt["checks"]["certificate_artifact"] is True
    assert receipt["checks"]["publication_pipeline_links"] is True
    assert receipt["required_profiles"] == ["public-claims-v1"]
    assert receipt["required_profile_hashes"] == {
        "public-claims-v1": cli_module.static_artifact_requirement_profile_sha256("public-claims-v1")
    }
    assert "index-artifact-discoverability" in receipt["required_profile_requirements"]["require_features"]
    assert receipt["required_profile_results"][0]["active_matches"] is True
    assert receipt["required_profile_results"][0]["active_hash_matches"] is True
    assert receipt["required_profile_results"][0]["descriptor_matches"] is True
    assert receipt["required_profile_results"][0]["descriptor_hash_matches"] is True
    assert receipt["required_profile_results"][0]["hash_matches"] is True
    assert receipt["required_profile_results"][0]["passed"] is True
    assert receipt["required_profile_requirements"]["require_gates"] == [
        "picard_certified",
        "poincare_markov_significant_baseline_win",
        "poincare_passes_permutation_control",
        "poincare_passes_section_robustness",
        "symbolic_passes_stride_robustness",
    ]
    assert "publication_pipeline.promotion_gate_pass_count=7" in receipt["required_minimums"]
    assert "metrics.picard_max_contraction=0.35" in receipt["required_maximums"]
    assert "index-artifact-discoverability" in receipt["required_features"]
    assert "active-profile-descriptor" in receipt["required_features"]
    assert receipt["checks"]["required_profile_hashes"] is True
    assert receipt["checks"]["required_gates"] is True
    assert receipt["checks"]["required_minimums"] is True
    assert receipt["checks"]["required_maximums"] is True
    assert receipt["checks"]["required_features"] is True
    assert all(row["feature"] in receipt["verification_schema_features"] for row in receipt["required_feature_results"])


def test_public_claim_profile_features_are_explicitly_versioned() -> None:
    descriptor = cli_module.static_artifact_requirement_profile_descriptor("public-claims-v1")
    required_features = descriptor["requirements"]["require_features"]

    assert tuple(required_features) == cli_module.PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE_FEATURES
    assert required_features == list(cli_module.PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE_FEATURES)
    assert set(required_features).issubset(set(cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES))
    assert "certificate-verifier-capability-digest" in cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
    assert "certificate-verifier-capability-digest" not in required_features
    assert required_features is not cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES


def test_required_feature_results_are_based_on_advertised_features() -> None:
    required = ["artifact-availability", "numeric-maximums", "missing-capability"]
    advertised = ["artifact-availability", "numeric-maximums"]

    results = cli_module._required_feature_results(required, advertised)

    assert results == [
        {"feature": "artifact-availability", "passed": True},
        {"feature": "numeric-maximums", "passed": True},
        {"feature": "missing-capability", "passed": False},
    ]


def test_verification_feature_digest_is_order_sensitive() -> None:
    features = ["artifact-availability", "numeric-maximums"]

    assert cli_module.static_artifact_verification_features_sha256(features) != (
        cli_module.static_artifact_verification_features_sha256(list(reversed(features)))
    )


def test_verify_static_artifacts_cli_rejects_inactive_required_profile(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    certificate_path = tmp_path / "certificate.json"
    receipt_path = tmp_path / "inactive-profile-receipt.json"
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    certificate["publication_pipeline"]["verification_profile"] = "local-draft-profile"
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    _refresh_manifest_hashes(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["required_profile_hashes"] is False
    assert receipt["required_profile_results"][0]["active_matches"] is False
    assert receipt["required_profile_results"][0]["active_hash_matches"] is False
    assert receipt["required_profile_results"][0]["descriptor_matches"] is True
    assert receipt["required_profile_results"][0]["passed"] is False


def test_verify_static_artifacts_cli_rejects_tampered_profile_descriptor(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    certificate_path = tmp_path / "certificate.json"
    receipt_path = tmp_path / "tampered-profile-receipt.json"
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    certificate["verification_profiles"]["public-claims-v1"]["requirements"]["require_gates"] = [
        "picard_certified",
    ]
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    _refresh_manifest_hashes(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["required_profile_hashes"] is False
    assert receipt["required_profile_results"][0]["active_matches"] is True
    assert receipt["required_profile_results"][0]["active_hash_matches"] is True
    assert receipt["required_profile_results"][0]["descriptor_hash_matches"] is True
    assert receipt["required_profile_results"][0]["descriptor_matches"] is False
    assert receipt["required_profile_results"][0]["passed"] is False


def test_verify_static_artifacts_cli_rejects_mismatched_publication_pipeline_links(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    certificate_path = tmp_path / "certificate.json"
    receipt_path = tmp_path / "pipeline-link-receipt.json"
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    certificate["publication_pipeline"]["integrity_manifest"] = "draft-manifest.json"
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    _refresh_manifest_hashes(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["certificate_hash"] is True
    assert receipt["checks"]["favicon_hash"] is True
    assert receipt["checks"]["publication_pipeline_links"] is False
    assert receipt["checks"]["required_profile_hashes"] is True


def test_verify_static_artifacts_cli_reports_invalid_nested_json_shapes(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    certificate_path = tmp_path / "certificate.json"
    manifest_path = tmp_path / "manifest.json"
    receipt_path = tmp_path / "invalid-shapes-receipt.json"
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    certificate["build_provenance"] = "not-an-object"
    manifest["build_provenance"] = "not-an-object"
    manifest["artifacts"] = []
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["commit_sha"] is None
    assert receipt["commit_sha_short"] is None
    assert receipt["checks"]["provenance_commit_match"] is False
    assert receipt["checks"]["required_commit"] is False
    assert receipt["checks"]["index_hash"] is False
    assert receipt["checks"]["certificate_hash"] is False
    assert receipt["checks"]["favicon_hash"] is False
    assert receipt["checks"]["index_size"] is False
    assert receipt["checks"]["certificate_size"] is False
    assert receipt["checks"]["favicon_size"] is False


def test_verify_static_artifacts_cli_reports_invalid_json_without_crashing(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    certificate_path = tmp_path / "certificate.json"
    manifest_path = tmp_path / "manifest.json"
    receipt_path = tmp_path / "invalid-json-receipt.json"
    certificate_path.write_text("{not-json", encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"]["certificate.json"]["sha256"] = _sha256(certificate_path)
    manifest["artifacts"]["certificate.json"]["bytes"] = certificate_path.stat().st_size
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["manifest_json"] is True
    assert receipt["checks"]["certificate_json"] is False
    assert receipt["checks"]["certificate_hash"] is True
    assert receipt["checks"]["certificate_size"] is True
    assert receipt["checks"]["required_profile_hashes"] is False
    assert receipt["parse_errors"]["manifest.json"] is None
    assert "Expecting property name" in receipt["parse_errors"]["certificate.json"]


def test_verify_static_artifacts_cli_reports_missing_local_artifact_without_crashing(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    favicon_path = tmp_path / "favicon.svg"
    receipt_path = tmp_path / "missing-favicon-receipt.json"
    favicon_path.unlink()

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["favicon_available"] is False
    assert receipt["checks"]["favicon_hash"] is False
    assert receipt["checks"]["favicon_size"] is False
    assert receipt["checks"]["manifest_available"] is True
    assert receipt["checks"]["required_profile_hashes"] is True
    assert "favicon.svg" in receipt["artifact_errors"]["favicon.svg"]


def test_verify_static_artifacts_from_url_reports_fetch_error(monkeypatch, tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        ".gitattributes": (tmp_path / ".gitattributes").read_bytes(),
        "manifest.json": (tmp_path / "manifest.json").read_bytes(),
    }

    class FakeResponse:
        def __init__(self, data: bytes) -> None:
            self.data = data

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return self.data

    def fake_urlopen(request, timeout: int) -> FakeResponse:
        artifact_name = request.full_url.rstrip("/").rsplit("/", 1)[-1]
        if artifact_name == "favicon.svg":
            raise OSError("simulated missing favicon")
        return FakeResponse(artifacts[artifact_name])

    monkeypatch.setattr(cli_module, "urlopen", fake_urlopen)

    result = cli_module.verify_static_artifacts_from_url(
        "https://example.test/3body",
        require_commit="abc123",
        require_profiles=["public-claims-v1"],
        require_features=["manifest-hash-algorithm"],
        require_feature_set_sha256=cli_module.static_artifact_verification_features_sha256(
            cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
        ),
    )

    assert result["verified"] is False
    assert result["checks"]["favicon_available"] is False
    assert result["checks"]["favicon_hash"] is False
    assert result["checks"]["favicon_size"] is False
    assert result["checks"]["manifest_available"] is True
    assert result["checks"]["required_profile_hashes"] is True
    assert result["artifact_errors"]["favicon.svg"] == "simulated missing favicon"


def test_verify_static_artifact_bytes_reports_missing_direct_artifact_key(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        ".gitattributes": (tmp_path / ".gitattributes").read_bytes(),
        "manifest.json": (tmp_path / "manifest.json").read_bytes(),
    }

    result = cli_module.verify_static_artifact_bytes(
        artifacts,
        source="direct-bytes",
        require_commit="abc123",
        require_profiles=["public-claims-v1"],
    )

    assert result["verified"] is False
    assert result["checks"]["favicon_available"] is False
    assert result["checks"]["favicon_hash"] is False
    assert result["checks"]["favicon_size"] is False
    assert result["checks"]["required_profile_hashes"] is True
    assert result["artifact_errors"]["favicon.svg"] == "artifact missing from provided bytes"


def test_verify_static_artifact_bytes_does_not_let_partial_error_map_hide_missing_key(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        ".gitattributes": (tmp_path / ".gitattributes").read_bytes(),
        "manifest.json": (tmp_path / "manifest.json").read_bytes(),
    }

    result = cli_module.verify_static_artifact_bytes(
        artifacts,
        source="direct-bytes",
        artifact_errors={"index.html": None, "certificate.json": None, "manifest.json": None},
        require_commit="abc123",
        require_profiles=["public-claims-v1"],
    )

    assert result["verified"] is False
    assert result["checks"]["favicon_available"] is False
    assert result["artifact_errors"]["favicon.svg"] == "artifact missing from provided bytes"


def test_verify_static_artifact_bytes_reports_malformed_error_map_without_crashing(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        "favicon.svg": (tmp_path / "favicon.svg").read_bytes(),
        ".gitattributes": (tmp_path / ".gitattributes").read_bytes(),
        "manifest.json": (tmp_path / "manifest.json").read_bytes(),
    }

    result = cli_module.verify_static_artifact_bytes(
        artifacts,
        source="direct-bytes",
        artifact_errors=["not", "a", "mapping"],  # type: ignore[arg-type]
        require_commit="abc123",
        require_profiles=["public-claims-v1"],
    )

    assert result["verified"] is False
    assert result["checks"]["index_available"] is False
    assert result["checks"]["index_hash"] is True
    assert result["artifact_errors"]["index.html"] == "artifact_errors is list, expected mapping"


def test_verify_static_artifact_bytes_reports_non_bytes_payload_without_crashing(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        "favicon.svg": "<svg></svg>",
        ".gitattributes": (tmp_path / ".gitattributes").read_bytes(),
        "manifest.json": (tmp_path / "manifest.json").read_bytes(),
    }

    result = cli_module.verify_static_artifact_bytes(
        artifacts,  # type: ignore[arg-type]
        source="direct-bytes",
        require_commit="abc123",
        require_profiles=["public-claims-v1"],
    )

    assert result["verified"] is False
    assert result["checks"]["favicon_available"] is False
    assert result["checks"]["favicon_hash"] is False
    assert result["checks"]["favicon_size"] is False
    assert result["checks"]["required_profile_hashes"] is True
    assert result["artifact_errors"]["favicon.svg"] == "artifact payload is str, expected bytes-like"


def test_verify_static_artifacts_cli_checks_public_url_manifest(monkeypatch, tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        "favicon.svg": (tmp_path / "favicon.svg").read_bytes(),
        ".gitattributes": (tmp_path / ".gitattributes").read_bytes(),
        "manifest.json": (tmp_path / "manifest.json").read_bytes(),
    }
    requested_urls: list[str] = []

    class FakeResponse:
        def __init__(self, data: bytes) -> None:
            self.data = data

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return self.data

    def fake_urlopen(request, timeout: int) -> FakeResponse:
        requested_urls.append(request.full_url)
        artifact_name = request.full_url.rstrip("/").rsplit("/", 1)[-1]
        return FakeResponse(artifacts[artifact_name])

    monkeypatch.setattr(cli_module, "urlopen", fake_urlopen)

    result = cli_module.verify_static_artifacts_from_url(
        "https://example.test/3body",
        require_commit="abc123",
        require_profiles=["public-claims-v1"],
        require_features=["manifest-hash-algorithm"],
        require_feature_set_sha256=cli_module.static_artifact_verification_features_sha256(
            cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
        ),
    )

    assert result["verified"] is True
    assert result["source"] == "https://example.test/3body/"
    assert result["required_commit"] == "abc123"
    assert result["verification_schema_version"] == 1
    assert "index-artifact-discoverability" in result["verification_schema_features"]
    assert "active-profile-descriptor" in result["verification_schema_features"]
    assert "manifest-hash-algorithm" in result["required_features"]
    assert "index-artifact-discoverability" in result["required_features"]
    assert result["required_feature_set_sha256"] == result["verification_schema_features_sha256"]
    assert result["checks"]["required_feature_set_sha256"] is True
    assert all(row["passed"] for row in result["required_feature_results"])
    assert result["verified_at_utc"].endswith("Z")
    assert result["checks"]["manifest_artifact"] is True
    assert result["checks"]["manifest_hash_algorithm"] is True
    assert result["checks"]["certificate_artifact"] is True
    assert result["checks"]["publication_pipeline_links"] is True
    assert result["required_profiles"] == ["public-claims-v1"]
    assert result["checks"]["required_commit"] is True
    assert result["checks"]["required_profile_hashes"] is True
    assert result["required_profile_results"][0]["active_profile"] == "public-claims-v1"
    assert result["checks"]["required_gates"] is True
    assert result["checks"]["required_minimums"] is True
    assert result["checks"]["required_maximums"] is True
    assert result["checks"]["index_certificate_link"] is True
    assert result["checks"]["index_manifest_link"] is True
    assert result["checks"]["index_favicon_link"] is True
    assert result["checks"]["favicon_hash"] is True
    assert result["checks"]["favicon_size"] is True
    assert result["checks"]["gitattributes_hash"] is True
    assert result["checks"]["gitattributes_size"] is True
    assert result["checks"]["gitattributes_policy"] is True
    assert result["required_gate_results"]["picard_certified"] is True
    assert result["required_minimum_results"][0]["passed"] is True
    assert result["required_maximum_results"][0]["passed"] is True
    assert requested_urls == [
        "https://example.test/3body/index.html",
        "https://example.test/3body/certificate.json",
        "https://example.test/3body/favicon.svg",
        "https://example.test/3body/.gitattributes",
        "https://example.test/3body/manifest.json",
    ]


def _write_static_artifact_bundle(site_dir) -> None:
    index_path = site_dir / "index.html"
    certificate_path = site_dir / "certificate.json"
    favicon_path = site_dir / "favicon.svg"
    gitattributes_path = site_dir / ".gitattributes"
    manifest_path = site_dir / "manifest.json"
    index_path.write_text(
        (
            '<html><head><link rel="icon" href="favicon.svg" type="image/svg+xml"></head>'
            '<body>ThreeBody Dynamics Lab <a href="certificate.json">certificate</a> '
            '<a href="manifest.json">manifest</a></body></html>'
        ),
        encoding="utf-8",
    )
    favicon_path.write_text("<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\"></svg>\n", encoding="utf-8")
    gitattributes_path.write_text("* text eol=lf\n", encoding="utf-8", newline="\n")
    profile_sha256 = cli_module.static_artifact_requirement_profile_sha256("public-claims-v1")
    verifier_feature_set = list(cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES)
    verifier_feature_set_sha256 = cli_module.static_artifact_verification_features_sha256(verifier_feature_set)
    certificate = {
        "certificate_schema_version": 1,
        "artifact": "threebody-static-research-certificate",
        "artifact_manifest": "manifest.json",
        "publication_pipeline": {
            "engine": "threebody.ui.static_site",
            "integrity_manifest": "manifest.json",
            "machine_readable_certificate": "certificate.json",
            "promotion_gate_pass_count": 7,
            "verification_profile": "public-claims-v1",
            "verification_profile_sha256": profile_sha256,
        },
        "verification_profiles": {
            "public-claims-v1": {
                **cli_module.static_artifact_requirement_profile_descriptor("public-claims-v1"),
                "sha256": profile_sha256,
            },
        },
        "verification_schema_features": verifier_feature_set,
        "verification_schema_features_sha256": verifier_feature_set_sha256,
        "metrics": {
            "general_max_energy_drift": 1.0e-10,
            "picard_max_contraction": 0.01,
            "restricted_max_jacobi_drift": 1.0e-12,
        },
        "build_provenance": {
            "commit_sha": "abc123",
            "commit_sha_short": "abc123",
        },
        "promotion_gates": {
            "picard_certified": True,
            "picard_contraction_reserve": 0.3437,
            "poincare_markov_significant_baseline_win": True,
            "poincare_passes_permutation_control": True,
            "poincare_passes_section_robustness": True,
            "poincare_section_robust_pass_fraction": 1.0,
            "symbolic_passes_stride_robustness": True,
            "symbolic_stride_robust_pass_fraction": 1.0,
        },
    }
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    manifest = {
        "manifest_schema_version": 1,
        "artifact": "threebody-static-site-manifest",
        "hash_algorithm": "sha256",
        "build_provenance": {
            "commit_sha": "abc123",
            "commit_sha_short": "abc123",
        },
        "artifacts": {
            "index.html": {
                "sha256": _sha256(index_path),
                "bytes": index_path.stat().st_size,
            },
            "certificate.json": {
                "sha256": _sha256(certificate_path),
                "bytes": certificate_path.stat().st_size,
            },
            "favicon.svg": {
                "sha256": _sha256(favicon_path),
                "bytes": favicon_path.stat().st_size,
            },
            ".gitattributes": {
                "sha256": _sha256(gitattributes_path),
                "bytes": gitattributes_path.stat().st_size,
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def _write_prediction_input(path) -> None:
    payload = {
        "masses": [1.0, 1.0, 1.0],
        "positions": [
            [0.97000436, -0.24308753],
            [-0.97000436, 0.24308753],
            [0.0, 0.0],
        ],
        "velocities": [
            [0.466203685, 0.43236573],
            [0.466203685, 0.43236573],
            [-0.93240737, -0.86473146],
        ],
        "target_time": 0.05,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _refresh_manifest_hashes(site_dir) -> None:
    manifest_path = site_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for artifact_name in ("index.html", "certificate.json", "favicon.svg", ".gitattributes"):
        artifact_path = site_dir / artifact_name
        manifest["artifacts"][artifact_name]["sha256"] = _sha256(artifact_path)
        manifest["artifacts"][artifact_name]["bytes"] = artifact_path.stat().st_size
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
