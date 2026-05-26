from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal

import numpy as np
from scipy.integrate import solve_ivp
from scipy.stats import chi2

from threebody.analysis import (
    AnalysisAtlas,
    ChartWordMarkovChain,
    ChartWordMarkovBaselineComparison,
    ChartWordMarkovBootstrapComparison,
    ChartWordMarkovValidation,
    ChartWordMarkovOrderSelection,
    bootstrap_markov_baseline_comparison,
    JacobiIntervalPicardFlowCertificate,
    JacobiPicardTuningCertificate,
    compare_markov_chain_to_independent_baseline,
    finite_difference_jacobian,
    jacobi_interval_picard_flow_certificate,
    jacobi_picard_tuning_certificate,
    markov_chain_from_words,
    permutation_control_markov_validation,
    poincare_markov_section_robustness,
    poincare_coordinate_sweep_from_reports,
    poincare_section_sweep_from_reports,
    poincare_section_word_from_reports,
    refined_chart_word_from_reports,
    return_map_word_from_reports,
    select_markov_order,
    validate_markov_chain,
)
from threebody.cli import (
    PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE,
    STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES,
    static_artifact_receipt_payload_sha256,
    static_artifact_requirement_profile_descriptor,
    static_artifact_requirement_profile_sha256,
    static_artifact_verification_features_sha256,
    verify_static_artifact_bytes,
    verify_static_artifacts,
    verify_static_artifacts_from_url,
)
from threebody.diagnostics import noether_invariant_drift_certificate
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator
from threebody.systems import GeneralThreeBodySystem
from threebody.types import Scenario, TrajectoryResult

ReferenceScenario = Literal["figure-eight", "hierarchical-flyby", "restricted-l4", "restricted-l5"]
WordMode = Literal["refined", "return", "poincare"]


def public_static_artifact_claim_contract() -> dict[str, object]:
    """Return the JSON-ready public Pages claim profile and verifier feature contract."""

    profile = PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE
    verification_schema_features = list(STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES)
    return {
        "contract_schema_version": 1,
        "profile": profile,
        "profile_sha256": static_artifact_requirement_profile_sha256(profile),
        "profile_descriptor": static_artifact_requirement_profile_descriptor(profile),
        "verification_schema_features": verification_schema_features,
        "verification_schema_features_sha256": static_artifact_verification_features_sha256(
            verification_schema_features
        ),
    }


def validate_public_static_artifact_receipt_contract(
    receipt: Mapping[str, object],
    contract: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Check whether a verifier receipt satisfies the stable public Pages claim contract."""

    contract = contract or public_static_artifact_claim_contract()
    profile = contract.get("profile")
    profile_sha256 = contract.get("profile_sha256")
    feature_set_sha256 = contract.get("verification_schema_features_sha256")
    required_profile_hashes = _mapping_field(receipt, "required_profile_hashes")
    receipt_payload_sha256 = receipt.get("receipt_payload_sha256")
    checks = {
        "receipt_verified": receipt.get("verified") is True,
        "receipt_payload_sha256_present": isinstance(receipt_payload_sha256, str) and len(receipt_payload_sha256) == 64,
        "receipt_payload_sha256_matches": receipt_payload_sha256 == static_artifact_receipt_payload_sha256(receipt),
        "required_profile_declared": profile in _sequence_field(receipt, "required_profiles"),
        "required_profile_hash_matches": required_profile_hashes.get(profile) == profile_sha256,
        "required_feature_set_sha256_matches": receipt.get("required_feature_set_sha256") == feature_set_sha256,
        "receipt_feature_set_sha256_matches": receipt.get("verification_schema_features_sha256") == feature_set_sha256,
        "certificate_feature_set_sha256_matches": receipt.get("certificate_verification_schema_features_sha256")
        == feature_set_sha256,
        "profile_hash_check_passed": _mapping_field(receipt, "checks").get("required_profile_hashes") is True,
        "feature_set_check_passed": _mapping_field(receipt, "checks").get("required_feature_set_sha256") is True,
    }
    return {
        "contract_schema_version": contract.get("contract_schema_version"),
        "profile": profile,
        "profile_sha256": profile_sha256,
        "verification_schema_features_sha256": feature_set_sha256,
        "receipt_payload_sha256": receipt_payload_sha256,
        "verified": all(checks.values()),
        "checks": checks,
    }


def public_static_artifact_audit_report_payload_sha256(audit_report: Mapping[str, object]) -> str:
    """Return a timestamp-independent canonical SHA-256 for a public Pages audit report."""

    payload = _audit_report_digest_payload(audit_report)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def verify_public_static_artifacts(
    site_dir: str | Path,
    *,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
) -> dict[str, object]:
    """Verify a generated static evidence directory against the public claim profile."""

    return verify_static_artifacts(
        Path(site_dir),
        require_commit=require_commit,
        require_gates=require_gates,
        require_minimums=require_minimums,
        require_maximums=require_maximums,
        require_features=require_features,
        require_feature_set_sha256=require_feature_set_sha256,
        require_public_claim=True,
    )


def audit_public_static_artifacts(
    site_dir: str | Path,
    *,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
) -> dict[str, object]:
    """Return a self-contained public Pages audit report for a generated static directory."""

    receipt = verify_public_static_artifacts(
        site_dir,
        require_commit=require_commit,
        require_gates=require_gates,
        require_minimums=require_minimums,
        require_maximums=require_maximums,
        require_features=require_features,
        require_feature_set_sha256=require_feature_set_sha256,
    )
    return _public_static_artifact_audit_report(receipt)


def verify_public_static_artifacts_from_url(
    base_url: str,
    *,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
) -> dict[str, object]:
    """Verify a public static evidence bundle URL against the public claim profile."""

    return verify_static_artifacts_from_url(
        base_url,
        require_commit=require_commit,
        require_gates=require_gates,
        require_minimums=require_minimums,
        require_maximums=require_maximums,
        require_features=require_features,
        require_feature_set_sha256=require_feature_set_sha256,
        require_public_claim=True,
    )


def audit_public_static_artifacts_from_url(
    base_url: str,
    *,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
) -> dict[str, object]:
    """Return a self-contained public Pages audit report for a public static URL."""

    receipt = verify_public_static_artifacts_from_url(
        base_url,
        require_commit=require_commit,
        require_gates=require_gates,
        require_minimums=require_minimums,
        require_maximums=require_maximums,
        require_features=require_features,
        require_feature_set_sha256=require_feature_set_sha256,
    )
    return _public_static_artifact_audit_report(receipt)


def verify_public_static_artifact_bytes(
    artifacts: dict[str, bytes],
    *,
    source: str = "direct-bytes",
    artifact_errors: dict[str, str | None] | None = None,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
) -> dict[str, object]:
    """Verify in-memory static evidence artifacts against the public claim profile."""

    return verify_static_artifact_bytes(
        artifacts,
        source=source,
        artifact_errors=artifact_errors,
        require_commit=require_commit,
        require_gates=require_gates,
        require_minimums=require_minimums,
        require_maximums=require_maximums,
        require_features=require_features,
        require_feature_set_sha256=require_feature_set_sha256,
        require_public_claim=True,
    )


def audit_public_static_artifact_bytes(
    artifacts: dict[str, bytes],
    *,
    source: str = "direct-bytes",
    artifact_errors: dict[str, str | None] | None = None,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
) -> dict[str, object]:
    """Return a self-contained public Pages audit report for in-memory static artifacts."""

    receipt = verify_public_static_artifact_bytes(
        artifacts,
        source=source,
        artifact_errors=artifact_errors,
        require_commit=require_commit,
        require_gates=require_gates,
        require_minimums=require_minimums,
        require_maximums=require_maximums,
        require_features=require_features,
        require_feature_set_sha256=require_feature_set_sha256,
    )
    return _public_static_artifact_audit_report(receipt)


def _public_static_artifact_audit_report(receipt: Mapping[str, object]) -> dict[str, object]:
    contract = public_static_artifact_claim_contract()
    receipt_contract_validation = validate_public_static_artifact_receipt_contract(receipt, contract)
    report = {
        "audit_schema_version": 1,
        "verified": receipt.get("verified") is True and receipt_contract_validation["verified"] is True,
        "contract": contract,
        "receipt": dict(receipt),
        "receipt_contract_validation": receipt_contract_validation,
    }
    report["audit_payload_sha256"] = public_static_artifact_audit_report_payload_sha256(report)
    return report


def _audit_report_digest_payload(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _audit_report_digest_payload(item)
            for key, item in value.items()
            if key not in {"audit_payload_sha256", "verified_at_utc"}
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_audit_report_digest_payload(item) for item in value]
    return value


def _mapping_field(payload: Mapping[str, object], key: str) -> Mapping[object, object]:
    value = payload.get(key)
    return value if isinstance(value, Mapping) else {}


def _sequence_field(payload: Mapping[str, object], key: str) -> tuple[object, ...]:
    value = payload.get(key)
    if isinstance(value, str) or not isinstance(value, Sequence):
        return ()
    return tuple(value)


def predict_three_body_positions(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    samples: int = 256,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    max_step: float = math.inf,
) -> dict[str, object]:
    """Predict the three body positions at ``target_time`` by high-precision integration.

    This is the practical answer to the generic three-body prediction problem:
    for arbitrary masses and initial state, the engine returns a controlled
    numerical forecast plus conservation diagnostics rather than claiming a
    global closed-form solution.
    """

    system, initial_state = _general_prediction_system(
        masses,
        positions,
        velocities,
        gravitational_constant=gravitational_constant,
        softening=softening,
    )
    target_time = _finite_float(target_time, "target_time")
    trajectory = _prediction_trajectory(
        system,
        initial_state,
        target_time,
        samples=samples,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
    final_state = trajectory.y[-1] if len(trajectory.y) else np.full(system.state_dim, np.nan)
    final_positions, final_velocities = system.split_state(final_state)
    invariant_certificate = noether_invariant_drift_certificate(system, trajectory).as_dict()
    return {
        "prediction_schema_version": 1,
        "prediction_type": "deterministic-position",
        "method": "adaptive-DOP853",
        "target_time": target_time,
        "dimension": system.dimension,
        "masses": [float(mass) for mass in system.masses],
        "gravitational_constant": float(system.gravitational_constant),
        "softening": float(system.softening),
        "success": trajectory.success,
        "message": trajectory.message,
        "positions": final_positions.tolist(),
        "velocities": final_velocities.tolist(),
        "final_state": final_state.tolist(),
        "sample_count": int(len(trajectory.t)),
        "solver": dict(trajectory.metadata),
        "invariant_certificate": invariant_certificate,
    }


def predict_three_body_ephemeris(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    samples: int = 256,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    max_step: float = math.inf,
    include_invariant_series: bool = False,
) -> dict[str, object]:
    """Return sampled positions and velocities from time 0 through ``target_time``."""

    system, initial_state = _general_prediction_system(
        masses,
        positions,
        velocities,
        gravitational_constant=gravitational_constant,
        softening=softening,
    )
    target_time = _finite_float(target_time, "target_time")
    trajectory = _prediction_trajectory(
        system,
        initial_state,
        target_time,
        samples=samples,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
    positions_series, velocities_series = _trajectory_position_velocity_series(system, trajectory)
    final_state = trajectory.y[-1] if len(trajectory.y) else np.full(system.state_dim, np.nan)
    invariant_certificate = noether_invariant_drift_certificate(system, trajectory).as_dict()
    result: dict[str, object] = {
        "prediction_schema_version": 1,
        "prediction_type": "deterministic-ephemeris",
        "method": "adaptive-DOP853",
        "target_time": target_time,
        "dimension": system.dimension,
        "masses": [float(mass) for mass in system.masses],
        "gravitational_constant": float(system.gravitational_constant),
        "softening": float(system.softening),
        "success": trajectory.success,
        "message": trajectory.message,
        "times": trajectory.t.tolist(),
        "positions": positions_series.tolist(),
        "velocities": velocities_series.tolist(),
        "final_state": final_state.tolist(),
        "sample_count": int(len(trajectory.t)),
        "solver": dict(trajectory.metadata),
        "invariant_certificate": invariant_certificate,
    }
    if include_invariant_series:
        result["invariant_series"] = _trajectory_invariant_series(system, trajectory)
    return result


def predict_three_body_position_distribution(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    count: int = 64,
    initial_state_covariance: Sequence[Sequence[float]] | None = None,
    position_scale: float = 1.0e-6,
    velocity_scale: float = 1.0e-6,
    seed: int = 0,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    samples: int = 256,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    max_step: float = math.inf,
    preserve_center_of_mass: bool = True,
    include_sample_positions: bool = False,
) -> dict[str, object]:
    """Return an empirical final-position distribution from perturbed initial states."""

    system, initial_state = _general_prediction_system(
        masses,
        positions,
        velocities,
        gravitational_constant=gravitational_constant,
        softening=softening,
    )
    target_time = _finite_float(target_time, "target_time")
    count = _validated_positive_int(count, "count")
    sample_count = _validated_sample_count(samples)
    generated_center_of_mass_covariance = initial_state_covariance is None and preserve_center_of_mass
    covariance0 = _initial_state_covariance(
        initial_state.size,
        system.dimension,
        initial_state_covariance=initial_state_covariance,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        masses=system.masses,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    rng = np.random.default_rng(seed)
    initial_states = _perturbed_initial_states(
        system,
        initial_state,
        count=count,
        rng=rng,
        initial_state_covariance=covariance0,
    )
    t_eval = _prediction_times(target_time, sample_count)
    integrator = AdaptiveIntegrator(rtol=rtol, atol=atol, max_step=max_step)
    successful_positions: list[np.ndarray] = []
    sample_rows: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for index, state in enumerate(initial_states):
        if target_time == 0.0:
            trajectory = TrajectoryResult(
                t=np.array([0.0], dtype=float),
                y=np.asarray([state], dtype=float),
                success=True,
                message="target_time is zero; returned the initial state.",
                metadata={"method": "identity", "nfev": 0, "njev": 0, "nlu": 0},
            )
        else:
            trajectory = integrator.integrate(system, (0.0, target_time), state, t_eval=t_eval)
        if not trajectory.success or len(trajectory.y) == 0:
            failures.append({"index": index, "message": trajectory.message})
            continue
        final_positions, final_velocities = system.split_state(trajectory.y[-1])
        successful_positions.append(final_positions)
        if include_sample_positions:
            sample_rows.append(
                {
                    "index": index,
                    "positions": final_positions.tolist(),
                    "velocities": final_velocities.tolist(),
                }
            )
    summary = _position_distribution_summary(successful_positions, system.dimension)
    base_prediction = predict_three_body_positions(
        masses,
        positions,
        velocities,
        target_time,
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=samples,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
    result: dict[str, object] = {
        "prediction_schema_version": 1,
        "prediction_type": "empirical-position-distribution",
        "method": "adaptive-DOP853-ensemble",
        "target_time": target_time,
        "dimension": system.dimension,
        "masses": [float(mass) for mass in system.masses],
        "gravitational_constant": float(system.gravitational_constant),
        "softening": float(system.softening),
        "uncertainty_model": {
            "type": "gaussian_initial_state",
            "count": count,
            "seed": int(seed),
            "position_scale": float(position_scale),
            "velocity_scale": float(velocity_scale),
            "preserve_center_of_mass": bool(generated_center_of_mass_covariance),
            "initial_state_covariance_supplied": initial_state_covariance is not None,
        },
        "initial_state_covariance": covariance0.tolist(),
        "success_count": len(successful_positions),
        "failure_count": len(failures),
        "failures": failures,
        "base_prediction": base_prediction,
        "position_distribution": summary,
    }
    if include_sample_positions:
        result["sample_predictions"] = sample_rows
    return result


def predict_three_body_distribution_ephemeris(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    count: int = 64,
    initial_state_covariance: Sequence[Sequence[float]] | None = None,
    position_scale: float = 1.0e-6,
    velocity_scale: float = 1.0e-6,
    seed: int = 0,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    samples: int = 256,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    max_step: float = math.inf,
    preserve_center_of_mass: bool = True,
    include_sample_ephemerides: bool = False,
) -> dict[str, object]:
    """Return an empirical position-distribution ephemeris over the full forecast interval."""

    system, initial_state = _general_prediction_system(
        masses,
        positions,
        velocities,
        gravitational_constant=gravitational_constant,
        softening=softening,
    )
    target_time = _finite_float(target_time, "target_time")
    count = _validated_positive_int(count, "count")
    sample_count = _validated_sample_count(samples)
    generated_center_of_mass_covariance = initial_state_covariance is None and preserve_center_of_mass
    covariance0 = _initial_state_covariance(
        initial_state.size,
        system.dimension,
        initial_state_covariance=initial_state_covariance,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        masses=system.masses,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    rng = np.random.default_rng(seed)
    initial_states = _perturbed_initial_states(
        system,
        initial_state,
        count=count,
        rng=rng,
        initial_state_covariance=covariance0,
    )
    integrator = AdaptiveIntegrator(rtol=rtol, atol=atol, max_step=max_step)
    successful_positions: list[np.ndarray] = []
    successful_times: np.ndarray | None = None
    sample_rows: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for index, state in enumerate(initial_states):
        trajectory = _prediction_trajectory_with_integrator(
            system,
            state,
            target_time,
            samples=sample_count,
            integrator=integrator,
        )
        if not trajectory.success or len(trajectory.y) == 0:
            failures.append({"index": index, "message": trajectory.message})
            continue
        positions_series, velocities_series = _trajectory_position_velocity_series(system, trajectory)
        successful_positions.append(positions_series)
        if successful_times is None:
            successful_times = trajectory.t
        if include_sample_ephemerides:
            sample_rows.append(
                {
                    "index": index,
                    "times": trajectory.t.tolist(),
                    "positions": positions_series.tolist(),
                    "velocities": velocities_series.tolist(),
                }
            )
    base_ephemeris = predict_three_body_ephemeris(
        masses,
        positions,
        velocities,
        target_time,
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=samples,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
    result: dict[str, object] = {
        "prediction_schema_version": 1,
        "prediction_type": "empirical-position-distribution-ephemeris",
        "method": "adaptive-DOP853-ensemble-ephemeris",
        "target_time": target_time,
        "dimension": system.dimension,
        "masses": [float(mass) for mass in system.masses],
        "gravitational_constant": float(system.gravitational_constant),
        "softening": float(system.softening),
        "uncertainty_model": {
            "type": "gaussian_initial_state",
            "count": count,
            "seed": int(seed),
            "position_scale": float(position_scale),
            "velocity_scale": float(velocity_scale),
            "preserve_center_of_mass": bool(generated_center_of_mass_covariance),
            "initial_state_covariance_supplied": initial_state_covariance is not None,
        },
        "initial_state_covariance": covariance0.tolist(),
        "success_count": len(successful_positions),
        "failure_count": len(failures),
        "failures": failures,
        "times": [] if successful_times is None else successful_times.tolist(),
        "base_ephemeris": base_ephemeris,
        "position_distribution_ephemeris": _position_distribution_ephemeris_summary(
            successful_positions,
            system.dimension,
        ),
    }
    if include_sample_ephemerides:
        result["sample_ephemerides"] = sample_rows
    return result


def solve_three_body_prediction_problem(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    count: int = 64,
    initial_state_covariance: Sequence[Sequence[float]] | None = None,
    position_scale: float = 1.0e-6,
    velocity_scale: float = 1.0e-6,
    seed: int = 0,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    samples: int = 256,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    max_step: float = math.inf,
    jacobian_step: float = 1.0e-6,
    position_tolerance: float = 1.0e-3,
    horizon_samples: int = 16,
    linearized_covariance_relative_tolerance: float = 0.75,
    preserve_center_of_mass: bool = True,
) -> dict[str, object]:
    """Return the complete operational answer to the general three-body prediction task."""

    deterministic_ephemeris = predict_three_body_ephemeris(
        masses,
        positions,
        velocities,
        target_time,
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=samples,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
    distribution_ephemeris = predict_three_body_distribution_ephemeris(
        masses,
        positions,
        velocities,
        target_time,
        count=count,
        initial_state_covariance=initial_state_covariance,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        seed=seed,
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=samples,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    linearized_ephemeris = predict_three_body_linearized_ephemeris(
        masses,
        positions,
        velocities,
        target_time,
        initial_state_covariance=initial_state_covariance,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=samples,
        jacobian_step=jacobian_step,
        rtol=rtol,
        atol=atol,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    interpretation_report = predict_three_body_interpretation_report(
        masses,
        positions,
        velocities,
        target_time,
        count=count,
        initial_state_covariance=initial_state_covariance,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        seed=seed,
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=samples,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
        jacobian_step=jacobian_step,
        position_tolerance=position_tolerance,
        horizon_samples=horizon_samples,
        linearized_covariance_relative_tolerance=linearized_covariance_relative_tolerance,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    ephemeris_comparison = _linearized_empirical_ephemeris_comparison(
        linearized_ephemeris,
        distribution_ephemeris,
        covariance_relative_tolerance=linearized_covariance_relative_tolerance,
    )
    verdict = interpretation_report.get("verdict", {})
    if not isinstance(verdict, Mapping):
        verdict = {}
    final_distribution = _final_position_distribution_from_ephemeris(distribution_ephemeris)
    final_positions = (
        deterministic_ephemeris["positions"][-1]
        if deterministic_ephemeris.get("positions")
        else []
    )
    return {
        "prediction_schema_version": 1,
        "prediction_type": "three-body-prediction-solution",
        "target_time": float(target_time),
        "answer": {
            "final_positions": final_positions,
            "final_position_distribution": final_distribution,
            "recommended_mode": verdict.get("recommended_mode", "unresolved"),
            "target_time_inside_forecast_horizon": verdict.get("target_time_inside_forecast_horizon") is True,
            "deterministic_resolved": verdict.get("deterministic_resolved") is True,
            "empirical_distribution_resolved": verdict.get("empirical_distribution_resolved") is True,
            "linearized_ephemeris_consistent_until": ephemeris_comparison["linearized_consistent_until"],
            "first_linearized_ephemeris_break_time": ephemeris_comparison["first_break_time"],
        },
        "deterministic_ephemeris": deterministic_ephemeris,
        "linearized_gaussian_ephemeris": linearized_ephemeris,
        "distribution_ephemeris": distribution_ephemeris,
        "ephemeris_distribution_comparison": ephemeris_comparison,
        "interpretation_report": interpretation_report,
    }


def predict_three_body_linearized_distribution(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    initial_state_covariance: Sequence[Sequence[float]] | None = None,
    position_scale: float = 1.0e-6,
    velocity_scale: float = 1.0e-6,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    jacobian_step: float = 1.0e-6,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    preserve_center_of_mass: bool = False,
) -> dict[str, object]:
    """Push an initial Gaussian uncertainty through the linearized three-body flow.

    If ``x(t) = Phi_t(x0)`` and ``P0`` is the initial covariance, this returns
    the first-order Gaussian approximation ``Pt = DPhi_t P0 DPhi_t^T``.
    """

    system, initial_state = _general_prediction_system(
        masses,
        positions,
        velocities,
        gravitational_constant=gravitational_constant,
        softening=softening,
    )
    target_time = _finite_float(target_time, "target_time")
    jacobian_step = _positive_float(jacobian_step, "jacobian_step")
    generated_center_of_mass_covariance = initial_state_covariance is None and preserve_center_of_mass
    covariance0 = _initial_state_covariance(
        initial_state.size,
        system.dimension,
        initial_state_covariance=initial_state_covariance,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        masses=system.masses,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    flow = _linearized_flow_map(
        system,
        initial_state,
        target_time,
        jacobian_step=jacobian_step,
        rtol=rtol,
        atol=atol,
    )
    transition = flow["transition_matrix"]
    covariance_t = _symmetrize_covariance(transition @ covariance0 @ transition.T)
    position_width = system.body_count * system.dimension
    position_covariance = covariance_t[:position_width, :position_width]
    body_covariances = [
        position_covariance[
            body_index * system.dimension : (body_index + 1) * system.dimension,
            body_index * system.dimension : (body_index + 1) * system.dimension,
        ]
        for body_index in range(system.body_count)
    ]
    final_positions, final_velocities = system.split_state(flow["final_state"])
    std_positions = np.sqrt(np.maximum(np.diag(position_covariance), 0.0)).reshape(
        system.body_count,
        system.dimension,
    )
    covariance_eigenvalues = np.linalg.eigvalsh(covariance_t)
    return {
        "prediction_schema_version": 1,
        "prediction_type": "linearized-gaussian-position-distribution",
        "method": "variational-flow-covariance-pushforward",
        "target_time": target_time,
        "dimension": system.dimension,
        "masses": [float(mass) for mass in system.masses],
        "gravitational_constant": float(system.gravitational_constant),
        "softening": float(system.softening),
        "success": bool(flow["success"]),
        "message": str(flow["message"]),
        "uncertainty_model": {
            "type": "gaussian_initial_state",
            "position_scale": float(position_scale),
            "velocity_scale": float(velocity_scale),
            "preserve_center_of_mass": bool(generated_center_of_mass_covariance),
            "initial_state_covariance_supplied": initial_state_covariance is not None,
        },
        "mean_positions": final_positions.tolist(),
        "mean_velocities": final_velocities.tolist(),
        "std_positions": std_positions.tolist(),
        "initial_state_covariance": covariance0.tolist(),
        "final_state_covariance": covariance_t.tolist(),
        "position_covariance": position_covariance.tolist(),
        "body_position_covariances": [covariance.tolist() for covariance in body_covariances],
        "position_confidence_regions": _position_confidence_regions(
            final_positions,
            body_covariances,
            method="linearized-gaussian",
        ),
        "state_transition_matrix": transition.tolist(),
        "linearized_diagnostics": {
            "jacobian_step": jacobian_step,
            "transition_condition_number": float(np.linalg.cond(transition)),
            "transition_spectral_radius": float(max(abs(np.linalg.eigvals(transition)))),
            "minimum_covariance_eigenvalue": float(np.min(covariance_eigenvalues)),
            "maximum_position_std": float(np.max(std_positions)),
        },
        "interpretation": (
            "First-order Gaussian push-forward: valid while neglected nonlinear terms stay small relative "
            "to the propagated covariance scale."
        ),
    }


def score_three_body_position_hypothesis(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    candidate_positions: Sequence[Sequence[float]],
    *,
    initial_state_covariance: Sequence[Sequence[float]] | None = None,
    position_scale: float = 1.0e-6,
    velocity_scale: float = 1.0e-6,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    jacobian_step: float = 1.0e-6,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    preserve_center_of_mass: bool = False,
) -> dict[str, object]:
    """Score a proposed target-time three-body position against the linearized forecast distribution."""

    linearized = predict_three_body_linearized_distribution(
        masses,
        positions,
        velocities,
        target_time,
        initial_state_covariance=initial_state_covariance,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        gravitational_constant=gravitational_constant,
        softening=softening,
        jacobian_step=jacobian_step,
        rtol=rtol,
        atol=atol,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    dimension = int(linearized["dimension"])
    candidate_array = np.asarray(candidate_positions, dtype=float)
    if candidate_array.shape != (3, dimension):
        raise ValueError("candidate_positions must have shape (3, dimension).")
    if np.any(~np.isfinite(candidate_array)):
        raise ValueError("candidate_positions must contain only finite values.")
    mean_positions = np.asarray(linearized["mean_positions"], dtype=float)
    position_covariance = np.asarray(linearized["position_covariance"], dtype=float)
    body_covariances = np.asarray(linearized["body_position_covariances"], dtype=float)
    body_scores = []
    for body_index in range(3):
        body_scores.append(
            _gaussian_hypothesis_score(
                candidate_array[body_index],
                mean_positions[body_index],
                body_covariances[body_index],
                label=f"body-{body_index}",
            )
        )
    joint_score = _gaussian_hypothesis_score(
        candidate_array.reshape(-1),
        mean_positions.reshape(-1),
        position_covariance,
        label="joint-position",
    )
    return {
        "prediction_schema_version": 1,
        "prediction_type": "three-body-position-hypothesis-score",
        "method": "linearized-gaussian-mahalanobis-score",
        "target_time": float(target_time),
        "dimension": dimension,
        "masses": list(linearized["masses"]),
        "candidate_positions": candidate_array.tolist(),
        "forecast": {
            "mean_positions": linearized["mean_positions"],
            "std_positions": linearized["std_positions"],
            "position_covariance": linearized["position_covariance"],
            "position_confidence_regions": linearized["position_confidence_regions"],
            "uncertainty_model": linearized["uncertainty_model"],
            "linearized_diagnostics": linearized["linearized_diagnostics"],
        },
        "joint_score": joint_score,
        "body_scores": body_scores,
        "interpretation": (
            "A smaller Mahalanobis distance means the proposed target-time positions are more typical under "
            "the local linearized Gaussian forecast. confidence_level_containing_point is the Gaussian mass "
            "inside the ellipsoid through the candidate point."
        ),
    }


def predict_three_body_linearized_ephemeris(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    initial_state_covariance: Sequence[Sequence[float]] | None = None,
    position_scale: float = 1.0e-6,
    velocity_scale: float = 1.0e-6,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    samples: int = 256,
    jacobian_step: float = 1.0e-6,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    preserve_center_of_mass: bool = False,
) -> dict[str, object]:
    """Return the time-resolved first-order Gaussian distribution along the nominal flow."""

    system, initial_state = _general_prediction_system(
        masses,
        positions,
        velocities,
        gravitational_constant=gravitational_constant,
        softening=softening,
    )
    target_time = _finite_float(target_time, "target_time")
    samples = _validated_sample_count(samples)
    jacobian_step = _positive_float(jacobian_step, "jacobian_step")
    generated_center_of_mass_covariance = initial_state_covariance is None and preserve_center_of_mass
    covariance0 = _initial_state_covariance(
        initial_state.size,
        system.dimension,
        initial_state_covariance=initial_state_covariance,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        masses=system.masses,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    flow = _linearized_flow_trace(
        system,
        initial_state,
        target_time,
        samples=samples,
        jacobian_step=jacobian_step,
        rtol=rtol,
        atol=atol,
    )
    rows = _linearized_ephemeris_rows(system, flow, covariance0)
    max_position_std = max((float(row["maximum_position_std"]) for row in rows), default=math.inf)
    return {
        "prediction_schema_version": 1,
        "prediction_type": "linearized-gaussian-ephemeris",
        "method": "variational-flow-covariance-ephemeris",
        "target_time": target_time,
        "dimension": system.dimension,
        "masses": [float(mass) for mass in system.masses],
        "gravitational_constant": float(system.gravitational_constant),
        "softening": float(system.softening),
        "success": bool(flow["success"]),
        "message": str(flow["message"]),
        "uncertainty_model": {
            "type": "gaussian_initial_state",
            "position_scale": float(position_scale),
            "velocity_scale": float(velocity_scale),
            "preserve_center_of_mass": bool(generated_center_of_mass_covariance),
            "initial_state_covariance_supplied": initial_state_covariance is not None,
        },
        "times": np.asarray(flow.get("times", []), dtype=float).tolist(),
        "initial_state_covariance": covariance0.tolist(),
        "rows": rows,
        "linearized_diagnostics": {
            "jacobian_step": jacobian_step,
            "sample_count": len(rows),
            "maximum_position_std": max_position_std,
        },
        "interpretation": (
            "Time-resolved first-order Gaussian push-forward: each row contains the nominal positions "
            "and the variationally propagated position covariance at that sample time."
        ),
    }


def predict_three_body_forecast_horizon(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    position_tolerance: float = 1.0e-3,
    initial_state_covariance: Sequence[Sequence[float]] | None = None,
    position_scale: float = 1.0e-6,
    velocity_scale: float = 1.0e-6,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    horizon_samples: int = 16,
    jacobian_step: float = 1.0e-6,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    preserve_center_of_mass: bool = False,
) -> dict[str, object]:
    """Estimate the time interval where propagated position uncertainty stays below tolerance."""

    system, initial_state = _general_prediction_system(
        masses,
        positions,
        velocities,
        gravitational_constant=gravitational_constant,
        softening=softening,
    )
    target_time = _finite_float(target_time, "target_time")
    position_tolerance = _positive_float(position_tolerance, "position_tolerance")
    horizon_samples = _validated_sample_count(horizon_samples)
    jacobian_step = _positive_float(jacobian_step, "jacobian_step")
    generated_center_of_mass_covariance = initial_state_covariance is None and preserve_center_of_mass
    covariance0 = _initial_state_covariance(
        initial_state.size,
        system.dimension,
        initial_state_covariance=initial_state_covariance,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        masses=system.masses,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    flow = _linearized_flow_trace(
        system,
        initial_state,
        target_time,
        samples=horizon_samples,
        jacobian_step=jacobian_step,
        rtol=rtol,
        atol=atol,
    )
    position_width = system.body_count * system.dimension
    rows = _forecast_horizon_rows(
        flow,
        covariance0,
        position_width=position_width,
        physical_dimension=system.dimension,
        position_tolerance=position_tolerance,
    )
    summary = _forecast_horizon_summary(rows)
    return {
        "prediction_schema_version": 1,
        "prediction_type": "linearized-forecast-horizon",
        "method": "variational-flow-uncertainty-horizon",
        "target_time": target_time,
        "dimension": system.dimension,
        "masses": [float(mass) for mass in system.masses],
        "gravitational_constant": float(system.gravitational_constant),
        "softening": float(system.softening),
        "success": bool(flow["success"]),
        "message": str(flow["message"]),
        "position_tolerance": position_tolerance,
        "uncertainty_model": {
            "type": "gaussian_initial_state",
            "position_scale": float(position_scale),
            "velocity_scale": float(velocity_scale),
            "preserve_center_of_mass": bool(generated_center_of_mass_covariance),
            "initial_state_covariance_supplied": initial_state_covariance is not None,
        },
        "horizon_samples": len(rows),
        "reliable_until": summary["reliable_until"],
        "first_unresolved_time": summary["first_unresolved_time"],
        "target_time_resolved": summary["target_time_resolved"],
        "reliability_fraction": summary["reliability_fraction"],
        "final_uncertainty_to_tolerance_ratio": summary["final_uncertainty_to_tolerance_ratio"],
        "rows": rows,
        "interpretation": (
            "Local forecast horizon: the final-position claim remains tolerance-resolved while the "
            "linearized propagated position standard deviation stays below position_tolerance."
        ),
    }


def predict_three_body_interpretation_report(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    count: int = 64,
    initial_state_covariance: Sequence[Sequence[float]] | None = None,
    position_scale: float = 1.0e-6,
    velocity_scale: float = 1.0e-6,
    seed: int = 0,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    samples: int = 256,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    max_step: float = math.inf,
    jacobian_step: float = 1.0e-6,
    position_tolerance: float = 1.0e-3,
    horizon_samples: int = 16,
    linearized_covariance_relative_tolerance: float = 0.75,
    preserve_center_of_mass: bool = True,
) -> dict[str, object]:
    """Return a point/linearized/ensemble prediction report with a mode recommendation."""

    generated_center_of_mass_covariance = initial_state_covariance is None and preserve_center_of_mass
    deterministic = predict_three_body_positions(
        masses,
        positions,
        velocities,
        target_time,
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=samples,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
    linearized = predict_three_body_linearized_distribution(
        masses,
        positions,
        velocities,
        target_time,
        initial_state_covariance=initial_state_covariance,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        gravitational_constant=gravitational_constant,
        softening=softening,
        jacobian_step=jacobian_step,
        rtol=rtol,
        atol=atol,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    horizon = predict_three_body_forecast_horizon(
        masses,
        positions,
        velocities,
        target_time,
        position_tolerance=position_tolerance,
        initial_state_covariance=initial_state_covariance,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        gravitational_constant=gravitational_constant,
        softening=softening,
        horizon_samples=horizon_samples,
        jacobian_step=jacobian_step,
        rtol=rtol,
        atol=atol,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    empirical = predict_three_body_position_distribution(
        masses,
        positions,
        velocities,
        target_time,
        count=count,
        initial_state_covariance=initial_state_covariance,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        seed=seed,
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=samples,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    comparison = _prediction_distribution_comparison(linearized, empirical)
    verdict = _prediction_report_verdict(
        deterministic,
        linearized,
        empirical,
        comparison,
        horizon,
        linearized_covariance_relative_tolerance=linearized_covariance_relative_tolerance,
    )
    return {
        "prediction_schema_version": 1,
        "prediction_type": "three-body-interpretation-report",
        "target_time": float(target_time),
        "uncertainty_model": {
            "type": "gaussian_initial_state",
            "count": int(count),
            "seed": int(seed),
            "position_scale": float(position_scale),
            "velocity_scale": float(velocity_scale),
            "preserve_center_of_mass": bool(generated_center_of_mass_covariance),
            "initial_state_covariance_supplied": initial_state_covariance is not None,
        },
        "deterministic": deterministic,
        "linearized_gaussian": linearized,
        "forecast_horizon": horizon,
        "empirical_distribution": empirical,
        "comparison": comparison,
        "verdict": verdict,
    }


def _general_prediction_system(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    *,
    gravitational_constant: float,
    softening: float,
) -> tuple[GeneralThreeBodySystem, np.ndarray]:
    masses_array = np.asarray(masses, dtype=float)
    positions_array = np.asarray(positions, dtype=float)
    velocities_array = np.asarray(velocities, dtype=float)
    if masses_array.shape != (3,):
        raise ValueError("masses must contain exactly three values.")
    if np.any(~np.isfinite(masses_array)) or np.any(masses_array <= 0.0):
        raise ValueError("masses must be finite positive values.")
    if positions_array.ndim != 2 or positions_array.shape[0] != 3 or positions_array.shape[1] not in (2, 3):
        raise ValueError("positions must have shape (3, 2) or (3, 3).")
    if velocities_array.shape != positions_array.shape:
        raise ValueError("velocities must have the same shape as positions.")
    if np.any(~np.isfinite(positions_array)) or np.any(~np.isfinite(velocities_array)):
        raise ValueError("positions and velocities must contain only finite values.")
    gravitational_constant = _positive_float(gravitational_constant, "gravitational_constant")
    softening = _nonnegative_float(softening, "softening")
    system = GeneralThreeBodySystem(
        masses=tuple(float(mass) for mass in masses_array),
        gravitational_constant=gravitational_constant,
        dimension=int(positions_array.shape[1]),
        softening=softening,
    )
    return system, system.flatten_state(positions_array, velocities_array)


def _finite_float(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")
    return value


def _positive_float(value: float, name: str) -> float:
    value = _finite_float(value, name)
    if value <= 0.0:
        raise ValueError(f"{name} must be positive.")
    return value


def _nonnegative_float(value: float, name: str) -> float:
    value = _finite_float(value, name)
    if value < 0.0:
        raise ValueError(f"{name} must be nonnegative.")
    return value


def _validated_positive_int(value: int, name: str) -> int:
    value = int(value)
    if value < 1:
        raise ValueError(f"{name} must be >= 1.")
    return value


def _validated_sample_count(samples: int) -> int:
    samples = int(samples)
    if samples < 2:
        raise ValueError("samples must be >= 2.")
    return samples


def _prediction_times(target_time: float, samples: int) -> np.ndarray:
    if target_time == 0.0:
        return np.array([0.0], dtype=float)
    return np.linspace(0.0, target_time, samples)


def _prediction_trajectory(
    system: GeneralThreeBodySystem,
    initial_state: np.ndarray,
    target_time: float,
    *,
    samples: int,
    rtol: float,
    atol: float,
    max_step: float,
) -> TrajectoryResult:
    sample_count = _validated_sample_count(samples)
    t_eval = _prediction_times(target_time, sample_count)
    if target_time == 0.0:
        return TrajectoryResult(
            t=np.array([0.0], dtype=float),
            y=np.asarray([initial_state], dtype=float),
            success=True,
            message="target_time is zero; returned the initial state.",
            metadata={"method": "identity", "nfev": 0, "njev": 0, "nlu": 0},
        )
    return AdaptiveIntegrator(rtol=rtol, atol=atol, max_step=max_step).integrate(
        system,
        (0.0, target_time),
        initial_state,
        t_eval=t_eval,
    )


def _prediction_trajectory_with_integrator(
    system: GeneralThreeBodySystem,
    initial_state: np.ndarray,
    target_time: float,
    *,
    samples: int,
    integrator: AdaptiveIntegrator,
) -> TrajectoryResult:
    t_eval = _prediction_times(target_time, samples)
    if target_time == 0.0:
        return TrajectoryResult(
            t=np.array([0.0], dtype=float),
            y=np.asarray([initial_state], dtype=float),
            success=True,
            message="target_time is zero; returned the initial state.",
            metadata={"method": "identity", "nfev": 0, "njev": 0, "nlu": 0},
        )
    return integrator.integrate(system, (0.0, target_time), initial_state, t_eval=t_eval)


def _trajectory_position_velocity_series(
    system: GeneralThreeBodySystem,
    trajectory: TrajectoryResult,
) -> tuple[np.ndarray, np.ndarray]:
    if len(trajectory.y) == 0:
        empty_shape = (0, system.body_count, system.dimension)
        return np.empty(empty_shape, dtype=float), np.empty(empty_shape, dtype=float)
    positions: list[np.ndarray] = []
    velocities: list[np.ndarray] = []
    for state in trajectory.y:
        state_positions, state_velocities = system.split_state(state)
        positions.append(state_positions)
        velocities.append(state_velocities)
    return np.asarray(positions, dtype=float), np.asarray(velocities, dtype=float)


def _trajectory_invariant_series(
    system: GeneralThreeBodySystem,
    trajectory: TrajectoryResult,
) -> dict[str, object]:
    if len(trajectory.y) == 0:
        return {
            "energy": [],
            "energy_drift": [],
            "linear_momentum_norm": [],
            "angular_momentum_norm": [],
            "angular_momentum_drift_norm": [],
        }
    energies = np.array([system.total_energy(state) for state in trajectory.y], dtype=float)
    linear_momenta = np.array([np.linalg.norm(system.linear_momentum(state)) for state in trajectory.y], dtype=float)
    angular_momenta = np.array([system.angular_momentum(state) for state in trajectory.y], dtype=float)
    angular_drift = np.linalg.norm(angular_momenta - angular_momenta[0], axis=1)
    return {
        "energy": energies.tolist(),
        "energy_drift": (energies - energies[0]).tolist(),
        "linear_momentum_norm": linear_momenta.tolist(),
        "angular_momentum_norm": np.linalg.norm(angular_momenta, axis=1).tolist(),
        "angular_momentum_drift_norm": angular_drift.tolist(),
    }


def _perturbed_initial_states(
    system: GeneralThreeBodySystem,
    initial_state: np.ndarray,
    *,
    count: int,
    rng: np.random.Generator,
    initial_state_covariance: np.ndarray | None = None,
    position_scale: float = 1.0e-6,
    velocity_scale: float = 1.0e-6,
    preserve_center_of_mass: bool = True,
) -> list[np.ndarray]:
    if initial_state_covariance is not None:
        return _covariance_perturbed_initial_states(
            initial_state,
            covariance=initial_state_covariance,
            count=count,
            rng=rng,
        )
    positions, velocities = system.split_state(initial_state)
    states = [initial_state.copy()]
    masses = np.asarray(system.masses, dtype=float)
    for _index in range(1, count):
        position_noise = rng.normal(0.0, position_scale, size=positions.shape)
        velocity_noise = rng.normal(0.0, velocity_scale, size=velocities.shape)
        if preserve_center_of_mass:
            position_noise = position_noise - np.average(position_noise, axis=0, weights=masses)
            velocity_noise = velocity_noise - np.average(velocity_noise, axis=0, weights=masses)
        states.append(system.flatten_state(positions + position_noise, velocities + velocity_noise))
    return states


def _covariance_perturbed_initial_states(
    initial_state: np.ndarray,
    *,
    covariance: np.ndarray,
    count: int,
    rng: np.random.Generator,
) -> list[np.ndarray]:
    covariance = np.asarray(covariance, dtype=float)
    if covariance.shape != (initial_state.size, initial_state.size):
        raise ValueError("initial_state_covariance must have shape (state_dim, state_dim).")
    covariance = _symmetrize_covariance(covariance)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    spectral_scale = max(float(np.max(np.abs(eigenvalues))), 1.0)
    tolerance = 1.0e-12 * spectral_scale
    if float(np.min(eigenvalues)) < -tolerance:
        raise ValueError("initial_state_covariance must be positive semidefinite.")
    square_roots = np.sqrt(np.maximum(eigenvalues, 0.0))
    states = [initial_state.copy()]
    for _index in range(1, count):
        standard_normal = rng.normal(0.0, 1.0, size=initial_state.size)
        perturbation = eigenvectors @ (square_roots * standard_normal)
        states.append(initial_state + perturbation)
    return states


def _position_distribution_summary(positions: list[np.ndarray], dimension: int) -> dict[str, object]:
    if not positions:
        return {
            "mean_positions": [],
            "median_positions": [],
            "q05_positions": [],
            "q95_positions": [],
            "flat_covariance": [],
            "body_covariances": [],
            "position_confidence_regions": [],
            "max_body_radius_from_mean": math.inf,
        }
    stack = np.asarray(positions, dtype=float)
    flat = stack.reshape(stack.shape[0], 3 * dimension)
    mean = np.mean(stack, axis=0)
    quantiles = np.quantile(stack, [0.05, 0.5, 0.95], axis=0)
    if flat.shape[0] > 1:
        flat_covariance = np.cov(flat, rowvar=False)
        body_covariances = [
            np.cov(stack[:, body_index, :], rowvar=False).reshape(dimension, dimension)
            for body_index in range(3)
        ]
    else:
        flat_covariance = np.zeros((3 * dimension, 3 * dimension), dtype=float)
        body_covariances = [np.zeros((dimension, dimension), dtype=float) for _body in range(3)]
    body_radii = np.linalg.norm(stack - mean[None, :, :], axis=2)
    return {
        "mean_positions": mean.tolist(),
        "median_positions": quantiles[1].tolist(),
        "q05_positions": quantiles[0].tolist(),
        "q95_positions": quantiles[2].tolist(),
        "flat_covariance": flat_covariance.tolist(),
        "body_covariances": [covariance.tolist() for covariance in body_covariances],
        "position_confidence_regions": _position_confidence_regions(
            mean,
            body_covariances,
            method="sample-covariance-gaussian-equivalent",
        ),
        "max_body_radius_from_mean": float(np.max(body_radii)),
    }


def _position_distribution_ephemeris_summary(
    positions_by_sample: list[np.ndarray],
    dimension: int,
) -> dict[str, object]:
    if not positions_by_sample:
        return {
            "mean_positions": [],
            "median_positions": [],
            "q05_positions": [],
            "q95_positions": [],
            "flat_covariances": [],
            "position_confidence_regions": [],
            "max_body_radius_from_mean": [],
        }
    stack = np.asarray(positions_by_sample, dtype=float)
    # Shape: ensemble, time, body, dimension.
    ensemble_count, time_count = stack.shape[:2]
    mean = np.mean(stack, axis=0)
    quantiles = np.quantile(stack, [0.05, 0.5, 0.95], axis=0)
    flat_covariances: list[list[list[float]]] = []
    confidence_regions: list[list[dict[str, object]]] = []
    max_body_radii: list[float] = []
    for time_index in range(time_count):
        time_positions = stack[:, time_index, :, :]
        flat = time_positions.reshape(ensemble_count, 3 * dimension)
        if ensemble_count > 1:
            covariance = np.cov(flat, rowvar=False)
            body_covariances = [
                np.cov(time_positions[:, body_index, :], rowvar=False).reshape(dimension, dimension)
                for body_index in range(3)
            ]
        else:
            covariance = np.zeros((3 * dimension, 3 * dimension), dtype=float)
            body_covariances = [np.zeros((dimension, dimension), dtype=float) for _body in range(3)]
        flat_covariances.append(covariance.tolist())
        confidence_regions.append(
            _position_confidence_regions(
                mean[time_index],
                body_covariances,
                method="sample-covariance-gaussian-equivalent",
            )
        )
        body_radii = np.linalg.norm(time_positions - mean[time_index][None, :, :], axis=2)
        max_body_radii.append(float(np.max(body_radii)))
    return {
        "mean_positions": mean.tolist(),
        "median_positions": quantiles[1].tolist(),
        "q05_positions": quantiles[0].tolist(),
        "q95_positions": quantiles[2].tolist(),
        "flat_covariances": flat_covariances,
        "position_confidence_regions": confidence_regions,
        "max_body_radius_from_mean": max_body_radii,
    }


def _final_position_distribution_from_ephemeris(distribution_ephemeris: Mapping[str, object]) -> dict[str, object]:
    summary = distribution_ephemeris.get("position_distribution_ephemeris", {})
    if not isinstance(summary, Mapping):
        summary = {}

    def final_value(key: str) -> object:
        values = summary.get(key, [])
        if isinstance(values, Sequence) and not isinstance(values, (str, bytes, bytearray)) and values:
            return values[-1]
        return []

    return {
        "mean_positions": final_value("mean_positions"),
        "median_positions": final_value("median_positions"),
        "q05_positions": final_value("q05_positions"),
        "q95_positions": final_value("q95_positions"),
        "flat_covariance": final_value("flat_covariances"),
        "position_confidence_regions": final_value("position_confidence_regions"),
        "max_body_radius_from_mean": final_value("max_body_radius_from_mean"),
        "success_count": int(distribution_ephemeris.get("success_count", 0)),
        "failure_count": int(distribution_ephemeris.get("failure_count", 0)),
    }


def _position_confidence_regions(
    mean_positions: Sequence[Sequence[float]] | np.ndarray,
    body_covariances: Sequence[Sequence[Sequence[float]]] | np.ndarray,
    *,
    method: str,
    levels: Sequence[float] = (0.5, 0.9, 0.95, 0.99),
) -> list[dict[str, object]]:
    means = np.asarray(mean_positions, dtype=float)
    covariances = np.asarray(body_covariances, dtype=float)
    if means.ndim != 2 or covariances.ndim != 3 or covariances.shape[0] != means.shape[0]:
        return []
    dimension = int(means.shape[1])
    regions: list[dict[str, object]] = []
    for body_index, (center, covariance) in enumerate(zip(means, covariances, strict=True)):
        covariance = _symmetrize_covariance(covariance)
        if covariance.shape != (dimension, dimension) or np.any(~np.isfinite(covariance)):
            region_levels = [
                {
                    "probability": float(level),
                    "mahalanobis_radius": math.inf,
                    "semi_axes": [math.inf for _axis in range(dimension)],
                    "axis_directions": np.eye(dimension, dtype=float).tolist(),
                }
                for level in levels
            ]
        else:
            eigenvalues, eigenvectors = np.linalg.eigh(covariance)
            order = np.argsort(eigenvalues)[::-1]
            eigenvalues = np.maximum(eigenvalues[order], 0.0)
            eigenvectors = eigenvectors[:, order]
            region_levels = []
            for level in levels:
                probability = float(level)
                mahalanobis_radius_squared = float(chi2.ppf(probability, dimension))
                mahalanobis_radius = float(math.sqrt(mahalanobis_radius_squared))
                semi_axes = np.sqrt(eigenvalues * mahalanobis_radius_squared)
                region_levels.append(
                    {
                        "probability": probability,
                        "mahalanobis_radius": mahalanobis_radius,
                        "semi_axes": semi_axes.tolist(),
                        "axis_directions": eigenvectors.T.tolist(),
                    }
                )
        regions.append(
            {
                "body_index": body_index,
                "method": method,
                "center": center.tolist(),
                "levels": region_levels,
            }
        )
    return regions


def _gaussian_hypothesis_score(
    candidate: Sequence[float] | np.ndarray,
    mean: Sequence[float] | np.ndarray,
    covariance: Sequence[Sequence[float]] | np.ndarray,
    *,
    label: str,
    levels: Sequence[float] = (0.5, 0.9, 0.95, 0.99),
) -> dict[str, object]:
    candidate_array = np.asarray(candidate, dtype=float).reshape(-1)
    mean_array = np.asarray(mean, dtype=float).reshape(-1)
    covariance_array = _symmetrize_covariance(np.asarray(covariance, dtype=float))
    if candidate_array.shape != mean_array.shape or covariance_array.shape != (candidate_array.size, candidate_array.size):
        raise ValueError("candidate, mean, and covariance shapes are inconsistent.")
    residual = candidate_array - mean_array
    if np.any(~np.isfinite(covariance_array)):
        return {
            "label": label,
            "degrees_of_freedom": 0,
            "rank": 0,
            "mahalanobis_distance": math.inf,
            "mahalanobis_distance_squared": math.inf,
            "confidence_level_containing_point": 1.0,
            "gaussian_log_density": -math.inf,
            "inside_confidence_levels": {str(float(level)): False for level in levels},
            "residual": residual.tolist(),
        }
    eigenvalues, eigenvectors = np.linalg.eigh(covariance_array)
    spectral_scale = float(np.max(np.abs(eigenvalues))) if eigenvalues.size else 0.0
    tolerance = 1.0e-12 * max(spectral_scale, np.finfo(float).tiny)
    positive = eigenvalues > tolerance
    rank = int(np.count_nonzero(positive))
    null_projection = eigenvectors[:, ~positive].T @ residual if rank < candidate_array.size else np.zeros(0, dtype=float)
    outside_support = bool(null_projection.size and np.linalg.norm(null_projection) > math.sqrt(tolerance))
    if rank == 0:
        mahalanobis_squared = 0.0 if not outside_support else math.inf
        log_density = 0.0 if not outside_support else -math.inf
        confidence_level = 0.0 if not outside_support else 1.0
    elif outside_support:
        mahalanobis_squared = math.inf
        log_density = -math.inf
        confidence_level = 1.0
    else:
        projected = eigenvectors[:, positive].T @ residual
        positive_eigenvalues = eigenvalues[positive]
        mahalanobis_squared = float(np.sum((projected**2) / positive_eigenvalues))
        log_pseudodeterminant = float(np.sum(np.log(positive_eigenvalues)))
        log_density = float(-0.5 * (rank * math.log(2.0 * math.pi) + log_pseudodeterminant + mahalanobis_squared))
        confidence_level = float(chi2.cdf(mahalanobis_squared, rank))
    mahalanobis_distance = math.inf if not math.isfinite(mahalanobis_squared) else float(math.sqrt(mahalanobis_squared))
    inside_levels = {
        str(float(level)): bool(math.isfinite(mahalanobis_squared) and confidence_level <= float(level))
        for level in levels
    }
    return {
        "label": label,
        "degrees_of_freedom": rank,
        "rank": rank,
        "mahalanobis_distance": mahalanobis_distance,
        "mahalanobis_distance_squared": float(mahalanobis_squared),
        "confidence_level_containing_point": confidence_level,
        "gaussian_log_density": log_density,
        "inside_confidence_levels": inside_levels,
        "residual": residual.tolist(),
    }


def _linearized_empirical_ephemeris_comparison(
    linearized_ephemeris: Mapping[str, object],
    empirical_ephemeris: Mapping[str, object],
    *,
    covariance_relative_tolerance: float,
    mean_sigma_tolerance: float = 3.0,
) -> dict[str, object]:
    linearized_rows = linearized_ephemeris.get("rows", [])
    if isinstance(linearized_rows, str) or not isinstance(linearized_rows, Sequence):
        linearized_rows = []
    empirical_summary = empirical_ephemeris.get("position_distribution_ephemeris", {})
    if not isinstance(empirical_summary, Mapping):
        empirical_summary = {}
    empirical_means = np.asarray(empirical_summary.get("mean_positions", []), dtype=float)
    empirical_covariances = np.asarray(empirical_summary.get("flat_covariances", []), dtype=float)
    times = np.asarray(empirical_ephemeris.get("times", []), dtype=float)
    row_count = min(len(linearized_rows), len(empirical_means), len(empirical_covariances))
    rows: list[dict[str, object]] = []
    linearized_consistent_until: float | None = None
    first_break_time: float | None = None
    for index in range(row_count):
        linearized_row = linearized_rows[index]
        if not isinstance(linearized_row, Mapping):
            continue
        time = float(times[index]) if index < len(times) else float(linearized_row.get("time", index))
        linearized_mean = np.asarray(linearized_row.get("mean_positions", []), dtype=float)
        empirical_mean = np.asarray(empirical_means[index], dtype=float)
        linearized_covariance = np.asarray(linearized_row.get("position_covariance", []), dtype=float)
        empirical_covariance = np.asarray(empirical_covariances[index], dtype=float)
        mean_gap_norm = (
            float(np.linalg.norm(empirical_mean - linearized_mean))
            if empirical_mean.shape == linearized_mean.shape and empirical_mean.size
            else math.inf
        )
        covariance_gap = (
            float(np.linalg.norm(empirical_covariance - linearized_covariance, ord="fro"))
            if empirical_covariance.shape == linearized_covariance.shape and empirical_covariance.size
            else math.inf
        )
        empirical_norm = (
            float(np.linalg.norm(empirical_covariance, ord="fro"))
            if empirical_covariance.size
            else math.inf
        )
        linearized_norm = (
            float(np.linalg.norm(linearized_covariance, ord="fro"))
            if linearized_covariance.size
            else math.inf
        )
        covariance_scale = max(empirical_norm, linearized_norm, 1.0e-300)
        covariance_relative_gap = (
            covariance_gap / covariance_scale
            if math.isfinite(covariance_gap) and math.isfinite(covariance_scale)
            else math.inf
        )
        empirical_std = (
            np.sqrt(np.maximum(np.diag(empirical_covariance), 0.0))
            if empirical_covariance.ndim == 2
            else np.asarray([math.inf], dtype=float)
        )
        linearized_std = (
            np.sqrt(np.maximum(np.diag(linearized_covariance), 0.0))
            if linearized_covariance.ndim == 2
            else np.asarray([math.inf], dtype=float)
        )
        spread_scale = max(float(np.max(empirical_std)), float(np.max(linearized_std)), 1.0e-300)
        mean_gap_in_sigma_units = mean_gap_norm / spread_scale
        consistent = bool(
            covariance_relative_gap <= covariance_relative_tolerance
            and mean_gap_in_sigma_units <= mean_sigma_tolerance
        )
        if consistent and first_break_time is None:
            linearized_consistent_until = time
        elif first_break_time is None:
            first_break_time = time
        rows.append(
            {
                "time": time,
                "mean_gap_norm": mean_gap_norm,
                "mean_gap_in_sigma_units": float(mean_gap_in_sigma_units),
                "covariance_frobenius_gap": covariance_gap,
                "covariance_relative_gap": float(covariance_relative_gap),
                "linearized_consistent_with_empirical": consistent,
            }
        )
    final_row = rows[-1] if rows else {}
    return {
        "comparison_schema_version": 1,
        "row_count": len(rows),
        "covariance_relative_tolerance": float(covariance_relative_tolerance),
        "mean_sigma_tolerance": float(mean_sigma_tolerance),
        "linearized_consistent_until": linearized_consistent_until,
        "first_break_time": first_break_time,
        "target_time_consistent": final_row.get("linearized_consistent_with_empirical") is True,
        "final_covariance_relative_gap": float(final_row.get("covariance_relative_gap", math.inf)),
        "final_mean_gap_in_sigma_units": float(final_row.get("mean_gap_in_sigma_units", math.inf)),
        "rows": rows,
    }


def _initial_state_covariance(
    state_dimension: int,
    physical_dimension: int,
    *,
    initial_state_covariance: Sequence[Sequence[float]] | None,
    position_scale: float,
    velocity_scale: float,
    masses: Sequence[float] | None = None,
    preserve_center_of_mass: bool = False,
) -> np.ndarray:
    if initial_state_covariance is not None:
        covariance = np.asarray(initial_state_covariance, dtype=float)
        if covariance.shape != (state_dimension, state_dimension):
            raise ValueError("initial_state_covariance must have shape (state_dim, state_dim).")
        if np.any(~np.isfinite(covariance)):
            raise ValueError("initial_state_covariance must contain only finite values.")
        return _symmetrize_covariance(covariance)
    position_scale = _nonnegative_float(position_scale, "position_scale")
    velocity_scale = _nonnegative_float(velocity_scale, "velocity_scale")
    position_width = 3 * physical_dimension
    if preserve_center_of_mass:
        if masses is None:
            raise ValueError("masses are required when preserve_center_of_mass is true.")
        position_covariance = _center_of_mass_preserving_covariance_block(
            masses,
            physical_dimension,
            position_scale,
        )
        velocity_covariance = _center_of_mass_preserving_covariance_block(
            masses,
            physical_dimension,
            velocity_scale,
        )
        covariance = np.zeros((state_dimension, state_dimension), dtype=float)
        covariance[:position_width, :position_width] = position_covariance
        covariance[position_width:, position_width:] = velocity_covariance
        return covariance
    diagonal = np.concatenate(
        [
            np.full(position_width, position_scale**2, dtype=float),
            np.full(state_dimension - position_width, velocity_scale**2, dtype=float),
        ]
    )
    return np.diag(diagonal)


def _center_of_mass_preserving_covariance_block(
    masses: Sequence[float],
    physical_dimension: int,
    scale: float,
) -> np.ndarray:
    masses_array = np.asarray(masses, dtype=float)
    if masses_array.shape != (3,) or np.any(~np.isfinite(masses_array)) or np.any(masses_array <= 0.0):
        raise ValueError("masses must contain exactly three finite positive values.")
    if physical_dimension not in (2, 3):
        raise ValueError("physical_dimension must be 2 or 3.")
    weights = masses_array / np.sum(masses_array)
    body_projection = np.eye(3, dtype=float) - np.ones((3, 1), dtype=float) @ weights[None, :]
    body_covariance = (scale**2) * (body_projection @ body_projection.T)
    covariance = np.zeros((3 * physical_dimension, 3 * physical_dimension), dtype=float)
    for axis in range(physical_dimension):
        indices = [body_index * physical_dimension + axis for body_index in range(3)]
        covariance[np.ix_(indices, indices)] = body_covariance
    return _symmetrize_covariance(covariance)


def _linearized_flow_map(
    system: GeneralThreeBodySystem,
    initial_state: np.ndarray,
    target_time: float,
    *,
    jacobian_step: float,
    rtol: float,
    atol: float,
) -> dict[str, object]:
    state_dimension = initial_state.size
    identity = np.eye(state_dimension, dtype=float)
    if target_time == 0.0:
        return {
            "success": True,
            "message": "target_time is zero; returned identity state-transition matrix.",
            "final_state": initial_state.copy(),
            "transition_matrix": identity,
        }
    combined_initial = np.concatenate([initial_state, identity.reshape(-1)])

    def combined_rhs(time: float, combined_state: np.ndarray) -> np.ndarray:
        current_state = combined_state[:state_dimension]
        transition = combined_state[state_dimension:].reshape(state_dimension, state_dimension)
        jacobian = finite_difference_jacobian(system, current_state, time=time, step=jacobian_step)
        return np.concatenate([system.rhs(time, current_state), (jacobian @ transition).reshape(-1)])

    solution = solve_ivp(
        fun=combined_rhs,
        t_span=(0.0, target_time),
        y0=combined_initial,
        method="DOP853",
        t_eval=(target_time,),
        rtol=rtol,
        atol=atol,
    )
    if solution.y.size == 0:
        return {
            "success": False,
            "message": str(solution.message),
            "final_state": np.full_like(initial_state, np.nan, dtype=float),
            "transition_matrix": np.full((state_dimension, state_dimension), np.nan, dtype=float),
        }
    final = np.asarray(solution.y[:, -1], dtype=float)
    return {
        "success": bool(solution.success),
        "message": str(solution.message),
        "final_state": final[:state_dimension],
        "transition_matrix": final[state_dimension:].reshape(state_dimension, state_dimension),
    }


def _linearized_flow_trace(
    system: GeneralThreeBodySystem,
    initial_state: np.ndarray,
    target_time: float,
    *,
    samples: int,
    jacobian_step: float,
    rtol: float,
    atol: float,
) -> dict[str, object]:
    state_dimension = initial_state.size
    identity = np.eye(state_dimension, dtype=float)
    t_eval = _prediction_times(target_time, samples)
    if target_time == 0.0:
        return {
            "success": True,
            "message": "target_time is zero; returned identity state-transition matrix.",
            "times": np.array([0.0], dtype=float),
            "states": np.asarray([initial_state.copy()], dtype=float),
            "transition_matrices": np.asarray([identity], dtype=float),
        }
    combined_initial = np.concatenate([initial_state, identity.reshape(-1)])

    def combined_rhs(time: float, combined_state: np.ndarray) -> np.ndarray:
        current_state = combined_state[:state_dimension]
        transition = combined_state[state_dimension:].reshape(state_dimension, state_dimension)
        jacobian = finite_difference_jacobian(system, current_state, time=time, step=jacobian_step)
        return np.concatenate([system.rhs(time, current_state), (jacobian @ transition).reshape(-1)])

    solution = solve_ivp(
        fun=combined_rhs,
        t_span=(0.0, target_time),
        y0=combined_initial,
        method="DOP853",
        t_eval=t_eval,
        rtol=rtol,
        atol=atol,
    )
    if solution.y.size == 0:
        return {
            "success": False,
            "message": str(solution.message),
            "times": np.asarray(solution.t, dtype=float),
            "states": np.empty((0, state_dimension), dtype=float),
            "transition_matrices": np.empty((0, state_dimension, state_dimension), dtype=float),
        }
    combined = np.asarray(solution.y.T, dtype=float)
    return {
        "success": bool(solution.success),
        "message": str(solution.message),
        "times": np.asarray(solution.t, dtype=float),
        "states": combined[:, :state_dimension],
        "transition_matrices": combined[:, state_dimension:].reshape(-1, state_dimension, state_dimension),
    }


def _linearized_ephemeris_rows(
    system: GeneralThreeBodySystem,
    flow: Mapping[str, object],
    covariance0: np.ndarray,
) -> list[dict[str, object]]:
    times = np.asarray(flow.get("times", []), dtype=float)
    states = np.asarray(flow.get("states", []), dtype=float)
    transitions = np.asarray(flow.get("transition_matrices", []), dtype=float)
    position_width = system.body_count * system.dimension
    rows: list[dict[str, object]] = []
    for time, state, transition in zip(times, states, transitions, strict=False):
        positions, velocities = system.split_state(state)
        if transition.shape != covariance0.shape or np.any(~np.isfinite(transition)):
            position_covariance = np.full((position_width, position_width), math.inf, dtype=float)
            state_covariance = np.full_like(covariance0, math.inf, dtype=float)
            std_positions = np.full((system.body_count, system.dimension), math.inf, dtype=float)
            transition_spectral_radius = math.inf
            transition_condition_number = math.inf
        else:
            state_covariance = _symmetrize_covariance(transition @ covariance0 @ transition.T)
            position_covariance = state_covariance[:position_width, :position_width]
            std_positions = np.sqrt(np.maximum(np.diag(position_covariance), 0.0)).reshape(
                system.body_count,
                system.dimension,
            )
            transition_spectral_radius = float(max(abs(np.linalg.eigvals(transition))))
            transition_condition_number = float(np.linalg.cond(transition))
        rows.append(
            {
                "time": float(time),
                "mean_positions": positions.tolist(),
                "mean_velocities": velocities.tolist(),
                "std_positions": std_positions.tolist(),
                "position_covariance": position_covariance.tolist(),
                "position_confidence_regions": _position_confidence_regions(
                    positions,
                    [
                        position_covariance[
                            body_index * system.dimension : (body_index + 1) * system.dimension,
                            body_index * system.dimension : (body_index + 1) * system.dimension,
                        ]
                        for body_index in range(system.body_count)
                    ],
                    method="linearized-gaussian",
                ),
                "maximum_position_std": float(np.max(std_positions)),
                "state_covariance_trace": float(np.trace(state_covariance)),
                "transition_spectral_radius": transition_spectral_radius,
                "transition_condition_number": transition_condition_number,
            }
        )
    return rows


def _symmetrize_covariance(covariance: np.ndarray) -> np.ndarray:
    covariance = np.asarray(covariance, dtype=float)
    return 0.5 * (covariance + covariance.T)


def _forecast_horizon_rows(
    flow: Mapping[str, object],
    covariance0: np.ndarray,
    *,
    position_width: int,
    physical_dimension: int,
    position_tolerance: float,
) -> list[dict[str, object]]:
    times = np.asarray(flow.get("times", []), dtype=float)
    transitions = np.asarray(flow.get("transition_matrices", []), dtype=float)
    rows: list[dict[str, object]] = []
    for time, transition in zip(times, transitions, strict=False):
        if transition.shape[0] != covariance0.shape[0] or np.any(~np.isfinite(transition)):
            rows.append(
                {
                    "time": float(time),
                    "max_position_std": math.inf,
                    "rms_position_std": math.inf,
                    "uncertainty_to_tolerance_ratio": math.inf,
                    "transition_spectral_radius": math.inf,
                    "transition_condition_number": math.inf,
                    "resolved": False,
                }
            )
            continue
        covariance_t = _symmetrize_covariance(transition @ covariance0 @ transition.T)
        position_covariance = covariance_t[:position_width, :position_width]
        position_variance = np.maximum(np.diag(position_covariance), 0.0)
        position_std = np.sqrt(position_variance).reshape(3, physical_dimension)
        max_position_std = float(np.max(position_std))
        rms_position_std = float(np.sqrt(np.mean(position_variance)))
        ratio = max_position_std / position_tolerance
        rows.append(
            {
                "time": float(time),
                "max_position_std": max_position_std,
                "rms_position_std": rms_position_std,
                "uncertainty_to_tolerance_ratio": float(ratio),
                "transition_spectral_radius": float(max(abs(np.linalg.eigvals(transition)))),
                "transition_condition_number": float(np.linalg.cond(transition)),
                "resolved": bool(ratio <= 1.0),
            }
        )
    return rows


def _forecast_horizon_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {
            "reliable_until": None,
            "first_unresolved_time": None,
            "target_time_resolved": False,
            "reliability_fraction": 0.0,
            "final_uncertainty_to_tolerance_ratio": math.inf,
        }
    reliable_until: float | None = None
    first_unresolved_time: float | None = None
    resolved_prefix_count = 0
    for row in rows:
        resolved = row.get("resolved") is True
        if resolved and first_unresolved_time is None:
            reliable_until = float(row.get("time", math.nan))
            resolved_prefix_count += 1
        elif first_unresolved_time is None:
            first_unresolved_time = float(row.get("time", math.nan))
    final_row = rows[-1]
    return {
        "reliable_until": reliable_until,
        "first_unresolved_time": first_unresolved_time,
        "target_time_resolved": final_row.get("resolved") is True,
        "reliability_fraction": float(resolved_prefix_count / len(rows)),
        "final_uncertainty_to_tolerance_ratio": float(
            final_row.get("uncertainty_to_tolerance_ratio", math.inf)
        ),
    }


def _prediction_distribution_comparison(
    linearized: Mapping[str, object],
    empirical: Mapping[str, object],
) -> dict[str, object]:
    linearized_mean = np.asarray(linearized.get("mean_positions", []), dtype=float)
    empirical_distribution = empirical.get("position_distribution", {})
    if not isinstance(empirical_distribution, Mapping):
        empirical_distribution = {}
    empirical_mean = np.asarray(empirical_distribution.get("mean_positions", []), dtype=float)
    linearized_covariance = np.asarray(linearized.get("position_covariance", []), dtype=float)
    empirical_covariance = np.asarray(empirical_distribution.get("flat_covariance", []), dtype=float)
    if linearized_mean.shape == empirical_mean.shape and linearized_mean.size:
        body_mean_gap = np.linalg.norm(empirical_mean - linearized_mean, axis=1)
        mean_gap_norm = float(np.linalg.norm(empirical_mean - linearized_mean))
        max_body_mean_gap = float(np.max(body_mean_gap))
    else:
        body_mean_gap = np.asarray([], dtype=float)
        mean_gap_norm = math.inf
        max_body_mean_gap = math.inf
    if linearized_covariance.shape == empirical_covariance.shape and linearized_covariance.size:
        covariance_gap = float(np.linalg.norm(empirical_covariance - linearized_covariance, ord="fro"))
        empirical_norm = float(np.linalg.norm(empirical_covariance, ord="fro"))
        linearized_norm = float(np.linalg.norm(linearized_covariance, ord="fro"))
        covariance_relative_gap = covariance_gap / max(empirical_norm, linearized_norm, 1.0e-300)
        empirical_std = np.sqrt(np.maximum(np.diag(empirical_covariance), 0.0))
        linearized_std = np.sqrt(np.maximum(np.diag(linearized_covariance), 0.0))
        max_empirical_std = float(np.max(empirical_std))
        max_linearized_std = float(np.max(linearized_std))
    else:
        covariance_gap = math.inf
        empirical_norm = math.inf
        linearized_norm = math.inf
        covariance_relative_gap = math.inf
        max_empirical_std = math.inf
        max_linearized_std = math.inf
    spread_scale = max(max_empirical_std, max_linearized_std, 1.0e-300)
    return {
        "body_mean_gap": body_mean_gap.tolist(),
        "mean_gap_norm": mean_gap_norm,
        "max_body_mean_gap": max_body_mean_gap,
        "mean_gap_in_sigma_units": float(max_body_mean_gap / spread_scale),
        "covariance_frobenius_gap": covariance_gap,
        "empirical_covariance_frobenius_norm": empirical_norm,
        "linearized_covariance_frobenius_norm": linearized_norm,
        "covariance_relative_gap": covariance_relative_gap,
        "max_empirical_position_std": max_empirical_std,
        "max_linearized_position_std": max_linearized_std,
    }


def _prediction_report_verdict(
    deterministic: Mapping[str, object],
    linearized: Mapping[str, object],
    empirical: Mapping[str, object],
    comparison: Mapping[str, object],
    horizon: Mapping[str, object],
    *,
    linearized_covariance_relative_tolerance: float,
) -> dict[str, object]:
    invariant_certificate = deterministic.get("invariant_certificate", {})
    if not isinstance(invariant_certificate, Mapping):
        invariant_certificate = {}
    deterministic_resolved = bool(
        deterministic.get("success") is True
        and invariant_certificate.get("maximum_relative_energy_drift", math.inf) <= 1.0e-8
    )
    empirical_success_count = int(empirical.get("success_count", 0))
    empirical_failure_count = int(empirical.get("failure_count", 0))
    empirical_resolved = empirical_success_count > 0 and empirical_failure_count == 0
    target_time_resolved = horizon.get("target_time_resolved") is True
    covariance_relative_gap = float(comparison.get("covariance_relative_gap", math.inf))
    mean_gap_in_sigma_units = float(comparison.get("mean_gap_in_sigma_units", math.inf))
    linearized_consistent = bool(
        linearized.get("success") is True
        and empirical_resolved
        and target_time_resolved
        and covariance_relative_gap <= linearized_covariance_relative_tolerance
        and mean_gap_in_sigma_units <= 3.0
    )
    if linearized_consistent:
        recommended_mode = "linearized-gaussian"
    elif empirical_resolved:
        recommended_mode = "empirical-ensemble"
    elif deterministic_resolved:
        recommended_mode = "deterministic-only"
    else:
        recommended_mode = "unresolved"
    return {
        "deterministic_resolved": deterministic_resolved,
        "linearized_consistent_with_ensemble": linearized_consistent,
        "empirical_distribution_resolved": empirical_resolved,
        "target_time_inside_forecast_horizon": target_time_resolved,
        "recommended_mode": recommended_mode,
        "linearized_covariance_relative_tolerance": float(linearized_covariance_relative_tolerance),
        "rationale": _prediction_verdict_rationale(
            recommended_mode,
            deterministic_resolved=deterministic_resolved,
            target_time_resolved=target_time_resolved,
            covariance_relative_gap=covariance_relative_gap,
            mean_gap_in_sigma_units=mean_gap_in_sigma_units,
            empirical_failure_count=empirical_failure_count,
        ),
    }


def _prediction_verdict_rationale(
    recommended_mode: str,
    *,
    deterministic_resolved: bool,
    target_time_resolved: bool,
    covariance_relative_gap: float,
    mean_gap_in_sigma_units: float,
    empirical_failure_count: int,
) -> str:
    if recommended_mode == "linearized-gaussian":
        return (
            "The deterministic trajectory is resolved, and the variational covariance push-forward agrees "
            "with the empirical ensemble within the declared mean/covariance gates; the target time is inside "
            "the declared local forecast horizon."
        )
    if recommended_mode == "empirical-ensemble":
        return (
            "The empirical ensemble integrated successfully, but the linearized Gaussian approximation is "
            f"not promoted: covariance_relative_gap={covariance_relative_gap:.3g}, "
            f"mean_gap_in_sigma_units={mean_gap_in_sigma_units:.3g}, "
            f"target_time_resolved={target_time_resolved}."
        )
    if recommended_mode == "deterministic-only":
        return (
            "Only the nominal trajectory is resolved; the uncertainty propagation did not produce a clean "
            f"ensemble result, with empirical_failure_count={empirical_failure_count}."
        )
    return (
        "The nominal trajectory or uncertainty propagation failed the configured diagnostics; tighten solver "
        f"settings or shorten the forecast horizon. deterministic_resolved={deterministic_resolved}."
    )


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
    word_mode: WordMode = "refined",
) -> ChartWordMarkovChain:
    """Build a symbolic Markov model from refined, return-map, or Poincare-section chart words."""

    atlas = AnalysisAtlas()
    words = []
    for scenario_name in scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    return markov_chain_from_words(tuple(words))


def validate_hysteresis_markov_chain(
    train_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    validation_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    *,
    periods: float = 8.0,
    samples: int = 240,
    stride: int = 20,
    coordinate: str = "hierarchy_perturbation_strength",
    word_mode: WordMode = "refined",
) -> tuple[ChartWordMarkovChain, ChartWordMarkovValidation]:
    """Fit and validate a hysteresis symbolic Markov model."""

    chain = build_hysteresis_markov_chain(
        train_scenarios,
        periods=periods,
        samples=samples,
        stride=stride,
        coordinate=coordinate,
        word_mode=word_mode,
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
        heldout_words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    return chain, validate_markov_chain(chain, tuple(heldout_words))


def compare_hysteresis_markov_to_baseline(
    train_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    validation_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    *,
    periods: float = 8.0,
    samples: int = 240,
    stride: int = 20,
    coordinate: str = "hierarchy_perturbation_strength",
    word_mode: WordMode = "refined",
) -> tuple[ChartWordMarkovChain, ChartWordMarkovBaselineComparison]:
    """Fit hysteresis Markov dynamics and compare against an independent baseline."""

    atlas = AnalysisAtlas()
    training_words = []
    for scenario_name in train_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        training_words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    chain = markov_chain_from_words(tuple(training_words))
    validation_words = []
    for scenario_name in validation_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        validation_words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
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
    word_mode: WordMode = "refined",
    resamples: int = 512,
    confidence_level: float = 0.95,
    random_seed: int = 0,
) -> tuple[ChartWordMarkovChain, ChartWordMarkovBootstrapComparison]:
    """Fit hysteresis Markov dynamics and bootstrap its baseline gain."""

    atlas = AnalysisAtlas()
    training_words = []
    for scenario_name in train_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        training_words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    chain = markov_chain_from_words(tuple(training_words))
    validation_words = []
    for scenario_name in validation_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        validation_words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    return chain, bootstrap_markov_baseline_comparison(
        chain,
        tuple(training_words),
        tuple(validation_words),
        resamples=resamples,
        confidence_level=confidence_level,
        random_seed=random_seed,
    )


def select_hysteresis_markov_order(
    train_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    validation_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    *,
    periods: float = 8.0,
    samples: int = 240,
    stride: int = 20,
    coordinate: str = "hierarchy_perturbation_strength",
    word_mode: WordMode = "refined",
    max_order: int = 2,
    criterion: str = "bic",
) -> ChartWordMarkovOrderSelection:
    """Select independent, first-order, or higher-order hysteresis memory depth."""

    atlas = AnalysisAtlas()
    training_words = []
    for scenario_name in train_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        training_words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    validation_words = []
    for scenario_name in validation_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        validation_words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    return select_markov_order(
        tuple(training_words),
        tuple(validation_words),
        max_order=max_order,
        criterion=criterion,
    )


def run_verification_report(
    *,
    scenario: ReferenceScenario = "hierarchical-flyby",
    periods: float = 8.0,
    samples: int = 500,
    stride: int = 20,
    inner_pair: tuple[int, int] = (0, 1),
    target_contraction: float = 0.35,
    word_mode: WordMode = "refined",
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
    atlas = AnalysisAtlas()
    reports = atlas.analyze_trajectory(reference.system, trajectory, stride=stride)
    heldout_training_runs = _heldout_phase_training_runs(
        scenario,
        periods=periods,
        samples=samples,
    )
    heldout_training_reports = tuple(
        atlas.analyze_trajectory(system, phase_trajectory, stride=stride)
        for system, phase_trajectory in heldout_training_runs
    )
    if heldout_training_reports:
        training_words = tuple(
            _hysteresis_word_from_reports(report_set, coordinate="hierarchy_perturbation_strength", word_mode=word_mode)
            for report_set in heldout_training_reports
        )
        validation_words = (
            _hysteresis_word_from_reports(reports, coordinate="hierarchy_perturbation_strength", word_mode=word_mode),
        )
        chain = markov_chain_from_words(training_words)
        bootstrap_comparison = bootstrap_markov_baseline_comparison(
            chain,
            training_words,
            validation_words,
            resamples=512,
            random_seed=0,
        )
        order_selection = select_markov_order(training_words, validation_words, max_order=2)
        validation_mode = "heldout_binary_phase"
    else:
        chain, bootstrap_comparison = compare_hysteresis_markov_to_baseline_with_uncertainty(
            (scenario,),
            (scenario,),
            periods=periods,
            samples=samples,
            stride=stride,
            word_mode=word_mode,
        )
        order_selection = select_hysteresis_markov_order(
            (scenario,),
            (scenario,),
            periods=periods,
            samples=samples,
            stride=stride,
            word_mode=word_mode,
        )
        validation_mode = "self_reference"
    poincare_sweep = poincare_section_sweep_from_reports(
        reports,
        coordinate="hierarchy_perturbation_strength",
    )
    section_source_reports = heldout_training_reports[0] if heldout_training_reports else reports
    poincare_coordinate_sweep = poincare_coordinate_sweep_from_reports(section_source_reports)
    poincare_training_words = tuple(
        _poincare_word_from_sweep(report_set, poincare_coordinate_sweep)
        for report_set in (heldout_training_reports or (reports,))
    )
    poincare_validation_words = (_poincare_word_from_sweep(reports, poincare_coordinate_sweep),)
    poincare_chain = markov_chain_from_words(poincare_training_words)
    poincare_bootstrap = bootstrap_markov_baseline_comparison(
        poincare_chain,
        poincare_training_words,
        poincare_validation_words,
        resamples=512,
        random_seed=17,
    )
    poincare_order_selection = select_markov_order(poincare_training_words, poincare_validation_words, max_order=2)
    poincare_permutation_control = permutation_control_markov_validation(
        poincare_chain,
        poincare_validation_words,
        permutations=512,
        random_seed=29,
    )
    poincare_section_robustness = poincare_markov_section_robustness(
        heldout_training_reports or (tuple(reports),),
        poincare_coordinate_sweep.best,
        validation_report_sets=(tuple(reports),) if heldout_training_reports else None,
        resamples=128,
        permutations=128,
        random_seed=37,
        minimum_pass_count=1,
        minimum_pass_fraction=0.1,
    )
    symbolic_stride_robustness = _symbolic_stride_robustness(
        atlas,
        validation_run=(reference.system, trajectory),
        training_runs=heldout_training_runs,
        stride_values=_stride_probe_values(stride),
        word_mode=word_mode,
    )
    comparison = bootstrap_comparison.comparison
    return {
        "metadata": {
            "report_schema_version": 2,
            "engine": "threebody-engine",
            "scenario": reference.name,
            "source_scenario": scenario,
            "periods": periods,
            "samples": samples,
            "stride": stride,
            "target_contraction": target_contraction,
            "word_mode": word_mode,
            "random_seeds": {
                "hysteresis_bootstrap": 11,
                "poincare_bootstrap": 29,
                "poincare_permutation_control": 37,
                "symbolic_stride_robustness": 43,
            },
        },
        "jacobi": jacobi_report,
        "hysteresis_markov": {
            "chain": chain.as_dict(),
            "baseline_comparison": comparison.as_dict(),
            "bootstrap_comparison": bootstrap_comparison.as_dict(),
            "order_selection": order_selection.as_dict(),
            "validation_mode": validation_mode,
            "poincare_section_sweep": poincare_sweep.as_dict(),
            "poincare_coordinate_sweep": poincare_coordinate_sweep.as_dict(),
            "poincare_markov": {
                "training_word_lengths": [word.length for word in poincare_training_words],
                "validation_word_lengths": [word.length for word in poincare_validation_words],
                "validation_mode": validation_mode,
                "chain": poincare_chain.as_dict(),
                "bootstrap_comparison": poincare_bootstrap.as_dict(),
                "order_selection": poincare_order_selection.as_dict(),
                "permutation_control": poincare_permutation_control.as_dict(),
                "section_robustness": poincare_section_robustness.as_dict(),
                "stride_robustness": symbolic_stride_robustness,
            },
        },
        "promotion_gates": {
            "picard_certified": bool(jacobi_report["picard_tuning"]["certified"]),
            "picard_contraction_reserve": jacobi_report["picard_tuning"]["contraction_reserve"],
            "hysteresis_beats_independent_baseline": comparison.beats_baseline,
            "hysteresis_significant_baseline_win": bootstrap_comparison.significant_baseline_win,
            "hysteresis_log_likelihood_gain": comparison.log_likelihood_gain,
            "hysteresis_log_likelihood_gain_ci": list(bootstrap_comparison.log_likelihood_gain_ci),
            "hysteresis_selected_markov_order": order_selection.selected_order,
            "hysteresis_memory_order_selected": order_selection.memory_selected,
            "poincare_has_sufficient_section": poincare_sweep.has_sufficient_section,
            "poincare_best_crossing_count": poincare_sweep.best.crossing_count,
            "poincare_coordinate_has_sufficient_section": poincare_coordinate_sweep.has_sufficient_section,
            "poincare_best_coordinate": poincare_coordinate_sweep.best.coordinate,
            "poincare_best_coordinate_crossing_count": poincare_coordinate_sweep.best.best.crossing_count,
            "poincare_markov_significant_baseline_win": poincare_bootstrap.significant_baseline_win,
            "poincare_markov_log_likelihood_gain_ci": list(poincare_bootstrap.log_likelihood_gain_ci),
            "poincare_selected_markov_order": poincare_order_selection.selected_order,
            "poincare_memory_order_selected": poincare_order_selection.memory_selected,
            "poincare_heldout_phase_validation": bool(heldout_training_reports),
            "poincare_passes_permutation_control": poincare_permutation_control.passes_permutation_control,
            "poincare_permutation_control_gap": poincare_permutation_control.actual_minus_control,
            "poincare_section_robust_pass_count": poincare_section_robustness.pass_count,
            "poincare_section_robust_pass_fraction": poincare_section_robustness.pass_fraction,
            "poincare_passes_section_robustness": poincare_section_robustness.passes_robustness,
            "symbolic_stride_robust_pass_count": symbolic_stride_robustness["pass_count"],
            "symbolic_stride_robust_pass_fraction": symbolic_stride_robustness["pass_fraction"],
            "symbolic_passes_stride_robustness": symbolic_stride_robustness["passes_stride_robustness"],
        },
    }


def _hysteresis_word_from_reports(
    reports: tuple[object, ...],
    *,
    coordinate: str,
    word_mode: WordMode,
):
    if word_mode == "refined":
        return refined_chart_word_from_reports(reports)
    if word_mode == "return":
        return return_map_word_from_reports(reports, coordinate=coordinate)
    if word_mode == "poincare":
        return poincare_section_word_from_reports(reports, coordinate=coordinate)
    raise ValueError("word_mode must be 'refined', 'return', or 'poincare'.")


def _heldout_phase_training_runs(
    scenario: ReferenceScenario,
    *,
    periods: float,
    samples: int,
) -> tuple[tuple[object, TrajectoryResult], ...]:
    if scenario != "hierarchical-flyby":
        return ()
    library = OrbitLibrary()
    integrator = AdaptiveIntegrator()
    runs = []
    for binary_phase in (0.5 * math.pi, math.pi):
        phase_scenario = library.general_hierarchical_flyby(
            binary_phase=binary_phase,
            intruder_velocity=(0.8, 1.6),
            duration=periods,
            samples=samples,
        )
        phase_trajectory = integrator.integrate(
            phase_scenario.system,
            phase_scenario.t_span,
            phase_scenario.initial_state,
            t_eval=phase_scenario.t_eval,
        )
        runs.append((phase_scenario.system, phase_trajectory))
    return tuple(runs)


def _stride_probe_values(base_stride: int) -> tuple[int, ...]:
    base = max(int(base_stride), 1)
    return tuple(sorted({max(1, int(round(0.8 * base))), base, max(1, int(round(1.5 * base)))}))


def _symbolic_stride_robustness(
    atlas: AnalysisAtlas,
    *,
    validation_run: tuple[object, TrajectoryResult],
    training_runs: tuple[tuple[object, TrajectoryResult], ...],
    stride_values: tuple[int, ...],
    word_mode: WordMode,
) -> dict[str, object]:
    if not training_runs:
        return {
            "stride_values": [int(stride) for stride in stride_values],
            "evaluated_count": 0,
            "pass_count": 0,
            "pass_fraction": 0.0,
            "minimum_pass_fraction": 1.0,
            "passes_stride_robustness": False,
            "candidates": [],
        }
    rows = []
    for index, stride in enumerate(stride_values):
        validation_reports = atlas.analyze_trajectory(validation_run[0], validation_run[1], stride=stride)
        training_reports = tuple(
            atlas.analyze_trajectory(system, trajectory, stride=stride)
            for system, trajectory in training_runs
        )
        training_words = tuple(
            _hysteresis_word_from_reports(
                report_set,
                coordinate="hierarchy_perturbation_strength",
                word_mode=word_mode,
            )
            for report_set in training_reports
        )
        validation_word = _hysteresis_word_from_reports(
            validation_reports,
            coordinate="hierarchy_perturbation_strength",
            word_mode=word_mode,
        )
        chain = markov_chain_from_words(training_words)
        bootstrap = bootstrap_markov_baseline_comparison(
            chain,
            training_words,
            (validation_word,),
            resamples=64,
            random_seed=101 + index,
        )
        order_selection = select_markov_order(training_words, (validation_word,), max_order=2)
        coordinate_sweep = poincare_coordinate_sweep_from_reports(training_reports[0])
        poincare_training_words = tuple(_poincare_word_from_sweep(report_set, coordinate_sweep) for report_set in training_reports)
        poincare_validation_words = (_poincare_word_from_sweep(validation_reports, coordinate_sweep),)
        poincare_chain = markov_chain_from_words(poincare_training_words)
        poincare_bootstrap = bootstrap_markov_baseline_comparison(
            poincare_chain,
            poincare_training_words,
            poincare_validation_words,
            resamples=64,
            random_seed=151 + index,
        )
        poincare_order = select_markov_order(poincare_training_words, poincare_validation_words, max_order=2)
        permutation = permutation_control_markov_validation(
            poincare_chain,
            poincare_validation_words,
            permutations=64,
            random_seed=181 + index,
        )
        section_robustness = poincare_markov_section_robustness(
            training_reports,
            coordinate_sweep.best,
            validation_report_sets=(validation_reports,),
            resamples=32,
            permutations=32,
            random_seed=211 + index,
            minimum_pass_count=1,
            minimum_pass_fraction=0.1,
        )
        passes = bool(
            bootstrap.significant_baseline_win
            and order_selection.memory_selected
            and coordinate_sweep.has_sufficient_section
            and poincare_bootstrap.significant_baseline_win
            and poincare_order.memory_selected
            and permutation.passes_permutation_control
            and section_robustness.passes_robustness
        )
        rows.append(
            {
                "stride": int(stride),
                "hysteresis_significant_baseline_win": bootstrap.significant_baseline_win,
                "hysteresis_memory_order_selected": order_selection.memory_selected,
                "poincare_best_coordinate": coordinate_sweep.best.coordinate,
                "poincare_best_crossing_count": coordinate_sweep.best.best.crossing_count,
                "poincare_training_word_lengths": [word.length for word in poincare_training_words],
                "poincare_validation_word_length": poincare_validation_words[0].length,
                "poincare_markov_significant_baseline_win": poincare_bootstrap.significant_baseline_win,
                "poincare_memory_order_selected": poincare_order.memory_selected,
                "poincare_passes_permutation_control": permutation.passes_permutation_control,
                "poincare_passes_section_robustness": section_robustness.passes_robustness,
                "passes": passes,
            }
        )
    pass_count = sum(1 for row in rows if row["passes"])
    evaluated_count = len(rows)
    pass_fraction = float(pass_count / evaluated_count) if evaluated_count else 0.0
    return {
        "stride_values": [int(stride) for stride in stride_values],
        "evaluated_count": evaluated_count,
        "pass_count": pass_count,
        "pass_fraction": pass_fraction,
        "minimum_pass_fraction": 1.0,
        "passes_stride_robustness": bool(evaluated_count > 0 and pass_fraction >= 1.0),
        "candidates": rows,
    }


def _poincare_word_from_sweep(reports: tuple[object, ...], sweep: object):
    return poincare_section_word_from_reports(
        reports,
        coordinate=sweep.best.coordinate,
        section_value=sweep.best.best.section_value,
        direction=sweep.best.direction,
    )


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
