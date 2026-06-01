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
    positions_series, _velocities_series = _trajectory_position_velocity_series(system, trajectory)
    close_approach_diagnostics = _close_approach_diagnostics(
        positions_series,
        trajectory.t,
        softening=system.softening,
    )
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
        "close_approach_diagnostics": close_approach_diagnostics,
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
    target_times: Sequence[float] | None = None,
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
        target_times=target_times,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
    positions_series, velocities_series = _trajectory_position_velocity_series(system, trajectory)
    final_state = trajectory.y[-1] if len(trajectory.y) else np.full(system.state_dim, np.nan)
    invariant_certificate = noether_invariant_drift_certificate(system, trajectory).as_dict()
    close_approach_diagnostics = _close_approach_diagnostics(
        positions_series,
        trajectory.t,
        softening=system.softening,
    )
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
        "close_approach_diagnostics": close_approach_diagnostics,
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
    target_times: Sequence[float] | None = None,
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
    sample_close_approach_diagnostics: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for index, state in enumerate(initial_states):
        trajectory = _prediction_trajectory_with_integrator(
            system,
            state,
            target_time,
            samples=sample_count,
            target_times=target_times,
            integrator=integrator,
        )
        if not trajectory.success or len(trajectory.y) == 0:
            failures.append({"index": index, "message": trajectory.message})
            continue
        positions_series, velocities_series = _trajectory_position_velocity_series(system, trajectory)
        successful_positions.append(positions_series)
        sample_close_approach_diagnostics.append(
            _close_approach_diagnostics(
                positions_series,
                trajectory.t,
                softening=system.softening,
            )
        )
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
        target_times=target_times,
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
        "ensemble_close_approach_diagnostics": _ensemble_close_approach_diagnostics(
            sample_close_approach_diagnostics
        ),
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
    target_times: Sequence[float] | None = None,
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
        target_times=target_times,
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
        target_times=target_times,
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
        target_times=target_times,
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
    linearized_diagnostics = linearized_ephemeris.get("linearized_diagnostics", {})
    if not isinstance(linearized_diagnostics, Mapping):
        linearized_diagnostics = {}
    final_sensitivity = linearized_diagnostics.get("final_linearized_sensitivity", {})
    if not isinstance(final_sensitivity, Mapping):
        final_sensitivity = {}
    input_contract = _prediction_input_contract(
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
        target_times=target_times,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
        jacobian_step=jacobian_step,
        position_tolerance=position_tolerance,
        horizon_samples=horizon_samples,
        linearized_covariance_relative_tolerance=linearized_covariance_relative_tolerance,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    answer = {
        "final_positions": final_positions,
        "final_position_distribution": final_distribution,
        "recommended_mode": verdict.get("recommended_mode", "unresolved"),
        "target_time_inside_forecast_horizon": verdict.get("target_time_inside_forecast_horizon") is True,
        "deterministic_resolved": verdict.get("deterministic_resolved") is True,
        "empirical_distribution_resolved": verdict.get("empirical_distribution_resolved") is True,
        "linearized_ephemeris_consistent_until": ephemeris_comparison["linearized_consistent_until"],
        "first_linearized_ephemeris_break_time": ephemeris_comparison["first_break_time"],
        "finite_time_lyapunov_exponent": float(
            final_sensitivity.get("finite_time_lyapunov_exponent", math.inf)
        ),
        "uncertainty_amplification_factor": float(
            final_sensitivity.get("uncertainty_amplification_factor", math.inf)
        ),
        "minimum_pair_distance": deterministic_ephemeris["close_approach_diagnostics"][
            "minimum_pair_distance"
        ],
        "close_approach_warning_level": deterministic_ephemeris["close_approach_diagnostics"][
            "warning_level"
        ],
        "regularization_recommended": deterministic_ephemeris["close_approach_diagnostics"][
            "regularization_recommended"
        ],
    }
    return {
        "prediction_schema_version": 1,
        "prediction_type": "three-body-prediction-solution",
        "target_time": float(target_time),
        "prediction_input_contract": input_contract,
        "prediction_input_sha256": _canonical_json_sha256(input_contract),
        "answer": answer,
        "prediction_summary": _prediction_solution_summary(answer, ephemeris_comparison),
        "mathematical_statement": _prediction_mathematical_statement(
            answer,
            deterministic_ephemeris,
            ephemeris_comparison,
        ),
        "deterministic_ephemeris": deterministic_ephemeris,
        "linearized_gaussian_ephemeris": linearized_ephemeris,
        "distribution_ephemeris": distribution_ephemeris,
        "ephemeris_distribution_comparison": ephemeris_comparison,
        "interpretation_report": interpretation_report,
    }


def solve_three_body_target_positions(
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
    target_times: Sequence[float] | None = None,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    max_step: float = math.inf,
    jacobian_step: float = 1.0e-6,
    position_tolerance: float = 1.0e-3,
    horizon_samples: int = 16,
    linearized_covariance_relative_tolerance: float = 0.75,
    preserve_center_of_mass: bool = True,
    include_solution_bundle: bool = False,
) -> dict[str, object]:
    """Return the compact target-time answer for the original prediction question.

    This is a small public wrapper around the full solution bundle. It keeps the
    direct answer visible: the deterministic positions ``r_i(t)`` and, when an
    uncertainty model is declared, the target-time probability distribution.
    """

    solution = solve_three_body_prediction_problem(
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
        target_times=target_times,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
        jacobian_step=jacobian_step,
        position_tolerance=position_tolerance,
        horizon_samples=horizon_samples,
        linearized_covariance_relative_tolerance=linearized_covariance_relative_tolerance,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    compact = _target_position_solution_from_bundle(solution)
    if include_solution_bundle:
        compact["solution_bundle"] = solution
    return compact


def answer_three_body_problem(
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
    target_times: Sequence[float] | None = None,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    max_step: float = math.inf,
    jacobian_step: float = 1.0e-6,
    position_tolerance: float = 1.0e-3,
    horizon_samples: int = 16,
    linearized_covariance_relative_tolerance: float = 0.75,
    preserve_center_of_mass: bool = True,
    include_solution_bundle: bool = False,
) -> dict[str, object]:
    """Return the direct answer to the original three-body prediction question.

    The answer is deliberately finite-time and diagnostic-gated. It reports the
    deterministic target positions when that readout is defensible, otherwise
    the pushed-forward target distribution or an unresolved verdict.
    """

    input_certificate = _three_body_input_admissibility_certificate(
        masses,
        positions,
        velocities,
        target_time,
        gravitational_constant=gravitational_constant,
        softening=softening,
    )
    if input_certificate.get("admissible") is not True:
        return _inadmissible_three_body_answer(input_certificate)

    target_solution = solve_three_body_target_positions(
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
        target_times=target_times,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
        jacobian_step=jacobian_step,
        position_tolerance=position_tolerance,
        horizon_samples=horizon_samples,
        linearized_covariance_relative_tolerance=linearized_covariance_relative_tolerance,
        preserve_center_of_mass=preserve_center_of_mass,
        include_solution_bundle=include_solution_bundle,
    )
    numerical_convergence_certificate = _target_position_numerical_convergence_certificate(
        masses,
        positions,
        velocities,
        target_time,
        target_positions=target_solution.get("target_positions", []),
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=samples,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
        position_tolerance=position_tolerance,
    )
    system, initial_state = _general_prediction_system(
        masses,
        positions,
        velocities,
        gravitational_constant=gravitational_constant,
        softening=softening,
    )
    initial_positions, initial_velocities = system.split_state(initial_state)
    initial_pair_diagnostics = _initial_pair_distance_diagnostics(initial_positions, 0.0)
    angular_momentum = _angular_momentum_vector(system.masses, initial_positions, initial_velocities)
    readout = target_solution.get("target_readout_decision", {})
    if not isinstance(readout, Mapping):
        readout = {}
    primary_readout = str(readout.get("primary_readout", "unresolved"))
    answer_kind = _three_body_answer_kind(primary_readout)
    regularization_recommended = bool(
        target_solution.get("diagnostics", {}).get("regularization_recommended", False)
        if isinstance(target_solution.get("diagnostics"), Mapping)
        else False
    )
    target_time_resolved = bool(
        target_solution.get("target_sensitivity_budget", {}).get("target_time_resolved", False)
        if isinstance(target_solution.get("target_sensitivity_budget"), Mapping)
        else False
    )
    certificate_validation = validate_three_body_target_prediction_certificate(target_solution)
    probability_answer = dict(target_solution.get("probability_answer", {})) if isinstance(
        target_solution.get("probability_answer"), Mapping
    ) else {}
    probability_answer["distribution"] = target_solution.get("target_position_distribution", {})
    theorem_answer = {
        "theorem_name": "Finite-time Newtonian three-body prediction as a flow-map and push-forward law",
        "statement": (
            "For positive masses and finite non-collisional initial data, the Newtonian initial-value "
            "problem defines a unique local flow Phi_t up to collision or loss of numerical admissibility. "
            "At a finite target time inside the certified diagnostic horizon, the target positions are "
            "r_i(t) = Pi_{r_i} Phi_t(x0). If the initial state is modeled as a probability law mu_0, "
            "the target uncertainty law is mu_t = (Phi_t)_# mu_0."
        ),
        "statement_ko": (
            "양의 질량과 유한한 비충돌 초기자료가 주어지면 뉴턴 초기값 문제는 충돌 또는 "
            "수치적 허용성 상실 전까지 유일한 국소 흐름 Phi_t를 정의한다. 목표시간이 "
            "진단으로 인증된 범위 안에 있으면 각 위치는 r_i(t) = Pi_{r_i} Phi_t(x0)로 읽고, "
            "초기상태를 확률법칙 mu_0로 두면 목표시간의 불확실성 법칙은 mu_t = (Phi_t)_# mu_0이다."
        ),
        "assumptions": [
            "all masses are finite and strictly positive",
            "initial positions and velocities are finite",
            "no two bodies occupy the same initial position",
            "the requested target time is finite",
            "diagnostics do not promote an unresolved close-approach state",
        ],
        "outputs": [
            "deterministic target coordinates r_i(t)",
            "empirical pushed-forward target distribution Law(X_t)",
            "linearized covariance reference P_t = D Phi_t P_0 D Phi_t^T",
            "readout decision explaining whether to publish point coordinates, probability regions, or unresolved",
        ],
        "non_claims": [
            "no finite elementary closed form is claimed for all generic three-body inputs",
            "no prediction is promoted across collision, regularization, or failed diagnostic gates",
            "the empirical law is a reproducible numerical approximation to the push-forward law",
        ],
    }
    answer_status = "answered" if answer_kind != "unresolved" else "unresolved"
    if regularization_recommended:
        answer_status = "limited-by-close-approach"
    numerical_convergence_passed = (
        numerical_convergence_certificate.get("supports_position_answer") is True
    )
    body_answer_table = _direct_three_body_answer_table(
        target_solution,
        numerical_convergence_certificate,
    )
    return {
        "answer_schema_version": 1,
        "answer_type": "three-body-problem-answer",
        "question": {
            "english": (
                "Given masses, initial positions, initial velocities, and finite target time t, "
                "return r_i(t) when defensible or Law(X_t) when uncertainty dominates."
            ),
            "korean": (
                "질량, 초기 위치, 초기 속도, 유한 목표시간 t가 주어졌을 때 "
                "방어 가능하면 r_i(t)를 반환하고, 불확실성이 지배적이면 Law(X_t)를 반환한다."
            ),
        },
        "answer_status": answer_status,
        "answer_kind": answer_kind,
        "claim": target_solution.get("claim"),
        "recommended_mode": target_solution.get("recommended_mode"),
        "primary_readout": primary_readout,
        "input_admissibility": {
            **input_certificate,
            "finite_positive_masses": True,
            "finite_positions_and_velocities": True,
            "finite_target_time": bool(math.isfinite(float(target_time))),
            "no_initial_binary_collision": bool(initial_pair_diagnostics["minimum_pair_distance"] > 0.0),
            "initial_pair_distances": initial_pair_diagnostics,
            "angular_momentum_vector": angular_momentum.tolist(),
            "softening": float(softening),
            "exact_newtonian_equations": bool(float(softening) == 0.0),
            "softening_disclosed": bool(float(softening) > 0.0),
        },
        "mathematical_model": {
            "initial_value_problem": "Newtonian three-body flow on finite non-collisional data",
            "state_flow": "x(t) = Phi_t(x(0))",
            "point_position_answer": "r_i(t) = Pi_{r_i} Phi_t(x(0))",
            "probability_answer": "Law(X_t) = (Phi_t)_# Law(X_0)",
            "linearized_covariance_answer": "P_t = D Phi_t(x0) P_0 D Phi_t(x0)^T",
            "scope": (
                "finite-time, diagnostic-gated prediction; not a finite elementary closed-form "
                "solution of the generic three-body problem"
            ),
        },
        "theorem_answer": theorem_answer,
        "position_answer": {
            "formula": "r_i(t) = Pi_{r_i} Phi_t(x0)",
            "coordinates": target_solution.get("target_positions", []),
            "coordinate_table": target_solution.get("target_position_table", []),
            "body_answer_table": body_answer_table,
            "defensible": bool(
                answer_kind in {
                    "point-position-answer-with-probability-regions",
                    "deterministic-position-answer",
                }
                and target_time_resolved
                and not regularization_recommended
                and numerical_convergence_passed
            ),
        },
        "distribution_answer": {
            "formula": "mu_t = (Phi_t)_# mu_0",
            "law_notation": "Law(X_t) = (Phi_t)_# Law(X_0)",
            "distribution": target_solution.get("target_position_distribution", {}),
            "body_answer_table": body_answer_table,
            "defensible": bool(
                answer_kind
                in {
                    "point-position-answer-with-probability-regions",
                    "probability-distribution-answer",
                }
                and not regularization_recommended
            ),
        },
        "decision_protocol": {
            "ordered_readout": [
                "publish point positions with probability regions when target time is tolerance-resolved",
                "publish only Law(X_t) when uncertainty dominates but diagnostics remain admissible",
                "publish deterministic coordinates only when uncertainty inputs are absent or not promoted",
                "return unresolved when close-approach or diagnostic gates fail",
            ],
            "selected_readout": primary_readout,
            "selected_answer_kind": answer_kind,
        },
        "numerical_convergence_certificate": numerical_convergence_certificate,
        "deterministic_answer": target_solution.get("deterministic_flow_answer", {}),
        "probability_answer": probability_answer,
        "target_positions": target_solution.get("target_positions", []),
        "target_position_distribution": target_solution.get("target_position_distribution", {}),
        "target_position_table": target_solution.get("target_position_table", []),
        "body_answer_table": body_answer_table,
        "target_pair_geometry": target_solution.get("target_pair_geometry", {}),
        "target_sensitivity_budget": target_solution.get("target_sensitivity_budget", {}),
        "target_readout_decision": readout,
        "publishability": {
            "paper_position_claim_defensible": bool(
                answer_kind in {
                    "point-position-answer-with-probability-regions",
                    "deterministic-position-answer",
                }
                and target_time_resolved
                and not regularization_recommended
                and numerical_convergence_passed
            ),
            "paper_distribution_claim_defensible": bool(
                answer_kind
                in {
                    "point-position-answer-with-probability-regions",
                    "probability-distribution-answer",
                }
                and not regularization_recommended
            ),
            "certificate_valid": bool(certificate_validation.get("valid") is True),
            "numerical_convergence_passed": bool(numerical_convergence_passed),
            "limitations": [
                "finite-time answer only",
                "requires finite non-collisional input data",
                "point-position publication requires agreement with a stricter reference integration",
                "close-approach or regularization gates can downgrade the answer",
                "does not claim a finite elementary global closed form",
            ],
        },
        "target_prediction_certificate": target_solution.get("target_prediction_certificate", {}),
        "certificate_validation": certificate_validation,
        "target_solution": target_solution,
    }


def _three_body_input_admissibility_certificate(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    gravitational_constant: float,
    softening: float,
) -> dict[str, object]:
    """Return a non-throwing certificate for the direct three-body question."""

    reasons: list[str] = []
    reasons_ko: list[str] = []
    masses_array: np.ndarray | None = None
    positions_array: np.ndarray | None = None
    velocities_array: np.ndarray | None = None
    try:
        masses_array = np.asarray(masses, dtype=float)
    except (TypeError, ValueError):
        reasons.append("masses cannot be converted to a finite numeric array")
        reasons_ko.append("질량 배열을 유한한 숫자 배열로 변환할 수 없다.")
    try:
        positions_array = np.asarray(positions, dtype=float)
    except (TypeError, ValueError):
        reasons.append("positions cannot be converted to a finite numeric matrix")
        reasons_ko.append("위치 배열을 유한한 숫자 행렬로 변환할 수 없다.")
    try:
        velocities_array = np.asarray(velocities, dtype=float)
    except (TypeError, ValueError):
        reasons.append("velocities cannot be converted to a finite numeric matrix")
        reasons_ko.append("속도 배열을 유한한 숫자 행렬로 변환할 수 없다.")

    finite_positive_masses = (
        masses_array is not None
        and masses_array.shape == (3,)
        and bool(np.all(np.isfinite(masses_array)))
        and bool(np.all(masses_array > 0.0))
    )
    if not finite_positive_masses:
        reasons.append("masses must contain exactly three finite positive values")
        reasons_ko.append("질량은 정확히 세 개의 유한한 양수여야 한다.")

    positions_shape_valid = (
        positions_array is not None
        and positions_array.ndim == 2
        and positions_array.shape[0] == 3
        and positions_array.shape[1] in (2, 3)
    )
    if not positions_shape_valid:
        reasons.append("positions must have shape (3, 2) or (3, 3)")
        reasons_ko.append("위치는 (3, 2) 또는 (3, 3) 형태여야 한다.")

    velocities_shape_valid = (
        velocities_array is not None
        and positions_array is not None
        and positions_shape_valid
        and velocities_array.shape == positions_array.shape
    )
    if not velocities_shape_valid:
        reasons.append("velocities must have the same shape as positions")
        reasons_ko.append("속도는 위치와 같은 형태여야 한다.")

    finite_positions_and_velocities = (
        positions_shape_valid
        and velocities_shape_valid
        and positions_array is not None
        and velocities_array is not None
        and bool(np.all(np.isfinite(positions_array)))
        and bool(np.all(np.isfinite(velocities_array)))
    )
    if not finite_positions_and_velocities:
        reasons.append("positions and velocities must contain only finite values")
        reasons_ko.append("위치와 속도에는 유한한 값만 들어 있어야 한다.")

    finite_target_time = False
    try:
        finite_target_time = math.isfinite(float(target_time))
    except (TypeError, ValueError):
        finite_target_time = False
    if not finite_target_time:
        reasons.append("target_time must be finite")
        reasons_ko.append("목표 시간 target_time은 유한해야 한다.")

    gravitational_constant_positive = False
    try:
        gravitational_constant_positive = math.isfinite(float(gravitational_constant)) and float(
            gravitational_constant
        ) > 0.0
    except (TypeError, ValueError):
        gravitational_constant_positive = False
    if not gravitational_constant_positive:
        reasons.append("gravitational_constant must be finite and positive")
        reasons_ko.append("중력상수는 유한한 양수여야 한다.")

    softening_nonnegative = False
    try:
        softening_nonnegative = math.isfinite(float(softening)) and float(softening) >= 0.0
    except (TypeError, ValueError):
        softening_nonnegative = False
    if not softening_nonnegative:
        reasons.append("softening must be finite and nonnegative")
        reasons_ko.append("softening은 유한한 0 이상의 값이어야 한다.")

    pair_diagnostics: dict[str, object] = {
        "collision_distance_atol": 0.0,
        "minimum_pair_distance": math.nan,
        "minimum_pair": [],
        "pairs": [],
    }
    no_initial_binary_collision = False
    if positions_shape_valid and positions_array is not None and np.all(np.isfinite(positions_array)):
        pair_diagnostics = _initial_pair_distance_diagnostics(positions_array, 0.0)
        no_initial_binary_collision = bool(pair_diagnostics["minimum_pair_distance"] > 0.0)
        if not no_initial_binary_collision:
            reasons.append("initial positions contain a binary collision")
            reasons_ko.append("초기 위치에 두 물체가 같은 위치에 있는 이중 충돌이 포함되어 있다.")

    exact_newtonian_equations = bool(softening_nonnegative and float(softening) == 0.0)
    softened_initial_collision_regularized = bool(
        softening_nonnegative and float(softening) > 0.0 and not no_initial_binary_collision
    )
    admissible = bool(
        finite_positive_masses
        and positions_shape_valid
        and velocities_shape_valid
        and finite_positions_and_velocities
        and finite_target_time
        and gravitational_constant_positive
        and softening_nonnegative
        and (no_initial_binary_collision or softened_initial_collision_regularized)
    )
    if softened_initial_collision_regularized:
        reasons.append("initial collision is only admissible for the declared softened model")
        reasons_ko.append("초기 충돌은 선언된 softened 모델에서만 허용된다.")
    return {
        "certificate_schema_version": 1,
        "certificate_type": "three-body-input-admissibility",
        "admissible": admissible,
        "newtonian_admissible": bool(admissible and no_initial_binary_collision and exact_newtonian_equations),
        "finite_positive_masses": finite_positive_masses,
        "positions_shape_valid": positions_shape_valid,
        "velocities_shape_valid": velocities_shape_valid,
        "finite_positions_and_velocities": finite_positions_and_velocities,
        "finite_target_time": finite_target_time,
        "gravitational_constant_positive": gravitational_constant_positive,
        "softening_nonnegative": softening_nonnegative,
        "no_initial_binary_collision": no_initial_binary_collision,
        "softened_initial_collision_regularized": softened_initial_collision_regularized,
        "exact_newtonian_equations": exact_newtonian_equations,
        "softening_disclosed": bool(softening_nonnegative and float(softening) > 0.0),
        "initial_pair_distances": pair_diagnostics,
        "blocking_reasons": [] if admissible else reasons,
        "blocking_reasons_ko": [] if admissible else reasons_ko,
        "limitations": (
            [
                "The exact Newtonian point-position question is inadmissible at an initial binary collision."
            ]
            if not no_initial_binary_collision
            else []
        ),
    }


def _inadmissible_three_body_answer(input_certificate: Mapping[str, object]) -> dict[str, object]:
    reasons = input_certificate.get("blocking_reasons", [])
    reasons_ko = input_certificate.get("blocking_reasons_ko", [])
    return {
        "answer_schema_version": 1,
        "answer_type": "three-body-problem-answer",
        "answer_status": "unresolved",
        "answer_kind": "unresolved",
        "claim": "unresolved-target-position",
        "recommended_mode": "unresolved",
        "primary_readout": "unresolved",
        "question": {
            "english": (
                "Given masses, initial positions, initial velocities, and finite target time t, "
                "return r_i(t) when defensible or Law(X_t) when uncertainty dominates."
            ),
            "korean": (
                "질량, 초기 위치, 초기 속도, 유한 목표시간 t가 주어졌을 때 "
                "방어 가능하면 r_i(t)를 반환하고, 불확실성이 지배적이면 Law(X_t)를 반환한다."
            ),
        },
        "unresolved_reason": "input is not admissible for the declared three-body prediction problem",
        "unresolved_reason_ko": "입력이 선언된 삼체 예측 문제의 허용 조건을 만족하지 않는다.",
        "blocking_reasons": reasons if isinstance(reasons, Sequence) else [],
        "blocking_reasons_ko": reasons_ko if isinstance(reasons_ko, Sequence) else [],
        "input_admissibility": dict(input_certificate),
        "mathematical_model": {
            "initial_value_problem": "Newtonian three-body flow on finite non-collisional data",
            "state_flow": "x(t) = Phi_t(x(0))",
            "point_position_answer": "r_i(t) = Pi_{r_i} Phi_t(x(0))",
            "probability_answer": "Law(X_t) = (Phi_t)_# Law(X_0)",
            "scope": "unresolved because the input failed admissibility gates",
        },
        "theorem_answer": {
            "theorem_name": "Finite-time Newtonian three-body prediction as a flow-map and push-forward law",
            "statement": (
                "The theorem-level answer applies only after finite, positive-mass, non-collisional "
                "initial data and finite target time gates pass."
            ),
            "statement_ko": (
                "정리 수준의 답은 유한한 양의 질량, 비충돌 초기자료, 유한 목표시간 gate를 "
                "통과한 뒤에만 적용된다."
            ),
        },
        "position_answer": {"defensible": False, "coordinates": [], "body_answer_table": []},
        "distribution_answer": {"defensible": False, "distribution": {}, "body_answer_table": []},
        "body_answer_table": [],
        "target_positions": [],
        "target_position_distribution": {},
        "target_position_table": [],
        "target_readout_decision": {
            "primary_readout": "unresolved",
            "blocking_reasons": reasons if isinstance(reasons, Sequence) else [],
        },
        "publishability": {
            "paper_position_claim_defensible": False,
            "paper_distribution_claim_defensible": False,
            "certificate_valid": False,
            "numerical_convergence_passed": False,
            "limitations": [
                "input failed admissibility gates",
                "finite-time answer only",
                "requires finite non-collisional input data for the exact Newtonian problem",
            ],
        },
        "target_prediction_certificate": {},
        "certificate_validation": {"valid": False, "checks": {"input_admissible": False}},
        "target_solution": {},
    }


def _target_position_numerical_convergence_certificate(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    target_positions: object,
    gravitational_constant: float,
    softening: float,
    samples: int,
    rtol: float,
    atol: float,
    max_step: float,
    position_tolerance: float,
) -> dict[str, object]:
    """Compare the promoted target coordinates with a stricter integration."""

    reference_rtol = min(float(rtol) * 1.0e-2, 1.0e-12)
    reference_atol = min(float(atol) * 1.0e-2, 1.0e-14)
    reference_samples = max(int(samples) * 2, 8)
    try:
        promoted_positions = np.asarray(target_positions, dtype=float)
        reference = predict_three_body_positions(
            masses,
            positions,
            velocities,
            target_time,
            gravitational_constant=gravitational_constant,
            softening=softening,
            samples=reference_samples,
            rtol=reference_rtol,
            atol=reference_atol,
            max_step=max_step,
        )
        reference_positions = np.asarray(reference.get("positions", []), dtype=float)
        if promoted_positions.shape != reference_positions.shape or promoted_positions.size == 0:
            raise ValueError("promoted and reference target positions have incompatible shapes")
        body_position_deltas = np.linalg.norm(promoted_positions - reference_positions, axis=1)
        max_delta = float(np.max(body_position_deltas))
        rms_delta = float(np.sqrt(np.mean(body_position_deltas**2)))
        reference_scale = float(max(np.max(np.linalg.norm(reference_positions, axis=1)), 1.0))
        tolerance = _positive_float(position_tolerance, "position_tolerance")
        supports_position_answer = bool(
            reference.get("success") is True
            and np.all(np.isfinite(body_position_deltas))
            and max_delta <= tolerance
        )
        return {
            "certificate_schema_version": 1,
            "certificate_type": "target-position-numerical-convergence",
            "method": "stricter-adaptive-DOP853-reference",
            "base_rtol": float(rtol),
            "base_atol": float(atol),
            "reference_rtol": reference_rtol,
            "reference_atol": reference_atol,
            "base_samples": int(samples),
            "reference_samples": reference_samples,
            "position_tolerance": tolerance,
            "body_position_deltas": body_position_deltas.tolist(),
            "maximum_body_position_delta": max_delta,
            "rms_body_position_delta": rms_delta,
            "relative_maximum_body_position_delta": float(max_delta / reference_scale),
            "tolerance_ratio": float(max_delta / tolerance),
            "supports_position_answer": supports_position_answer,
            "reference_success": bool(reference.get("success") is True),
            "reference_invariant_certificate": reference.get("invariant_certificate", {}),
            "interpretation": (
                "The promoted target coordinates are compared with a stricter integration. "
                "A point-position publication requires the maximum body-position delta to stay "
                "inside position_tolerance."
            ),
        }
    except Exception as exc:
        return {
            "certificate_schema_version": 1,
            "certificate_type": "target-position-numerical-convergence",
            "method": "stricter-adaptive-DOP853-reference",
            "base_rtol": float(rtol),
            "base_atol": float(atol),
            "reference_rtol": reference_rtol,
            "reference_atol": reference_atol,
            "base_samples": int(samples),
            "reference_samples": reference_samples,
            "position_tolerance": float(position_tolerance),
            "supports_position_answer": False,
            "reference_success": False,
            "error": str(exc),
        }


def _direct_three_body_answer_table(
    target_solution: Mapping[str, object],
    numerical_convergence_certificate: Mapping[str, object],
) -> list[dict[str, object]]:
    """Build one direct target-time answer row per body."""

    table = target_solution.get("target_position_table", [])
    if not isinstance(table, Sequence) or isinstance(table, (str, bytes, bytearray)):
        return []
    readout = target_solution.get("target_readout_decision", {})
    if not isinstance(readout, Mapping):
        readout = {}
    per_body_readout = readout.get("per_body_readouts", [])
    if not isinstance(per_body_readout, Sequence) or isinstance(per_body_readout, (str, bytes, bytearray)):
        per_body_readout = []
    convergence_deltas = numerical_convergence_certificate.get("body_position_deltas", [])
    if not isinstance(convergence_deltas, Sequence) or isinstance(
        convergence_deltas,
        (str, bytes, bytearray),
    ):
        convergence_deltas = []
    convergence_tolerance = float(numerical_convergence_certificate.get("position_tolerance", math.nan))
    convergence_passed = numerical_convergence_certificate.get("supports_position_answer") is True
    rows: list[dict[str, object]] = []
    for index, row in enumerate(table):
        if not isinstance(row, Mapping):
            continue
        body_index = int(row.get("body_index", index))
        body_readout = per_body_readout[body_index] if body_index < len(per_body_readout) else {}
        if not isinstance(body_readout, Mapping):
            body_readout = {}
        confidence_region = row.get("confidence_region_95", {})
        if not isinstance(confidence_region, Mapping):
            confidence_region = {}
        convergence_delta = (
            float(convergence_deltas[body_index])
            if body_index < len(convergence_deltas)
            else math.nan
        )
        recommended_readout = str(
            body_readout.get("recommended_readout", row.get("recommended_readout", "unresolved"))
        )
        publishable_as_position = bool(
            convergence_passed
            and recommended_readout
            in {
                "point-position-with-confidence-region",
                "probability-region",
            }
        )
        direct_row = {
            "body_index": body_index,
            "answer_formula": "r_i(t) = Pi_{r_i} Phi_t(x0)",
            "probability_formula": "mu_t = (Phi_t)_# mu_0",
            "deterministic_position": row.get("deterministic_position", []),
            "probability_mean": row.get("probability_mean", []),
            "probability_median": row.get("probability_median", []),
            "central_90_interval": row.get("central_90_interval", {}),
            "confidence_region_95": confidence_region,
            "deterministic_to_mean_distance": row.get("deterministic_to_mean_distance", math.nan),
            "relative_95_radius": float(confidence_region.get("relative_95_radius", math.nan)),
            "position_claim_strength": row.get("position_claim_strength", "unresolved"),
            "recommended_readout": recommended_readout,
            "publishable_as_position": publishable_as_position,
            "publishable_as_distribution": recommended_readout
            in {
                "point-position-with-confidence-region",
                "probability-region",
                "distribution-summary-only",
            },
            "numerical_convergence_delta": convergence_delta,
            "numerical_convergence_tolerance": convergence_tolerance,
            "numerical_convergence_passed": bool(
                convergence_passed
                and math.isfinite(convergence_delta)
                and math.isfinite(convergence_tolerance)
                and convergence_delta <= convergence_tolerance
            ),
            "answer_ko": (
                f"body {body_index}: 목표시간 위치는 deterministic_position으로 제시하고, "
                "초기 불확실성을 고려한 확률적 위치는 probability_mean 및 central_90_interval/"
                "confidence_region_95로 제시한다."
            ),
            "answer_en": (
                f"body {body_index}: use deterministic_position for r_i(t), and probability_mean plus "
                "central_90_interval/confidence_region_95 for the pushed-forward uncertainty law."
            ),
        }
        rows.append(direct_row)
    return rows


def validate_three_body_target_prediction_certificate(
    target_solution: Mapping[str, object],
) -> dict[str, object]:
    """Validate the reproducibility certificate embedded in a compact target answer."""

    certificate = target_solution.get("target_prediction_certificate", {})
    if not isinstance(certificate, Mapping):
        certificate = {}
    input_contract = certificate.get("input_contract", {})
    if not isinstance(input_contract, Mapping):
        input_contract = {}
    result_payload = _target_prediction_result_payload(target_solution)
    expected_result_keys = sorted(result_payload)
    checks = {
        "certificate_present": bool(certificate),
        "certificate_type_matches": (
            certificate.get("certificate_type") == "three-body-target-prediction-reproducibility"
        ),
        "certificate_schema_version_matches": certificate.get("certificate_schema_version") == 1,
        "input_contract_present": bool(input_contract),
        "input_contract_sha256_matches": (
            certificate.get("input_contract_sha256") == _canonical_json_sha256(input_contract)
        ),
        "result_payload_sha256_matches": (
            certificate.get("result_payload_sha256") == _canonical_json_sha256(result_payload)
        ),
        "result_payload_keys_match": certificate.get("result_payload_keys") == expected_result_keys,
        "prediction_schema_version_matches": (
            certificate.get("prediction_schema_version") == target_solution.get("prediction_schema_version")
        ),
        "prediction_type_matches": (
            certificate.get("prediction_type") == target_solution.get("prediction_type")
        ),
        "claim_matches": certificate.get("claim") == target_solution.get("claim"),
        "recommended_mode_matches": (
            certificate.get("recommended_mode") == target_solution.get("recommended_mode")
        ),
    }
    return {
        "validation_schema_version": 1,
        "validation_type": "three-body-target-prediction-certificate-validation",
        "valid": all(checks.values()),
        "checks": checks,
        "input_contract_sha256": certificate.get("input_contract_sha256"),
        "computed_input_contract_sha256": _canonical_json_sha256(input_contract),
        "result_payload_sha256": certificate.get("result_payload_sha256"),
        "computed_result_payload_sha256": _canonical_json_sha256(result_payload),
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
    sensitivity = _linearized_sensitivity_diagnostics(transition, target_time)
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
            **sensitivity,
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
    target_times: Sequence[float] | None = None,
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
        target_times=target_times,
        jacobian_step=jacobian_step,
        rtol=rtol,
        atol=atol,
    )
    rows = _linearized_ephemeris_rows(system, flow, covariance0)
    max_position_std = max((float(row["maximum_position_std"]) for row in rows), default=math.inf)
    final_sensitivity = rows[-1].get("linearized_sensitivity", {}) if rows else {}
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
            "final_linearized_sensitivity": final_sensitivity,
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
    target_times: Sequence[float] | None = None,
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


def generate_random_three_body_case(
    *,
    seed: int = 0,
    dimension: int = 2,
    mass_range: tuple[float, float] = (0.6, 1.6),
    position_scale: float = 1.0,
    velocity_scale: float = 0.35,
    minimum_pair_distance: float = 0.35,
    recenter: bool = True,
    max_attempts: int = 512,
) -> dict[str, object]:
    """Generate a reproducible non-collisional random three-body initial state."""

    dimension = int(dimension)
    if dimension not in (2, 3):
        raise ValueError("dimension must be 2 or 3.")
    mass_low, mass_high = (float(mass_range[0]), float(mass_range[1]))
    if not (math.isfinite(mass_low) and math.isfinite(mass_high) and 0.0 < mass_low <= mass_high):
        raise ValueError("mass_range must contain finite positive bounds with low <= high.")
    position_scale = _positive_float(position_scale, "position_scale")
    velocity_scale = _positive_float(velocity_scale, "velocity_scale")
    minimum_pair_distance = _nonnegative_float(minimum_pair_distance, "minimum_pair_distance")
    max_attempts = _validated_positive_int(max_attempts, "max_attempts")
    rng = np.random.default_rng(seed)
    masses = rng.uniform(mass_low, mass_high, size=3)
    positions = np.empty((3, dimension), dtype=float)
    for attempt in range(max_attempts):
        candidate = rng.normal(0.0, position_scale, size=(3, dimension))
        pair_diagnostics = _initial_pair_distance_diagnostics(candidate, minimum_pair_distance)
        if pair_diagnostics["minimum_pair_distance"] > minimum_pair_distance:
            positions = candidate
            break
    else:
        raise ValueError("Could not generate a random case satisfying minimum_pair_distance.")
    velocities = rng.normal(0.0, velocity_scale, size=(3, dimension))
    if recenter:
        positions = _recenter_rows_by_mass(positions, masses)
        velocities = _recenter_rows_by_mass(velocities, masses)
    pair_diagnostics = _initial_pair_distance_diagnostics(positions, minimum_pair_distance)
    return {
        "case_schema_version": 1,
        "case_type": "random-general-three-body-initial-state",
        "seed": int(seed),
        "dimension": dimension,
        "masses": masses.tolist(),
        "positions": positions.tolist(),
        "velocities": velocities.tolist(),
        "generation_parameters": {
            "mass_range": [mass_low, mass_high],
            "position_scale": position_scale,
            "velocity_scale": velocity_scale,
            "minimum_pair_distance": minimum_pair_distance,
            "recenter": bool(recenter),
        },
        "diagnostics": {
            "pair_distances": pair_diagnostics,
            "center_of_mass_position": _mass_weighted_center(masses.tolist(), positions.tolist()),
            "center_of_mass_velocity": _mass_weighted_center(masses.tolist(), velocities.tolist()),
        },
    }


def solve_random_three_body_prediction_demo(
    *,
    seed: int = 0,
    target_time: float = 0.1,
    dimension: int = 2,
    count: int = 16,
    samples: int = 64,
    reference_samples: int = 128,
    position_scale: float = 1.0,
    velocity_scale: float = 0.35,
    uncertainty_position_scale: float = 1.0e-7,
    uncertainty_velocity_scale: float = 1.0e-7,
    success_tolerance: float = 1.0e-6,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
) -> dict[str, object]:
    """Run a reproducible random three-body forecast and compare approaches.

    The reference is the same Newtonian model integrated with stricter tolerances
    and denser sampling. The report is meant to demonstrate a successful
    operational forecast, not a global closed-form theorem.
    """

    target_time = _finite_float(target_time, "target_time")
    count = _validated_positive_int(count, "count")
    samples = _validated_sample_count(samples)
    reference_samples = _validated_sample_count(reference_samples)
    success_tolerance = _positive_float(success_tolerance, "success_tolerance")
    case = generate_random_three_body_case(
        seed=seed,
        dimension=dimension,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
    )
    masses = case["masses"]
    positions = case["positions"]
    velocities = case["velocities"]
    point = predict_three_body_positions(
        masses,
        positions,
        velocities,
        target_time,
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=samples,
        rtol=1.0e-10,
        atol=1.0e-12,
    )
    ephemeris = predict_three_body_ephemeris(
        masses,
        positions,
        velocities,
        target_time,
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=samples,
        rtol=1.0e-10,
        atol=1.0e-12,
    )
    target_solution = solve_three_body_target_positions(
        masses,
        positions,
        velocities,
        target_time,
        count=count,
        position_scale=uncertainty_position_scale,
        velocity_scale=uncertainty_velocity_scale,
        samples=samples,
        horizon_samples=min(16, samples),
        gravitational_constant=gravitational_constant,
        softening=softening,
        preserve_center_of_mass=True,
    )
    direct_answer = answer_three_body_problem(
        masses,
        positions,
        velocities,
        target_time,
        count=count,
        position_scale=uncertainty_position_scale,
        velocity_scale=uncertainty_velocity_scale,
        samples=samples,
        horizon_samples=min(16, samples),
        gravitational_constant=gravitational_constant,
        softening=softening,
        preserve_center_of_mass=True,
    )
    reference = predict_three_body_positions(
        masses,
        positions,
        velocities,
        target_time,
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=reference_samples,
        rtol=1.0e-12,
        atol=1.0e-14,
    )
    reference_positions = np.asarray(reference["positions"], dtype=float)
    approaches = _random_demo_approach_rows(
        point,
        ephemeris,
        target_solution,
        reference_positions,
    )
    max_error = min((float(row["max_body_position_error"]) for row in approaches), default=math.inf)
    point_error = float(approaches[0]["max_body_position_error"]) if approaches else math.inf
    invariant_drift = float(point["invariant_certificate"]["maximum_relative_energy_drift"])
    close_warning = str(point["close_approach_diagnostics"]["warning_level"])
    success = bool(
        point.get("success") is True
        and reference.get("success") is True
        and point_error <= success_tolerance
        and invariant_drift <= 1.0e-8
        and close_warning in {"nominal", "close-approach"}
    )
    return {
        "demo_schema_version": 1,
        "demo_type": "random-three-body-prediction-demo",
        "seed": int(seed),
        "target_time": target_time,
        "case": case,
        "reference": {
            "method": "adaptive-DOP853-high-precision-reference",
            "positions": reference["positions"],
            "velocities": reference["velocities"],
            "success": reference["success"],
            "invariant_certificate": reference["invariant_certificate"],
        },
        "approaches": approaches,
        "target_solution": {
            "claim": target_solution["claim"],
            "recommended_mode": target_solution["recommended_mode"],
            "target_readout_decision": target_solution["target_readout_decision"],
            "target_sensitivity_budget": target_solution["target_sensitivity_budget"],
            "target_distribution_quality": target_solution["target_distribution_quality"],
        },
        "direct_answer": {
            "answer_type": direct_answer["answer_type"],
            "answer_status": direct_answer["answer_status"],
            "answer_kind": direct_answer["answer_kind"],
            "theorem_answer": direct_answer["theorem_answer"],
            "body_answer_table": direct_answer["body_answer_table"],
            "input_admissibility": direct_answer["input_admissibility"],
            "target_readout_decision": direct_answer["target_readout_decision"],
            "numerical_convergence_certificate": direct_answer["numerical_convergence_certificate"],
            "publishability": direct_answer["publishability"],
        },
        "success_report": {
            "success": success,
            "success_tolerance": success_tolerance,
            "best_max_body_position_error": max_error,
            "point_forecast_max_body_position_error": point_error,
            "maximum_relative_energy_drift": invariant_drift,
            "close_approach_warning_level": close_warning,
            "interpretation": (
                "Success means the random-case point forecast agrees with a stricter reference "
                "integration inside success_tolerance while invariant drift and close-approach "
                "diagnostics remain within configured gates."
            ),
        },
    }


def global_closed_form_solution_contract() -> dict[str, object]:
    """Return the only currently defensible global closed-form research contract.

    The contract deliberately separates a finite elementary-function formula,
    which this project does not claim, from a Sundman-style globally convergent
    regularized series representation, which is the viable analytic route for
    the general Newtonian three-body problem under explicit admissibility gates.
    """

    return {
        "contract_schema_version": 1,
        "contract_type": "three-body-global-closed-form-research-contract",
        "promoted_route": "sundman-style-regularized-convergent-series",
        "not_promoted": "finite-elementary-function-global-formula",
        "mathematical_object": {
            "state": "x = (r_0, r_1, r_2, v_0, v_1, v_2)",
            "flow": "x(t) = Phi_t(x(0))",
            "regularized_time_series": "x(tau) = sum_{k >= 0} a_k tau^k after collision/time regularization",
            "physical_time_recovery": "t = T(tau), with T monotone on admissible branches",
            "position_readout": "r_i(t) = Pi_{r_i} Phi_t(x(0))",
        },
        "admissibility_gates": [
            "three finite positive masses",
            "finite 2D or 3D initial positions and velocities",
            "no initial binary collision",
            "nonzero angular momentum gate for the currently promoted Sundman contract",
            "triple-collision branch is not promoted until a regularized collision chart is implemented",
        ],
        "claim_boundaries": {
            "elementary_closed_form_certified": False,
            "global_convergent_series_contract_certified": "conditional-on-admissibility-gates",
            "effective_computation_claim": (
                "not claimed; the contract is an analytic representation target, while numerical "
                "prediction remains the practical solver path"
            ),
        },
        "implementation_status": {
            "initial_state_admissibility_certificate": "implemented",
            "series_coefficient_generator": "not-yet-implemented",
            "collision_regularized_chart_atlas": "not-yet-implemented",
            "effective_truncation_error_bound": "not-yet-implemented",
        },
        "research_program": [
            "prove and encode the regularized time transform used by the series branch",
            "derive coefficient recurrences in center-of-mass and collision-regularized coordinates",
            "add interval bounds for truncation error and inverse time-map recovery",
            "connect the certificate to existing close-approach and Picard gates",
        ],
    }


def assess_three_body_global_closed_form_claim(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    *,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    angular_momentum_atol: float = 1.0e-12,
    angular_momentum_rtol: float = 1.0e-12,
    collision_distance_atol: float = 0.0,
) -> dict[str, object]:
    """Assess whether an initial state can enter the global closed-form route.

    This does not claim a new elementary solution. It returns a machine-readable
    certificate saying whether the supplied initial state passes the gates for a
    Sundman-style regularized convergent-series research program.
    """

    system, initial_state = _general_prediction_system(
        masses,
        positions,
        velocities,
        gravitational_constant=gravitational_constant,
        softening=softening,
    )
    angular_momentum_atol = _nonnegative_float(angular_momentum_atol, "angular_momentum_atol")
    angular_momentum_rtol = _nonnegative_float(angular_momentum_rtol, "angular_momentum_rtol")
    collision_distance_atol = _nonnegative_float(collision_distance_atol, "collision_distance_atol")
    positions_array, velocities_array = system.split_state(initial_state)
    pair_diagnostics = _initial_pair_distance_diagnostics(positions_array, collision_distance_atol)
    angular_momentum = _angular_momentum_vector(system.masses, positions_array, velocities_array)
    angular_momentum_norm = float(np.linalg.norm(angular_momentum))
    characteristic_scale = _angular_momentum_characteristic_scale(
        system.masses,
        positions_array,
        velocities_array,
    )
    angular_momentum_ratio = _safe_ratio(angular_momentum_norm, characteristic_scale)
    nonzero_angular_momentum = bool(
        angular_momentum_norm > angular_momentum_atol
        and angular_momentum_ratio > angular_momentum_rtol
    )
    no_initial_binary_collision = pair_diagnostics["minimum_pair_distance"] > collision_distance_atol
    sundman_admissible = bool(no_initial_binary_collision and nonzero_angular_momentum)
    if sundman_admissible:
        claim_status = "conditional-global-convergent-series-contract"
        promoted_claim = (
            "This initial state passes the implemented gates for the Sundman-style global "
            "regularized convergent-series route."
        )
    elif not no_initial_binary_collision:
        claim_status = "blocked-initial-binary-collision"
        promoted_claim = (
            "The closed-form route is not promoted because the supplied initial state starts "
            "at or below the configured binary-collision distance."
        )
    else:
        claim_status = "blocked-zero-angular-momentum-gate"
        promoted_claim = (
            "The currently implemented global series contract is not promoted because the "
            "angular-momentum gate fails; triple-collision analysis remains unresolved."
        )
    contract = global_closed_form_solution_contract()
    return {
        "certificate_schema_version": 1,
        "certificate_type": "three-body-global-closed-form-claim-assessment",
        "claim_status": claim_status,
        "promoted_claim": promoted_claim,
        "contract": contract,
        "problem": {
            "dimension": system.dimension,
            "masses": [float(mass) for mass in system.masses],
            "gravitational_constant": float(system.gravitational_constant),
            "softening": float(system.softening),
        },
        "initial_state_diagnostics": {
            "pair_distances": pair_diagnostics,
            "angular_momentum_vector": angular_momentum.tolist(),
            "angular_momentum_norm": angular_momentum_norm,
            "characteristic_angular_momentum_scale": characteristic_scale,
            "angular_momentum_ratio": angular_momentum_ratio,
            "center_of_mass_position": _mass_weighted_center(system.masses, positions_array.tolist()),
            "center_of_mass_velocity": _mass_weighted_center(system.masses, velocities_array.tolist()),
        },
        "readiness_checks": {
            "valid_initial_state": True,
            "no_initial_binary_collision": no_initial_binary_collision,
            "nonzero_angular_momentum": nonzero_angular_momentum,
            "sundman_contract_admissible": sundman_admissible,
            "elementary_closed_form_certified": False,
            "series_coefficient_generator_available": False,
            "collision_regularized_chart_atlas_available": False,
            "effective_truncation_error_bound_available": False,
        },
        "next_required_work": [
            "implement coefficient recurrences for the regularized series branch",
            "add binary-collision and triple-collision chart transitions",
            "prove interval truncation bounds for finite partial sums",
            "compare partial sums against the existing adaptive-flow API on benchmark intervals",
        ],
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


def _initial_pair_distance_diagnostics(
    positions: np.ndarray,
    collision_distance_atol: float,
) -> dict[str, object]:
    pair_order = ((0, 1), (0, 2), (1, 2))
    rows: list[dict[str, object]] = []
    distances: list[float] = []
    for left, right in pair_order:
        separation = np.asarray(positions[right] - positions[left], dtype=float)
        distance = float(np.linalg.norm(separation))
        distances.append(distance)
        rows.append(
            {
                "body_pair": [left, right],
                "distance": distance,
                "separation_vector": separation.tolist(),
                "passes_collision_gate": bool(distance > collision_distance_atol),
            }
        )
    minimum_index = int(np.argmin(distances)) if distances else -1
    return {
        "collision_distance_atol": float(collision_distance_atol),
        "minimum_pair_distance": distances[minimum_index] if minimum_index >= 0 else math.inf,
        "minimum_pair": list(pair_order[minimum_index]) if minimum_index >= 0 else [],
        "pairs": rows,
    }


def _angular_momentum_vector(
    masses: Sequence[float],
    positions: np.ndarray,
    velocities: np.ndarray,
) -> np.ndarray:
    masses_array = np.asarray(masses, dtype=float)
    if positions.shape[1] == 2:
        z_component = float(
            np.sum(masses_array * (positions[:, 0] * velocities[:, 1] - positions[:, 1] * velocities[:, 0]))
        )
        return np.asarray([0.0, 0.0, z_component], dtype=float)
    return np.sum(masses_array[:, None] * np.cross(positions, velocities), axis=0)


def _angular_momentum_characteristic_scale(
    masses: Sequence[float],
    positions: np.ndarray,
    velocities: np.ndarray,
) -> float:
    masses_array = np.asarray(masses, dtype=float)
    total_mass = float(np.sum(masses_array))
    center_position = np.sum(masses_array[:, None] * positions, axis=0) / total_mass
    center_velocity = np.sum(masses_array[:, None] * velocities, axis=0) / total_mass
    position_radii = np.linalg.norm(positions - center_position[None, :], axis=1)
    velocity_radii = np.linalg.norm(velocities - center_velocity[None, :], axis=1)
    length_scale = float(np.max(position_radii)) if position_radii.size else 0.0
    velocity_scale = float(np.max(velocity_radii)) if velocity_radii.size else 0.0
    scale = total_mass * length_scale * velocity_scale
    return scale if math.isfinite(scale) and scale > 0.0 else 0.0


def _recenter_rows_by_mass(rows: np.ndarray, masses: np.ndarray) -> np.ndarray:
    weights = masses / float(np.sum(masses))
    center = np.sum(weights[:, None] * rows, axis=0)
    return rows - center[None, :]


def _random_demo_approach_rows(
    point: Mapping[str, object],
    ephemeris: Mapping[str, object],
    target_solution: Mapping[str, object],
    reference_positions: np.ndarray,
) -> list[dict[str, object]]:
    target_distribution = target_solution.get("target_position_distribution", {})
    if not isinstance(target_distribution, Mapping):
        target_distribution = {}
    candidates = [
        (
            "adaptive-flow-final-state",
            point.get("positions", []),
            "Direct DOP853 integration to target_time.",
        ),
        (
            "ephemeris-final-row",
            _indexed_sequence_value(ephemeris.get("positions", []), len(ephemeris.get("positions", [])) - 1),
            "Final row of the sampled deterministic ephemeris.",
        ),
        (
            "target-solution-deterministic-readout",
            target_solution.get("target_positions", []),
            "Compact target solver deterministic r_i(t) readout.",
        ),
        (
            "empirical-mean-readout",
            target_distribution.get("mean_positions", []),
            "Mean of the pushed-forward uncertainty ensemble.",
        ),
    ]
    rows: list[dict[str, object]] = []
    for name, positions, interpretation in candidates:
        position_array = _position_matrix_or_none(positions)
        if position_array is None or reference_positions.shape != position_array.shape:
            max_error = math.inf
            rms_error = math.inf
            errors: list[float] = []
        else:
            body_errors = np.linalg.norm(position_array - reference_positions, axis=1)
            errors = body_errors.tolist()
            max_error = float(np.max(body_errors))
            rms_error = float(np.sqrt(np.mean(body_errors**2)))
        rows.append(
            {
                "approach": name,
                "positions": positions,
                "body_position_errors": errors,
                "max_body_position_error": max_error,
                "rms_body_position_error": rms_error,
                "interpretation": interpretation,
            }
        )
    return rows


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


def _prediction_times(
    target_time: float,
    samples: int,
    target_times: Sequence[float] | None = None,
) -> np.ndarray:
    if target_times is not None:
        return _validated_target_times(target_time, target_times)
    if target_time == 0.0:
        return np.array([0.0], dtype=float)
    return np.linspace(0.0, target_time, samples)


def _validated_target_times(target_time: float, target_times: Sequence[float]) -> np.ndarray:
    times = np.asarray(target_times, dtype=float)
    if times.ndim != 1 or times.size == 0:
        raise ValueError("target_times must be a non-empty one-dimensional sequence.")
    if np.any(~np.isfinite(times)):
        raise ValueError("target_times must contain only finite values.")
    if target_time == 0.0:
        if np.any(times != 0.0):
            raise ValueError("target_times must contain only 0 when target_time is 0.")
        return np.array([0.0], dtype=float)
    direction = 1.0 if target_time > 0.0 else -1.0
    directed_times = direction * times
    if np.any(np.diff(directed_times) <= 0.0):
        raise ValueError("target_times must be strictly monotone in the integration direction.")
    if np.any(directed_times < 0.0) or np.any(directed_times > direction * target_time):
        raise ValueError("target_times must lie between 0 and target_time.")
    if not math.isclose(float(times[-1]), target_time, rel_tol=0.0, abs_tol=1.0e-15):
        raise ValueError("target_times must end at target_time.")
    return times


def _prediction_trajectory(
    system: GeneralThreeBodySystem,
    initial_state: np.ndarray,
    target_time: float,
    *,
    samples: int,
    target_times: Sequence[float] | None = None,
    rtol: float,
    atol: float,
    max_step: float,
) -> TrajectoryResult:
    sample_count = _validated_sample_count(samples)
    t_eval = _prediction_times(target_time, sample_count, target_times=target_times)
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
    target_times: Sequence[float] | None = None,
    integrator: AdaptiveIntegrator,
) -> TrajectoryResult:
    t_eval = _prediction_times(target_time, samples, target_times=target_times)
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


def _close_approach_diagnostics(
    positions_series: Sequence[Sequence[Sequence[float]]] | np.ndarray,
    times: Sequence[float] | np.ndarray,
    *,
    softening: float,
) -> dict[str, object]:
    positions = np.asarray(positions_series, dtype=float)
    time_array = np.asarray(times, dtype=float)
    body_pairs = [(0, 1), (0, 2), (1, 2)]
    if positions.ndim != 3 or positions.shape[0] == 0 or positions.shape[1] != 3:
        return {
            "body_pairs": [[first, second] for first, second in body_pairs],
            "minimum_pair_distance": math.inf,
            "minimum_pair": [],
            "minimum_time": math.nan,
            "minimum_time_index": -1,
            "characteristic_pair_distance": math.inf,
            "minimum_to_characteristic_ratio": math.inf,
            "softening": float(softening),
            "minimum_to_softening_ratio": math.inf,
            "warning_level": "unavailable",
            "regularization_recommended": False,
            "interpretation": "No sampled positions were available for close-approach diagnostics.",
        }
    pair_distances = np.stack(
        [
            np.linalg.norm(positions[:, first, :] - positions[:, second, :], axis=1)
            for first, second in body_pairs
        ],
        axis=1,
    )
    finite_mask = np.isfinite(pair_distances)
    if not np.any(finite_mask):
        minimum_distance = math.inf
        time_index = -1
        pair_index = -1
        characteristic_distance = math.inf
    else:
        masked = np.where(finite_mask, pair_distances, math.inf)
        flat_index = int(np.argmin(masked))
        time_index, pair_index = np.unravel_index(flat_index, masked.shape)
        minimum_distance = float(masked[time_index, pair_index])
        characteristic_distance = float(np.median(pair_distances[finite_mask]))
    if not math.isfinite(characteristic_distance) or characteristic_distance <= 0.0:
        characteristic_ratio = math.inf
    else:
        characteristic_ratio = minimum_distance / characteristic_distance
    softening = float(softening)
    softening_ratio = math.inf if softening <= 0.0 else minimum_distance / softening
    if not math.isfinite(minimum_distance):
        warning_level = "unavailable"
    elif minimum_distance <= 0.0:
        warning_level = "collision-scale"
    elif softening > 0.0 and minimum_distance <= 2.0 * softening:
        warning_level = "softening-scale"
    elif characteristic_ratio <= 1.0e-6:
        warning_level = "collision-scale"
    elif characteristic_ratio <= 1.0e-3:
        warning_level = "close-approach"
    else:
        warning_level = "nominal"
    return {
        "body_pairs": [[first, second] for first, second in body_pairs],
        "minimum_pair_distance": minimum_distance,
        "minimum_pair": [] if pair_index < 0 else list(body_pairs[pair_index]),
        "minimum_time": math.nan if time_index < 0 or time_index >= len(time_array) else float(time_array[time_index]),
        "minimum_time_index": int(time_index),
        "characteristic_pair_distance": characteristic_distance,
        "minimum_to_characteristic_ratio": float(characteristic_ratio),
        "softening": softening,
        "minimum_to_softening_ratio": float(softening_ratio),
        "warning_level": warning_level,
        "regularization_recommended": warning_level in {"collision-scale", "softening-scale", "close-approach"},
        "interpretation": (
            "Close-approach diagnostic over sampled positions. Small minimum_to_characteristic_ratio or "
            "minimum distances near the softening scale indicate that a regularized collision chart or a "
            "smaller integration step should be considered before promoting a long-horizon forecast."
        ),
    }


def _ensemble_close_approach_diagnostics(sample_diagnostics: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not sample_diagnostics:
        return {
            "sample_count": 0,
            "minimum_pair_distance": math.inf,
            "minimum_sample_index": -1,
            "warning_level_counts": {},
            "regularization_recommended_count": 0,
            "regularization_recommended_fraction": 0.0,
        }
    distances = np.asarray(
        [float(row.get("minimum_pair_distance", math.inf)) for row in sample_diagnostics],
        dtype=float,
    )
    minimum_sample_index = int(np.argmin(distances)) if distances.size else -1
    warning_counts: dict[str, int] = {}
    regularization_count = 0
    for row in sample_diagnostics:
        warning_level = str(row.get("warning_level", "unavailable"))
        warning_counts[warning_level] = warning_counts.get(warning_level, 0) + 1
        if row.get("regularization_recommended") is True:
            regularization_count += 1
    sample_count = len(sample_diagnostics)
    return {
        "sample_count": sample_count,
        "minimum_pair_distance": float(distances[minimum_sample_index]) if minimum_sample_index >= 0 else math.inf,
        "minimum_sample_index": minimum_sample_index,
        "minimum_sample_diagnostics": (
            dict(sample_diagnostics[minimum_sample_index]) if minimum_sample_index >= 0 else {}
        ),
        "warning_level_counts": warning_counts,
        "regularization_recommended_count": regularization_count,
        "regularization_recommended_fraction": float(regularization_count / sample_count),
    }


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


def _prediction_solution_summary(
    answer: Mapping[str, object],
    ephemeris_comparison: Mapping[str, object],
) -> dict[str, object]:
    recommended_mode = str(answer.get("recommended_mode", "unresolved"))
    final_positions = answer.get("final_positions", [])
    final_distribution = answer.get("final_position_distribution", {})
    if not isinstance(final_distribution, Mapping):
        final_distribution = {}
    confidence_regions = final_distribution.get("position_confidence_regions", [])
    confidence_95 = _body_confidence_level_summary(confidence_regions, probability=0.95)
    target_inside_horizon = answer.get("target_time_inside_forecast_horizon") is True
    deterministic_resolved = answer.get("deterministic_resolved") is True
    empirical_resolved = answer.get("empirical_distribution_resolved") is True
    regularization_recommended = answer.get("regularization_recommended") is True
    linearized_consistent = ephemeris_comparison.get("target_time_consistent") is True
    claim = _prediction_solution_claim(
        recommended_mode=recommended_mode,
        target_inside_horizon=target_inside_horizon,
        deterministic_resolved=deterministic_resolved,
        empirical_resolved=empirical_resolved,
        linearized_consistent=linearized_consistent,
        regularization_recommended=regularization_recommended,
    )
    if recommended_mode == "linearized-gaussian":
        headline = "Target-time positions are locally predictable with a linearized Gaussian uncertainty model."
    elif recommended_mode == "empirical-ensemble":
        headline = "Target-time positions are best stated as an empirical ensemble distribution."
    elif recommended_mode == "deterministic-only":
        headline = "A deterministic target-time trajectory is available, but the uncertainty model is not resolved."
    else:
        headline = "The target-time prediction is unresolved under the configured diagnostics."
    reliability_factors = {
        "target_time_inside_forecast_horizon": target_inside_horizon,
        "empirical_distribution_resolved": empirical_resolved,
        "linearized_consistent_with_empirical_at_target": linearized_consistent,
        "regularization_recommended": regularization_recommended,
    }
    limitations: list[str] = []
    if not target_inside_horizon:
        limitations.append("Target time is outside the configured forecast-horizon tolerance.")
    if not empirical_resolved:
        limitations.append("Empirical ensemble did not produce a resolved distribution.")
    if not linearized_consistent:
        limitations.append("Linearized Gaussian and empirical ephemeris disagree at the target-time gate.")
    if regularization_recommended:
        limitations.append("Sampled trajectory enters a close-approach regime; regularized coordinates may be required.")
    if not limitations:
        limitations.append("No configured diagnostic blocked the promoted forecast mode.")
    if claim == "target-position-and-distribution":
        reliability_statement = (
            "The target time is inside the forecast horizon, the empirical distribution is resolved, "
            "and the promoted distribution model passes the configured consistency gates."
        )
        actionable_next_step = (
            "Use deterministic_final_positions for the point estimate and confidence_regions_95 for "
            "reported target-time uncertainty."
        )
    elif claim == "distributional-target-position":
        reliability_statement = (
            "A target-time probability distribution is defensible, but a point forecast should be treated "
            "as a distribution summary rather than a uniquely stable prediction."
        )
        actionable_next_step = (
            "Report body-wise means, medians, quantiles, and confidence_regions_95 instead of only a point orbit."
        )
    elif claim == "deterministic-target-position":
        reliability_statement = (
            "The Newtonian flow integration produced a target-time position, but configured uncertainty "
            "diagnostics did not justify a probability claim."
        )
        actionable_next_step = (
            "Reduce target time, tighten tolerances, or provide a calibrated initial_state_covariance "
            "before publishing uncertainty regions."
        )
    else:
        reliability_statement = (
            "The configured diagnostics do not support a stable point or distributional target-time claim."
        )
        actionable_next_step = (
            "Increase ensemble count, shorten target time, use regularized coordinates near close approach, "
            "or switch to a regime-local atlas claim."
        )
    probability_statement = (
        "The final_position_distribution field contains the pushed-forward probability model; "
        "confidence_regions_95 gives per-body 95 percent Gaussian-equivalent regions."
        if confidence_95
        else "No 95 percent confidence region was available from the configured distribution path."
    )
    risk_statement = (
        "Close-approach diagnostics request regularized coordinates before promoting a strong forecast."
        if regularization_recommended
        else "No sampled close-approach diagnostic requested regularized coordinates."
    )
    return {
        "summary_schema_version": 1,
        "claim": claim,
        "headline": headline,
        "recommended_mode": recommended_mode,
        "position_statement": (
            "deterministic_final_positions is the target-time Newtonian flow-map estimate for the three bodies."
        ),
        "probability_statement": probability_statement,
        "reliability_statement": reliability_statement,
        "risk_statement": risk_statement,
        "actionable_next_step": actionable_next_step,
        "deterministic_final_positions": final_positions,
        "probabilistic_final_position_mean": final_distribution.get("mean_positions", []),
        "probabilistic_final_position_median": final_distribution.get("median_positions", []),
        "confidence_regions_95": confidence_95,
        "body_95_confidence_regions": confidence_95,
        "key_metrics": {
            "target_time_inside_forecast_horizon": target_inside_horizon,
            "linearized_target_time_consistent": linearized_consistent,
            "uncertainty_amplification_factor": float(
                answer.get("uncertainty_amplification_factor", math.inf)
            ),
            "finite_time_lyapunov_exponent": float(
                answer.get("finite_time_lyapunov_exponent", math.inf)
            ),
            "minimum_pair_distance": float(answer.get("minimum_pair_distance", math.inf)),
            "close_approach_warning_level": str(answer.get("close_approach_warning_level", "unavailable")),
            "regularization_recommended": regularization_recommended,
            "final_covariance_relative_gap": float(
                ephemeris_comparison.get("final_covariance_relative_gap", math.inf)
            ),
            "final_mean_gap_in_sigma_units": float(
                ephemeris_comparison.get("final_mean_gap_in_sigma_units", math.inf)
            ),
        },
        "reliability_factors": reliability_factors,
        "limitations": limitations,
    }


def _prediction_solution_claim(
    *,
    recommended_mode: str,
    target_inside_horizon: bool,
    deterministic_resolved: bool,
    empirical_resolved: bool,
    linearized_consistent: bool,
    regularization_recommended: bool,
) -> str:
    if (
        recommended_mode == "linearized-gaussian"
        and target_inside_horizon
        and empirical_resolved
        and linearized_consistent
        and not regularization_recommended
    ):
        return "target-position-and-distribution"
    if recommended_mode == "empirical-ensemble" and empirical_resolved and not regularization_recommended:
        return "distributional-target-position"
    if recommended_mode == "deterministic-only" and deterministic_resolved:
        return "deterministic-target-position"
    if empirical_resolved and not regularization_recommended:
        return "distributional-target-position"
    if deterministic_resolved:
        return "deterministic-target-position"
    return "unresolved-target-position"


def _target_position_solution_from_bundle(solution: Mapping[str, object]) -> dict[str, object]:
    answer = solution.get("answer", {})
    if not isinstance(answer, Mapping):
        answer = {}
    summary = solution.get("prediction_summary", {})
    if not isinstance(summary, Mapping):
        summary = {}
    statement = solution.get("mathematical_statement", {})
    if not isinstance(statement, Mapping):
        statement = {}
    deterministic_ephemeris = solution.get("deterministic_ephemeris", {})
    if not isinstance(deterministic_ephemeris, Mapping):
        deterministic_ephemeris = {}
    comparison = solution.get("ephemeris_distribution_comparison", {})
    if not isinstance(comparison, Mapping):
        comparison = {}
    final_distribution = answer.get("final_position_distribution", {})
    if not isinstance(final_distribution, Mapping):
        final_distribution = {}
    body_answers = statement.get("body_position_claims", [])
    target_position_table = _target_position_answer_table(
        body_answers,
        claim=str(summary.get("claim", "unresolved-target-position")),
    )
    center_of_mass_frame = _center_of_mass_frame_summary(
        deterministic_ephemeris,
        final_distribution,
    )
    target_pair_geometry = _target_pair_geometry_summary(
        answer.get("final_positions", []),
        final_distribution,
    )
    target_distribution_quality = _target_distribution_quality_summary(
        final_distribution,
        characteristic_scale=_target_position_characteristic_scale(body_answers),
    )
    target_sensitivity_budget = _target_sensitivity_budget_summary(solution, answer)
    compact = {
        "prediction_schema_version": 1,
        "prediction_type": "three-body-target-position-solution",
        "target_time": float(solution.get("target_time", math.nan)),
        "claim": str(summary.get("claim", "unresolved-target-position")),
        "recommended_mode": str(answer.get("recommended_mode", "unresolved")),
        "target_positions": answer.get("final_positions", []),
        "target_position_distribution": final_distribution,
        "target_position_table": target_position_table,
        "center_of_mass_frame": center_of_mass_frame,
        "target_pair_geometry": target_pair_geometry,
        "target_distribution_quality": target_distribution_quality,
        "target_sensitivity_budget": target_sensitivity_budget,
        "body_answers": body_answers,
        "deterministic_flow_answer": {
            "definition": "r_i(t) = Pi_{r_i} Phi_t(x(0))",
            "positions": answer.get("final_positions", []),
            "positions_relative_to_center_of_mass": center_of_mass_frame.get(
                "target_positions_relative_to_center",
                [],
            ),
            "pair_geometry": target_pair_geometry.get("deterministic", {}),
            "method": deterministic_ephemeris.get("method", "adaptive-DOP853"),
            "invariant_certificate": deterministic_ephemeris.get("invariant_certificate", {}),
        },
        "probability_answer": {
            "definition": "Law(X_t) = (Phi_t)_# Law(X_0)",
            "mean_positions": final_distribution.get("mean_positions", []),
            "median_positions": final_distribution.get("median_positions", []),
            "q05_positions": final_distribution.get("q05_positions", []),
            "q95_positions": final_distribution.get("q95_positions", []),
            "confidence_regions_95": summary.get("body_95_confidence_regions", []),
            "target_position_table": target_position_table,
            "mean_positions_relative_to_center_of_mass": center_of_mass_frame.get(
                "distribution_mean_relative_to_center",
                [],
            ),
            "pair_geometry": target_pair_geometry.get("probability", {}),
            "distribution_quality": target_distribution_quality,
            "sensitivity_budget": target_sensitivity_budget,
            "success_count": final_distribution.get("success_count", 0),
            "failure_count": final_distribution.get("failure_count", 0),
        },
        "diagnostics": {
            "target_time_inside_forecast_horizon": (
                answer.get("target_time_inside_forecast_horizon") is True
            ),
            "linearized_target_time_consistent": comparison.get("target_time_consistent") is True,
            "uncertainty_amplification_factor": float(
                answer.get("uncertainty_amplification_factor", math.inf)
            ),
            "finite_time_lyapunov_exponent": float(
                answer.get("finite_time_lyapunov_exponent", math.inf)
            ),
            "minimum_pair_distance": float(answer.get("minimum_pair_distance", math.inf)),
            "close_approach_warning_level": str(
                answer.get("close_approach_warning_level", "unavailable")
            ),
            "regularization_recommended": answer.get("regularization_recommended") is True,
            "first_linearized_ephemeris_break_time": answer.get(
                "first_linearized_ephemeris_break_time"
            ),
        },
        "mathematical_statement": statement,
    }
    compact["target_readout_decision"] = _target_readout_decision(compact)
    compact["target_prediction_certificate"] = _target_prediction_certificate(
        compact,
        solution,
    )
    return compact


def _target_readout_decision(compact_solution: Mapping[str, object]) -> dict[str, object]:
    claim = str(compact_solution.get("claim", "unresolved-target-position"))
    recommended_mode = str(compact_solution.get("recommended_mode", "unresolved"))
    target_positions = compact_solution.get("target_positions", [])
    distribution = compact_solution.get("target_position_distribution", {})
    if not isinstance(distribution, Mapping):
        distribution = {}
    diagnostics = compact_solution.get("diagnostics", {})
    if not isinstance(diagnostics, Mapping):
        diagnostics = {}
    distribution_quality = compact_solution.get("target_distribution_quality", {})
    if not isinstance(distribution_quality, Mapping):
        distribution_quality = {}
    sensitivity_budget = compact_solution.get("target_sensitivity_budget", {})
    if not isinstance(sensitivity_budget, Mapping):
        sensitivity_budget = {}
    table = compact_solution.get("target_position_table", [])
    deterministic_available = _position_matrix_or_none(target_positions) is not None
    distribution_available = _position_matrix_or_none(distribution.get("mean_positions", [])) is not None
    publishable_probability = claim in {
        "target-position-and-distribution",
        "distributional-target-position",
    }
    publishable_point = claim in {
        "target-position-and-distribution",
        "deterministic-target-position",
    }
    regularization_required = diagnostics.get("regularization_recommended") is True
    linearized_consistent = diagnostics.get("linearized_target_time_consistent") is True
    inside_horizon = diagnostics.get("target_time_inside_forecast_horizon") is True
    sampling_strength = str(distribution_quality.get("sampling_error_strength", "unavailable"))
    if publishable_point and publishable_probability:
        primary_readout = "point-positions-with-probability-regions"
    elif publishable_probability:
        primary_readout = "probability-distribution"
    elif publishable_point:
        primary_readout = "deterministic-positions"
    else:
        primary_readout = "unresolved"
    blocking_reasons: list[str] = []
    if not deterministic_available:
        blocking_reasons.append("deterministic target positions are unavailable")
    if not distribution_available:
        blocking_reasons.append("target probability distribution is unavailable")
    if not inside_horizon:
        blocking_reasons.append("target time is outside the configured forecast horizon")
    if not linearized_consistent:
        blocking_reasons.append("linearized Gaussian and empirical distribution disagree at target time")
    if regularization_required:
        blocking_reasons.append("close approach requests regularized coordinates before a strong claim")
    if sampling_strength == "sampling-noisy":
        blocking_reasons.append("empirical distribution mean is sampling-noisy")
    decision_reasons = (
        blocking_reasons
        if blocking_reasons
        else ["no configured diagnostic blocks the selected readout"]
    )
    return {
        "decision_schema_version": 1,
        "decision_type": "three-body-target-readout-decision",
        "question_answered": (
            "Given masses, initial positions, initial velocities, and target time t, "
            "which target-time position statement is defensible?"
        ),
        "primary_readout": primary_readout,
        "promoted_claim": claim,
        "recommended_mode": recommended_mode,
        "deterministic_answer_available": deterministic_available,
        "probability_answer_available": distribution_available,
        "publishable_point_positions": publishable_point and deterministic_available,
        "publishable_probability_distribution": publishable_probability and distribution_available,
        "requires_regularized_coordinates": regularization_required,
        "mathematical_objects": {
            "point_position": "r_i(t) = Pi_{r_i} Phi_t(x(0))",
            "probability_distribution": "Law(X_t) = (Phi_t)_# Law(X_0)",
        },
        "diagnostic_gates": {
            "target_time_inside_forecast_horizon": inside_horizon,
            "linearized_target_time_consistent": linearized_consistent,
            "sampling_error_strength": sampling_strength,
            "final_uncertainty_to_tolerance_ratio": float(
                sensitivity_budget.get("final_uncertainty_to_tolerance_ratio", math.inf)
            ),
            "regularization_recommended": regularization_required,
        },
        "decision_reasons": decision_reasons,
        "blocking_reasons": blocking_reasons,
        "per_body_readouts": _target_per_body_readout_decisions(table),
    }


def _three_body_answer_kind(primary_readout: str) -> str:
    if primary_readout == "point-positions-with-probability-regions":
        return "point-position-answer-with-probability-regions"
    if primary_readout == "probability-distribution":
        return "probability-distribution-answer"
    if primary_readout == "deterministic-positions":
        return "deterministic-position-answer"
    return "unresolved"


def _target_sensitivity_budget_summary(
    solution: Mapping[str, object],
    answer: Mapping[str, object],
) -> dict[str, object]:
    report = solution.get("interpretation_report", {})
    if not isinstance(report, Mapping):
        report = {}
    horizon = report.get("forecast_horizon", {})
    if not isinstance(horizon, Mapping):
        horizon = {}
    rows = horizon.get("rows", [])
    final_row: Mapping[str, object] = {}
    if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, bytearray)) and rows:
        candidate = rows[-1]
        if isinstance(candidate, Mapping):
            final_row = candidate
    uncertainty_model = horizon.get("uncertainty_model", {})
    if not isinstance(uncertainty_model, Mapping):
        uncertainty_model = {}
    target_time_resolved = horizon.get("target_time_resolved") is True
    final_ratio = float(horizon.get("final_uncertainty_to_tolerance_ratio", math.inf))
    max_position_std = float(final_row.get("max_position_std", math.nan))
    position_tolerance = float(horizon.get("position_tolerance", math.nan))
    return {
        "budget_schema_version": 1,
        "budget_type": "three-body-target-sensitivity-budget",
        "target_time": float(solution.get("target_time", math.nan)),
        "position_tolerance": position_tolerance,
        "target_time_resolved": target_time_resolved,
        "reliable_until": horizon.get("reliable_until"),
        "first_unresolved_time": horizon.get("first_unresolved_time"),
        "reliability_fraction": float(horizon.get("reliability_fraction", math.nan)),
        "final_max_position_std": max_position_std,
        "final_rms_position_std": float(final_row.get("rms_position_std", math.nan)),
        "final_uncertainty_to_tolerance_ratio": final_ratio,
        "forecast_margin_to_tolerance": (
            float(position_tolerance - max_position_std)
            if math.isfinite(position_tolerance) and math.isfinite(max_position_std)
            else math.nan
        ),
        "uncertainty_amplification_factor": float(
            answer.get("uncertainty_amplification_factor", math.inf)
        ),
        "finite_time_lyapunov_exponent": float(
            answer.get("finite_time_lyapunov_exponent", math.inf)
        ),
        "minimum_pair_distance": float(answer.get("minimum_pair_distance", math.inf)),
        "regularization_recommended": answer.get("regularization_recommended") is True,
        "uncertainty_model": dict(uncertainty_model),
        "interpretation": (
            "This local budget compares the variationally propagated target-position "
            "standard deviation against the declared position_tolerance. It is a "
            "finite-time numerical predictability certificate for the supplied initial "
            "uncertainty model, not a global closed-form solution."
        ),
    }


def _target_per_body_readout_decisions(table: object) -> list[dict[str, object]]:
    if not isinstance(table, Sequence) or isinstance(table, (str, bytes, bytearray)):
        return []
    rows: list[dict[str, object]] = []
    for row in table:
        if not isinstance(row, Mapping):
            continue
        rows.append(
            {
                "body_index": int(row.get("body_index", len(rows))),
                "position_claim_strength": str(row.get("position_claim_strength", "unavailable")),
                "recommended_readout": str(row.get("recommended_readout", "unresolved")),
                "deterministic_position": row.get("deterministic_position", []),
                "probability_mean": row.get("probability_mean", []),
                "central_90_interval": row.get("central_90_interval", {}),
                "confidence_region_95": row.get("confidence_region_95", {}),
            }
        )
    return rows


def _target_distribution_quality_summary(
    final_distribution: Mapping[str, object],
    *,
    characteristic_scale: float,
) -> dict[str, object]:
    success_count = int(final_distribution.get("success_count", 0))
    failure_count = int(final_distribution.get("failure_count", 0))
    flat_covariance = final_distribution.get("flat_covariance", [])
    mean_positions = _position_matrix_or_none(final_distribution.get("mean_positions", []))
    body_rows: list[dict[str, object]] = []
    max_standard_errors: list[float] = []
    if success_count > 0 and mean_positions is not None:
        try:
            covariance = np.asarray(flat_covariance, dtype=float)
        except (TypeError, ValueError):
            covariance = np.asarray([])
        dimension = mean_positions.shape[1]
        expected_width = mean_positions.shape[0] * dimension
        if covariance.shape == (expected_width, expected_width) and np.all(np.isfinite(covariance)):
            variances = np.maximum(np.diag(covariance), 0.0).reshape(mean_positions.shape[0], dimension)
            standard_errors = np.sqrt(variances / float(success_count))
            for body_index, row in enumerate(standard_errors):
                max_standard_error = float(np.max(row))
                max_standard_errors.append(max_standard_error)
                body_rows.append(
                    {
                        "body_index": body_index,
                        "mean_standard_error": row.tolist(),
                        "max_mean_standard_error": max_standard_error,
                        "relative_max_mean_standard_error": _safe_ratio(
                            max_standard_error,
                            characteristic_scale,
                        ),
                    }
                )
    max_mean_standard_error = max(max_standard_errors) if max_standard_errors else math.nan
    relative_max = _safe_ratio(max_mean_standard_error, characteristic_scale)
    return {
        "quality_schema_version": 1,
        "sample_count": success_count,
        "failure_count": failure_count,
        "body_mean_standard_errors": body_rows,
        "max_mean_standard_error": max_mean_standard_error,
        "relative_max_mean_standard_error": relative_max,
        "sampling_error_strength": _sampling_error_strength(relative_max),
        "interpretation": (
            "Mean standard errors estimate Monte Carlo sampling uncertainty of the empirical "
            "target-position mean, not the physical spread of the predicted positions."
        ),
    }


def _sampling_error_strength(relative_standard_error: float) -> str:
    if not math.isfinite(relative_standard_error):
        return "unavailable"
    if relative_standard_error <= 1.0e-4:
        return "well-sampled"
    if relative_standard_error <= 1.0e-2:
        return "usable"
    return "sampling-noisy"


def _prediction_input_contract(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    count: int,
    initial_state_covariance: Sequence[Sequence[float]] | None,
    position_scale: float,
    velocity_scale: float,
    seed: int,
    gravitational_constant: float,
    softening: float,
    samples: int,
    target_times: Sequence[float] | None,
    rtol: float,
    atol: float,
    max_step: float,
    jacobian_step: float,
    position_tolerance: float,
    horizon_samples: int,
    linearized_covariance_relative_tolerance: float,
    preserve_center_of_mass: bool,
) -> dict[str, object]:
    return {
        "contract_schema_version": 1,
        "problem_type": "general-newtonian-three-body-initial-value-problem",
        "inputs": {
            "masses": _json_number_array(masses),
            "positions": _json_nested_number_array(positions),
            "velocities": _json_nested_number_array(velocities),
            "target_time": float(target_time),
            "target_times": None if target_times is None else _json_number_array(target_times),
            "initial_state_covariance": (
                None
                if initial_state_covariance is None
                else _json_nested_number_array(initial_state_covariance)
            ),
        },
        "solver_parameters": {
            "gravitational_constant": float(gravitational_constant),
            "softening": float(softening),
            "samples": int(samples),
            "rtol": float(rtol),
            "atol": float(atol),
            "max_step": float(max_step),
            "jacobian_step": float(jacobian_step),
        },
        "uncertainty_parameters": {
            "count": int(count),
            "position_scale": float(position_scale),
            "velocity_scale": float(velocity_scale),
            "seed": int(seed),
            "preserve_center_of_mass": bool(preserve_center_of_mass),
        },
        "interpretation_parameters": {
            "position_tolerance": float(position_tolerance),
            "horizon_samples": int(horizon_samples),
            "linearized_covariance_relative_tolerance": float(
                linearized_covariance_relative_tolerance
            ),
        },
    }


def _target_prediction_certificate(
    compact_solution: Mapping[str, object],
    full_solution: Mapping[str, object],
) -> dict[str, object]:
    input_contract = full_solution.get("prediction_input_contract", {})
    if not isinstance(input_contract, Mapping):
        input_contract = {}
    input_sha256 = full_solution.get("prediction_input_sha256")
    if not isinstance(input_sha256, str):
        input_sha256 = _canonical_json_sha256(input_contract)
    result_payload = _target_prediction_result_payload(compact_solution)
    return {
        "certificate_schema_version": 1,
        "certificate_type": "three-body-target-prediction-reproducibility",
        "input_contract_sha256": input_sha256,
        "input_contract": dict(input_contract),
        "result_payload_sha256": _canonical_json_sha256(result_payload),
        "result_payload_keys": sorted(result_payload),
        "prediction_schema_version": compact_solution.get("prediction_schema_version"),
        "prediction_type": compact_solution.get("prediction_type"),
        "claim": compact_solution.get("claim"),
        "recommended_mode": compact_solution.get("recommended_mode"),
        "reproducibility_statement": (
            "The target answer is tied to this input contract and solver/uncertainty parameter set; "
            "recompute with the same contract to audit the reported target positions and distribution."
        ),
    }


def _target_prediction_result_payload(compact_solution: Mapping[str, object]) -> dict[str, object]:
    excluded = {"target_prediction_certificate", "solution_bundle"}
    return {str(key): value for key, value in compact_solution.items() if key not in excluded}


def _canonical_json_sha256(payload: object) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _json_number_array(values: Sequence[float]) -> list[float]:
    return [float(value) for value in values]


def _json_nested_number_array(values: Sequence[Sequence[float]]) -> list[list[float]]:
    return [[float(value) for value in row] for row in values]


def _target_pair_geometry_summary(
    target_positions: object,
    final_distribution: Mapping[str, object],
) -> dict[str, object]:
    pair_order = [[0, 1], [0, 2], [1, 2]]
    deterministic_positions = _position_matrix_or_none(target_positions)
    mean_positions = _position_matrix_or_none(final_distribution.get("mean_positions", []))
    q05_positions = _position_matrix_or_none(final_distribution.get("q05_positions", []))
    q95_positions = _position_matrix_or_none(final_distribution.get("q95_positions", []))
    pair_rows = []
    deterministic_distances = []
    mean_distances = []
    central_intervals = []
    for left, right in pair_order:
        deterministic_distance = _matrix_row_distance(deterministic_positions, left, right)
        mean_distance = _matrix_row_distance(mean_positions, left, right)
        central_interval = _pair_distance_bounds_from_coordinate_boxes(
            q05_positions,
            q95_positions,
            left,
            right,
        )
        deterministic_distances.append(deterministic_distance)
        mean_distances.append(mean_distance)
        central_intervals.append(central_interval)
        pair_rows.append(
            {
                "body_pair": [left, right],
                "deterministic_distance": deterministic_distance,
                "deterministic_separation_vector": _matrix_row_difference(
                    deterministic_positions,
                    right,
                    left,
                ),
                "probability_mean_distance": mean_distance,
                "probability_mean_separation_vector": _matrix_row_difference(
                    mean_positions,
                    right,
                    left,
                ),
                "central_90_distance_interval_from_coordinate_box": central_interval,
            }
        )
    return {
        "geometry_schema_version": 1,
        "pair_order": pair_order,
        "pair_distances": pair_rows,
        "deterministic": {
            "pair_distances": deterministic_distances,
            "perimeter": _finite_sum(deterministic_distances),
            "triangle_area": _triangle_area(deterministic_positions),
        },
        "probability": {
            "mean_pair_distances": mean_distances,
            "central_90_pair_distance_intervals_from_coordinate_boxes": central_intervals,
            "mean_perimeter": _finite_sum(mean_distances),
            "mean_triangle_area": _triangle_area(mean_positions),
            "interval_note": (
                "Distance intervals are conservative bounds from marginal coordinate q05/q95 boxes, "
                "not exact pair-distance quantiles."
            ),
        },
    }


def _center_of_mass_frame_summary(
    deterministic_ephemeris: Mapping[str, object],
    final_distribution: Mapping[str, object],
) -> dict[str, object]:
    masses = deterministic_ephemeris.get("masses", [])
    positions = deterministic_ephemeris.get("positions", [])
    velocities = deterministic_ephemeris.get("velocities", [])
    initial_positions = _indexed_sequence_value(positions, 0)
    target_positions = _indexed_sequence_value(positions, len(positions) - 1) if isinstance(positions, Sequence) else []
    initial_velocities = _indexed_sequence_value(velocities, 0)
    target_velocities = _indexed_sequence_value(velocities, len(velocities) - 1) if isinstance(velocities, Sequence) else []
    initial_center = _mass_weighted_center(masses, initial_positions)
    target_center = _mass_weighted_center(masses, target_positions)
    initial_center_velocity = _mass_weighted_center(masses, initial_velocities)
    target_center_velocity = _mass_weighted_center(masses, target_velocities)
    mean_positions = final_distribution.get("mean_positions", [])
    return {
        "frame": "mass-weighted-center-of-mass",
        "total_mass": _total_mass(masses),
        "initial_center_position": initial_center,
        "target_center_position": target_center,
        "center_displacement": _vector_difference(target_center, initial_center),
        "initial_center_velocity": initial_center_velocity,
        "target_center_velocity": target_center_velocity,
        "target_center_speed": _vector_norm(target_center_velocity),
        "target_positions_relative_to_center": _subtract_vector_from_rows(target_positions, target_center),
        "distribution_mean_relative_to_center": _subtract_vector_from_rows(mean_positions, target_center),
        "interpretation": (
            "Use target_positions_relative_to_center when comparing intrinsic three-body geometry "
            "independently of inertial-frame translation."
        ),
    }


def _target_position_answer_table(
    body_answers: object,
    *,
    claim: str,
) -> list[dict[str, object]]:
    if not isinstance(body_answers, Sequence) or isinstance(body_answers, (str, bytes, bytearray)):
        return []
    characteristic_scale = _target_position_characteristic_scale(body_answers)
    rows: list[dict[str, object]] = []
    for answer in body_answers:
        if not isinstance(answer, Mapping):
            continue
        confidence_region = answer.get("confidence_region_95", {})
        if not isinstance(confidence_region, Mapping):
            confidence_region = {}
        semi_axes = confidence_region.get("semi_axes", [])
        max_semi_axis = _max_numeric_value(semi_axes)
        deterministic_to_mean_distance = _euclidean_distance(
            answer.get("deterministic_position", []),
            answer.get("distribution_mean", []),
        )
        relative_95_radius = _safe_ratio(max_semi_axis, characteristic_scale)
        rows.append(
            {
                "body_index": int(answer.get("body_index", len(rows))),
                "claim": claim,
                "position_claim_strength": _position_claim_strength(relative_95_radius),
                "recommended_readout": _recommended_position_readout(claim, relative_95_radius),
                "deterministic_position": answer.get("deterministic_position", []),
                "probability_mean": answer.get("distribution_mean", []),
                "probability_median": answer.get("distribution_median", []),
                "central_90_interval": {
                    "lower": answer.get("distribution_q05", []),
                    "upper": answer.get("distribution_q95", []),
                },
                "confidence_region_95": {
                    "center": confidence_region.get("center", []),
                    "semi_axes": semi_axes,
                    "axis_directions": confidence_region.get("axis_directions", []),
                    "max_semi_axis": max_semi_axis,
                    "relative_95_radius": relative_95_radius,
                },
                "deterministic_to_mean_distance": deterministic_to_mean_distance,
                "deterministic_to_mean_distance_relative": _safe_ratio(
                    deterministic_to_mean_distance,
                    characteristic_scale,
                ),
                "characteristic_position_scale": characteristic_scale,
            }
        )
    return rows


def _target_position_characteristic_scale(body_answers: Sequence[object]) -> float:
    positions = []
    for answer in body_answers:
        if not isinstance(answer, Mapping):
            continue
        position = answer.get("deterministic_position", [])
        if not isinstance(position, Sequence) or isinstance(position, (str, bytes, bytearray)):
            continue
        try:
            position_array = np.asarray(position, dtype=float)
        except (TypeError, ValueError):
            continue
        if position_array.ndim == 1 and position_array.size and np.all(np.isfinite(position_array)):
            positions.append(position_array)
    if not positions:
        return math.nan
    stack = np.vstack(positions)
    if len(stack) >= 2:
        pair_distances = [
            float(np.linalg.norm(stack[left] - stack[right]))
            for left in range(len(stack))
            for right in range(left + 1, len(stack))
        ]
        finite_pairs = [distance for distance in pair_distances if math.isfinite(distance)]
        if finite_pairs and max(finite_pairs) > 0.0:
            return max(finite_pairs)
    norms = [float(np.linalg.norm(position)) for position in stack]
    finite_norms = [norm for norm in norms if math.isfinite(norm)]
    if finite_norms and max(finite_norms) > 0.0:
        return max(finite_norms)
    return 1.0


def _position_claim_strength(relative_95_radius: float) -> str:
    if not math.isfinite(relative_95_radius):
        return "unavailable"
    if relative_95_radius <= 1.0e-3:
        return "point-resolved"
    if relative_95_radius <= 1.0e-1:
        return "localized-distribution"
    return "broad-distribution"


def _recommended_position_readout(claim: str, relative_95_radius: float) -> str:
    strength = _position_claim_strength(relative_95_radius)
    if claim == "target-position-and-distribution" and strength == "point-resolved":
        return "point-position-with-confidence-region"
    if strength in {"point-resolved", "localized-distribution"}:
        return "probability-region"
    if strength == "broad-distribution":
        return "distribution-summary-only"
    return "unresolved"


def _prediction_mathematical_statement(
    answer: Mapping[str, object],
    deterministic_ephemeris: Mapping[str, object],
    ephemeris_comparison: Mapping[str, object],
) -> dict[str, object]:
    final_distribution = answer.get("final_position_distribution", {})
    if not isinstance(final_distribution, Mapping):
        final_distribution = {}
    confidence_95 = _body_confidence_level_summary(
        final_distribution.get("position_confidence_regions", []),
        probability=0.95,
    )
    final_positions = answer.get("final_positions", [])
    mean_positions = final_distribution.get("mean_positions", [])
    median_positions = final_distribution.get("median_positions", [])
    q05_positions = final_distribution.get("q05_positions", [])
    q95_positions = final_distribution.get("q95_positions", [])
    body_claims = []
    for body_index in range(3):
        body_claims.append(
            {
                "body_index": body_index,
                "deterministic_position": _indexed_sequence_value(final_positions, body_index),
                "distribution_mean": _indexed_sequence_value(mean_positions, body_index),
                "distribution_median": _indexed_sequence_value(median_positions, body_index),
                "distribution_q05": _indexed_sequence_value(q05_positions, body_index),
                "distribution_q95": _indexed_sequence_value(q95_positions, body_index),
                "confidence_region_95": _confidence_region_for_body(confidence_95, body_index),
            }
        )
    target_time = float(deterministic_ephemeris.get("target_time", math.nan))
    dimension = int(deterministic_ephemeris.get("dimension", 0))
    softening = float(deterministic_ephemeris.get("softening", 0.0))
    return {
        "statement_schema_version": 1,
        "problem_type": "general-newtonian-three-body-initial-value-problem",
        "target_time": target_time,
        "dimension": dimension,
        "masses": list(deterministic_ephemeris.get("masses", [])),
        "gravitational_constant": float(
            deterministic_ephemeris.get("gravitational_constant", 1.0)
        ),
        "softening": softening,
        "deterministic_problem": {
            "state_vector": "x = (r_0, r_1, r_2, v_0, v_1, v_2)",
            "equations": [
                "d r_i / dt = v_i",
                (
                    "d v_i / dt = G * sum_{j != i} m_j * (r_j - r_i) / "
                    "(||r_j - r_i||^2 + epsilon^2)^(3/2)"
                ),
            ],
            "flow_map": "x(t) = Phi_t(x(0))",
            "position_readout": "r_i(t) = Pi_{r_i} Phi_t(x(0))",
            "softening_parameter": "epsilon",
            "softening_value": softening,
        },
        "probability_problem": {
            "initial_law": "X_0 is the declared or generated Gaussian uncertainty around x(0).",
            "exact_pushforward": "Law(X_t) = (Phi_t)_# Law(X_0).",
            "linearized_gaussian": "P_t = D Phi_t(x0) P_0 D Phi_t(x0)^T.",
            "empirical_ensemble": "Samples x_t^k = Phi_t(x_0^k) approximate the pushed-forward law.",
            "confidence_region_meaning": (
                "Each 95 percent body region is a Gaussian-equivalent covariance region "
                "for that body's target-time position."
            ),
        },
        "claim_contract": {
            "promoted_claim": _prediction_solution_claim(
                recommended_mode=str(answer.get("recommended_mode", "unresolved")),
                target_inside_horizon=answer.get("target_time_inside_forecast_horizon") is True,
                deterministic_resolved=answer.get("deterministic_resolved") is True,
                empirical_resolved=answer.get("empirical_distribution_resolved") is True,
                linearized_consistent=ephemeris_comparison.get("target_time_consistent") is True,
                regularization_recommended=answer.get("regularization_recommended") is True,
            ),
            "recommended_mode": str(answer.get("recommended_mode", "unresolved")),
            "target_time_inside_forecast_horizon": (
                answer.get("target_time_inside_forecast_horizon") is True
            ),
            "linearized_target_time_consistent": (
                ephemeris_comparison.get("target_time_consistent") is True
            ),
            "regularization_recommended": answer.get("regularization_recommended") is True,
        },
        "body_position_claims": body_claims,
    }


def _body_confidence_level_summary(
    confidence_regions: object,
    *,
    probability: float,
) -> list[dict[str, object]]:
    if not isinstance(confidence_regions, Sequence) or isinstance(confidence_regions, (str, bytes, bytearray)):
        return []
    rows: list[dict[str, object]] = []
    for region in confidence_regions:
        if not isinstance(region, Mapping):
            continue
        levels = region.get("levels", [])
        selected_level: Mapping[str, object] | None = None
        if isinstance(levels, Sequence) and not isinstance(levels, (str, bytes, bytearray)):
            for level in levels:
                if isinstance(level, Mapping) and math.isclose(
                    float(level.get("probability", math.nan)),
                    probability,
                    rel_tol=0.0,
                    abs_tol=1.0e-12,
                ):
                    selected_level = level
                    break
        if selected_level is None:
            continue
        rows.append(
            {
                "body_index": int(region.get("body_index", len(rows))),
                "center": region.get("center", []),
                "probability": float(probability),
                "semi_axes": selected_level.get("semi_axes", []),
                "axis_directions": selected_level.get("axis_directions", []),
            }
        )
    return rows


def _indexed_sequence_value(values: object, index: int) -> object:
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes, bytearray)):
        if 0 <= index < len(values):
            return values[index]
    return []


def _confidence_region_for_body(
    confidence_regions: Sequence[Mapping[str, object]],
    body_index: int,
) -> dict[str, object]:
    for region in confidence_regions:
        if int(region.get("body_index", -1)) == body_index:
            return dict(region)
    return {}


def _max_numeric_value(values: object) -> float:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        return math.nan
    numeric_values = []
    for value in values:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(numeric):
            numeric_values.append(numeric)
    return max(numeric_values) if numeric_values else math.nan


def _euclidean_distance(left: object, right: object) -> float:
    if (
        not isinstance(left, Sequence)
        or isinstance(left, (str, bytes, bytearray))
        or not isinstance(right, Sequence)
        or isinstance(right, (str, bytes, bytearray))
        or len(left) != len(right)
    ):
        return math.nan
    try:
        left_array = np.asarray(left, dtype=float)
        right_array = np.asarray(right, dtype=float)
    except (TypeError, ValueError):
        return math.nan
    if left_array.shape != right_array.shape or np.any(~np.isfinite(left_array)) or np.any(~np.isfinite(right_array)):
        return math.nan
    return float(np.linalg.norm(left_array - right_array))


def _safe_ratio(numerator: float, denominator: float) -> float:
    if not math.isfinite(numerator) or not math.isfinite(denominator) or denominator <= 0.0:
        return math.nan
    return float(numerator / denominator)


def _total_mass(masses: object) -> float:
    if not isinstance(masses, Sequence) or isinstance(masses, (str, bytes, bytearray)):
        return math.nan
    try:
        mass_array = np.asarray(masses, dtype=float)
    except (TypeError, ValueError):
        return math.nan
    if mass_array.ndim != 1 or mass_array.size == 0 or np.any(~np.isfinite(mass_array)):
        return math.nan
    total = float(np.sum(mass_array))
    return total if total > 0.0 else math.nan


def _mass_weighted_center(masses: object, vectors: object) -> list[float]:
    total = _total_mass(masses)
    if not math.isfinite(total):
        return []
    try:
        mass_array = np.asarray(masses, dtype=float)
        vector_array = np.asarray(vectors, dtype=float)
    except (TypeError, ValueError):
        return []
    if (
        mass_array.ndim != 1
        or vector_array.ndim != 2
        or vector_array.shape[0] != mass_array.size
        or np.any(~np.isfinite(vector_array))
    ):
        return []
    return np.average(vector_array, axis=0, weights=mass_array).tolist()


def _vector_difference(left: object, right: object) -> list[float]:
    try:
        left_array = np.asarray(left, dtype=float)
        right_array = np.asarray(right, dtype=float)
    except (TypeError, ValueError):
        return []
    if (
        left_array.ndim != 1
        or right_array.ndim != 1
        or left_array.shape != right_array.shape
        or np.any(~np.isfinite(left_array))
        or np.any(~np.isfinite(right_array))
    ):
        return []
    return (left_array - right_array).tolist()


def _vector_norm(vector: object) -> float:
    try:
        array = np.asarray(vector, dtype=float)
    except (TypeError, ValueError):
        return math.nan
    if array.ndim != 1 or np.any(~np.isfinite(array)):
        return math.nan
    return float(np.linalg.norm(array))


def _subtract_vector_from_rows(rows: object, vector: object) -> list[list[float]]:
    try:
        row_array = np.asarray(rows, dtype=float)
        vector_array = np.asarray(vector, dtype=float)
    except (TypeError, ValueError):
        return []
    if (
        row_array.ndim != 2
        or vector_array.ndim != 1
        or row_array.shape[1] != vector_array.size
        or np.any(~np.isfinite(row_array))
        or np.any(~np.isfinite(vector_array))
    ):
        return []
    return (row_array - vector_array[None, :]).tolist()


def _position_matrix_or_none(values: object) -> np.ndarray | None:
    try:
        array = np.asarray(values, dtype=float)
    except (TypeError, ValueError):
        return None
    if array.ndim != 2 or array.shape[0] < 3 or array.shape[1] == 0 or np.any(~np.isfinite(array)):
        return None
    return array


def _matrix_row_distance(matrix: np.ndarray | None, left: int, right: int) -> float:
    if matrix is None or left >= len(matrix) or right >= len(matrix):
        return math.nan
    return float(np.linalg.norm(matrix[right] - matrix[left]))


def _matrix_row_difference(matrix: np.ndarray | None, left: int, right: int) -> list[float]:
    if matrix is None or left >= len(matrix) or right >= len(matrix):
        return []
    return (matrix[left] - matrix[right]).tolist()


def _pair_distance_bounds_from_coordinate_boxes(
    lower: np.ndarray | None,
    upper: np.ndarray | None,
    left: int,
    right: int,
) -> dict[str, float]:
    if lower is None or upper is None or left >= len(lower) or right >= len(lower) or lower.shape != upper.shape:
        return {"lower": math.nan, "upper": math.nan}
    left_low = np.minimum(lower[left], upper[left])
    left_high = np.maximum(lower[left], upper[left])
    right_low = np.minimum(lower[right], upper[right])
    right_high = np.maximum(lower[right], upper[right])
    min_components = np.maximum.reduce(
        [
            left_low - right_high,
            right_low - left_high,
            np.zeros_like(left_low),
        ]
    )
    max_components = np.maximum(
        np.abs(left_low - right_high),
        np.abs(left_high - right_low),
    )
    return {
        "lower": float(np.linalg.norm(min_components)),
        "upper": float(np.linalg.norm(max_components)),
    }


def _triangle_area(matrix: np.ndarray | None) -> float:
    if matrix is None or len(matrix) < 3:
        return math.nan
    first = matrix[1] - matrix[0]
    second = matrix[2] - matrix[0]
    if first.size == 2:
        return float(0.5 * abs(first[0] * second[1] - first[1] * second[0]))
    if first.size == 3:
        return float(0.5 * np.linalg.norm(np.cross(first, second)))
    return math.nan


def _finite_sum(values: Sequence[float]) -> float:
    finite_values = [float(value) for value in values if math.isfinite(float(value))]
    return float(sum(finite_values)) if len(finite_values) == len(values) else math.nan


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
    linearized_times = np.asarray(linearized_ephemeris.get("times", []), dtype=float)
    row_count = min(len(linearized_rows), len(empirical_means), len(empirical_covariances))
    compared_times = times[:row_count] if len(times) >= row_count else linearized_times[:row_count]
    if len(linearized_times) >= row_count and len(times) >= row_count and row_count:
        time_mismatches = np.abs(linearized_times[:row_count] - times[:row_count])
        maximum_time_mismatch = float(np.max(time_mismatches))
    else:
        maximum_time_mismatch = math.inf if row_count else 0.0
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
        "times": np.asarray(compared_times, dtype=float).tolist(),
        "time_grid_aligned": bool(maximum_time_mismatch <= 1.0e-12),
        "maximum_time_mismatch": maximum_time_mismatch,
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
    target_times: Sequence[float] | None = None,
    jacobian_step: float,
    rtol: float,
    atol: float,
) -> dict[str, object]:
    state_dimension = initial_state.size
    identity = np.eye(state_dimension, dtype=float)
    t_eval = _prediction_times(target_time, samples, target_times=target_times)
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
            sensitivity = _invalid_linearized_sensitivity_diagnostics()
        else:
            state_covariance = _symmetrize_covariance(transition @ covariance0 @ transition.T)
            position_covariance = state_covariance[:position_width, :position_width]
            std_positions = np.sqrt(np.maximum(np.diag(position_covariance), 0.0)).reshape(
                system.body_count,
                system.dimension,
            )
            sensitivity = _linearized_sensitivity_diagnostics(transition, float(time))
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
                "transition_spectral_radius": sensitivity["transition_spectral_radius"],
                "transition_condition_number": sensitivity["transition_condition_number"],
                "linearized_sensitivity": sensitivity,
            }
        )
    return rows


def _symmetrize_covariance(covariance: np.ndarray) -> np.ndarray:
    covariance = np.asarray(covariance, dtype=float)
    return 0.5 * (covariance + covariance.T)


def _linearized_sensitivity_diagnostics(transition: np.ndarray, elapsed_time: float) -> dict[str, float]:
    transition = np.asarray(transition, dtype=float)
    if transition.ndim != 2 or transition.shape[0] != transition.shape[1] or np.any(~np.isfinite(transition)):
        return _invalid_linearized_sensitivity_diagnostics()
    singular_values = np.linalg.svd(transition, compute_uv=False)
    maximum_singular_value = float(np.max(singular_values)) if singular_values.size else math.inf
    minimum_singular_value = float(np.min(singular_values)) if singular_values.size else math.inf
    condition_number = math.inf if minimum_singular_value == 0.0 else maximum_singular_value / minimum_singular_value
    spectral_radius = float(max(abs(np.linalg.eigvals(transition)))) if transition.size else math.inf
    if elapsed_time == 0.0:
        finite_time_lyapunov_exponent = 0.0 if maximum_singular_value > 0.0 else -math.inf
    elif maximum_singular_value > 0.0 and math.isfinite(maximum_singular_value):
        finite_time_lyapunov_exponent = float(math.log(maximum_singular_value) / abs(elapsed_time))
    else:
        finite_time_lyapunov_exponent = math.inf
    return {
        "transition_spectral_radius": spectral_radius,
        "transition_condition_number": float(condition_number),
        "maximum_singular_value": maximum_singular_value,
        "minimum_singular_value": minimum_singular_value,
        "uncertainty_amplification_factor": maximum_singular_value,
        "finite_time_lyapunov_exponent": finite_time_lyapunov_exponent,
    }


def _invalid_linearized_sensitivity_diagnostics() -> dict[str, float]:
    return {
        "transition_spectral_radius": math.inf,
        "transition_condition_number": math.inf,
        "maximum_singular_value": math.inf,
        "minimum_singular_value": math.inf,
        "uncertainty_amplification_factor": math.inf,
        "finite_time_lyapunov_exponent": math.inf,
    }


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
            sensitivity = _invalid_linearized_sensitivity_diagnostics()
            rows.append(
                {
                    "time": float(time),
                    "max_position_std": math.inf,
                    "rms_position_std": math.inf,
                    "uncertainty_to_tolerance_ratio": math.inf,
                    "transition_spectral_radius": sensitivity["transition_spectral_radius"],
                    "transition_condition_number": sensitivity["transition_condition_number"],
                    "linearized_sensitivity": sensitivity,
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
        sensitivity = _linearized_sensitivity_diagnostics(transition, float(time))
        rows.append(
            {
                "time": float(time),
                "max_position_std": max_position_std,
                "rms_position_std": rms_position_std,
                "uncertainty_to_tolerance_ratio": float(ratio),
                "transition_spectral_radius": sensitivity["transition_spectral_radius"],
                "transition_condition_number": sensitivity["transition_condition_number"],
                "linearized_sensitivity": sensitivity,
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
